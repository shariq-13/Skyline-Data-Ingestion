import boto3  # aws sdk for python
import json
from datetime import datetime

# S3 Bucket Name and AWS Region hardcoded directly in the file
BUCKET_NAME = "opensky-raw-etl"
REGION      = "us-east-1"

# S3 client - reads AWS credentials automatically (from IAM Role or AWS CLI config)
s3 = boto3.client("s3", region_name=REGION)


def save_to_s3(source_name, records):
    """
    Save a list of flight records to S3 as a JSON file.

    S3 path structure:
      raw/{source}/year=YYYY/month=MM/day=DD/fetch_TIMESTAMP.json

    Example:
      raw/opensky_states/year=2026/month=08/day=11/fetch_20260811_143000.json
    """

    now = datetime.now()

    # Build the S3 key (the file path inside the bucket)
    s3_key = (
        f"raw/{source_name}/"
        f"year={now.strftime('%Y')}/"
        f"month={now.strftime('%m')}/"
        f"day={now.strftime('%d')}/"
        f"fetch_{now.strftime('%Y%m%d_%H%M%S')}.json"
    )

    # Convert flight records list to a JSON string
    content = json.dumps(records, indent=2)

    # Upload to S3
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=content,
        ContentType="application/json",
    )

    print(f"  Saved to s3://{BUCKET_NAME}/{s3_key}")
    print(f"  Records saved: {len(records)}")
    return s3_key


def save_all_to_s3(results):
    """
    results is a dict like: { "opensky_states": [...] }
    Loop through each source and save to S3.
    """

    for source_name, records in results.items():
        print(f"\nSaving {source_name} to S3 ...")
        save_to_s3(source_name, records)