import pandas as pd
import pytest

from src import clean


def make_game(**overrides):
    game = {
        "id": 1,
        "year": 2024,
        "round": 1,
        "roundname": "Round 1",
        "date": "2024-03-14 19:30:00",
        "tz": "+11:00",
        "venue": " M.C.G. ",
        "hteamid": 3,
        "hteam": "Carlton",
        "ateamid": 14,
        "ateam": "Richmond",
        "hgoals": 12,
        "hbehinds": 14,
        "hscore": 86,
        "agoals": 12,
        "abehinds": 9,
        "ascore": 81,
        "winnerteamid": 3,
        "winner": "Carlton",
        "is_final": 0,
        "is_grand_final": 0,
        "complete": 100,
        "updated": "2024-03-14 22:14:45",
    }
    game.update(overrides)
    return game


def test_clean_games_renames_and_uppercases_columns():
    df = clean.clean_games([make_game()])
    assert "HOME_SCORE" in df.columns
    assert "COMPLETE_PCT" not in df.columns
    assert df.loc[0, "VENUE"] == "M.C.G."


def test_clean_games_converts_types():
    df = clean.clean_games([make_game()])
    assert pd.api.types.is_datetime64_any_dtype(df["MATCH_DATETIME"])
    assert df.loc[0, "IS_FINAL"] == False
    assert df.loc[0, "HOME_SCORE"] == 86


def test_clean_games_removes_unfinished_games():
    games = [make_game(), make_game(id=2, complete=0, hscore=None, ascore=None)]
    df = clean.clean_games(games)
    assert list(df["GAME_ID"]) == [1]


def test_clean_games_removes_duplicates():
    df = clean.clean_games([make_game(), make_game()])
    assert len(df) == 1


def test_clean_games_removes_bad_scores():
    df = clean.clean_games([make_game(hscore=100)])
    assert df.empty


def test_clean_games_handles_draw():
    draw = make_game(hgoals=10, hbehinds=10, hscore=70, agoals=10, abehinds=10, ascore=70, winnerteamid=None, winner=None)
    df = clean.clean_games([draw])
    assert pd.isna(df.loc[0, "WINNER_TEAM_ID"])


def test_clean_games_flags_finals():
    df = clean.clean_games([make_game(is_final=6, is_grand_final=1)])
    assert df.loc[0, "IS_FINAL"] == True
    assert df.loc[0, "IS_GRAND_FINAL"] == True


def test_clean_teams_sets_active_teams_retirement_to_null():
    teams = [{"id": 1, "name": "Adelaide", "abbrev": "ADE", "debut": 1991, "retirement": 9999, "logo": "/logo.png"}]
    df = clean.clean_teams(teams)
    assert pd.isna(df.loc[0, "RETIREMENT_YEAR"])
    assert df.loc[0, "LOGO_URL"].startswith("https://")


def test_clean_standings_rounds_percentage():
    standings = [{
        "year": 2024, "id": 16, "name": "Sydney", "rank": 1, "played": 23, "wins": 17, "losses": 6,
        "draws": 0, "pts": 68, "for": 2242, "against": 1769, "percentage": 126.738270209158,
        "goals_for": 328, "behinds_for": 274, "goals_against": 252, "behinds_against": 257,
    }]
    df = clean.clean_standings(standings)
    assert df.loc[0, "PERCENTAGE"] == 126.74
    assert df.loc[0, "PREMIERSHIP_POINTS"] == 68


def test_missing_api_column_raises_error():
    game = make_game()
    del game["venue"]
    with pytest.raises(ValueError):
        clean.clean_games([game])


def test_empty_input_returns_empty_dataframe():
    df = clean.clean_standings([])
    assert df.empty
