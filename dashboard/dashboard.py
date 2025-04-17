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


st.sidebar.markdown("## ⚙️ Data Pipeline")
if "dagster_running" not in st.session_state:
    st.session_state.dagster_running = False

dagster_status = st.sidebar.empty()

with st.sidebar:
    if st.button("🚀 Run Dagster Job", disabled=st.session_state.dagster_running):
        with st.spinner("Running Dagster `combined_pipeline_job`..."):
            st.session_state.dagster_running = True
            result = subprocess.run(
                ["dagster", "job", "execute", "-f", "data_pipeline/project_master.py", "-j", "combined_pipeline_job"],
                capture_output=True,
                text=True
            )
            st.session_state.dagster_running = False

            if result.returncode == 0:
                dagster_status.success("✅ Dagster job completed successfully!")
                st.rerun()
            else:
                dagster_status.error("❌ Dagster job failed")
                st.code(result.stderr, language="bash")

st.sidebar.markdown("----")

dataset = st.sidebar.radio("🗄️ Select Dataset", ["Offence Type", "Offender Age"])


if dataset == "Offence Type":
    df = pd.read_sql("SELECT * FROM crime_offence_garda", pg_engine)
    
    if df.empty:
        st.warning("⚠️ No data available to display.")
        
    st.subheader("🔍 Crime by Offence Type")

    offence_filter = st.sidebar.multiselect("🔎 Filter by Offence Type", sorted(df["offence_type"].unique()))
    if offence_filter:
        df = df[df["offence_type"].isin(offence_filter)]

    division_filter = st.sidebar.multiselect("🏢 Filter by Garda Division", sorted(df["garda_division"].unique()))
    if division_filter:
        df = df[df["garda_division"].isin(division_filter)]
    
    if df.empty:
        st.warning("⚠️ No data available for the selected filters.")
    else:
        st.plotly_chart(vz.overall_crime_trend(df), use_container_width=True)
        st.plotly_chart(vz.quarterly_crime_trend(df), use_container_width=True)
        st.plotly_chart(vz.top_garda_divisions(df), use_container_width=True)
        st.plotly_chart(vz.quarterly_crime_trend_by_offence_type(df), use_container_width=True)
        st.plotly_chart(vz.average_crime_trend_by_offence_type(df), use_container_width=True)
        st.plotly_chart(vz.crime_distribution_per_quarter(df), use_container_width=True)

elif dataset == "Offender Age":
    df = pd.read_sql("SELECT * FROM crime_offence_age", pg_engine)
    
    if df.empty:
        st.warning("⚠️ No data available to display.")
    st.subheader("👥 Crime by Offender Age")

    age_filter = st.sidebar.multiselect("🎂 Filter by Age Group", sorted(df["suspected_offender_age"].unique()))
    if age_filter:
        df = df[df["suspected_offender_age"].isin(age_filter)]
    
    if df.empty:
        st.warning("⚠️ No data available for the selected filters.")
    else:
        st.plotly_chart(vz.crime_by_age(df), use_container_width=True)
        st.plotly_chart(vz.crime_age_heatmap(df), use_container_width=True)
        st.plotly_chart(vz.crime_age_bar_latest(df), use_container_width=True)
        st.plotly_chart(vz.crime_age_bar_over_time(df), use_container_width=True)
        st.plotly_chart(vz.crime_age_area(df), use_container_width=True)
