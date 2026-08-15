import os
from storage.snowflake_loader import get_connection


def _get_query(filename: str) -> str:
    """Reads a SQL query file from the snowflake_queries directory."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_path = os.path.join(project_root, "snowflake_queries", filename)
    with open(sql_path, "r", encoding="utf-8") as file:
        return file.read()


def bronze_to_silver(conn=None) -> None:
    """
    Executes the Silver transformation query from snowflake_queries/silver_load.sql
    to deduplicate raw flight data into OPENSKY_ETL.STAGED.STAGED_DATA.
    """
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    print("Executing Silver transform from snowflake_queries/silver_load.sql...")
    query = _get_query("silver_load.sql")
    cursor = conn.cursor()
    cursor.execute(query)
    cursor.close()

    if should_close:
        conn.close()

    print("  -> Silver transformation complete.")