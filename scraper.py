import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

CITIES = [
    # Western Europe
    "Paris", "London", "Amsterdam", "Barcelona", "Madrid", "Rome", "Milan",
    "Berlin", "Vienna", "Lisbon", "Athens", "Dublin", "Brussels", "Zurich",
    "Geneva", "Copenhagen", "Stockholm", "Oslo", "Helsinki", "Porto",
    # Eastern Europe
    "Prague", "Budapest", "Warsaw", "Krakow", "Bucharest", "Sofia",
    "Belgrade", "Zagreb", "Tallinn", "Riga", "Vilnius", "Ljubljana",
    # Southeast Asia
    "Bangkok", "Kuala Lumpur", "Singapore", "Bali", "Ho Chi Minh City",
    "Hanoi", "Jakarta", "Manila", "Chiang Mai", "Phuket", "Phnom Penh",
    "Siem Reap",
    # East Asia
    "Tokyo", "Hong Kong", "Seoul", "Osaka", "Macau", "Beijing", "Shanghai",
    "Taipei", "Kyoto",
    # Middle East & Turkey
    "Istanbul", "Dubai", "Antalya", "Abu Dhabi", "Tel Aviv", "Amman", "Doha",
    # Americas
    "New York", "Los Angeles", "Mexico City", "Buenos Aires", "Rio de Janeiro",
    "Miami", "Chicago", "San Francisco", "Cancun", "Sao Paulo", "Bogota",
    "Lima", "Toronto", "Vancouver", "Montreal",
    # South Asia
    "Mumbai", "Delhi", "Bangalore", "Colombo", "Kathmandu", "Dhaka",
    # Africa & Oceania
    "Sydney", "Melbourne", "Auckland", "Cape Town", "Johannesburg", "Nairobi",
    "Marrakech", "Cairo", "Casablanca"
]

# Manual URL overrides for cities where name != Numbeo's URL slug
URL_OVERRIDES = {
    "Krakow": "Krakow-Cracow",
    "Macau": "Macao",
    "Bali": "Denpasar",
    "Siem Reap": "Siem-Reap",
    "Tel Aviv": "Tel-Aviv-Yafo",
    "Rio de Janeiro": "Rio-De-Janeiro",
    "Cairo": "Cairo-Egypt",
}

def scrape_city(city_name, retries=3):
    slug = URL_OVERRIDES.get(city_name, city_name.replace(" ", "-"))
    url = f"https://www.numbeo.com/cost-of-living/in/{slug}"
    headers = {"User-Agent": "Mozilla/5.0"}

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 429:
                wait = 30 * attempt
                print(f"  Rate limited: {city_name} — waiting {wait}s (attempt {attempt}/{retries})")
                time.sleep(wait)
                continue

            if response.status_code != 200:
                print(f"  Failed: {city_name} (status {response.status_code})")
                return None

            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", {"class": "data_wide_table"})
            if not table:
                print(f"  No table found: {city_name} (URL: {url})")
                return None

            rows = table.find_all("tr")
            data = {"city": city_name}
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    item = cols[0].get_text(strip=True)
                    price = cols[1].get_text(strip=True)
                    data[item] = price

            print(f"  OK: {city_name}")
            return data

        except Exception as e:
            print(f"  Error: {city_name} — {e}")
            return None

    print(f"  Gave up: {city_name}")
    return None


def run_scraper():
    # Load already-scraped cities if CSV exists
    try:
        existing_df = pd.read_csv("numbeo_raw.csv")
        done_cities = set(existing_df["city"].tolist())
        results = existing_df.to_dict("records")
        print(f"Resuming — {len(done_cities)} cities already scraped.\n")
    except FileNotFoundError:
        done_cities = set()
        results = []

    remaining = [c for c in CITIES if c not in done_cities]
    print(f"{len(remaining)} cities left to scrape.\n")

    for city in remaining:
        print(f"Scraping {city}...")
        result = scrape_city(city)
        if result:
            results.append(result)
        delay = random.uniform(4, 8)
        time.sleep(delay)

    df = pd.DataFrame(results)
    df.to_csv("numbeo_raw.csv", index=False)
    print(f"\nDone. {len(results)}/{len(CITIES)} cities saved to numbeo_raw.csv")


if __name__ == "__main__":
    run_scraper()