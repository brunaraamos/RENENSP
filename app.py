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

TEXT_COLUMNS = [
    "Year", "State", "City", "WWTP", "Event", "Period", "Substance", "Drug_Class",
    "Analytical_Platform", "Analysis_Type", "Detection", "Sampling_Date", "Local"
]

# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_data():
    """Load renensp.csv robustly and return Plotly-safe data types."""
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
        st.write("Read attempts:", read_errors[:10])
        st.stop()

    df = df.dropna(how="all")
    df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        st.error(f"Missing columns in renensp.csv: {missing}")
        st.write("Columns found:", df.columns.tolist())
        st.stop()

    # Dates as display strings avoid Plotly/Numpy dtype promotion issues in Cloud.
    df["Sampling_Date"] = pd.to_datetime(df["Sampling_Date"], errors="coerce").dt.strftime("%Y-%m-%d")

    # Year as string avoids pandas nullable integer problems with Plotly + NumPy 2.
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64").astype(str)
    df["Year"] = df["Year"].replace({"<NA>": None, "nan": None})

    numeric_cols = ["Event_Day", "Population_NH4N", "Load_g_day", "PNML_mg_day_1000inh"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    text_cols = [
        "State", "City", "WWTP", "Event", "Period", "Substance",
        "Drug_Class", "Analytical_Platform", "Analysis_Type", "Detection"
    ]
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": None, "None": None, "": None})

    df["Local"] = df["State"].fillna("") + " - " + df["City"].fillna("")

    return df


df = load_data()

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def unique_sorted(dataframe, column):
    if dataframe is None or len(dataframe) == 0 or column not in dataframe.columns:
        return []
    values = dataframe[column].dropna().unique().tolist()
    return sorted(values)


def format_int(value):
    if pd.isna(value) or value is None:
        return "NA"
    return f"{int(value):,}"


def event_specific_population(dataframe):
    if len(dataframe) == 0 or "Population_NH4N" not in dataframe.columns:
        return None

    keys = ["Year", "State", "City", "WWTP", "Event"]
    pop = (
        dataframe.dropna(subset=["Population_NH4N"])
        .drop_duplicates(subset=keys)["Population_NH4N"]
        .sum()
    )

    if pd.isna(pop) or pop == 0:
        return None
    return pop


def get_population_table(dataframe):
    keys = ["Year", "State", "City", "WWTP", "Event"]
    if len(dataframe) == 0:
        return pd.DataFrame(columns=keys + ["Population_NH4N"])
    return (
        dataframe.dropna(subset=["Population_NH4N"])
        .groupby(keys, as_index=False)["Population_NH4N"]
        .max()
        .sort_values(keys)
    )


def site_context_table(dataframe):
    cols = ["Year", "Local", "State", "City", "WWTP", "Event", "Period", "Population_NH4N"]
    if len(dataframe) == 0:
        return pd.DataFrame(columns=cols)
    return (
        dataframe[cols]
        .drop_duplicates()
        .sort_values(["Year", "State", "City", "WWTP", "Event", "Period"])
    )


def make_plot_df(dataframe, y_columns=None):
    """Return a Plotly-safe copy with text columns as strings and y columns numeric."""
    if y_columns is None:
        y_columns = []

    plot_df = dataframe.copy()

    for col in TEXT_COLUMNS:
        if col in plot_df.columns:
            plot_df[col] = plot_df[col].astype(str)
            plot_df[col] = plot_df[col].replace({"None": "", "nan": "", "<NA>": ""})

    for col in y_columns:
        if col in plot_df.columns:
            plot_df[col] = pd.to_numeric(plot_df[col], errors="coerce")

    required = [col for col in y_columns if col in plot_df.columns]
    if required:
        plot_df = plot_df.dropna(subset=required)

    return plot_df


def apply_local_filters(dataframe, prefix, label):
    """Add Year -> Local -> WWTP -> Event -> Period filters and show selected context."""
    if len(dataframe) == 0:
        return dataframe

    st.markdown(f"### {label}: Year → Local → WWTP → Event → Period")
    st.caption(
        "These filters make the spatial and temporal origin explicit for every result. "
        "Local combines State and City. WWTP identifies the wastewater treatment plant."
    )

    c1, c2, c3 = st.columns(3)

    filtered_local = dataframe.copy()

    with c1:
        years = ["All"] + unique_sorted(filtered_local, "Year")
        year_choice = st.selectbox("Year", years, key=f"{prefix}_year")
    if year_choice != "All":
        filtered_local = filtered_local[filtered_local["Year"] == year_choice]

    with c2:
        locals_ = ["All"] + unique_sorted(filtered_local, "Local")
        local_choice = st.selectbox("Local", locals_, key=f"{prefix}_local")
    if local_choice != "All":
        filtered_local = filtered_local[filtered_local["Local"] == local_choice]

    with c3:
        wwtps = ["All"] + unique_sorted(filtered_local, "WWTP")
        wwtp_choice = st.selectbox("WWTP", wwtps, key=f"{prefix}_wwtp")
    if wwtp_choice != "All":
        filtered_local = filtered_local[filtered_local["WWTP"] == wwtp_choice]

    c4, c5 = st.columns(2)

    with c4:
        events = ["All"] + unique_sorted(filtered_local, "Event")
        event_choice = st.selectbox("Event", events, key=f"{prefix}_event")
    if event_choice != "All":
        filtered_local = filtered_local[filtered_local["Event"] == event_choice]

    with c5:
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

    with st.expander("Selected Site Context", expanded=False):
        st.dataframe(context, use_container_width=True)

    return filtered_local


def empty_message(text):
    st.info(text)

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
    "Use the cascade below to navigate globally by **Year**, **Local**, **WWTP**, **Event** and **Period**. "
    "Each analytical tab also has its own local filters so that Quantification and Screening can be explored independently."
)

nav1, nav2, nav3 = st.columns(3)

with nav1:
    year_options = ["All"] + unique_sorted(df, "Year")
    selected_year = st.selectbox("1. Select year", year_options)

df_year = df.copy()
if selected_year != "All":
    df_year = df_year[df_year["Year"] == selected_year]

with nav2:
    local_options = ["All"] + unique_sorted(df_year, "Local")
    selected_local = st.selectbox("2. Select local", local_options)

df_local = df_year.copy()
if selected_local != "All":
    df_local = df_local[df_local["Local"] == selected_local]

with nav3:
    wwtp_options = ["All"] + unique_sorted(df_local, "WWTP")
    selected_wwtp = st.selectbox("3. Select WWTP", wwtp_options)

df_wwtp = df_local.copy()
if selected_wwtp != "All":
    df_wwtp = df_wwtp[df_wwtp["WWTP"] == selected_wwtp]

nav4, nav5 = st.columns(2)

with nav4:
    event_options = ["All"] + unique_sorted(df_wwtp, "Event")
    selected_event = st.selectbox("4. Select event", event_options)

df_event = df_wwtp.copy()
if selected_event != "All":
    df_event = df_event[df_event["Event"] == selected_event]

with nav5:
    period_options = unique_sorted(df_event, "Period")
    selected_periods = st.multiselect("5. Select period", period_options, default=period_options)

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
    "Population covered is calculated from unique year-state-city-WWTP-event combinations, "
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
        Substance Consumption through Wastewater-Based Epidemiology - RENENSP

        **Original title in Portuguese:**  
        Rede Nordeste de produção de padrões secundários e monitoramento do consumo através da epidemiologia do esgoto
        de novas substâncias psicoativas - RENENSP

        **Funding call:**  
        PROCAD - Academic Cooperation Support Action - Drug Policies  
        Joint Call No. 2/2024 - CAPES/SENAD

        **Proponent institution:** Federal Rural University of Pernambuco (UFRPE)  
        **Graduate program:** Graduate Program in Chemistry - UFRPE  
        **Project period:** November 2024 to October 2029  
        **Duration:** 60 months  
        **Knowledge area:** Chemistry  
        **Thematic axis:** Axis 2 - New Psychoactive Substances (NPS)

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
        **PEM - Petroleum, Energy and Mass Spectrometry Research Group**  
        Instagram: [@grupo.pem](https://www.instagram.com/grupo.pem/)

        © RENENSP Network - 2026
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
        **Principal Coordinator:** Jandyson Machado Santos - PPGQ/UFRPE  
        **Associate Coordinator:** Josean Fechine Tavares - PgPNSB/UFPB

        ### Partner Teams
        - Adriana Santos Ribeiro - PGMateriais/UFAL
        - Alberto Wisniewski Jr - PPGQ/UFS
        - Alexandro M. L. de Assis - Federal Police/AL and PGMateriais/UFAL
        - Beate Saegesser Santos - Department of Pharmacy/UFPE
        - Cezar Silvino Gomes - Federal Police/PB
        - Cícero Flávio Soares Aragão - Department of Pharmacy/UFRN
        - Cíntia Maria do Rego Barros Veiga - Scientific Police Institute/PB
        - Elaine Andrade de Oliveira Bezerra - Scientific Police Institute/PB
        - Marcos José Brandão Guimarães - Technical-Scientific Institute of Forensics/RN
        - Mônica Paulo de Souza - Federal Police/PB
        - Ricardo Saldanha Honorato - Federal Police/PE
        - Rosana Coutinho Freire Silva - Scientific Police of Alagoas
        - Socrates Golzio dos Santos - Department of Pharmacy/UFPB
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
        filtered.groupby(["Year", "State", "City", "Local", "WWTP"], as_index=False)
        .agg(Monitoring_Results=("Substance", "count"), Population_NH4N=("Population_NH4N", "max"))
        .merge(wwtp_coords, on=["State", "City", "WWTP"], how="left")
    )

    missing_coords = map_data[map_data["lat"].isna()]
    if len(missing_coords) > 0:
        st.warning("Some WWTPs do not have coordinates yet. Add them to the wwtp_coords table in app.py to display them on the map.")

    map_data = map_data.dropna(subset=["lat", "lon"])
    map_data = make_plot_df(map_data, y_columns=["Monitoring_Results", "Population_NH4N"])

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
                "Local": True,
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
        st.plotly_chart(fig_map, use_container_width=True, config={"scrollZoom": True, "displayModeBar": True, "displaylogo": False})
    else:
        empty_message("No mapped WWTPs available for the selected filters.")

# ============================================================
# DASHBOARD
# ============================================================

with tab_dashboard:
    st.subheader("General Dashboard")

    dashboard_plot = make_plot_df(filtered)

    if len(dashboard_plot) > 0:
        colA, colB = st.columns(2)
        with colA:
            fig = px.histogram(dashboard_plot, x="Substance", color="Analysis_Type", title="Monitoring results by substance")
            st.plotly_chart(fig, use_container_width=True)
        with colB:
            fig = px.histogram(dashboard_plot, x="Local", color="State", title="Monitoring results by local")
            st.plotly_chart(fig, use_container_width=True)

        colC, colD = st.columns(2)
        with colC:
            fig = px.histogram(dashboard_plot, x="WWTP", color="Event", title="Monitoring results by WWTP and event")
            st.plotly_chart(fig, use_container_width=True)
        with colD:
            fig = px.histogram(dashboard_plot, x="Period", color="Detection", title="Detection by period")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")

# ============================================================
# POPULATION
# ============================================================

with tab_population:
    st.subheader("Population Estimated by NH4-N")
    st.info("Population_NH4N is year-, event-, WWTP- and sampling-day-specific.")

    available_years = unique_sorted(filtered, "Year")
    selected_pop_year = st.selectbox("Select year for population view", ["All"] + available_years, key="population_year")

    pop_filtered = filtered.copy()
    if selected_pop_year != "All":
        pop_filtered = pop_filtered[pop_filtered["Year"] == selected_pop_year]

    pop_table = get_population_table(pop_filtered)
    pop_table["Local"] = pop_table["State"].astype(str) + " - " + pop_table["City"].astype(str)
    pop_plot = make_plot_df(pop_table, y_columns=["Population_NH4N"])

    if len(pop_plot) > 0:
        fig_pop_wwtp = px.bar(
            pop_plot,
            x="WWTP",
            y="Population_NH4N",
            color="Local",
            barmode="group",
            title=f"Estimated Population by WWTP and Local ({selected_pop_year})",
            labels={"Population_NH4N": "Estimated population (NH4-N)", "WWTP": "WWTP"}
        )
        st.plotly_chart(fig_pop_wwtp, use_container_width=True)

        fig_pop_event = px.bar(
            pop_plot,
            x="Event",
            y="Population_NH4N",
            color="WWTP",
            barmode="group",
            facet_col="Local",
            title=f"Estimated Population by Event, Local and WWTP ({selected_pop_year})",
            labels={"Population_NH4N": "Estimated population (NH4-N)", "Event": "Event"}
        )
        st.plotly_chart(fig_pop_event, use_container_width=True)

        st.markdown("### Population Summary")
        st.dataframe(pop_plot, use_container_width=True)
    else:
        empty_message("No population data available for the selected filters.")

# ============================================================
# TARGET QUANTIFICATION
# ============================================================

with tab_quantification:
    st.subheader("Target Quantification - Triple Quadrupole MS/MS")

    quant_base = filtered[filtered["Analysis_Type"] == "Quantification"]
    quant_local = apply_local_filters(quant_base, "quant", "Quantification") if len(quant_base) > 0 else quant_base

    classical_quant = quant_local[quant_local["Drug_Class"] == "Classical"]
    nps_quant = quant_local[quant_local["Drug_Class"] != "Classical"]

    classical_quant_plot = make_plot_df(classical_quant, y_columns=["Load_g_day", "PNML_mg_day_1000inh", "Event_Day"])
    nps_quant_plot = make_plot_df(nps_quant, y_columns=["Load_g_day", "PNML_mg_day_1000inh", "Event_Day"])

    qtab1, qtab2 = st.tabs(["Classical Drugs", "Quantified NPS"])

    with qtab1:
        st.markdown("### Quantification - Classical Drugs: Year → Local → WWTP → Period")
        if len(classical_quant_plot) > 0:
            fig_load_classical = px.bar(
                classical_quant_plot,
                x="WWTP",
                y="Load_g_day",
                color="Substance",
                barmode="group",
                facet_col="Local",
                hover_data=["Year", "Local", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                title="Classical Drugs - Load by Local and WWTP",
                labels={"Load_g_day": "Load (g/day)", "WWTP": "WWTP"}
            )
            st.plotly_chart(fig_load_classical, use_container_width=True)

            fig_pnml_classical = px.bar(
                classical_quant_plot,
                x="WWTP",
                y="PNML_mg_day_1000inh",
                color="Substance",
                barmode="group",
                facet_col="Period",
                hover_data=["Year", "Local", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                title="Classical Drugs - PNML by WWTP and Period",
                labels={"PNML_mg_day_1000inh": "PNML (mg/day/1000 inhabitants)", "WWTP": "WWTP"}
            )
            st.plotly_chart(fig_pnml_classical, use_container_width=True)

            temporal_classical = classical_quant_plot.dropna(subset=["Event_Day", "PNML_mg_day_1000inh"])
            if temporal_classical["Event_Day"].nunique() > 1:
                fig_trend_classical = px.line(
                    temporal_classical.sort_values("Event_Day"),
                    x="Event_Day",
                    y="PNML_mg_day_1000inh",
                    color="Substance",
                    line_dash="Event",
                    markers=True,
                    facet_col="WWTP",
                    hover_data=["Year", "Local", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                    title="Classical Drugs - Temporal Profile by WWTP",
                    labels={"Event_Day": "Event day", "PNML_mg_day_1000inh": "PNML (mg/day/1000 inhabitants)"}
                )
                st.plotly_chart(fig_trend_classical, use_container_width=True)
            else:
                empty_message("Temporal profile requires more than one Event_Day.")

            st.markdown("### Classical Drugs Quantification Dataset")
            st.dataframe(classical_quant_plot, use_container_width=True)
        else:
            empty_message("No classical drug quantification data available for the selected filters.")

    with qtab2:
        st.markdown("### Quantification - NPS: Year → Local → WWTP → Period")
        if len(nps_quant_plot) > 0:
            fig_load_nps = px.bar(
                nps_quant_plot,
                x="WWTP",
                y="Load_g_day",
                color="Substance",
                barmode="group",
                facet_col="Local",
                hover_data=["Year", "Local", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                title="Quantified NPS - Load by Local and WWTP",
                labels={"Load_g_day": "Load (g/day)", "WWTP": "WWTP"}
            )
            st.plotly_chart(fig_load_nps, use_container_width=True)

            fig_pnml_nps = px.bar(
                nps_quant_plot,
                x="WWTP",
                y="PNML_mg_day_1000inh",
                color="Substance",
                barmode="group",
                facet_col="Period",
                hover_data=["Year", "Local", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                title="Quantified NPS - PNML by WWTP and Period",
                labels={"PNML_mg_day_1000inh": "PNML (mg/day/1000 inhabitants)", "WWTP": "WWTP"}
            )
            st.plotly_chart(fig_pnml_nps, use_container_width=True)

            temporal_nps = nps_quant_plot.dropna(subset=["Event_Day", "PNML_mg_day_1000inh"])
            if temporal_nps["Event_Day"].nunique() > 1:
                fig_trend_nps = px.line(
                    temporal_nps.sort_values("Event_Day"),
                    x="Event_Day",
                    y="PNML_mg_day_1000inh",
                    color="Substance",
                    line_dash="Event",
                    markers=True,
                    facet_col="WWTP",
                    hover_data=["Year", "Local", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                    title="Quantified NPS - Temporal Profile by WWTP",
                    labels={"Event_Day": "Event day", "PNML_mg_day_1000inh": "PNML (mg/day/1000 inhabitants)"}
                )
                st.plotly_chart(fig_trend_nps, use_container_width=True)
            else:
                empty_message("Temporal profile requires more than one Event_Day.")

            st.markdown("### Quantified NPS Dataset")
            st.dataframe(nps_quant_plot, use_container_width=True)
        else:
            empty_message("No quantified NPS data available for the selected filters.")

# ============================================================
# SCREENING
# ============================================================

with tab_screening:
    st.subheader("Screening - Orbitrap HRMS")

    screening_base = filtered[filtered["Analysis_Type"] == "Screening"]
    screening_local = apply_local_filters(screening_base, "screen", "Screening") if len(screening_base) > 0 else screening_base

    screening_classical = screening_local[screening_local["Drug_Class"] == "Classical"]
    screening_nps = screening_local[screening_local["Drug_Class"] != "Classical"]

    screening_classical_plot = make_plot_df(screening_classical)
    screening_nps_plot = make_plot_df(screening_nps)

    stab1, stab2 = st.tabs(["Classical Drugs", "NPS"])

    with stab1:
        st.markdown("### Screening - Classical Drugs: Year → Local → WWTP → Period")
        if len(screening_classical_plot) > 0:
            fig_classical_screen = px.histogram(
                screening_classical_plot,
                x="WWTP",
                color="Detection",
                facet_col="Local",
                hover_data=["Year", "Local", "State", "City", "WWTP", "Event", "Period", "Sampling_Date", "Substance"],
                title="Classical Drugs Screening by Local and WWTP"
            )
            st.plotly_chart(fig_classical_screen, use_container_width=True)

            fig_classical_period = px.histogram(
                screening_classical_plot,
                x="Period",
                color="Detection",
                facet_col="WWTP",
                hover_data=["Year", "Local", "State", "City", "WWTP", "Event", "Period", "Sampling_Date", "Substance"],
                title="Classical Drugs Screening by Period and WWTP"
            )
            st.plotly_chart(fig_classical_period, use_container_width=True)

            st.markdown("### Classical Drugs Screening Dataset")
            st.dataframe(screening_classical_plot, use_container_width=True)
        else:
            empty_message("No classical drug screening data available for the selected filters.")

    with stab2:
        st.markdown("### Screening - NPS: Year → Local → WWTP → Period")
        if len(screening_nps_plot) > 0:
            detected_nps_local = screening_nps_plot[screening_nps_plot["Detection"] == "Detected"]

            fig_nps_by_local = px.histogram(
                detected_nps_local,
                x="WWTP",
                color="Substance",
                facet_col="Local",
                hover_data=["Year", "Local", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                title="Detected NPS by Local and WWTP"
            )
            st.plotly_chart(fig_nps_by_local, use_container_width=True)

            detection_frequency = (
                screening_nps_plot
                .groupby(["Year", "Local", "State", "City", "WWTP", "Period", "Substance", "Detection"])
                .size()
                .reset_index(name="Count")
            )
            detection_frequency = make_plot_df(detection_frequency, y_columns=["Count"])

            fig_nps_frequency = px.bar(
                detection_frequency,
                x="WWTP",
                y="Count",
                color="Detection",
                facet_col="Period",
                hover_data=["Year", "Local", "State", "City", "WWTP", "Period", "Substance"],
                title="NPS Detection Frequency by WWTP and Period"
            )
            st.plotly_chart(fig_nps_frequency, use_container_width=True)

            heatmap_data = (
                screening_nps_plot
                .assign(Detected_Num=screening_nps_plot["Detection"].eq("Detected").astype(int))
                .pivot_table(index="Substance", columns="WWTP", values="Detected_Num", aggfunc="sum", fill_value=0)
            )
            if len(heatmap_data) > 0:
                fig_heatmap = px.imshow(
                    heatmap_data,
                    text_auto=True,
                    aspect="auto",
                    title="NPS Detection Heatmap by Substance and WWTP"
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)

            st.markdown("### NPS Screening Dataset")
            st.dataframe(screening_nps_plot, use_container_width=True)
        else:
            empty_message("No NPS screening data available for the selected filters.")

# ============================================================
# EVENTS
# ============================================================

with tab_events:
    st.subheader("Event Comparison")

    events_plot_base = make_plot_df(filtered, y_columns=["PNML_mg_day_1000inh"])

    if len(events_plot_base) > 0:
        event_overview = (
            events_plot_base.groupby(["Year", "Event", "State", "City", "Local", "WWTP"], as_index=False)
            .agg(Monitoring_Results=("Event", "count"), Substances=("Substance", "nunique"), Population=("Population_NH4N", "max"))
        )
        event_overview = make_plot_df(event_overview, y_columns=["Monitoring_Results", "Population"])

        fig_event = px.bar(
            event_overview,
            x="WWTP",
            y="Monitoring_Results",
            color="Local",
            barmode="group",
            facet_col="Event",
            hover_data=["Year", "Local", "State", "City", "WWTP", "Event", "Population"],
            title="Monitoring results by WWTP, local and event"
        )
        st.plotly_chart(fig_event, use_container_width=True)

        quant_events = events_plot_base[events_plot_base["Analysis_Type"] == "Quantification"]
        quant_events = make_plot_df(quant_events, y_columns=["PNML_mg_day_1000inh"])

        if len(quant_events) > 0:
            fig_compare = px.bar(
                quant_events,
                x="WWTP",
                y="PNML_mg_day_1000inh",
                color="Substance",
                barmode="group",
                facet_col="Local",
                hover_data=["Year", "Local", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                title="Quantified substances across locals and WWTPs",
                labels={"PNML_mg_day_1000inh": "PNML"}
            )
            st.plotly_chart(fig_compare, use_container_width=True)

        st.markdown("### Event Overview")
        st.dataframe(event_overview, use_container_width=True)
    else:
        empty_message("No event data available for the selected filters.")

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
        **Local** combines State and City.  
        **WWTP** identifies the wastewater treatment plant or sampling site.  
        **Population_NH4N** represents the population estimated based on ammoniacal nitrogen and can vary by year, event,
        WWTP and sampling day.  
        **Load (g/day)** represents the estimated daily mass load entering the wastewater system.  
        **PNML (mg/day/1000 inhabitants)** represents the population-normalized mass load.

        ### Interpretation
        Results should always be interpreted together with the spatial context: Year, Local, WWTP and Period.
        This is why the quantification and screening tabs include site-specific filters and site context tables.
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
