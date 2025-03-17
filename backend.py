from flask import Flask, request, jsonify
import requests
import pandas as pd

app = Flask(__name__)

# APIFY API URL (Replace with your actual API URL)
APIFY_API_URL = "https://api.apify.com/v2/datasets/jTMxakh4vuvXiMo8J/items"

# Load property locations CSV for neighborhood corrections
try:
    property_locations = pd.read_csv("Property_Locations.csv")
    property_locations.columns = property_locations.columns.str.strip().str.lower()

    if "property name" in property_locations.columns and "property location" in property_locations.columns:
        property_locations_dict = {
            name.strip().lower(): location for name, location in zip(
                property_locations["property name"], property_locations["property location"]
            )
        }
    else:
        print("⚠️ CSV does not contain expected columns: 'Property Name' & 'Property Location'")
        property_locations_dict = {}
except Exception as e:
    print(f"⚠️ Error loading Property_Locations.csv: {e}")
    property_locations_dict = {}

# Load commission data CSV
try:
    commission_data = pd.read_csv("Formatted_Commission_Manifest.csv")
    commission_data.columns = commission_data.columns.str.strip().str.lower()

    if "property name" in commission_data.columns and "commission" in commission_data.columns:
        commission_dict = {
            name.strip().lower(): commission for name, commission in zip(
                commission_data["property name"], commission_data["commission"]
            )
        }
    else:
        print("⚠️ CSV does not contain expected columns: 'Property Name' & 'Commission'")
        commission_dict = {}
except Exception as e:
    print(f"⚠️ Error loading Formatted_Commission_Manifest.csv: {e}")
    commission_dict = {}

def fetch_data():
    response = requests.get(APIFY_API_URL)
    if response.status_code == 200:
        return response.json()
    return []

@app.route('/search', methods=['GET'])
def search():
    data = fetch_data()

    results = []
    for item in data:
        property_name = item.get("propertyName", "N/A").strip().lower()  # Normalize for matching
        address = item.get("location", {}).get("fullAddress", "N/A")

        # Replace neighborhood with correct one from CSV if available
        neighborhood = property_locations_dict.get(property_name, item.get("location", {}).get("neighborhood", "N/A"))

        # Get commission from CSV if available
        commission = commission_dict.get(property_name, "Not Available")

        walk_score = item.get("scores", {}).get("walkScore", "N/A")
        transit_score = item.get("scores", {}).get("transitScore", "N/A")
        description = item.get("description", "No description available")
        url = item.get("url", "#")
        photos = item.get("photos", [])

        # Coordinates for map feature
        latitude = item.get("coordinates", {}).get("latitude", None)
        longitude = item.get("coordinates", {}).get("longitude", None)

        # Rent Range
        rent_data = item.get("rent", {})
        min_rent = rent_data.get("min", "N/A")
        max_rent = rent_data.get("max", "N/A")

        # Parking & Pet Fees
        parking_fees = item.get("parkingFees", "Not specified")
        pet_fees = item.get("petFees", "Not specified")

        # Schools Nearby
        schools = item.get("schools", {}).get("public", []) + item.get("schools", {}).get("private", [])

        # Nearby Points of Interest (Transit & Shopping)
        transit_poi = item.get("transitAndPOI", [])

        # Apartment Models (Units Available)
        models = item.get("models", [])
        for model in models:
            floorplan_name = model.get("modelName", "N/A")
            rent_label = model.get("rentLabel", "N/A")
            details = model.get("details", [])
            bedrooms = details[0] if details else "N/A"
            bathrooms = details[1] if len(details) > 1 else "N/A"
            sqft = details[2] if len(details) > 2 else "N/A"
            deposit = details[3] if len(details) > 3 else "N/A"

            units = model.get("units", [])
            for unit in units:
                unit_number = unit.get("type", "N/A")
                unit_rent = unit.get("price", rent_label)
                unit_sqft = unit.get("sqft", sqft)
                availability = unit.get("availability", "Unknown")

                results.append({
                    "Property Name": item.get("propertyName", "N/A"),  # Original casing
                    "Address": address,
                    "Neighborhood": neighborhood,
                    "Commission": commission,  # Fixed commission matching
                    "Rent": unit_rent,
                    "Deposit": deposit,
                    "Floorplan": floorplan_name,
                    "Unit Number": unit_number,
                    "Bedrooms": bedrooms,
                    "Bathrooms": bathrooms,
                    "Square Footage": unit_sqft,
                    "Availability": availability,
                    "Walk Score": walk_score,
                    "Transit Score": transit_score,
                    "Parking Fees": parking_fees,
                    "Pet Fees": pet_fees,
                    "Schools Nearby": schools,
                    "Nearby Points of Interest": transit_poi,
                    "Description": description,
                    "URL": url,
                    "Photos": photos,
                    "Latitude": latitude,
                    "Longitude": longitude
                })

    return jsonify(results)

if __name__ == '__main__':
    # 🚀 FIX FOR RENDER DEPLOYMENT
    app.run(host="0.0.0.0", port=5000, debug=True)
