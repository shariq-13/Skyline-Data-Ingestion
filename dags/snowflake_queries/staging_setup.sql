-- ============================================================
-- Step 4.2: Run once in Snowflake to set up Silver & Gold Layers
-- ============================================================

USE WAREHOUSE OPENSKY_WH;

-- Create database for processed data
CREATE DATABASE IF NOT EXISTS OPENSKY_ETL;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS OPENSKY_ETL.STAGED;
CREATE SCHEMA IF NOT EXISTS OPENSKY_ETL.FINAL;

-- Create Silver Staging Table
CREATE TABLE IF NOT EXISTS OPENSKY_ETL.STAGED.STAGED_DATA (
    icao24          VARCHAR(50),
    callsign        VARCHAR(50),
    origin_country  VARCHAR(100),
    time_position   TIMESTAMP_NTZ,
    longitude       FLOAT,
    latitude        FLOAT,
    baro_altitude   FLOAT,
    velocity        FLOAT,
    on_ground       BOOLEAN,
    ingested_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Create Gold Analytical Summary Table
CREATE TABLE IF NOT EXISTS OPENSKY_ETL.FINAL.FINAL_DATA (
    flight_hour           TIMESTAMP_NTZ,
    origin_country        VARCHAR(100),
    total_unique_flights  INT,
    avg_velocity_ms       FLOAT,
    avg_altitude_meters   FLOAT,
    max_velocity_ms       FLOAT,
    updated_at            TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);