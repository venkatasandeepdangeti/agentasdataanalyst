import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from agent import DataQualityAgent

load_dotenv()

if not os.path.exists("data/customers.csv"):
    import generate_data
    generate_data.main()

st.set_page_config(page_title="Data Quality Agent | AutoAnalyst", page_icon="\U0001F9EA")

st.title("Data Quality Agent")
st.caption(
    "Scans a dataset for real, verifiable quality issues (nulls, duplicates, type mismatches, "
    "invalid dates) before they poison a dashboard or a decision. Issues are found with real code, "
    "not guessed by the AI; the AI only explains why each one matters and suggests a fix."
)

if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY")):
    st.warning("Set an API key in .env (see .env.example) before scanning.")

uploaded = st.file_uploader("Upload a CSV", type="csv")
use_sample = st.button("Or try the sample messy customer dataset")

df = None
id_col = None
date_cols = []

if uploaded:
    df = pd.read_csv(uploaded)
elif use_sample:
    df = pd.read_csv("data/customers.csv")
    id_col = "customer_id"
    date_cols = ["signup_date"]

SEVERITY_COLORS = {9: "🔴", 8: "🔴", 7: "🟠", 6: "🟠", 5: "🟡", 4: "🟡", 3: "🟢"}


def severity_icon(score):
    return SEVERITY_COLORS.get(round(score), "🟢" if score < 4 else "🔴")


if df is not None:
    st.write(f"Loaded {len(df)} rows, {len(df.columns)} columns.")

    if "issues" not in st.session_state or st.session_state.get("_df_id") != id(df):
        with st.spinner("Scanning for quality issues and writing explanations..."):
            try:
                agent = DataQualityAgent()
                st.session_state.issues = agent.scan(df, id_col=id_col, date_cols=date_cols)
                st.session_state._df_id = id(df)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.session_state.issues = []

    issues = st.session_state.get("issues", [])

    if not issues:
        st.success("No quality issues found above the detection thresholds.")
    else:
        st.write(f"Found {len(issues)} issue(s), sorted by severity:")
        for issue in issues:
            icon = severity_icon(issue["severity"])
            with st.expander(f"{icon} {issue['type'].replace('_', ' ').title()} — `{issue['column']}` (severity {issue['severity']:.1f}/10)"):
                st.write(issue["explanation"])
                st.caption(f"Detail: {issue['detail']}")
