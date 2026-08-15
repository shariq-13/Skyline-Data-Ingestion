from storage.snowflake_loader import get_connection, _get_query


def silver_to_gold(conn=None) -> None:
    """Executes gold_load.sql to aggregate Silver data into Gold layer."""
    owns_conn = conn is None
    conn = conn or get_connection()

    print("Executing Gold aggregation from snowflake_queries/gold_load.sql...")
    query = _get_query("gold_load.sql")
    cursor = conn.cursor()

    try:
        # Split multi-statement SQL files by semicolon
        statements = [stmt.strip() for stmt in query.split(";") if stmt.strip()]
        for stmt in statements:
            cursor.execute(stmt)

        conn.commit()
        print("  -> Gold transformation complete.")

    except Exception as e:
        conn.rollback()
        print(f"Error executing Gold transformation: {e}")
        raise e

    finally:
        cursor.close()
        if owns_conn:
            conn.close()