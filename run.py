from ingestion.fetcher import fetch_live_data
from storage.s3_storage import save_all_to_s3
from storage.snowflake_loader import save_all_to_snowflake
from storage.silver_loader import bronze_to_silver
from storage.gold_loader import silver_to_gold


def main():
    # print("=== Step 1: Fetching OpenSky Live Flight Data ===")
    # results = fetch_live_data()

    # print("\n=== Step 2: Saving Raw JSON to S3 ===")
    # save_all_to_s3(results)

    print("\n=== Step 3: Loading Raw Data into Snowflake (Bronze) ===")
    save_all_to_snowflake()

    print("\n=== Step 4: Bronze → Silver (Flight Deduplication) ===")
    bronze_to_silver()

    print("\n=== Step 5: Silver → Gold (Flight Metrics Aggregation) ===")
    silver_to_gold()

    print("\nDone!")


if __name__ == "__main__":
    main()