"""
attractions_api.py — OpenTripMap API + Nominatim Geocoding
राजस्थान के पर्यटन स्थलों का डेटा OpenTripMap API से लाता है।
Fetches tourist attractions for Rajasthan cities via OpenTripMap + Nominatim.
"""

import os
import time
import csv
import requests
from typing import Any
from geopy.geocoders import Nominatim
from dotenv import load_dotenv

load_dotenv()

OPENTRIPMAP_API_KEY = os.getenv("OPENTRIPMAP_API_KEY", "")
OPENTRIPMAP_BASE = "https://api.opentripmap.com/0.1/en/places"

# राजस्थान के प्रमुख शहर / Major Rajasthan cities
CITIES = ["Jaipur", "Jodhpur", "Udaipur", "Jaisalmer", "Pushkar", "Ajmer"]


def get_city_coordinates(city_name: str) -> tuple[float, float] | None:
    """
    Nominatim से शहर के निर्देशांक प्राप्त करता है।
    Returns (lat, lon) for the given city using Nominatim geocoding.
    """
    geolocator = Nominatim(user_agent="safarai_scraper/1.0")
    location = geolocator.geocode(f"{city_name}, Rajasthan, India")
    if location:
        return location.latitude, location.longitude
    return None


def get_attractions_near(
    lat: float,
    lon: float,
    radius_m: int = 20000,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    OpenTripMap /radius endpoint से आकर्षण लाता है।
    Fetches attractions within radius_m metres of (lat, lon).
    """
    url = f"{OPENTRIPMAP_BASE}/radius"
    params = {
        "radius": radius_m,
        "lon": lon,
        "lat": lat,
        "limit": limit,
        "format": "json",
        "apikey": OPENTRIPMAP_API_KEY,
    }
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def get_attraction_details(xid: str) -> dict[str, Any]:
    """
    OpenTripMap /xid endpoint से विस्तृत जानकारी लाता है।
    Returns detailed info for a single attraction by its xid.
    """
    url = f"{OPENTRIPMAP_BASE}/xid/{xid}"
    params = {"apikey": OPENTRIPMAP_API_KEY}
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def collect_city_attractions(city_name: str, state: str = "Rajasthan") -> list[dict[str, Any]]:
    """
    शहर के सभी आकर्षण एकत्रित करता है।
    Combines geocoding + nearby search + detail fetch for a city.
    """
    print(f"[INFO] Processing city: {city_name}, {state}")

    coords = get_city_coordinates(city_name)
    if not coords:
        print(f"[WARN] Could not geocode {city_name}")
        return []

    lat, lon = coords
    print(f"[INFO] Coordinates: lat={lat:.4f}, lon={lon:.4f}")
    time.sleep(0.3)

    raw_list = get_attractions_near(lat, lon)
    print(f"[INFO] Found {len(raw_list)} raw attractions near {city_name}")
    time.sleep(0.3)

    attractions = []
    for item in raw_list:
        xid = item.get("xid")
        if not xid:
            continue
        try:
            details = get_attraction_details(xid)
            attractions.append(
                {
                    "city": city_name,
                    "state": state,
                    "xid": xid,
                    "name": details.get("name", ""),
                    "kinds": details.get("kinds", ""),
                    "lat": details.get("point", {}).get("lat", ""),
                    "lon": details.get("point", {}).get("lon", ""),
                    "wikipedia": details.get("wikipedia", ""),
                    "image": details.get("preview", {}).get("source", ""),
                    "description": details.get("wikipedia_extracts", {}).get(
                        "text", ""
                    ),
                    "rate": details.get("rate", ""),
                }
            )
        except Exception as exc:
            print(f"[WARN] Could not fetch details for xid={xid}: {exc}")
        time.sleep(0.3)

    print(f"[INFO] Collected {len(attractions)} attractions for {city_name}")
    return attractions


def save_attractions_csv(attractions: list[dict[str, Any]], filename: str) -> None:
    """
    आकर्षणों को CSV फ़ाइल में सहेजता है।
    Saves the list of attraction dicts to a CSV file.
    """
    if not attractions:
        print("[WARN] No attractions to save.")
        return

    fieldnames = list(attractions[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(attractions)
    print(f"[INFO] Saved {len(attractions)} attractions → {filename}")


if __name__ == "__main__":
    # सभी शहरों का डेटा एकत्र करें / Collect data for all cities
    all_attractions: list[dict] = []
    for city in CITIES:
        city_data = collect_city_attractions(city)
        all_attractions.extend(city_data)

    output_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "attractions.csv"
    )
    save_attractions_csv(all_attractions, output_path)
