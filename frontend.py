import streamlit as st
import pandas as pd
import requests
from dateutil import parser
from datetime import datetime

# 🛠️ Ensure Page Config is the First Command
st.set_page_config(page_title="Charlotte Apartment Finder", page_icon="🏠", layout="wide")

# Set Backend API URL
BACKEND_URL = "http://127.0.0.1:5000/search"

# Function to Fetch Data
@st.cache_data
def fetch_data():
    response = requests.get(BACKEND_URL)
    if response.status_code == 200:
        return pd.DataFrame(response.json())  
    else:
        st.error("Failed to fetch data from backend.")
        return pd.DataFrame()

df = fetch_data()

# --- 💠 Apply Custom Page Styling ---
LOGO_URL = "https://i.imgur.com/LUQTwbB.png"  
PRIMARY_COLOR = "#2F80ED"  
BACKGROUND_COLOR = "#F7F9FC"  
TEXT_COLOR = "#000000"  

# --- 🎨 Custom Styling (CSS) ---
st.markdown(f"""
    <style>
        body {{
            background-color: {BACKGROUND_COLOR};
            font-family: 'Arial', sans-serif;
        }}
        .stApp {{
            background-color: {BACKGROUND_COLOR};
        }}
        .title-container {{
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .title-container img {{
            max-width: 180px;
            margin-right: 15px;
        }}
        .apartment-card {{
            background-color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            color: {TEXT_COLOR};  
        }}
        .rent-price {{
            font-size: 22px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        }}
        .search-button {{
            background-color: {PRIMARY_COLOR};
            color: white;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            text-align: center;
            display: block;
            width: 100%;
        }}
    </style>
""", unsafe_allow_html=True)

# --- 🏠 Page Title & Branding ---
st.markdown(f"""
    <div class='title-container'>
        <img src="{LOGO_URL}" alt="Charlotte Apartment Finders Logo">
        <h1 style="color: {PRIMARY_COLOR};">Charlotte Apartment Finder</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown("### Find Your Dream Apartment in Charlotte ✨")

# --- 🔍 Sidebar for Filters ---
st.sidebar.header("🔍 Search Filters")
apartment_name = st.sidebar.text_input("Apartment Name (Optional)", "")
move_date = st.sidebar.date_input("Move-In Date (Optional)", value=None)
max_price = st.sidebar.number_input("Max Rent ($) (Optional)", value=0, step=100)
neighborhood = st.sidebar.text_input("Neighborhood (Optional)", "")
bedrooms = st.sidebar.text_input("Bedrooms (Optional, e.g., Studio, 1 Bed, 2 Beds)", "")
min_sqft = st.sidebar.number_input("Minimum Square Footage (Optional)", value=0, step=50)

# --- 🛠️ Function to Parse Availability Dates ---
def parse_availability(value):
    value = str(value).strip()
    today = datetime.today().date()
    if value.lower() in ["now", "soon"]:
        return today  
    try:
        parsed_date = parser.parse(value, fuzzy=True).date()
        return parsed_date
    except:
        return None  

# --- 🛠️ Function to Format Parking & Pet Fees (Restored) ---
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

if st.sidebar.button("🔎 Search"):
    filtered_df = df.copy()

    # --- 🛠️ Fix Rent Extraction from `price` ---
    filtered_df["Rent"] = filtered_df["Rent"].astype(str).str.replace("[$,]", "", regex=True)  
    filtered_df["Rent"] = pd.to_numeric(filtered_df["Rent"], errors="coerce").fillna(0).astype(int)  

    # Convert other data types
    filtered_df["Square Footage"] = pd.to_numeric(filtered_df["Square Footage"], errors="coerce")
    filtered_df["Availability"] = filtered_df["Availability"].astype(str).str.strip()
    filtered_df["Availability"] = filtered_df["Availability"].fillna("Unknown")
    filtered_df["Availability Date"] = filtered_df["Availability"].apply(parse_availability)
    filtered_df["Availability Date"] = pd.to_datetime(filtered_df["Availability Date"], errors="coerce").dt.date

    # 🛠️ Apply Fix: Format Parking & Pet Fees
    filtered_df["Parking Fees"] = filtered_df["Parking Fees"].apply(lambda x: format_fees(eval(x)) if isinstance(x, str) else format_fees(x))
    filtered_df["Pet Fees"] = filtered_df["Pet Fees"].apply(lambda x: format_fees(eval(x)) if isinstance(x, str) else format_fees(x))

    if move_date:
        move_date = move_date  
        filtered_df = filtered_df[
            (filtered_df["Availability Date"].notna()) & (filtered_df["Availability Date"] <= move_date)  
        ]

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

    # --- 🏠 Display Results with Card Style ---
    if not filtered_df.empty:
        for _, row in filtered_df.iterrows():
            st.markdown(f"""
            <div class='apartment-card'>
                <h2 style="color: {PRIMARY_COLOR};">🏢 {row["Property Name"]}</h2>
                <p style="color: {TEXT_COLOR};">📍 <b>Address:</b> {row["Address"]} - {row["Neighborhood"]}</p>
                <p style="color: {TEXT_COLOR};">🏠 <b>Floorplan:</b> {row["Floorplan"]}</p>
                <p style="color: {TEXT_COLOR};">🔢 <b>Unit:</b> {row["Unit Number"]}</p>
                <p class='rent-price'>💰 Rent: ${row["Rent"]:,.0f}</p>
                <p style="color: {TEXT_COLOR};">🚗 <b>Parking Fees:</b> {row["Parking Fees"]}</p>
                <p style="color: {TEXT_COLOR};">🐶 <b>Pet Fees:</b> {row["Pet Fees"]}</p>
                <a href="{row["URL"]}" target="_blank" style="display:inline-block; padding:8px 12px; background:{PRIMARY_COLOR}; color:white; border-radius:5px; text-decoration:none;">🔗 View Listing</a>
            </div>
            """, unsafe_allow_html=True)

            st.divider()
    else:
        st.warning("⚠️ No apartments found. Try adjusting your search criteria.")
