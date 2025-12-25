import os
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(os.getenv("USAGE_DB_PATH", "usage_metrics.sqlite")).resolve()

st.set_page_config(page_title="Usage Dashboard", page_icon="📊", layout="wide")
st.title("📊 Bot Usage Dashboard")
st.caption(f"Data source: {DB_PATH}")


@st.cache_data(ttl=30)
def load_events(limit: int = 2000) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?",
            conn,
            params=(limit,),
        )
    finally:
        conn.close()
    if df.empty:
        return df
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    df["success"] = df["success"].fillna(0).astype(int).astype(bool)
    return df


def render_metrics(df: pd.DataFrame):
    latency = df["latency_ms"].dropna()
    success_count = int(df["success"].sum())
    total = len(df)
    fail = total - success_count
    cols = st.columns(4)
    cols[0].metric("Total requests", f"{total}")
    cols[1].metric("Success rate", f"{(success_count/total*100):.1f}%" if total else "0%")
    if not latency.empty:
        cols[2].metric("P50 latency (ms)", f"{latency.quantile(0.5):.0f}")
        cols[3].metric("P90 latency (ms)", f"{latency.quantile(0.9):.0f}")
    else:
        cols[2].metric("P50 latency (ms)", "–")
        cols[3].metric("P90 latency (ms)", "–")
    st.metric("Errors", f"{fail}")


def render_charts(df: pd.DataFrame):
    with st.expander("Persona mix", expanded=True):
        st.bar_chart(df["persona"].value_counts())
    if "ts" in df.columns and not df["ts"].isna().all():
        daily = df.set_index("ts").resample("D").size()
        with st.expander("Requests per day", expanded=True):
            st.line_chart(daily)
    with st.expander("Query types", expanded=False):
        st.bar_chart(df["query_type"].value_counts())


def render_tables(df: pd.DataFrame):
    st.subheader("Recent requests")
    st.dataframe(df[["ts", "persona", "query_type", "success", "latency_ms", "error", "raw_query"]].head(50))
    errors = df[df["success"] == False]
    if not errors.empty:
        st.subheader("Recent errors")
        st.dataframe(errors[["ts", "persona", "query_type", "error", "raw_query"]].head(50))


def main():
    df = load_events()
    if df.empty:
        st.info("No usage data yet. Once the bot handles requests, logs will appear here.")
        return
    render_metrics(df)
    render_charts(df)
    render_tables(df)


if __name__ == "__main__":
    main()
