import logging

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

from src.config import SNOWFLAKE

logger = logging.getLogger(__name__)


def get_connection():
    settings = {key: value for key, value in SNOWFLAKE.items() if value}
    missing = [key for key in ("account", "user") if key not in settings]
    if "password" not in settings and "private_key_file" not in settings:
        missing.append("password or private key file")
    if missing:
        raise ValueError(f"Missing Snowflake settings in .env: {missing}")
    if "private_key_file" in settings:
        settings.pop("password", None)
        settings["authenticator"] = "SNOWFLAKE_JWT"
    return snowflake.connector.connect(**settings)


def clear_existing_rows(conn, table, seasons=None):
    cursor = conn.cursor()
    if seasons:
        placeholders = ", ".join(["%s"] * len(seasons))
        cursor.execute(f"DELETE FROM RAW.{table} WHERE SEASON IN ({placeholders})", list(seasons))
    else:
        cursor.execute(f"TRUNCATE TABLE RAW.{table}")
    cursor.close()


def load_table(conn, df, table, seasons=None):
    if df.empty:
        logger.warning("No rows to load into RAW.%s", table)
        return 0

    df = df.copy()
    df["LOADED_AT"] = pd.Timestamp.now(tz="UTC").tz_localize(None)

    clear_existing_rows(conn, table, seasons)
    success, _, rows, _ = write_pandas(
        conn,
        df,
        table_name=table,
        schema="RAW",
        use_logical_type=True,
    )
    if not success:
        raise RuntimeError(f"Loading RAW.{table} failed")

    logger.info("Loaded %s rows into RAW.%s", rows, table)
    return rows


def load_all(conn, teams, games, standings, seasons):
    load_table(conn, teams, "TEAMS")
    load_table(conn, games, "GAMES", seasons)
    load_table(conn, standings, "STANDINGS", seasons)
