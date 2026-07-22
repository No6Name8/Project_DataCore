"""
test_enrichment.py — optional seasonal + location enrichment across the models.

Covers, per enriched model:
  * 2 tests confirming enrichment WORKS when the optional fields are present
  * 2 tests confirming graceful degradation when the fields are ABSENT
    (output identical in shape/behaviour to the pre-enrichment version)
Plus 1 test confirming Rawabi's fraud output combines its existing behavioral
signal with the new district-scale signal.

Enriched models: Business Classifier (location), Fraud Detector (location),
Revenue Forecaster (seasonal). The Expense Estimator has no optional input in
this task and is intentionally not covered here.

Run:  python -m pytest tests/test_enrichment.py -v
"""

import sys, os
import pytest
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DATA_DIR = os.path.join(ROOT, "data", "processed")

# District placements used by the demo (mirror api/app.py)
LOC_CAFE      = {"location_district": "Al Olaya",  "location_city": "Riyadh",
                 "location_lat": 24.69, "location_lng": 46.68}
LOC_MINIMKT   = {"location_district": "Al Naseem", "location_city": "Riyadh"}
LOC_RAWABI    = {"location_district": "Al Batha",  "location_city": "Riyadh"}
LOC_UNKNOWN   = {"location_district": "Nowhereville", "location_city": "Riyadh"}


def _tx(bid):
    tx = pd.read_csv(os.path.join(DATA_DIR, f"{bid}_transactions.csv"))
    tx["timestamp"] = pd.to_datetime(tx["timestamp"])
    return tx


# ── Model 1: BusinessClassifier — location enrichment ─────────────────────────

class TestClassifierLocation:

    @pytest.fixture(scope="class")
    def clf(self):
        from models.business_classifier import BusinessClassifier
        c = BusinessClassifier()
        c.load()
        return c

    # ── enrichment present ──
    def test_location_context_attached(self, clf):
        r = clf.classify_from_data(_tx("cafe"), bid="cafe",
                                   location=LOC_CAFE, business_type="cafe")
        assert "location_context" in r
        lc = r["location_context"]
        assert lc["district"] == "Al Olaya"
        assert lc["district_profile"]["avg_household_income_sar"] > 0
        assert lc["competitor_density"]["density_tier"] == "saturated"
        assert r["data_quality"]["location_enrichment_used"] is True

    def test_market_gap_flag_fires_for_underserved(self, clf):
        r = clf.classify_from_data(_tx("minimarket"), bid="minimarket",
                                   location=LOC_MINIMKT, business_type="minimarket")
        assert r["data_quality"]["market_gap_detected"] is True
        assert r["location_context"]["competitor_density"]["density_tier"] == "underserved"

    # ── graceful degradation (absent) ──
    def test_no_location_identical_core_and_no_context(self, clf):
        base = clf.classify_from_data(_tx("cafe"), bid="cafe")
        enr  = clf.classify_from_data(_tx("cafe"), bid="cafe",
                                      location=LOC_CAFE, business_type="cafe")
        # No location supplied → no enrichment keys at all
        assert "location_context" not in base
        assert "location_enrichment_used" not in base["data_quality"]
        # Core inference unchanged by the presence of location metadata
        assert base["cluster_id"] == enr["cluster_id"]
        assert base["dominant_archetype"] == enr["dominant_archetype"]
        assert base["confidence"] == enr["confidence"]
        assert base["raw_features"] == enr["raw_features"]

    def test_unknown_district_degrades_gracefully(self, clf):
        r = clf.classify_from_data(_tx("cafe"), bid="cafe",
                                   location=LOC_UNKNOWN, business_type="cafe")
        assert r["data_quality"]["location_enrichment_used"] is False
        assert r["data_quality"]["market_gap_detected"] is False
        assert "location_context" not in r          # nothing fabricated
        assert "cluster_id" in r                     # core result still intact


# ── Model 3: FraudDetector — location enrichment ──────────────────────────────

class TestFraudLocation:

    @pytest.fixture(scope="class")
    def det(self):
        from models.fraud_detector import FraudDetector
        d = FraudDetector()
        d.load()
        return d

    # ── enrichment present ──
    def test_district_scale_context_attached(self, det):
        rep = det.assess("cardealer", location=LOC_RAWABI)
        assert "location_context" in rep
        norm = rep["location_context"]["transaction_scale_vs_district_norm"]
        assert norm["well_above_range"] > 0
        assert rep["data_quality"]["location_enrichment_used"] is True
        assert rep["data_quality"]["district_scale_flag_triggered"] is True

    def test_low_scale_business_not_triggered(self, det):
        # Cafe: tiny tickets in a high-income district → no district-scale flag
        rep = det.assess("cafe", location=LOC_CAFE)
        assert rep["data_quality"]["location_enrichment_used"] is True
        assert rep["data_quality"]["district_scale_flag_triggered"] is False

    # ── graceful degradation (absent) ──
    def test_no_location_identical_core_and_no_context(self, det):
        base = det.assess("cardealer")
        enr  = det.assess("cardealer", location=LOC_RAWABI)
        assert "location_context" not in base
        assert "location_enrichment_used" not in base["data_quality"]
        # Behavioral fraud score/status unchanged by adding location metadata
        assert base["fraud_score"] == enr["fraud_score"]
        assert base["overall_status"] == enr["overall_status"]

    def test_unknown_district_degrades_gracefully(self, det):
        rep = det.assess("cardealer", location=LOC_UNKNOWN)
        assert rep["data_quality"]["location_enrichment_used"] is False
        assert rep["data_quality"]["district_scale_flag_triggered"] is False
        assert "location_context" not in rep
        assert "fraud_score" in rep


# ── Model 4: RevenueForecaster — seasonal enrichment ──────────────────────────

class TestForecasterSeasonal:

    # ── enrichment present ──
    def test_prepare_data_adds_regressors_for_sa(self):
        from models.revenue_forecaster import RevenueForecaster
        from data.calendar_context import REGRESSOR_KEYS
        f = RevenueForecaster()
        daily = f.prepare_data(_tx("cafe"), bid="cafe")   # default → SA
        for key in REGRESSOR_KEYS:
            assert key in daily.columns
        assert f._active_regressors["cafe"] == list(REGRESSOR_KEYS)

    def test_fit_sets_seasonal_flag_for_sa(self):
        from models.revenue_forecaster import RevenueForecaster
        f = RevenueForecaster()
        f.fit("cafe", _tx("cafe"))                        # default → SA
        s = f.summaries["cafe"]
        assert s["seasonal_context_used"] is True
        assert s["data_quality"]["seasonal_context_used"] is True

    # ── graceful degradation (absent / non-SA) ──
    def test_prepare_data_no_regressors_for_non_sa(self):
        from models.revenue_forecaster import RevenueForecaster
        from data.calendar_context import REGRESSOR_KEYS
        f = RevenueForecaster()
        daily = f.prepare_data(_tx("cafe"), bid="cafe",
                               location={"location_country": "AE"})
        for key in REGRESSOR_KEYS:
            assert key not in daily.columns
        assert f._active_regressors["cafe"] == []

    def test_fit_non_sa_degrades_but_still_forecasts(self):
        from models.revenue_forecaster import RevenueForecaster
        f = RevenueForecaster()
        f.fit("cafe", _tx("cafe"), location={"location_country": "AE"})
        s = f.summaries["cafe"]
        assert s["seasonal_context_used"] is False
        # Still a complete, valid forecast — degradation, not failure
        assert s["forecast_avg_daily"] > 0
        assert "trend_direction" in s


# ── Model 2: ExpenseEstimator — location (rent tier) enrichment ───────────────

class TestExpenseEstimatorLocation:

    @pytest.fixture(scope="class")
    def est(self):
        from models.expense_estimator import ExpenseEstimator
        return ExpenseEstimator()

    _PROFILE = {
        "ticket_size": "low", "transaction_velocity": "moderate",
        "revenue_stability": "stable", "payment_mix": "mixed",
        "nocturnal_activity": "minimal", "temporal_pattern": "distributed",
    }

    # ── enrichment present ──
    def test_high_tier_scales_overhead_up(self, est):
        base = est.estimate(dict(self._PROFILE), bid="x")
        hi   = est.estimate(dict(self._PROFILE), bid="x",
                            location={"location_district": "Al Olaya"})  # commercial tier = high
        # high tier → 1.3x on the 0.08 overhead baseline
        assert hi["breakdown"]["overhead_ratio"] == round(0.08 * 1.3, 4)
        assert hi["breakdown"]["overhead_ratio"] > base["breakdown"]["overhead_ratio"]
        assert hi["data_quality"]["location_enrichment_used"] is True
        assert hi["data_quality"]["district_rent_tier_applied"] == "high"

    def test_medium_tier_is_neutral_multiplier(self, est):
        # Al Aziziyah commercial tier = medium → 1.0x (overhead unchanged) but flagged used
        r = est.estimate(dict(self._PROFILE), bid="x",
                         location={"location_district": "Al Aziziyah"})
        assert r["breakdown"]["overhead_ratio"] == 0.08
        assert r["data_quality"]["location_enrichment_used"] is True
        assert r["data_quality"]["district_rent_tier_applied"] == "medium"

    # ── graceful degradation (absent) ──
    def test_no_location_identical_to_today(self, est):
        base = est.estimate(dict(self._PROFILE), bid="x")
        assert base["breakdown"]["overhead_ratio"] == 0.08
        # No location supplied → no enrichment keys at all
        assert "location_enrichment_used" not in base["data_quality"]
        assert "district_rent_tier_applied" not in base["data_quality"]

    def test_unknown_district_degrades_neutral(self, est):
        base = est.estimate(dict(self._PROFILE), bid="x")
        r    = est.estimate(dict(self._PROFILE), bid="x",
                            location={"location_district": "Nowhereville"})
        # Unknown district → neutral overhead, transparent used=False, tier=null
        assert r["breakdown"]["overhead_ratio"] == base["breakdown"]["overhead_ratio"]
        assert r["total_expense_ratio"] == base["total_expense_ratio"]
        assert r["data_quality"]["location_enrichment_used"] is False
        assert r["data_quality"]["district_rent_tier_applied"] is None


# ── LocationContext: honest market-gap logic (evidence + unknown case) ────────

class TestCompetitorDensityHonesty:

    @pytest.fixture(scope="class")
    def loc(self):
        from data.location_context import LocationContext
        return LocationContext()

    def test_data_absent_returns_unknown_not_underserved(self, loc):
        # Known district, business type with NO seeded entry → unknown, not a gap
        r = loc.get_competitor_density("Al Olaya", "florist")
        assert r["density_tier"] == "unknown"
        assert r["market_gap_flag"] is False
        assert "insufficient reference data" in r["evidence"]

    def test_unknown_district_returns_unknown(self, loc):
        r = loc.get_competitor_density("Nowhereville", "cafe")
        assert r["density_tier"] == "unknown"
        assert r["market_gap_flag"] is False
        assert r["similar_businesses_in_district"] is None

    def test_underserved_is_backed_by_a_real_count(self, loc):
        r = loc.get_competitor_density("Al Naseem", "minimarket")
        assert r["density_tier"] == "underserved"
        assert r["market_gap_flag"] is True
        assert r["similar_businesses_in_district"] == 2      # genuine low count
        assert "2 similar" in r["evidence"]

    def test_saturated_is_backed_by_a_real_count(self, loc):
        r = loc.get_competitor_density("Al Olaya", "cafe")
        assert r["density_tier"] == "saturated"
        assert r["market_gap_flag"] is False
        assert r["similar_businesses_in_district"] == 9


# ── Model 1: BusinessClassifier — registration / license cross-check ──────────

REG_CONSISTENT_CAFE = {"license_category": "food_beverage", "license_status": "active",
                       "registration_date": "2021-05-10", "registration_number": "1010556677"}
# Laundromat DECLARED under a food_beverage license → inconsistent with its
# services-personal transaction fingerprint.
REG_INCONSISTENT_LAUNDRY = {"license_category": "food_beverage", "license_status": "active",
                            "registration_date": "2020-08-05"}

class TestClassifierLicenseCrossCheck:

    @pytest.fixture(scope="class")
    def clf(self):
        from models.business_classifier import BusinessClassifier
        c = BusinessClassifier()
        c.load()
        return c

    # ── enrichment present ──
    def test_consistent_license_keeps_inference(self, clf):
        r = clf.classify_from_data(_tx("cafe"), bid="cafe", registration=REG_CONSISTENT_CAFE)
        assert r["license_cross_check"] == "consistent"
        assert r["business_type"] == "cafe"
        assert r["type_source"] == "inference"
        assert r["data_quality"]["registration_enrichment_used"] is True
        assert r["data_quality"]["license_cross_check_result"] == "consistent"

    def test_inconsistent_license_becomes_ground_truth(self, clf):
        r = clf.classify_from_data(_tx("laundromat"), bid="laundromat",
                                   registration=REG_INCONSISTENT_LAUNDRY)
        assert r["license_cross_check"] == "inconsistent"
        # License is ground truth → business_type overridden to license-implied type
        assert r["type_source"] == "license"
        assert r["business_type"] == "cafe"                      # food_beverage → cafe
        assert r["inferred_type_before_license"] == "laundromat"  # inference preserved
        assert r["data_quality"]["license_cross_check_result"] == "inconsistent"

    # ── graceful degradation (absent) ──
    def test_no_registration_identical_to_today(self, clf):
        r = clf.classify_from_data(_tx("cafe"), bid="cafe")
        assert "business_type" not in r
        assert "type_source" not in r
        assert "license_cross_check" not in r
        assert "registration_enrichment_used" not in r["data_quality"]

    def test_registration_without_license_category_degrades(self, clf):
        r = clf.classify_from_data(_tx("cafe"), bid="cafe",
                                   registration={"registration_number": "1010000000"})
        assert r["data_quality"]["registration_enrichment_used"] is False
        assert r["data_quality"]["license_cross_check_result"] is None
        assert "license_cross_check" not in r        # nothing fabricated


# ── Model 3: FraudDetector — registration (age + license status) signals ──────

class TestFraudRegistration:

    @pytest.fixture(scope="class")
    def det(self):
        from models.fraud_detector import FraudDetector
        d = FraudDetector()
        d.load()
        return d

    # ── enrichment present ──
    def test_new_business_high_volume_flag_fires(self, det):
        reg = {"license_category": "retail_specialty", "license_status": "active",
               "registration_date": "2025-03-15"}   # < 180d before the data window
        rep = det.assess("cardealer", location=LOC_RAWABI, registration=reg)
        assert rep["data_quality"]["registration_enrichment_used"] is True
        assert rep["data_quality"]["new_business_high_volume_flag"] is True
        assert rep["registration_context"]["business_age_days"] < 180
        assert "new_business_high_volume" in [r["condition"] for r in rep["reasons"]]

    def test_license_status_flag_fires(self, det):
        reg = {"license_category": "food_beverage", "license_status": "expired",
               "registration_date": "2019-01-01"}
        rep = det.assess("cafe", registration=reg)
        assert rep["data_quality"]["license_status_flag"] is True
        assert "license_status_flag" in [r["condition"] for r in rep["reasons"]]

    # ── graceful degradation (absent) ──
    def test_no_registration_identical_to_today(self, det):
        base = det.assess("cardealer")
        assert "registration_context" not in base
        assert "registration_enrichment_used" not in base["data_quality"]
        assert "new_business_high_volume_flag" not in base["data_quality"]

    def test_old_active_business_no_flags(self, det):
        reg = {"license_category": "food_beverage", "license_status": "active",
               "registration_date": "2015-01-01"}   # old + active + no district scale
        rep = det.assess("cafe", registration=reg)
        assert rep["data_quality"]["registration_enrichment_used"] is True
        assert rep["data_quality"]["new_business_high_volume_flag"] is False
        assert rep["data_quality"]["license_status_flag"] is False


# ── license_taxonomy mapping stability ────────────────────────────────────────

def test_license_taxonomy_mapping_is_stable():
    from data.license_taxonomy import (
        get_expected_business_types, is_type_consistent_with_license,
        business_type_to_license_category, archetype_label_to_business_type)
    assert get_expected_business_types("food_beverage") == ["cafe", "restaurant"]
    assert get_expected_business_types("retail_general") == ["minimarket", "supermarket"]
    assert is_type_consistent_with_license("cafe", "food_beverage") is True
    assert is_type_consistent_with_license("laundromat", "food_beverage") is False
    assert is_type_consistent_with_license("auto_gallery", "retail_specialty") is True
    # "other" / unknown categories can never be contradicted
    assert is_type_consistent_with_license("cafe", "other") is True
    assert is_type_consistent_with_license("cafe", "banana") is True
    assert business_type_to_license_category("minimarket") == "retail_general"
    assert archetype_label_to_business_type("high_freq_low_ticket_food") == "cafe"
    assert archetype_label_to_business_type("low_ticket_steady_essential") == "laundromat"


# ── Cross-model: Rawabi combines existing + district-scale signal ─────────────

def test_rawabi_combines_existing_and_district_signal():
    from models.fraud_detector import FraudDetector
    d = FraudDetector()
    d.load()
    rep = d.assess("cardealer", location=LOC_RAWABI)

    # Existing behavioral signal is present (Rawabi flags on large-ticket outliers)
    assert rep["anomalies_detected"] > 0
    reason_conditions = [r["condition"] for r in rep.get("reasons", [])]
    existing = [c for c in reason_conditions if c != "district_scale_anomaly"]
    assert existing, "expected at least one pre-existing (behavioral/amount) fraud reason"

    # New district-scale signal is present AND combined (not replacing) the above
    assert rep["data_quality"]["district_scale_flag_triggered"] is True
    assert "district_scale_anomaly" in reason_conditions


def test_rawabi_stacks_four_signals_with_registration():
    """Rawabi + location + recent registration → 4 distinct stacked fraud signals."""
    from models.fraud_detector import FraudDetector
    d = FraudDetector()
    d.load()
    reg = {"license_category": "retail_specialty", "license_status": "active",
           "registration_date": "2025-03-15"}
    rep = d.assess("cardealer", location=LOC_RAWABI, registration=reg)

    conditions = {r["condition"] for r in rep.get("reasons", [])}
    expected = {"critical_amount_outlier", "high_behavioral_anomaly",
                "district_scale_anomaly", "new_business_high_volume"}
    assert expected.issubset(conditions), f"missing signals: {expected - conditions}"
    # All three enrichment flags corroborate the stack
    assert rep["data_quality"]["district_scale_flag_triggered"] is True
    assert rep["data_quality"]["new_business_high_volume_flag"] is True
