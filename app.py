import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="RENENSP",
    page_icon="🧪",
    layout="wide"
)

px.defaults.template = "plotly_white"

RENENSP_COLORS = [
    "#003C43",  # dark teal
    "#005F63",
    "#0A9396",
    "#94D2BD",
    "#EE9B00",
    "#CA6702",
    "#BB3E03",
    "#AE2012",
    "#5E6472",
]

PERIOD_COLORS = {
    "Reference": "#003C43",
    "Before": "#94D2BD",
    "During": "#EE9B00",
    "After": "#5E6472",
}

px.defaults.color_discrete_sequence = RENENSP_COLORS
px.defaults.color_continuous_scale = "Teal"

# ============================================================
# ============================================================
# VISUAL STYLE
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f4f8f8 0%, #eef6f6 45%, #ffffff 100%);
    }

    .block-container {
        padding-top: 0.8rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    .hero {
        background: linear-gradient(135deg, #003c43 0%, #005f63 55%, #0a9396 100%);
        color: white;
        padding: 28px 36px;
        border-radius: 24px;
        margin-bottom: 18px;
        box-shadow: 0 10px 32px rgba(0, 60, 67, 0.25);
    }

    .hero h1 {
        color: white;
        font-size: 40px;
        font-weight: 900;
        margin-bottom: 10px;
    }

    .hero p {
        font-size: 16px;
        line-height: 1.5;
        max-width: 950px;
        margin: 8px 0;
    }

    h1, h2, h3 {
        color: #003c43;
        font-weight: 850;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #002f35 0%, #005f63 100%);
    }

    [data-testid="stSidebar"] * {
        color: white;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #dbe7e7;
        padding: 18px;
        border-radius: 20px;
        box-shadow: 0 6px 18px rgba(0, 95, 99, 0.10);
    }

    div[data-testid="stMetric"] label {
        color: #005f63;
        font-weight: 800;
    }

    div[data-testid="stMetricValue"] {
        color: #003c43;
        font-weight: 900;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 16px;
        padding: 12px 20px;
        border: 1px solid #dbe7e7;
        font-weight: 700;
    }

    .stTabs [aria-selected="true"] {
        background-color: #005f63 !important;
        color: white !important;
    }

    .stAlert {
        border-radius: 16px;
    }

    .stDataFrame {
        border-radius: 16px;
        overflow: hidden;
    }

    div.stButton > button {
        border-radius: 14px;
        border: 1px solid #005f63;
        color: #005f63;
        background-color: white;
        font-weight: 800;
    }

    div.stButton > button:hover {
        background-color: #005f63;
        color: white;
        border: 1px solid #005f63;
    }

    .hero-meta {
        font-size: 15px !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        font-size: 18px !important;
        line-height: 1.2 !important;
    }

    .js-plotly-plot text {
        fill: #111111 !important;
    }

    .gtitle {
        fill: #111111 !important;
        font-weight: 700 !important;
    }

    .footer {
        text-align: center;
        color: #456;
        font-size: 14px;
        padding-top: 20px;
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

    df["Sampling_Date"] = pd.to_datetime(df["Sampling_Date"], errors="coerce").dt.strftime("%Y-%m-%d")

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64").astype(str)
    df["Year"] = df["Year"].replace({"<NA>": None, "nan": None})

    numeric_cols = [
        "Event_Day",
        "Population_NH4N",
        "Load_g_day",
        "PNML_mg_day_1000inh"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    text_cols = [
        "State", "City", "WWTP", "Event", "Period", "Substance",
        "Drug_Class", "Analytical_Platform", "Analysis_Type", "Detection"
    ]

    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": None, "None": None, "": None})

    if "Local" not in df.columns:
        df["Local"] = df["State"].fillna("") + " - " + df["City"].fillna("")
    else:
        df["Local"] = df["Local"].astype(str).str.strip()

    return df


df = load_data()

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def unique_sorted(dataframe, column):
    if dataframe is None or len(dataframe) == 0 or column not in dataframe.columns:
        return []

    return sorted(dataframe[column].dropna().unique().tolist())


def format_int(value):
    if pd.isna(value) or value is None:
        return "NA"

    return f"{int(value):,}".replace(",", ".")


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


def empty_message(text):
    st.info(text)


def professional_layout(fig, title=None):
    fig.update_layout(
        title=dict(
            text=title if title else fig.layout.title.text,
            font=dict(size=22, color="#111111", family="Arial"),
            x=0.02
        ),
        font=dict(
            family="Arial",
            size=14,
            color="#111111"
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend=dict(
            title_font=dict(color="#111111"),
            font=dict(color="#111111", size=13),
            bgcolor="rgba(255,255,255,0)"
        ),
        margin=dict(l=40, r=30, t=70, b=50)
    )

    fig.update_xaxes(
        title_font=dict(color="#111111", size=15),
        tickfont=dict(color="#111111", size=13),
        linecolor="#111111",
        gridcolor="#E5E7EB",
        zerolinecolor="#E5E7EB"
    )

    fig.update_yaxes(
        title_font=dict(color="#111111", size=15),
        tickfont=dict(color="#111111", size=13),
        linecolor="#111111",
        gridcolor="#E5E7EB",
        zerolinecolor="#E5E7EB"
    )

    return fig


_original_plotly_chart = st.plotly_chart


def renensp_plotly_chart(fig, *args, **kwargs):
    try:
        fig = professional_layout(fig)
    except Exception:
        pass
    return _original_plotly_chart(fig, *args, **kwargs)


st.plotly_chart = renensp_plotly_chart


def safe_top_value(dataframe, value_col):
    if len(dataframe) == 0 or value_col not in dataframe.columns:
        return None

    temp = dataframe.dropna(subset=[value_col])

    if len(temp) == 0:
        return None

    return temp.loc[temp[value_col].idxmax()]


def calculate_reference_event_change(dataframe):
    quant = dataframe[dataframe["Analysis_Type"].eq("Quantification")].copy()

    if len(quant) == 0:
        return pd.DataFrame()

    quant["Period"] = quant["Period"].astype(str).str.strip()
    quant["PNML_mg_day_1000inh"] = pd.to_numeric(
        quant["PNML_mg_day_1000inh"],
        errors="coerce"
    )

    grouped = (
        quant.groupby(
            ["State", "City", "Local", "WWTP", "Event", "Substance", "Period"],
            as_index=False
        )["PNML_mg_day_1000inh"]
        .mean()
    )

    pivot = grouped.pivot_table(
        index=["State", "City", "Local", "WWTP", "Event", "Substance"],
        columns="Period",
        values="PNML_mg_day_1000inh",
        aggfunc="mean"
    ).reset_index()

    for col in ["Reference", "Before", "During", "After"]:
        if col not in pivot.columns:
            pivot[col] = pd.NA

    pivot["Increase_vs_Reference_%"] = (
        (pivot["During"] - pivot["Reference"]) / pivot["Reference"]
    ) * 100

    pivot["Increase_vs_Before_%"] = (
        (pivot["During"] - pivot["Before"]) / pivot["Before"]
    ) * 100

    pivot["Recovery_After_vs_During_%"] = (
        (pivot["After"] - pivot["During"]) / pivot["During"]
    ) * 100

    return pivot


def apply_local_filters(dataframe, prefix, label):
    if len(dataframe) == 0:
        return dataframe

    st.markdown(f"### {label}: spatial and temporal filters")
    st.caption("Use these filters to explore results by year, local, WWTP, event and period.")

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

    with st.expander("Selected site context", expanded=False):
        st.dataframe(site_context_table(filtered_local), use_container_width=True)

    return filtered_local

# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <h1>RENENSP</h1>
        <p>
        Wastewater-based epidemiology platform for monitoring classical drugs and NPS in Northeast Brazil.
        </p>
        <p class="hero-meta">
        PROCAD CAPES/SENAD • UFRPE • PEM Research Group
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================
# SIDEBAR FILTERS
# ============================================================

try:
    st.sidebar.image("logo_renensp.png", width=220)
except Exception:
    st.sidebar.markdown("### RENENSP")

st.sidebar.markdown("## Filters")
st.sidebar.caption("Use these filters to refine the whole platform.")

st.sidebar.markdown("### Site Filters")

year_filter = st.sidebar.multiselect(
    "Year",
    unique_sorted(df, "Year"),
    default=unique_sorted(df, "Year")
)

local_filter = st.sidebar.multiselect(
    "Local",
    unique_sorted(df, "Local"),
    default=unique_sorted(df, "Local")
)

wwtp_filter = st.sidebar.multiselect(
    "WWTP",
    unique_sorted(df, "WWTP"),
    default=unique_sorted(df, "WWTP")
)

event_filter = st.sidebar.multiselect(
    "Event",
    unique_sorted(df, "Event"),
    default=unique_sorted(df, "Event")
)

period_filter = st.sidebar.multiselect(
    "Period",
    unique_sorted(df, "Period"),
    default=unique_sorted(df, "Period")
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Analytical Filters")

substance_filter = st.sidebar.multiselect("Substance", unique_sorted(df, "Substance"))
drug_class_filter = st.sidebar.multiselect("Drug Class", unique_sorted(df, "Drug_Class"))
platform_filter = st.sidebar.multiselect("Analytical Platform", unique_sorted(df, "Analytical_Platform"))
analysis_filter = st.sidebar.multiselect("Analysis Type", unique_sorted(df, "Analysis_Type"))
detection_filter = st.sidebar.multiselect("Detection", unique_sorted(df, "Detection"))

st.sidebar.markdown("---")
st.sidebar.caption("RENENSP Network | 2026")

# ============================================================
# APPLY SIDEBAR FILTERS
# ============================================================

filtered = df.copy()

if year_filter:
    filtered = filtered[filtered["Year"].isin(year_filter)]

if local_filter:
    filtered = filtered[filtered["Local"].isin(local_filter)]

if wwtp_filter:
    filtered = filtered[filtered["WWTP"].isin(wwtp_filter)]

if event_filter:
    filtered = filtered[filtered["Event"].isin(event_filter)]

if period_filter:
    filtered = filtered[filtered["Period"].isin(period_filter)]

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

selected_periods = period_filter

# ============================================================
# OVERVIEW
# ============================================================

st.header("Overview")

detected_nps = filtered[
    (filtered["Analysis_Type"] == "Screening") &
    (filtered["Drug_Class"] != "Classical") &
    (filtered["Detection"] == "Detected")
]

detected_classical = filtered[
    (filtered["Drug_Class"] == "Classical") &
    (filtered["Detection"] == "Detected")
]

population_covered = event_specific_population(filtered)

col1, col2, col3, col4 = st.columns(4)
col1.metric("🧪 Monitoring results", len(filtered))
col2.metric("📍 States", filtered["State"].nunique())
col3.metric("🏙️ Cities", filtered["City"].nunique())
col4.metric("🏭 WWTPs", filtered["WWTP"].nunique())

col5, col6, col7, col8 = st.columns(4)
col5.metric("🎉 Events", filtered["Event"].nunique())
col6.metric("🧬 Detected classical drugs", detected_classical["Substance"].nunique())
col7.metric("⚠️ Detected NPS", detected_nps["Substance"].nunique())
col8.metric("👥 Population covered", format_int(population_covered))

st.caption(
    "Population covered is calculated from unique year-state-city-WWTP-event combinations, "
    "avoiding repeated counts across substances from the same sampling context."
)

# ============================================================
# TABS
# ============================================================

tab_about, tab_partners, tab_map, tab_dashboard, tab_keyfindings, tab_alert, tab_compare, tab_rankings, tab_population, tab_quantification, tab_screening, tab_events, tab_method, tab_data = st.tabs([
    "Project",
    "Network",
    "Map",
    "Overview",
    "Key Findings",
    "NPS Alert",
    "Reference vs Event",
    "Rankings",
    "Population",
    "Quantification",
    "Screening",
    "Events",
    "Methodology",
    "Open Data"
])

# ============================================================
# PROJECT
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

        **Proponent institution:** Federal Rural University of Pernambuco - UFRPE  
        **Graduate program:** Graduate Program in Chemistry - UFRPE  
        **Project period:** November 2024 to October 2029  
        **Duration:** 60 months  
        **Knowledge area:** Chemistry  
        **Thematic axis:** Axis 2 - New Psychoactive Substances

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

        **Project Coordination**  
        Prof. Dr. Jandyson Machado Santos  
        Federal Rural University of Pernambuco - UFRPE  
        jandyson.machado@ufrpe.br

        **Platform Development**  
        Dra. Bruna Ramos de Souza Gomes  
        brunaramosquimica@gmail.com

        **Research Group**  
        PEM - Petroleum, Energy and Mass Spectrometry Research Group  
        Instagram: [@grupo.pem](https://www.instagram.com/grupo.pem/)

        © RENENSP Network - 2026
        """
    )

# ============================================================
# NETWORK
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

    st.info(
        "This map shows monitoring coverage, detected substances, estimated population, "
        "analytical platforms and maximum PNML by WWTP."
    )

    if "Latitude" in filtered.columns and "Longitude" in filtered.columns:
        map_data = (
            filtered.groupby(["Year", "State", "City", "Local", "WWTP"], as_index=False)
            .agg(
                Monitoring_Results=("Substance", "count"),
                Substances_Monitored=("Substance", "nunique"),
                Detected_Results=("Detection", lambda x: (x == "Detected").sum()),
                Population_NH4N=("Population_NH4N", "max"),
                Max_PNML=("PNML_mg_day_1000inh", "max"),
                Mean_PNML=("PNML_mg_day_1000inh", "mean"),
                Events=("Event", lambda x: ", ".join(sorted(x.dropna().unique()))),
                Periods=("Period", lambda x: ", ".join(sorted(x.dropna().unique()))),
                Platforms=("Analytical_Platform", lambda x: ", ".join(sorted(x.dropna().unique()))),
                Analysis_Types=("Analysis_Type", lambda x: ", ".join(sorted(x.dropna().unique()))),
                Substances_List=("Substance", lambda x: ", ".join(sorted(x.dropna().unique()))),
                lat=("Latitude", "max"),
                lon=("Longitude", "max")
            )
        )
    else:
        wwtp_coords = pd.DataFrame({
            "State": ["PE", "PE", "PB", "PB", "RN", "AL", "SE", "CE", "BA", "MA", "PI"],
            "City": [
                "Recife", "Olinda", "Joao Pessoa", "Campina Grande", "Natal",
                "Maceio", "Aracaju", "Fortaleza", "Salvador", "Sao Luis", "Teresina"
            ],
            "WWTP": [
                "Cabanga", "Peixinho", "Mangabeira", "Catingueira", "Jundiai-Guarapes",
                "Benedito Bentes", "Orlando Dantas", "Coco", "Boca do Rio", "Vinhais", "Piraja"
            ],
            "lat": [-8.071, -7.999, -7.175, -7.2307, -5.7945, -9.6498, -10.9472, -3.7319, -12.9777, -2.5307, -5.0892],
            "lon": [-34.884, -34.860, -34.845, -35.8817, -35.2110, -35.7089, -37.0731, -38.5267, -38.5016, -44.3068, -42.8016],
        })

        map_data = (
            filtered.groupby(["Year", "State", "City", "Local", "WWTP"], as_index=False)
            .agg(
                Monitoring_Results=("Substance", "count"),
                Substances_Monitored=("Substance", "nunique"),
                Detected_Results=("Detection", lambda x: (x == "Detected").sum()),
                Population_NH4N=("Population_NH4N", "max"),
                Max_PNML=("PNML_mg_day_1000inh", "max"),
                Mean_PNML=("PNML_mg_day_1000inh", "mean"),
                Events=("Event", lambda x: ", ".join(sorted(x.dropna().unique()))),
                Periods=("Period", lambda x: ", ".join(sorted(x.dropna().unique()))),
                Platforms=("Analytical_Platform", lambda x: ", ".join(sorted(x.dropna().unique()))),
                Analysis_Types=("Analysis_Type", lambda x: ", ".join(sorted(x.dropna().unique()))),
                Substances_List=("Substance", lambda x: ", ".join(sorted(x.dropna().unique()))),
            )
            .merge(wwtp_coords, on=["State", "City", "WWTP"], how="left")
        )

    detected_aux = filtered[filtered["Detection"] == "Detected"]

    detected_summary = (
        detected_aux.groupby(["Year", "State", "City", "Local", "WWTP"], as_index=False)
        .agg(
            Detected_Substances=("Substance", "nunique"),
            NPS_Detected=("Substance", lambda x: detected_aux.loc[x.index][detected_aux.loc[x.index, "Drug_Class"] != "Classical"]["Substance"].nunique()),
            Classical_Detected=("Substance", lambda x: detected_aux.loc[x.index][detected_aux.loc[x.index, "Drug_Class"] == "Classical"]["Substance"].nunique())
        )
    )

    map_data = map_data.merge(
        detected_summary,
        on=["Year", "State", "City", "Local", "WWTP"],
        how="left"
    )

    for col in ["Detected_Substances", "NPS_Detected", "Classical_Detected"]:
        map_data[col] = map_data[col].fillna(0)

    missing_coords = map_data[map_data["lat"].isna() | map_data["lon"].isna()]

    if len(missing_coords) > 0:
        st.warning("Some WWTPs do not have coordinates yet.")

        with st.expander("WWTPs without coordinates", expanded=False):
            st.dataframe(
                missing_coords[["Year", "State", "City", "WWTP", "Events"]],
                use_container_width=True
            )

    map_data = map_data.dropna(subset=["lat", "lon"])

    map_data = make_plot_df(
        map_data,
        y_columns=[
            "Monitoring_Results", "Substances_Monitored", "Detected_Results",
            "Detected_Substances", "NPS_Detected", "Classical_Detected",
            "Population_NH4N", "Max_PNML", "Mean_PNML"
        ]
    )

    if len(map_data) > 0:
        map_view = st.radio(
            "Map view",
            [
                "Monitoring coverage",
                "Detected substances",
                "Detected NPS",
                "Population covered",
                "Maximum PNML"
            ],
            horizontal=True
        )

        if map_view == "Monitoring coverage":
            size_col = "Monitoring_Results"
            color_col = "Monitoring_Results"
            map_title = "Monitoring coverage by WWTP"

        elif map_view == "Detected substances":
            size_col = "Detected_Substances"
            color_col = "Detected_Substances"
            map_title = "Detected substances by WWTP"

        elif map_view == "Detected NPS":
            size_col = "NPS_Detected"
            color_col = "NPS_Detected"
            map_title = "Detected NPS by WWTP"

        elif map_view == "Population covered":
            size_col = "Population_NH4N"
            color_col = "Population_NH4N"
            map_title = "Estimated population covered by WWTP"

        else:
            size_col = "Max_PNML"
            color_col = "Max_PNML"
            map_title = "Maximum PNML by WWTP"

        fig_map = px.scatter_mapbox(
            map_data,
            lat="lat",
            lon="lon",
            size=size_col,
            color=color_col,
            hover_name="WWTP",
            hover_data={
                "Year": True,
                "Local": True,
                "State": True,
                "City": True,
                "Events": True,
                "Periods": True,
                "Platforms": True,
                "Analysis_Types": True,
                "Monitoring_Results": True,
                "Substances_Monitored": True,
                "Detected_Results": True,
                "Detected_Substances": True,
                "Classical_Detected": True,
                "NPS_Detected": True,
                "Population_NH4N": True,
                "Max_PNML": ":.2f",
                "Mean_PNML": ":.2f",
                "Substances_List": True,
                "lat": False,
                "lon": False,
            },
            zoom=5,
            height=680,
            title=map_title
        )

        fig_map.update_layout(
            mapbox_style="open-street-map",
            dragmode="zoom",
            mapbox=dict(center=dict(lat=-7.8, lon=-37.2), zoom=4.5),
            margin={"r": 0, "t": 45, "l": 0, "b": 0},
            coloraxis_colorbar=dict(title=map_view)
        )

        st.plotly_chart(
            fig_map,
            use_container_width=True,
            config={"scrollZoom": True, "displayModeBar": True, "displaylogo": False}
        )

        st.markdown("### Monitoring Summary by WWTP")

        ranking_map = map_data[
            [
                "Year", "State", "City", "Local", "WWTP", "Events", "Periods",
                "Platforms", "Analysis_Types", "Monitoring_Results",
                "Substances_Monitored", "Detected_Results", "Detected_Substances",
                "Classical_Detected", "NPS_Detected", "Population_NH4N",
                "Max_PNML", "Mean_PNML", "Substances_List"
            ]
        ].sort_values("Monitoring_Results", ascending=False)

        st.dataframe(ranking_map, use_container_width=True)

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
            fig = px.histogram(
                dashboard_plot,
                x="Substance",
                color="Analysis_Type",
                title="Monitoring results by substance"
            )
            fig.update_layout(xaxis_title="Substance", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)

        with colB:
            fig = px.histogram(
                dashboard_plot,
                x="Local",
                color="State",
                title="Monitoring results by local"
            )
            fig.update_layout(xaxis_title="Local", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)

        colC, colD = st.columns(2)

        with colC:
            fig = px.histogram(
                dashboard_plot,
                x="WWTP",
                color="Event",
                title="Monitoring results by WWTP and event"
            )
            fig.update_layout(xaxis_title="WWTP", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)

        with colD:
            fig = px.histogram(
                dashboard_plot,
                x="Period",
                color="Detection",
                title="Detection by period"
            )
            fig.update_layout(xaxis_title="Period", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)

    else:
        empty_message("No data available for the selected filters.")

# ============================================================
# KEY FINDINGS
# ============================================================

with tab_keyfindings:
    st.subheader("Automatic Key Findings")

    if len(filtered) == 0:
        empty_message("No data available for the selected filters.")

    else:
        quant = filtered[filtered["Analysis_Type"] == "Quantification"]
        screening_detected = filtered[filtered["Detection"] == "Detected"]

        top_pnml = safe_top_value(quant, "PNML_mg_day_1000inh")
        top_load = safe_top_value(quant, "Load_g_day")

        col1, col2, col3 = st.columns(3)

        col1.metric("Total records", len(filtered))
        col2.metric("Detected substances", screening_detected["Substance"].nunique())
        col3.metric("Events monitored", filtered["Event"].nunique())

        st.markdown("### Main Highlights")

        if top_pnml is not None:
            st.success(
                f"The highest PNML was observed for **{top_pnml['Substance']}** "
                f"in **{top_pnml['City']}**, WWTP **{top_pnml['WWTP']}**, "
                f"during **{top_pnml['Event']}** "
                f"({top_pnml['PNML_mg_day_1000inh']:.2f} mg/day/1000 inhabitants)."
            )

        if top_load is not None:
            st.info(
                f"The highest daily load was observed for **{top_load['Substance']}** "
                f"in **{top_load['City']}**, WWTP **{top_load['WWTP']}**, "
                f"during **{top_load['Event']}** "
                f"({top_load['Load_g_day']:.2f} g/day)."
            )

        detected_nps_alert = filtered[
            (filtered["Drug_Class"] != "Classical") &
            (filtered["Detection"] == "Detected")
        ]

        if len(detected_nps_alert) > 0:
            st.warning(
                f"Detected NPS were found in the selected data: "
                f"**{detected_nps_alert['Substance'].nunique()} unique NPS**."
            )

            st.dataframe(
                detected_nps_alert[
                    [
                        "Year", "State", "City", "WWTP", "Event", "Period",
                        "Substance", "Analytical_Platform", "Sampling_Date"
                    ]
                ].drop_duplicates(),
                use_container_width=True
            )
        else:
            st.info("No NPS detections were found for the selected filters.")

# ============================================================
# NPS ALERT
# ============================================================

with tab_alert:
    st.subheader("NPS Alert")

    nps_alert = filtered[
        (filtered["Drug_Class"] != "Classical") &
        (filtered["Detection"] == "Detected")
    ].copy()

    if len(nps_alert) > 0:
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Detected NPS records", len(nps_alert))
        col2.metric("Unique NPS", nps_alert["Substance"].nunique())
        col3.metric("🏙️ Cities", nps_alert["City"].nunique())
        col4.metric("🏭 WWTPs", nps_alert["WWTP"].nunique())

        fig_nps_alert = px.histogram(
            nps_alert,
            x="Substance",
            color="City",
            facet_col="Event",
            title="Detected NPS by substance, city and event",
            hover_data=["Year", "State", "City", "WWTP", "Period", "Sampling_Date"]
        )

        st.plotly_chart(fig_nps_alert, use_container_width=True)

        heatmap_alert = (
            nps_alert
            .assign(Detected_Num=1)
            .pivot_table(
                index="Substance",
                columns="WWTP",
                values="Detected_Num",
                aggfunc="sum",
                fill_value=0
            )
        )

        fig_heatmap_alert = px.imshow(
            heatmap_alert,
            text_auto=True,
            aspect="auto",
            title="NPS Alert Heatmap by Substance and WWTP"
        )

        st.plotly_chart(fig_heatmap_alert, use_container_width=True)

        st.markdown("### NPS Alert Table")

        st.dataframe(
            nps_alert[
                [
                    "Year", "State", "City", "Local", "WWTP", "Event", "Period",
                    "Substance", "Analytical_Platform", "Sampling_Date"
                ]
            ].drop_duplicates(),
            use_container_width=True
        )

    else:
        empty_message("No detected NPS available for the selected filters.")

# ============================================================
# REFERENCE VS EVENT
# ============================================================

with tab_compare:
    st.subheader("Reference vs Event Comparison")

    st.info(
        "This section compares PNML values side by side: Reference versus Before, During and After "
        "for the same year, local, WWTP, event and substance."
    )

    if "Reference" not in selected_periods or "During" not in selected_periods:
        st.warning(
            "For this comparison, keep both Reference and During selected in the Period filter."
        )

    comparison = calculate_reference_event_change(filtered)

    if len(comparison) > 0:
        available_periods = [
            col for col in ["Reference", "Before", "During", "After"]
            if col in comparison.columns
        ]

        comparison_long = comparison.melt(
            id_vars=["State", "City", "Local", "WWTP", "Event", "Substance"],
            value_vars=available_periods,
            var_name="Period",
            value_name="PNML_mg_day_1000inh"
        ).dropna(subset=["PNML_mg_day_1000inh"])

        if len(comparison_long) > 0:
            st.markdown("### Reference vs Event Periods")

            fig_periods = px.bar(
                comparison_long,
                x="Substance",
                y="PNML_mg_day_1000inh",
                color="Period",
                barmode="group",
                facet_col="Event",
                color_discrete_map=PERIOD_COLORS,
                hover_data=["State", "City", "Local", "WWTP", "Event", "Period"],
                title="Reference, Before, During and After PNML by substance",
                labels={
                    "PNML_mg_day_1000inh": "PNML (mg/day/1000 inhabitants)",
                    "Substance": "Substance"
                }
            )

            st.plotly_chart(fig_periods, use_container_width=True)

            comparison_plot = comparison.dropna(subset=["Increase_vs_Reference_%"])

            if len(comparison_plot) > 0:
                st.markdown("### Percentage Change")

                fig_increase_ref = px.bar(
                    comparison_plot,
                    x="Substance",
                    y="Increase_vs_Reference_%",
                    color="City",
                    facet_col="Event",
                    color_discrete_sequence=RENENSP_COLORS,
                    hover_data=[
                        "State", "City", "WWTP",
                        "Reference", "Before", "During", "After",
                        "Increase_vs_Reference_%", "Increase_vs_Before_%"
                    ],
                    title="Percentage increase from Reference to During period",
                    labels={"Increase_vs_Reference_%": "Increase vs Reference (%)"}
                )

                st.plotly_chart(fig_increase_ref, use_container_width=True)

                top_increase = comparison_plot.sort_values(
                    "Increase_vs_Reference_%",
                    ascending=False
                ).head(10)

                st.markdown("### Top 10 Increases vs Reference")

                st.dataframe(
                    top_increase[
                        [
                            "State", "City", "WWTP", "Event", "Substance",
                            "Reference", "Before", "During", "After",
                            "Increase_vs_Reference_%", "Increase_vs_Before_%"
                        ]
                    ],
                    use_container_width=True
                )

        else:
            empty_message(
                "Reference and event periods were not available for the selected filters."
            )

        st.markdown("### Complete Comparison Table")

        st.dataframe(
            comparison[
                [
                    "State", "City", "Local", "WWTP", "Event", "Substance",
                    "Reference", "Before", "During", "After",
                    "Increase_vs_Reference_%", "Increase_vs_Before_%", "Recovery_After_vs_During_%"
                ]
            ],
            use_container_width=True
        )

    else:
        empty_message("No quantification data available for comparison.")

# ============================================================
# RANKINGS
# ============================================================

with tab_rankings:
    st.subheader("Rankings")

    quant_rank = filtered[filtered["Analysis_Type"] == "Quantification"].copy()
    detected_rank = filtered[filtered["Detection"] == "Detected"].copy()

    rtab1, rtab2, rtab3, rtab4 = st.tabs([
        "Top PNML",
        "Top Load",
        "Most Detected Substances",
        "WWTP Ranking"
    ])

    with rtab1:
        st.markdown("### Top 10 Highest PNML")

        top_pnml_table = (
            quant_rank
            .dropna(subset=["PNML_mg_day_1000inh"])
            .sort_values("PNML_mg_day_1000inh", ascending=False)
            .head(10)
        )

        if len(top_pnml_table) > 0:
            fig_top_pnml = px.bar(
                top_pnml_table,
                x="Substance",
                y="PNML_mg_day_1000inh",
                color="City",
                hover_data=["Year", "State", "City", "WWTP", "Event", "Period"],
                title="Top 10 highest PNML values"
            )

            st.plotly_chart(fig_top_pnml, use_container_width=True)
            st.dataframe(top_pnml_table, use_container_width=True)
        else:
            empty_message("No PNML data available.")

    with rtab2:
        st.markdown("### Top 10 Highest Loads")

        top_load_table = (
            quant_rank
            .dropna(subset=["Load_g_day"])
            .sort_values("Load_g_day", ascending=False)
            .head(10)
        )

        if len(top_load_table) > 0:
            fig_top_load = px.bar(
                top_load_table,
                x="Substance",
                y="Load_g_day",
                color="City",
                hover_data=["Year", "State", "City", "WWTP", "Event", "Period"],
                title="Top 10 highest daily loads"
            )

            st.plotly_chart(fig_top_load, use_container_width=True)
            st.dataframe(top_load_table, use_container_width=True)
        else:
            empty_message("No load data available.")

    with rtab3:
        st.markdown("### Most Frequently Detected Substances")

        substance_freq = (
            detected_rank
            .groupby(["Substance", "Drug_Class"], as_index=False)
            .size()
            .rename(columns={"size": "Detection_Count"})
            .sort_values("Detection_Count", ascending=False)
        )

        if len(substance_freq) > 0:
            fig_freq = px.bar(
                substance_freq.head(20),
                x="Substance",
                y="Detection_Count",
                color="Drug_Class",
                title="Most frequently detected substances"
            )

            st.plotly_chart(fig_freq, use_container_width=True)
            st.dataframe(substance_freq, use_container_width=True)
        else:
            empty_message("No detected substances available.")

    with rtab4:
        st.markdown("### WWTP Monitoring Ranking")

        wwtp_ranking = (
            filtered
            .groupby(["State", "City", "Local", "WWTP"], as_index=False)
            .agg(
                Monitoring_Results=("Substance", "count"),
                Unique_Substances=("Substance", "nunique"),
                Detected_Results=("Detection", lambda x: (x == "Detected").sum()),
                Events=("Event", lambda x: ", ".join(sorted(x.dropna().unique()))),
                Population_NH4N=("Population_NH4N", "max"),
                Max_PNML=("PNML_mg_day_1000inh", "max")
            )
            .sort_values("Monitoring_Results", ascending=False)
        )

        if len(wwtp_ranking) > 0:
            fig_wwtp_rank = px.bar(
                wwtp_ranking,
                x="WWTP",
                y="Monitoring_Results",
                color="City",
                hover_data=[
                    "State", "City", "Events", "Unique_Substances",
                    "Detected_Results", "Population_NH4N", "Max_PNML"
                ],
                title="WWTP ranking by monitoring results"
            )

            st.plotly_chart(fig_wwtp_rank, use_container_width=True)
            st.dataframe(wwtp_ranking, use_container_width=True)
        else:
            empty_message("No WWTP ranking available.")

# ============================================================
# POPULATION
# ============================================================

with tab_population:
    st.subheader("Population Estimated by NH4-N")
    st.info("Population_NH4N is year-, event-, WWTP- and sampling-day-specific.")

    available_years = unique_sorted(filtered, "Year")

    selected_pop_year = st.selectbox(
        "Select year for population view",
        ["All"] + available_years,
        key="population_year"
    )

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
            title=f"Estimated population by WWTP and local ({selected_pop_year})",
            labels={"Population_NH4N": "Estimated population by NH4-N", "WWTP": "WWTP"}
        )

        st.plotly_chart(fig_pop_wwtp, use_container_width=True)

        fig_pop_event = px.bar(
            pop_plot,
            x="Event",
            y="Population_NH4N",
            color="WWTP",
            barmode="group",
            facet_col="Local",
            title=f"Estimated population by event, local and WWTP ({selected_pop_year})",
            labels={"Population_NH4N": "Estimated population by NH4-N", "Event": "Event"}
        )

        st.plotly_chart(fig_pop_event, use_container_width=True)

        st.markdown("### Population Summary")
        st.dataframe(pop_plot, use_container_width=True)

    else:
        empty_message("No population data available for the selected filters.")

# ============================================================
# QUANTIFICATION
# ============================================================

with tab_quantification:
    st.subheader("Target Quantification - Triple Quadrupole MS/MS")

    quant_base = filtered[filtered["Analysis_Type"] == "Quantification"]

    if len(quant_base) > 0:
        quant_local = apply_local_filters(quant_base, "quant", "Quantification")
    else:
        quant_local = quant_base

    classical_quant = quant_local[quant_local["Drug_Class"] == "Classical"]
    nps_quant = quant_local[quant_local["Drug_Class"] != "Classical"]

    classical_quant_plot = make_plot_df(
        classical_quant,
        y_columns=["Load_g_day", "PNML_mg_day_1000inh", "Event_Day"]
    )

    nps_quant_plot = make_plot_df(
        nps_quant,
        y_columns=["Load_g_day", "PNML_mg_day_1000inh", "Event_Day"]
    )

    qtab1, qtab2 = st.tabs(["Classical Drugs", "Quantified NPS"])

    with qtab1:
        st.markdown("### Classical Drugs Quantification")

        if len(classical_quant_plot) > 0:
            fig_load_classical = px.bar(
                classical_quant_plot,
                x="WWTP",
                y="Load_g_day",
                color="Substance",
                barmode="group",
                facet_col="Local",
                hover_data=["Year", "Local", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                title="Classical drugs - load by local and WWTP",
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
                title="Classical drugs - PNML by WWTP and period",
                labels={
                    "PNML_mg_day_1000inh": "PNML (mg/day/1000 inhabitants)",
                    "WWTP": "WWTP"
                }
            )

            st.plotly_chart(fig_pnml_classical, use_container_width=True)

            temporal_classical = classical_quant_plot.dropna(
                subset=["Event_Day", "PNML_mg_day_1000inh"]
            )

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
                    title="Classical drugs - temporal profile by WWTP",
                    labels={
                        "Event_Day": "Event day",
                        "PNML_mg_day_1000inh": "PNML (mg/day/1000 inhabitants)"
                    }
                )

                st.plotly_chart(fig_trend_classical, use_container_width=True)

            else:
                empty_message("Temporal profile requires more than one Event_Day.")

            st.markdown("### Classical Drugs Quantification Dataset")
            st.dataframe(classical_quant_plot, use_container_width=True)

        else:
            empty_message("No classical drug quantification data available for the selected filters.")

    with qtab2:
        st.markdown("### NPS Quantification")

        if len(nps_quant_plot) > 0:
            fig_load_nps = px.bar(
                nps_quant_plot,
                x="WWTP",
                y="Load_g_day",
                color="Substance",
                barmode="group",
                facet_col="Local",
                hover_data=["Year", "Local", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                title="Quantified NPS - load by local and WWTP",
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
                title="Quantified NPS - PNML by WWTP and period",
                labels={
                    "PNML_mg_day_1000inh": "PNML (mg/day/1000 inhabitants)",
                    "WWTP": "WWTP"
                }
            )

            st.plotly_chart(fig_pnml_nps, use_container_width=True)

            temporal_nps = nps_quant_plot.dropna(
                subset=["Event_Day", "PNML_mg_day_1000inh"]
            )

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
                    title="Quantified NPS - temporal profile by WWTP",
                    labels={
                        "Event_Day": "Event day",
                        "PNML_mg_day_1000inh": "PNML (mg/day/1000 inhabitants)"
                    }
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

    if len(screening_base) > 0:
        screening_local = apply_local_filters(screening_base, "screen", "Screening")
    else:
        screening_local = screening_base

    screening_classical = screening_local[screening_local["Drug_Class"] == "Classical"]
    screening_nps = screening_local[screening_local["Drug_Class"] != "Classical"]

    screening_classical_plot = make_plot_df(screening_classical)
    screening_nps_plot = make_plot_df(screening_nps)

    stab1, stab2 = st.tabs(["Classical Drugs", "NPS"])

    with stab1:
        st.markdown("### Classical Drugs Screening")

        if len(screening_classical_plot) > 0:
            fig_classical_substances = px.histogram(
                screening_classical_plot,
                x="Substance",
                color="Detection",
                facet_col="WWTP",
                hover_data=["Year", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                title="Classical drugs screening by substance and WWTP"
            )

            st.plotly_chart(fig_classical_substances, use_container_width=True)

            classical_heatmap_data = (
                screening_classical_plot
                .assign(
                    Detected_Num=screening_classical_plot["Detection"].eq("Detected").astype(int)
                )
                .pivot_table(
                    index="Substance",
                    columns="WWTP",
                    values="Detected_Num",
                    aggfunc="sum",
                    fill_value=0
                )
            )

            if len(classical_heatmap_data) > 0:
                fig_classical_heatmap = px.imshow(
                    classical_heatmap_data,
                    text_auto=True,
                    aspect="auto",
                    title="Classical drugs detection heatmap by substance and WWTP"
                )

                st.plotly_chart(fig_classical_heatmap, use_container_width=True)

            st.markdown("### Classical Drugs Screening Dataset")
            st.dataframe(screening_classical_plot, use_container_width=True)

        else:
            empty_message("No classical drug screening data available for the selected filters.")

    with stab2:
        st.markdown("### NPS Screening")

        if len(screening_nps_plot) > 0:
            detected_nps_local = screening_nps_plot[
                screening_nps_plot["Detection"] == "Detected"
            ]

            if len(detected_nps_local) > 0:
                fig_nps_by_local = px.histogram(
                    detected_nps_local,
                    x="WWTP",
                    color="Substance",
                    facet_col="Local",
                    hover_data=["Year", "Local", "State", "City", "WWTP", "Event", "Period", "Sampling_Date"],
                    title="Detected NPS by local and WWTP"
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
                title="NPS detection frequency by WWTP and period"
            )

            st.plotly_chart(fig_nps_frequency, use_container_width=True)

            heatmap_data = (
                screening_nps_plot
                .assign(
                    Detected_Num=screening_nps_plot["Detection"].eq("Detected").astype(int)
                )
                .pivot_table(
                    index="Substance",
                    columns="WWTP",
                    values="Detected_Num",
                    aggfunc="sum",
                    fill_value=0
                )
            )

            if len(heatmap_data) > 0:
                fig_heatmap = px.imshow(
                    heatmap_data,
                    text_auto=True,
                    aspect="auto",
                    title="NPS detection heatmap by substance and WWTP"
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
            events_plot_base
            .groupby(["Year", "Event", "State", "City", "Local", "WWTP"], as_index=False)
            .agg(
                Monitoring_Results=("Event", "count"),
                Substances=("Substance", "nunique"),
                Population=("Population_NH4N", "max")
            )
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

    st.warning(
        "These data are intended for scientific, epidemiological and public health interpretation. "
        "They do not represent individual-level consumption or law enforcement evidence."
    )

    st.markdown(
        """
        ### Wastewater-Based Epidemiology

        Wastewater-based epidemiology estimates community-level exposure or consumption of chemical substances by
        measuring biomarkers, parent compounds, or transformation products in wastewater samples.

        ### Analytical Platforms

        **Triple Quadrupole MS/MS** is used for target quantification of selected substances.  

        **Orbitrap HRMS** is used for screening of classical drugs and new psychoactive substances.

        ### Main Indicators

        **Local** combines State and City.  

        **WWTP** identifies the wastewater treatment plant or sampling site.  

        **Population_NH4N** represents the population estimated based on ammoniacal nitrogen and can vary by year,
        event, WWTP and sampling day.  

        **Load (g/day)** represents the estimated daily mass load entering the wastewater system.  

        **PNML (mg/day/1000 inhabitants)** represents the population-normalized mass load.

        ### Interpretation

        Results should always be interpreted together with the spatial context: Year, Local, WWTP, Event and Period.
        """
    )

    st.markdown("---")

    st.markdown(
        """
        ### How to cite this platform

        RENENSP Network. **RENENSP WBE Observatory: Wastewater-Based Epidemiology Monitoring Platform for Northeast Brazil.** 2026.
        """
    )

# ============================================================
# OPEN DATA
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

st.markdown(
    """
    <div class="footer">
    RENENSP Observatory | PROCAD CAPES/SENAD<br>
    Project Coordinator: Prof. Dr. Jandyson Machado Santos - UFRPE<br>
    Platform Developer: Dra. Bruna Ramos de Souza Gomes<br>
    © 2026 RENENSP Network
    </div>
    """,
    unsafe_allow_html=True
)
