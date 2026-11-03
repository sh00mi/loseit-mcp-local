"""MCP server that reads locally-scraped LoseIt data out of SQLite.

This does NOT talk to LoseIt directly — it only reads whatever scraper.py
has already stored in ~/.loseit-data/loseit.db. Run scraper.py on a
schedule (see README.md for the launchd setup) to keep it fresh.
"""
from datetime import date, timedelta
from mcp.server.mcpserver import MCPServer
import db

mcp = MCPServer("loseit")


def _default_range(days: int):
    end = date.today()
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()


@mcp.tool()
def get_daily_summary(start_date: str = None, end_date: str = None, days: int = 7) -> list[dict]:
    """Get daily calorie budget/eaten/remaining, nutrient totals, and journal notes.

    Nutrient totals are the day's sums from LoseIt: protein_g, carbs_g, fat_g,
    sat_fat_g, fiber_g, sugars_g, sodium_mg, cholesterol_mg. Use this, not
    get_food_log, for fiber or any other nutrient question.

    Args:
        start_date: YYYY-MM-DD, optional
        end_date: YYYY-MM-DD, optional
        days: if start/end not given, look back this many days from today (default 7)
    """
    if not start_date or not end_date:
        start_date, end_date = _default_range(days)
    return db.query_daily_summary(start_date, end_date)


@mcp.tool()
def get_food_log(start_date: str = None, end_date: str = None, days: int = 7) -> list[dict]:
    """Get individual logged food items with per-item calories.

    Per-item nutrients (protein_g, carbs_g, fat_g) are always null: the
    scraper does not open each entry. A null there does not mean LoseIt has
    no data for the food. Use get_daily_summary for the day's nutrient totals.

    Args:
        start_date: YYYY-MM-DD, optional
        end_date: YYYY-MM-DD, optional
        days: if start/end not given, look back this many days from today (default 7)
    """
    if not start_date or not end_date:
        start_date, end_date = _default_range(days)
    return db.query_food_log(start_date, end_date)


@mcp.tool()
def get_weight_history(start_date: str = None, end_date: str = None, days: int = 30) -> list[dict]:
    """Get logged body weight over time.

    Args:
        start_date: YYYY-MM-DD, optional
        end_date: YYYY-MM-DD, optional
        days: if start/end not given, look back this many days from today (default 30)
    """
    if not start_date or not end_date:
        start_date, end_date = _default_range(days)
    return db.query_weight_log(start_date, end_date)


@mcp.tool()
def get_water_log(start_date: str = None, end_date: str = None, days: int = 7) -> list[dict]:
    """Get logged water intake (fluid ounces) over time.

    Args:
        start_date: YYYY-MM-DD, optional
        end_date: YYYY-MM-DD, optional
        days: if start/end not given, look back this many days from today (default 7)
    """
    if not start_date or not end_date:
        start_date, end_date = _default_range(days)
    return db.query_water_log(start_date, end_date)


if __name__ == "__main__":
    mcp.run()
