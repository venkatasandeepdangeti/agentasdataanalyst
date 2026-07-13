# Insight Narrator

Upload any CSV (or try the sample dataset) and the agent automatically finds and explains the 3 most interesting things in it — no question required. This is the "I don't know what to ask" companion to the [NL-to-SQL agent](../nl_to_sql/)'s "I know what to ask."

## How it stays trustworthy
Statistics are computed with real code (`profiler.py` - pandas/scipy, trend regression, z-score outlier detection, Pearson correlation), never guessed by the AI. The AI's only job is turning a real, computed statistic into a one-sentence plain-English headline. If the stats are wrong, that's a code bug you can find and fix - not an AI hallucination you can't verify.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then edit .env and set a real API key (Groq/Gemini/Anthropic)
python generate_data.py   # builds data/sales_performance.csv
streamlit run app.py
```

## Sample dataset
`generate_data.py` builds a synthetic 2-year daily sales dataset with three deliberate, findable patterns:
- **Trend**: revenue grows steadily over time
- **Outlier**: one deliberate stockout crash (Nov 15, North region)
- **Correlation**: marketing spend is strongly correlated with revenue

Upload your own CSV instead and it'll profile that - the sample is just there so the demo always has something real to find.

## Known issue: crashes on ARM64 (aarch64) Linux
If Streamlit segfaults, this is a known pyarrow bug (jemalloc background thread) on ARM64. Fix:
```bash
export ARROW_DEFAULT_MEMORY_POOL=system
streamlit run app.py
```
