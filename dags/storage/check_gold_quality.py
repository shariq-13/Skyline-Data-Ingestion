import os
from storage.snowflake_loader import get_connection


def _get_query(filename: str) -> str:
    """Reads a SQL query file from the snowflake_queries directory."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_path = os.path.join(project_root, "snowflake_queries", filename)
    with open(sql_path, "r", encoding="utf-8") as file:
        return file.read()


def check_gold_quality(conn=None) -> None:
    """
    Executes data quality checks from snowflake_queries/check_gold_quality.sql
    to ensure records exist in OPENSKY_ETL.FINAL.BUSINESS_READY_FLIGHT_ANALYTICS.
    """
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    print("Executing Gold Data Quality check from snowflake_queries/check_gold_quality.sql...")
    
    query = _get_query("check_gold_quality.sql")
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        result = cursor.fetchone()
        row_count = result[0] if result else 0

        if row_count == 0:
            raise ValueError(
                "Data Quality Check Failed: OPENSKY_ETL.FINAL.BUSINESS_READY_FLIGHT_ANALYTICS returned 0 records."
            )

        print(f"  -> Data Quality Passed: {row_count} rows verified in Gold layer.")

    finally:
        cursor.close()
        if should_close:
            conn.close()