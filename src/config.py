import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
SQL_DIR = BASE_DIR / "sql"

API_URL = "https://api.squiggle.com.au/"
USER_AGENT = os.getenv("SQUIGGLE_USER_AGENT", "afl-snowflake-pipeline student project")
LOGO_BASE_URL = "https://squiggle.com.au"

DEFAULT_YEARS = [2022, 2023, 2024, 2025, 2026]

PRIVATE_KEY_FILE = os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE")

SNOWFLAKE = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "private_key_file": str(BASE_DIR / PRIVATE_KEY_FILE) if PRIVATE_KEY_FILE else None,
    "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "AFL_WH"),
    "database": os.getenv("SNOWFLAKE_DATABASE", "AFL_DB"),
}
