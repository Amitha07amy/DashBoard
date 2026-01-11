import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# CONFIG
st.set_page_config(
    page_title="Solar Energy Impact Dashboard",
    layout="wide"
)

# SIMPLE ACCESS CONTROL
APP_PASSWORD = "senoko_solar_2026"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Restricted Access")

    password_input = st.text_input(
        "Enter access password",
        type="password"
    )

    if password_input:
        if password_input == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")

    st.stop()

# LOAD DATA
@st.cache_data
def load_data():
    return pd.read_excel("/Users/amitha/Downloads/Master_Energy_Monthly_FINAL_WITH_COST.xlsx")

df = load_data()

# Create Month-Year label
df["Month_Year"] = pd.to_datetime(
    df["Year"].astype(str) + "-" + df["Month"] + "-01",
    errors="coerce"
).dt.strftime("%b %Y")

# HEADER
st.title("Solar Energy Impact & Cost Interpretation Dashboard")
st.caption(
    "20 Senoko Drive | Monthly Energy & Financial Summary (Billing-Cycle Aligned)"
)

# FILTERS
col1, col2, col3 = st.columns([3, 1.5, 1.5])

with col2:
    year_filter = st.multiselect(
        "Select Year",
        sorted(df["Year"].unique()),
        default=sorted(df["Year"].unique())
    )

with col3:
    trust_filter = st.multiselect(
        "Data Trust",
        df["Data_Trust"].unique(),
        default=["High", "Medium"]
    )

filtered_df = df[
    (df["Year"].isin(year_filter)) &
    (df["Data_Trust"].isin(trust_filter))
]

# KPI SECTION

st.subheader("Executive Summary")

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "🔆 Total Solar Generated (kWh)",
    f"{filtered_df['Solar_Gen_kWh'].sum():,.0f}"
)

k2.metric(
    "💰 Solar Savings (SGD)",
    f"${filtered_df['Solar_Savings_SGD'].sum():,.0f}"
)

k3.metric(
    "💸 Export Revenue (SGD)",
    f"${filtered_df['Export_Revenue_SGD'].sum():,.0f}"
)

grid_dependency = (
    filtered_df["Grid_Import_kWh"].sum()
    / filtered_df["Total_Energy_Consumed_kWh"].sum()
) * 100

k4.metric(
    "⚡ Grid Dependency (%)",
    f"{grid_dependency:.1f}%"
)

# SOLAR GENERATION TREND
st.subheader("Monthly Solar Generation")

fig_solar = px.bar(
    filtered_df,
    x="Month_Year",
    y="Solar_Gen_kWh",
    color="Data_Trust",
    title="Monthly Solar Energy Generation (kWh)"
)
st.plotly_chart(fig_solar, use_container_width=True)

# ENERGY MIX
st.subheader("Energy Supply Mix")

fig_mix = px.bar(
    filtered_df,
    x="Month_Year",
    y=[
        "Grid_Import_kWh",
        "Solar_Self_kWh",
        "Grid_Export_kWh"
    ],
    title="Energy Supply Mix by Month",
    labels={"value": "Energy (kWh)", "variable": "Source"}
)
st.plotly_chart(fig_mix, use_container_width=True)

# BILL IMPACT WATERFALL
st.subheader("Impact of Solar on Electricity Cost")

grid_cost = filtered_df["Grid_Import_Cost_SGD"].sum()
solar_savings = filtered_df["Solar_Savings_SGD"].sum()
export_revenue = filtered_df["Export_Revenue_SGD"].sum()

fig_waterfall = go.Figure(go.Waterfall(
    name="Cost Impact",
    orientation="v",
    measure=["absolute", "relative", "relative", "total"],
    x=[
        "Grid Import Cost",
        "Solar Savings",
        "Export Revenue",
        "Net Energy Impact"
    ],
    y=[
        grid_cost,
        -solar_savings,
        -export_revenue,
        grid_cost - solar_savings - export_revenue
    ]
))

fig_waterfall.update_layout(
    title="Electricity Cost Impact After Solar",
    yaxis_title="SGD"
)

st.plotly_chart(fig_waterfall, use_container_width=True)

# GRID DEPENDENCY TREND
st.subheader("Grid Electricity Dependency")

fig_grid = px.line(
    filtered_df,
    x="Month_Year",
    y="Grid_Import_kWh",
    title="Grid Electricity Consumption Over Time"
)
st.plotly_chart(fig_grid, use_container_width=True)

# DATA TRUST & VALIDATION
st.subheader("Data Trust & Energy Balance Validation")

st.dataframe(
    filtered_df[
        [
            "Month",
            "Billing_Cycles_Used",
            "Data_Trust",
            "Energy_Balance_Check"
        ]
    ],
    use_container_width=True
)
