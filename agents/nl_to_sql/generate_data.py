"""Generates a synthetic e-commerce dataset into a local DuckDB file for the NL-to-SQL agent demo.

Safe to run repeatedly - always rebuilds duckdb/ecommerce.duckdb from scratch.
"""
import os

import duckdb
import numpy as np
import pandas as pd

rng = np.random.default_rng(seed=42)

REGIONS = ["North", "South", "East", "West"]
CATEGORIES = ["Electronics", "Apparel", "Home", "Toys", "Grocery"]

N_CUSTOMERS = 500
N_PRODUCTS = 60
N_ORDERS = 8000

def build_customers():
    return pd.DataFrame({
        "customer_id": np.arange(1, N_CUSTOMERS + 1),
        "name": [f"Customer {i}" for i in range(1, N_CUSTOMERS + 1)],
        "region": rng.choice(REGIONS, N_CUSTOMERS),
        "signup_date": pd.to_datetime("2023-01-01") + pd.to_timedelta(
            rng.integers(0, 700, N_CUSTOMERS), unit="D"
        ),
    })

def build_products():
    category_per_product = rng.choice(CATEGORIES, N_PRODUCTS)
    base_price = rng.uniform(5, 500, N_PRODUCTS).round(2)
    return pd.DataFrame({
        "product_id": np.arange(1, N_PRODUCTS + 1),
        "name": [f"Product {i}" for i in range(1, N_PRODUCTS + 1)],
        "category": category_per_product,
        "unit_price": base_price,
    })

def build_orders(customers, products):
    order_dates = pd.to_datetime("2024-01-01") + pd.to_timedelta(
        rng.integers(0, 730, N_ORDERS), unit="D"
    )
    # seasonal bump: boost order volume in Nov/Dec by duplicating some Nov/Dec rows
    month = order_dates.month
    seasonal_boost_mask = rng.random(N_ORDERS) < np.where((month == 11) | (month == 12), 0.35, 0.0)

    customer_ids = rng.choice(customers["customer_id"], N_ORDERS)
    product_ids = rng.choice(products["product_id"], N_ORDERS)
    quantities = rng.integers(1, 6, N_ORDERS)

    df = pd.DataFrame({
        "order_id": np.arange(1, N_ORDERS + 1),
        "customer_id": customer_ids,
        "product_id": product_ids,
        "quantity": quantities,
        "order_date": order_dates,
    })

    # Inject one deliberate anomaly: a sharp dip in March 2024 (for Insight Narrator agent later)
    march_2024_mask = (df["order_date"].dt.year == 2024) & (df["order_date"].dt.month == 3)
    keep_mask = ~march_2024_mask | (rng.random(N_ORDERS) < 0.3)  # drop 70% of March 2024 orders
    df = df[keep_mask].reset_index(drop=True)
    df["order_id"] = np.arange(1, len(df) + 1)

    return df.merge(customers[["customer_id", "region"]], on="customer_id", how="left")

def main():
    os.makedirs("duckdb", exist_ok=True)

    customers = build_customers()
    products = build_products()
    orders = build_orders(customers, products)

    con = duckdb.connect("duckdb/ecommerce.duckdb")
    con.execute("CREATE OR REPLACE TABLE customers AS SELECT * FROM customers")
    con.execute("CREATE OR REPLACE TABLE products AS SELECT * FROM products")
    con.execute("CREATE OR REPLACE TABLE orders AS SELECT * FROM orders")
    con.close()

    print(f"Built duckdb/ecommerce.duckdb: {len(customers)} customers, {len(products)} products, {len(orders)} orders")

if __name__ == "__main__":
    main()
