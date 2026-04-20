"""
Travel Budget Cost Calculator
Inputs  → tier selections per category + trip params
Outputs → daily costs per category, total trip cost, verdict
"""

import pandas as pd

# --------------------------------------------------------------------------- #
# Load data
# --------------------------------------------------------------------------- #

def load_tier_data(csv_path: str = "data/numbeo_tiers_usd.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path, index_col="city")
    return df


# --------------------------------------------------------------------------- #
# Core calculator
# --------------------------------------------------------------------------- #

CATEGORIES = ["accommodation", "food", "transport", "entertainment"]
TIERS      = ["budget", "mid", "comfort"]

CONTINGENCY = 0.12  # 12% buffer applied to estimates


def get_daily_costs(
    df: pd.DataFrame,
    city: str,
    accommodation_tier: str,
    food_tier: str,
    transport_tier: str,
    entertainment_tier: str,
) -> dict:
    """
    Returns daily cost per category (USD) for the chosen tiers.
    """
    if city not in df.index:
        raise ValueError(f"City '{city}' not found in dataset.")

    selections = {
        "accommodation":  accommodation_tier,
        "food":           food_tier,
        "transport":      transport_tier,
        "entertainment":  entertainment_tier,
    }

    daily = {}
    for cat, tier in selections.items():
        if tier not in TIERS:
            raise ValueError(f"Tier '{tier}' invalid. Choose from: {TIERS}")
        col = f"{cat}_{tier}"
        daily[cat] = round(df.loc[city, col], 2)

    daily["total"] = round(sum(daily.values()), 2)
    return daily


def estimate_trip_cost(
    df: pd.DataFrame,
    city: str,
    days: int,
    people: int,
    accommodation_tier: str,
    food_tier: str,
    transport_tier: str,
    entertainment_tier: str,
) -> dict:
    """
    Full trip cost estimate with contingency buffer.

    Returns a dict with:
      - daily_costs       : per-category daily cost (per person)
      - subtotal          : raw total before buffer
      - contingency_amount: 12% buffer
      - total_estimated   : subtotal + buffer
      - per_person_total  : total_estimated / people
      - inputs            : echo of inputs for reference
    """
    daily = get_daily_costs(
        df, city,
        accommodation_tier, food_tier,
        transport_tier, entertainment_tier,
    )

    # All costs are per-person (accommodation = per bed price).
    subtotal = round(daily["total"] * people * days, 2)
    contingency = round(subtotal * CONTINGENCY, 2)
    total        = round(subtotal + contingency, 2)

    return {
        "inputs": {
            "city": city, "days": days, "people": people,
            "accommodation": accommodation_tier, "food": food_tier,
            "transport": transport_tier, "entertainment": entertainment_tier,
        },
        "daily_costs_per_person_usd": daily,
        "subtotal_usd":               subtotal,
        "contingency_usd":            contingency,
        "total_estimated_usd":        total,
        "per_person_total_usd":       round(total / people, 2),
    }


# --------------------------------------------------------------------------- #
# Verdict engine
# --------------------------------------------------------------------------- #

def get_verdict(user_budget_usd: float, estimate: dict) -> dict:
    """
    Compares user budget against estimated total.

    Returns:
      - verdict  : "Comfortable" | "Tight but doable" | "You'll run out by day X"
      - surplus  : positive = under budget, negative = over budget
      - daily_surplus : surplus / days
      - runout_day    : day budget runs out (if over budget), else None
    """
    total     = estimate["total_estimated_usd"]
    days      = estimate["inputs"]["days"]
    people    = estimate["inputs"]["people"]
    surplus   = round(user_budget_usd - total, 2)

    # Daily burn = per-person total × people + contingency
    daily_total  = estimate["daily_costs_per_person_usd"]["total"]
    scaled_daily = daily_total * people * (1 + CONTINGENCY)

    daily_surplus = round(surplus / days, 2) if days else 0

    if surplus >= total * 0.15:
        verdict = "Comfortable"
    elif surplus >= 0:
        verdict = "Tight but doable"
    else:
        days_covered = user_budget_usd / (scaled_daily) if scaled_daily else 0
        runout_day   = max(1, int(days_covered))
        return {
            "verdict":      f"You'll run out by day {runout_day}",
            "surplus_usd":  surplus,
            "daily_surplus_usd": daily_surplus,
            "runout_day":   runout_day,
        }

    return {
        "verdict":           verdict,
        "surplus_usd":       surplus,
        "daily_surplus_usd": daily_surplus,
        "runout_day":        None,
    }


# --------------------------------------------------------------------------- #
# Convenience: one-call summary
# --------------------------------------------------------------------------- #

def budget_check(
    city: str,
    days: int,
    people: int,
    user_budget_usd: float,
    accommodation_tier: str = "mid",
    food_tier: str          = "mid",
    transport_tier: str     = "budget",
    entertainment_tier: str = "budget",
    csv_path: str           = "numbeo_tiers_usd.csv",
) -> dict:
    df       = load_tier_data(csv_path)
    estimate = estimate_trip_cost(
        df, city, days, people,
        accommodation_tier, food_tier, transport_tier, entertainment_tier,
    )
    verdict  = get_verdict(user_budget_usd, estimate)
    return {"estimate": estimate, "verdict": verdict}


# --------------------------------------------------------------------------- #
# Quick smoke test
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    result = budget_check(
        city              = "Bangkok",
        days              = 10,
        people            = 2,
        user_budget_usd   = 1200,
        accommodation_tier= "budget",
        food_tier         = "mid",
        transport_tier    = "budget",
        entertainment_tier= "budget",
    )

    est = result["estimate"]
    vrd = result["verdict"]

    print("=== ESTIMATE ===")
    print(f"City:        {est['inputs']['city']}")
    print(f"Days:        {est['inputs']['days']}  |  People: {est['inputs']['people']}")
    print(f"Daily costs (per person): {est['daily_costs_per_person_usd']}")
    print(f"Subtotal:    ${est['subtotal_usd']}")
    print(f"Contingency: ${est['contingency_usd']} (12%)")
    print(f"Total est.:  ${est['total_estimated_usd']}")
    print(f"Per person:  ${est['per_person_total_usd']}")
    print("\n=== VERDICT ===")
    print(f"Verdict:       {vrd['verdict']}")
    print(f"Surplus:       ${vrd['surplus_usd']}")
    print(f"Daily surplus: ${vrd['daily_surplus_usd']}/day")