"""
osm_attractions.py — Overpass API (OpenStreetMap) — No API key needed!
बिना API key के OpenStreetMap Overpass API से राजस्थान के पर्यटन स्थल लाता है।
Fetches Rajasthan tourist spots from Overpass API — no credentials required.
"""

import csv
import time
import requests
from typing import Any

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Overpass QL timeout / समयसीमा
OVERPASS_TIMEOUT = 60


def query_overpass(query: str) -> dict[str, Any]:
    """
    Overpass QL query चलाता है और JSON response देता है।
    Sends an Overpass QL query and returns the parsed JSON response.
    """
    response = requests.post(
        OVERPASS_URL,
        data={"data": query},
        timeout=OVERPASS_TIMEOUT + 10,
    )
    response.raise_for_status()
    return response.json()


def get_rajasthan_tourist_spots() -> list[dict[str, Any]]:
    """
    राजस्थान के किले, स्मारक, संग्रहालय और पर्यटन स्थल लाता है।
    Queries Overpass for attractions, forts, monuments and museums in Rajasthan.
    """
    query = f"""
    [out:json][timeout:{OVERPASS_TIMEOUT}];
    area["name"="Rajasthan"]["admin_level"="4"]->.rajasthan;
    (
      node["tourism"="attraction"](area.rajasthan);
      way["tourism"="attraction"](area.rajasthan);
      node["historic"="fort"](area.rajasthan);
      way["historic"="fort"](area.rajasthan);
      node["historic"="monument"](area.rajasthan);
      way["historic"="monument"](area.rajasthan);
      node["tourism"="museum"](area.rajasthan);
      way["tourism"="museum"](area.rajasthan);
    );
    out center tags;
    """
    print("[INFO] Querying Overpass for Rajasthan tourist spots…")
    data = query_overpass(query)
    return data.get("elements", [])


def get_city_restaurants_osm(city_name: str) -> list[dict[str, Any]]:
    """
    शहर के OSM रेस्तरां नोड्स लाता है।
    Queries Overpass for restaurant nodes in a given city.
    """
    query = f"""
    [out:json][timeout:{OVERPASS_TIMEOUT}];
    area["name"="{city_name}"]["admin_level"~"6|7|8"]->.city;
    (
      node["amenity"="restaurant"](area.city);
      node["amenity"="cafe"](area.city);
      node["amenity"="fast_food"](area.city);
    );
    out tags;
    """
    print(f"[INFO] Querying OSM restaurants for {city_name}…")
    data = query_overpass(query)
    return data.get("elements", [])


def parse_osm_attraction(element: dict[str, Any]) -> dict[str, Any]:
    """
    OSM element को structured attraction dict में बदलता है।
    Parses an OSM element (node or way) into a structured attraction dict.
    """
    tags = element.get("tags", {})

    # Ways have a 'center' key for lat/lon / Ways के लिए center lat/lon
    if element.get("type") == "way":
        center = element.get("center", {})
        lat = center.get("lat", "")
        lon = center.get("lon", "")
    else:
        lat = element.get("lat", "")
        lon = element.get("lon", "")

    return {
        "osm_id": element.get("id", ""),
        "osm_type": element.get("type", ""),
        "name": tags.get("name", tags.get("name:en", "")),
        "name_hi": tags.get("name:hi", ""),
        "tourism": tags.get("tourism", ""),
        "historic": tags.get("historic", ""),
        "amenity": tags.get("amenity", ""),
        "lat": lat,
        "lon": lon,
        "city": tags.get("addr:city", ""),
        "description": tags.get("description", tags.get("wikipedia", "")),
        "opening_hours": tags.get("opening_hours", ""),
        "fee": tags.get("fee", ""),
    }


def save_osm_csv(attractions: list[dict[str, Any]], filename: str) -> None:
    """
    OSM आकर्षण डेटा को CSV फ़ाइल में सहेजता है।
    Saves the list of parsed OSM attraction dicts to a CSV file.
    """
    if not attractions:
        print("[WARN] No OSM attractions to save.")
        return

    fieldnames = list(attractions[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(attractions)
    print(f"[INFO] Saved {len(attractions)} OSM records → {filename}")


if __name__ == "__main__":
    import os

    # राजस्थान के पर्यटन स्थल / Rajasthan tourist spots
    raw_spots = get_rajasthan_tourist_spots()
    parsed = [parse_osm_attraction(e) for e in raw_spots]
    output_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "osm_attractions.csv"
    )
    save_osm_csv(parsed, output_path)
    time.sleep(1)
