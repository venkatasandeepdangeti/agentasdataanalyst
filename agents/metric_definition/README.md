# Metric Definition Agent

Every company eventually has 3 different definitions of "active user" living in 3 different dashboards. This agent checks a submitted SQL definition of a metric against a canonical (source-of-truth) definition and explains any real semantic difference in plain English.

Of the four agents in this repo, this is the one with the clearest path to being an actual internal tool a company would pay for - metric drift between teams is a real, expensive, recurring problem.

## A different design than the other three agents
`nl_to_sql`, `insight_narrator`, and `data_quality` all deliberately keep the LLM out of *detection* - real code finds the facts, the LLM only narrates them. This agent is different on purpose: whether two SQL snippets mean the same thing isn't something you can check with a simple rule - it genuinely requires understanding what the SQL *means* (does this WHERE clause include or exclude trial users? does this JOIN change the population being counted?). That's exactly the kind of judgment call an LLM is suited for, so here it does the actual comparison, not just the write-up.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then edit .env and set a real API key (Groq/Gemini/Anthropic)
streamlit run app.py
```

## Try it
Pick a metric, and the submitted SQL box is pre-filled with a real, subtle mismatch:
- **Active User**: submitted version forgets to exclude trial accounts
- **Churn Rate**: submitted version uses the wrong period boundary for the denominator
- **Monthly Recurring Revenue**: submitted version accidentally includes trialing subscriptions

Fix the SQL yourself and hit Compare again to see the agent confirm a match.

## Known issue: crashes on ARM64 (aarch64) Linux
If Streamlit segfaults, this is a known pyarrow bug (jemalloc background thread) on ARM64. Fix:
```bash
export ARROW_DEFAULT_MEMORY_POOL=system
streamlit run app.py
```
