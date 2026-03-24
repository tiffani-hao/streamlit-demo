import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import plotly.graph_objects as go

from mock_algo import load_and_prepare, run_mock_cusum

# Title settings
st.set_page_config(page_title="CUSUM Demo", layout="wide")
st.header("HIV Cluster Alerts Demo")
st.caption("The 'CUSUM' here is a mock algorithm for UI demonstration.")
st.text("""This tool utilizes the cumulative sum (CUSUM) method to help detect unusual increases in case counts over time.
In this demo, users can upload monthly case count data and view simple alert outputs and visualizations.""")

# Sidebar settings
with st.sidebar:
    st.header("Settings")
    threshold = st.number_input("Threshold", min_value=0.0, max_value=50.0, value=4.0, step=0.5)

# Upload CSV
uploaded = st.file_uploader("Upload a CSV (month, county, cases)", type=["csv"])

if uploaded is None:
    st.info("Please upload a CSV file to begin.")
    st.stop()

df = pd.read_csv(uploaded)

if df is None:
    st.stop()

st.divider()

# Data preview
try:
    prepared = load_and_prepare(df)
except Exception as e:
    st.error(str(e))
    st.stop()

st.subheader("Data preview")
c1, c2, c3 = st.columns(3)
c1.metric("Counties", prepared["county"].nunique())
c2.metric("Months", prepared["month"].nunique())
c3.metric("Range", f"{prepared['month'].min()} → {prepared['month'].max()}")

st.divider()

# Run CUSUM algorithm
per_month, episodes = run_mock_cusum(prepared, threshold=threshold)

st.subheader("Alerts")
if episodes.empty:
    st.info("No alerts detected (try lowering the threshold).")
else:
    st.dataframe(episodes, use_container_width=True)

    # Download alerts
    ep_dl = episodes.copy()
    for c in ["alert_start_month", "detection_month", "alert_end_month"]:
        if c in ep_dl.columns:
            ep_dl[c] = ep_dl[c].astype(str)

    st.download_button(
        "Download alerts.csv",
        data=ep_dl.to_csv(index=False).encode("utf-8"),
        file_name="alerts.csv",
        mime="text/csv",
    )

# Download per-month metrics
pm_dl = per_month.copy()
pm_dl["month"] = pm_dl["month"].astype(str)
st.download_button(
    "Download per_month_metrics.csv",
    data=pm_dl.to_csv(index=False).encode("utf-8"),
    file_name="per_month_metrics.csv",
    mime="text/csv",
)

st.divider()

# Visualizations
st.subheader("Visualizations")
county_list = sorted(prepared["county"].unique().tolist())
selected = st.selectbox("Select county", county_list)
col1, col2 = st.columns(2)

g = per_month[per_month["county"] == selected].sort_values("month").copy()
x = g["month"].astype(str).tolist()

# Alert windows for shading
shades = []
if not episodes.empty:
    ep_c = episodes[episodes["county"] == selected]
    for _, row in ep_c.iterrows():
        start = str(row["alert_start_month"])
        end = None if pd.isna(row["alert_end_month"]) else str(row["alert_end_month"])
        shades.append((start, end))

# Colors
raw_color = "#E76BA3"
smooth_color = "#B07CC6"
baseline_color = "#6C8AE4"
cusum_color = "#8E63B7"
threshold_color = "#C85A9E"
shade_color = "#F7D4E5"

# Plot 1: cases & baseline
with col1:
    fig1 = go.Figure()

    fig1.add_trace(go.Scatter(
        x=x,
        y=g["cases_raw"],
        mode="lines",
        name="raw case count",
        line=dict(color=raw_color),
        hovertemplate="Month: %{x}<br>Raw case count: %{y}<extra></extra>"
    ))

    fig1.add_trace(go.Scatter(
        x=x,
        y=g["cases_smoothed"],
        mode="lines",
        name="smoothed case count",
        line=dict(color=smooth_color),
        hovertemplate="Month: %{x}<br>Smoothed case count: %{y:.2f}<extra></extra>"
    ))

    fig1.add_trace(go.Scatter(
        x=x,
        y=g["baseline"],
        mode="lines",
        name="baseline",
        line=dict(color=baseline_color),
        hovertemplate="Month: %{x}<br>Baseline: %{y:.2f}<extra></extra>"
    ))

    for start, end in shades:
        if start in x:
            x0 = start
            x1 = x[-1] if end is None or end not in x else end
            fig1.add_vrect(
                x0=x0,
                x1=x1,
                fillcolor=shade_color,
                opacity=0.15,
                line_width=0
            )

    fig1.update_layout(
        title=f"{selected} County - Case Count & Baseline (alerts shaded)",
        xaxis_title="Year",
        yaxis_title="Case Count",
        hovermode="x unified",
        legend=dict(font=dict(size=10)),
        xaxis=dict(tickangle=90, tickfont=dict(size=8)),
        yaxis=dict(tickfont=dict(size=8)),
        margin=dict(l=40, r=20, t=60, b=80)
    )

    st.plotly_chart(fig1, use_container_width=True)

# Plot 2: CUSUM curve
with col2:
    fig2 = go.Figure()

    fig2.add_trace(go.Scatter(
        x=x,
        y=g["cusum"],
        mode="lines",
        name="CUSUM value",
        line=dict(color=cusum_color),
        hovertemplate="Month: %{x}<br>CUSUM value: %{y:.2f}<extra></extra>"
    ))

    fig2.add_trace(go.Scatter(
        x=x,
        y=[threshold] * len(x),
        mode="lines",
        name="threshold",
        line=dict(color=threshold_color, dash="dash"),
        hovertemplate="Month: %{x}<br>Threshold: %{y:.2f}<extra></extra>"
    ))

    fig2.update_layout(
        title=f"{selected} County - CUSUM Value",
        xaxis_title="Year",
        yaxis_title="CUSUM Value",
        hovermode="x unified",
        legend=dict(font=dict(size=10)),
        xaxis=dict(tickangle=90, tickfont=dict(size=8)),
        yaxis=dict(tickfont=dict(size=8)),
        margin=dict(l=40, r=20, t=60, b=80)
    )

    st.plotly_chart(fig2, use_container_width=True)