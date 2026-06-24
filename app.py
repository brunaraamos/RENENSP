import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="RENENSP",
    layout="wide"
)

st.title("Northeast Brazil WBE Drug Observatory")

st.caption(
    "Developed under RENENSP – Northeast Network for the Production of Secondary Reference Standards and Monitoring of New Psychoactive Substance Consumption through Wastewater-Based Epidemiology"
)

st.write("""
The platform provides open-access data on classical drugs and new psychoactive substances (NPS)
monitored across Northeast Brazil through wastewater-based epidemiology (WBE).
""")

@st.cache_data
def load_data():
    return pd.read_csv("renensp.csv")

df = load_data()

st.sidebar.header("Filters")

state = st.sidebar.multiselect(
    "State",
    sorted(df["state"].dropna().unique())
)

event = st.sidebar.multiselect(
    "Event",
    sorted(df["event"].dropna().unique())
)

group = st.sidebar.multiselect(
    "Drug group",
    sorted(df["group"].dropna().unique())
)

analysis = st.sidebar.multiselect(
    "Analysis type",
    sorted(df["analysis_type"].dropna().unique())
)

filtered = df.copy()

if state:
    filtered = filtered[filtered["state"].isin(state)]

if event:
    filtered = filtered[filtered["event"].isin(event)]

if group:
    filtered = filtered[filtered["group"].isin(group)]

if analysis:
    filtered = filtered[filtered["analysis_type"].isin(analysis)]

st.header("Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Records", len(filtered))
col2.metric("States", filtered["state"].nunique())
col3.metric("Substances", filtered["substance"].nunique())
col4.metric("Events", filtered["event"].nunique())

st.header("Filtered Data")
st.dataframe(filtered, use_container_width=True)

st.header("Drug Categories")

tab1, tab2 = st.tabs(["Classical Drugs", "New Psychoactive Substances (NPS)"])

with tab1:
    classical = filtered[filtered["group"] == "Classical"]
    st.subheader("Classical Drugs")
    st.dataframe(classical, use_container_width=True)

with tab2:
    nps = filtered[filtered["group"] == "NPS"]
    st.subheader("New Psychoactive Substances (NPS)")
    st.dataframe(nps, use_container_width=True)
