# NL-to-SQL Agent

Ask a question in plain English about a synthetic e-commerce dataset (customers, products, orders). The agent generates a SQL query, shows it to you before running it, executes it read-only against a local DuckDB file, and narrates the result in one sentence.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then edit .env and set your real ANTHROPIC_API_KEY
python generate_data.py   # builds duckdb/ecommerce.duckdb
streamlit run app.py
```

## Safety
- Only `SELECT` statements are ever executed; the agent validates and rejects anything else (INSERT/UPDATE/DELETE/DROP/ALTER/etc.) before running it.
- The DuckDB connection opens read-only.
- Generated SQL is always shown to the user before/alongside execution — no silent queries.

## Dataset
`generate_data.py` builds a synthetic dataset with a fixed random seed (reproducible):
- `customers` (500 rows, 4 regions)
- `products` (60 rows, 5 categories)
- `orders` (~8,000 rows spanning 2024-2025, with a deliberate order-volume dip in March 2024 for testing anomaly-detection questions)
