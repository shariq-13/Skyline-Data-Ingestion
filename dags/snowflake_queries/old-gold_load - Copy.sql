TRUNCATE TABLE OPENSKY_ETL.FINAL.FINAL_DATA;

INSERT INTO OPENSKY_ETL.FINAL.FINAL_DATA (
    flight_hour,
    origin_country,
    total_unique_flights,
    avg_velocity_ms,
    avg_altitude_meters,
    max_velocity_ms,
    updated_at
)
SELECT 
    DATE_TRUNC('HOUR', time_position) AS flight_hour,
    origin_country,
    COUNT(DISTINCT icao24)            AS total_unique_flights,
    ROUND(AVG(velocity), 2)           AS avg_velocity_ms,
    ROUND(AVG(baro_altitude), 2)       AS avg_altitude_meters,
    MAX(velocity)                     AS max_velocity_ms,
    CURRENT_TIMESTAMP()               AS updated_at
FROM OPENSKY_ETL.STAGED.STAGED_DATA
WHERE time_position IS NOT NULL
GROUP BY 1, 2;