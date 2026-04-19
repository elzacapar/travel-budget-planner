# ✈️ Travel Budget Planner

**Is my travel budget realistic?** Answer that question in under 30 seconds.

🔗 **[Live app → travel-budget-planner.streamlit.app](https://travel-budget-planner.streamlit.app/)**

---

## What it does

Most travel planning tools make you open 5 separate tabs to estimate a trip cost. This app aggregates everything into one structured input → one cost breakdown → one clear verdict.

Enter your destination, trip length, number of people, and budget. Select your travel style per category independently — budget food with mid-range accommodation, for example — and the app tells you whether your budget is comfortable, tight, or insufficient, with a day-by-day surplus or deficit.

---

## The differentiator

Every existing free tool gives you one travel style at a time — budget *or* mid-range *or* comfort. This app lets you **mix tiers independently per category**, which is how real travelers actually plan:

| Category | Budget | Mid | Comfort |
|---|---|---|---|
| 🏨 Accommodation | Hostel / guesthouse | 3-star hotel / Airbnb | 4-star hotel |
| 🍜 Food | Street food / self-catering | Mix of mid-range restaurants | Restaurants + nicer dinners |
| 🚌 Transport | Public transit only | Transit + occasional taxi | Taxis / rideshare regularly |
| 🎭 Activities | Free sights only | Some paid attractions | Tours + paid experiences daily |

No other free travel budget tool does this.

---

## Features

- **100 cities** across 8 regions — Western & Eastern Europe, Southeast Asia, East Asia, Middle East, Americas, South Asia, Africa & Oceania
- **Per-category tier mixing** — independent budget/mid/comfort selection per category
- **Verdict banner** — Comfortable ✅ / Tight but doable ⚠️ / You'll run out by day X ❌
- **12% contingency buffer** automatically added to all estimates
- **Live currency conversion** — 150+ currencies via exchangerate-api.com
- **AI budget advisor** — powered by Groq (Llama 3.1), generates destination-specific saving tips and cheaper alternatives if budget is tight
- **Interactive Plotly chart** — estimated cost vs. budget per category

---

## Tech stack

| Layer | Tool |
|---|---|
| App framework | Streamlit |
| Data wrangling | pandas |
| Visualisations | Plotly |
| Currency conversion | exchangerate-api.com (free tier) |
| AI advisor | Groq API — Llama 3.1 8B |
| Deployment | Streamlit Community Cloud |
| Data source | Numbeo (crowdsourced traveler averages) |

---

## Project structure

```
travel-budget-planner/
├── app.py                  # Streamlit UI
├── cost_calculator.py      # Cost estimation and verdict logic
├── llm_advisor.py          # AI budget advisor (Groq)
├── numbeo_tiers_usd.csv    # City cost data by tier
├── requirements.txt
└── .env                    # API keys (not committed)
```

---

## Run locally

```bash
git clone https://github.com/elzacapar/travel-budget-planner
cd travel-budget-planner
pip install -r requirements.txt
```

Create a `.env` file:
```
GROQ_API_KEY=your_key
EXCHANGERATE_API_KEY=your_key
```

```bash
streamlit run app.py
```

---

## Data & limitations

- Estimates are based on crowdsourced traveler averages from [Numbeo](https://www.numbeo.com) — actual costs vary
- Data is a periodic snapshot — prices change with inflation and seasonality
- Accommodation estimates are approximate — verify on Booking.com for specific dates
- Flights are excluded (too dynamic for reliable estimates)
- Luxury tier excluded (insufficient data quality)

---

## Origin story

Built from personal experience — planning frequent trips across Southeast Asia and Europe on a budget. The frustration of opening 5 separate tabs to estimate a trip was the problem. This app solves it in under 30 seconds.

---

## Author

**Elza Capar** — Data Science student at EC Utbildning, Sweden.

[GitHub](https://github.com/elzacapar)
