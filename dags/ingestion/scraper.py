import requests
from bs4 import BeautifulSoup

# Some websites block requests that don't have a browser user-agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}


def scrape_flight_details(state):
    """
    Given a single OpenSky state vector array, extract and clean its fields[cite: 1].
    Returns a dictionary of normalized flight metrics[cite: 1].
    Returns an empty dictionary if anything goes wrong[cite: 1].
    """
    try:
        if not state or len(state) < 17:
            print("    Invalid or incomplete state vector received")
            return {}

        callsign = state[1].strip() if state[1] else "N/A"

        return {
            "icao24": state[0],
            "callsign": callsign,
            "origin_country": state[2] if state[2] else "UNKNOWN",
            "time_position": state[3],
            "last_contact": state[4],
            "longitude": state[5],
            "latitude": state[6],
            "baro_altitude": state[7],
            "on_ground": state[8] if state[8] is not None else False,
            "velocity": state[9],
            "true_track": state[10],
            "vertical_rate": state[11],
            "geo_altitude": state[13],
            "squawk": state[14],
        }

    except Exception as e:
        print(f"    Error scraping flight details: {e}")
        return {}


def scrape_flight_data(raw_payload):
    """
    Loop through flight state vectors in the raw OpenSky payload[cite: 1]
    and convert each into a clean flight record dictionary[cite: 1].
    """
    time_fetched = raw_payload.get("fetched_at") or raw_payload.get("time")
    states = raw_payload.get("states", [])

    parsed_records = []

    for i, state in enumerate(states):
        icao = state[0] if len(state) > 0 else "UNKNOWN"
        callsign = state[1].strip() if len(state) > 1 and state[1] else "N/A"

        print(f"  Scraping flight {i + 1}/{len(states)}: {icao} ({callsign})...")

        flight_dict = scrape_flight_details(state)
        if flight_dict:
            flight_dict["time_fetched"] = time_fetched
            parsed_records.append(flight_dict)

    return parsed_records