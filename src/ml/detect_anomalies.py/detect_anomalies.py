"""Detect unusual weather records and report a synthetic stress test.

The source data has no human-verified anomaly labels. The printed evaluation is
descriptive: chronological holdout flag rate plus detection of deliberately
extreme synthetic examples. It is not a real-world accuracy estimate.
"""
from pathlib import Path

import pandas as pd
from sklearn.ensemble import IsolationForest

ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data/consumption/lake_weather_dashboard.csv"
OUTPUT_PATH = ROOT / "data/consumption/lake_weather_anomalies.csv"
FEATURES = ["temperature_max_f", "temperature_min_f", "precipitation_in", "wind_speed_max_mph"]
CONTAMINATION = 0.05
RANDOM_STATE = 42


def make_model() -> IsolationForest:
    return IsolationForest(n_estimators=200, contamination=CONTAMINATION, random_state=RANDOM_STATE)


def main() -> None:
    data = pd.read_csv(INPUT_PATH)
    data["weather_date"] = pd.to_datetime(data["weather_date"])
    data = data.dropna(subset=FEATURES).sort_values(["lake_slug", "weather_date"])

    results = []
    for lake_slug, lake_data in data.groupby("lake_slug", sort=True):
        lake_data = lake_data.sort_values("weather_date").copy()
        values = lake_data[FEATURES].astype(float)
        split_at = min(max(10, int(len(values) * 0.8)), len(values) - 1)
        train, holdout = values.iloc[:split_at], values.iloc[split_at:]

        evaluation_model = make_model().fit(train)
        threshold = float(pd.Series(-evaluation_model.score_samples(train)).quantile(1 - CONTAMINATION))
        holdout_scores = -evaluation_model.score_samples(holdout)
        holdout_flag_rate = float((holdout_scores >= threshold).mean())

        # Deliberately extreme weather combinations form a simple stress test.
        synthetic = holdout.iloc[::10].head(20).copy()
        if not synthetic.empty:
            synthetic["temperature_max_f"] = max(115.0, float(train["temperature_max_f"].max()) + 35)
            synthetic["temperature_min_f"] = min(-20.0, float(train["temperature_min_f"].min()) - 35)
            synthetic["precipitation_in"] = max(10.0, float(train["precipitation_in"].max()) + 8)
            synthetic["wind_speed_max_mph"] = max(100.0, float(train["wind_speed_max_mph"].max()) + 60)
            synthetic_scores = -evaluation_model.score_samples(synthetic[FEATURES])
            synthetic_detection_rate = float((synthetic_scores >= threshold).mean())
        else:
            synthetic_detection_rate = float("nan")

        print(f"Evaluation {lake_slug}: chronological holdout flagged {holdout_flag_rate:.1%}; synthetic extreme-case detection {synthetic_detection_rate:.1%} ({len(synthetic)} injected cases). Synthetic detection is a stress test, not real-world accuracy.")

        production_model = make_model().fit(values)
        anomaly_scores = -production_model.score_samples(values)
        production_threshold = float(pd.Series(anomaly_scores).quantile(1 - CONTAMINATION))
        lake_result = lake_data[["lake_slug", "lake_name", "weather_date"]].copy()
        lake_result["anomaly_score"] = anomaly_scores
        lake_result["is_anomaly"] = anomaly_scores >= production_threshold
        results.append(lake_result)

    output = pd.concat(results, ignore_index=True)
    output["weather_date"] = output["weather_date"].dt.strftime("%Y-%m-%d")
    output.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {int(output['is_anomaly'].sum())} flagged rows out of {len(output)} to {OUTPUT_PATH.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
