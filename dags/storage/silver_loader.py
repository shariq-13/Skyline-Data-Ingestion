from pathlib import Path
from storage.snowflake_loader import get_connection


def _get_query(filename: str) -> str:
    """Reads SQL query file from dags/snowflake_queries/."""
    sql_path = Path(__file__).resolve().parent.parent / "snowflake_queries" / filename
    with open(sql_path, "r", encoding="utf-8") as f:
        return f.read()


def bronze_to_silver(conn=None) -> None:
    """Executes silver_load.sql to transform raw data into Silver layer."""
    owns_conn = conn is None
    conn = conn or get_connection()

    query = _get_query("silver_load.sql")
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    cursor.close()

    if owns_conn:
        conn.close()

    print("  -> Silver transformation complete.")