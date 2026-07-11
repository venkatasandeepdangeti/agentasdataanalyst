import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from agent import NLToSQLAgent

load_dotenv()

st.set_page_config(page_title="NL-to-SQL Agent | AutoAnalyst", page_icon="\U0001F4CA")

st.title("NL-to-SQL Agent")
st.caption("Ask a question about the demo e-commerce dataset in plain English. The agent writes the SQL, runs it, and explains the result.")

SAMPLE_QUESTIONS = [
    "What were the top 5 products by revenue?",
    "Which region had the biggest month-over-month growth in 2024?",
    "Are there any months with unusually low order volume?",
]

if "history" not in st.session_state:
    st.session_state.history = []  # list of {"question": str, "result": dict | None, "error": str | None}

with st.sidebar:
    st.subheader("Try a sample question")
    for q in SAMPLE_QUESTIONS:
        if st.button(q, use_container_width=True):
            st.session_state.pending_question = q

if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY")):
    st.warning("Set an API key in .env (see .env.example) before asking questions.")

question = st.chat_input("Ask a question about this data...")
if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    st.session_state.history.append({"question": question, "result": None, "error": None})

agent = None

for turn in st.session_state.history:
    with st.chat_message("user"):
        st.write(turn["question"])
    with st.chat_message("assistant"):
        # Only run the agent once per turn - cache the outcome so replaying earlier
        # turns on rerun doesn't re-call the LLM (costly and slow).
        if turn["result"] is None and turn["error"] is None:
            with st.spinner("Thinking..."):
                try:
                    agent = agent or NLToSQLAgent()
                    turn["result"] = agent.ask(turn["question"])
                except Exception as e:
                    turn["error"] = str(e)

        if turn["error"]:
            st.error(f"Something went wrong: {turn['error']}")
            continue

        result = turn["result"]
        with st.expander("Generated SQL"):
            st.code(result["sql"], language="sql")

        df: pd.DataFrame = result["result"]
        st.dataframe(df, use_container_width=True)

        numeric_cols = df.select_dtypes(include="number").columns
        if len(df.columns) >= 2 and len(numeric_cols) >= 1:
            try:
                chart_df = df.set_index(df.columns[0])[numeric_cols[0]]
                st.bar_chart(chart_df)
            except Exception:
                pass

        st.write(result["narration"])
