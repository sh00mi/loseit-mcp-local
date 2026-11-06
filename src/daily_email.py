"""Render one stored day as a plain-text email body for LOSEIT_DAILY_SUMMARY_EMAIL.

The format is meant to be read by a bot first and a human second:

    format: loseit-daily/1
    date: 2026-07-10
    calorie_budget: 2000
    ...
    weight: 180.2
    weight_units: lb
    water_fl_oz: 64
    notes: Felt good

    food: meal|name|brand|quantity|units|calories
    Breakfast|Eggs||2|Each|140

Every key is always present; a missing value is left empty. Keys match the
SQLite/MCP column names. Text fields never contain "|" or newlines.

Usage: python src/daily_email.py [--date YYYY-MM-DD]   (default: yesterday)
Prints the body on stdout; exits 1 if the day has no daily_summary row.
"""
import argparse
import sys
from datetime import date, timedelta

import db

FORMAT = "loseit-daily/1"
SUMMARY_KEYS = (
    "calorie_budget",
    "calories_eaten",
    "exercise_calories_burned",
    "calories_remaining_before_exercise",
    "calories_remaining_after_exercise",
    "protein_g",
    "carbs_g",
    "fat_g",
    "sat_fat_g",
    "fiber_g",
    "sugars_g",
    "sodium_mg",
    "cholesterol_mg",
)
# food_log's per-item macro columns are never populated by the scraper.
FOOD_KEYS = ("meal", "name", "brand", "quantity", "units", "calories")
MEAL_ORDER = ("Breakfast", "Lunch", "Dinner", "Snacks")


def _fmt(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:g}" if value == int(value) else f"{round(value, 2):g}"
    return " / ".join(line.strip() for line in str(value).splitlines() if line.strip())


def _cell(value) -> str:
    return _fmt(value).replace("|", "/")


def render(day: str) -> str | None:
    summary = db.query_daily_summary(day, day)
    if not summary:
        return None
    s = summary[0]
    weight = db.query_weight_log(day, day)
    water = db.query_water_log(day, day)
    w = weight[0] if weight else {}

    lines = [f"format: {FORMAT}", f"date: {day}"]
    lines += [f"{k}: {_fmt(s.get(k))}" for k in SUMMARY_KEYS]
    lines.append(f"weight: {_fmt(w.get('weight'))}")
    lines.append(f"weight_units: {_fmt(w.get('units'))}")
    lines.append(f"water_fl_oz: {_fmt(water[0]['fluid_ounces'] if water else None)}")
    lines.append(f"notes: {_fmt(s.get('notes'))}")
    lines.append("")
    lines.append("food: " + "|".join(FOOD_KEYS))
    foods = sorted(
        db.query_food_log(day, day),
        key=lambda r: (MEAL_ORDER.index(r["meal"]) if r["meal"] in MEAL_ORDER else len(MEAL_ORDER), r["id"]),
    )
    for row in foods:
        lines.append("|".join(_cell(row.get(k)) for k in FOOD_KEYS))
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--date", default=None, help="YYYY-MM-DD, default yesterday")
    args = parser.parse_args(argv)
    day = args.date or (date.today() - timedelta(days=1)).isoformat()
    date.fromisoformat(day)
    body = render(day)
    if body is None:
        print(f"No daily_summary stored for {day}.", file=sys.stderr)
        return 1
    sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
