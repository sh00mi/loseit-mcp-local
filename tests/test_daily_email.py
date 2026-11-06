"""daily_email.py: the bot-parsable body for LOSEIT_DAILY_SUMMARY_EMAIL."""
import db
import daily_email


def _parse(body: str):
    head, _, food = body.partition("\n\n")
    fields = dict(line.split(": ", 1) if ": " in line else (line.rstrip(":"), "") for line in head.splitlines())
    food_lines = food.strip().splitlines()
    cols = food_lines[0].removeprefix("food: ").split("|")
    rows = [dict(zip(cols, line.split("|"))) for line in food_lines[1:]]
    return fields, cols, rows


def _store_day(day="2026-07-10", notes="Felt good\nslept late"):
    db.upsert_daily_summary({
        "date": day,
        "calorie_budget": 2000.0,
        "calories_eaten": 1500.0,
        "exercise_calories_burned": 200.0,
        "calories_remaining_before_exercise": 500.0,
        "calories_remaining_after_exercise": 700.0,
        "protein_g": 100.5,
        "carbs_g": 150.0,
        "fat_g": 50.0,
        "fiber_g": 23.6,
        "notes": notes,
    })
    food = {"brand": None, "protein_g": None, "carbs_g": None, "fat_g": None}
    db.replace_food_log(day, [
        {**food, "meal": "Snacks", "name": "Chips | salted", "quantity": 1.0, "units": "Bag", "calories": 150.0},
        {**food, "meal": "Breakfast", "name": "Eggs", "brand": "Farm", "quantity": 0.5, "units": "Each", "calories": 70.0},
        {**food, "meal": "Lunch", "name": "Soup", "quantity": 1.0, "units": "Cup", "calories": 200.0},
    ])


def test_render_missing_day_returns_none(tmp_db):
    assert daily_email.render("2026-07-10") is None


def test_render_has_every_key_and_values(tmp_db):
    _store_day()
    db.upsert_weight("2026-07-10", 180.2)
    db.upsert_water("2026-07-10", 64.0)
    fields, cols, rows = _parse(daily_email.render("2026-07-10"))
    assert fields["format"] == "loseit-daily/1"
    assert fields["date"] == "2026-07-10"
    for key in daily_email.SUMMARY_KEYS:
        assert key in fields
    assert fields["calorie_budget"] == "2000"
    assert fields["protein_g"] == "100.5"
    assert fields["fiber_g"] == "23.6"
    assert fields["sodium_mg"] == ""
    assert fields["weight"] == "180.2"
    assert fields["weight_units"] == "lb"
    assert fields["water_fl_oz"] == "64"
    assert fields["notes"] == "Felt good / slept late"
    assert cols == list(daily_email.FOOD_KEYS)
    assert [r["meal"] for r in rows] == ["Breakfast", "Lunch", "Snacks"]
    assert rows[0] == {"meal": "Breakfast", "name": "Eggs", "brand": "Farm", "quantity": "0.5", "units": "Each", "calories": "70"}
    assert rows[2]["name"] == "Chips / salted"


def test_render_without_weight_or_water_leaves_values_empty(tmp_db):
    _store_day(notes=None)
    fields, _, _ = _parse(daily_email.render("2026-07-10"))
    assert fields["weight"] == ""
    assert fields["weight_units"] == ""
    assert fields["water_fl_oz"] == ""
    assert fields["notes"] == ""


def test_main_exits_1_when_day_missing(tmp_db, capsys):
    assert daily_email.main(["--date", "2026-07-10"]) == 1
    assert "No daily_summary" in capsys.readouterr().err
