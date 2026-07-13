"""Insight Narrator agent: profiles any dataset (deterministic stats, no LLM) and narrates
the top 3 findings in plain English. The LLM's job is explaining what the stats found,
never computing the stats itself - keeps findings trustworthy and reproducible.

Supports three LLM providers, selected via LLM_PROVIDER env var ("anthropic", "gemini", or "groq").
Defaults to "groq" - best free-tier limits of the three for this demo.
"""
import os

import pandas as pd

from profiler import top_findings

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

    def complete(self, prompt: str, max_tokens: int = 200) -> str:
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


def _narrate_finding(llm: LLMClient, finding: dict) -> str:
    if finding["type"] == "trend":
        prompt = (
            f"A statistical analysis found a real trend: the column '{finding['column']}' is "
            f"{finding['detail']['direction']} over time (correlation r={finding['detail']['r_value']:.2f}, "
            f"p={finding['detail']['p_value']:.4f}). In exactly one plain-English sentence, headline this "
            f"finding for a business audience. No preamble."
        )
    elif finding["type"] == "outlier":
        labels = ", ".join(f"{k}={v}" for k, v in finding["detail"]["row_labels"].items())
        prompt = (
            f"A statistical analysis found an outlier: in column '{finding['column']}', one data point "
            f"({labels}) has value {finding['detail']['value']:.1f}, versus a dataset average of "
            f"{finding['detail']['mean']:.1f} ({finding['detail']['z_score']:.1f} standard deviations away). "
            f"In exactly one plain-English sentence, headline this finding for a business audience. No preamble."
        )
    else:
        d = finding["detail"]
        direction = "positively" if d["r_value"] > 0 else "negatively"
        prompt = (
            f"A statistical analysis found a correlation: '{d['col_a']}' and '{d['col_b']}' are "
            f"{direction} correlated (r={d['r_value']:.2f}, p={d['p_value']:.4f}). In exactly one "
            f"plain-English sentence, headline this finding for a business audience - note this shows "
            f"correlation, not proven causation. No preamble."
        )
    return llm.complete(prompt)


class InsightNarratorAgent:
    def __init__(self, provider=None, api_key=None):
        self.llm = LLMClient(provider=provider, api_key=api_key)

    def analyze(self, df: pd.DataFrame, date_col: str | None = None, label_cols: list[str] | None = None) -> list[dict]:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        label_cols = label_cols or []

        findings = top_findings(df, date_col, numeric_cols, label_cols, n=3)

        for f in findings:
            f["narration"] = _narrate_finding(self.llm, f)

        return findings
