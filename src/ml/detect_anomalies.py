"""Per-lake Isolation Forest flags unusual weather records.
Evaluation is chronological holdout plus injected extreme cases; no human labels,
so this is a stress test rather than a real-world accuracy estimate.
"""
from pathlib import Path
import pandas as pd
from sklearn.ensemble import IsolationForest

ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = ROOT / "data/consumption/lake_weather_dashboard.csv"
OUTPUT_PATH = ROOT / "data/consumption/lake_weather_anomalies.csv"
FEATURES = ["temperature_max_f", "temperature_min_f", "precipitation_in", "wind_speed_max_mph"]
CONTAMINATION = 0.05


def model():
    return IsolationForest(n_estimators=200, contamination=CONTAMINATION, random_state=42)


def main():
    data = pd.read_csv(INPUT_PATH)
    data["weather_date"] = pd.to_datetime(data["weather_date"])
    data = data.dropna(subset=FEATURES).sort_values(["lake_slug", "weather_date"])
    results = []
    for lake_slug, lake_data in data.groupby("lake_slug", sort=True):
        lake_data = lake_data.sort_values("weather_date").copy()
        values = lake_data[FEATURES].astype(float)
        split = min(max(10, int(len(values) * 0.8)), len(values) - 1)
        train, holdout = values.iloc[:split], values.iloc[split:]
        evaluator = model().fit(train)
        threshold = float(pd.Series(-evaluator.score_samples(train)).quantile(0.95))
        holdout_scores = -evaluator.score_samples(holdout)
        holdout_rate = float((holdout_scores >= threshold).mean())
        synthetic = holdout.iloc[::10].head(20).copy()
        if not synthetic.empty:
            synthetic["temperature_max_f"] = max(115.0, float(train["temperature_max_f"].max()) + 35)
            synthetic["temperature_min_f"] = min(-20.0, float(train["temperature_min_f"].min()) - 35)
            synthetic["precipitation_in"] = max(10.0, float(train["precipitation_in"].max()) + 8)
            synthetic["wind_speed_max_mph"] = max(100.0, float(train["wind_speed_max_mph"].max()) + 60)
            stress_rate = float((-evaluator.score_samples(synthetic[FEATURES]) >= threshold).mean())
        else:
            stress_rate = float("nan")
        print(f"Evaluation {lake_slug}: holdout flagged {holdout_rate:.1%}; injected extreme detection {stress_rate:.1%} across {len(synthetic)} cases (stress test only, not real-world accuracy).")
        production = model().fit(values)
        scores = -production.score_samples(values)
        cutoff = float(pd.Series(scores).quantile(0.95))
        result = lake_data[["lake_slug", "lake_name", "weather_date"]].copy()
        result["anomaly_score"] = scores
        result["is_anomaly"] = scores >= cutoff
        results.append(result)
    output = pd.concat(results, ignore_index=True)
    output["weather_date"] = output["weather_date"].dt.strftime("%Y-%m-%d")
    output.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {int(output['is_anomaly'].sum())} flagged rows out of {len(output)} to {OUTPUT_PATH.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
