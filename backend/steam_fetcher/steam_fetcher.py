#!/usr/bin/env python3

import os
import time
import json
import logging
import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone

# --------------------------------------------------
# Configuration
# --------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")
DAILY_CALL_LIMIT = int(os.getenv("DAILY_CALL_LIMIT", "100000"))

ENV_APPIDS = os.getenv("APPID_LIST")

HARDCODED_APPIDS = []

if ENV_APPIDS:
    APPIDS = [int(x.strip()) for x in ENV_APPIDS.split(",") if x.strip()]
else:
    APPIDS = HARDCODED_APPIDS

if not APPIDS:
    raise RuntimeError("No APPIDs provided. Set APPID_LIST or edit HARDCODED_APPIDS.")

APP_DETAILS_URL = "https://store.steampowered.com/api/appdetails"
REVIEWS_URL = "https://store.steampowered.com/appreviews"

REQUEST_SLEEP = max(0.86, 86400 / DAILY_CALL_LIMIT)

# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("steam_fetcher")

# --------------------------------------------------
# Database helpers
# --------------------------------------------------


def get_conn():
    logger.info("Connecting to PostgreSQL...")
    conn = psycopg2.connect(DATABASE_URL)
    logger.info("PostgreSQL connection established")
    return conn


# --------------------------------------------------
# Steam API helpers
# --------------------------------------------------


def fetch_game_details(appid):
    logger.info("Fetching game details for appid=%d", appid)
    params = {"appids": appid}
    r = requests.get(APP_DETAILS_URL, params=params, timeout=30)
    r.raise_for_status()

    data = r.json()
    entry = data.get(str(appid))

    if not entry or not entry.get("success"):
        logger.warning("Steam returned no game data for appid=%d", appid)
        return None

    game = entry["data"]

    release_date_str = game.get("release_date", {}).get("date")
    release_date = None
    if release_date_str:
        try:
            release_date = datetime.strptime(release_date_str, "%b %d, %Y").replace(
                tzinfo=timezone.utc
            )
        except Exception:
            logger.warning(
                "Could not parse release date '%s' for appid=%d",
                release_date_str,
                appid,
            )

    return {
        "appid": appid,
        "name": game.get("name"),
        "developers": ",".join(game.get("developers", [])) or None,
        "publishers": ",".join(game.get("publishers", [])) or None,
        "platforms": ",".join([k for k, v in game.get("platforms", {}).items() if v])
        or None,
        "release_date": release_date,
        "capsule_imageV5": game.get("header_image"),
    }


def fetch_reviews(appid, cursor):
    params = {
        "json": 1,
        "language": "english",
        "filter": "recent",
        "cursor": cursor,
        "purchase_type": "all",
        "num_per_page": 100,
    }
    r = requests.get(f"{REVIEWS_URL}/{appid}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


# --------------------------------------------------
# Insertion helpers
# --------------------------------------------------


def upsert_game(conn, game):
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


def insert_reviews(conn, appid, reviews):
    rows = []
    for r in reviews:
        rows.append(
            (
                int(r["recommendationid"]),
                appid,
                int(r["author"]["steamid"]),
                r.get("language"),
                r.get("review"),
                r.get("voted_up"),
                r.get("votes_up"),
                r.get("votes_funny"),
                datetime.fromtimestamp(r["timestamp_created"], tz=timezone.utc),
                datetime.fromtimestamp(r["timestamp_updated"], tz=timezone.utc),
                r["author"].get("steam_purchase"),
                r["author"].get("received_for_free"),
                r["author"].get("written_during_early_access"),
                r["author"].get("primarily_steam_deck"),
                json.dumps(r),
            )
        )

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


def upsert_query_summary(conn, appid, summary, cursor):
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


# --------------------------------------------------
# Main loop
# --------------------------------------------------


def main():
    conn = get_conn()
    calls = 0

    try:
        for appid in APPIDS:
            game = fetch_game_details(appid)
            calls += 1

            if not game:
                continue

            upsert_game(conn, game)
            conn.commit()
            time.sleep(REQUEST_SLEEP)

            cursor = "*"
            page = 1
            total_reviews = 0
            first_page = True

            while True:
                data = fetch_reviews(appid, cursor)
                calls += 1

                if first_page:
                    qs = data.get("query_summary")
                    if qs:
                        upsert_query_summary(conn, appid, qs, data.get("cursor"))
                        conn.commit()
                    first_page = False

                reviews = data.get("reviews", [])
                cursor = data.get("cursor")

                if not reviews:
                    break

                insert_reviews(conn, appid, reviews)
                conn.commit()
                total_reviews += len(reviews)

                page += 1
                time.sleep(REQUEST_SLEEP)

                if not cursor:
                    break

    finally:
        conn.close()


if __name__ == "__main__":
    main()
