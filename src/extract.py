import json
import logging
import time

import requests

from src.config import API_URL, RAW_DIR, USER_AGENT

logger = logging.getLogger(__name__)


def fetch(query, retries=3):
    url = f"{API_URL}?q={query}"
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            logger.warning("Request failed for %s (attempt %s/%s): %s", query, attempt, retries, error)
            if attempt == retries:
                raise
            time.sleep(2 * attempt)


def save_raw(data, name):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
    return path


def get_teams():
    data = fetch("teams")
    save_raw(data, "teams")
    return data["teams"]


def get_games(year):
    data = fetch(f"games;year={year}")
    save_raw(data, f"games_{year}")
    return data["games"]


def get_standings(year):
    data = fetch(f"standings;year={year}")
    save_raw(data, f"standings_{year}")
    rows = data["standings"]
    for row in rows:
        row["year"] = year
    return rows


def extract_all(years):
    teams = get_teams()
    logger.info("Extracted %s teams", len(teams))

    games = []
    standings = []
    for year in years:
        year_games = get_games(year)
        time.sleep(1)
        year_standings = get_standings(year)
        time.sleep(1)
        logger.info("Extracted %s games and %s ladder rows for %s", len(year_games), len(year_standings), year)
        games.extend(year_games)
        standings.extend(year_standings)

    return teams, games, standings
