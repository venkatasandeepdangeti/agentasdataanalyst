"""NL-to-SQL agent: turns a plain-English question into SQL, runs it read-only against
the demo DuckDB database, and returns the generated SQL, the result, and a one-sentence
narration of what the result shows.

Supports two LLM providers, selected via LLM_PROVIDER env var ("anthropic" or "gemini").
Defaults to "gemini" since it has a usable free tier for this demo.
"""
import os
import re

import duckdb

ANTHROPIC_MODEL = "claude-sonnet-4-5"
GEMINI_MODEL = "gemini-flash-latest"

SCHEMA_DESCRIPTION = """
Tables in this DuckDB database:

customers(customer_id INT, name VARCHAR, region VARCHAR, signup_date DATE)
  - region is one of: North, South, East, West

products(product_id INT, name VARCHAR, category VARCHAR, unit_price DOUBLE)
  - category is one of: Electronics, Apparel, Home, Toys, Grocery

orders(order_id INT, customer_id INT, product_id INT, quantity INT, order_date DATE, region VARCHAR)
  - order_date spans 2024-01-01 to 2025-12-31
  - join orders.customer_id -> customers.customer_id
  - join orders.product_id -> products.product_id
  - revenue for an order = orders.quantity * products.unit_price (requires a join to products)
"""

FORBIDDEN_KEYWORDS = ("insert", "update", "delete", "drop", "alter", "create", "attach", "copy", "pragma")


class LLMClient:
    """Thin wrapper so the agent logic doesn't care which provider is behind it."""

    def __init__(self, provider=None, api_key=None):
        self.provider = provider or os.environ.get("LLM_PROVIDER", "gemini")

        if self.provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        elif self.provider == "gemini":
            from google import genai
            self._client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
        else:
            raise ValueError(f"Unknown LLM_PROVIDER: {self.provider}")

    def complete(self, prompt: str, max_tokens: int = 500) -> str:
        if self.provider == "anthropic":
            response = self._client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        else:
            response = self._client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            return response.text.strip()


class NLToSQLAgent:
    def __init__(self, db_path="duckdb/ecommerce.duckdb", provider=None, api_key=None):
        self.db_path = db_path
        self.llm = LLMClient(provider=provider, api_key=api_key)

    def _generate_sql(self, question: str) -> str:
        prompt = f"""You are a SQL generator for a DuckDB database. Given the schema below and a user's
plain-English question, output ONLY a single read-only SELECT SQL query that answers it.
No explanation, no markdown code fences, just the raw SQL statement.

{SCHEMA_DESCRIPTION}

Question: {question}

SQL:"""
        sql = self.llm.complete(prompt, max_tokens=500)
        sql = re.sub(r"^```sql\s*|\s*```$", "", sql, flags=re.IGNORECASE).strip()
        return sql

    def _validate_sql(self, sql: str):
        lowered = sql.lower().lstrip()
        if not (lowered.startswith("select") or lowered.startswith("with")):
            raise ValueError("Generated query is not a read-only SELECT/CTE statement - refusing to run it.")
        for kw in FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{kw}\b", lowered):
                raise ValueError(f"Generated query contains forbidden keyword '{kw}' - refusing to run it.")

    def _narrate(self, question: str, sql: str, result_df) -> str:
        preview = result_df.head(20).to_csv(index=False)
        prompt = f"""A user asked: "{question}"
This SQL was run: {sql}
The result (CSV, possibly truncated):
{preview}

In exactly one sentence, plainly summarize what this result shows. No preamble."""
        return self.llm.complete(prompt, max_tokens=200)

    def ask(self, question: str) -> dict:
        sql = self._generate_sql(question)
        self._validate_sql(sql)

        con = duckdb.connect(self.db_path, read_only=True)
        try:
            con.execute("PRAGMA threads=1")
            result_df = con.execute(sql).fetchdf()
        finally:
            con.close()

        narration = self._narrate(question, sql, result_df)

        return {"sql": sql, "result": result_df, "narration": narration}
