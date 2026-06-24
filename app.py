import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="RENENSP WBE Observatory",
    layout="wide"
)

st.title("Northeast Brazil WBE Drug Observatory")

st.caption(
    "Developed under RENENSP – Northeast Network for the Production of Secondary Reference Standards and Monitoring of New Psychoactive Substance Consumption through Wastewater-Based Epidemiology"
)

st.write("""
Public platform for monitoring classical drugs and new psychoactive substances (NPS)
through wastewater-based epidemiology (WBE) across Northeast Brazil.
""")

@st.cache_data
def load_data():
    df = pd.read_csv("renensp.csv")
    df["Sampling_Date"] = pd.to_datetime(df["Sampling_Date"], errors="coerce")
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("Filters")

state = st.sidebar.multiselect("State", sorted(df["State"].dropna().unique()))
city = st.sidebar.multiselect("City", sorted(df["City"].dropna().unique()))
event = st.sidebar.multiselect("Event", sorted(df["Event"].dropna().unique()))
period = st.sidebar.multiselect("Period", sorted(df["Period"].dropna().unique()))
platform = st.sidebar.multiselect("Analytical Platform", sorted(df["Analytical_Platform"].dropna().unique()))
analysis = st.sidebar.multiselect("Analysis Type", sorted(df["Analysis_Type"].dropna().unique()))
drug_class = st.sidebar.multiselect("Drug Class", sorted(df["Drug_Class"].dropna().unique()))
substance = st.sidebar.multiselect("Substance", sorted(df["Substance"].dropna().unique()))

filtered = df.copy()

if state:
    filtered = filtered[filtered["State"].isin(state)]
if city:
    filtered = filtered[filtered["City"].isin(city)]
if event:
    filtered = filtered[filtered["Event"].isin(event)]
if period:
    filtered = filtered[filtered["Period"].isin(period)]
if platform:
    filtered = filtered[filtered["Analytical_Platform"].isin(platform)]
if analysis:
    filtered = filtered[filtered["Analysis_Type"].isin(analysis)]
if drug_class:
    filtered = filtered[filtered["Drug_Class"].isin(drug_class)]
if substance:
    filtered = filtered[filtered["Substance"].isin(substance)]

# Overview
st.header("Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Records", len(filtered))
col2.metric("States", filtered["State"].nunique())
col3.metric("Substances", filtered["Substance"].nunique())
col4.metric("Events", filtered["Event"].nunique())

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Dashboard",
    "Target Quantification",
    "NPS Screening",
    "Data Table"
])

with tab1:
    st.subheader("General Dashboard")

    if len(filtered) > 0:
        colA, colB = st.columns(2)

        with colA:
            fig1 = px.histogram(
                filtered,
                x="Substance",
                color="Analysis_Type",
                title="Records by Substance"
            )
            st.plotly_chart(fig1, use_container_width=True)

        with colB:
            fig2 = px.histogram(
                filtered,
                x="Period",
                color="Detection",
                title="Detection by Period"
            )
            st.plotly_chart(fig2, use_container_width=True)

    else:
        st.warning("No data available for the selected filters.")

with tab2:
    st.subheader("Target Quantification – Triple Quadrupole MS/MS")

    quant = filtered[
        filtered["Analysis_Type"] == "Quantification"
    ]

    if len(quant) > 0:
        fig3 = px.line(
            quant,
            x="Event_Day",
            y="PNML_mg_day_1000inh",
            color="Substance",
            markers=True,
            title="Temporal Profile by Event Day"
        )
        st.plotly_chart(fig3, use_container_width=True)

        fig4 = px.bar(
            quant,
            x="Substance",
            y="PNML_mg_day_1000inh",
            color="Period",
            title="Population-Normalized Mass Load by Substance"
        )
        st.plotly_chart(fig4, use_container_width=True)

        st.dataframe(quant, use_container_width=True)
    else:
        st.info("No quantification data available for the selected filters.")

with tab3:
    st.subheader("NPS Screening – Orbitrap HRMS")

    screening = filtered[
        filtered["Analysis_Type"] == "Screening"
    ]

    if len(screening) > 0:
        detected = screening[screening["Detection"] == "Detected"]

        fig5 = px.histogram(
            detected,
            x="Substance",
            color="Period",
            title="Detected NPS by Period"
        )
        st.plotly_chart(fig5, use_container_width=True)

        detection_frequency = (
            screening
            .groupby(["Substance", "Detection"])
            .size()
            .reset_index(name="Count")
        )

        fig6 = px.bar(
            detection_frequency,
            x="Substance",
            y="Count",
            color="Detection",
            title="Screening Detection Frequency"
        )
        st.plotly_chart(fig6, use_container_width=True)

        st.dataframe(screening, use_container_width=True)
    else:
        st.info("No screening data available for the selected filters.")

with tab4:
    st.subheader("Complete Dataset")
    st.dataframe(filtered, use_container_width=True)

    csv = filtered.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download filtered data as CSV",
        data=csv,
        file_name="renensp_filtered_data.csv",
        mime="text/csv"
    )
