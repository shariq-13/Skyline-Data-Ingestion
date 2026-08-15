-- Checks that records exist in the Gold analytics table post-load
SELECT COUNT(1) AS total_gold_records
FROM OPENSKY_ETL.FINAL.BUSINESS_READY_FLIGHT_ANALYTICS;