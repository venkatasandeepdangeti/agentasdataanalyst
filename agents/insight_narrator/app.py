import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from agent import InsightNarratorAgent

load_dotenv()

if not os.path.exists("data/sales_performance.csv"):
    import generate_data
    generate_data.main()

st.set_page_config(page_title="Insight Narrator | AutoAnalyst", page_icon="\U0001F50D")

st.title("Insight Narrator")
st.caption(
    "Upload a dataset (or try the sample) and the agent automatically finds and explains the "
    "3 most interesting things in it - no question required. Stats are computed with real code, "
    "not guessed by the AI; the AI only writes the plain-English explanation."
)

if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY")):
    st.warning("Set an API key in .env (see .env.example) before analyzing.")

uploaded = st.file_uploader("Upload a CSV", type="csv")
use_sample = st.button("Or try the sample sales dataset")

df = None
date_col = None
label_cols = []

if uploaded:
    df = pd.read_csv(uploaded)
    # best-effort guess at a date column
    for col in df.columns:
        if "date" in col.lower():
            try:
                df[col] = pd.to_datetime(df[col])
                date_col = col
            except Exception:
                pass
            break
elif use_sample:
    df = pd.read_csv("data/sales_performance.csv", parse_dates=["date"])
    date_col = "date"
    label_cols = ["date"]

if df is not None:
    st.write(f"Loaded {len(df)} rows, {len(df.columns)} columns.")

    if "findings" not in st.session_state or st.session_state.get("_df_id") != id(df):
        with st.spinner("Profiling the dataset and writing explanations..."):
            try:
                agent = InsightNarratorAgent()
                st.session_state.findings = agent.analyze(df, date_col=date_col, label_cols=label_cols)
                st.session_state._df_id = id(df)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.session_state.findings = []

    findings = st.session_state.get("findings", [])

    if not findings:
        st.info("No statistically significant findings turned up in this dataset.")
    else:
        tabs = st.tabs([f"Finding {i+1}" for i in range(len(findings))])
        for tab, finding in zip(tabs, findings):
            with tab:
                st.subheader(finding["narration"])
                st.caption(f"Type: {finding['type']} · Column: {finding['column']} · Score: {finding['score']:.2f}")

                chart_data = finding["chart_data"]
                if finding["type"] == "correlation":
                    st.scatter_chart(chart_data, x=chart_data.columns[0], y=chart_data.columns[1])
                else:
                    st.line_chart(chart_data)
