import boto3  # aws sdk for python
import json
from datetime import datetime

# S3 Bucket Name and AWS Region hardcoded directly in the file
BUCKET_NAME = "opensky-raw-etl"
REGION      = "us-east-1"

# S3 client - reads AWS credentials automatically (from IAM Role or AWS CLI config)
s3 = boto3.client("s3", region_name=REGION)


def save_to_s3(records):
    """
    Save flight records directly inside raw/opensky_states/:
      raw/opensky_states/year=YYYY/month=MM/day=DD/fetch_TIMESTAMP.json
    """
    now = datetime.now()

    s3_key = (
        f"raw/opensky_states/"
        f"year={now.strftime('%Y')}/"
        f"month={now.strftime('%m')}/"
        f"day={now.strftime('%d')}/"
        f"fetch_{now.strftime('%Y%m%d_%H%M%S')}.json"
    )

    content = json.dumps(records, indent=2)

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=content,
        ContentType="application/json",
    )

    print(f"  Saved to s3://{BUCKET_NAME}/{s3_key}")
    print(f"  Records saved: {len(records)}")
    return s3_key


def save_all_to_s3(data):
    """
    Accepts data list (or dict) and saves directly to raw/opensky_states/.
    Returns s3_key string for Airflow XCom.
    """
    if isinstance(data, dict):
        data = list(data.values())[0]

    return save_to_s3(data)