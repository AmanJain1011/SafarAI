"""
hotels_api.py — Makcorps Hotel Price API
राजस्थान के होटलों का डेटा Makcorps API से लाता है।
Fetches hotel price data for Rajasthan cities using the Makcorps API.
"""

import os
import time
import csv
from datetime import date, timedelta
from typing import Any
import requests
from dotenv import load_dotenv

load_dotenv()

MAKCORPS_API_KEY = os.getenv("MAKCORPS_API_KEY", "")
MAKCORPS_BASE = "https://api.makcorps.com"

# बजट होटल की अधिकतम कीमत / Maximum price for budget hotels (INR/night)
BUDGET_THRESHOLD = 2000


def search_hotels_by_city(
    city: str,
    checkin: str | None = None,
    checkout: str | None = None,
) -> list[dict[str, Any]]:
    """
    शहर के होटलों की खोज करता है।
    Searches hotels in a city; defaults to tomorrow's date for check-in.
    """
    if checkin is None:
        checkin = str(date.today() + timedelta(days=1))
    if checkout is None:
        checkout = str(date.today() + timedelta(days=2))

    url = f"{MAKCORPS_BASE}/city"
    params = {
        "cityid": city,
        "checkin": checkin,
        "checkout": checkout,
        "adults": 2,
        "rooms": 1,
        "currency": "INR",
        "api_key": MAKCORPS_API_KEY,
    }
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    # Makcorps returns results list inside data / डेटा में results list होती है
    if isinstance(data, list):
        return data
    return data.get("hotels", data.get("results", []))


def parse_hotel(raw: dict[str, Any], city: str) -> dict[str, Any]:
    """
    Raw Makcorps hotel dict को structured format में बदलता है।
    Parses a raw Makcorps hotel entry into a structured dict.
    """
    try:
        price = float(raw.get("price", raw.get("min_price", 0)) or 0)
    except (ValueError, TypeError):
        price = 0.0

    return {
        "city": city,
        "hotel_id": raw.get("hotel_id", raw.get("id", "")),
        "name": raw.get("name", raw.get("hotel_name", "")),
        "price_per_night": price,
        "category": classify_hotel(price),
        "rating": raw.get("rating", raw.get("stars", "")),
        "address": raw.get("address", ""),
        "lat": raw.get("latitude", raw.get("lat", "")),
        "lon": raw.get("longitude", raw.get("lon", "")),
        "amenities": raw.get("amenities", ""),
    }


def classify_hotel(price: float) -> str:
    """
    कीमत के आधार पर होटल की श्रेणी तय करता है।
    Classifies a hotel into a tier based on nightly price (INR).
    """
    if price < 500:
        return "ultra-budget"
    if price < 1000:
        return "budget"
    if price < 2500:
        return "mid-range"
    if price < 5000:
        return "premium"
    return "luxury"


def collect_city_hotels(city: str) -> list[dict[str, Any]]:
    """
    शहर के बजट होटल (≤₹2000) एकत्रित करता है।
    Collects hotels for a city, filtering to budget hotels (≤₹2000/night).
    """
    print(f"[INFO] Fetching hotels for {city}…")
    try:
        raw_hotels = search_hotels_by_city(city)
    except Exception as exc:
        print(f"[WARN] Failed to fetch hotels for {city}: {exc}")
        return []

    hotels = [parse_hotel(h, city) for h in raw_hotels]
    budget = [h for h in hotels if h["price_per_night"] <= BUDGET_THRESHOLD]
    print(f"[INFO] {len(budget)}/{len(hotels)} budget hotels for {city}")
    return budget


def save_hotels_csv(hotels: list[dict[str, Any]], filename: str) -> None:
    """
    होटल डेटा को CSV फ़ाइल में सहेजता है।
    Saves the list of hotel dicts to a CSV file.
    """
    if not hotels:
        print("[WARN] No hotels to save.")
        return

    fieldnames = list(hotels[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(hotels)
    print(f"[INFO] Saved {len(hotels)} hotels → {filename}")


if __name__ == "__main__":
    # Free tier: ~100 calls/day, इसलिए अभी सिर्फ जयपुर
    # Free tier limit: only Jaipur for now to conserve quota
    jaipur_hotels = collect_city_hotels("Jaipur")
    output_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "hotels.csv"
    )
    save_hotels_csv(jaipur_hotels, output_path)
    time.sleep(0.3)
