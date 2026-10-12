import logging

import pandas as pd

from src.config import LOGO_BASE_URL, PROCESSED_DIR

logger = logging.getLogger(__name__)

TEAM_COLUMNS = {
    "id": "team_id",
    "name": "team_name",
    "abbrev": "abbreviation",
    "debut": "debut_year",
    "retirement": "retirement_year",
    "logo": "logo_url",
}

GAME_COLUMNS = {
    "id": "game_id",
    "year": "season",
    "round": "round_number",
    "roundname": "round_name",
    "date": "match_datetime",
    "tz": "timezone",
    "venue": "venue",
    "hteamid": "home_team_id",
    "hteam": "home_team",
    "ateamid": "away_team_id",
    "ateam": "away_team",
    "hgoals": "home_goals",
    "hbehinds": "home_behinds",
    "hscore": "home_score",
    "agoals": "away_goals",
    "abehinds": "away_behinds",
    "ascore": "away_score",
    "winnerteamid": "winner_team_id",
    "winner": "winner",
    "is_final": "is_final",
    "is_grand_final": "is_grand_final",
    "complete": "complete_pct",
    "updated": "updated_at",
}

STANDING_COLUMNS = {
    "year": "season",
    "id": "team_id",
    "name": "team_name",
    "rank": "ladder_rank",
    "played": "played",
    "wins": "wins",
    "losses": "losses",
    "draws": "draws",
    "pts": "premiership_points",
    "for": "points_for",
    "against": "points_against",
    "percentage": "percentage",
    "goals_for": "goals_for",
    "behinds_for": "behinds_for",
    "goals_against": "goals_against",
    "behinds_against": "behinds_against",
}


def select_and_rename(rows, columns):
    if not rows:
        return pd.DataFrame(columns=list(columns.values()))
    df = pd.DataFrame(rows)
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"API response is missing columns: {missing}")
    return df[list(columns)].rename(columns=columns)


def strip_text(df, columns):
    for column in columns:
        df[column] = df[column].astype("string").str.strip()
    return df


def to_snowflake_format(df):
    df = df.reset_index(drop=True)
    df.columns = [column.upper() for column in df.columns]
    return df


def clean_teams(teams):
    df = select_and_rename(teams, TEAM_COLUMNS)
    df = df.drop_duplicates(subset="team_id", keep="last")
    df = strip_text(df, ["team_name", "abbreviation"])
    df["retirement_year"] = df["retirement_year"].where(df["retirement_year"] != 9999).astype("Int64")
    df["debut_year"] = df["debut_year"].astype("Int64")
    df["logo_url"] = LOGO_BASE_URL + df["logo_url"].astype("string")
    return to_snowflake_format(df)


def clean_games(games):
    df = select_and_rename(games, GAME_COLUMNS)
    df = df.drop_duplicates(subset="game_id", keep="last")

    total = len(df)
    df = df[df["complete_pct"] == 100]
    df = df.dropna(subset=["home_team_id", "away_team_id", "home_score", "away_score"])
    if total - len(df):
        logger.info("Removed %s games that are not finished yet", total - len(df))

    int_columns = [
        "game_id", "season", "round_number", "home_team_id", "away_team_id",
        "home_goals", "home_behinds", "home_score", "away_goals", "away_behinds", "away_score",
    ]
    df[int_columns] = df[int_columns].astype(int)
    df["winner_team_id"] = df["winner_team_id"].astype("Int64")

    valid_scores = (
        (df["home_score"] == df["home_goals"] * 6 + df["home_behinds"])
        & (df["away_score"] == df["away_goals"] * 6 + df["away_behinds"])
    )
    if (~valid_scores).sum():
        logger.warning("Removed %s games where the score did not match goals and behinds", (~valid_scores).sum())
    df = df[valid_scores].copy()

    df["match_datetime"] = pd.to_datetime(df["match_datetime"])
    df["updated_at"] = pd.to_datetime(df["updated_at"])
    df["is_final"] = df["is_final"].fillna(0).astype(int) > 0
    df["is_grand_final"] = df["is_grand_final"].fillna(0).astype(int) == 1
    df = strip_text(df, ["round_name", "timezone", "venue", "home_team", "away_team", "winner"])

    df = df.drop(columns="complete_pct").sort_values(["season", "match_datetime", "game_id"])
    return to_snowflake_format(df)


def clean_standings(standings):
    df = select_and_rename(standings, STANDING_COLUMNS)
    df = df.drop_duplicates(subset=["season", "team_id"], keep="last")
    df = strip_text(df, ["team_name"])
    df["percentage"] = df["percentage"].astype(float).round(2)
    int_columns = [column for column in df.columns if column not in ("team_name", "percentage")]
    df[int_columns] = df[int_columns].astype(int)
    df = df.sort_values(["season", "ladder_rank"])
    return to_snowflake_format(df)


def save_processed(dataframes):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in dataframes.items():
        df.to_csv(PROCESSED_DIR / f"{name.lower()}.csv", index=False)
