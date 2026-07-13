# AutoAnalyst

AI agents that do data analytics autonomously — plain English in, insight out. Instead of dashboards people have to interpret, these agents interpret data *for* people.

**🔗 Live demo (no setup required): https://ftbkfugig5aod9sq2g2mhm.streamlit.app/**

## Agents

| Agent | What it does | Status |
|---|---|---|
| [`nl_to_sql`](agents/nl_to_sql/) | Ask a question in plain English, get the generated SQL + result + a one-sentence explanation | Working demo — [try it live](https://ftbkfugig5aod9sq2g2mhm.streamlit.app/) |
| [`insight_narrator`](agents/insight_narrator/) | Upload a dataset, agent finds and narrates the 3 most interesting things in it - no question needed | Working demo |
| `data_quality` | Scans a dataset for quality issues (nulls, duplicates, type mismatches) and explains why they matter | Planned |
| `metric_definition` | Keeps metric definitions (e.g. "active user") consistent across teams | Planned |

## Try it

```bash
cd agents/nl_to_sql
pip install -r requirements.txt
cp .env.example .env   # add a real ANTHROPIC_API_KEY or GEMINI_API_KEY
python generate_data.py
streamlit run app.py
```

Ask things like:
- "What were the top 5 products by revenue?"
- "Which region had the biggest month-over-month growth in 2024?"
- "Are there any months with unusually low order volume?"

## Design principles
- **Transparency first** — every agent shows its work (generated SQL, confidence notes) rather than just handing over an answer
- **Read-only, sandboxed demos** — no agent here ever touches real production data or credentials; everything runs against local synthetic/public datasets
- **Deterministic where it matters** — statistical/data-quality detection uses real code, not LLM guessing; the LLM's job is generating queries and narrating results, not doing the analysis itself

## Roadmap
Full planning lives in a companion Obsidian vault (not in this repo). Short version: ship each agent as a standalone Streamlit demo, then embed the working demos into a personal data-analytics website.
