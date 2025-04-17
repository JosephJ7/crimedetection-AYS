import streamlit as st
import pandas as pd
import sys
import os
import subprocess

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import pg_engine
from data_pipeline import visualizations as vz

st.set_page_config(layout="wide", page_title="📊 Ireland Crime Dashboard")
st.title("📊 Ireland Crime Dashboard")

# Sidebar - Dataset Selector
dataset = st.sidebar.radio("Select Dataset", ["Offence Type", "Offender Age"])

# Disable UI elements when Dagster is running
dagster_running = False

# -----------------------------
# 📌 Dataset: Offence Type
# -----------------------------
if dataset == "Offence Type":
    df = pd.read_sql("SELECT * FROM crime_offence_garda", pg_engine)
    st.header("🔍 Crime by Offence Type")

    viz = st.selectbox("Choose Visualization", [
        "Overall Crime Trend",
        "Quarterly Crime Trend",
        "Top Garda Divisions",
        "Quarterly by Offence Type",
        "Average Crime by Offence Type",
        "Quarterly Distribution"
    ], disabled=dagster_running)  # Disable selection if Dagster job is running

    # Optional filters
    if "offence_type" in df.columns:
        offence_filter = st.multiselect("Filter by Offence Type", sorted(df["offence_type"].unique()), disabled=dagster_running)
        if offence_filter:
            df = df[df["offence_type"].isin(offence_filter)]

    if "garda_division" in df.columns and "Top Garda" in viz:
        division_filter = st.multiselect("Filter by Garda Division", sorted(df["garda_division"].unique()), disabled=dagster_running)
        if division_filter:
            df = df[df["garda_division"].isin(division_filter)]

    # Plotly charts
    charts = {
        "Overall Crime Trend": vz.overall_crime_trend,
        "Quarterly Crime Trend": vz.quarterly_crime_trend,
        "Top Garda Divisions": vz.top_garda_divisions,
        "Quarterly by Offence Type": vz.quarterly_crime_trend_by_offence_type,
        "Average Crime by Offence Type": vz.average_crime_trend_by_offence_type,
        "Quarterly Distribution": vz.crime_distribution_per_quarter
    }

    if viz in charts:
        st.plotly_chart(charts[viz](df), use_container_width=True)

# -----------------------------
# 📌 Dataset: Offender Age
# -----------------------------
elif dataset == "Offender Age":
    df = pd.read_sql("SELECT * FROM crime_offence_age", pg_engine)
    st.header("🔍 Crime by Offender Age")

    viz = st.selectbox("Choose Visualization", [
        "Total Crime by Age Over Time",
        "Heatmap of Age vs Year",
        "Latest Year",
        "Age Over Time (Animated)",
        "Proportional Area Chart"
    ], disabled=dagster_running)  # Disable selection if Dagster job is running

    # Filter by age group
    age_filter = st.multiselect("Filter by Age Group", sorted(df["suspected_offender_age"].unique()), disabled=dagster_running)
    if age_filter:
        df = df[df["suspected_offender_age"].isin(age_filter)]

    charts = {
        "Total Crime by Age Over Time": vz.crime_by_age,
        "Heatmap of Age vs Year": vz.crime_age_heatmap,
        "Latest Year": vz.crime_age_bar_latest,
        "Age Over Time (Animated)": vz.crime_age_bar_over_time,
        "Proportional Area Chart": vz.crime_age_area
    }

    if viz in charts:
        st.plotly_chart(charts[viz](df), use_container_width=True)

# Sidebar - Dagster Job Control
st.sidebar.markdown("## ⚙️ Data Pipeline")

# Run Dagster job
if st.sidebar.button("🚀 Run Dagster Job", disabled=dagster_running):
    with st.spinner("Running Dagster `combined_pipeline_job`..."):
        dagster_running = True  

        result = subprocess.run(
            ["dagster", "job", "execute", "-f", "data_pipeline/project_master.py", "-j", "combined_pipeline_job"],
            capture_output=True,
            text=True
        )
        # dagster_result = result
        dagster_running = False  # Reset the flag after job completes
        if result.returncode == 0:
            st.sidebar.success("✅ Dagster job completed successfully!")
        else:
            st.sidebar.error("❌ Dagster job failed")
            st.sidebar.code(result.stderr, language="bash")
