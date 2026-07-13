"""Generates a synthetic customer dataset with deliberately planted data quality issues,
so the Data Quality agent has real, findable problems to catch:

1. Missing values: ~8% of rows have a null email
2. Duplicate IDs: 5 customer_ids each appear twice (simulating a real duplicate-entry bug)
3. Type mismatch: ~15 rows have lifetime_revenue stored as "$1,234.56" text instead of a number,
   which silently turns the whole column into text when loaded naively
4. Invalid dates: 3 rows have a signup_date in the future (an impossible value)

Safe to run repeatedly - always rebuilds data/customers.csv from scratch.
"""
import os

import numpy as np
import pandas as pd

rng = np.random.default_rng(seed=11)

N_CUSTOMERS = 400
REGIONS = ["North", "South", "East", "West"]


def main():
    os.makedirs("data", exist_ok=True)

    customer_ids = list(range(1, N_CUSTOMERS + 1))
    signup_dates = pd.to_datetime("2022-01-01") + pd.to_timedelta(
        rng.integers(0, 1000, N_CUSTOMERS), unit="D"
    )

    df = pd.DataFrame({
        "customer_id": customer_ids,
        "name": [f"Customer {i}" for i in customer_ids],
        "email": [f"customer{i}@example.com" for i in customer_ids],
        "age": rng.integers(18, 75, N_CUSTOMERS),
        "signup_date": signup_dates,
        "region": rng.choice(REGIONS, N_CUSTOMERS),
        "lifetime_revenue": rng.uniform(50, 5000, N_CUSTOMERS).round(2),
    })

    # Issue 1: missing emails (~8% of rows)
    missing_email_idx = rng.choice(df.index, size=int(N_CUSTOMERS * 0.08), replace=False)
    df.loc[missing_email_idx, "email"] = None

    # Issue 2: duplicate customer_ids - append 5 duplicate rows with the same ID as an existing row
    dup_source_idx = rng.choice(df.index, size=5, replace=False)
    dup_rows = df.loc[dup_source_idx].copy()
    dup_rows["lifetime_revenue"] = dup_rows["lifetime_revenue"] * rng.uniform(0.9, 1.1, 5)  # slightly different, like a re-entry
    df = pd.concat([df, dup_rows], ignore_index=True)

    # Issue 3: lifetime_revenue stored as currency-formatted text for some rows -
    # this forces the whole column to load as text (object dtype) instead of numeric
    text_revenue_idx = rng.choice(df.index, size=15, replace=False)
    df["lifetime_revenue"] = df["lifetime_revenue"].astype(object)
    for idx in text_revenue_idx:
        df.at[idx, "lifetime_revenue"] = f"${df.at[idx, 'lifetime_revenue']:,.2f}"

    # Issue 4: impossible signup dates (in the future)
    future_date_idx = rng.choice(df.index, size=3, replace=False)
    df.loc[future_date_idx, "signup_date"] = pd.Timestamp("2030-01-01")

    df.to_csv("data/customers.csv", index=False)
    print(f"Built data/customers.csv: {len(df)} rows (includes 5 planted duplicates)")


if __name__ == "__main__":
    main()
