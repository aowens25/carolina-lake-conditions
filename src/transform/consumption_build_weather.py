from pathlib import Path

import pandas as pd

MODELED_PATH = Path("data/modeled/lake_day_weather.csv")
CONSUMPTION_DIR = Path("data/consumption")


def load_modeled() -> pd.DataFrame:
    if not MODELED_PATH.exists():
        raise FileNotFoundError(f"Modeled file not found: {MODELED_PATH}")

    return pd.read_csv(MODELED_PATH)


def calculate_conditions_score(df: pd.DataFrame) -> pd.DataFrame:
    consumption = df.copy()

    consumption["wind_penalty"] = consumption["wind_speed_max_mph"].apply(
        lambda x: 30 if x >= 20 else 15 if x >= 12 else 0
    )

    consumption["rain_penalty"] = consumption["precipitation_in"].apply(
        lambda x: 25 if x >= 0.4 else 10 if x > 0 else 0
    )

    consumption["conditions_score"] = (
        100 - consumption["wind_penalty"] - consumption["rain_penalty"]
    )

    consumption["conditions_label"] = consumption["conditions_score"].apply(
        lambda x: "Good" if x >= 80 else "Okay" if x >= 60 else "Poor"
    )

    return consumption


def build_consumption(df: pd.DataFrame) -> pd.DataFrame:
    consumption = calculate_conditions_score(df)

    return consumption[
        [
            "lake_slug",
            "lake_name",
            "weather_date",
            "temperature_max_f",
            "temperature_min_f",
            "precipitation_in",
            "wind_speed_max_mph",
            "conditions_score",
            "conditions_label",
            "source_system",
            "updated_at_utc",
        ]
    ]


def save_consumption(df: pd.DataFrame) -> None:
    CONSUMPTION_DIR.mkdir(parents=True, exist_ok=True)

    output_path = CONSUMPTION_DIR / "lake_weather_dashboard.csv"
    df.to_csv(output_path, index=False)

    print(f"Saved consumption weather data to {output_path}")


def main() -> None:
    modeled_df = load_modeled()
    consumption_df = build_consumption(modeled_df)

    print(consumption_df.head())
    print(f"Consumption rows: {len(consumption_df)}")

    save_consumption(consumption_df)


if __name__ == "__main__":
    main()