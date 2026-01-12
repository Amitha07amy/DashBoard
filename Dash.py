import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Solar Energy Impact Dashboard", layout="wide")

# =========================
# ACCESS CONTROL
# =========================
APP_PASSWORD = "senoko_solar_2026"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Restricted Access")
    pwd = st.text_input("Enter access password", type="password")
    if pwd:
        if pwd == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    return pd.read_excel(
        Path(__file__).parent / "data" / "Master_Energy_Monthly_FINAL_WITH_COST.xlsx"
    )

df = load_data()

# =========================
# DATE HANDLING
# =========================
df["Month_Year"] = pd.to_datetime(
    df["Month"] + " " + df["Year"].astype(str),
    format="%B %Y",
    errors="coerce"
)
df = df.sort_values("Month_Year")

# =========================
# TRUSTED DAYS MAP
# =========================
trusted_days_map = {
    "June": 18,
    "July": 17,
    "August": 17,
    "September": 17,
    "October": 17,
    "November": 1,
    "December": 15
}

df["Trusted_Days"] = df["Month"].map(trusted_days_map)

# =========================
# HEADER
# =========================
st.title("Solar Energy Impact & Cost Interpretation Dashboard")
st.caption("20 Senoko Drive | Monthly Energy & Financial Summary (Billing-Cycle Aligned)")

# =========================
# FILTERS
# =========================
_, col2, col3 = st.columns([3, 1.5, 1.5])

with col2:
    year_filter = st.multiselect(
        "Select Year", sorted(df["Year"].unique()), default=[2025]
    )

with col3:
    trust_filter = st.multiselect(
        "Data Trust", df["Data_Trust"].unique(), default=["High", "Medium"]
    )

filtered_df = df[
    (df["Year"].isin(year_filter)) &
    (df["Data_Trust"].isin(trust_filter))
]

# =========================
# KPI SECTION
# =========================
st.subheader("Executive Summary")

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("🔆 Solar Generated (kWh)", f"{filtered_df['Solar_Gen_kWh'].sum():,.0f}")
k2.metric("💰 Solar Savings (SGD)", f"${filtered_df['Solar_Savings_SGD'].sum():,.0f}")
k3.metric("💸 Export Revenue (SGD)", f"${filtered_df['Export_Revenue_SGD'].sum():,.0f}")
k4.metric("📅 Trusted Days", int(filtered_df["Trusted_Days"].sum()))

grid_dep = (
    filtered_df["Grid_Import_kWh"].sum()
    / filtered_df["Total_Energy_Consumed_kWh"].sum()
) * 100

k5.metric("⚡ Grid Dependency (%)", f"{grid_dep:.1f}%")

# =========================
# PER-DAY NORMALIZATION
# =========================
st.subheader("Per-Day Normalized Energy (Trusted Days Only)")

per_day_df = filtered_df.dropna(subset=["Trusted_Days"]).copy()
per_day_df["Solar_per_Day"] = per_day_df["Solar_Gen_kWh"] / per_day_df["Trusted_Days"]
per_day_df["Grid_per_Day"] = per_day_df["Grid_Import_kWh"] / per_day_df["Trusted_Days"]
per_day_df["Savings_per_Day"] = per_day_df["Solar_Savings_SGD"] / per_day_df["Trusted_Days"]

fig_per_day = px.bar(
    per_day_df,
    x="Month_Year",
    y=["Solar_per_Day", "Grid_per_Day"],
    barmode="group",
    labels={"value": "kWh / Day", "variable": "Metric"},
    title="Daily Energy Based on Trusted Days"
)
st.plotly_chart(fig_per_day, use_container_width=True)

# =========================
# BEFORE vs AFTER COUPLING
# =========================
st.subheader("Before vs After Solar Coupling (Trusted Days)")

def coupling_status(month):
    if month in ["January", "February", "March"]:
        return "Before Coupling"
    elif month == "April":
        return "Transition"
    else:
        return "After Coupling"

coupling_df = filtered_df.copy()
coupling_df["Coupling_Status"] = coupling_df["Month"].apply(coupling_status)

agg_coupling = coupling_df.groupby("Coupling_Status")[[
    "Grid_Import_kWh",
    "Solar_Self_kWh",
    "Solar_Gen_kWh"
]].sum().reset_index()

fig_coupling = px.bar(
    agg_coupling,
    x="Coupling_Status",
    y=["Grid_Import_kWh", "Solar_Self_kWh", "Solar_Gen_kWh"],
    barmode="group",
    title="Energy Comparison Before vs After Coupling (Trusted Days)",
    labels={"value": "Energy (kWh)", "variable": "Metric"}
)
st.plotly_chart(fig_coupling, use_container_width=True)

# =========================
# EXPORT vs SP BILL MISMATCH
# =========================
st.subheader("Solar Export vs SP Bill Detection")

# Assumption: SP export billed ≈ Export_Revenue / Export_Tariff
if "Export_Tariff_SGD_per_kWh" in df.columns:
    filtered_df["SP_Billed_Export_kWh"] = (
        filtered_df["Export_Revenue_SGD"] /
        filtered_df["Export_Tariff_SGD_per_kWh"]
    )

    filtered_df["Export_Mismatch_kWh"] = (
        filtered_df["Grid_Export_kWh"] -
        filtered_df["SP_Billed_Export_kWh"]
    )

    fig_export = px.bar(
        filtered_df,
        x="Month_Year",
        y=["Grid_Export_kWh", "SP_Billed_Export_kWh"],
        barmode="group",
        title="Solar Export: System vs SP Billed",
        labels={"value": "Export (kWh)", "variable": "Source"}
    )
    st.plotly_chart(fig_export, use_container_width=True)

    st.info(
        "Difference between system-measured export and SP-billed export "
        "indicates under-detection by the grid meter during certain periods."
    )

# =========================
# DATA VALIDATION
# =========================
st.subheader("Data Trust & Energy Balance Validation")

st.dataframe(
    filtered_df[
        ["Month", "Trusted_Days", "Billing_Cycles_Used", "Data_Trust", "Energy_Balance_Check"]
    ],
    use_container_width=True
)
