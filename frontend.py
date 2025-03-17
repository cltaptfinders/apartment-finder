import streamlit as st
import pandas as pd
import requests
import json
import os
import time
from dateutil import parser
from datetime import datetime

# 🏠 Page Configuration
st.set_page_config(page_title="Charlotte Apartment Finder", page_icon="🏠", layout="wide")

# 📡 Backend API URL
BACKEND_URL = "https://apartment-finder-backend.onrender.com/search"

# 📂 Define JSON Cache File & Expiry Time (24 hours)
JSON_FILE = "data.json"
REFRESH_INTERVAL = 86400  # 24 hours in seconds

# 🔄 Function to Fetch & Cache Data
@st.cache_data
def fetch_data():
    """Fetch data from API and save to JSON file, refreshing once per day."""
    if os.path.exists(JSON_FILE):
        file_mod_time = os.path.getmtime(JSON_FILE)
        if time.time() - file_mod_time < REFRESH_INTERVAL:
            with open(JSON_FILE, "r") as f:
                return pd.DataFrame(json.load(f))

    response = requests.get(BACKEND_URL)
    if response.status_code == 200:
        data = response.json()
        with open(JSON_FILE, "w") as f:
            json.dump(data, f)
        return pd.DataFrame(data)
    else:
        st.error("⚠️ Failed to fetch data from backend.")
        return pd.DataFrame()

df = fetch_data()

# --- 🏠 Page Styling ---
LOGO_URL = "https://i.imgur.com/LUQTwbB.png"
PRIMARY_COLOR = "#2F80ED"
BACKGROUND_COLOR = "#F7F9FC"
TEXT_COLOR = "#000000"

st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to", ["Apartment Finder", "Property Map"])

# --- 🎨 Custom CSS ---
st.markdown(f"""
    <style>
        .stApp {{ background-color: {BACKGROUND_COLOR}; }}
        .apartment-card {{
            background-color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            color: {TEXT_COLOR};
        }}
        .rent-price {{ font-size: 22px; font-weight: bold; color: {PRIMARY_COLOR}; }}
    </style>
""", unsafe_allow_html=True)

# --- 📍 Property Map Page ---
if page == "Property Map":
    st.title("📍 Charlotte Apartment Map")
    st.markdown("### Browse all partner properties on a live interactive map.")

    # Ensure Latitude & Longitude are properly formatted
    df_map = df.copy()
    df_map.rename(columns={"Latitude": "lat", "Longitude": "lon"}, inplace=True)

    if "lat" in df_map.columns and "lon" in df_map.columns:
        st.map(df_map[["lat", "lon"]])
    else:
        st.error("⚠️ Latitude and Longitude data not found!")

# --- 🏠 Apartment Finder Page ---
if page == "Apartment Finder":
    st.markdown(f"""
        <div style='display: flex; align-items: center; justify-content: center;'>
            <img src="{LOGO_URL}" alt="Charlotte Apartment Finders Logo" style='max-width: 180px; margin-right: 15px;'>
            <h1 style="color: {PRIMARY_COLOR};">Charlotte Apartment Finder</h1>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### Find Your Dream Apartment in Charlotte ✨")

    st.sidebar.header("🔍 Search Filters")
    apartment_name = st.sidebar.text_input("Apartment Name (Optional)", "")
    move_date = st.sidebar.date_input("Move-In Date (Optional)", value=None)
    max_price = st.sidebar.number_input("Max Rent ($) (Optional)", value=0, step=100)
    neighborhood = st.sidebar.text_input("Neighborhood (Optional)", "")
    bedrooms = st.sidebar.text_input("Bedrooms (Optional, e.g., Studio, 1 Bed, 2 Beds)", "")
    min_sqft = st.sidebar.number_input("Minimum Square Footage (Optional)", value=0, step=50)

    # --- 🛠️ Helper Functions ---
    def parse_availability(value):
        """Convert 'now' and 'soon' to today's date, otherwise parse normally."""
        value = str(value).strip()
        today = datetime.today().date()
        if value.lower() in ["now", "soon"]:
            return today  
        try:
            return parser.parse(value, fuzzy=True).date()
        except:
            return None  

    def format_fees(fees_list):
        """Formats parking & pet fees into readable text"""
        if not isinstance(fees_list, list) or not fees_list:
            return "Not specified"
        extracted_fees = []
        for category in fees_list:
            if isinstance(category, dict) and "fees" in category:
                for fee in category["fees"]:
                    key = fee.get("key", "").strip()
                    value = fee.get("value", "").strip()
                    if key and value and value != "--":
                        extracted_fees.append(f"{key}: {value}")
        return ", ".join(extracted_fees) if extracted_fees else "Not specified"

    # 🏡 Filter & Display Results
    if st.sidebar.button("🔎 Search"):
        filtered_df = df.copy()

        filtered_df["Rent"] = filtered_df["Rent"].astype(str).str.replace("[$,]", "", regex=True)
        filtered_df["Rent"] = pd.to_numeric(filtered_df["Rent"], errors="coerce").fillna(0).astype(int)

        filtered_df["Square Footage"] = pd.to_numeric(filtered_df["Square Footage"], errors="coerce")
        filtered_df["Availability"] = filtered_df["Availability"].astype(str).str.strip()
        filtered_df["Availability Date"] = filtered_df["Availability"].apply(parse_availability)
        filtered_df["Availability Date"] = pd.to_datetime(filtered_df["Availability Date"], errors="coerce").dt.date

        filtered_df["Parking Fees"] = filtered_df["Parking Fees"].apply(lambda x: format_fees(eval(x)) if isinstance(x, str) else format_fees(x))
        filtered_df["Pet Fees"] = filtered_df["Pet Fees"].apply(lambda x: format_fees(eval(x)) if isinstance(x, str) else format_fees(x))
        filtered_df["Application Fee"] = filtered_df.get("Application Fee", "N/A")

        # Apply filters
        if move_date:
            filtered_df = filtered_df[(filtered_df["Availability Date"].notna()) & (filtered_df["Availability Date"] <= move_date)]
        if apartment_name:
            filtered_df = filtered_df[filtered_df["Property Name"].str.contains(apartment_name, case=False, na=False)]
        if max_price > 0:
            filtered_df = filtered_df[filtered_df["Rent"] <= max_price]
        if neighborhood:
            filtered_df = filtered_df[filtered_df["Neighborhood"].str.contains(neighborhood, case=False, na=False)]
        if bedrooms:
            filtered_df = filtered_df[filtered_df["Bedrooms"].str.contains(bedrooms, case=False, na=False)]
        if min_sqft > 0:
            filtered_df = filtered_df[filtered_df["Square Footage"] >= min_sqft]

        filtered_df = filtered_df.drop_duplicates(subset=["Property Name", "Unit Number", "Rent", "Availability"], keep="first")

        if not filtered_df.empty:
            for _, row in filtered_df.iterrows():
                application_fee = row["Application Fee"] if "Application Fee" in row else "N/A"
                commission = row["Commission"] if "Commission" in row else "Not Available"
                st.markdown(f"""
                <div class='apartment-card'>
                    <h2 style="color: {PRIMARY_COLOR};">🏢 {row["Property Name"]}</h2>
                    <p>📍 <b>Address:</b> {row["Address"]} - {row["Neighborhood"]}</p>
                    <p class='rent-price'>💰 Rent: ${row["Rent"]:,.0f}</p>
                    <p>📅 <b>Availability:</b> {row["Availability"]}</p>
                    <p>🛏️ <b>Bedrooms:</b> {row["Bedrooms"]} | 🛁 <b>Bathrooms:</b> {row["Bathrooms"]}</p>
                    <p>🏠 <b>Floorplan:</b> {row["Floorplan"]}</p>
                    <p>🔢 <b>Unit Number:</b> {row["Unit Number"]}</p>
                    <p>💰 <b>Commission:</b> {commission}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ No apartments found. Try adjusting your search criteria.")
