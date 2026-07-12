# NL-to-SQL Agent

Ask a question in plain English about a synthetic e-commerce dataset (customers, products, orders). The agent generates a SQL query, shows it to you before running it, executes it read-only against a local DuckDB file, and narrates the result in one sentence.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then edit .env and set your real ANTHROPIC_API_KEY or GEMINI_API_KEY
python generate_data.py   # builds duckdb/ecommerce.duckdb
streamlit run app.py
```

## Known issue: crashes on ARM64 (aarch64) Linux

If Streamlit segfaults shortly after you ask a question (works fine standalone, crashes only inside the running app), this is a known pyarrow bug on ARM64 - a background memory-management thread (jemalloc) in pyarrow's ARM wheel can crash under sustained/threaded use. Fix: set this environment variable before starting Streamlit:

```bash
export ARROW_DEFAULT_MEMORY_POOL=system
streamlit run app.py
```

(If you're running this as a systemd/supervisor service instead of directly in a terminal, set it as an `Environment=` line in the service definition rather than a shell export.)

## Safety
- Only `SELECT` statements are ever executed; the agent validates and rejects anything else (INSERT/UPDATE/DELETE/DROP/ALTER/etc.) before running it.
- The DuckDB connection opens read-only.
- Generated SQL is always shown to the user before/alongside execution — no silent queries.

## Dataset
`generate_data.py` builds a synthetic dataset with a fixed random seed (reproducible):
- `customers` (500 rows, 4 regions)
- `products` (60 rows, 5 categories)
- `orders` (~8,000 rows spanning 2024-2025, with a deliberate order-volume dip in March 2024 for testing anomaly-detection questions)
