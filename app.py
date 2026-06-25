import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="RENENSP WBE Observatory",
    layout="wide"
)

# ============================================================
# VISUAL STYLE
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f7fbfb 0%, #eef6f6 45%, #ffffff 100%);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1 {
        color: #005f63;
        font-weight: 900;
        letter-spacing: 1px;
    }

    h2, h3 {
        color: #12343b;
        font-weight: 750;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #003c43 0%, #005f63 100%);
    }

    [data-testid="stSidebar"] * {
        color: white;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #dbe7e7;
        padding: 18px;
        border-radius: 18px;
        box-shadow: 0 4px 14px rgba(0, 95, 99, 0.10);
    }

    div[data-testid="stMetric"] label {
        color: #005f63;
        font-weight: 700;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 14px 14px 0 0;
        padding: 10px 18px;
        border: 1px solid #dbe7e7;
    }

    .stTabs [aria-selected="true"] {
        background-color: #005f63 !important;
        color: white !important;
    }

    .stAlert {
        border-radius: 16px;
    }

    .stDataFrame {
        border-radius: 14px;
        overflow: hidden;
    }

    div.stButton > button {
        border-radius: 12px;
        border: 1px solid #005f63;
        color: #005f63;
        background-color: white;
        font-weight: 700;
    }

    div.stButton > button:hover {
        background-color: #005f63;
        color: white;
        border: 1px solid #005f63;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# REQUIRED COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "Year", "State", "City", "WWTP", "Event", "Sampling_Date", "Event_Day", "Period",
    "Substance", "Drug_Class", "Analytical_Platform", "Analysis_Type", "Detection",
    "Population_NH4N", "Load_g_day", "PNML_mg_day_1000inh"
]

# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():
    """Load renensp.csv with robust encoding and separator detection."""

    df = None
    read_errors = []

    for encoding in ["utf-8-sig", "utf-8", "latin-1"]:
        for sep in [",", ";", "\t"]:
            try:
                temp = pd.read_csv(
                    "renensp.csv",
                    sep=sep,
                    encoding=encoding,
                    engine="python"
                )
                temp.columns = temp.columns.str.strip().str.replace("\ufeff", "", regex=False)

                if all(col in temp.columns for col in ["Year", "State", "City", "WWTP", "Period"]):
                    df = temp
                    break
            except Exception as exc:
                read_errors.append(f"encoding={encoding}, sep={sep}: {exc}")

        if df is not None:
            break

    if df is None:
        st.error("The file renensp.csv was not read correctly.")
        st.write("Expected columns:", REQUIRED_COLUMNS)
        st.write("Read attempts:", read_errors[:5])
        st.stop()

    df = df.dropna(how="all")
    df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing:
        st.error(f"Missing columns in renensp.csv: {missing}")
        st.write("Columns found:", df.columns.tolist())
        st.stop()

    # Date and numeric conversion
    df["Sampling_Date"] = pd.to_datetime(df["Sampling_Date"], errors="coerce")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df["Event_Day"] = pd.to_numeric(df["Event_Day"], errors="coerce")
    df["Population_NH4N"] = pd.to_numeric(df["Population_NH4N"], errors="coerce")
    df["Load_g_day"] = pd.to_numeric(df["Load_g_day"], errors="coerce")
    df["PNML_mg_day_1000inh"] = pd.to_numeric(df["PNML_mg_day_1000inh"], errors="coerce")

    text_cols = [
        "State", "City", "WWTP", "Event", "Period", "Substance",
        "Drug_Class", "Analytical_Platform", "Analysis_Type", "Detection"
    ]

    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": None, "None": None, "": None})

    return df


df = load_data()

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def unique_sorted(dataframe, column):
    if column not in dataframe.columns or len(dataframe) == 0:
        return []
    return sorted(dataframe[column].dropna().unique().tolist())


def format_int(value):
    if pd.isna(value) or value is None:
        return "NA"
    return f"{int(value):,}"


def event_specific_population(dataframe):
    if len(dataframe) == 0 or "Population_NH4N" not in dataframe.columns:
        return None

    keys = ["Year", "State", "City", "WWTP", "Event"]

    pop = (
        dataframe
        .dropna(subset=["Population_NH4N"])
        .drop_duplicates(subset=keys)["Population_NH4N"]
        .sum()
    )

    if pd.isna(pop) or pop == 0:
        return None

    return pop


def get_population_table(dataframe):
    keys = ["Year", "State", "City", "WWTP", "Event"]

    return (
        dataframe
        .dropna(subset=["Population_NH4N"])
        .groupby(keys, as_index=False)["Population_NH4N"]
        .max()
        .sort_values(keys)
    )


def site_context_table(dataframe):
    cols = ["Year", "State", "City", "WWTP", "Event", "Period", "Population_NH4N"]

    if len(dataframe) == 0:
        return pd.DataFrame(columns=cols)

    return (
        dataframe[cols]
        .drop_duplicates()
        .sort_values(["Year", "State", "City", "WWTP", "Event", "Period"])
    )


def apply_local_filters(dataframe, prefix):
    """Add local filters inside a tab and return the filtered dataframe."""

    if len(dataframe) == 0:
        return dataframe

    st.markdown("### Spatial and Temporal Selection")
    st.caption(
        "Use these filters to identify exactly where and when the result was generated: "
        "Year → State → City → WWTP → Event → Period."
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        years = ["All"] + [str(int(y)) for y in unique_sorted(dataframe.dropna(subset=["Year"]), "Year")]
        year_choice = st.selectbox("Year", years, key=f"{prefix}_year")

    filtered_local = dataframe.copy()
    if year_choice != "All":
        filtered_local = filtered_local[filtered_local["Year"] == int(year_choice)]

    with c2:
        states = ["All"] + unique_sorted(filtered_local, "State")
        state_choice = st.selectbox("State", states, key=f"{prefix}_state")

    if state_choice != "All":
        filtered_local = filtered_local[filtered_local["State"] == state_choice]

    with c3:
        cities = ["All"] + unique_sorted(filtered_local, "City")
        city_choice = st.selectbox("City", cities, key=f"{prefix}_city")

    if city_choice != "All":
        filtered_local = filtered_local[filtered_local["City"] == city_choice]

    c4, c5, c6 = st.columns(3)

    with c4:
        wwtps = ["All"] + unique_sorted(filtered_local, "WWTP")
        wwtp_choice = st.selectbox("WWTP", wwtps, key=f"{prefix}_wwtp")

    if wwtp_choice != "All":
        filtered_local = filtered_local[filtered_local["WWTP"] == wwtp_choice]

    with c5:
        events = ["All"] + unique_sorted(filtered_local, "Event")
        event_choice = st.selectbox("Event", events, key=f"{prefix}_event")

    if event_choice != "All":
        filtered_local = filtered_local[filtered_local["Event"] == event_choice]

    with c6:
        periods = unique_sorted(filtered_local, "Period")
        period_choice = st.multiselect(
            "Period",
            periods,
            default=periods,
            key=f"{prefix}_period"
        )

    if period_choice:
        filtered_local = filtered_local[filtered_local["Period"].isin(period_choice)]

    context = site_context_table(filtered_local)

    st.markdown("### Selected Site Context")
    st.dataframe(context, use_container_width=True)

    return filtered_local


# ============================================================
# HEADER
# ============================================================

st.title("RENENSP")

st.caption(
    "Northeast Network for the Production of Secondary Reference Standards and Monitoring of "
    "New Psychoactive Substance Consumption through Wastewater-Based Epidemiology"
)

st.info(
    """
    The RENENSP Network is a collaborative initiative focused on monitoring classical drugs and
    new psychoactive substances (NPS) through wastewater-based epidemiology (WBE) across Northeast Brazil.

    This public platform provides open-access data generated by the network to support research,
    innovation, public health actions, and evidence-based policies.
    """
)

st.markdown("🔗 **PEM Research Group:** [@grupo.pem](https://www.instagram.com/grupo.pem/)")

# ============================================================
# SIDEBAR FILTERS
# ============================================================

try:
    st.sidebar.image("logo_renensp.png", use_container_width=True)
except Exception:
    st.sidebar.warning("Logo file not found: logo_renensp.png")

st.sidebar.header("Additional filters")

substance_filter = st.sidebar.multiselect("Substance", unique_sorted(df, "Substance"))
drug_class_filter = st.sidebar.multiselect("Drug Class", unique_sorted(df, "Drug_Class"))
platform_filter = st.sidebar.multiselect("Analytical Platform", unique_sorted(df, "Analytical_Platform"))
analysis_filter = st.sidebar.multiselect("Analysis Type", unique_sorted(df, "Analysis_Type"))
detection_filter = st.sidebar.multiselect("Detection", unique_sorted(df, "Detection"))

# ============================================================
# GLOBAL CASCADE NAVIGATION
# ============================================================

st.header("Data Navigation")
st.markdown(
    "Use the cascade below to navigate by **year**, **state**, **city**, **WWTP**, **event** and **period**. "
    "The analytical tabs also include their own local site filters so the origin of each result is always visible."
)

nav1, nav2, nav3 = st.columns(3)

with nav1:
    year_options = ["All"] + [str(int(y)) for y in unique_sorted(df.dropna(subset=["Year"]), "Year")]
    selected_year = st.selectbox("1. Select year", year_options)

df_year = df.copy()
if selected_year != "All":
    df_year = df_year[df_year["Year"] == int(selected_year)]

with nav2:
    state_options = ["All"] + unique_sorted(df_year, "State")
    selected_state = st.selectbox("2. Select state", state_options)

df_state = df_year.copy()
if selected_state != "All":
    df_state = df_state[df_state["State"] == selected_state]

with nav3:
    city_options = ["All"] + unique_sorted(df_state, "City")
    selected_city = st.selectbox("3. Select city", city_options)

df_city = df_state.copy()
if selected_city != "All":
    df_city = df_city[df_city["City"] == selected_city]

nav4, nav5, nav6 = st.columns(3)

with nav4:
    wwtp_options = ["All"] + unique_sorted(df_city, "WWTP")
    selected_wwtp = st.selectbox("4. Select WWTP", wwtp_options)

df_wwtp = df_city.copy()
if selected_wwtp != "All":
    df_wwtp = df_wwtp[df_wwtp["WWTP"] == selected_wwtp]

with nav5:
    event_options = ["All"] + unique_sorted(df_wwtp, "Event")
    selected_event = st.selectbox("5. Select event", event_options)

df_event = df_wwtp.copy()
if selected_event != "All":
    df_event = df_event[df_event["Event"] == selected_event]

with nav6:
    period_options = unique_sorted(df_event, "Period")
    selected_periods = st.multiselect("6. Select period", period_options, default=period_options)

filtered = df_event.copy()

if selected_periods:
    filtered = filtered[filtered["Period"].isin(selected_periods)]

if substance_filter:
    filtered = filtered[filtered["Substance"].isin(substance_filter)]
if drug_class_filter:
    filtered = filtered[filtered["Drug_Class"].isin(drug_class_filter)]
if platform_filter:
    filtered = filtered[filtered["Analytical_Platform"].isin(platform_filter)]
if analysis_filter:
    filtered = filtered[filtered["Analysis_Type"].isin(analysis_filter)]
if detection_filter:
    filtered = filtered[filtered["Detection"].isin(detection_filter)]

# ============================================================
# OVERVIEW
# ============================================================

st.header("Overview")

detected_nps = filtered[
    (filtered["Analysis_Type"] == "Screening") &
    (filtered["Drug_Class"] != "Classical") &
    (filtered["Detection"] == "Detected")
]

population_covered = event_specific_population(filtered)

col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)

col1.metric("Monitoring results", len(filtered))
col2.metric("Years", filtered["Year"].nunique())
col3.metric("States", filtered["State"].nunique())
col4.metric("Cities", filtered["City"].nunique())
col5.metric("WWTPs", filtered["WWTP"].nunique())
col6.metric("Events", filtered["Event"].nunique())
col7.metric("Detected NPS", detected_nps["Substance"].nunique())
col8.metric("Population covered", format_int(population_covered))

st.caption(
    "Population covered is calculated from unique year–state–city–WWTP–event combinations, "
    "avoiding repeated counts across substances from the same sampling context."
)

# ============================================================
# TABS
# ============================================================

tab_about, tab_partners, tab_map, tab_dashboard, tab_population, tab_quantification, tab_screening, tab_events, tab_method, tab_data = st.tabs([
    "About the Project",
    "Partner Institutions",
    "Interactive Map",
    "Dashboard",
    "Population",
    "Target Quantification",
    "Screening",
    "Events",
    "Methodology",
    "Data Explorer"
])

# ============================================================
# ABOUT THE PROJECT
# ============================================================

with tab_about:
    st.subheader("About the RENENSP Project")

    st.markdown(
        """
        **Project title:**  
        Northeast Network for the Production of Secondary Reference Standards and Monitoring of New Psychoactive
        Substance Consumption through Wastewater-Based Epidemiology – RENENSP

        **Original title in Portuguese:**  
        Rede Nordeste de produção de padrões secundários e monitoramento do consumo através da epidemiologia do esgoto
        de novas substâncias psicoativas – RENENSP

        **Funding call:**  
        PROCAD – Academic Cooperation Support Action – Drug Policies  
        Joint Call No. 2/2024 – CAPES/SENAD

        **Proponent institution:** Federal Rural University of Pernambuco (UFRPE)  
        **Graduate program:** Graduate Program in Chemistry – UFRPE  
        **Project period:** November 2024 to October 2029  
        **Duration:** 60 months  
        **Knowledge area:** Chemistry  
        **Thematic axis:** Axis 2 – New Psychoactive Substances (NPS)

        ### Project description
        RENENSP aims to establish an academic and scientific cooperation network involving higher education institutions
        and public security agencies. The project focuses on the production of secondary reference standards for NPS and
        the monitoring of NPS consumption through wastewater-based epidemiology in Northeast Brazil.
        """
    )

    st.markdown("---")
    st.subheader("Platform Information")

    st.markdown(
        """
        **RENENSP Observatory**

        Developed under the PROCAD CAPES/SENAD Project.

        ### Project Coordination
        **Prof. Dr. Jandyson Machado Santos**  
        Federal Rural University of Pernambuco (UFRPE)  
        📧 jandyson.machado@ufrpe.br

        ### Platform Development
        **Dr. Bruna Ramos de Souza Gomes**  
        Platform Developer  
        📧 brunaramosquimica@gmail.com

        ### Research Group
        **PEM – Petroleum, Energy and Mass Spectrometry Research Group**  
        Instagram: [@grupo.pem](https://www.instagram.com/grupo.pem/)

        © RENENSP Network – 2026
        """
    )

# ============================================================
# PARTNER INSTITUTIONS
# ============================================================

with tab_partners:
    st.subheader("Partner Institutions and Research Team")

    st.markdown(
        """
        ### Coordination
        **Principal Coordinator:** Jandyson Machado Santos – PPGQ/UFRPE  
        **Associate Coordinator:** Josean Fechine Tavares – PgPNSB/UFPB

        ### Partner Teams
        - Adriana Santos Ribeiro – PGMateriais/UFAL
        - Alberto Wisniewski Jr – PPGQ/UFS
        - Alexandro M. L. de Assis – Federal Police/AL and PGMateriais/UFAL
        - Beate Saegesser Santos – Department of Pharmacy/UFPE
        - Cezar Silvino Gomes – Federal Police/PB
        - Cícero Flávio Soares Aragão – Department of Pharmacy/UFRN
        - Cíntia Maria do Rego Barros Veiga – Scientific Police Institute/PB
        - Elaine Andrade de Oliveira Bezerra – Scientific Police Institute/PB
        - Marcos José Brandão Guimarães – Technical-Scientific Institute of Forensics/RN
        - Mônica Paulo de Souza – Federal Police/PB
        - Ricardo Saldanha Honorato – Federal Police/PE
        - Rosana Coutinho Freire Silva – Scientific Police of Alagoas
        - Socrates Golzio dos Santos – Department of Pharmacy/UFPB
        """
    )

# ============================================================
# MAP
# ============================================================

with tab_map:
    st.subheader("Interactive Monitoring Map")
    st.info("Use the mouse wheel, double click, or zoom buttons to explore the map.")

    wwtp_coords = pd.DataFrame({
        "State": ["PE", "PE", "PB", "PB", "RN", "AL", "SE", "CE", "BA", "MA", "PI"],
        "City": ["Recife", "Olinda", "Joao Pessoa", "Campina Grande", "Natal", "Maceio", "Aracaju", "Fortaleza", "Salvador", "Sao Luis", "Teresina"],
        "WWTP": ["Cabanga", "Peixinho", "Mangabeira", "Catingueira", "Jundiai-Guarapes", "Benedito Bentes", "Orlando Dantas", "Coco", "Boca do Rio", "Vinhais", "Piraja"],
        "lat": [-8.071, -7.999, -7.175, -7.2307, -5.7945, -9.6498, -10.9472, -3.7319, -12.9777, -2.5307, -5.0892],
        "lon": [-34.884, -34.860, -34.845, -35.8817, -35.2110, -35.7089, -37.0731, -38.5267, -38.5016, -44.3068, -42.8016],
    })

    map_data = (
        filtered
        .groupby(["Year", "State", "City", "WWTP"], as_index=False)
        .agg(
            Monitoring_Results=("Substance", "count"),
            Population_NH4N=("Population_NH4N", "max")
        )
        .merge(wwtp_coords, on=["State", "City", "WWTP"], how="left")
    )

    missing_coords = map_data[map_data["lat"].isna()]

    if len(missing_coords) > 0:
        st.warning(
            "Some WWTPs do not have coordinates yet. Add them to the wwtp_coords table in app.py to display them on the map."
        )

    map_data = map_data.dropna(subset=["lat", "lon"])

    if len(map_data) > 0:
        fig_map = px.scatter_mapbox(
            map_data,
            lat="lat",
            lon="lon",
            size="Monitoring_Results",
            color="State",
            hover_name="WWTP",
            hover_data={
                "Year": True,
                "State": True,
                "City": True,
                "Monitoring_Results": True,
                "Population_NH4N": True,
                "lat": False,
                "lon": False,
            },
            zoom=5,
            height=650,
            title="RENENSP monitoring coverage by WWTP"
        )

        fig_map.update_layout(
            mapbox_style="open-street-map",
            dragmode="zoom",
            mapbox=dict(center=dict(lat=-7.8, lon=-37.2), zoom=4.5),
            margin={"r": 0, "t": 40, "l": 0, "b": 0}
        )

        st.plotly_chart(
            fig_map,
            use_container_width=True,
            config={"scrollZoom": True, "displayModeBar": True, "displaylogo": False}
        )
    else:
        st.info("No mapped WWTPs available for the selected filters.")

# ============================================================
# GENERAL DASHBOARD
# ============================================================

with tab_dashboard:
    st.subheader("General Dashboard")

    if len(filtered) > 0:
        colA, colB = st.columns(2)

        with colA:
            fig = px.histogram(
                filtered,
                x="Substance",
                color="Analysis_Type",
                title="Monitoring results by substance"
            )
            st.plotly_chart(fig, use_container_width=True)

        with colB:
            fig = px.histogram(
                filtered,
                x="WWTP",
                color="State",
                title="Monitoring results by WWTP"
            )
            st.plotly_chart(fig, use_container_width=True)

        colC, colD = st.columns(2)

        with colC:
            fig = px.histogram(
                filtered,
                x="Event",
                color="Year",
                title="Monitoring results by event and year"
            )
            st.plotly_chart(fig, use_container_width=True)

        with colD:
            fig = px.histogram(
                filtered,
                x="Period",
                color="Detection",
                title="Detection by period"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")

# ============================================================
# POPULATION
# ============================================================

with tab_population:
    st.subheader("Population Estimated by NH4-N")
    st.info("Population_NH4N is year-, event-, WWTP- and sampling-day-specific.")

    available_years = sorted(filtered["Year"].dropna().unique())

    selected_pop_year = st.selectbox(
        "Select year for population view",
        ["All"] + [str(int(y)) for y in available_years],
        key="population_year"
    )

    pop_filtered = filtered.copy()

    if selected_pop_year != "All":
        pop_filtered = pop_filtered[pop_filtered["Year"] == int(selected_pop_year)]

    pop_table = get_population_table(pop_filtered)

    if len(pop_table) > 0:
        fig_pop_wwtp = px.bar(
            pop_table,
            x="WWTP",
            y="Population_NH4N",
            color="State",
            barmode="group",
            title=f"Estimated Population by WWTP ({selected_pop_year})",
            labels={"Population_NH4N": "Estimated population (NH4-N)", "WWTP": "WWTP"}
        )
        st.plotly_chart(fig_pop_wwtp, use_container_width=True)

        fig_pop_event = px.bar(
            pop_table,
            x="Event",
            y="Population_NH4N",
            color="WWTP",
            barmode="group",
            title=f"Estimated Population by Event and WWTP ({selected_pop_year})",
            labels={"Population_NH4N": "Estimated population (NH4-N)", "Event": "Event"}
        )
        st.plotly_chart(fig_pop_event, use_container_width=True)

        st.markdown("### Population Summary")
        st.dataframe(pop_table, use_container_width=True)
    else:
        st.info("No population data available for the selected filters.")

# ============================================================
# TARGET QUANTIFICATION
# ============================================================

with tab_quantification:
    st.subheader("Target Quantification – Triple Quadrupole MS/MS")

    quant_base = filtered[filtered["Analysis_Type"] == "Quantification"]
    quant_local = apply_local_filters(quant_base, "quant") if len(quant_base) > 0 else quant_base

    classical_quant = quant_local[quant_local["Drug_Class"] == "Classical"]
    nps_quant = quant_local[quant_local["Drug_Class"] != "Classical"]

    qtab1, qtab2 = st.tabs(["Classical Drugs", "Quantified NPS"])

    with qtab1:
        st.markdown("### Classical Drugs Quantification")

        if len(classical_quant) > 0:
            fig_load_classical = px.bar(
                classical_quant,
                x="WWTP",
                y="Load_g_day",
                color="Substance",
                barmode="group",
                facet_col="Event",
                hover_data=["Year", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                title="Classical Drugs – Load by WWTP and Event",
                labels={"Load_g_day": "Load (g/day)", "WWTP": "WWTP"}
            )
            st.plotly_chart(fig_load_classical, use_container_width=True)

            fig_pnml_classical = px.bar(
                classical_quant,
                x="WWTP",
                y="PNML_mg_day_1000inh",
                color="Substance",
                barmode="group",
                facet_col="Event",
                hover_data=["Year", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                title="Classical Drugs – PNML by WWTP and Event",
                labels={"PNML_mg_day_1000inh": "PNML (mg/day/1000 inhabitants)", "WWTP": "WWTP"}
            )
            st.plotly_chart(fig_pnml_classical, use_container_width=True)

            temporal_classical = classical_quant.dropna(subset=["Event_Day", "PNML_mg_day_1000inh"])

            if temporal_classical["Event_Day"].nunique() > 1:
                fig_trend_classical = px.line(
                    temporal_classical.sort_values("Event_Day"),
                    x="Event_Day",
                    y="PNML_mg_day_1000inh",
                    color="Substance",
                    line_dash="Event",
                    markers=True,
                    facet_col="WWTP",
                    hover_data=["Year", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                    title="Classical Drugs – Temporal Profile by WWTP",
                    labels={"Event_Day": "Event day", "PNML_mg_day_1000inh": "PNML (mg/day/1000 inhabitants)"}
                )
                st.plotly_chart(fig_trend_classical, use_container_width=True)
            else:
                st.info("Temporal profile requires more than one Event_Day.")

            st.markdown("### Classical Drugs Dataset")
            st.dataframe(classical_quant, use_container_width=True)
        else:
            st.info("No classical drug quantification data available for the selected filters.")

    with qtab2:
        st.markdown("### Quantified NPS")

        if len(nps_quant) > 0:
            fig_load_nps = px.bar(
                nps_quant,
                x="WWTP",
                y="Load_g_day",
                color="Substance",
                barmode="group",
                facet_col="Event",
                hover_data=["Year", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                title="Quantified NPS – Load by WWTP and Event",
                labels={"Load_g_day": "Load (g/day)", "WWTP": "WWTP"}
            )
            st.plotly_chart(fig_load_nps, use_container_width=True)

            fig_pnml_nps = px.bar(
                nps_quant,
                x="WWTP",
                y="PNML_mg_day_1000inh",
                color="Substance",
                barmode="group",
                facet_col="Event",
                hover_data=["Year", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                title="Quantified NPS – PNML by WWTP and Event",
                labels={"PNML_mg_day_1000inh": "PNML (mg/day/1000 inhabitants)", "WWTP": "WWTP"}
            )
            st.plotly_chart(fig_pnml_nps, use_container_width=True)

            temporal_nps = nps_quant.dropna(subset=["Event_Day", "PNML_mg_day_1000inh"])

            if temporal_nps["Event_Day"].nunique() > 1:
                fig_trend_nps = px.line(
                    temporal_nps.sort_values("Event_Day"),
                    x="Event_Day",
                    y="PNML_mg_day_1000inh",
                    color="Substance",
                    line_dash="Event",
                    markers=True,
                    facet_col="WWTP",
                    hover_data=["Year", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                    title="Quantified NPS – Temporal Profile by WWTP",
                    labels={"Event_Day": "Event day", "PNML_mg_day_1000inh": "PNML (mg/day/1000 inhabitants)"}
                )
                st.plotly_chart(fig_trend_nps, use_container_width=True)
            else:
                st.info("Temporal profile requires more than one Event_Day.")

            st.markdown("### Quantified NPS Dataset")
            st.dataframe(nps_quant, use_container_width=True)
        else:
            st.info("No quantified NPS data available for the selected filters.")

# ============================================================
# SCREENING
# ============================================================

with tab_screening:
    st.subheader("Screening – Orbitrap HRMS")

    screening_base = filtered[filtered["Analysis_Type"] == "Screening"]
    screening_local = apply_local_filters(screening_base, "screen") if len(screening_base) > 0 else screening_base

    screening_classical = screening_local[screening_local["Drug_Class"] == "Classical"]
    screening_nps = screening_local[screening_local["Drug_Class"] != "Classical"]

    stab1, stab2 = st.tabs(["Classical Drugs", "NPS"])

    with stab1:
        st.markdown("### Classical Drugs Screening")

        if len(screening_classical) > 0:
            fig_classical_screen = px.histogram(
                screening_classical,
                x="WWTP",
                color="Detection",
                facet_col="Event",
                hover_data=["Year", "State", "City", "WWTP", "Event", "Period", "Sampling_Date", "Substance"],
                title="Classical Drugs Screening by WWTP and Event"
            )
            st.plotly_chart(fig_classical_screen, use_container_width=True)

            fig_classical_substance = px.histogram(
                screening_classical,
                x="Substance",
                color="Detection",
                facet_col="WWTP",
                hover_data=["Year", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                title="Classical Drugs Screening by Substance and WWTP"
            )
            st.plotly_chart(fig_classical_substance, use_container_width=True)

            st.markdown("### Classical Drugs Screening Dataset")
            st.dataframe(screening_classical, use_container_width=True)
        else:
            st.info("No classical drug screening data available for the selected filters.")

    with stab2:
        st.markdown("### NPS Screening")

        if len(screening_nps) > 0:
            detected_nps_local = screening_nps[screening_nps["Detection"] == "Detected"]

            fig_nps_by_wwtp = px.histogram(
                detected_nps_local,
                x="WWTP",
                color="Substance",
                facet_col="Event",
                hover_data=["Year", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                title="Detected NPS by WWTP and Event"
            )
            st.plotly_chart(fig_nps_by_wwtp, use_container_width=True)

            detection_frequency = (
                screening_nps
                .groupby(["Year", "State", "City", "WWTP", "Event", "Substance", "Detection"])
                .size()
                .reset_index(name="Count")
            )

            fig_nps_frequency = px.bar(
                detection_frequency,
                x="WWTP",
                y="Count",
                color="Detection",
                facet_col="Event",
                hover_data=["Year", "State", "City", "WWTP", "Event", "Substance"],
                title="NPS Detection Frequency by WWTP and Event"
            )
            st.plotly_chart(fig_nps_frequency, use_container_width=True)

            heatmap_data = (
                screening_nps
                .assign(Detected_Num=screening_nps["Detection"].eq("Detected").astype(int))
                .pivot_table(
                    index="Substance",
                    columns="WWTP",
                    values="Detected_Num",
                    aggfunc="sum",
                    fill_value=0
                )
            )

            fig_heatmap = px.imshow(
                heatmap_data,
                text_auto=True,
                aspect="auto",
                title="NPS Detection Heatmap by Substance and WWTP"
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)

            st.markdown("### NPS Screening Dataset")
            st.dataframe(screening_nps, use_container_width=True)
        else:
            st.info("No NPS screening data available for the selected filters.")

# ============================================================
# EVENTS
# ============================================================

with tab_events:
    st.subheader("Event Comparison")

    if len(filtered) > 0:
        event_overview = (
            filtered
            .groupby(["Year", "Event", "State", "City", "WWTP"])
            .agg(
                Monitoring_Results=("Event", "count"),
                Substances=("Substance", "nunique"),
                Population=("Population_NH4N", "max")
            )
            .reset_index()
        )

        fig_event = px.bar(
            event_overview,
            x="WWTP",
            y="Monitoring_Results",
            color="State",
            barmode="group",
            facet_col="Event",
            hover_data=["Year", "State", "City", "WWTP", "Event", "Population"],
            title="Monitoring results by WWTP, event and state"
        )
        st.plotly_chart(fig_event, use_container_width=True)

        quant_events = filtered[filtered["Analysis_Type"] == "Quantification"]

        if len(quant_events) > 0:
            fig_compare = px.bar(
                quant_events,
                x="WWTP",
                y="PNML_mg_day_1000inh",
                color="Substance",
                barmode="group",
                facet_col="Event",
                hover_data=["Year", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                title="Quantified substances across WWTPs and events",
                labels={"PNML_mg_day_1000inh": "PNML"}
            )
            st.plotly_chart(fig_compare, use_container_width=True)

        st.markdown("### Event Overview")
        st.dataframe(event_overview, use_container_width=True)
    else:
        st.info("No event data available for the selected filters.")

# ============================================================
# METHODOLOGY
# ============================================================

with tab_method:
    st.subheader("Methodology")

    st.markdown(
        """
        ### Wastewater-Based Epidemiology
        Wastewater-based epidemiology (WBE) estimates community-level exposure or consumption of chemical substances by
        measuring biomarkers, parent compounds, or transformation products in wastewater samples.

        ### Analytical Platforms
        **Triple Quadrupole MS/MS** is used for target quantification of selected substances.  
        **Orbitrap HRMS** is used for screening of classical drugs and new psychoactive substances (NPS).

        ### Main Indicators
        **WWTP** identifies the wastewater treatment plant or sampling site.  
        **Population_NH4N** represents the population estimated based on ammoniacal nitrogen and can vary by year, event,
        WWTP and sampling day.  
        **Load (g/day)** represents the estimated daily mass load entering the wastewater system.  
        **PNML (mg/day/1000 inhabitants)** represents the population-normalized mass load.

        ### Interpretation
        Results should always be interpreted together with the spatial context: State, City and WWTP. This is why the
        quantification and screening tabs include site-specific filters and site context tables.
        """
    )

# ============================================================
# DATA EXPLORER
# ============================================================

with tab_data:
    st.subheader("Complete Dataset")

    st.dataframe(filtered, use_container_width=True)

    csv = filtered.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download filtered data as CSV",
        data=csv,
        file_name="renensp_filtered_data.csv",
        mime="text/csv"
    )

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    """
    RENENSP Observatory | PROCAD CAPES/SENAD  
    Project Coordinator: Prof. Dr. Jandyson Machado Santos (UFRPE)  
    Platform Developer: Dr. Bruna Ramos de Souza Gomes  
    © 2026 RENENSP Network
    """
)
