# 🏜️ SafarAI — AI-Powered Rajasthan Travel Budget Planner

> **Budget travel, smartly planned 🏜️**

SafarAI is an intelligent travel-budget planner for Rajasthan, India. It combines natural-language understanding, real-time price data from multiple APIs, and a budget-optimization engine to generate personalised day-by-day itineraries — complete with fraud detection for hotel listings.

---

## ✨ Features

- 🗣️ **NLU Parser** — Understands Hindi + English travel requests (budget, cities, duration, party size, food preference)
- 📊 **Budget Optimizer** — Allocates budget across hotels, food, attractions, and transport using a two-stage optimization engine
- 🔍 **Fraud Detector** — Flags suspicious hotel listings using IsolationForest + rule-based checks
- 🗺️ **Multi-source Data** — OpenTripMap, Foursquare, Google Places, Overpass (OSM), Makcorps Hotels
- 💬 **Streamlit Chat UI** — Conversational interface with chat history

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| NLU | spaCy, regex |
| ML / Fraud | scikit-learn (IsolationForest) |
| Data | pandas, numpy |
| Scrapers | requests, geopy, beautifulsoup4 |
| UI | Streamlit |
| Config | python-dotenv |
| CI | GitHub Actions |

---

## 📁 Project Structure

```
SafarAI/
├── src/
│   ├── app.py                    # Streamlit chat interface
│   ├── nlu/
│   │   └── parser.py             # NLU travel request parser
│   ├── optimizer/
│   │   └── engine.py             # Budget optimization engine
│   ├── fraud/
│   │   └── detector.py           # Fraud detection (IsolationForest)
│   ├── scrapers/
│   │   ├── attractions_api.py    # OpenTripMap scraper
│   │   ├── restaurants_api.py    # Foursquare scraper
│   │   ├── hotels_api.py         # Makcorps hotel scraper
│   │   ├── osm_attractions.py    # Overpass API (no key needed)
│   │   └── google_places_api.py  # Google Places scraper
│   └── data/                     # Scraped CSVs (git-ignored)
├── tests/
│   └── test_parser.py            # NLU parser unit tests
├── .github/
│   └── workflows/
│       └── price_refresh.yml     # Weekly price refresh CI
├── requirements.txt
├── .env.example
└── CONTRIBUTING.md
```

---

## 🚀 Setup

### Prerequisites
- Python 3.11+
- API keys (see `.env.example`)

### Installation

```bash
git clone https://github.com/AmanJain1011/SafarAI.git
cd SafarAI

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm

cp .env.example .env          # Fill in your API keys
```

### Run the app

```bash
streamlit run src/app.py
```

### Run scrapers (collect data first)

```bash
python -m src.scrapers.osm_attractions      # No API key needed
python -m src.scrapers.attractions_api      # Requires OPENTRIPMAP_API_KEY
python -m src.scrapers.restaurants_api      # Requires FOURSQUARE_API_KEY
python -m src.scrapers.hotels_api           # Requires MAKCORPS_API_KEY (Jaipur only)
python -m src.scrapers.google_places_api    # Requires GOOGLE_PLACES_API_KEY (Jaipur only)
```

### Run tests

```bash
python -m pytest tests/ -v
```

---

## 🌿 Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable, production-ready |
| `aman-dev` | AmanJain1011's development branch |
| `yash-dev` | Yash12256's development branch |

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contribution guide.

---

## 👥 Contributors

| Contributor | GitHub |
|-------------|--------|
| Aman Jain | [@AmanJain1011](https://github.com/AmanJain1011) |
| Yash | [@Yash12256](https://github.com/Yash12256) |

---

## 📄 License

[MIT](LICENSE)
