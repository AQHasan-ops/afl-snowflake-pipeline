import argparse
import logging
import sys

from src import clean, extract, transform
from src.config import DEFAULT_YEARS


def parse_args():
    parser = argparse.ArgumentParser(description="AFL data pipeline: Squiggle API to Snowflake")
    parser.add_argument("--years", nargs="+", type=int, default=DEFAULT_YEARS, help="seasons to pull")
    parser.add_argument("--setup", action="store_true", help="create the warehouse, database, schemas and raw tables first")
    parser.add_argument("--no-snowflake", action="store_true", help="only extract and clean, save CSVs locally")
    parser.add_argument("--transform-only", action="store_true", help="skip the API and only rebuild the SQL layers")
    return parser.parse_args()


def run_transformations(conn):
    transform.run_folder(conn, "staging")
    transform.run_folder(conn, "reporting")
    return transform.run_checks(conn)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    args = parse_args()

    if not args.transform_only:
        teams, games, standings = extract.extract_all(args.years)
        teams_df = clean.clean_teams(teams)
        games_df = clean.clean_games(games)
        standings_df = clean.clean_standings(standings)
        clean.save_processed({"teams": teams_df, "games": games_df, "standings": standings_df})
        logging.info("Cleaned %s teams, %s games, %s ladder rows", len(teams_df), len(games_df), len(standings_df))

        if args.no_snowflake:
            logging.info("Skipping Snowflake, CSVs saved in data/processed")
            return

    from src import load

    conn = load.get_connection()
    try:
        if args.setup:
            transform.run_folder(conn, "setup")
        if not args.transform_only:
            load.load_all(conn, teams_df, games_df, standings_df, args.years)
        failed = run_transformations(conn)
    finally:
        conn.close()

    if failed:
        logging.error("Pipeline finished with %s failed checks", len(failed))
        sys.exit(1)
    logging.info("Pipeline finished successfully")


if __name__ == "__main__":
    main()
