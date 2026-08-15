import os
from storage.snowflake_loader import get_connection


def _get_query(filename: str) -> str:
    """Reads a SQL query file from the snowflake_queries directory."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_path = os.path.join(project_root, "snowflake_queries", filename)
    with open(sql_path, "r", encoding="utf-8") as file:
        return file.read()


def silver_to_gold(conn=None) -> None:
    """
    Executes the Gold aggregation query from snowflake_queries/gold_load.sql
    to aggregate staged flight metrics into OPENSKY_ETL.FINAL.BUSINESS_READY_FLIGHT_ANALYTICS.
    """
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    print("Executing Gold aggregation from snowflake_queries/gold_load.sql...")
    query = _get_query("gold_load.sql")
    cursor = conn.cursor()
    cursor.execute(query)
    cursor.close()

    if should_close:
        conn.close()

    print("  -> Gold transformation complete.")