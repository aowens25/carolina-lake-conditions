from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

DB_PATH = Path("data/lake_conditions.duckdb")


@st.cache_data
def load_data() -> pd.DataFrame:
    if not DB_PATH.exists():
        st.error("DuckDB database not found. Run the pipeline first.")
        return pd.DataFrame()

    conn = duckdb.connect(str(DB_PATH))

    df = conn.execute(
        """
        SELECT *
        FROM lake_weather
        ORDER BY weather_date
        """
    ).df()

    conn.close()

    df["weather_date"] = pd.to_datetime(df["weather_date"])

    return df


def main() -> None:
    st.set_page_config(page_title="Carolina Lake Conditions", layout="wide")

    st.title("Carolina Lake Conditions Dashboard")

    df = load_data()

    if df.empty:
        return

    st.sidebar.header("Filters")

    lake_names = sorted(df["lake_name"].unique())
    selected_lake = st.sidebar.selectbox("Select Lake", lake_names)

    filtered_lake = df[df["lake_name"] == selected_lake].copy()

    selected_date = st.sidebar.date_input(
        "Select Date",
        value=filtered_lake["weather_date"].min(),
        min_value=filtered_lake["weather_date"].min(),
        max_value=filtered_lake["weather_date"].max(),
    )

    filtered_day = filtered_lake[
        filtered_lake["weather_date"] == pd.to_datetime(selected_date)
    ]

    st.subheader(f"{selected_lake} Conditions Summary")

    if not filtered_day.empty:
        row = filtered_day.iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Conditions", row["conditions_label"])
        col2.metric("Score", int(row["conditions_score"]))
        col3.metric("Temp Max (°F)", round(row["temperature_max_f"], 1))
        col4.metric("Wind Max (mph)", round(row["wind_speed_max_mph"], 1))
    else:
        st.warning("No data available for the selected date.")

    st.subheader("Forecast Table")

    table_df = filtered_lake.sort_values("weather_date")[
        [
            "weather_date",
            "temperature_max_f",
            "temperature_min_f",
            "precipitation_in",
            "wind_speed_max_mph",
            "conditions_score",
            "conditions_label",
        ]
    ]

    st.dataframe(table_df, use_container_width=True)

    st.subheader("Temperature Trend")

    temp_chart_df = filtered_lake.set_index("weather_date")[
        ["temperature_max_f", "temperature_min_f"]
    ]

    st.line_chart(temp_chart_df)

    st.subheader("Wind and Precipitation")

    col1, col2 = st.columns(2)

    with col1:
        wind_chart_df = filtered_lake.set_index("weather_date")[["wind_speed_max_mph"]]
        st.line_chart(wind_chart_df)

    with col2:
        precip_chart_df = filtered_lake.set_index("weather_date")[["precipitation_in"]]
        st.bar_chart(precip_chart_df)


if __name__ == "__main__":
    main()