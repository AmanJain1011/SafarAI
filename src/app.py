"""
app.py — SafarAI Streamlit Chat Interface
राजस्थान यात्रा बजट प्लानर का मुख्य UI।
Main Streamlit chat UI for SafarAI — Rajasthan Travel Budget Planner.
"""

import streamlit as st

from src.nlu.parser import parse_travel_request
from src.optimizer.engine import BudgetOptimizer, TravelConstraints, format_itinerary
from src.fraud.detector import FraudDetector

# ─────────────────────────────────────────────
# Page config / पेज सेटअप
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SafarAI — Rajasthan Travel Planner",
    page_icon="🏜️",
    layout="centered",
)

st.title("🏜️ SafarAI — Rajasthan Travel Planner")
st.caption("Budget travel, smartly planned 🏜️ | बजट यात्रा, स्मार्ट तरीके से")


# ─────────────────────────────────────────────
# Cached resource loaders
# ─────────────────────────────────────────────

@st.cache_resource
def get_optimizer() -> BudgetOptimizer:
    """Optimizer को cache करके load करता है। / Loads and caches the BudgetOptimizer."""
    return BudgetOptimizer()


@st.cache_resource
def get_fraud_detector() -> FraudDetector:
    """FraudDetector को cache करके load करता है। / Loads and caches the FraudDetector."""
    detector = FraudDetector()
    optimizer = get_optimizer()
    if not optimizer.hotels_df.empty:
        detector.fit_price_model(optimizer.hotels_df)
    return detector


# ─────────────────────────────────────────────
# Chat history / चैट इतिहास
# ─────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "🙏 नमस्ते! मैं SafarAI हूँ — आपका राजस्थान यात्रा बजट सहायक।\n\n"
                "आप मुझे बताएं: कहाँ जाना है, कितने दिन, कितना बजट, और कितने लोग?\n\n"
                "_Example: Plan a 5-day trip to Jaipur for 2 people with budget ₹15000_"
            ),
        }
    ]

# Render existing messages / पुराने संदेश दिखाएं
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ─────────────────────────────────────────────
# User input / उपयोगकर्ता इनपुट
# ─────────────────────────────────────────────

user_input = st.chat_input("अपनी यात्रा योजना बताएं… / Describe your trip…")

if user_input:
    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # ── Pipeline: parse → constraints → optimize → fraud check → format ──
    with st.chat_message("assistant"):
        with st.spinner("✈️ Planning your trip…"):
            try:
                # 1. NLU Parsing / भाषा विश्लेषण
                parsed = parse_travel_request(user_input)

                # 2. Validate budget / बजट जाँच
                if not parsed.get("budget_inr"):
                    response = (
                        "❓ मुझे बजट नहीं मिला। कृपया अपना बजट बताएं।\n\n"
                        "_Example: ₹15000 budget for 5 days in Jaipur_"
                    )
                    st.markdown(response)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response}
                    )
                    st.stop()

                # 3. Build constraints / सीमाएँ बनाएं
                constraints = TravelConstraints(
                    total_budget=float(parsed["budget_inr"]),
                    duration_days=int(parsed.get("duration_days") or 3),
                    party_size=int(parsed.get("party_size") or 1),
                    cities=parsed.get("cities") or ["Jaipur"],
                    preferences={
                        "hotel": parsed.get("hotel_preference"),
                        "food": parsed.get("food_preference"),
                        "travel_style": parsed.get("travel_style"),
                    },
                )

                # 4. Optimize / अनुकूलन
                optimizer = get_optimizer()
                itinerary = optimizer.optimize(constraints)

                # 5. Fraud check on recommended hotel / धोखाधड़ी जाँच
                fraud_detector = get_fraud_detector()
                fraud_warnings: list[str] = []
                for day in itinerary.days:
                    hotel = day.hotel
                    check = fraud_detector.check_listing(hotel)
                    if check["risk_score"] >= 0.3:
                        fraud_warnings.append(
                            f"⚠️ Day {day.day_number} hotel **{hotel.get('name', '?')}** "
                            f"— Fraud risk: {check['risk_label']}"
                        )

                # 6. Format itinerary / itinerary format करें
                response = format_itinerary(itinerary, constraints.party_size)

                if fraud_warnings:
                    response += "\n\n### 🔍 Fraud Risk Alerts\n" + "\n".join(
                        fraud_warnings
                    )

                st.markdown(response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )

            except Exception as exc:
                error_msg = (
                    f"😕 कुछ गड़बड़ हो गई। कृपया दोबारा कोशिश करें।\n\n"
                    f"_Error: {exc}_"
                )
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )
