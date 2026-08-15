TRUNCATE TABLE OPENSKY_ETL.FINAL.BUSINESS_READY_FLIGHT_ANALYTICS;

INSERT INTO OPENSKY_ETL.FINAL.BUSINESS_READY_FLIGHT_ANALYTICS (
    snapshot_hour,
    origin_country,
    spatial_sector,
    sector_center_lat,
    sector_center_lon,
    flight_phase,
    unique_aircraft_count,
    active_callsigns_count,
    airborne_aircraft_count,
    ground_aircraft_count,
    avg_airborne_altitude_ft,
    max_airborne_altitude_ft,
    min_airborne_altitude_ft,
    avg_ground_speed_knots,
    hourly_sector_density_rank
)
WITH base_vectors AS (
    SELECT 
        DATE_TRUNC('hour', TO_TIMESTAMP(time_position)) AS snapshot_hour,
        COALESCE(TRIM(origin_country), 'Unknown')        AS origin_country,
        COALESCE(TRIM(callsign), 'UNASSIGNED')           AS callsign,
        icao24,
        latitude,
        longitude,
        ST_GEOHASH(ST_MAKEPOINT(longitude, latitude), 4) AS spatial_sector,
        baro_altitude * 3.28084                         AS altitude_ft,
        velocity * 1.94384                              AS speed_knots,
        on_ground,
        CASE 
            WHEN on_ground THEN 'Ground / Taxi'
            WHEN baro_altitude * 3.28084 < 10000 THEN 'Low Altitude / Approach'
            WHEN baro_altitude * 3.28084 BETWEEN 10000 AND 28000 THEN 'Mid Altitude'
            WHEN baro_altitude * 3.28084 > 28000 THEN 'High Cruise'
            ELSE 'Unknown'
        END AS flight_phase
    FROM OPENSKY_ETL.STAGED.STAGED_DATA
    WHERE icao24 IS NOT NULL
      AND time_position IS NOT NULL
),
hourly_aggregates AS (
    SELECT 
        snapshot_hour,
        origin_country,
        spatial_sector,
        flight_phase,
        
        ROUND(AVG(latitude), 4)                                  AS sector_center_lat,
        ROUND(AVG(longitude), 4)                                 AS sector_center_lon,
        
        COUNT(DISTINCT icao24)                                   AS unique_aircraft_count,
        COUNT(DISTINCT callsign)                                 AS active_callsigns_count,
        COUNT(DISTINCT CASE WHEN NOT on_ground THEN icao24 END)  AS airborne_aircraft_count,
        COUNT(DISTINCT CASE WHEN on_ground THEN icao24 END)      AS ground_aircraft_count,
        
        ROUND(AVG(CASE WHEN NOT on_ground THEN altitude_ft END), 2) AS avg_airborne_altitude_ft,
        ROUND(MAX(CASE WHEN NOT on_ground THEN altitude_ft END), 2) AS max_airborne_altitude_ft,
        ROUND(MIN(CASE WHEN NOT on_ground THEN altitude_ft END), 2) AS min_airborne_altitude_ft,
        
        ROUND(AVG(speed_knots), 2)                                  AS avg_ground_speed_knots
    FROM base_vectors
    GROUP BY 1, 2, 3, 4
)
SELECT 
    snapshot_hour,
    origin_country,
    spatial_sector,
    sector_center_lat,
    sector_center_lon,
    flight_phase,
    unique_aircraft_count,
    active_callsigns_count,
    airborne_aircraft_count,
    ground_aircraft_count,
    avg_airborne_altitude_ft,
    max_airborne_altitude_ft,
    min_airborne_altitude_ft,
    avg_ground_speed_knots,
    
    DENSE_RANK() OVER (
        PARTITION BY snapshot_hour 
        ORDER BY airborne_aircraft_count DESC
    ) AS hourly_sector_density_rank
FROM hourly_aggregates;