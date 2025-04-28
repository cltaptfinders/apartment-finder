def dedup_fee_string(fee_str):
    if not isinstance(fee_str, str):
        return fee_str
    parts = [p.strip() for p in fee_str.split(",")]
    seen = set()
    deduped = []
    for part in parts:
        if part not in seen:
            deduped.append(part)
            seen.add(part)
    return ", ".join(deduped)

import streamlit as st
import pandas as pd
import requests
import json
import os
import time
import base64
import firebase_admin
from firebase_admin import auth, credentials
from firebase_admin import firestore
from dateutil import parser
from datetime import datetime

# 🏠 Page Configuration
st.set_page_config(page_title="Charlotte Apartment Finder", page_icon="🏠", layout="wide")

# 📡 Firebase Authentication Setup (Using Base64 Encoding)
firebase_key_b64 = os.getenv("FIREBASE_KEY_B64")  # Retrieve Base64-encoded key

if firebase_key_b64:
    try:
        firebase_key_json = base64.b64decode(firebase_key_b64).decode("utf-8")  # Decode to JSON string
        firebase_key_dict = json.loads(firebase_key_json)  # Convert JSON string to dictionary

        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_key_dict)
            firebase_admin.initialize_app(cred)

        print("✅ Firebase successfully initialized!")
    except Exception as e:
        st.error(f"⚠️ Firebase initialization failed: {e}")
        st.stop()
else:
    st.error("⚠️ FIREBASE_KEY_B64 is missing in environment variables.")
    st.stop()

# 🔑 Firebase Web API Key
FIREBASE_WEB_API_KEY = "AIzaSyAdWQkhvXlzK4wRy7JxCbWkOGIC3Wkts38"

def authenticate_user(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=payload)
    data = response.json()
    return data if "idToken" in data else None

if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

def login_page():
    st.title("🔐 Login to Apartment Finders AI")
    st.sidebar.image("Logo Ai.png", width=200)
    email = st.text_input("📧 Email", key="email")
    password = st.text_input("🔑 Password", type="password", key="password")

    if st.button("Login"):
        user_data = authenticate_user(email, password)
        if user_data:
            firebase_user = auth.get_user_by_email(email)
            user_role = firebase_user.custom_claims.get("role", "agent")
            st.session_state.user = user_data
            st.session_state.role = user_role
            st.success(f"✅ Successfully logged in as {user_role.capitalize()}!")
            st.rerun()
        else:
            st.error("❌ Invalid email or password. Please try again.")

if st.session_state.user:
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()

if not st.session_state.user:
    login_page()
    st.stop()

st.sidebar.title("📌 Navigation")
nav_options = ["Apartment Finder", "Property Map"]
if st.session_state.role == "admin":
    nav_options.append("Manage Properties")
page = st.sidebar.radio("Go to", nav_options)

# 🚫 Temporarily disable live API fetch to avoid backend timeout
JSON_FILE = "data.json"

@st.cache_data
def fetch_data():
    if not os.path.exists(JSON_FILE):
        st.error("⚠️ data.json file not found.")
        return pd.DataFrame()
    with open(JSON_FILE, "r") as f:
        local_df = pd.DataFrame(json.load(f))

    # Merge Firebase overrides
    try:
        db = firestore.client()
        overrides = db.collection("properties").stream()
        override_data = {}
        for doc in overrides:
            override_data[doc.id] = doc.to_dict()

        for prop_name, updates in override_data.items():
            mask = local_df["Property Name"].str.strip().str.lower() == prop_name.strip().lower()
            for key, value in updates.items():
                local_df.loc[mask, key] = value

    except Exception as e:
        st.warning(f"⚠️ Failed to load overrides from Firebase: {e}")

    return local_df

df = fetch_data()

LOGO_URL = "https://raw.githubusercontent.com/cltaptfinders/apartment-finder/main/Logo%20Ai.png"
PRIMARY_COLOR = "#2F80ED"

st.sidebar.image(LOGO_URL, width=200)

if page == "Property Map":
    st.title("📍 Charlotte Apartment Map")
    st.markdown("### Hover over any property to see its name and commission.")

    import pydeck as pdk

    def format_commission(val):
        try:
            val_str = str(val).strip()
            if "$" in val_str:
                return f"${float(val_str.replace('$', '').replace(',', '')):,.0f}"
            elif "%" in val_str:
                return f"{float(val_str.replace('%', '')):.0f}%"
            else:
                num = float(val_str)
                if num <= 100:
                    return f"{num:.0f}%"
                else:
                    return f"${num:,.0f}"
        except:
            return "N/A"

    def format_rent(val):
        try:
            return f"${float(str(val).replace('$', '').replace(',', '')):,.0f}"
        except:
            return "N/A"

    def parse_commission_value(val):
        try:
            val_str = str(val).replace("$", "").replace("%", "").replace(",", "").strip()
            return float(val_str)
        except:
            return 0

    def extract_bedroom_range(property_name, df):
        beds = df[df["Property Name"] == property_name]["Bedrooms"].dropna().unique().tolist()
        beds = [b.strip() for b in beds if isinstance(b, str)]
        if not beds:
            return "N/A"
        try:
            bed_numbers = []
            for b in beds:
                if "studio" in b.lower():
                    bed_numbers.append(0)
                else:
                    num = int("".join([c for c in b if c.isdigit()]))
                    bed_numbers.append(num)
            return f"{'Studio' if 0 in bed_numbers else min(bed_numbers)}–{max(bed_numbers)} Beds"
        except:
            return ", ".join(beds)

    def extract_rent_range(property_name, df):
        rents = df[df["Property Name"] == property_name]["Rent"]
        rents = rents.astype(str).str.replace("[$,]", "", regex=True)
        rents = pd.to_numeric(rents, errors="coerce").dropna()
        if rents.empty:
            return "N/A"
        min_rent = rents.min()
        max_rent = rents.max()
        if min_rent == max_rent:
            return f"${min_rent:,.0f}"
        return f"${min_rent:,.0f}–${max_rent:,.0f}"

    df_map = df.copy()
    df_map = df_map.dropna(subset=["Latitude", "Longitude"])
    df_map["Latitude"] = pd.to_numeric(df_map["Latitude"], errors="coerce")
    df_map["Longitude"] = pd.to_numeric(df_map["Longitude"], errors="coerce")

    df_map["Commission Value"] = df_map["Commission"].apply(parse_commission_value)

    def get_marker_color(val, raw_val):
        try:
            raw_str = str(raw_val)
            if "$" in raw_str and val >= 1500:
                return [0, 200, 0, 160]  # green for flat $1500+
            elif "%" in raw_str and val >= 100:
                return [0, 200, 0, 160]  # green for 100%+
            elif "$" in raw_str and val <= 500:
                return [255, 215, 0, 160]  # yellow for flat $500 or less
            else:
                return [47, 128, 237, 160]  # blue
        except:
            return [47, 128, 237, 160]

    df_map["marker_color"] = df_map.apply(lambda row: get_marker_color(row["Commission Value"], row["Commission"]), axis=1)

    df_map["tooltip"] = df_map.apply(
        lambda row: f"{row['Property Name']}<br>💰 Commission: {format_commission(row.get('Commission'))}<br>💵 Rent: {extract_rent_range(row['Property Name'], df)}<br>🛏️ Bedrooms: {extract_bedroom_range(row['Property Name'], df)}", 
        axis=1
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_map,
        get_position='[Longitude, Latitude]',
        get_fill_color='marker_color',
        get_radius=80,
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=df_map["Latitude"].mean(),
        longitude=df_map["Longitude"].mean(),
        zoom=11,
        pitch=0,
    )

    tooltip = {"html": "{tooltip}", "style": {"backgroundColor": "white", "color": "black"}}

    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip))

if page == "Apartment Finder":
    st.markdown("### Find Your Dream Apartment in Charlotte ✨")

    st.sidebar.header("🔍 Search Filters")
    apartment_name = st.sidebar.text_input("Apartment Name (Optional)", "")
    move_date = st.sidebar.date_input("Move-In Date (Optional)", value=None)
    max_price = st.sidebar.number_input("Max Rent ($) (Optional)", value=0, step=100)
    neighborhoods = df["Neighborhood"].dropna().unique().tolist()
    selected_neighborhoods = st.sidebar.multiselect("Neighborhood(s)", sorted(neighborhoods))
    bedrooms = st.sidebar.text_input("Bedrooms (Optional, e.g., Studio, 1 Bed, 2 Beds)", "")
    min_sqft = st.sidebar.number_input("Minimum Square Footage (Optional)", value=0, step=50)
    show_all_units = st.sidebar.checkbox("Show all matching units", value=False)

    def parse_availability(value):
        value = str(value).strip()
        today = datetime.today().date()
        if value.lower() in ["now", "soon"]:
            return today
        try:
            return parser.parse(value, fuzzy=True).date()
        except:
            return None

    def format_fees(fees_list):
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

        required_columns = ["Property Name", "Unit Number", "Rent", "Square Footage", "Availability"]
        for col in required_columns:
            if col not in filtered_df.columns:
                st.error(f"⚠️ Error: '{col}' column missing from data. Please check backend response.")
                st.stop()

        filtered_df["Rent"] = filtered_df["Rent"].astype(str).str.replace("[$,]", "", regex=True)
        filtered_df["Rent"] = pd.to_numeric(filtered_df["Rent"], errors="coerce").fillna(0).astype(int)
        filtered_df["Square Footage"] = pd.to_numeric(filtered_df["Square Footage"], errors="coerce")
        filtered_df["Availability"] = filtered_df["Availability"].astype(str).str.strip()
        filtered_df["Availability Date"] = filtered_df["Availability"].apply(parse_availability)
        filtered_df["Availability Date"] = pd.to_datetime(filtered_df["Availability Date"], errors="coerce").dt.date
        filtered_df["Parking Fees"] = filtered_df["Parking Fees"].apply(lambda x: format_fees(eval(x)) if isinstance(x, str) else format_fees(x))
        filtered_df["Pet Fees"] = filtered_df["Pet Fees"].apply(lambda x: format_fees(eval(x)) if isinstance(x, str) else format_fees(x))
        filtered_df["Application Fee"] = filtered_df.get("Application Fee", "N/A")

        if move_date:
            filtered_df = filtered_df[(filtered_df["Availability Date"].notna()) & (filtered_df["Availability Date"] <= move_date)]
        if apartment_name:
            filtered_df = filtered_df[filtered_df["Property Name"].str.contains(apartment_name, case=False, na=False)]
        if max_price > 0:
            filtered_df = filtered_df[filtered_df["Rent"] <= max_price]
        if selected_neighborhoods:
            filtered_df = filtered_df[filtered_df["Neighborhood"].isin(selected_neighborhoods)]
        if bedrooms:
            filtered_df = filtered_df[filtered_df["Bedrooms"].str.contains(bedrooms, case=False, na=False)]
        if min_sqft > 0:
            filtered_df = filtered_df[filtered_df["Square Footage"] >= min_sqft]

        if not show_all_units:
            filtered_df = filtered_df.sort_values(by="Rent").drop_duplicates(subset=["Property Name"], keep="first")

        if not filtered_df.empty:
            for _, row in filtered_df.iterrows():
                application_fee = row.get("Application Fee", "N/A")
                commission = row.get("Commission", "Not Available")
                st.markdown(f"""
                <div class='apartment-card'>
                    <h2 style="color: {PRIMARY_COLOR};">🏢 {row["Property Name"]}</h2>
                    <p>📍 <b>Address:</b> {row["Address"]} - {row["Neighborhood"]}</p>
                    <p class='rent-price'>💰 Rent: ${row["Rent"]:,.0f}</p>
                    <p>📅 <b>Availability:</b> {row["Availability"]}</p>
                    <p>🛏️ <b>Bedrooms:</b> {row["Bedrooms"]} | 🛁 <b>Bathrooms:</b> {row["Bathrooms"]}</p>
                    <p>📏 <b>Square Footage:</b> {row["Square Footage"]} sqft</p>
                    <p>🚗 <b>Parking Fees:</b> {row["Parking Fees"]}</p>
                    <p>🐶 <b>Pet Fees:</b> {row["Pet Fees"]}</p>
                    <p>📝 <b>Application Fee:</b> {application_fee}</p>
                    <p>💰 <b>Commission:</b> {commission}</p>
                    <a href="{row["URL"]}" target="_blank" style="display:inline-block; padding:8px 12px; background:{PRIMARY_COLOR}; color:white; border-radius:5px; text-decoration:none;">🔗 View Listing</a>
                </div>
                """, unsafe_allow_html=True)
                st.divider()
        else:
            st.warning("⚠️ No apartments found. Try adjusting your search criteria.")

        if page == "Manage Properties" and st.session_state.role == "admin":
            st.title("🔧 Manage Property Data")
            st.markdown("Edit commission, deposit, and neighborhood directly from this dashboard.")

            editable_columns = ["Property Name", "Commission", "Deposit", "Neighborhood"]
            editable_df = df[editable_columns].copy()
            editable_df = editable_df.groupby("Property Name").agg({
                "Commission": "first",
                "Deposit": "first",
                "Neighborhood": "first"
            }).reset_index()

            edited_df = st.data_editor(editable_df, num_rows="dynamic", use_container_width=True)

        if st.button("💾 Save Changes"):
            db = firestore.client()
            update_count = 0
            for _, row in edited_df.iterrows():
                prop_name = str(row["Property Name"]).strip()
                doc_ref = db.collection("properties").document(prop_name)
                doc_ref.set({
                    "Commission": row["Commission"],
                    "Deposit": row["Deposit"],
                    "Neighborhood": row["Neighborhood"]
                }, merge=True)
                update_count += 1
            st.success(f"✅ {update_count} properties updated in Firebase.")

    st.warning("⚠️ Changes made here are not yet connected to Firebase. Let Brandon know when you're ready to save this live.")