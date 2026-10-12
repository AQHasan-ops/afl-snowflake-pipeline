# AFL Snowflake Pipeline

Personal project, still in progress.

A small pipeline that pulls AFL data from the Squiggle API, cleans it with Python and loads it into Snowflake. SQL then turns it into tables that are ready for reporting.

Tools: Python, REST API, Snowflake, SQL

## How it works

- `extract.py` gets teams, games and ladder data for each season from the Squiggle API. The raw JSON is saved in `data/raw`.
- `clean.py` renames columns, fixes types, removes duplicates and unfinished games, and checks that scores add up.
- `load.py` loads the cleaned data into the RAW schema in Snowflake.
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

## Running

Snowflake details go in `.env` (see `.env.example`).

```
pip install -r requirements.txt
python main.py --setup
python main.py --years 2025 2026
python main.py --no-snowflake
pytest
```

`--setup` creates the warehouse, database and tables the first time. `--no-snowflake` only saves CSVs locally.

## To do

- Use MERGE instead of delete and insert
- Add the tips endpoint
- Run it on a schedule
- Build a dashboard
- Clean up venue names

Data from https://api.squiggle.com.au
