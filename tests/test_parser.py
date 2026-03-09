"""
tests/test_parser.py — Unit tests for the NLU parser (src/nlu/parser.py)
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.nlu.parser import (
    extract_budget,
    extract_duration,
    extract_cities,
    extract_party_size,
    extract_preference,
    parse_travel_request,
    FOOD_KEYWORDS,
    HOTEL_KEYWORDS,
)


# ───────────────────────────── Budget ─────────────────────────────

def test_extract_budget_rupee_symbol():
    assert extract_budget("budget ₹15000") == 15000


def test_extract_budget_rs():
    assert extract_budget("rs 8000 for the trip") == 8000


def test_extract_budget_inr():
    assert extract_budget("inr 20000 trip") == 20000


def test_extract_budget_rupees_word():
    assert extract_budget("10000 rupees") == 10000


def test_extract_budget_none():
    assert extract_budget("no money mentioned here") is None


# ───────────────────────────── Duration ───────────────────────────

def test_extract_duration_days():
    assert extract_duration("5 days trip") == 5


def test_extract_duration_nights():
    assert extract_duration("3 nights in jaipur") == 3


def test_extract_duration_word():
    assert extract_duration("seven days") == 7


def test_extract_duration_none():
    assert extract_duration("no duration here") is None


# ───────────────────────────── Cities ─────────────────────────────

def test_extract_cities_single():
    cities = extract_cities("I want to visit jaipur")
    assert "Jaipur" in cities


def test_extract_cities_multiple():
    cities = extract_cities("trip to jaipur and udaipur")
    assert "Jaipur" in cities
    assert "Udaipur" in cities


def test_extract_cities_none():
    cities = extract_cities("I want to travel somewhere nice")
    assert cities == []


# ───────────────────────────── Party Size ─────────────────────────

def test_extract_party_size_people():
    assert extract_party_size("3 people") == 3


def test_extract_party_size_solo():
    assert extract_party_size("solo trip") == 1


def test_extract_party_size_default():
    assert extract_party_size("just a normal trip") == 1


def test_extract_party_size_me_and_friend():
    assert extract_party_size("me and my friend") == 2


# ───────────────────────────── Food Preference ────────────────────

def test_food_preference_veg():
    pref = extract_preference("I am vegetarian", FOOD_KEYWORDS, "veg")
    assert pref == "veg"


def test_food_preference_non_veg():
    pref = extract_preference("I love chicken and mutton", FOOD_KEYWORDS, "veg")
    assert pref == "non-veg"


def test_food_preference_default():
    pref = extract_preference("no food preference", FOOD_KEYWORDS, "veg")
    assert pref == "veg"


# ───────────────────────────── Complete Parse ─────────────────────

def test_complete_parse_basic():
    msg = "Plan a 5-day trip to Jaipur for 2 people with budget ₹15000"
    result = parse_travel_request(msg)
    assert result["budget_inr"] == 15000
    assert result["duration_days"] == 5
    assert "Jaipur" in result["cities"]
    assert result["party_size"] == 2


def test_complete_parse_solo():
    msg = "Solo trip to Udaipur, 3 days, Rs 8000, vegetarian"
    result = parse_travel_request(msg)
    assert result["budget_inr"] == 8000
    assert result["duration_days"] == 3
    assert "Udaipur" in result["cities"]
    assert result["food_preference"] == "veg"
