"""Metric Definition agent: compares a submitted SQL definition of a metric against the
canonical (source-of-truth) definition, and explains any semantic divergence in plain English.

Design note - this agent is architecturally different from nl_to_sql, insight_narrator, and
data_quality: those three deliberately keep the LLM out of "detection" (real code finds things,
the LLM only narrates). Comparing whether two SQL snippets mean the same thing is not a
deterministic check you can write a simple rule for - it genuinely requires understanding
what the SQL *means*, which is exactly the kind of task an LLM is suited for. The LLM here
does the actual comparison, not just the write-up.

Supports three LLM providers, selected via LLM_PROVIDER env var ("anthropic", "gemini", or "groq").
Defaults to "groq" - best free-tier limits of the three for this demo.
"""
import os

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

    def complete(self, prompt: str, max_tokens: int = 400) -> str:
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


class MetricDefinitionAgent:
    def __init__(self, provider=None, api_key=None):
        self.llm = LLMClient(provider=provider, api_key=api_key)

    def compare(self, metric_name: str, description: str, canonical_sql: str, submitted_sql: str) -> dict:
        prompt = f"""You are checking whether two SQL definitions of the same business metric are
semantically equivalent - not comparing the text, but whether they would produce the same result
and mean the same thing to someone reading a dashboard.

Metric: {metric_name}
Canonical definition (source of truth): {description}

Canonical SQL:
{canonical_sql}

Submitted SQL (to check against the canonical definition):
{submitted_sql}

First line: respond with exactly "MATCH" if these are semantically equivalent, or "MISMATCH" if
they differ in a way that would produce different numbers or a different meaning.

Then, in 1-2 plain-English sentences: if MISMATCH, explain precisely what differs and why it
matters (e.g. "the submitted version includes trial users, which inflates the count"). If MATCH,
briefly confirm why they're equivalent despite any surface-level differences in the SQL.

No markdown formatting, no preamble beyond the MATCH/MISMATCH line."""

        response = self.llm.complete(prompt)
        lines = response.split("\n", 1)
        verdict = "MISMATCH" if "MISMATCH" in lines[0].upper() else "MATCH"
        explanation = lines[1].strip() if len(lines) > 1 else response

        return {"verdict": verdict, "explanation": explanation}
