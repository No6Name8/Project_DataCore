"""
calendar_context.py  --  DataCore AI Engine: Saudi seasonal / calendar context.

Hardcoded, fully-offline lookup of Saudi-Arabia-relevant dates that influence
consumer revenue.  No external API calls — this is a static reference table so
the demo runs deterministically with no network dependency.

get_calendar_features(date) turns any date into a small dict of boolean/day-count
signals that the Revenue Forecaster consumes as Prophet regressors.  When a date
falls outside the documented year range the features degrade gracefully to
False / None rather than raising.

Date sources (approximate — Islamic dates are lunar and shift ~11 days/year;
the Umm al-Qura calendar is the official Saudi reference):
  * Ramadan / Eid windows: approximate Umm al-Qura / widely-published Gregorian
    equivalents for 2022–2027.  Real deployments would sync SAMA / Umm al-Qura.
  * Saudi National Day: fixed 23 September (Royal decree).
  * School summer break: approximate; the Saudi academic year runs roughly
    late-August to late-June, so summer break ~ 20 Jun – 25 Aug.
These are illustrative for the demo and are NOT authoritative religious dates.
"""

from datetime import date, timedelta

# ── Ramadan (start, end) inclusive, Gregorian, per Hijri year ──────────────────
RAMADAN = {
    2022: ("2022-04-02", "2022-05-01"),
    2023: ("2023-03-23", "2023-04-20"),
    2024: ("2024-03-11", "2024-04-09"),
    2025: ("2025-03-01", "2025-03-29"),
    2026: ("2026-02-18", "2026-03-19"),
    2027: ("2027-02-08", "2027-03-08"),
}

# ── Eid al-Fitr windows (1st–4th Shawwal, approx) ──────────────────────────────
EID_AL_FITR = {
    2022: ("2022-05-02", "2022-05-05"),
    2023: ("2023-04-21", "2023-04-24"),
    2024: ("2024-04-10", "2024-04-13"),
    2025: ("2025-03-30", "2025-04-02"),
    2026: ("2026-03-20", "2026-03-23"),
    2027: ("2027-03-09", "2027-03-12"),
}

# ── Eid al-Adha windows (10th–13th Dhul-Hijjah, approx) ────────────────────────
EID_AL_ADHA = {
    2022: ("2022-07-09", "2022-07-12"),
    2023: ("2023-06-28", "2023-07-01"),
    2024: ("2024-06-16", "2024-06-19"),
    2025: ("2025-06-06", "2025-06-09"),
    2026: ("2026-05-26", "2026-05-29"),
    2027: ("2027-05-16", "2027-05-19"),
}

# ── Saudi National Day — fixed 23 September; we treat the surrounding week ──────
NATIONAL_DAY_MONTH = 9
NATIONAL_DAY_DAY   = 23

# ── School summer-break window (month/day), applied to every year (approx) ─────
SCHOOL_HOLIDAY_START = (6, 20)   # 20 Jun
SCHOOL_HOLIDAY_END   = (8, 25)   # 25 Aug

_YEARS = sorted(RAMADAN.keys())


# ── Helpers ────────────────────────────────────────────────────────────────────

def _to_date(d) -> date:
    """Coerce str / datetime / pandas.Timestamp / date to a datetime.date."""
    if isinstance(d, date) and not hasattr(d, "hour"):
        return d
    if hasattr(d, "date"):          # datetime / pd.Timestamp
        return d.date()
    return date.fromisoformat(str(d)[:10])


def _in_window(d: date, window: tuple) -> bool:
    start = date.fromisoformat(window[0])
    end   = date.fromisoformat(window[1])
    return start <= d <= end


def _any_window(d: date, table: dict) -> bool:
    win = table.get(d.year)
    if win and _in_window(d, win):
        return True
    # Windows can straddle a year boundary (e.g. Ramadan starting in Feb) — also
    # check the adjacent year's window defensively.
    for yr in (d.year - 1, d.year + 1):
        win = table.get(yr)
        if win and _in_window(d, win):
            return True
    return False


def _days_until_ramadan(d: date):
    """Days until the next Ramadan start on/after `d`; None if beyond the table."""
    candidates = []
    for yr in _YEARS:
        start = date.fromisoformat(RAMADAN[yr][0])
        if start >= d:
            candidates.append((start - d).days)
    return min(candidates) if candidates else None


def _is_national_day_week(d: date) -> bool:
    nd = date(d.year, NATIONAL_DAY_MONTH, NATIONAL_DAY_DAY)
    return abs((d - nd).days) <= 3     # 20–26 September


def _is_school_holiday(d: date) -> bool:
    start = date(d.year, *SCHOOL_HOLIDAY_START)
    end   = date(d.year, *SCHOOL_HOLIDAY_END)
    return start <= d <= end


# ── Public API ─────────────────────────────────────────────────────────────────

def get_calendar_features(d) -> dict:
    """
    Returns Saudi calendar context for a single date.

    Keys:
      is_ramadan            bool
      is_eid_window         bool   (Eid al-Fitr OR Eid al-Adha)
      is_national_day_week  bool
      is_school_holiday     bool
      days_until_ramadan    int | None   (None if outside the documented range)

    Never raises — an unparseable / out-of-range date yields all-neutral features.
    """
    try:
        dd = _to_date(d)
    except (ValueError, TypeError):
        return {
            "is_ramadan": False, "is_eid_window": False,
            "is_national_day_week": False, "is_school_holiday": False,
            "days_until_ramadan": None,
        }

    return {
        "is_ramadan":           _any_window(dd, RAMADAN),
        "is_eid_window":        _any_window(dd, EID_AL_FITR) or _any_window(dd, EID_AL_ADHA),
        "is_national_day_week": _is_national_day_week(dd),
        "is_school_holiday":    _is_school_holiday(dd),
        "days_until_ramadan":   _days_until_ramadan(dd),
    }


# The four boolean features used as Prophet regressors (days_until_ramadan is a
# display feature, not a regressor — it is unbounded and mostly redundant).
REGRESSOR_KEYS = ["is_ramadan", "is_eid_window", "is_national_day_week", "is_school_holiday"]


if __name__ == "__main__":
    for sample in ["2025-03-10", "2025-06-07", "2025-07-15", "2025-09-23", "2030-01-01"]:
        print(f"{sample} -> {get_calendar_features(sample)}")
