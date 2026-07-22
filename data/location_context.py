"""
location_context.py  --  DataCore AI Engine: offline district reference helper.

Backs the optional LOCATION enrichment layer.  Reads a static JSON file
(data/district_reference.json) — NO external API calls, fully offline for the
demo.  Every lookup degrades gracefully: an unknown district or business type
returns None so callers can treat location as "not applied" and behave exactly
as they did before location was supplied.

The underlying values are ILLUSTRATIVE demo estimates (see the JSON _meta block)
and would be replaced by the bank's real market data in production.
"""

import os
import json

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REF_PATH = os.path.join(_ROOT, "data", "district_reference.json")

# Competitor-count → tier thresholds (kept in sync with the JSON _meta block)
_UNDERSERVED_MAX = 2   # count <= this → underserved
_SATURATED_MIN   = 7   # count >= this → saturated


class LocationContext:
    """
    Offline lookups over the static district reference file.

    Usage:
        loc = LocationContext()
        loc.get_district_profile("Al Olaya")
        loc.get_competitor_density("Al Naseem", "minimarket")
    """

    def __init__(self, ref_path: str = None):
        self._ref_path = ref_path or _REF_PATH
        self._data = self._load()

    # ── Loading ────────────────────────────────────────────────────────────────
    def _load(self) -> dict:
        try:
            with open(self._ref_path, encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, ValueError):
            # Missing/corrupt reference → behave as if no location data exists.
            return {"districts": {}, "aliases": {}}

        districts = raw.get("districts", {})
        aliases   = (raw.get("_meta", {}) or {}).get("business_type_aliases", {})
        return {"districts": districts, "aliases": aliases}

    # ── Normalisation ──────────────────────────────────────────────────────────
    def _norm_type(self, business_type) -> str:
        """Map API business-type names onto the JSON's competitor keys."""
        if not business_type:
            return ""
        bt = str(business_type).strip().lower()
        return self._data["aliases"].get(bt, bt)

    def _district(self, district_name):
        if not district_name:
            return None
        return self._data["districts"].get(str(district_name).strip())

    # ── Public: district profile ───────────────────────────────────────────────
    def get_district_profile(self, district_name):
        """
        Returns:
          { "avg_household_income_sar": int,
            "population_density_tier":  "low"|"medium"|"high",
            "commercial_activity_tier": "low"|"medium"|"high" }
        or None when the district is unknown (caller degrades to neutral).
        """
        d = self._district(district_name)
        if not d:
            return None
        return {
            "avg_household_income_sar": int(d.get("avg_household_income_sar", 0)),
            "population_density_tier":  d.get("population_density_tier", "medium"),
            "commercial_activity_tier": d.get("commercial_activity_tier", "medium"),
        }

    # ── Public: competitor density ─────────────────────────────────────────────
    def get_competitor_density(self, district_name, business_type):
        """
        Returns a dict with an explicit three-way outcome plus a plain-language
        `evidence` string explaining WHY the flag did (or didn't) fire:

          { "similar_businesses_in_district": int | None,
            "density_tier": "underserved"|"balanced"|"saturated"|"unknown",
            "market_gap_flag": bool,   # true ONLY for a data-backed "underserved"
            "evidence": str }

        The three cases are distinguished explicitly so absence of data is never
        mistaken for an underserved market:
          * data present + few competitors  → "underserved", market_gap True
          * data present + many/moderate     → "saturated"/"balanced", flag False
          * data absent (no entry)           → "unknown", flag False
        """
        d = self._district(district_name)
        key = self._norm_type(business_type)
        competitors = (d or {}).get("competitors", {})

        # ── Case 3: data absent — honest "unknown", never a false gap ─────────
        if not d or key not in competitors:
            return {
                "similar_businesses_in_district": None,
                "density_tier":                   "unknown",
                "market_gap_flag":                False,
                "evidence": "insufficient reference data for this district/business type",
            }

        count = int(competitors[key])
        # ── Cases 1 & 2: data present ─────────────────────────────────────────
        if count <= _UNDERSERVED_MAX:
            tier = "underserved"
            evidence = (f"{count} similar business(es) recorded in this district "
                        f"(<= {_UNDERSERVED_MAX}, underserved / potential market gap)")
        elif count >= _SATURATED_MIN:
            tier = "saturated"
            evidence = (f"{count} similar businesses recorded in this district "
                        f"(>= {_SATURATED_MIN}, saturated)")
        else:
            tier = "balanced"
            evidence = (f"{count} similar businesses recorded in this district "
                        f"(balanced supply)")
        return {
            "similar_businesses_in_district": count,
            "density_tier":                   tier,
            "market_gap_flag":                tier == "underserved",
            "evidence":                       evidence,
        }


if __name__ == "__main__":
    loc = LocationContext()
    for dist in ["Al Olaya", "Al Naseem", "Al Batha", "Nowhere"]:
        print(dist, "->", loc.get_district_profile(dist))
    print("cafe@AlOlaya    ->", loc.get_competitor_density("Al Olaya", "cafe"))
    print("minimarket@Naseem->", loc.get_competitor_density("Al Naseem", "minimarket"))
    print("cardealer@Batha ->", loc.get_competitor_density("Al Batha", "cardealer"))
