import os

import streamlit as st
from dotenv import load_dotenv

from agent import MetricDefinitionAgent
from glossary import GLOSSARY

load_dotenv()

st.set_page_config(page_title="Metric Definition Agent | AutoAnalyst", page_icon="\U0001F4CF")

st.title("Metric Definition Agent")
st.caption(
    "Every company eventually has 3 different definitions of \"active user\" in 3 different "
    "dashboards. This agent checks a submitted SQL definition against the canonical one and "
    "explains any real difference in plain English - not a text diff, a meaning diff."
)

if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY")):
    st.warning("Set an API key in .env (see .env.example) before comparing.")

metric_name = st.selectbox("Metric", list(GLOSSARY.keys()))
metric = GLOSSARY[metric_name]

col1, col2 = st.columns(2)

with col1:
    st.subheader("Canonical definition")
    st.write(metric["description"])
    st.code(metric["canonical_sql"], language="sql")

with col2:
    st.subheader("Submitted SQL")
    st.caption("Pre-filled with a real example mismatch - edit it to test your own version, or fix it and see the agent confirm a match.")
    submitted_sql = st.text_area(
        "SQL to check", value=metric["example_submission"], height=160, label_visibility="collapsed",
        key=f"submitted_sql_{metric_name}",  # forces reset when switching metrics, not just on first load
    )

if st.button("Compare", type="primary"):
    with st.spinner("Comparing definitions..."):
        try:
            agent = MetricDefinitionAgent()
            result = agent.compare(
                metric_name=metric_name,
                description=metric["description"],
                canonical_sql=metric["canonical_sql"],
                submitted_sql=submitted_sql,
            )
            if result["verdict"] == "MATCH":
                st.success(f"✅ MATCH — {result['explanation']}")
            else:
                st.error(f"⚠️ MISMATCH — {result['explanation']}")
        except Exception as e:
            st.error(f"Something went wrong: {e}")
