import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import json
from datetime import datetime, timezone

import requests

from src.config.lakes import LAKES

SOURCE_SYSTEM = "open_meteo"
RAW_DIR = Path("data/raw")


def fetch_weather(lake: dict) -> dict:
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lake["latitude"],
        "longitude": lake["longitude"],
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
        "timezone": "America/New_York",
        "temperature_unit": "fahrenheit",
        "windspeed_unit": "mph",
        "precipitation_unit": "inch",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    return {
        "source_system": SOURCE_SYSTEM,
        "lake_slug": lake["lake_slug"],
        "lake_name": lake["lake_name"],
        "latitude": lake["latitude"],
        "longitude": lake["longitude"],
        "api_url": response.url,
        "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
        "raw_payload": response.json(),
    }


def save_raw(record: dict) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    file_name = f"{record['lake_slug']}_weather_{SOURCE_SYSTEM}_{timestamp}.json"
    file_path = RAW_DIR / file_name

    with open(file_path, "w") as f:
        json.dump(record, f, indent=2)

    print(f"Saved raw weather data to {file_path}")


def main() -> None:
    for lake in LAKES:
        print(f"Fetching weather for {lake['lake_name']}...")
        record = fetch_weather(lake)
        save_raw(record)


if __name__ == "__main__":
    main()