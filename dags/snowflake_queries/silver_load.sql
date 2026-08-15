INSERT INTO OPENSKY_ETL.STAGED.STAGED_DATA (
    icao24, callsign, origin_country, time_position,
    longitude, latitude, baro_altitude, velocity, on_ground, ingested_at
)
WITH raw_flattened AS (
    SELECT 
        f.value[0]::STRING                            AS icao24,
        TRIM(f.value[1]::STRING)                      AS callsign,
        UPPER(TRIM(f.value[2]::STRING))               AS origin_country,
        TO_TIMESTAMP_NTZ(f.value[3]::INT)             AS time_position,
        f.value[5]::FLOAT                             AS longitude,
        f.value[6]::FLOAT                             AS latitude,
        f.value[7]::FLOAT                             AS baro_altitude,
        f.value[9]::FLOAT                             AS velocity,
        f.value[8]::BOOLEAN                           AS on_ground,
        ingested_at,
        ROW_NUMBER() OVER (
            PARTITION BY f.value[0]::STRING, f.value[3]::INT 
            ORDER BY ingested_at DESC
        ) AS row_num
    FROM OPENSKY_RAW_ETL.RAW.RAW_DATA,
    LATERAL FLATTEN(input => raw_data:states) f
    WHERE f.value[0] IS NOT NULL 
      AND f.value[3] IS NOT NULL
)
SELECT 
    icao24, callsign, origin_country, time_position,
    longitude, latitude, baro_altitude, velocity, on_ground, ingested_at
FROM raw_flattened
WHERE row_num = 1;