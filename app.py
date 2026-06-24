import streamlit as st

st.set_page_config(
    page_title="RENENSP",
    layout="wide"
)

st.title("RENENSP")

st.write("""
The Northeast Brazil WBE Drug Observatory is a public platform developed under RENENSP (Northeast Network for the Production of Secondary Reference Standards and Monitoring of New Psychoactive Substance Consumption through Wastewater-Based Epidemiology). The platform provides open-access data on classical drugs and new psychoactive substances (NPS) monitored across Northeast Brazil.
""")

st.header("Monitored States")

st.write("""
- Pernambuco
- Paraíba
- Rio Grande do Norte
""")

st.header("Drug Categories")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Classical Drugs")
    st.write("• Screening")
    st.write("• Quantification")

with col2:
    st.subheader("New Psychoactive Substances (NPS)")
    st.write("• Screening")
    st.write("• Quantification")

st.header("Target Events")

st.write("""
- Carnival
- São João Festival
- New Year's Eve
- Reference Weeks
- Special Events
""")
