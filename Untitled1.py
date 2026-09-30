#!/usr/bin/env python
# coding: utf-8

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Netflix Insights", page_icon="N", layout="wide")
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background: #ffffff; }
    [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e5e5e5; }
    .block-container { padding-top: 1.6rem; padding-bottom: 3rem; }
    h1, h2, h3, p, label, [data-testid="stCaption"] { color: #191919; }
    h1 { border-bottom: 3px solid #e50914; padding-bottom: 0.5rem; }
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e5e5e5;
        border-top: 3px solid #e50914;
        padding: 1rem 1.1rem;
        border-radius: 4px;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] { color: #191919; }
    [data-testid="stFileUploader"] { color: #191919; }
    [data-testid="stDataFrame"] { border: 1px solid #e5e5e5; }
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
        background-color: #e50914;
        border-color: #e50914;
    }
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background-color: #a80710;
        color: #ffffff;
    }
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] input,
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] svg { color: #ffffff; }
    [data-testid="stSidebar"] [data-testid="stDateInput"] input {
        background-color: #e50914;
        border-color: #e50914;
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

logo_col, title_col = st.columns([1, 5], vertical_alignment="center")
with logo_col:
    logo_path = Path(__file__).with_name("images.png")
    if logo_path.exists():
        st.image(str(logo_path), width=170)
with title_col:
    st.title("Netflix viewing insights")
    st.caption("Revenue, ratings, and viewing activity across your audience")

required_columns = {
    "Watch_Date",
    "Region",
    "Monthly_Revenue",
    "Subscription_Plan",
    "Rating",
    "Category",
}
local_csv = Path(__file__).with_name("netflix.csv")
uploaded_csv = st.sidebar.file_uploader("Choose a Netflix CSV", type="csv")

try:
    if uploaded_csv is not None:
        data = pd.read_csv(uploaded_csv)
        source_name = uploaded_csv.name
    elif local_csv.exists():
        data = pd.read_csv(local_csv)
        source_name = local_csv.name
    else:
        st.info("Upload your Netflix CSV in the sidebar to view the dashboard.")
        st.caption(
            "Required columns: Watch_Date, Region, Monthly_Revenue, "
            "Subscription_Plan, Rating, Category"
        )
        st.stop()
except (OSError, pd.errors.ParserError, UnicodeDecodeError) as error:
    st.error(f"Could not read the CSV: {error}")
    st.stop()

missing_columns = required_columns - set(data.columns)
if missing_columns:
    st.error("The CSV is missing required columns: " + ", ".join(sorted(missing_columns)))
    st.stop()

data = data.copy()
data["Watch_Date"] = pd.to_datetime(data["Watch_Date"], errors="coerce")
data["Monthly_Revenue"] = pd.to_numeric(data["Monthly_Revenue"], errors="coerce")
data["Rating"] = pd.to_numeric(data["Rating"], errors="coerce")
data = data.dropna(subset=["Watch_Date"])

if data.empty:
    st.warning("No rows have a valid Watch_Date value.")
    st.stop()

with st.sidebar:
    st.subheader("Filters")
    regions = st.multiselect("Region", sorted(data["Region"].dropna().unique()))
    plans = st.multiselect(
        "Subscription plan", sorted(data["Subscription_Plan"].dropna().unique())
    )
    categories = st.multiselect("Category", sorted(data["Category"].dropna().unique()))
    date_range = st.date_input(
        "Watch date",
        value=(data["Watch_Date"].min().date(), data["Watch_Date"].max().date()),
        min_value=data["Watch_Date"].min().date(),
        max_value=data["Watch_Date"].max().date(),
    )

filtered = data
if regions:
    filtered = filtered[filtered["Region"].isin(regions)]
if plans:
    filtered = filtered[filtered["Subscription_Plan"].isin(plans)]
if categories:
    filtered = filtered[filtered["Category"].isin(categories)]
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        filtered["Watch_Date"].between(
            pd.Timestamp(start_date), pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
        )
    ]

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

revenue = filtered["Monthly_Revenue"].sum()
average_rating = filtered["Rating"].mean()
metric_columns = st.columns(4)
metric_columns[0].metric("Records", f"{len(filtered):,}")
metric_columns[1].metric("Total revenue", f"${revenue:,.2f}")
metric_columns[2].metric(
    "Average rating", f"{average_rating:.2f}" if pd.notna(average_rating) else "N/A"
)
metric_columns[3].metric("Duplicate rows", f"{filtered.duplicated().sum():,}")
st.caption(f"Data source: {source_name}")

plt.rcParams.update(
    {
        "axes.facecolor": "#ffffff",
        "figure.facecolor": "#ffffff",
        "axes.edgecolor": "#dddddd",
        "axes.labelcolor": "#333333",
        "xtick.color": "#333333",
        "ytick.color": "#333333",
        "text.color": "#191919",
        "font.family": "sans-serif",
    }
)

left_chart, right_chart = st.columns(2)
with left_chart:
    st.subheader("Revenue by region")
    revenue_by_region = filtered.groupby("Region")["Monthly_Revenue"].sum().sort_values()
    figure, axis = plt.subplots(figsize=(8, 4.2))
    revenue_by_region.plot(kind="bar", ax=axis, color="#e50914", width=0.68)
    axis.set_ylabel("Monthly revenue")
    axis.set_xlabel("")
    axis.set_title("")
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="y", color="#e5e5e5", linewidth=0.8)
    axis.set_axisbelow(True)
    figure.tight_layout()
    st.pyplot(figure, use_container_width=True)
    plt.close(figure)

with right_chart:
    st.subheader("Rating by subscription plan")
    ratings_by_plan = filtered.groupby("Subscription_Plan")["Rating"].sum().dropna()
    if ratings_by_plan.empty or ratings_by_plan.sum() == 0:
        st.info("No rating data available for the selected filters.")
    else:
        figure, axis = plt.subplots(figsize=(8, 4.2))
        ratings_by_plan.plot(
            kind="pie",
            ax=axis,
            autopct="%1.0f%%",
            startangle=90,
            colors=["#e50914", "#ff4b55", "#8f0710", "#d9d9d9", "#6b6b6b"],
            wedgeprops={"linewidth": 2, "edgecolor": "#ffffff"},
        )
        axis.set_ylabel("")
        axis.set_title("")
        figure.tight_layout()
        st.pyplot(figure, use_container_width=True)
        plt.close(figure)

left_chart, right_chart = st.columns(2)
with left_chart:
    st.subheader("Revenue by category")
    revenue_by_category = filtered.groupby("Category")["Monthly_Revenue"].sum().sort_values()
    figure, axis = plt.subplots(figsize=(8, 4.2))
    revenue_by_category.plot(kind="bar", ax=axis, color="#b20710", width=0.68)
    axis.set_ylabel("Monthly revenue")
    axis.set_xlabel("")
    axis.set_title("")
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="y", color="#e5e5e5", linewidth=0.8)
    axis.set_axisbelow(True)
    figure.tight_layout()
    st.pyplot(figure, use_container_width=True)
    plt.close(figure)

with right_chart:
    st.subheader("Revenue by month")
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    filtered = filtered.assign(Month=filtered["Watch_Date"].dt.month_name())
    revenue_by_month = (
        filtered.groupby("Month")["Monthly_Revenue"].sum().reindex(month_order).dropna()
    )
    figure, axis = plt.subplots(figsize=(8, 4.2))
    revenue_by_month.plot(kind="bar", ax=axis, color="#e50914", width=0.68)
    axis.set_ylabel("Monthly revenue")
    axis.set_xlabel("")
    axis.set_title("")
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="y", color="#e5e5e5", linewidth=0.8)
    axis.set_axisbelow(True)
    figure.tight_layout()
    st.pyplot(figure, use_container_width=True)
    plt.close(figure)

with st.expander("View filtered data"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)