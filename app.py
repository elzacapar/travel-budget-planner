import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from dotenv import load_dotenv
import os

from cost_calculator import load_tier_data, estimate_trip_cost, get_verdict

load_dotenv()

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

st.set_page_config(
    page_title="Travel Budget Planner",
    page_icon="✈️",
    layout="centered",
)

TIER_OPTIONS = ["Budget", "Mid", "Comfort"]
TIER_MAP     = {"Budget": "budget", "Mid": "mid", "Comfort": "comfort"}
CONTINGENCY  = 0.12

REGIONS = {
    "Western Europe": [
        "Paris", "London", "Amsterdam", "Barcelona", "Madrid", "Rome", "Milan",
        "Berlin", "Vienna", "Lisbon", "Athens", "Dublin", "Brussels", "Zurich",
        "Geneva", "Copenhagen", "Stockholm", "Oslo", "Helsinki", "Porto"
    ],
    "Eastern Europe": [
        "Prague", "Budapest", "Warsaw", "Krakow", "Bucharest", "Sofia",
        "Belgrade", "Zagreb", "Tallinn", "Riga", "Vilnius", "Ljubljana"
    ],
    "Southeast Asia": [
        "Bangkok", "Kuala Lumpur", "Singapore", "Bali", "Ho Chi Minh City",
        "Hanoi", "Jakarta", "Manila", "Chiang Mai", "Phuket", "Phnom Penh",
        "Siem Reap"
    ],
    "East Asia": [
        "Tokyo", "Hong Kong", "Seoul", "Osaka", "Macau", "Beijing",
        "Shanghai", "Taipei", "Kyoto"
    ],
    "Middle East & Turkey": [
        "Istanbul", "Dubai", "Antalya", "Abu Dhabi", "Tel Aviv", "Amman", "Doha"
    ],
    "Americas": [
        "New York", "Los Angeles", "Mexico City", "Buenos Aires", "Rio de Janeiro",
        "Miami", "Chicago", "San Francisco", "Cancun", "Sao Paulo", "Bogota",
        "Lima", "Toronto", "Vancouver", "Montreal"
    ],
    "South Asia": [
        "Mumbai", "Delhi", "Bangalore", "Colombo", "Kathmandu", "Dhaka"
    ],
    "Africa & Oceania": [
        "Sydney", "Melbourne", "Auckland", "Cape Town", "Johannesburg",
        "Nairobi", "Marrakech", "Cairo", "Casablanca"
    ],
}

VERDICT_STYLE = {
    "Comfortable":      {"color": "#2ecc71", "icon": "✅"},
    "Tight but doable": {"color": "#f39c12", "icon": "⚠️"},
}

# --------------------------------------------------------------------------- #
# Data loaders (cached)
# --------------------------------------------------------------------------- #

@st.cache_data
def get_data():
    return load_tier_data("data/numbeo_tiers_usd.csv")


@st.cache_data(ttl=3600)
def get_exchange_rates():
    key = os.getenv("EXCHANGERATE_API_KEY")
    r = requests.get(f"https://v6.exchangerate-api.com/v6/{key}/latest/USD")
    data = r.json()
    if data.get("result") != "success":
        st.warning("Could not fetch exchange rates — displaying in USD.")
        return {"USD": 1.0}
    return data["conversion_rates"]


df         = get_data()
cities     = sorted(df.index.tolist())
rates      = get_exchange_rates()
currencies = sorted(rates.keys())

# --------------------------------------------------------------------------- #
# Currency helpers
# --------------------------------------------------------------------------- #

def fx(usd_amount: float, rate: float) -> float:
    return usd_amount * rate


def fmt(usd_amount: float, currency: str, rate: float) -> str:
    return f"{currency} {fx(usd_amount, rate):,.2f}"


# --------------------------------------------------------------------------- #
# Sidebar — inputs
# --------------------------------------------------------------------------- #

with st.sidebar:
    st.title("✈️ Trip Details")

    region = st.selectbox("Region", list(REGIONS.keys()))
    city   = st.selectbox("City", sorted(REGIONS[region]))
    days   = st.number_input("Number of days",   min_value=1,  max_value=365, value=7)
    people = st.number_input("Number of people", min_value=1,  max_value=20,  value=1)

    currency = st.selectbox("Currency", currencies, index=currencies.index("USD"))
    rate     = rates[currency]

    budget_local = st.number_input(
        f"Your total budget ({currency})",
        min_value=0.0, value=1000.0, step=50.0
    )
    budget_usd = budget_local / rate

    st.markdown("---")
    st.subheader("Travel style")
    st.caption("Select independently per category")

    acc_tier = st.selectbox("🏨 Accommodation", TIER_OPTIONS, index=1, help=(
        "**Budget** — Hostel dorm or cheap guesthouse\n\n"
        "**Mid** — 3-star hotel or Airbnb private room\n\n"
        "**Comfort** — 4-star hotel"
    ))
    food_tier = st.selectbox("🍜 Food", TIER_OPTIONS, index=1, help=(
        "**Budget** — Street food, self-catering, inexpensive restaurants\n\n"
        "**Mid** — Mix of mid-range restaurants\n\n"
        "**Comfort** — Restaurants daily with nicer dinners"
    ))
    trans_tier = st.selectbox("🚌 Transport", TIER_OPTIONS, index=0, help=(
        "**Budget** — Public transit only\n\n"
        "**Mid** — Public transit + occasional taxi or rideshare\n\n"
        "**Comfort** — Taxis and rideshare regularly"
    ))
    ent_tier = st.selectbox("🎭 Activities", TIER_OPTIONS, index=0, help=(
        "**Budget** — Free sights only\n\n"
        "**Mid** — Some paid attractions and museums\n\n"
        "**Comfort** — Tours and paid experiences daily"
    ))

    calculate = st.button("Calculate", type="primary", use_container_width=True)

# --------------------------------------------------------------------------- #
# Main area
# --------------------------------------------------------------------------- #

st.title("Is my budget realistic?")
st.caption("Estimates based on traveler averages (Numbeo). Actual costs vary.")

if calculate:
    st.session_state["estimate"] = estimate_trip_cost(
        df, city, days, people,
        TIER_MAP[acc_tier], TIER_MAP[food_tier],
        TIER_MAP[trans_tier], TIER_MAP[ent_tier],
    )
    st.session_state["verdict"]  = get_verdict(budget_usd, st.session_state["estimate"])
    st.session_state["snapshot"] = dict(
        city=city, days=days, people=people, currency=currency, rate=rate,
        budget_usd=budget_usd, acc_tier=acc_tier, food_tier=food_tier,
        trans_tier=trans_tier, ent_tier=ent_tier,
    )

if "estimate" not in st.session_state:
    st.info("Fill in your trip details in the sidebar and press **Calculate**.")
    st.stop()

estimate = st.session_state["estimate"]
verdict  = st.session_state["verdict"]
snap     = st.session_state["snapshot"]

# use snapshot values below so advice matches the last calculation
city, days, people       = snap["city"], snap["days"], snap["people"]
currency, rate           = snap["currency"], snap["rate"]
budget_usd               = snap["budget_usd"]
acc_tier, food_tier      = snap["acc_tier"], snap["food_tier"]
trans_tier, ent_tier     = snap["trans_tier"], snap["ent_tier"]

# --------------------------------------------------------------------------- #
# Verdict banner
# --------------------------------------------------------------------------- #

vtext     = verdict["verdict"]
is_runout = vtext.startswith("You'll run out")

if is_runout:
    color, icon = "#e74c3c", "❌"
else:
    color = VERDICT_STYLE[vtext]["color"]
    icon  = VERDICT_STYLE[vtext]["icon"]

st.markdown(
    f"""
    <div style="background-color:{color}22; border-left: 5px solid {color};
                padding: 1rem 1.25rem; border-radius: 6px; margin-bottom: 1rem;">
        <span style="font-size:1.4rem; font-weight:700; color:{color};">
            {icon} {vtext}
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

surplus_usd = verdict["surplus_usd"]
daily_s_usd = verdict["daily_surplus_usd"]

if surplus_usd >= 0:
    st.markdown(
        f"You'd have **{fmt(surplus_usd, currency, rate)}** left over "
        f"(**{fmt(daily_s_usd, currency, rate)}/day** breathing room)."
    )
else:
    st.markdown(
        f"You're **{fmt(abs(surplus_usd), currency, rate)} short** of the estimated cost."
    )

# --------------------------------------------------------------------------- #
# Cost breakdown
# --------------------------------------------------------------------------- #

st.markdown("---")
st.subheader(f"📊 Cost breakdown — {city}")

daily       = estimate["daily_costs_per_person_usd"]
subtotal    = estimate["subtotal_usd"]
contingency = estimate["contingency_usd"]
total_est   = estimate["total_estimated_usd"]

col1, col2, col3 = st.columns(3)
col1.metric("Total estimated",   fmt(total_est,    currency, rate))
col2.metric("Your budget",       fmt(budget_usd,   currency, rate))
col3.metric("Surplus / Deficit", fmt(surplus_usd,  currency, rate))

st.markdown("#### Daily costs per person")
breakdown = {
    "Category": ["🏨 Accommodation", "🍜 Food", "🚌 Transport", "🎭 Activities"],
    "Tier":     [acc_tier, food_tier, trans_tier, ent_tier],
    "Per day":  [
        fmt(daily["accommodation"], currency, rate),
        fmt(daily["food"],          currency, rate),
        fmt(daily["transport"],     currency, rate),
        fmt(daily["entertainment"], currency, rate),
    ],
    "Trip total": [
        fmt(daily["accommodation"] * people * days, currency, rate),
        fmt(daily["food"]          * people * days, currency, rate),
        fmt(daily["transport"]     * people * days, currency, rate),
        fmt(daily["entertainment"] * people * days, currency, rate),
    ],
}
st.dataframe(pd.DataFrame(breakdown), hide_index=True, use_container_width=True)

st.caption(
    f"Subtotal: {fmt(subtotal, currency, rate)} · "
    f"12% contingency buffer: +{fmt(contingency, currency, rate)} · "
    f"**Total estimate: {fmt(total_est, currency, rate)}** · "
    "🏨 Accommodation estimates are approximate — verify on Booking.com for your dates."
)

# --------------------------------------------------------------------------- #
# Bar chart
# --------------------------------------------------------------------------- #

st.markdown("#### Budget vs. estimate")

cats = ["Accommodation", "Food", "Transport", "Activities"]
vals = [
    fx(daily["accommodation"] * people * days, rate),
    fx(daily["food"]          * people * days, rate),
    fx(daily["transport"]     * people * days, rate),
    fx(daily["entertainment"] * people * days, rate),
]
buffer_share = [v * CONTINGENCY for v in vals]

fig = go.Figure()
fig.add_trace(go.Bar(name="Estimated cost",        x=cats, y=vals,         marker_color="#4a90d9"))
fig.add_trace(go.Bar(name="12% buffer (included)", x=cats, y=buffer_share, marker_color="#a8c8f0"))
fig.add_hline(
    y=fx(budget_usd, rate) / len(cats),
    line_dash="dash", line_color="#2ecc71",
    annotation_text="Your budget (avg per category)",
    annotation_position="top right",
)
fig.update_layout(
    barmode="stack",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    yaxis_title=currency,
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    margin=dict(t=40, b=20),
    height=360,
)
st.plotly_chart(fig, use_container_width=True)

st.caption("✈️ Flights not included — prices are too dynamic for reliable estimates.")

# --------------------------------------------------------------------------- #
# LLM Budget Advisor
# --------------------------------------------------------------------------- #

st.markdown("---")
st.subheader("🤖 Budget Advisor")
st.caption("Powered by Claude. Personalised tips based on your trip breakdown.")

if st.button("Get personalised advice", type="secondary"):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY not set in your .env file.")
    else:
        from llm_advisor import build_context, get_advice

        ctx = build_context(
            city=city,
            days=days,
            people=people,
            tiers={
                "acc":       acc_tier,
                "food":      food_tier,
                "transport": trans_tier,
                "ent":       ent_tier,
            },
            estimate=estimate,
            verdict=verdict,
            currency=currency,
            rate=rate,
        )

        with st.spinner("Getting advice..."):
            try:
                advice = get_advice(ctx, api_key)
                st.markdown(advice)
            except Exception as e:
                st.error(f"API error: {e}")