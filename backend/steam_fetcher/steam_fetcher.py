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

# APPID list (env overrides hardcoded)
ENV_APPIDS = os.getenv("APPID_LIST")

HARDCODED_APPIDS = [
    # Example:
    # 570, 440, 730
]

if ENV_APPIDS:
    APPIDS = [int(x.strip()) for x in ENV_APPIDS.split(",") if x.strip()]
else:
    APPIDS = HARDCODED_APPIDS

if not APPIDS:
    raise RuntimeError("No APPIDs provided. Set APPID_LIST or edit HARDCODED_APPIDS.")

# Steam endpoints (stable)
APP_DETAILS_URL = "https://store.steampowered.com/api/appdetails"
REVIEWS_URL = "https://store.steampowered.com/appreviews"

REQUEST_SLEEP = max(0.86, 86400 / DAILY_CALL_LIMIT)

# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("steam_fetcher")

# --------------------------------------------------
# Database helpers
# --------------------------------------------------


def get_conn():
    return psycopg2.connect(DATABASE_URL)


# --------------------------------------------------
# Steam API helpers
# --------------------------------------------------


def fetch_game_details(appid):
    params = {"appids": appid}
    r = requests.get(APP_DETAILS_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    entry = data.get(str(appid))
    if not entry or not entry.get("success"):
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
            pass

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


def fetch_reviews(appid, cursor="*"):
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


# --------------------------------------------------
# Main loop
# --------------------------------------------------


def main():
    logger.info(
        "Starting steam_fetcher. Apps=%d | Daily limit=%d | Sleep=%.2fs",
        len(APPIDS),
        DAILY_CALL_LIMIT,
        REQUEST_SLEEP,
    )

    conn = get_conn()
    calls = 0

    try:
        for appid in APPIDS:
            logger.info("Processing app %d", appid)

            game = fetch_game_details(appid)
            calls += 1
            if not game:
                logger.warning("No data for app %d", appid)
                continue

            upsert_game(conn, game)
            conn.commit()
            time.sleep(REQUEST_SLEEP)

            cursor = "*"
            while True:
                data = fetch_reviews(appid, cursor)
                calls += 1

                reviews = data.get("reviews", [])
                if reviews:
                    insert_reviews(conn, appid, reviews)
                    conn.commit()

                cursor = data.get("cursor")
                if not reviews or not cursor:
                    break

                time.sleep(REQUEST_SLEEP)

            if calls >= DAILY_CALL_LIMIT:
                logger.warning("Daily API limit reached, stopping.")
                return

    finally:
        conn.close()


if __name__ == "__main__":
    main()
