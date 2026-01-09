#!/usr/bin/env python3
"""
steam_fetcher.py — feature-complete runner

Features:
- Cursor persistence (resume from query_summaries.cursor)
- ETA & progress reporting per app
- Daily incremental vs backfill (REVIEW_FILTER: "recent" or "all")
- Multi-app concurrency (MAX_WORKERS) with a global API call counter that respects DAILY_CALL_LIMIT
- Stop-early if no new reviews for STOP_IF_NO_NEW_PAGES consecutive pages
- Per-thread requests.Session with retries
- Robust date parsing and durable DB writes
"""

import os
import time
import json
import logging
import threading
from math import ceil
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone
from dateutil import parser as dateparser

# -------------------------
# Configuration (env-driven)
# -------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set")

DAILY_CALL_LIMIT = int(os.getenv("DAILY_CALL_LIMIT", "100000"))
ENV_APPIDS = os.getenv("APPID_LIST")
HARDCODED_APPIDS: List[int] = []  # optional
REVIEW_FILTER = os.getenv("REVIEW_FILTER", "recent")  # 'recent' or 'all'
NUM_PER_PAGE = int(os.getenv("NUM_PER_PAGE", "100"))  # Steam max 100
MAX_PAGES_PER_APP = int(os.getenv("MAX_PAGES_PER_APP", "0"))  # 0 => no limit
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# New behavior toggles
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "3"))  # concurrency across appids
STOP_IF_NO_NEW_PAGES = int(os.getenv("STOP_IF_NO_NEW_PAGES", "3"))
COMMIT_EVERY_PAGES = int(os.getenv("COMMIT_EVERY_PAGES", "5"))  # batch commits
RESUME_FROM_CURSOR = os.getenv("RESUME_FROM_CURSOR", "true").lower() in (
    "1",
    "true",
    "yes",
)

APPIDS = (
    [int(x.strip()) for x in ENV_APPIDS.split(",") if x.strip()]
    if ENV_APPIDS
    else HARDCODED_APPIDS
)
if not APPIDS:
    raise RuntimeError("No APPIDs provided. Set APPID_LIST or edit HARDCODED_APPIDS.")

APP_DETAILS_URL = "https://store.steampowered.com/api/appdetails"
REVIEWS_URL = "https://store.steampowered.com/appreviews"

# compute safe sleep between requests so we don't exceed DAILY_CALL_LIMIT over 24h
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
# Global counters & locks
# -------------------------
calls_made = 0
calls_lock = threading.Lock()

# Thread-local session holder
thread_local = threading.local()


# -------------------------
# Utility functions
# -------------------------
def get_session() -> requests.Session:
    """Return a thread-local requests.Session configured with retries."""
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
def timed(label: str, extra: str = ""):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info("TIMING | %-20s | %.3fs %s", label, elapsed, extra)


# -------------------------
# DB helpers
# -------------------------
def get_conn():
    """Return a new DB connection (caller must close)."""
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def get_local_review_count(conn, appid: int) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM reviews WHERE appid = %s", (appid,))
        n = cur.fetchone()[0]
        return n


def get_persisted_cursor(conn, appid: int) -> Optional[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT cursor FROM query_summaries WHERE appid = %s", (appid,))
        row = cur.fetchone()
        return row[0] if row else None


# -------------------------
# Steam API helpers
# -------------------------
def safe_get(
    url: str, params: Optional[Dict[str, Any]] = None, timeout: int = REQUEST_TIMEOUT
) -> Dict[str, Any]:
    """GET using the thread-local session; increments global calls counter safely."""
    global calls_made
    with calls_lock:
        if calls_made >= DAILY_CALL_LIMIT:
            raise RuntimeError(f"Daily API limit {DAILY_CALL_LIMIT} reached")
        calls_made += 1
        current_call = calls_made

    sess = get_session()
    r = sess.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    logger.debug(
        "HTTP call #%d %s params=%s status=%d", current_call, url, params, r.status_code
    )
    return r.json()


def parse_release_date(date_str: Optional[str]):
    if not date_str:
        return None
    date_str = date_str.strip()
    fmt_candidates = ("%b %d, %Y", "%d %b, %Y", "%Y-%m-%d", "%d %b %Y", "%b %Y")
    for fmt in fmt_candidates:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            continue
    try:
        dt = dateparser.parse(date_str)
        if not dt:
            return None
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        logger.debug("dateutil failed to parse '%s'", date_str)
        return None


def fetch_game_details(appid: int) -> Optional[Dict[str, Any]]:
    logger.info("Fetching game details for appid=%d", appid)
    params = {"appids": appid}
    try:
        with timed("steam_game_details", f"appid={appid}"):
            resp = safe_get(APP_DETAILS_URL, params=params)
    except Exception as e:
        logger.warning("Failed fetching app details for %d: %s", appid, e)
        return None
    entry = resp.get(str(appid))
    if not entry or not entry.get("success"):
        logger.warning("Steam returned no game data for appid=%d", appid)
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
    with timed(
        "steam_api_call", f"appid={appid} cursor={cursor[:6] if cursor else 'None'}"
    ):
        return safe_get(url, params=params)


# -------------------------
# DB insertion helpers (same as before, with small changes)
# -------------------------
def upsert_game(conn, game: Dict[str, Any]):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO games (
                appid, name, capsule_imageV5,
                developers, publishers, platforms, release_date
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
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


def insert_reviews(conn, appid: int, reviews: List[Dict[str, Any]]):
    if not reviews:
        return 0
    rows = []
    for r in reviews:
        try:
            recommendationid = int(
                r.get("recommendationid") or r.get("recommendation_id") or 0
            )
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
                recommendationid,
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
            )
            VALUES %s
            ON CONFLICT (recommendationid) DO NOTHING
            """,
            rows,
        )
    return len(rows)


def upsert_query_summary(
    conn, appid: int, summary: Dict[str, Any], cursor: Optional[str]
):
    if not summary:
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO query_summaries (
                appid,
                num_reviews,
                review_score,
                review_score_desc,
                total_positive,
                total_negative,
                total_reviews,
                cursor,
                updated_at,
                raw_json
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
# Worker for a single appid
# -------------------------
def process_app(appid: int):
    """Process one appid: fetch metadata, resume cursor, paginate reviews, persist cursor & progress."""
    logger.info("Worker starting for appid=%d", appid)
    conn = get_conn()
    try:
        # fetch metadata
        game = fetch_game_details(appid)
        if not game:
            logger.info("No game data for %d — skipping", appid)
            return {"appid": appid, "inserted": 0, "pages": 0, "time": 0.0}

        upsert_game(conn, game)
        conn.commit()

        # determine starting cursor
        start_cursor = None
        if RESUME_FROM_CURSOR:
            start_cursor = get_persisted_cursor(conn, appid)
            logger.info(
                "Resuming from persisted cursor for appid=%d: %s",
                appid,
                str(start_cursor)[:12] if start_cursor else "None",
            )

        cursor = start_cursor or "*"

        # get remote totals if available (for ETA)
        qs_row = None
        with conn.cursor() as cur:
            cur.execute(
                "SELECT total_reviews FROM query_summaries WHERE appid = %s", (appid,)
            )
            row = cur.fetchone()
            if row:
                qs_row = {"total_reviews": row[0]}

        # local count
        local_count = get_local_review_count(conn, appid)
        logger.info(
            "appid=%d local_reviews=%d remote_total=%s",
            appid,
            local_count,
            qs_row.get("total_reviews") if qs_row else "unknown",
        )

        page = 1
        total_inserted = 0
        page_times = []
        consecutive_no_new = 0

        # If we already have total remote count, compute pages remaining for ETA
        remote_total = qs_row.get("total_reviews") if qs_row else None

        while True:
            # global call limit check
            with calls_lock:
                if calls_made >= DAILY_CALL_LIMIT:
                    logger.warning(
                        "Global daily call limit reached. Worker for %d stopping.",
                        appid,
                    )
                    break

            logger.info(
                "Fetching reviews page=%d for appid=%d (cursor=%s)",
                page,
                appid,
                cursor[:12] if cursor else "None",
            )
            t0 = time.perf_counter()
            try:
                data = fetch_reviews(appid, cursor)
            except Exception as e:
                logger.warning(
                    "Failed to fetch reviews for %d page=%d: %s", appid, page, e
                )
                break
            t1 = time.perf_counter()
            page_times.append(t1 - t0)

            # persist query_summary on first page or when present
            qs = data.get("query_summary")
            if qs:
                try:
                    upsert_query_summary(conn, appid, qs, data.get("cursor"))
                    conn.commit()
                    # update remote_total for ETA
                    remote_total = qs.get("total_reviews") or remote_total
                except Exception as e:
                    logger.warning(
                        "Failed to upsert query_summary for %d: %s", appid, e
                    )
                    conn.rollback()

            reviews = data.get("reviews") or []
            cursor = data.get("cursor")

            if not reviews:
                logger.info("No reviews returned for appid=%d page=%d", appid, page)
                consecutive_no_new += 1
                if consecutive_no_new >= STOP_IF_NO_NEW_PAGES:
                    logger.info(
                        "Stopping appid=%d after %d consecutive empty pages",
                        appid,
                        consecutive_no_new,
                    )
                    break
            else:
                # insert and commit in batches
                inserted = 0
                try:
                    inserted = insert_reviews(conn, appid, reviews)
                    if inserted:
                        total_inserted += inserted
                        consecutive_no_new = 0
                    else:
                        consecutive_no_new += 1
                except Exception as e:
                    logger.warning(
                        "DB insert failed for appid=%d page=%d: %s", appid, page, e
                    )
                    conn.rollback()
                    # treat as failure page and break to avoid infinite loop
                    break

                # commit periodically to reduce fsyncs
                if page % COMMIT_EVERY_PAGES == 0:
                    with timed("db_commit", f"appid={appid} page={page}"):
                        conn.commit()
                else:
                    # still commit small metadata if query_summary updated earlier; ensure durability per page
                    conn.commit()

                logger.info(
                    "Inserted %d reviews for appid=%d (page %d). Total inserted this run: %d",
                    inserted,
                    appid,
                    page,
                    total_inserted,
                )

            page += 1

            # developer safety: optional page limit
            if MAX_PAGES_PER_APP > 0 and page > MAX_PAGES_PER_APP:
                logger.info(
                    "Reached MAX_PAGES_PER_APP (%d) for appid=%d — stopping pagination for this app",
                    MAX_PAGES_PER_APP,
                    appid,
                )
                break

            # if Steam returned no cursor, stop
            if not cursor:
                logger.info("Cursor exhausted for appid=%d", appid)
                break

            # ETA reporting: estimate remaining time based on average page time
            avg_page_time = statistics.mean(page_times) if page_times else 0.0
            if remote_total:
                remaining_reviews = max(
                    0, remote_total - get_local_review_count(conn, appid)
                )
                remaining_pages = (
                    ceil(remaining_reviews / NUM_PER_PAGE) if NUM_PER_PAGE else 0
                )
                eta_seconds = remaining_pages * avg_page_time if avg_page_time else None
                eta_str = f"{eta_seconds / 60:.1f}min" if eta_seconds else "unknown"
                logger.info(
                    "ETA for appid=%d: remaining_reviews=%d remaining_pages=%d avg_page_time=%.2fs ETA=%s",
                    appid,
                    remaining_reviews,
                    remaining_pages,
                    avg_page_time,
                    eta_str,
                )

            # polite sleep (global rate limiting)
            time.sleep(REQUEST_SLEEP)

        elapsed = sum(page_times) if page_times else 0.0
        logger.info(
            "Worker finished for appid=%d inserted=%d pages=%d time=%.1fs",
            appid,
            total_inserted,
            max(1, page - 1),
            elapsed,
        )
        return {
            "appid": appid,
            "inserted": total_inserted,
            "pages": max(0, page - 1),
            "time": elapsed,
        }
    finally:
        try:
            conn.close()
        except Exception:
            pass


# -------------------------
# Main program: parallel dispatch
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
    logger.info("==============================================")

    start = time.time()
    results = []
    # simple global progress: estimate total remote reviews (sum of query_summaries if present)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(process_app, appid): appid for appid in APPIDS}
        for fut in as_completed(futures):
            appid = futures[fut]
            try:
                res = fut.result()
                results.append(res)
            except Exception as e:
                logger.exception("Worker raised for appid=%s: %s", appid, e)

    total_inserted = sum(r.get("inserted", 0) for r in results)
    total_pages = sum(r.get("pages", 0) for r in results)
    elapsed = time.time() - start
    logger.info(
        "All workers finished. Inserted total=%d pages=%d time=%.1fs",
        total_inserted,
        total_pages,
        elapsed,
    )


if __name__ == "__main__":
    main()
