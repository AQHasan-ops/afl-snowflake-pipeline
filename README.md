# AFL Snowflake Pipeline

Personal project, still in progress.

A small pipeline that pulls AFL data from the Squiggle API, cleans it with Python and loads it into Snowflake. SQL then turns it into tables that are ready for reporting.

Tools: Python, REST API, Snowflake, SQL

## How it works

- `extract.py` gets teams, games and ladder data for each season from the Squiggle API. The raw JSON is saved in `data/raw` and reused on the next run. Use `--refresh` to download it again.
- `clean.py` renames columns, fixes types, removes duplicates and unfinished games, and checks that scores add up.
- `load.py` uploads the cleaned data to a temporary table first. The RAW table is only changed after the upload works. The delete and insert run in one transaction, so a failed load leaves the old data in place. After loading, it checks that the row count in Snowflake matches the cleaned data.
- `transform.py` runs the SQL files in `sql/staging` and `sql/reporting`, then runs the checks in `sql/checks`.

## Snowflake layers

- RAW: cleaned data from the API
- STAGING: views with extra columns like margin and total score
- REPORTING: the final tables

Reporting tables:

- `TEAM_SEASON_SUMMARY`: one row per team per season (wins, averages, ladder spot, premiers)
- `FCT_TEAM_GAMES`: one row per team per game
- `TEAM_FORM`: rolling form over the last 5 games
- `VENUE_SUMMARY`: scoring and home wins by venue

Team totals in `TEAM_SEASON_SUMMARY` include finals. Ladder columns (rank, premiership points, percentage) only cover the home and away season.

## Checks

Each file in `sql/checks` should return no rows. The pipeline fails if one does.

- no duplicate games in `RAW.GAMES`
- every score equals goals x 6 + behinds
- every game has exactly two team rows
- every team in a game exists in the teams table
- every ladder has 18 teams
- home and away wins, losses, draws and points match the official ladder from the API

## Results

Last run: 5 seasons (2022 to 2026), 1073 games, 90 ladder rows. All checks passed.

I also checked a few team totals by hand against the raw JSON (Fremantle 2026, Brisbane 2024, Collingwood 2023, Geelong 2022). All of them matched.

2026 top 8 from `TEAM_SEASON_SUMMARY` (includes finals):

| Rank | Team | Played | W | L | D | Win % | Avg margin | Premier |
|---|---|---|---|---|---|---|---|---|
| 1 | Fremantle | 27 | 21 | 6 | 0 | 77.8 | 22.5 | |
| 2 | Sydney | 25 | 19 | 6 | 0 | 76.0 | 28.6 | |
| 3 | Brisbane Lions | 27 | 19 | 8 | 0 | 70.4 | 17.1 | Yes |
| 4 | Hawthorn | 25 | 16 | 7 | 2 | 64.0 | 16.1 | |
| 5 | Geelong | 25 | 16 | 9 | 0 | 64.0 | 18.0 | |
| 6 | Adelaide | 25 | 16 | 9 | 0 | 64.0 | 11.6 | |
| 7 | Melbourne | 24 | 15 | 9 | 0 | 62.5 | 7.6 | |
| 8 | Western Bulldogs | 25 | 14 | 10 | 1 | 56.0 | -4.4 | |

## Setup

Snowflake login uses a key pair instead of a password, because password logins need MFA. I made an RSA key and added the public key to my user with `ALTER USER ... SET RSA_PUBLIC_KEY`. The path to the private key goes in `.env`. Neither the key nor `.env` is in the repo.

`.env` needs the account (`ORGNAME-ACCOUNTNAME`), the login name and the key path. See `.env.example`.

Key pair login breaks if the computer clock is off by more than about a minute.

## Running

```
pip install -r requirements.txt
python main.py --setup
python main.py --years 2025 2026
python main.py --refresh
python main.py --no-snowflake
pytest
```

`--setup` creates the warehouse, database and tables the first time. `--refresh` downloads fresh data from the API. `--no-snowflake` only saves CSVs locally.

## To do

- Use MERGE instead of delete and insert
- Add the tips endpoint
- Run it on a schedule
- Clean up venue names

Data from https://api.squiggle.com.au
