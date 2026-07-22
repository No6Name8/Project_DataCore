"""
license_taxonomy.py  --  DataCore AI Engine: registration / licensing taxonomy.

Static, offline mapping between Saudi-style license categories and the business
types the engine works with, plus the reverse links needed to cross-check a
model's *inferred* type against a *declared* license category.

No external calls. Pure lookup tables — the single source of truth for the
registration/licensing enrichment layer consumed by the Business Classifier
(ground-truth cross-check) and, indirectly, the demo wiring.

The controlled vocabulary is intentionally small and documented here so the
mapping is auditable.
"""

# ── Controlled vocabulary: license_category → expected business types ──────────
LICENSE_CATEGORY_TO_TYPES = {
    "food_beverage":     ["cafe", "restaurant"],
    "retail_general":    ["minimarket", "supermarket"],
    "retail_specialty":  ["auto_gallery", "motorbike_shop", "boutique"],
    "services_personal": ["laundromat", "salon"],
    "real_estate":       ["real_estate"],
    "other":             [],   # fallback bucket — cannot be contradicted
}

# Reverse index: business_type → its license_category
_TYPE_TO_CATEGORY = {
    t: cat for cat, types in LICENSE_CATEGORY_TO_TYPES.items() for t in types
}

# Classifier archetype label → canonical business_type.
# Lets us turn "what the transactions look like" (the inferred archetype) into a
# concrete business_type that can be compared against the declared license.
ARCHETYPE_LABEL_TO_TYPE = {
    "high_freq_low_ticket_food":              "cafe",
    "high_freq_mid_ticket_retail":            "minimarket",
    "high_freq_high_ticket_supermarket":      "supermarket",
    "low_freq_high_ticket_automotive":        "auto_gallery",
    "sparse_high_ticket_brokerage":           "real_estate",
    "low_ticket_steady_essential":            "laundromat",
    "low_freq_mid_ticket_dealer":             "motorbike_shop",
    "mid_ticket_mid_freq_services":           "salon",
    "mid_freq_high_ticket_electronics":       "boutique",
    "mid_freq_low_ticket_personal_services":  "salon",
    "low_freq_high_value_medical":            "clinic",
    "mid_freq_mid_ticket_fashion":            "boutique",
}


def get_expected_business_types(license_category) -> list:
    """Business types a given license category normally covers ([] if unknown)."""
    if not license_category:
        return []
    return list(LICENSE_CATEGORY_TO_TYPES.get(str(license_category).strip().lower(), []))


def business_type_to_license_category(business_type):
    """Reverse lookup: which license category a business type falls under (or None)."""
    if not business_type:
        return None
    return _TYPE_TO_CATEGORY.get(str(business_type).strip().lower())


def is_type_consistent_with_license(business_type, license_category) -> bool:
    """
    True when the (inferred) business type is consistent with the declared
    license category. Conservative by design: a missing side, the "other"
    bucket, or an unrecognised category returns True (we never fabricate an
    inconsistency we cannot substantiate).
    """
    if not business_type or not license_category:
        return True
    cat = str(license_category).strip().lower()
    if cat == "other" or cat not in LICENSE_CATEGORY_TO_TYPES:
        return True
    return str(business_type).strip().lower() in LICENSE_CATEGORY_TO_TYPES[cat]


def archetype_label_to_business_type(label):
    """Map a classifier archetype label to a concrete business_type (or None)."""
    if not label:
        return None
    return ARCHETYPE_LABEL_TO_TYPE.get(str(label).strip().lower())


if __name__ == "__main__":
    print("food_beverage ->", get_expected_business_types("food_beverage"))
    print("cafe consistent w/ food_beverage:", is_type_consistent_with_license("cafe", "food_beverage"))
    print("laundromat consistent w/ food_beverage:", is_type_consistent_with_license("laundromat", "food_beverage"))
    print("archetype high_freq_low_ticket_food ->", archetype_label_to_business_type("high_freq_low_ticket_food"))
