# Data Quality Agent

Scans a dataset for real, verifiable quality issues before they poison a dashboard or a decision. The "boring but critical" agent — nulls, duplicate IDs, numbers-stored-as-text, impossible dates.

## How it stays trustworthy
Issues are found with real code (`checker.py` - pandas, no LLM involved in detection). The AI's only job is explaining why a found issue matters and suggesting a fix. Severity scores (0-10) are hand-calibrated by business impact, not a raw statistical magnitude - a duplicate ID and a 5% missing-value rate aren't comparable on the same scale, so they're scored deliberately, not automatically.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then edit .env and set a real API key (Groq/Gemini/Anthropic)
python generate_data.py   # builds data/customers.csv
streamlit run app.py
```

## Sample dataset
`generate_data.py` builds a synthetic customer dataset with four deliberately planted issues:
- **Missing values**: ~8% of rows have a null email
- **Duplicates**: 5 customer IDs each appear twice
- **Type mismatch**: ~15 rows have `lifetime_revenue` stored as `"$1,234.56"` text, which silently blocks summing/averaging the column
- **Invalid dates**: 3 rows have a signup date in the future

Upload your own CSV instead and it'll scan that - the sample just guarantees the demo always finds something real.

## Known issue: crashes on ARM64 (aarch64) Linux
If Streamlit segfaults, this is a known pyarrow bug (jemalloc background thread) on ARM64. Fix:
```bash
export ARROW_DEFAULT_MEMORY_POOL=system
streamlit run app.py
```
