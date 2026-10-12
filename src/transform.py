import logging

from src.config import SQL_DIR

logger = logging.getLogger(__name__)


def run_sql_file(conn, path):
    logger.info("Running %s/%s", path.parent.name, path.name)
    for cursor in conn.execute_string(path.read_text(encoding="utf-8")):
        cursor.close()


def run_folder(conn, folder):
    for path in sorted((SQL_DIR / folder).glob("*.sql")):
        run_sql_file(conn, path)


def run_checks(conn):
    failed = []
    for path in sorted((SQL_DIR / "checks").glob("*.sql")):
        cursor = conn.cursor()
        rows = cursor.execute(path.read_text(encoding="utf-8")).fetchall()
        cursor.close()
        if rows:
            failed.append(path.stem)
            logger.error("Check failed: %s (%s bad rows)", path.stem, len(rows))
        else:
            logger.info("Check passed: %s", path.stem)
    return failed
