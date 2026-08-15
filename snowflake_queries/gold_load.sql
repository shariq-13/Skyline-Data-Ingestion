CREATE OR REPLACE TABLE OPENSKY_ETL.FINAL.FINAL_DATA AS
SELECT 
    DATE_TRUNC('HOUR', time_position) AS flight_hour,
    origin_country,
    COUNT(DISTINCT icao24) AS total_unique_flights,
    ROUND(AVG(velocity), 2) AS avg_velocity_ms,
    ROUND(AVG(baro_altitude), 2) AS avg_altitude_meters,
    MAX(velocity) AS max_velocity_ms,
    CURRENT_TIMESTAMP() AS updated_at
FROM OPENSKY_ETL.STAGED.STAGED_DATA
WHERE time_position >= DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY 1, 2;