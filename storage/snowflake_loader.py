import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()


# Snowflake connection config for OpenSky ETL
SNOWFLAKE_CONFIG = {
    "account":   "NHZOCAW-EXC99808",
    "user":      "BILAL03",
    "password":  os.getenv("SNOWFLAKE_PASSWORD"),
    "warehouse": "NEWS_WH",
    "database":  "NEWS_AI_ETL",
    "schema":    "RAW",
    "role":      "SYSADMIN",
}



def get_connection():
    """Establishes and returns a connection to Snowflake."""
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    return conn


def _get_query(filename: str) -> str:
    """Reads a SQL query file from the snowflake_queries directory."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_path = os.path.join(project_root, "snowflake_queries", filename)
    with open(sql_path, "r", encoding="utf-8") as file:
        return file.read()


def save_all_to_snowflake(conn=None) -> None:
    """
    Executes the COPY INTO query from bronze_load.sql to load raw S3 JSON files
    into OPENSKY_RAW_ETL.RAW.RAW_DATA.
    """
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    print("Executing Bronze load from snowflake_queries/bronze_load.sql...")
    query = _get_query("bronze_load.sql")
    cursor = conn.cursor()
    cursor.execute(query)
    cursor.close()

    if should_close:
        conn.close()

    print("  -> Bronze load complete.")