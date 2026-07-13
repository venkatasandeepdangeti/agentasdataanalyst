"""Data Quality agent: runs deterministic checks (checker.py) on a dataset and asks an LLM
to explain why each issue matters and suggest a fix - the LLM never detects issues itself,
only narrates ones already found by real code.

Supports three LLM providers, selected via LLM_PROVIDER env var ("anthropic", "gemini", or "groq").
Defaults to "groq" - best free-tier limits of the three for this demo.
"""
import os

import pandas as pd

from checker import run_all_checks

ANTHROPIC_MODEL = "claude-sonnet-4-5"
GEMINI_MODEL = "gemini-flash-latest"
GROQ_MODEL = "llama-3.3-70b-versatile"


class LLMClient:
    """Thin wrapper so the agent logic doesn't care which provider is behind it."""

    def __init__(self, provider=None, api_key=None):
        self.provider = provider or os.environ.get("LLM_PROVIDER", "groq")

        if self.provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        elif self.provider == "gemini":
            from google import genai
            self._client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
        elif self.provider == "groq":
            from groq import Groq
            self._client = Groq(api_key=api_key or os.environ.get("GROQ_API_KEY"))
        else:
            raise ValueError(f"Unknown LLM_PROVIDER: {self.provider}")

    def complete(self, prompt: str, max_tokens: int = 250) -> str:
        if self.provider == "anthropic":
            response = self._client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        elif self.provider == "gemini":
            response = self._client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            return response.text.strip()
        else:
            response = self._client.chat.completions.create(
                model=GROQ_MODEL,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content.strip()


def _explain_issue(llm: LLMClient, issue: dict) -> dict:
    d = issue["detail"]
    if issue["type"] == "missing_values":
        context = (
            f"Column '{issue['column']}' has {d['missing_count']} missing values "
            f"out of {d['total_rows']} rows ({d['missing_pct']:.1%})."
        )
    elif issue["type"] == "duplicates":
        context = (
            f"Column '{issue['column']}' has {d['duplicate_id_count']} duplicate IDs "
            f"({d['duplicate_row_count']} rows total). Example duplicated IDs: {d['example_ids']}."
        )
    elif issue["type"] == "type_mismatch":
        context = (
            f"Column '{issue['column']}' should be numeric, but {d['dirty_fraction']:.1%} of values "
            f"are stored as formatted text (e.g. {d['bad_value_examples']}), so the column can't be "
            f"summed or averaged as-is."
        )
    else:
        context = (
            f"Column '{issue['column']}' has {d['future_count']} dates after "
            f"{d['max_valid_date']} (example values: {d['example_values']}), which shouldn't be possible."
        )

    prompt = f"""A data quality check found this real issue in a dataset:
{context}

In two short sentences: (1) why this matters for someone using this data to make decisions,
and (2) a concrete one-line suggested fix. No preamble, no markdown formatting."""

    explanation = llm.complete(prompt)
    return {**issue, "explanation": explanation}


class DataQualityAgent:
    def __init__(self, provider=None, api_key=None):
        self.llm = LLMClient(provider=provider, api_key=api_key)

    def scan(self, df: pd.DataFrame, id_col: str = None, date_cols: list[str] = None) -> list[dict]:
        issues = run_all_checks(df, id_col=id_col, date_cols=date_cols)
        return [_explain_issue(self.llm, issue) for issue in issues]
