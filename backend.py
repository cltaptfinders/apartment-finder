from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# APIFY API URL (Replace with your actual API URL)
APIFY_API_URL = "https://api.apify.com/v2/datasets/jTMxakh4vuvXiMo8J/items"

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
        property_name = item.get("propertyName", "N/A")
        address = item.get("location", {}).get("fullAddress", "N/A")
        neighborhood = item.get("location", {}).get("neighborhood", "N/A")
        walk_score = item.get("scores", {}).get("walkScore", "N/A")
        transit_score = item.get("scores", {}).get("transitScore", "N/A")
        description = item.get("description", "No description available")
        url = item.get("url", "#")
        photos = item.get("photos", [])

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
                    "Property Name": property_name,
                    "Address": address,
                    "Neighborhood": neighborhood,
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
                    "Photos": photos
                })

    return jsonify(results)

if __name__ == '__main__':
    # 🚀 FIX FOR RENDER DEPLOYMENT
    app.run(host="0.0.0.0", port=5000, debug=True)
