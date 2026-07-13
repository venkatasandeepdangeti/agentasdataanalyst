"""Generates a synthetic daily sales/marketing dataset with three deliberate,
findable patterns, so the Insight Narrator agent has something real to discover:

1. A trend: revenue grows steadily over the 2-year period
2. An outlier: one deliberate extreme day (a stockout crash)
3. A correlation: marketing_spend is strongly correlated with revenue

A single daily series (not split by region) - keeps the trend/correlation signals clean,
since mixing multiple regions' different baseline levels into one series would add
unrelated variance that dilutes real patterns (a classic confounding problem).

Safe to run repeatedly - always rebuilds data/sales_performance.csv from scratch.
"""
import os

import numpy as np
import pandas as pd

rng = np.random.default_rng(seed=7)

N_DAYS = 730  # 2 years


def main():
    os.makedirs("data", exist_ok=True)

    dates = pd.date_range("2024-01-01", periods=N_DAYS, freq="D")
    rows = []

    base = 10000
    for i, date in enumerate(dates):
        trend = base + i * 4.5  # slow steady growth over the 2 years
        weekday_factor = 0.85 if date.weekday() >= 5 else 1.0
        noise = rng.normal(0, 150)

        marketing_spend = max(200, rng.normal(1500, 250))
        # deliberate strong, clean correlation: revenue responds to marketing spend
        revenue = trend * weekday_factor + marketing_spend * 3.0 + noise
        revenue = max(0, revenue)

        # only loosely tied to revenue (independent noise dominates), so this doesn't
        # outrank the marketing_spend correlation as "most interesting"
        units_sold = max(0, int(rng.normal(220, 60)))
        website_visits = max(0, int(rng.normal(1200, 500) + i * 0.3))

        rows.append({
            "date": date,
            "revenue": round(revenue, 2),
            "units_sold": units_sold,
            "marketing_spend": round(marketing_spend, 2),
            "website_visits": website_visits,
        })

    df = pd.DataFrame(rows)

    # deliberate outlier: a one-day stockout crash
    crash_date = pd.Timestamp("2024-11-15")
    mask = df["date"] == crash_date
    df.loc[mask, "revenue"] = 400.0
    df.loc[mask, "units_sold"] = 8
    df.loc[mask, "website_visits"] = df.loc[mask, "website_visits"] * 3  # traffic came, nothing to buy

    df.to_csv("data/sales_performance.csv", index=False)
    print(f"Built data/sales_performance.csv: {len(df)} rows")


if __name__ == "__main__":
    main()
