from pathlib import Path

import duckdb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DB_PATH = Path("data/lake_conditions.duckdb")
ANOMALY_PATH = Path("data/consumption/lake_weather_anomalies.csv")


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


def load_anomalies() -> pd.DataFrame:
    if not ANOMALY_PATH.exists():
        return pd.DataFrame()
    anomalies = pd.read_csv(ANOMALY_PATH)
    anomalies["weather_date"] = pd.to_datetime(anomalies["weather_date"])
    anomalies["is_anomaly"] = anomalies["is_anomaly"].astype(str).str.lower().eq("true")
    return anomalies


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

    st.subheader("7-Day Weather Forecast")
    today = pd.Timestamp.now().normalize()
    forecast = filtered_lake[filtered_lake["weather_date"] >= today].sort_values("weather_date")
    if forecast.empty:
        st.info("No upcoming forecast is available yet. The daily refresh will populate it.")
    else:
        controls = st.columns([1, 1])
        with controls[0]:
            forecast_days = st.selectbox("Forecast range", [3, 7], index=1, format_func=lambda n: f"Next {n} days")
        with controls[1]:
            forecast_view = st.selectbox("Show", ["Temperature", "Precipitation", "Wind"])
        forecast = forecast.head(forecast_days)
        fig = go.Figure()
        dates = forecast["weather_date"]
        if forecast_view == "Temperature":
            fig.add_trace(go.Scatter(
                x=dates, y=forecast["temperature_max_f"], name="High",
                mode="lines+markers", line=dict(color="#ff8c42", width=3),
                hovertemplate="%{x|%a, %b %-d}<br>High: %{y:.1f} °F<extra></extra>",
            ))
            fig.add_trace(go.Scatter(
                x=dates, y=forecast["temperature_min_f"], name="Low",
                mode="lines+markers", line=dict(color="#55b8ff", width=3),
                hovertemplate="%{x|%a, %b %-d}<br>Low: %{y:.1f} °F<extra></extra>",
            ))
            y_title = "Temperature (°F)"
        elif forecast_view == "Precipitation":
            fig.add_trace(go.Bar(
                x=dates, y=forecast["precipitation_in"], name="Rain",
                marker_color="#55b8ff",
                hovertemplate="%{x|%a, %b %-d}<br>Rain: %{y:.2f} in<extra></extra>",
            ))
            y_title = "Precipitation (inches)"
        else:
            fig.add_trace(go.Scatter(
                x=dates, y=forecast["wind_speed_max_mph"], name="Wind",
                mode="lines+markers", line=dict(color="#b79cff", width=3),
                hovertemplate="%{x|%a, %b %-d}<br>Wind: %{y:.1f} mph<extra></extra>",
            ))
            y_title = "Maximum wind (mph)"
        fig.update_layout(
            template="plotly_dark", height=390, margin=dict(l=10, r=10, t=20, b=10),
            hovermode="x unified", xaxis_title=None, yaxis_title=y_title,
            legend=dict(orientation="h", y=1.12, x=0),
        )
        fig.update_xaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "scrollZoom": True})

    with st.expander("How this forecast works", expanded=True):
        st.write(
            "The refresh job requests daily high and low temperatures, precipitation, and maximum wind "
            "from Open-Meteo's forecast API for this lake's location. This chart displays those provider "
            "forecasts; it does not train a separate weather-prediction model from the saved data. "
            "The feed is refreshed daily. Forecasts can change as new weather-model runs arrive."
        )
        st.caption(
            "The Isolation Forest elsewhere on this page is a separate tool: it scores unusual weather "
            "records for review and does not produce forecasts or safety advisories."
        )



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

    st.subheader("Unusual Weather Patterns")
    anomalies = load_anomalies()
    if anomalies.empty:
        st.caption("Anomaly results will appear after the next data refresh.")
    else:
        flagged = anomalies[
            (anomalies["lake_name"] == selected_lake) & anomalies["is_anomaly"]
        ]
        flagged = filtered_lake.merge(
            flagged[["weather_date", "anomaly_score"]],
            on="weather_date",
            how="inner",
        )
        if flagged.empty:
            st.caption("No unusual records flagged for this lake.")
        else:
            st.caption("Statistical outliers for review; these are not safety advisories.")
            st.dataframe(
                flagged[
                    [
                        "weather_date",
                        "temperature_max_f",
                        "temperature_min_f",
                        "precipitation_in",
                        "wind_speed_max_mph",
                        "anomaly_score",
                    ]
                ].sort_values("anomaly_score", ascending=False),
                use_container_width=True,
            )

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
