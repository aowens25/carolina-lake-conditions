from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROCESSED_PATH = Path("data/processed/weather_processed.csv")
MODELED_DIR = Path("data/modeled")


def load_processed() -> pd.DataFrame:
    if not PROCESSED_PATH.exists():
        raise FileNotFoundError(f"Processed file not found: {PROCESSED_PATH}")

    return pd.read_csv(PROCESSED_PATH)


def model_weather(df: pd.DataFrame) -> pd.DataFrame:
    modeled = df.copy()

    modeled["weather_date"] = pd.to_datetime(modeled["date"]).dt.date
    modeled["updated_at_utc"] = datetime.now(timezone.utc).isoformat()

    modeled = modeled[
        [
            "lake_slug",
            "lake_name",
            "weather_date",
            "temperature_max_f",
            "temperature_min_f",
            "precipitation_in",
            "wind_speed_max_mph",
            "source_system",
            "updated_at_utc",
        ]
    ]

    modeled = modeled.drop_duplicates(
        subset=["lake_slug", "weather_date"],
        keep="last",
    )

    return modeled


def save_modeled(df: pd.DataFrame) -> None:
    MODELED_DIR.mkdir(parents=True, exist_ok=True)

    output_path = MODELED_DIR / "lake_day_weather.csv"
    df.to_csv(output_path, index=False)

    print(f"Saved modeled weather data to {output_path}")


def main() -> None:
    processed_df = load_processed()
    modeled_df = model_weather(processed_df)

    print(modeled_df.head())
    print(f"Modeled rows: {len(modeled_df)}")

    save_modeled(modeled_df)


if __name__ == "__main__":
    main()