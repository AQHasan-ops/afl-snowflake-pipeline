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


def season_filter(seasons):
    if not seasons:
        return "", []
    placeholders = ", ".join(["%s"] * len(seasons))
    return f" WHERE SEASON IN ({placeholders})", list(seasons)


def count_rows(conn, table, seasons=None):
    where, params = season_filter(seasons)
    cursor = conn.cursor()
    count = cursor.execute(f"SELECT COUNT(*) FROM RAW.{table}{where}", params).fetchone()[0]
    cursor.close()
    return count


def upload_to_temp_table(conn, df, temp_table):
    conn.cursor().execute(f"DROP TABLE IF EXISTS RAW.{temp_table}")
    success, _, rows, _ = write_pandas(
        conn,
        df,
        table_name=temp_table,
        schema="RAW",
        auto_create_table=True,
        table_type="temporary",
        use_logical_type=True,
    )
    if not success or rows != len(df):
        raise RuntimeError(f"Upload to RAW.{temp_table} failed, RAW tables were not changed")


def replace_rows(conn, table, temp_table, columns, seasons=None):
    where, params = season_filter(seasons)
    column_list = ", ".join(columns)
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN")
        cursor.execute(f"DELETE FROM RAW.{table}{where}", params)
        cursor.execute(f"INSERT INTO RAW.{table} ({column_list}) SELECT {column_list} FROM RAW.{temp_table}")
        cursor.execute("COMMIT")
    except Exception:
        cursor.execute("ROLLBACK")
        raise
    finally:
        cursor.close()


def load_table(conn, df, table, seasons=None):
    if df.empty:
        logger.warning("No rows to load into RAW.%s", table)
        return 0

    df = df.copy()
    df["LOADED_AT"] = pd.Timestamp.now(tz="UTC").tz_localize(None)

    temp_table = f"{table}_NEW"
    upload_to_temp_table(conn, df, temp_table)
    replace_rows(conn, table, temp_table, list(df.columns), seasons)

    loaded = count_rows(conn, table, seasons)
    if loaded != len(df):
        raise RuntimeError(f"RAW.{table} has {loaded} rows but the cleaned data has {len(df)}")

    logger.info("Loaded %s rows into RAW.%s (matches cleaned data)", loaded, table)
    return loaded


def load_all(conn, teams, games, standings, seasons):
    load_table(conn, teams, "TEAMS")
    load_table(conn, games, "GAMES", seasons)
    load_table(conn, standings, "STANDINGS", seasons)
