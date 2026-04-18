from groq import Groq


def build_context(city, days, people, tiers, estimate, verdict, currency, rate) -> str:
    daily = estimate["daily_costs_per_person_usd"]
    surplus = verdict["surplus_usd"]

    def c(usd):
        return f"{currency} {usd * rate:,.0f}"

    return f"""
Trip: {city} | {days} days | {people} person(s)
Tiers: Accommodation={tiers['acc']}, Food={tiers['food']}, Transport={tiers['transport']}, Activities={tiers['ent']}

Daily cost per person:
  Accommodation: {c(daily['accommodation'])}
  Food:          {c(daily['food'])}
  Transport:     {c(daily['transport'])}
  Activities:    {c(daily['entertainment'])}

Total estimated: {c(estimate['total_estimated_usd'])}
Surplus/deficit: {c(surplus)} ({'surplus' if surplus >= 0 else 'DEFICIT'})
Verdict:         {verdict['verdict']}
""".strip()


def get_advice(context: str, api_key: str) -> str:
    client = Groq(api_key=api_key)

    chat_completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        max_tokens=1024,
        temperature=0.5,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a practical travel budget advisor. "
                    "Be concise, specific, and honest. No fluff. Use bullet points."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Here is a traveler's trip budget breakdown:\n\n{context}\n\n"
                    "Give advice in exactly three sections:\n"
                    "1. **Biggest cost drivers** — which categories dominate and why\n"
                    "2. **Where to save** — specific actionable tips for this destination and their chosen tiers\n"
                    "3. **Alternative destinations** — 2–3 cheaper cities with a similar vibe if the budget is tight "
                    "(skip this section if they have a comfortable surplus)"
                ),
            },
        ],
    )

    return chat_completion.choices[0].message.content