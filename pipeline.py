"""
Full data pipeline: scrape Numbeo → clean → transform to tiers CSV
Run manually: python pipeline.py
Run automatically: GitHub Actions (monthly)
"""

import re
import time
import random
import requests
import pandas as pd
from bs4 import BeautifulSoup

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

CITIES = [
    "Paris", "London", "Amsterdam", "Barcelona", "Madrid", "Rome", "Milan",
    "Berlin", "Vienna", "Lisbon", "Athens", "Dublin", "Brussels", "Zurich",
    "Geneva", "Copenhagen", "Stockholm", "Oslo", "Helsinki", "Porto",
    "Prague", "Budapest", "Warsaw", "Krakow", "Bucharest", "Sofia",
    "Belgrade", "Zagreb", "Tallinn", "Riga", "Vilnius", "Ljubljana",
    "Bangkok", "Kuala Lumpur", "Singapore", "Bali", "Ho Chi Minh City",
    "Hanoi", "Jakarta", "Manila", "Chiang Mai", "Phuket", "Phnom Penh",
    "Siem Reap",
    "Tokyo", "Hong Kong", "Seoul", "Osaka", "Macau", "Beijing", "Shanghai",
    "Taipei", "Kyoto",
    "Istanbul", "Dubai", "Antalya", "Abu Dhabi", "Tel Aviv", "Amman", "Doha",
    "New York", "Los Angeles", "Mexico City", "Buenos Aires", "Rio de Janeiro",
    "Miami", "Chicago", "San Francisco", "Cancun", "Sao Paulo", "Bogota",
    "Lima", "Toronto", "Vancouver", "Montreal",
    "Mumbai", "Delhi", "Bangalore", "Colombo", "Kathmandu", "Dhaka",
    "Sydney", "Melbourne", "Auckland", "Cape Town", "Johannesburg", "Nairobi",
    "Marrakech", "Cairo", "Casablanca",
]

URL_OVERRIDES = {
    "Krakow": "Krakow-Cracow",
    "Macau": "Macao",
    "Bali": "Denpasar",
    "Siem Reap": "Siem-Reap",
    "Tel Aviv": "Tel-Aviv-Yafo",
    "Rio de Janeiro": "Rio-De-Janeiro",
    "Cairo": "Cairo-Egypt",
}

# Currency codes for each city (ISO 4217)
CITY_CURRENCY = {
    "Bali": "IDR", "Jakarta": "IDR",
    "Ho Chi Minh City": "VND", "Hanoi": "VND",
    "Bangkok": "THB", "Chiang Mai": "THB", "Phuket": "THB",
    "Kuala Lumpur": "MYR", "Singapore": "SGD", "Manila": "PHP",
    "Phnom Penh": "USD", "Siem Reap": "USD",
    "Tokyo": "JPY", "Osaka": "JPY", "Kyoto": "JPY",
    "Seoul": "KRW", "Beijing": "CNY", "Shanghai": "CNY",
    "Hong Kong": "HKD", "Macau": "MOP", "Taipei": "TWD",
    "Budapest": "HUF", "Warsaw": "PLN", "Krakow": "PLN",
    "Bucharest": "RON", "Sofia": "EUR", "Belgrade": "RSD",
    "Zagreb": "EUR", "Tallinn": "EUR", "Riga": "EUR",
    "Vilnius": "EUR", "Ljubljana": "EUR", "Prague": "CZK",
    "Paris": "EUR", "Amsterdam": "EUR", "Barcelona": "EUR",
    "Madrid": "EUR", "Rome": "EUR", "Milan": "EUR",
    "Berlin": "EUR", "Vienna": "EUR", "Athens": "EUR",
    "Brussels": "EUR", "Helsinki": "EUR", "Porto": "EUR",
    "Lisbon": "EUR", "Dublin": "EUR",
    "London": "GBP", "Zurich": "CHF", "Geneva": "CHF",
    "Copenhagen": "DKK", "Stockholm": "SEK", "Oslo": "NOK",
    "Istanbul": "TRY", "Antalya": "TRY", "Dubai": "AED",
    "Abu Dhabi": "AED", "Tel Aviv": "ILS", "Amman": "JOD", "Doha": "QAR",
    "New York": "USD", "Los Angeles": "USD", "Miami": "USD",
    "Chicago": "USD", "San Francisco": "USD", "Cancun": "MXN",
    "Mexico City": "MXN", "Buenos Aires": "USD",
    "Rio de Janeiro": "BRL", "Sao Paulo": "BRL",
    "Bogota": "COP", "Lima": "PEN",
    "Toronto": "CAD", "Vancouver": "CAD", "Montreal": "CAD",
    "Mumbai": "INR", "Delhi": "INR", "Bangalore": "INR",
    "Colombo": "LKR", "Kathmandu": "NPR", "Dhaka": "BDT",
    "Sydney": "AUD", "Melbourne": "AUD", "Auckland": "NZD",
    "Cape Town": "ZAR", "Johannesburg": "ZAR", "Nairobi": "KES",
    "Marrakech": "MAD", "Casablanca": "MAD", "Cairo": "EGP",
}

def fetch_currency_map(api_key: str) -> dict:
    """Fetch live USD rates and build city → rate map."""
    print("Fetching live exchange rates...")
    r = requests.get(f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD")
    rates = r.json()["conversion_rates"]
    currency_map = {city: rates[code] for city, code in CITY_CURRENCY.items()}
    print("Rates fetched.\n")
    return currency_map

CITY_REGION = {
    "Paris": "Western Europe", "London": "Western Europe", "Amsterdam": "Western Europe",
    "Barcelona": "Western Europe", "Madrid": "Western Europe", "Rome": "Western Europe",
    "Milan": "Western Europe", "Berlin": "Western Europe", "Vienna": "Western Europe",
    "Lisbon": "Western Europe", "Athens": "Western Europe", "Dublin": "Western Europe",
    "Brussels": "Western Europe", "Zurich": "Western Europe", "Geneva": "Western Europe",
    "Copenhagen": "Western Europe", "Stockholm": "Western Europe", "Oslo": "Western Europe",
    "Helsinki": "Western Europe", "Porto": "Western Europe",
    "Prague": "Eastern Europe", "Budapest": "Eastern Europe", "Warsaw": "Eastern Europe",
    "Krakow": "Eastern Europe", "Bucharest": "Eastern Europe", "Sofia": "Eastern Europe",
    "Belgrade": "Eastern Europe", "Zagreb": "Eastern Europe", "Tallinn": "Eastern Europe",
    "Riga": "Eastern Europe", "Vilnius": "Eastern Europe", "Ljubljana": "Eastern Europe",
    "Bangkok": "Southeast Asia", "Kuala Lumpur": "Southeast Asia", "Singapore": "Southeast Asia",
    "Bali": "Southeast Asia", "Ho Chi Minh City": "Southeast Asia", "Hanoi": "Southeast Asia",
    "Jakarta": "Southeast Asia", "Manila": "Southeast Asia", "Chiang Mai": "Southeast Asia",
    "Phuket": "Southeast Asia", "Phnom Penh": "Southeast Asia", "Siem Reap": "Southeast Asia",
    "Tokyo": "East Asia", "Hong Kong": "East Asia", "Seoul": "East Asia",
    "Osaka": "East Asia", "Macau": "East Asia", "Beijing": "East Asia",
    "Shanghai": "East Asia", "Taipei": "East Asia", "Kyoto": "East Asia",
    "Istanbul": "Middle East", "Dubai": "Middle East", "Antalya": "Middle East",
    "Abu Dhabi": "Middle East", "Tel Aviv": "Middle East", "Amman": "Middle East", "Doha": "Middle East",
    "New York": "Americas", "Los Angeles": "Americas", "Mexico City": "Americas",
    "Buenos Aires": "Americas", "Rio de Janeiro": "Americas", "Miami": "Americas",
    "Chicago": "Americas", "San Francisco": "Americas", "Cancun": "Americas",
    "Sao Paulo": "Americas", "Bogota": "Americas", "Lima": "Americas",
    "Toronto": "Americas", "Vancouver": "Americas", "Montreal": "Americas",
    "Mumbai": "South Asia", "Delhi": "South Asia", "Bangalore": "South Asia",
    "Colombo": "South Asia", "Kathmandu": "South Asia", "Dhaka": "South Asia",
    "Sydney": "Africa & Oceania", "Melbourne": "Africa & Oceania", "Auckland": "Africa & Oceania",
    "Cape Town": "Africa & Oceania", "Johannesburg": "Africa & Oceania", "Nairobi": "Africa & Oceania",
    "Marrakech": "Africa & Oceania", "Cairo": "Africa & Oceania", "Casablanca": "Africa & Oceania",
}

REGION_ENTERTAINMENT = {
    "Western Europe":   {"budget": 5,  "mid": 20, "comfort": 45},
    "Eastern Europe":   {"budget": 3,  "mid": 12, "comfort": 25},
    "Southeast Asia":   {"budget": 3,  "mid": 10, "comfort": 20},
    "East Asia":        {"budget": 5,  "mid": 18, "comfort": 35},
    "Middle East":      {"budget": 5,  "mid": 15, "comfort": 35},
    "Americas":         {"budget": 5,  "mid": 20, "comfort": 40},
    "South Asia":       {"budget": 2,  "mid": 8,  "comfort": 18},
    "Africa & Oceania": {"budget": 5,  "mid": 15, "comfort": 30},
}

DROP_COLS = [
    "Domestic Non-Alcoholic Beer (0.5 Liter Bottle)",
    "Domestic Draft Non-Alcoholic Beer (0.5 Liter)",
    "Imported Non-Alcoholic Beer (0.33 Liter Bottle)",
    "Bottle of Non-Alcoholic Wine (Mid-Range)",
    "Buffalo Round or Equivalent Back Leg Red Meat (1 kg)",
]

# --------------------------------------------------------------------------- #
# Step 1: Scrape
# --------------------------------------------------------------------------- #

def parse_price(val):
    if pd.isna(val):
        return None
    cleaned = re.sub(r"[^\d,\.]", "", str(val)).replace(",", "")
    try:
        return float(cleaned)
    except:
        return None


def scrape_city(city_name, retries=3):
    slug = URL_OVERRIDES.get(city_name, city_name.replace(" ", "-"))
    url = f"https://www.numbeo.com/cost-of-living/in/{slug}"
    headers = {"User-Agent": "Mozilla/5.0"}

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 429:
                wait = 30 * attempt
                print(f"  Rate limited: {city_name} — waiting {wait}s")
                time.sleep(wait)
                continue
            if response.status_code != 200:
                print(f"  Failed: {city_name} (status {response.status_code})")
                return None
            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", {"class": "data_wide_table"})
            if not table:
                print(f"  No table: {city_name}")
                return None
            rows = table.find_all("tr")
            data = {"city": city_name}
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    data[cols[0].get_text(strip=True)] = cols[1].get_text(strip=True)
            print(f"  OK: {city_name}")
            return data
        except Exception as e:
            print(f"  Error: {city_name} — {e}")
            return None

    print(f"  Gave up: {city_name}")
    return None


def run_scraper():
    print("=== STEP 1: Scraping ===")

    # Resume from existing raw file if present
    try:
        existing_df = pd.read_csv("numbeo_raw.csv")
        done_cities = set(existing_df["city"].tolist())
        results = existing_df.to_dict("records")
        print(f"Resuming — {len(done_cities)} cities already done.\n")
    except FileNotFoundError:
        done_cities = set()
        results = []

    remaining = [c for c in CITIES if c not in done_cities]
    print(f"{len(remaining)} cities left.\n")

    for city in remaining:
        print(f"Scraping {city}...")
        result = scrape_city(city)
        if result:
            results.append(result)
            # Save after every city so progress is never lost
            pd.DataFrame(results).to_csv("numbeo_raw.csv", index=False)
        time.sleep(random.uniform(6, 12))  # slightly longer delay for CI

    print(f"Scraped {len(results)}/{len(CITIES)} cities → numbeo_raw.csv\n")
    return pd.DataFrame(results)

# --------------------------------------------------------------------------- #
# Step 2: Clean
# --------------------------------------------------------------------------- #

def clean(df_raw, currency_map):
    print("=== STEP 2: Cleaning ===")
    df = df_raw.copy()
    price_cols = [c for c in df.columns if c not in
                  ["city", "Annual Mortgage Interest Rate (20-Year Fixed, in %)"]]
    df[price_cols] = df[price_cols].map(parse_price)
    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
    price_cols = [c for c in df.columns if c not in
                  ["city", "Annual Mortgage Interest Rate (20-Year Fixed, in %)"]]
    df[price_cols] = df[price_cols].fillna(df[price_cols].median())
    df["Annual Mortgage Interest Rate (20-Year Fixed, in %)"] = df[
        "Annual Mortgage Interest Rate (20-Year Fixed, in %)"
    ].fillna(df["Annual Mortgage Interest Rate (20-Year Fixed, in %)"].median())

    # Convert to USD
    for idx, row in df.iterrows():
        rate = currency_map[row["city"]]
        df.loc[idx, price_cols] = row[price_cols] / rate

    df.to_csv("numbeo_clean_usd.csv", index=False)
    print("Cleaned → numbeo_clean_usd.csv\n")
    return df

# --------------------------------------------------------------------------- #
# Step 3: Transform to tiers
# --------------------------------------------------------------------------- #

def calculate_daily_costs(row):
    r = {}
    r["food_budget"] = (
        row["Meal at an Inexpensive Restaurant"] * 2 +
        row["Combo Meal at McDonald's (or Equivalent Fast-Food Meal)"]
    )
    r["food_mid"] = (
        row["Meal at an Inexpensive Restaurant"] +
        row["Meal for Two at a Mid-Range Restaurant (Three Courses, Without Drinks)"] / 2 +
        row["Combo Meal at McDonald's (or Equivalent Fast-Food Meal)"]
    )
    r["food_comfort"] = (
        row["Meal for Two at a Mid-Range Restaurant (Three Courses, Without Drinks)"] / 2 * 3
    )
    r["transport_budget"] = row["One-Way Ticket (Local Transport)"] * 2
    r["transport_mid"] = (
        row["One-Way Ticket (Local Transport)"] * 2 +
        row["Taxi Start (Standard Tariff)"] +
        row["Taxi 1 km (Standard Tariff)"] * 3
    )
    r["transport_comfort"] = (
        row["Taxi Start (Standard Tariff)"] * 3 +
        row["Taxi 1 km (Standard Tariff)"] * 5
    )
    r["accommodation_budget"] = row["1 Bedroom Apartment Outside of City Centre"] / 30 * 0.4
    r["accommodation_mid"]    = row["1 Bedroom Apartment Outside of City Centre"] / 30 * 1.2
    r["accommodation_comfort"]= row["1 Bedroom Apartment in City Centre"] / 30 * 2.0
    r["extras_budget"]  = row["Bottled Water (1.5 Liter)"]
    r["extras_mid"]     = row["Bottled Water (1.5 Liter)"] + row["Cappuccino (Regular Size)"]
    r["extras_comfort"] = (
        row["Bottled Water (1.5 Liter)"] +
        row["Cappuccino (Regular Size)"] * 2 +
        row["Soft Drink (Coca-Cola or Pepsi, 0.33 Liter Bottle)"]
    )
    return pd.Series(r)


def build_tiers(df_usd):
    print("=== STEP 3: Building tiers ===")
    df_tiers = df_usd[["city"]].copy()
    df_tiers = pd.concat([df_tiers, df_usd.apply(calculate_daily_costs, axis=1)], axis=1)

    # Entertainment — region-based flat values
    df_tiers["region"] = df_tiers["city"].map(CITY_REGION)
    for tier in ["budget", "mid", "comfort"]:
        df_tiers[f"entertainment_{tier}"] = df_tiers["region"].map(
            lambda r: REGION_ENTERTAINMENT[r][tier]
        )
    df_tiers.drop(columns="region", inplace=True)

    # Totals
    for tier in ["budget", "mid", "comfort"]:
        df_tiers[f"total_{tier}"] = (
            df_tiers[f"food_{tier}"] +
            df_tiers[f"transport_{tier}"] +
            df_tiers[f"accommodation_{tier}"] +
            df_tiers[f"entertainment_{tier}"] +
            df_tiers[f"extras_{tier}"]
        )

    df_tiers.to_csv("numbeo_tiers_usd.csv", index=False)
    print("Tiers saved → numbeo_tiers_usd.csv\n")


# --------------------------------------------------------------------------- #
# Run full pipeline
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("EXCHANGERATE_API_KEY")
    currency_map = fetch_currency_map(api_key) if api_key else CURRENCY_MAP_FALLBACK

    df_raw = run_scraper()
    if len(df_raw) > 0:
        df_usd = clean(df_raw, currency_map)
        build_tiers(df_usd)
        print("Pipeline complete.")