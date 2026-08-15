"""
OpenSky Flight Tracking ETL Pipeline - Airflow DAG

Prerequisites:
  - Airflow Connections configured in Admin > Connections:
      1. aws_default        (Amazon S3 credentials)
      2. snowflake_default  (Snowflake credentials for OPENSKY_ETL DB)
      3. slack_webhook      (Incoming Webhook URL for alerts)
  - Required Provider Packages:
      pip install apache-airflow-providers-snowflake apache-airflow-providers-amazon apache-airflow-providers-slack
"""

from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.slack.hooks.slack_webhook import SlackWebhookHook
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.utils.email import send_email

# Custom project module imports
from ingestion.fetcher import fetch_live_data
from ingestion.scraper import scrape_flight_data
from storage.check_gold_quality import check_gold_quality
from storage.gold_loader import silver_to_gold
from storage.s3_storage import save_all_to_s3
from storage.silver_loader import bronze_to_silver
from storage.snowflake_loader import save_all_to_snowflake


def notify_failure(context):
    """Failure callback hook for Airflow task monitoring via Slack & Email."""
    ti = context.get("task_instance")
    task_id = ti.task_id
    dag_id = ti.dag_id
    logical_date = context.get("logical_date")
    exception = context.get("exception")
    log_url = ti.log_url

    alert_message = f"""
    :red_circle: *Airflow Task Failure Alert*
    *DAG*: `{dag_id}`
    *Task*: `{task_id}`
    *Logical Date*: `{logical_date}`
    *Exception*: `{exception}`
    *Logs*: <{log_url}|View Airflow Task Logs>
    """

    # 1. Dispatch Slack Alert
    try:
        slack_hook = SlackWebhookHook(slack_webhook_conn_id="slack_webhook")
        slack_hook.send_text(alert_message)
    except Exception as e:
        print(f"Failed to dispatch Slack alert: {e}")

    # 2. Dispatch Email Alert
    try:
        email_recipient = "admin@yourdomain.com"
        subject = f"AIRFLOW FAILURE: [{dag_id}] {task_id}"
        html_body = alert_message.replace("\n", "<br>")
        send_email(to=email_recipient, subject=subject, html_content=html_body)
    except Exception as e:
        print(f"Failed to dispatch Email alert: {e}")


default_args = {
    "owner": "SHARIQ",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": notify_failure,
}


@dag(
    dag_id="OpenSky_Radar_Pipeline",
    description="Fetch live flight data, land in S3 + Snowflake Medallion layers",
    schedule=None,
    start_date=datetime(2026, 8, 1),
    catchup=False,
    default_args=default_args,
    tags=["opensky", "s3", "snowflake", "medallion"],
)
def opensky_flight_etl():

    @task
    def fetch_api():
        """Step 1: Poll OpenSky API for live state vectors."""
        from ingestion.fetcher import fetch_live_data

        payload = fetch_live_data()
        if not payload or not payload.get("states"):
            raise ValueError("Data Quality Check Failed: API returned 0 flight states.")
        return payload

    @task
    def scrape_data(raw_data: dict):
        """Step 2: Parse raw state vectors into clean dictionary records."""
       
        scraped = scrape_flight_data(raw_data)
        if len(scraped) == 0:
            raise ValueError("Data Quality Check Failed: Scraped state records count is 0.")
        return scraped

    @task
    def save_to_s3(data: list):
        """Step 3: Upload clean data to S3 partitioned by date and hour."""
        return save_all_to_s3(data)

    @task
    def load_bronze(s3_key: str):
        """Step 4: Execute COPY INTO Bronze RAW_DATA table in Snowflake."""
        conn = SnowflakeHook(snowflake_conn_id="snowflake_default").get_conn()
        save_all_to_snowflake(conn=conn)

    @task
    def load_silver():
        """Step 5: Deduplicate and parse into Silver STAGED_DATA table."""
        conn = SnowflakeHook(snowflake_conn_id="snowflake_default").get_conn()
        bronze_to_silver(conn=conn)

    @task
    def load_gold():
        """Step 6: Aggregate KPIs into Gold FINAL_DATA table for Power BI."""
        conn = SnowflakeHook(snowflake_conn_id="snowflake_default").get_conn()
        silver_to_gold(conn=conn)

    @task
    def check_gold_dq():
     """Step 7: Assert Gold table contains fresh data."""
     conn = SnowflakeHook(snowflake_conn_id="snowflake_default").get_conn()
     check_gold_quality(conn=conn)

    # Task Data Flow & Dependency Pipeline
    fetched = fetch_api()
    scraped = scrape_data(fetched)
    landed  = save_to_s3(scraped)
    
    # Database transformations execution sequence
    bronze  = load_bronze(landed)
    silver  = load_silver()
    gold    = load_gold()
    dq      = check_gold_dq()

    # Explicit Task Order Constraints
    bronze >> silver >> gold >> dq


opensky_flight_etl()