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


def get_data(query, name, refresh=False):
    path = RAW_DIR / f"{name}.json"
    if path.exists() and not refresh:
        logger.info("Using saved %s", path.name)
        with open(path, encoding="utf-8") as file:
            return json.load(file)

    data = fetch(query)
    save_raw(data, name)
    time.sleep(1)
    return data


def get_teams(refresh=False):
    return get_data("teams", "teams", refresh)["teams"]


def get_games(year, refresh=False):
    return get_data(f"games;year={year}", f"games_{year}", refresh)["games"]


def get_standings(year, refresh=False):
    rows = get_data(f"standings;year={year}", f"standings_{year}", refresh)["standings"]
    for row in rows:
        row["year"] = year
    return rows


def extract_all(years, refresh=False):
    teams = get_teams(refresh)
    logger.info("Extracted %s teams", len(teams))

    games = []
    standings = []
    for year in years:
        year_games = get_games(year, refresh)
        year_standings = get_standings(year, refresh)
        logger.info("Extracted %s games and %s ladder rows for %s", len(year_games), len(year_standings), year)
        games.extend(year_games)
        standings.extend(year_standings)

    return teams, games, standings
