import streamlit as st
from utils.data_loader import load_data
import utils.visualizations as vz

st.set_page_config(layout="wide")
st.title("📊 Ireland Crime Data Dashboard")

# Sidebar
dataset = st.sidebar.selectbox("Select Dataset", [
    "crime_offence_garda", "suspect_offender_age"
])
st.sidebar.write("Powered by Streamlit & Plotly")

# Load data
df = load_data(dataset)

# Preprocess
if dataset == "crime_offence_garda":
    df["year"] = df["Quarter"].str.extract(r'(\d{4})').astype(int)
    df["quarter_number"] = df["Quarter"].str.extract(r'(Q[1-4])')
    df["count"] = pd.to_numeric(df["count"], errors="coerce")
else:
    df["count"] = pd.to_numeric(df["count"], errors="coerce")

# Visualize
st.subheader("📈 Trends")

if dataset == "crime_offence_garda":
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(vz.overall_crime_trend(df), use_container_width=True)
    with col2:
        st.plotly_chart(vz.quarterly_trend(df), use_container_width=True)
    
    st.subheader("📍 Regions")
    st.plotly_chart(vz.pie_top_divisions(df), use_container_width=True)

else:
    st.plotly_chart(vz.crime_by_age(df), use_container_width=True)
    st.plotly_chart(vz.crime_age_heatmap(df), use_container_width=True)
