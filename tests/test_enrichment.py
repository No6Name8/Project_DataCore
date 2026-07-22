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
