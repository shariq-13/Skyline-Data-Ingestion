import os
OPENSKY_CONFIG = {
    "name": "opensky_states_all",
    "url": "https://opensky-network.org/api/states/all",
    "timeout": 30,
    "username": os.getenv("OPENSKY_USERNAME"),
    "password": os.getenv("OPENSKY_PASSWORD"),
    "timeout": 30,
}