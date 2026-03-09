"""
parser.py — NLU Parser using spaCy + regex
यात्रा अनुरोध को structured dict में बदलता है।
Parses natural-language travel requests into structured dicts using spaCy + regex.
"""

import re
import spacy

# spaCy मॉडल लोड करें (lazy load) / Load spaCy model lazily
_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback: blank English model if en_core_web_sm not installed
            _nlp = spacy.blank("en")
    return _nlp


# राजस्थान के समर्थित शहर / Supported cities in Rajasthan
SUPPORTED_CITIES = {
    "jaipur", "jodhpur", "udaipur", "jaisalmer", "pushkar",
    "ajmer", "bikaner", "mount abu", "ranthambore", "bharatpur",
    "chittorgarh", "kota", "alwar", "sikar", "nagaur",
}

# होटल पसंद के कीवर्ड / Hotel preference keywords
HOTEL_KEYWORDS = {
    "budget": ["cheap", "budget", "affordable", "hostel", "backpacker", "sasta", "किफायती"],
    "mid-range": ["mid", "decent", "comfortable", "standard", "moderate"],
    "premium": ["premium", "nice", "good", "3-star", "three-star"],
    "luxury": ["luxury", "5-star", "five-star", "lavish", "royal", "palace"],
}

# खाने की पसंद के कीवर्ड / Food preference keywords
FOOD_KEYWORDS = {
    "veg": ["veg", "vegetarian", "veggie", "no meat", "shudh", "शाकाहारी"],
    "non-veg": ["non-veg", "non veg", "meat", "chicken", "mutton", "maansahari", "मांसाहारी"],
    "street_food": ["street food", "local food", "chaat", "dhaba", "roadside"],
}

# यात्रा शैली / Travel style keywords
TRAVEL_STYLE = {
    "adventure": ["adventure", "trekking", "hiking", "thrill", "outdoor"],
    "cultural": ["culture", "heritage", "history", "museum", "fort", "temple"],
    "relaxation": ["relax", "rest", "peaceful", "calm", "leisure", "slow"],
    "photography": ["photo", "photography", "instagram", "scenic", "views"],
    "spiritual": ["spiritual", "pilgrimage", "temple", "mandir", "dargah", "teerth"],
}


def parse_travel_request(user_message: str) -> dict:
    """
    यात्रा अनुरोध को parse करके structured dict लौटाता है।
    Parses a travel request message into a structured dict with budget, cities, etc.
    """
    text = user_message.lower().strip()
    return {
        "raw_message": user_message,
        "budget_inr": extract_budget(text),
        "duration_days": extract_duration(text),
        "cities": extract_cities(text),
        "party_size": extract_party_size(text),
        "travel_style": extract_travel_style(text),
        "hotel_preference": extract_preference(text, HOTEL_KEYWORDS, "budget"),
        "food_preference": extract_preference(text, FOOD_KEYWORDS, "veg"),
        "interests": extract_interests(text),
    }


def extract_budget(text: str) -> int | None:
    """
    Text से बजट निकालता है (₹, Rs, INR support)।
    Extracts the travel budget in INR from the text.
    Returns the integer value, or None if not found.
    """
    # Patterns: ₹10000, Rs 10,000, 10000 rupees, INR 10000, 10k
    patterns = [
        r"(?:₹|rs\.?|inr)\s*([0-9,]+(?:\.[0-9]+)?)\s*(?:k\b)?",
        r"([0-9,]+(?:\.[0-9]+)?)\s*(?:k\b)?\s*(?:rupees?|₹|rs\.?|inr)",
        r"budget\s+(?:of|is|=)?\s*(?:₹|rs\.?|inr)?\s*([0-9,]+(?:\.[0-9]+)?)\s*(?:k\b)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "")
            value = float(raw)
            # Handle '10k' style — but the k is captured outside group; check context
            if re.search(
                r"(?:₹|rs\.?|inr)\s*" + re.escape(match.group(1)) + r"\s*k\b",
                text,
                re.IGNORECASE,
            ) or re.search(
                re.escape(match.group(1)) + r"\s*k\b\s*(?:rupees?|₹|rs\.?|inr)?",
                text,
                re.IGNORECASE,
            ):
                value *= 1000
            return int(value)

    # Handle plain 'Xk' like "15k budget"
    match = re.search(r"([0-9]+)\s*k\b.*?budget|budget.*?([0-9]+)\s*k\b", text, re.IGNORECASE)
    if match:
        raw = match.group(1) or match.group(2)
        return int(raw) * 1000

    return None


def extract_duration(text: str) -> int | None:
    """
    Text से यात्रा की अवधि (दिन) निकालता है।
    Extracts trip duration in days from the text.
    """
    patterns = [
        r"([0-9]+)[- ]?(?:days?|din|रात|nights?)",
        r"([0-9]+)[- ]?(?:day|night)\s*trip",
        r"(\w+)\s*days?",
    ]
    word_to_num = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    }
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1).lower()
            if raw.isdigit():
                return int(raw)
            if raw in word_to_num:
                return word_to_num[raw]

    return None


def extract_cities(text: str) -> list[str]:
    """
    Text से राजस्थान के शहरों के नाम निकालता है।
    Extracts mentioned Rajasthan city names from the text.
    """
    found = []
    # Check multi-word cities first (e.g. "mount abu")
    for city in sorted(SUPPORTED_CITIES, key=len, reverse=True):
        if re.search(r"\b" + re.escape(city) + r"\b", text, re.IGNORECASE):
            if city not in found:
                found.append(city.title())
    return found


def extract_party_size(text: str) -> int:
    """
    Text से यात्रियों की संख्या निकालता है।
    Extracts the number of travellers from the text. Defaults to 1.
    """
    patterns = [
        r"([0-9]+)\s*(?:people|person|persons|travellers?|friends?|log|लोग)",
        r"(?:me|main|myself)\s+and\s+([0-9]+)",
        r"group\s+of\s+([0-9]+)",
        r"family\s+of\s+([0-9]+)",
        r"([0-9]+)\s*(?:adults?|members?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

    # "me and my friend" → 2
    if re.search(r"\bme and my\b", text, re.IGNORECASE):
        return 2
    # "solo" → 1
    if re.search(r"\bsolo\b", text, re.IGNORECASE):
        return 1

    return 1


def extract_travel_style(text: str) -> list[str]:
    """
    Text से यात्रा की शैली निकालता है।
    Extracts travel style tags from the text.
    """
    styles = []
    for style, keywords in TRAVEL_STYLE.items():
        if any(kw in text for kw in keywords):
            styles.append(style)
    return styles if styles else ["cultural"]


def extract_preference(text: str, keyword_map: dict, default: str) -> str:
    """
    Keyword map के आधार पर preference निकालता है।
    Extracts a preference (hotel type, food type) based on keyword matching.
    """
    for preference, keywords in keyword_map.items():
        if any(kw in text for kw in keywords):
            return preference
    return default


def extract_interests(text: str) -> list[str]:
    """
    Text से रुचि क्षेत्र निकालता है।
    Extracts interest tags (forts, wildlife, food, etc.) from the text.
    """
    interest_keywords = {
        "forts": ["fort", "kila", "qila", "castle"],
        "wildlife": ["wildlife", "safari", "tiger", "jungle", "ranthambore"],
        "food": ["food", "cuisine", "eat", "restaurant", "khana"],
        "shopping": ["shopping", "market", "bazaar", "handicraft", "textile"],
        "temples": ["temple", "mandir", "shrine", "dargah", "mosque"],
        "lakes": ["lake", "jheel", "water", "boat"],
        "desert": ["desert", "sand dunes", "camel", "reti", "dunes"],
        "art": ["art", "painting", "miniature", "craft", "haveli"],
    }
    interests = []
    for interest, keywords in interest_keywords.items():
        if any(kw in text for kw in keywords):
            interests.append(interest)
    return interests


if __name__ == "__main__":
    # परीक्षण संदेश / Test messages
    test_messages = [
        "Plan a 5-day trip to Jaipur and Jodhpur for 2 people with budget ₹15000",
        "I want to visit Udaipur solo, budget Rs 8000, 3 days, vegetarian food only",
        "Rajasthan trip for family of 4, heritage and culture, 7 days, budget 40k",
        "Jaisalmer desert trip with friends, adventure, 4 days, 3 people, ₹12000",
    ]
    for msg in test_messages:
        result = parse_travel_request(msg)
        print(f"\nInput: {msg}")
        print(f"Parsed: {result}")
