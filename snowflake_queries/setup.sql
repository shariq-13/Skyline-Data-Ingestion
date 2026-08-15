-- ============================================================
-- Step 4.1: Run once in Snowflake to set up the Bronze Layer
-- ============================================================

-- Create the raw database
CREATE DATABASE IF NOT EXISTS OPENSKY_RAW_ETL;

-- Create raw schema
CREATE SCHEMA IF NOT EXISTS OPENSKY_RAW_ETL.RAW;

-- Create virtual warehouse
CREATE WAREHOUSE IF NOT EXISTS OPENSKY_WH
    WAREHOUSE_SIZE  = 'XSMALL'
    AUTO_SUSPEND    = 60
    AUTO_RESUME     = TRUE;

USE WAREHOUSE OPENSKY_WH;

-- Create file format for raw JSON payload
CREATE OR REPLACE FILE FORMAT OPENSKY_RAW_ETL.RAW.JSON_FORMAT
    TYPE = 'JSON'
    STRIP_OUTER_ARRAY = TRUE;

-- Create storage integration for AWS S3 IAM Role Access
CREATE OR REPLACE STORAGE INTEGRATION S3_OPENSKY_INTEGRATION
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = 'S3'
    ENABLED = TRUE
    STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/SnowflakeS3Role'
    STORAGE_ALLOWED_LOCATIONS = ('s3://your-opensky-raw-bucket/raw/opensky/');

-- Create external stage pointing to S3 raw partition path
CREATE OR REPLACE STAGE OPENSKY_RAW_ETL.RAW.S3_OPENSKY_STAGE
    URL = 's3://your-opensky-raw-bucket/raw/opensky/'
    STORAGE_INTEGRATION = S3_OPENSKY_INTEGRATION
    FILE_FORMAT = OPENSKY_RAW_ETL.RAW.JSON_FORMAT;

-- Create the raw flight data table (Bronze)
CREATE TABLE IF NOT EXISTS OPENSKY_RAW_ETL.RAW.RAW_DATA (
    raw_data     VARIANT,
    ingested_at  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);