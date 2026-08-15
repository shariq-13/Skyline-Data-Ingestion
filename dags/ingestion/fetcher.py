import os
import requests

OPENSKY_URL = "https://opensky-network.org/api/states/all"

def fetch_live_data():
    """Fetch live flight state vectors directly via HTTPS."""
    username = os.getenv("OPENSKY_USERNAME")
    password = os.getenv("OPENSKY_PASSWORD")

    auth = (username, password) if username and password else None

    response = requests.get(OPENSKY_URL, auth=auth, timeout=10)
    response.raise_for_status()

    data = response.json()
    return {"states": data.get("states", [])}