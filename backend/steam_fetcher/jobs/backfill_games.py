#!/usr/bin/env python3

import os
import time
import logging
import json
from datetime import datetime, timezone
from typing import Optional

import requests
import psycopg2
from dateutil import parser as dateparser

# -------------------------
# Config
# -------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set")

STEAM_APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"
STEAM_REVIEWS_URL = "https://store.steampowered.com/appreviews"

REQUEST_TIMEOUT = 15
SLEEP_BETWEEN_CALLS = 0.3

# -------------------------
# Logging
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("backfill_games")


# -------------------------
# DB helpers
# -------------------------
def get_conn():
    return psycopg2.connect(DATABASE_URL)


# -------------------------
# Steam helpers
# -------------------------
def fetch_app_details(appid: int) -> Optional[dict]:
    try:
        r = requests.get(
            STEAM_APPDETAILS_URL,
            params={"appids": appid},
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        payload = r.json().get(str(appid))
        if not payload or not payload.get("success"):
            return None
        return payload["data"]
    except Exception as e:
        logger.warning("Failed to fetch appdetails for appid=%d: %s", appid, e)
        return None


def fetch_query_summary(appid: int) -> Optional[dict]:
    try:
        r = requests.get(
            f"{STEAM_REVIEWS_URL}/{appid}",
            params={
                "json": 1,
                "language": "english",
                "filter": "all",
                "num_per_page": 0,
            },
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        return r.json().get("query_summary")
    except Exception as e:
        logger.warning("Failed to fetch query_summary for appid=%d: %s", appid, e)
        return None


def parse_release_date(value: Optional[str]):
    if not value:
        return None
    try:
        for fmt in ("%b %d, %Y", "%d %b, %Y", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(value, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except Exception:
                pass
        dt = dateparser.parse(value)
        if not dt:
            return None
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


# -------------------------
# Backfill logic
# -------------------------
def backfill_games(limit: Optional[int] = None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT g.appid, g.name
                FROM games g
                LEFT JOIN query_summaries qs ON qs.appid = g.appid
                WHERE g.capsule_imageV5 IS NULL
                   OR g.release_date IS NULL
                   OR qs.appid IS NULL
                   OR qs.review_score IS NULL
                ORDER BY g.appid
                """
                + (" LIMIT %s" if limit else ""),
                (limit,) if limit else (),
            )
            rows = cur.fetchall()

        logger.info("Found %d games needing backfill", len(rows))
        updated_games = 0
        updated_summaries = 0

        for appid, name in rows:
            logger.info("Backfilling appid=%d (%s)", appid, name)

            # ---------- games ----------
            data = fetch_app_details(appid)
            if not data:
                continue

            header = data.get("header_image")
            rd = data.get("release_date") or {}
            rd_str = rd.get("date") if isinstance(rd, dict) else rd
            release_date = None if rd.get("coming_soon") else parse_release_date(rd_str)

            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE games
                    SET
                        capsule_imageV5 = COALESCE(capsule_imageV5, %s),
                        release_date = COALESCE(release_date, %s),
                        last_updated = NOW()
                    WHERE appid = %s
                    """,
                    (header, release_date, appid),
                )
                if cur.rowcount:
                    updated_games += 1

            # ---------- query_summaries (FULL) ----------
            qs = fetch_query_summary(appid)
            if qs:
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
                            raw_json,
                            updated_at
                        )
                        VALUES (%s,%s,%s,%s,%s,%s,%s,NULL,%s,NOW())
                        ON CONFLICT (appid) DO UPDATE SET
                            num_reviews = EXCLUDED.num_reviews,
                            review_score = EXCLUDED.review_score,
                            review_score_desc = EXCLUDED.review_score_desc,
                            total_positive = EXCLUDED.total_positive,
                            total_negative = EXCLUDED.total_negative,
                            total_reviews = EXCLUDED.total_reviews,
                            raw_json = EXCLUDED.raw_json,
                            updated_at = NOW()
                        """,
                        (
                            appid,
                            qs.get("num_reviews"),
                            qs.get("review_score"),
                            qs.get("review_score_desc"),
                            qs.get("total_positive"),
                            qs.get("total_negative"),
                            qs.get("total_reviews"),
                            json.dumps(qs),
                        ),
                    )
                    updated_summaries += 1

            conn.commit()
            time.sleep(SLEEP_BETWEEN_CALLS)

        logger.info(
            "Backfill complete. Updated games=%d query_summaries=%d",
            updated_games,
            updated_summaries,
        )

    finally:
        conn.close()


# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    backfill_games()
