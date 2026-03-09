"""
google_places_api.py — Google Places API (Nearby Search + Place Details)
Google Places API से जयपुर के पर्यटन स्थलों का डेटा लाता है।
Fetches tourist attraction data for Jaipur using the Google Places API.
Note: Only Jaipur is processed to conserve the $200 free credit.
"""

import os
import time
import csv
import requests
from typing import Any
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
NEARBY_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


def search_tourist_attractions(city: str, radius_m: int = 20000) -> list[dict[str, Any]]:
    """
    Google Places Nearby Search से पर्यटन स्थल खोजता है।
    Returns a list of place stubs (place_id, name, location) near the city centre.
    Falls back to Nominatim to geocode the city if needed.
    """
    from geopy.geocoders import Nominatim

    geolocator = Nominatim(user_agent="safarai_google/1.0")
    location = geolocator.geocode(f"{city}, Rajasthan, India")
    if not location:
        print(f"[WARN] Could not geocode {city}")
        return []

    lat, lon = location.latitude, location.longitude
    time.sleep(0.3)

    results: list[dict] = []
    params = {
        "location": f"{lat},{lon}",
        "radius": radius_m,
        "type": "tourist_attraction",
        "key": GOOGLE_API_KEY,
    }

    while True:
        response = requests.get(NEARBY_SEARCH_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        results.extend(data.get("results", []))

        next_token = data.get("next_page_token")
        if not next_token:
            break
        # Google requires a short delay before using next_page_token
        time.sleep(2)
        params = {"pagetoken": next_token, "key": GOOGLE_API_KEY}

    print(f"[INFO] Found {len(results)} places near {city}")
    return results


def get_place_details(place_id: str) -> dict[str, Any]:
    """
    Google Place Details API से विस्तृत जानकारी लाता है।
    Fetches detailed information for a single place by place_id.
    """
    params = {
        "place_id": place_id,
        "fields": "place_id,name,rating,user_ratings_total,formatted_address,"
        "geometry,types,opening_hours,price_level,photos,editorial_summary",
        "key": GOOGLE_API_KEY,
    }
    response = requests.get(DETAILS_URL, params=params, timeout=15)
    response.raise_for_status()
    return response.json().get("result", {})


def parse_google_place(raw: dict[str, Any], city: str) -> dict[str, Any]:
    """
    Raw Google Places dict को structured attraction dict में बदलता है।
    Parses a raw Google Places result into a structured dict.
    """
    geometry = raw.get("geometry", {}).get("location", {})
    return {
        "city": city,
        "place_id": raw.get("place_id", ""),
        "name": raw.get("name", ""),
        "rating": raw.get("rating", ""),
        "user_ratings_total": raw.get("user_ratings_total", ""),
        "address": raw.get("formatted_address", raw.get("vicinity", "")),
        "lat": geometry.get("lat", ""),
        "lon": geometry.get("lng", ""),
        "types": "|".join(raw.get("types", [])),
        "price_level": raw.get("price_level", ""),
        "open_now": raw.get("opening_hours", {}).get("open_now", ""),
        "summary": raw.get("editorial_summary", {}).get("overview", ""),
    }


if __name__ == "__main__":
    # $200 क्रेडिट बचाने के लिए अभी सिर्फ जयपुर
    # Only Jaipur to conserve the $200 Google Maps credit
    city = "Jaipur"
    stubs = search_tourist_attractions(city)

    places: list[dict] = []
    for stub in stubs:
        place_id = stub.get("place_id", "")
        if not place_id:
            continue
        try:
            details = get_place_details(place_id)
            places.append(parse_google_place(details, city))
        except Exception as exc:
            print(f"[WARN] Details failed for place_id={place_id}: {exc}")
        time.sleep(0.3)

    output_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "google_places.csv"
    )
    if places:
        fieldnames = list(places[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(places)
        print(f"[INFO] Saved {len(places)} Google places → {output_path}")
    else:
        print("[WARN] No places collected.")
