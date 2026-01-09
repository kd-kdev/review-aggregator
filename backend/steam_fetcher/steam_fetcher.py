#!/usr/bin/env python3
"""
steam_fetcher.py — concurrent + resume + ETA

Features:
- Cursor persistence (resume from query_summaries.cursor)
- Per-page cursor persistence (safe pause & resume)
- Multi-app concurrency (MAX_WORKERS)
- Per-app ETA (heuristic) & global ETA (heuristic)
- Daily global API call counter enforced (DAILY_CALL_LIMIT)
- Backfill vs incremental via REVIEW_FILTER ('all' or 'recent')
- Stop-early strategy (STOP_IF_NO_NEW_PAGES)
- Graceful SIGINT/SIGTERM handling (finish current page, persist)
- Per-thread requests.Session with retries
- Config via environment variables
"""

import os
import time
import json
import logging
import signal
import threading
import statistics
from math import ceil
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import psycopg2
from psycopg2.extras import execute_values
from dateutil import parser as dateparser

# -------------------------
# Config (env)
# -------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set")

DAILY_CALL_LIMIT = int(os.getenv("DAILY_CALL_LIMIT", "100000"))
ENV_APPIDS = os.getenv("APPID_LIST")
HARDCODED_APPIDS: List[int] = []  # fallback if APPID_LIST not provided

REVIEW_FILTER = os.getenv("REVIEW_FILTER", "recent")  # 'recent' or 'all'
NUM_PER_PAGE = int(os.getenv("NUM_PER_PAGE", "100"))  # Steam accepts up to 100
MAX_PAGES_PER_APP = int(os.getenv("MAX_PAGES_PER_APP", "0"))  # 0 => no limit
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

MAX_WORKERS = int(os.getenv("MAX_WORKERS", "3"))
STOP_IF_NO_NEW_PAGES = int(os.getenv("STOP_IF_NO_NEW_PAGES", "3"))
COMMIT_EVERY_PAGES = int(os.getenv("COMMIT_EVERY_PAGES", "5"))
RESUME_MODE = os.getenv("RESUME_MODE", "auto").lower()  # auto | restart | recent

APPIDS = (
    [int(x.strip()) for x in ENV_APPIDS.split(",") if x.strip()]
    if ENV_APPIDS
    else HARDCODED_APPIDS
)
if not APPIDS:
    raise RuntimeError("No APPIDs provided. Set APPID_LIST or HARDCODED_APPIDS.")

APP_DETAILS_URL = "https://store.steampowered.com/api/appdetails"
REVIEWS_URL = "https://store.steampowered.com/appreviews"

REQUEST_SLEEP = max(0.86, 86400.0 / max(1, DAILY_CALL_LIMIT))

# -------------------------
# Logging
# -------------------------
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("steam_fetcher")

# -------------------------
# Global state
# -------------------------
calls_made = 0
calls_lock = threading.Lock()
stop_requested = False
stop_lock = threading.Lock()

# per-app runtime stats (protected by stats_lock)
app_stats: Dict[int, Dict[str, Any]] = {}
stats_lock = threading.Lock()

# thread-local session
thread_local = threading.local()


# -------------------------
# Utilities
# -------------------------
def handle_sigterm(signum, frame):
    global stop_requested
    with stop_lock:
        stop_requested = True
    logger.warning(
        "Shutdown signal received; current pages will finish and progress persisted."
    )


signal.signal(signal.SIGINT, handle_sigterm)
signal.signal(signal.SIGTERM, handle_sigterm)


def get_session() -> requests.Session:
    if getattr(thread_local, "session", None) is None:
        s = requests.Session()
        retries = Retry(
            total=3, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504)
        )
        s.mount("https://", HTTPAdapter(max_retries=retries))
        s.headers.update({"User-Agent": "steam-fetcher/1.0 (+https://example.com)"})
        thread_local.session = s
    return thread_local.session


@contextmanager
def timed(name: str, extra: str = ""):
    t0 = time.perf_counter()
    try:
        yield
    finally:
        t = time.perf_counter() - t0
        logger.info("TIMING | %-18s | %.3fs %s", name, t, extra)


# -------------------------
# DB helpers
# -------------------------
def get_conn():
    return psycopg2.connect(DATABASE_URL)


def get_local_review_count(conn, appid: int) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM reviews WHERE appid = %s", (appid,))
        row = cur.fetchone()
        return int(row[0]) if row else 0


def get_last_cursor(conn, appid: int) -> Optional[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT cursor FROM query_summaries WHERE appid = %s", (appid,))
        row = cur.fetchone()
        return row[0] if row and row[0] else None


def persist_cursor(conn, appid: int, cursor: Optional[str]):
    """Persist cursor into query_summaries.cursor without overwriting other fields."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO query_summaries (appid, cursor, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (appid) DO UPDATE SET cursor = EXCLUDED.cursor, updated_at = NOW()
            """,
            (appid, cursor),
        )


def upsert_query_summary(conn, appid: int, summary: dict, cursor: Optional[str]):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO query_summaries (
                appid, num_reviews, review_score, review_score_desc,
                total_positive, total_negative, total_reviews,
                cursor, updated_at, raw_json
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s)
            ON CONFLICT (appid) DO UPDATE SET
                num_reviews = EXCLUDED.num_reviews,
                review_score = EXCLUDED.review_score,
                review_score_desc = EXCLUDED.review_score_desc,
                total_positive = EXCLUDED.total_positive,
                total_negative = EXCLUDED.total_negative,
                total_reviews = EXCLUDED.total_reviews,
                cursor = EXCLUDED.cursor,
                updated_at = NOW(),
                raw_json = EXCLUDED.raw_json
            """,
            (
                appid,
                summary.get("num_reviews"),
                summary.get("review_score"),
                summary.get("review_score_desc"),
                summary.get("total_positive"),
                summary.get("total_negative"),
                summary.get("total_reviews"),
                cursor,
                json.dumps(summary),
            ),
        )


# -------------------------
# Steam helpers
# -------------------------
def safe_get(
    url: str, params: Optional[Dict[str, Any]] = None, timeout: int = REQUEST_TIMEOUT
) -> Dict[str, Any]:
    global calls_made
    # check global limit
    with calls_lock:
        if calls_made >= DAILY_CALL_LIMIT:
            raise RuntimeError("Daily API call limit reached")
        calls_made += 1
        this_call = calls_made

    sess = get_session()
    r = sess.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    logger.debug(
        "HTTP call #%d %s params=%s status=%d", this_call, url, params, r.status_code
    )
    return r.json()


def parse_release_date(date_str: Optional[str]):
    if not date_str:
        return None
    try:
        # try a few common forms quickly
        for fmt in ("%b %d, %Y", "%d %b, %Y", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except Exception:
                pass
        # fallback to dateutil
        dt = dateparser.parse(date_str)
        if not dt:
            return None
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        logger.debug("Failed to parse date '%s'", date_str)
        return None


def fetch_game_details(appid: int) -> Optional[Dict[str, Any]]:
    logger.info("Fetching game details for appid=%d", appid)
    try:
        with timed("steam_game_details", f"appid={appid}"):
            data = safe_get(APP_DETAILS_URL, {"appids": appid})
    except Exception as e:
        logger.warning("Failed to fetch game details for %d: %s", appid, e)
        return None
    entry = data.get(str(appid))
    if not entry or not entry.get("success"):
        logger.warning("No game data for appid=%d", appid)
        return None
    game = entry["data"]
    rd = game.get("release_date")
    release_date_str = rd.get("date") if isinstance(rd, dict) else rd
    release_date = parse_release_date(release_date_str)
    if release_date_str and not release_date:
        logger.warning(
            "Could not parse release date '%s' for appid=%d", release_date_str, appid
        )
    return {
        "appid": appid,
        "name": game.get("name"),
        "developers": ",".join(game.get("developers", [])) or None,
        "publishers": ",".join(game.get("publishers", [])) or None,
        "platforms": ",".join(
            [k for k, v in (game.get("platforms") or {}).items() if v]
        )
        or None,
        "release_date": release_date,
        "capsule_imageV5": game.get("header_image"),
    }


def fetch_reviews(appid: int, cursor: str) -> Dict[str, Any]:
    params = {
        "json": 1,
        "language": "english",
        "filter": REVIEW_FILTER,
        "cursor": cursor,
        "purchase_type": "all",
        "num_per_page": NUM_PER_PAGE,
    }
    url = f"{REVIEWS_URL}/{appid}"
    with timed("steam_api_call", f"appid={appid} cursor={str(cursor)[:8]}"):
        return safe_get(url, params=params)


# -------------------------
# Insert helpers
# -------------------------
def upsert_game(conn, game: Dict[str, Any]):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO games (
                appid, name, capsule_imageV5,
                developers, publishers, platforms, release_date
            ) VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (appid) DO UPDATE SET
                name = EXCLUDED.name,
                capsule_imageV5 = EXCLUDED.capsule_imageV5,
                developers = EXCLUDED.developers,
                publishers = EXCLUDED.publishers,
                platforms = EXCLUDED.platforms,
                release_date = EXCLUDED.release_date,
                last_updated = NOW()
            """,
            (
                game["appid"],
                game["name"],
                game["capsule_imageV5"],
                game["developers"],
                game["publishers"],
                game["platforms"],
                game["release_date"],
            ),
        )


def insert_reviews(conn, appid: int, reviews: List[Dict[str, Any]]) -> int:
    if not reviews:
        return 0
    rows = []
    for r in reviews:
        try:
            recid = int(r.get("recommendationid") or r.get("recommendation_id") or 0)
        except Exception:
            continue
        author = r.get("author") or {}
        try:
            steamid = int(author.get("steamid")) if author.get("steamid") else None
        except Exception:
            steamid = None

        def ts_to_dt(ts):
            try:
                return datetime.fromtimestamp(int(ts), tz=timezone.utc) if ts else None
            except Exception:
                return None

        rows.append(
            (
                recid,
                appid,
                steamid,
                r.get("language"),
                r.get("review"),
                r.get("voted_up"),
                r.get("votes_up"),
                r.get("votes_funny"),
                ts_to_dt(r.get("timestamp_created")),
                ts_to_dt(r.get("timestamp_updated")),
                author.get("steam_purchase"),
                author.get("received_for_free"),
                author.get("written_during_early_access"),
                author.get("primarily_steam_deck"),
                json.dumps(r),
            )
        )
    if not rows:
        return 0
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO reviews (
                recommendationid, appid, steamid, language, review,
                voted_up, votes_up, votes_funny,
                timestamp_created, timestamp_updated,
                steam_purchase, received_for_free,
                written_during_early_access, primarily_steam_deck,
                raw_json
            ) VALUES %s
            ON CONFLICT (recommendationid) DO NOTHING
            """,
            rows,
        )
    return len(rows)


# -------------------------
# Worker
# -------------------------
def process_app(appid: int):
    global stop_requested
    logger.info("Worker started for appid=%d", appid)

    # per-worker session created lazily via get_session()
    conn = get_conn()
    try:
        game = fetch_game_details(appid)
        # increment global calls was done inside fetch; safe to proceed
        if not game:
            logger.info("No game details for %d; skipping", appid)
            return {"appid": appid, "inserted": 0, "pages": 0, "time": 0.0}

        # upsert metadata
        upsert_game(conn, game)
        conn.commit()

        # determine resume/start cursor
        if RESUME_MODE == "restart":
            cursor = "*"
        elif RESUME_MODE == "recent":
            cursor = "*"
        else:
            persisted = get_last_cursor(conn, appid)
            cursor = persisted if persisted else "*"
        logger.info(
            "appid=%d starting cursor=%s (mode=%s)",
            appid,
            str(cursor)[:12],
            RESUME_MODE,
        )

        # determine remote total for ETA (if available)
        remote_total = None
        with conn.cursor() as cur:
            cur.execute(
                "SELECT total_reviews FROM query_summaries WHERE appid = %s", (appid,)
            )
            r = cur.fetchone()
            if r and r[0]:
                remote_total = int(r[0])

        local_count = get_local_review_count(conn, appid)
        logger.info(
            "appid=%d local_count=%d remote_total=%s", appid, local_count, remote_total
        )

        page = 1
        pages_processed = 0
        inserted_total = 0
        page_times: List[float] = []
        consecutive_no_new = 0

        # track stats for ETA & global reporting
        with stats_lock:
            app_stats[appid] = {
                "pages_done": 0,
                "avg_page_time": 0.0,
                "remaining_pages_est": None,
            }

        while True:
            # check stop requested
            with stop_lock:
                if stop_requested:
                    logger.warning(
                        "Stop requested; finishing current work for appid=%d", appid
                    )
                    break

            # enforce global call limit pre-check
            with calls_lock:
                if calls_made >= DAILY_CALL_LIMIT:
                    logger.warning(
                        "Global daily call limit reached; stopping appid=%d", appid
                    )
                    break

            logger.info(
                "Fetching reviews page=%d for appid=%d (cursor=%s)",
                page,
                appid,
                str(cursor)[:12] if cursor else "None",
            )
            t0 = time.perf_counter()
            try:
                data = fetch_reviews(appid, cursor)
            except Exception as e:
                logger.warning(
                    "Failed to fetch reviews for appid=%d page=%d: %s", appid, page, e
                )
                break
            t1 = time.perf_counter()
            page_time = t1 - t0
            page_times.append(page_time)

            # persist query_summary if present
            qs = data.get("query_summary")
            if qs:
                try:
                    upsert_query_summary(conn, appid, qs, data.get("cursor"))
                    conn.commit()
                    remote_total = qs.get("total_reviews") or remote_total
                except Exception as e:
                    logger.warning(
                        "Failed to upsert query_summary for %d: %s", appid, e
                    )
                    conn.rollback()
            else:
                # still persist cursor even if no query_summary
                try:
                    persist_cursor(conn, appid, data.get("cursor"))
                    conn.commit()
                except Exception:
                    conn.rollback()

            # insert reviews
            reviews = data.get("reviews") or []
            cursor = data.get(
                "cursor"
            )  # update cursor from response for next iteration

            if not reviews:
                consecutive_no_new += 1
                logger.info(
                    "No reviews returned for appid=%d page=%d (consecutive_no_new=%d)",
                    appid,
                    page,
                    consecutive_no_new,
                )
                if consecutive_no_new >= STOP_IF_NO_NEW_PAGES:
                    logger.info(
                        "Stopping appid=%d after %d consecutive empty pages",
                        appid,
                        consecutive_no_new,
                    )
                    break
            else:
                # do insertion
                try:
                    inserted = insert_reviews(conn, appid, reviews)
                except Exception as e:
                    logger.warning(
                        "DB insert failed for appid=%d page=%d: %s", appid, page, e
                    )
                    conn.rollback()
                    break

                if inserted:
                    inserted_total += inserted
                    consecutive_no_new = 0
                else:
                    consecutive_no_new += 1

                # commit batch/per-page durability
                try:
                    if page % COMMIT_EVERY_PAGES == 0:
                        with timed("db_commit", f"appid={appid} page={page}"):
                            conn.commit()
                    else:
                        conn.commit()
                except Exception as e:
                    logger.warning(
                        "DB commit failed for appid=%d page=%d: %s", appid, page, e
                    )
                    conn.rollback()
                    break

                logger.info(
                    "Inserted %d reviews for appid=%d (page %d). Total inserted this run: %d",
                    inserted,
                    appid,
                    page,
                    inserted_total,
                )

            pages_processed += 1
            page += 1

            # update app_stats for ETA
            avg_time = statistics.mean(page_times) if page_times else REQUEST_SLEEP
            # remaining reviews heuristic: remote_total - local_count (local_count may be stale; recompute)
            local_count = get_local_review_count(conn, appid)
            remaining_reviews = (
                max(0, (remote_total - local_count) if remote_total else None)
                if remote_total
                else None
            )
            remaining_pages_est = (
                ceil(remaining_reviews / NUM_PER_PAGE)
                if remaining_reviews is not None and NUM_PER_PAGE
                else None
            )

            with stats_lock:
                app_stats[appid]["pages_done"] = pages_processed
                app_stats[appid]["avg_page_time"] = avg_time
                app_stats[appid]["remaining_pages_est"] = remaining_pages_est

            # log ETA per app (heuristic)
            if remaining_pages_est is not None and avg_time:
                eta_secs = remaining_pages_est * avg_time
                eta_str = (
                    f"{eta_secs / 60:.1f}min" if eta_secs >= 60 else f"{eta_secs:.1f}s"
                )
                logger.info(
                    "ETA for appid=%d: remaining_reviews=%d remaining_pages=%d avg_page_time=%.2fs ETA=%s",
                    appid,
                    remaining_reviews,
                    remaining_pages_est,
                    avg_time,
                    eta_str,
                )
            else:
                logger.info(
                    "ETA for appid=%d: remote_total=%s avg_page_time=%.2fs ETA=unknown",
                    appid,
                    remote_total,
                    avg_time,
                )

            # developer safety
            if MAX_PAGES_PER_APP > 0 and pages_processed >= MAX_PAGES_PER_APP:
                logger.info(
                    "Reached MAX_PAGES_PER_APP for appid=%d (%d) — stopping",
                    appid,
                    MAX_PAGES_PER_APP,
                )
                break

            # stop if cursor exhausted
            if not cursor:
                logger.info("Cursor exhausted for appid=%d", appid)
                break

            # polite sleep
            time.sleep(REQUEST_SLEEP)

        # finalize: ensure last cursor persisted
        try:
            persist_cursor(conn, appid, cursor)
            conn.commit()
        except Exception:
            conn.rollback()

        # final stats update
        with stats_lock:
            app_stats[appid]["pages_done"] = pages_processed
            app_stats[appid]["avg_page_time"] = (
                statistics.mean(page_times) if page_times else 0.0
            )
            app_stats[appid]["remaining_pages_est"] = (
                remaining_pages_est if "remaining_pages_est" in locals() else None
            )

        elapsed = sum(page_times) if page_times else 0.0
        logger.info(
            "Worker finished appid=%d inserted=%d pages=%d time=%.1fs",
            appid,
            inserted_total,
            pages_processed,
            elapsed,
        )
        return {
            "appid": appid,
            "inserted": inserted_total,
            "pages": pages_processed,
            "time": elapsed,
        }
    finally:
        try:
            conn.close()
        except Exception:
            pass


# -------------------------
# Global ETA helper
# -------------------------
def compute_global_eta():
    """
    Heuristic global ETA:
    Sum remaining_seconds across apps and divide by active worker count.
    This is approximate and labeled as heuristic in logs.
    """
    with stats_lock:
        entries = list(app_stats.items())
    if not entries:
        return None
    total_remaining_seconds = 0.0
    total_pages_left = 0
    valid_entries = 0
    for appid, s in entries:
        rem_pages = s.get("remaining_pages_est")
        avg = s.get("avg_page_time") or 0.0
        if rem_pages is None or avg == 0.0:
            continue
        total_remaining_seconds += rem_pages * avg
        total_pages_left += rem_pages
        valid_entries += 1
    if valid_entries == 0:
        return None
    # wall-clock heuristic: assume MAX_WORKERS parallelism
    parallelism = min(MAX_WORKERS, max(1, valid_entries))
    wall_clock_seconds = total_remaining_seconds / parallelism
    return wall_clock_seconds


# -------------------------
# Main
# -------------------------
def main():
    logger.info("==============================================")
    logger.info("Steam Fetcher starting")
    logger.info("APPIDS: %s", APPIDS)
    logger.info("REVIEW_FILTER: %s", REVIEW_FILTER)
    logger.info("NUM_PER_PAGE: %d", NUM_PER_PAGE)
    logger.info("MAX_PAGES_PER_APP: %d", MAX_PAGES_PER_APP)
    logger.info("MAX_WORKERS: %d", MAX_WORKERS)
    logger.info("STOP_IF_NO_NEW_PAGES: %d", STOP_IF_NO_NEW_PAGES)
    logger.info("COMMIT_EVERY_PAGES: %d", COMMIT_EVERY_PAGES)
    logger.info("Daily call limit: %d", DAILY_CALL_LIMIT)
    logger.info("Sleep between requests: %.2fs", REQUEST_SLEEP)
    logger.info("RESUME_MODE: %s", RESUME_MODE)
    logger.info("==============================================")

    start = time.time()
    results = []

    # initialize app_stats placeholders
    with stats_lock:
        for aid in APPIDS:
            app_stats[aid] = {
                "pages_done": 0,
                "avg_page_time": 0.0,
                "remaining_pages_est": None,
            }

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(process_app, aid): aid for aid in APPIDS}
        # periodically log global ETA while workers run
        try:
            while futures:
                done, not_done = [], []
                for fut in futures:
                    if fut.done():
                        done.append(fut)
                    else:
                        not_done.append(fut)
                # collect completed
                for fut in done:
                    aid = futures.pop(fut)
                    try:
                        res = fut.result()
                        results.append(res)
                    except Exception as e:
                        logger.exception("Worker for appid %s raised: %s", aid, e)
                # log global ETA
                eta_seconds = compute_global_eta()
                if eta_seconds is not None:
                    eta_str = (
                        f"{eta_seconds / 60:.1f}min"
                        if eta_seconds >= 60
                        else f"{eta_seconds:.1f}s"
                    )
                    logger.info("Global ETA (heuristic): %s", eta_str)
                # sleep briefly then continue
                if futures:
                    time.sleep(5)
        except KeyboardInterrupt:
            logger.warning(
                "Main interrupted by user; waiting for workers to notice stop flag"
            )
            with stop_lock:
                global stop_requested
                stop_requested = True
            # wait for futures to finish their current page
            for fut in futures:
                try:
                    fut.result(timeout=60)
                except Exception:
                    pass

    total_inserted = sum((r.get("inserted", 0) for r in results))
    total_pages = sum((r.get("pages", 0) for r in results))
    elapsed = time.time() - start
    logger.info(
        "All workers finished. Inserted total=%d pages=%d time=%.1fs",
        total_inserted,
        total_pages,
        elapsed,
    )


if __name__ == "__main__":
    main()
