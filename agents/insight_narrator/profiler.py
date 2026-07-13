"""Deterministic statistical profiling - finds candidate "interesting things" in a dataframe.
No LLM involved here on purpose: the agent's job is to narrate what the stats found, not to
invent the stats itself. Keeps findings trustworthy and reproducible.
"""
import numpy as np
import pandas as pd
from scipy import stats


def find_trend_findings(df: pd.DataFrame, date_col: str, numeric_cols: list[str]) -> list[dict]:
    findings = []
    df_sorted = df.sort_values(date_col)
    x = np.arange(len(df_sorted))

    for col in numeric_cols:
        y = df_sorted[col].values
        if np.std(y) == 0:
            continue
        result = stats.linregress(x, y)
        if result.pvalue < 0.01 and abs(result.rvalue) > 0.2:
            findings.append({
                "type": "trend",
                "column": col,
                "score": abs(result.rvalue),
                "detail": {
                    "slope": result.slope,
                    "r_value": result.rvalue,
                    "p_value": result.pvalue,
                    "direction": "increasing" if result.slope > 0 else "decreasing",
                },
                "chart_data": df_sorted.set_index(date_col)[col],
            })
    return findings


def find_outlier_findings(df: pd.DataFrame, numeric_cols: list[str], label_cols: list[str]) -> list[dict]:
    findings = []
    for col in numeric_cols:
        z_scores = pd.Series(np.abs(stats.zscore(df[col])), index=df.index)
        max_idx = z_scores.idxmax()
        max_z = z_scores.loc[max_idx]
        if max_z > 3:
            row = df.loc[max_idx]
            labels = {lc: row[lc] for lc in label_cols if lc in row}
            findings.append({
                "type": "outlier",
                "column": col,
                "score": max_z,
                "row_key": max_idx,  # identifies which underlying row/event this outlier is about
                "detail": {
                    "value": row[col],
                    "mean": df[col].mean(),
                    "z_score": max_z,
                    "row_labels": labels,
                },
                "chart_data": df[col],
            })
    return findings


def find_correlation_findings(df: pd.DataFrame, numeric_cols: list[str]) -> list[dict]:
    findings = []
    seen = set()
    for i, col_a in enumerate(numeric_cols):
        for col_b in numeric_cols[i + 1:]:
            if (col_a, col_b) in seen:
                continue
            seen.add((col_a, col_b))
            r, p = stats.pearsonr(df[col_a], df[col_b])
            if p < 0.01 and abs(r) > 0.4:
                findings.append({
                    "type": "correlation",
                    "column": f"{col_a} vs {col_b}",
                    "score": abs(r),
                    "detail": {"col_a": col_a, "col_b": col_b, "r_value": r, "p_value": p},
                    "chart_data": df[[col_a, col_b]],
                })
    return findings


def top_findings(df: pd.DataFrame, date_col: str | None, numeric_cols: list[str],
                  label_cols: list[str], n: int = 3) -> list[dict]:
    candidates = []
    if date_col:
        candidates += find_trend_findings(df, date_col, numeric_cols)
    candidates += find_outlier_findings(df, numeric_cols, label_cols)
    candidates += find_correlation_findings(df, numeric_cols)

    candidates.sort(key=lambda f: f["score"], reverse=True)

    # The only real redundancy risk: multiple outlier findings pointing to the same
    # underlying row/event (e.g. one crash day showing up as an outlier in both revenue
    # and units sold - that's one story, not two). A trend and an outlier about the same
    # column are NOT redundant - they're two different, complementary observations.
    def is_redundant(f, seen_row_keys):
        return f["type"] == "outlier" and f["row_key"] in seen_row_keys

    def mark_seen(f, seen_row_keys):
        if f["type"] == "outlier":
            seen_row_keys.add(f["row_key"])

    seen_row_keys = set()
    diverse = []

    # Prefer variety first: take the single strongest candidate of each distinct type
    # (a demo/dashboard with a trend + an outlier + a correlation is more useful than
    # the same type of finding three times, even if a second outlier scores higher).
    for finding_type in ("outlier", "trend", "correlation"):
        for f in candidates:
            if f["type"] != finding_type:
                continue
            if is_redundant(f, seen_row_keys):
                continue
            diverse.append(f)
            mark_seen(f, seen_row_keys)
            break
        if len(diverse) >= n:
            break

    # Fill any remaining slots with the next-best candidates regardless of type
    for f in candidates:
        if len(diverse) >= n:
            break
        if f in diverse or is_redundant(f, seen_row_keys):
            continue
        diverse.append(f)
        mark_seen(f, seen_row_keys)

    diverse.sort(key=lambda f: f["score"], reverse=True)
    return diverse if diverse else candidates[:n]
