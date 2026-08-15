INSERT INTO OPENSKY_ETL.STAGED.STAGED_DATA (
    icao24, callsign, origin_country, time_position,
    longitude, latitude, baro_altitude, velocity, on_ground, ingested_at
)
WITH raw_flattened AS (
    SELECT 
        COALESCE(f.value[0]::STRING, raw_data[0]::STRING, raw_data:icao24::STRING) AS icao24,
        TRIM(COALESCE(f.value[1]::STRING, raw_data[1]::STRING, raw_data:callsign::STRING)) AS callsign,
        UPPER(TRIM(COALESCE(f.value[2]::STRING, raw_data[2]::STRING, raw_data:origin_country::STRING))) AS origin_country,
        TO_TIMESTAMP_NTZ(COALESCE(f.value[3]::INT, raw_data[3]::INT, raw_data:time_position::INT)) AS time_position,
        COALESCE(f.value[5]::FLOAT, raw_data[5]::FLOAT, raw_data:longitude::FLOAT) AS longitude,
        COALESCE(f.value[6]::FLOAT, raw_data[6]::FLOAT, raw_data:latitude::FLOAT) AS latitude,
        COALESCE(f.value[7]::FLOAT, raw_data[7]::FLOAT, raw_data:baro_altitude::FLOAT) AS baro_altitude,
        COALESCE(f.value[9]::FLOAT, raw_data[9]::FLOAT, raw_data:velocity::FLOAT) AS velocity,
        COALESCE(f.value[8]::BOOLEAN, raw_data[8]::BOOLEAN, raw_data:on_ground::BOOLEAN) AS on_ground,
        ingested_at,
        ROW_NUMBER() OVER (
            PARTITION BY 
                COALESCE(f.value[0]::STRING, raw_data[0]::STRING, raw_data:icao24::STRING),
                COALESCE(f.value[3]::INT, raw_data[3]::INT, raw_data:time_position::INT)
            ORDER BY ingested_at DESC
        ) AS row_num
    FROM OPENSKY_RAW_ETL.RAW.RAW_DATA,
    LATERAL FLATTEN(input => COALESCE(raw_data:states, raw_data), OUTER => TRUE) f
)
SELECT 
    icao24, callsign, origin_country, time_position,
    longitude, latitude, baro_altitude, velocity, on_ground, ingested_at
FROM raw_flattened
WHERE row_num = 1
  AND icao24 IS NOT NULL;