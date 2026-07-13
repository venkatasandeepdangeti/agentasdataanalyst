"""Deterministic data quality checks - finds real, verifiable issues in a dataframe.
No LLM involved in detection, only in explaining/suggesting fixes for what's found here.

Severity is hand-calibrated (0-10) based on business impact, not a raw statistical magnitude -
a duplicate ID and a 0.6 correlation aren't on the same scale, so don't score them as if they were.
"""
import re

import pandas as pd


def check_missing_values(df: pd.DataFrame, threshold: float = 0.02) -> list[dict]:
    issues = []
    for col in df.columns:
        missing_pct = df[col].isna().mean()
        if missing_pct > threshold:
            issues.append({
                "type": "missing_values",
                "column": col,
                "severity": min(3 + missing_pct * 5, 7),
                "detail": {
                    "missing_count": int(df[col].isna().sum()),
                    "missing_pct": missing_pct,
                    "total_rows": len(df),
                },
            })
    return issues


def check_duplicates(df: pd.DataFrame, id_col: str) -> list[dict]:
    issues = []
    dup_mask = df[id_col].duplicated(keep=False)
    if dup_mask.any():
        dup_ids = sorted(df.loc[dup_mask, id_col].unique().tolist())
        issues.append({
            "type": "duplicates",
            "column": id_col,
            "severity": 9,
            "detail": {
                "duplicate_id_count": len(dup_ids),
                "duplicate_row_count": int(dup_mask.sum()),
                "example_ids": dup_ids[:5],
            },
        })
    return issues


def check_type_mismatch(df: pd.DataFrame) -> list[dict]:
    issues = []
    for col in df.columns:
        if not (df[col].dtype == object or pd.api.types.is_string_dtype(df[col])):
            continue
        non_null = df[col].dropna()
        if len(non_null) == 0:
            continue

        raw_numeric = pd.to_numeric(non_null, errors="coerce")
        cleaned = non_null.astype(str).str.replace(r"[$,]", "", regex=True)
        cleaned_numeric = pd.to_numeric(cleaned, errors="coerce")

        raw_fraction = raw_numeric.notna().mean()
        cleaned_fraction = cleaned_numeric.notna().mean()

        # If values only become numeric AFTER stripping currency symbols/commas, the raw
        # column is numbers wearing a costume - it can't be summed/averaged as-is, even
        # though every value is "really" a number underneath.
        if cleaned_fraction > 0.95 and raw_fraction < cleaned_fraction:
            dirty_mask = raw_numeric.isna() & cleaned_numeric.notna()
            bad_examples = non_null[dirty_mask].head(3).tolist()
            issues.append({
                "type": "type_mismatch",
                "column": col,
                "severity": 8,
                "detail": {
                    "dirty_fraction": 1 - raw_fraction,
                    "bad_value_examples": bad_examples,
                },
            })
    return issues


def check_invalid_dates(df: pd.DataFrame, date_cols: list[str], max_date: str = None) -> list[dict]:
    issues = []
    max_ts = pd.Timestamp(max_date) if max_date else pd.Timestamp.now()
    for col in date_cols:
        if col not in df.columns:
            continue
        parsed = pd.to_datetime(df[col], errors="coerce")
        future_mask = parsed > max_ts
        if future_mask.any():
            issues.append({
                "type": "invalid_dates",
                "column": col,
                "severity": 6,
                "detail": {
                    "future_count": int(future_mask.sum()),
                    "example_values": parsed[future_mask].dt.strftime("%Y-%m-%d").head(3).tolist(),
                    "max_valid_date": max_ts.strftime("%Y-%m-%d"),
                },
            })
    return issues


def run_all_checks(df: pd.DataFrame, id_col: str = None, date_cols: list[str] = None) -> list[dict]:
    issues = []
    issues += check_missing_values(df)
    if id_col:
        issues += check_duplicates(df, id_col)
    issues += check_type_mismatch(df)
    if date_cols:
        issues += check_invalid_dates(df, date_cols)

    issues.sort(key=lambda i: i["severity"], reverse=True)
    return issues
