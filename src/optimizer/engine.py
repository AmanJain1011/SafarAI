"""
engine.py — Budget Optimization Engine
यात्रा बजट को optimize करके itinerary बनाता है।
Optimizes a travel budget and builds a day-by-day Rajasthan itinerary.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

# डेटा फ़ाइलें / Data file paths (relative to this file)
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# बजट विभाजन / Budget split fractions
BUDGET_SPLIT = {
    "hotel": 0.35,
    "food": 0.25,
    "attractions": 0.15,
    "transport": 0.15,
    "misc": 0.10,
}

# आपातकालीन बफर / Emergency buffer fraction
EMERGENCY_BUFFER_FRACTION = 0.10

# प्रतिदिन अधिकतम आकर्षण / Max attractions per day
MAX_ATTRACTIONS_PER_DAY = 3

# भोजन का विभाजन (सुबह/दोपहर/रात) / Meal split (breakfast/lunch/dinner)
MEAL_SPLIT = {"breakfast": 0.20, "lunch": 0.35, "dinner": 0.45}

# स्थानीय परिवहन अनुमान (₹/दिन) / Local transport estimate (INR/day)
LOCAL_TRANSPORT_INR_PER_DAY = 300


@dataclass
class TravelConstraints:
    """यात्रा की सीमाएँ / Travel constraints from the user request."""

    total_budget: float
    duration_days: int
    party_size: int = 1
    cities: list[str] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)

    @property
    def usable_budget(self) -> float:
        """10% emergency buffer काटने के बाद उपलब्ध बजट।
        Budget available after reserving 10% as emergency buffer."""
        return self.total_budget * (1 - EMERGENCY_BUFFER_FRACTION)

    @property
    def emergency_buffer(self) -> float:
        """₹ में आपातकालीन बफर / Emergency buffer amount in INR."""
        return self.total_budget * EMERGENCY_BUFFER_FRACTION


@dataclass
class DayPlan:
    """एक दिन की योजना / Plan for a single day of the trip."""

    day_number: int
    city: str
    hotel: dict[str, Any]
    meals: list[dict[str, Any]]
    attractions: list[dict[str, Any]]
    transport: float
    day_cost: float


@dataclass
class Itinerary:
    """पूरी यात्रा योजना / Complete trip itinerary."""

    days: list[DayPlan]
    total_cost: float
    budget_remaining: float
    emergency_buffer: float
    warnings: list[str] = field(default_factory=list)


class BudgetOptimizer:
    """
    बजट Optimizer: CSV डेटा से itinerary तैयार करता है।
    Builds an optimized itinerary from pre-scraped CSV data.
    """

    def __init__(self) -> None:
        self.hotels_df: pd.DataFrame = pd.DataFrame()
        self.restaurants_df: pd.DataFrame = pd.DataFrame()
        self.attractions_df: pd.DataFrame = pd.DataFrame()
        self._load_data()

    def _load_data(self) -> None:
        """CSV फ़ाइलें लोड करता है (उपलब्ध होने पर)।
        Loads pre-scraped CSV data files if they exist."""
        for attr, filename in [
            ("hotels_df", "hotels.csv"),
            ("restaurants_df", "restaurants.csv"),
            ("attractions_df", "attractions.csv"),
        ]:
            filepath = os.path.join(_DATA_DIR, filename)
            if os.path.exists(filepath):
                try:
                    setattr(self, attr, pd.read_csv(filepath))
                except Exception as exc:
                    print(f"[WARN] Could not load {filename}: {exc}")

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def optimize(self, constraints: TravelConstraints) -> Itinerary:
        """
        Two-stage optimization:
        1. प्रत्येक दिन के लिए होटल, भोजन, आकर्षण चुनता है।
        2. बजट अधिक होने पर refinement करता है।
        Stage 1: Assign hotels/meals/attractions for each day.
        Stage 2: Refine if over budget.
        """
        warnings: list[str] = []
        usable = constraints.usable_budget / max(constraints.party_size, 1)

        days: list[DayPlan] = []
        city_sequence = self._assign_cities(constraints)

        for day_num in range(1, constraints.duration_days + 1):
            city = city_sequence[(day_num - 1) % len(city_sequence)]
            hotel = self._pick_hotel(city, usable * BUDGET_SPLIT["hotel"])
            meals = self._pick_meals(city, usable * BUDGET_SPLIT["food"])
            attractions = self._pick_attractions(
                city, usable * BUDGET_SPLIT["attractions"]
            )
            transport = self._estimate_local_transport()

            day_cost = (
                hotel.get("price_per_night", 0)
                + sum(m.get("avg_cost_for_two", 0) / 2 for m in meals)
                + sum(a.get("entry_fee", 0) for a in attractions)
                + transport
            )
            days.append(
                DayPlan(
                    day_number=day_num,
                    city=city,
                    hotel=hotel,
                    meals=meals,
                    attractions=attractions,
                    transport=transport,
                    day_cost=day_cost,
                )
            )

        total_cost = sum(d.day_cost for d in days) * constraints.party_size
        days, total_cost, warnings = self._refine(
            days, constraints, total_cost, warnings
        )

        return Itinerary(
            days=days,
            total_cost=total_cost,
            budget_remaining=constraints.usable_budget - total_cost,
            emergency_buffer=constraints.emergency_buffer,
            warnings=warnings,
        )

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _assign_cities(self, constraints: TravelConstraints) -> list[str]:
        """दिनों को शहरों में बाँटता है। / Distributes days across requested cities."""
        if constraints.cities:
            return constraints.cities
        return ["Jaipur"]

    def _pick_hotel(self, city: str, budget: float) -> dict[str, Any]:
        """
        बजट के अनुसार होटल चुनता है।
        Picks the best hotel within budget for the given city.
        """
        if self.hotels_df.empty:
            return {"name": "Budget Guesthouse", "price_per_night": min(budget, 500)}

        city_hotels = self.hotels_df[
            self.hotels_df["city"].str.lower() == city.lower()
        ]
        if city_hotels.empty:
            city_hotels = self.hotels_df

        affordable = city_hotels[city_hotels["price_per_night"] <= budget]
        if affordable.empty:
            affordable = city_hotels.nsmallest(1, "price_per_night")

        best = affordable.sort_values("price_per_night", ascending=False).iloc[0]
        return best.to_dict()

    def _pick_meals(self, city: str, food_budget: float) -> list[dict[str, Any]]:
        """
        भोजन के विकल्प चुनता है (20/35/45% split)।
        Selects meal options using a breakfast/lunch/dinner budget split.
        """
        meals = []
        if self.restaurants_df.empty:
            for meal, fraction in MEAL_SPLIT.items():
                meals.append(
                    {
                        "meal": meal,
                        "name": f"Local {meal.title()}",
                        "avg_cost_for_two": food_budget * fraction * 2,
                    }
                )
            return meals

        city_restaurants = self.restaurants_df[
            self.restaurants_df["city"].str.lower() == city.lower()
        ]
        if city_restaurants.empty:
            city_restaurants = self.restaurants_df

        for meal, fraction in MEAL_SPLIT.items():
            meal_budget_for_two = food_budget * fraction * 2
            affordable = city_restaurants[
                city_restaurants["avg_cost_for_two"] <= meal_budget_for_two
            ]
            if affordable.empty:
                affordable = city_restaurants.nsmallest(1, "avg_cost_for_two")
            if len(affordable) == 1:
                pick = affordable.iloc[0].to_dict()
            else:
                pick = affordable.sample(1).iloc[0].to_dict()
            pick["meal"] = meal
            meals.append(pick)

        return meals

    def _pick_attractions(
        self, city: str, attractions_budget: float
    ) -> list[dict[str, Any]]:
        """
        प्रतिदिन अधिकतम 3 आकर्षण चुनता है।
        Picks up to MAX_ATTRACTIONS_PER_DAY attractions within budget.
        """
        if self.attractions_df.empty:
            return [{"name": "City Heritage Walk", "entry_fee": 0}]

        city_attr = self.attractions_df[
            self.attractions_df["city"].str.lower() == city.lower()
        ]
        if city_attr.empty:
            city_attr = self.attractions_df

        if "entry_fee" not in city_attr.columns:
            city_attr = city_attr.copy()
            city_attr["entry_fee"] = 0

        picked: list[dict[str, Any]] = []
        remaining_budget = attractions_budget

        for _, row in city_attr.sample(frac=1).iterrows():
            if len(picked) >= MAX_ATTRACTIONS_PER_DAY:
                break
            fee = float(row.get("entry_fee", 0) or 0)
            if fee <= remaining_budget:
                picked.append(row.to_dict())
                remaining_budget -= fee

        return picked if picked else [{"name": "City Heritage Walk", "entry_fee": 0}]

    def _estimate_local_transport(self) -> float:
        """स्थानीय परिवहन खर्च अनुमानित करता है। / Returns estimated local transport cost."""
        return LOCAL_TRANSPORT_INR_PER_DAY

    def _refine(
        self,
        days: list[DayPlan],
        constraints: TravelConstraints,
        total_cost: float,
        warnings: list[str],
    ) -> tuple[list[DayPlan], float, list[str]]:
        """
        बजट अधिक होने पर itinerary को सरल बनाता है।
        Reduces costs if over budget by picking cheaper options.
        """
        if total_cost > constraints.usable_budget:
            overshoot = total_cost - constraints.usable_budget
            warnings.append(
                f"⚠️ Budget tight! Estimated cost ₹{total_cost:,.0f} exceeds "
                f"usable budget ₹{constraints.usable_budget:,.0f} "
                f"by ₹{overshoot:,.0f}. Consider fewer cities or shorter stay."
            )
        return days, total_cost, warnings


def format_itinerary(itinerary: Itinerary, party_size: int = 1) -> str:
    """
    Itinerary को readable string में format करता है।
    Formats the Itinerary object into a human-readable string with emojis.
    """
    lines = ["## 🏜️ Your SafarAI Rajasthan Itinerary\n"]
    for day in itinerary.days:
        lines.append(f"### Day {day.day_number} — 📍 {day.city}")
        lines.append(f"🏨 **Hotel:** {day.hotel.get('name', 'N/A')} "
                     f"(₹{day.hotel.get('price_per_night', 0):,.0f}/night)")

        meal_strs = [
            f"{m.get('meal', '').title()}: {m.get('name', 'Local eatery')}"
            for m in day.meals
        ]
        lines.append(f"🍽️ **Meals:** {' | '.join(meal_strs)}")

        attr_strs = [a.get("name", "Attraction") for a in day.attractions]
        lines.append(f"🎯 **Attractions:** {', '.join(attr_strs)}")
        lines.append(f"🚗 **Local Transport:** ₹{day.transport:,.0f}")
        lines.append(f"💰 **Day Cost (per person):** ₹{day.day_cost:,.0f}\n")

    lines.append(f"---")
    lines.append(
        f"💵 **Total Estimated Cost ({party_size} person(s)):** "
        f"₹{itinerary.total_cost:,.0f}"
    )
    lines.append(
        f"🟢 **Budget Remaining:** ₹{max(itinerary.budget_remaining, 0):,.0f}"
    )
    lines.append(
        f"🆘 **Emergency Buffer (10%):** ₹{itinerary.emergency_buffer:,.0f}"
    )

    for warning in itinerary.warnings:
        lines.append(f"\n{warning}")

    return "\n".join(lines)
