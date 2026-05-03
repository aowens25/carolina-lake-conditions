import json
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


def get_raw_weather_files() -> list[Path]:
    files = sorted(RAW_DIR.glob("*_weather_open_meteo_*.json"))

    if not files:
        raise FileNotFoundError("No raw weather files found in data/raw")

    return files


def process_raw_file(raw_file: Path) -> pd.DataFrame:
    with open(raw_file, "r") as f:
        record = json.load(f)

    daily = record["raw_payload"]["daily"]

    rows = []

    for i in range(len(daily["time"])):
        rows.append(
            {
                "lake_slug": record["lake_slug"],
                "lake_name": record["lake_name"],
                "date": daily["time"][i],
                "temperature_max_f": daily["temperature_2m_max"][i],
                "temperature_min_f": daily["temperature_2m_min"][i],
                "precipitation_in": daily["precipitation_sum"][i],
                "wind_speed_max_mph": daily["windspeed_10m_max"][i],
                "source_system": record["source_system"],
                "ingested_at_utc": record["ingested_at_utc"],
                "raw_file_name": raw_file.name,
            }
        )

    return pd.DataFrame(rows)


def process_weather() -> pd.DataFrame:
    raw_files = get_raw_weather_files()
    dfs = []

    for raw_file in raw_files:
        print(f"Processing raw file: {raw_file}")
        dfs.append(process_raw_file(raw_file))

    return pd.concat(dfs, ignore_index=True)


def save_processed(df: pd.DataFrame) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    output_path = PROCESSED_DIR / "weather_processed.csv"
    df.to_csv(output_path, index=False)

    print(f"Saved processed weather data to {output_path}")


def main() -> None:
    df = process_weather()

    print(df.head())
    print(f"Processed rows: {len(df)}")

    save_processed(df)


if __name__ == "__main__":
    main()