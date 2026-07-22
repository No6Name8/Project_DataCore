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
        Returns:
          { "similar_businesses_in_district": int,
            "density_tier": "underserved"|"balanced"|"saturated",
            "market_gap_flag": bool }   # true only when tier == "underserved"
        or None when the district (or its data for this type) is unknown.
        """
        d = self._district(district_name)
        if not d:
            return None
        key = self._norm_type(business_type)
        competitors = d.get("competitors", {})
        if key not in competitors:
            return None
        count = int(competitors[key])
        if count <= _UNDERSERVED_MAX:
            tier = "underserved"
        elif count >= _SATURATED_MIN:
            tier = "saturated"
        else:
            tier = "balanced"
        return {
            "similar_businesses_in_district": count,
            "density_tier":                   tier,
            "market_gap_flag":                tier == "underserved",
        }


if __name__ == "__main__":
    loc = LocationContext()
    for dist in ["Al Olaya", "Al Naseem", "Al Batha", "Nowhere"]:
        print(dist, "->", loc.get_district_profile(dist))
    print("cafe@AlOlaya    ->", loc.get_competitor_density("Al Olaya", "cafe"))
    print("minimarket@Naseem->", loc.get_competitor_density("Al Naseem", "minimarket"))
    print("cardealer@Batha ->", loc.get_competitor_density("Al Batha", "cardealer"))
