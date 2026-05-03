from pathlib import Path

import duckdb

CONSUMPTION_PATH = Path("data/consumption/lake_weather_dashboard.csv")
DB_PATH = Path("data/lake_conditions.duckdb")


def main() -> None:
    if not CONSUMPTION_PATH.exists():
        raise FileNotFoundError(f"Consumption file not found: {CONSUMPTION_PATH}")

    conn = duckdb.connect(str(DB_PATH))

    conn.execute("DROP TABLE IF EXISTS lake_weather")

    conn.execute(
        f"""
        CREATE TABLE lake_weather AS
        SELECT
            lake_slug,
            lake_name,
            CAST(weather_date AS DATE) AS weather_date,
            temperature_max_f,
            temperature_min_f,
            precipitation_in,
            wind_speed_max_mph,
            conditions_score,
            conditions_label,
            source_system,
            updated_at_utc
        FROM read_csv_auto('{CONSUMPTION_PATH}')
        """
    )

    row_count = conn.execute("SELECT COUNT(*) FROM lake_weather").fetchone()[0]

    conn.close()

    print(f"Loaded {row_count} rows into {DB_PATH}")


if __name__ == "__main__":
    main()