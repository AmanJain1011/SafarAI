"""
restaurants_api.py — Foursquare Places API
राजस्थान के रेस्तरां का डेटा Foursquare से लाता है।
Fetches restaurant data for Rajasthan cities using Foursquare Places API.
"""

import os
import time
import csv
import requests
from typing import Any
from dotenv import load_dotenv

load_dotenv()

FOURSQUARE_API_KEY = os.getenv("FOURSQUARE_API_KEY", "")
FOURSQUARE_BASE = "https://api.foursquare.com/v3/places/search"

# Foursquare category IDs for food / खाने की श्रेणियाँ
CATEGORY_IDS = {
    "restaurant": 13065,
    "cafe": 13032,
    "street_food": 13145,
    "vegetarian": 13377,
    "indian_restaurant": 13199,
}

# राजस्थान के प्रमुख शहर / Major Rajasthan cities
CITIES = ["Jaipur", "Jodhpur", "Udaipur", "Jaisalmer", "Pushkar", "Ajmer"]


def search_restaurants(city: str, category_id: int, limit: int = 50) -> list[dict[str, Any]]:
    """
    Foursquare API से रेस्तरां खोजता है।
    Searches restaurants in a city for a given Foursquare category ID.
    """
    headers = {
        "Authorization": FOURSQUARE_API_KEY,
        "Accept": "application/json",
    }
    params = {
        "near": f"{city}, Rajasthan, India",
        "categories": category_id,
        "limit": limit,
        "fields": "fsq_id,name,categories,location,geocodes,rating,price,hours,stats",
    }
    response = requests.get(FOURSQUARE_BASE, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    return response.json().get("results", [])


def parse_restaurant(raw: dict[str, Any], city: str) -> dict[str, Any]:
    """
    Raw Foursquare response को structured dict में बदलता है।
    Parses a raw Foursquare place into a structured restaurant dict.
    """
    location = raw.get("location", {})
    geocodes = raw.get("geocodes", {}).get("main", {})
    categories = raw.get("categories", [])
    category_name = categories[0].get("name", "") if categories else ""

    return {
        "city": city,
        "fsq_id": raw.get("fsq_id", ""),
        "name": raw.get("name", ""),
        "cuisine": category_name,
        "veg_only": "vegetarian" in category_name.lower()
        or "veg" in raw.get("name", "").lower(),
        "address": location.get("formatted_address", ""),
        "lat": geocodes.get("latitude", ""),
        "lon": geocodes.get("longitude", ""),
        "rating": raw.get("rating", ""),
        "price_tier": raw.get("price", ""),
        "avg_cost_for_two": estimate_cost(raw.get("price", 0)),
    }


def estimate_cost(price_tier) -> int:
    """
    Foursquare price tier से दो लोगों के लिए औसत खर्च अनुमानित करता है।
    Estimates average cost for two people based on Foursquare price tier (1-4).
    """
    mapping = {1: 200, 2: 500, 3: 1000, 4: 2000}
    try:
        return mapping.get(int(price_tier), 400)
    except (TypeError, ValueError):
        return 400


def collect_city_restaurants(city: str) -> list[dict[str, Any]]:
    """
    शहर के सभी श्रेणियों से रेस्तरां एकत्रित करता है (डुप्लिकेट हटाता है)।
    Collects restaurants for all categories in a city and deduplicates by fsq_id.
    """
    seen_ids: set[str] = set()
    restaurants: list[dict] = []

    for category_name, category_id in CATEGORY_IDS.items():
        print(f"[INFO] Fetching {category_name} in {city}…")
        try:
            results = search_restaurants(city, category_id)
        except Exception as exc:
            print(f"[WARN] Failed to fetch {category_name} in {city}: {exc}")
            time.sleep(0.3)
            continue

        for raw in results:
            fsq_id = raw.get("fsq_id", "")
            if fsq_id and fsq_id in seen_ids:
                continue
            if fsq_id:
                seen_ids.add(fsq_id)
            restaurants.append(parse_restaurant(raw, city))

        time.sleep(0.3)

    print(f"[INFO] Collected {len(restaurants)} restaurants for {city}")
    return restaurants


def save_restaurants_csv(restaurants: list[dict[str, Any]], filename: str) -> None:
    """
    रेस्तरां डेटा को CSV फ़ाइल में सहेजता है।
    Saves the list of restaurant dicts to a CSV file.
    """
    if not restaurants:
        print("[WARN] No restaurants to save.")
        return

    fieldnames = list(restaurants[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(restaurants)
    print(f"[INFO] Saved {len(restaurants)} restaurants → {filename}")


if __name__ == "__main__":
    # सभी शहरों का डेटा एकत्र करें / Collect data for all cities
    all_restaurants: list[dict] = []
    for city in CITIES:
        city_data = collect_city_restaurants(city)
        all_restaurants.extend(city_data)

    output_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "restaurants.csv"
    )
    save_restaurants_csv(all_restaurants, output_path)
