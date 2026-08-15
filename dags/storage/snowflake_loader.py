import os
from pathlib import Path


def get_connection():
    """Returns Snowflake connection using Airflow's SnowflakeHook."""
    from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
    return SnowflakeHook(snowflake_conn_id="snowflake_default").get_conn()


def _get_query(filename: str) -> str:
    """Reads SQL query file from dags/snowflake_queries/."""
    sql_path = Path(__file__).resolve().parent.parent / "snowflake_queries" / filename
    with open(sql_path, "r", encoding="utf-8") as f:
        return f.read()


def save_all_to_snowflake(conn=None) -> None:
    """Executes bronze.sql to load raw S3 JSON files into Bronze layer."""
    owns_conn = conn is None
    conn = conn or get_connection()

    query = _get_query("bronze_load.sql")
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    cursor.close()

    if owns_conn:
        conn.close()

    print("  -> Bronze load complete.")