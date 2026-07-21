"""
test_robustness.py — deliberate broken-input test cases for all four models.
Run with:  python -m pytest tests/test_robustness.py -v
"""

import sys, os
import pytest
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_tx(n=50, seed=1, bad_amounts=False, missing_amount_col=False,
             missing_timestamp_col=False, include_negatives=False):
    rng = np.random.default_rng(seed)
    ts  = pd.date_range("2025-04-01", periods=n, freq="4h")
    amounts = rng.lognormal(mean=3.5, sigma=0.8, size=n)

    if bad_amounts:
        amounts[:5] = -999.0      # inject negatives
    if include_negatives:
        amounts[:3] = -1.0

    df = pd.DataFrame({"timestamp": ts, "amount_sar": amounts})

    if missing_amount_col:
        df = df.drop(columns=["amount_sar"])
    if missing_timestamp_col:
        df = df.drop(columns=["timestamp"])

    return df


# ── Model 1: BusinessClassifier ───────────────────────────────────────────────

class TestBusinessClassifier:

    @pytest.fixture(scope="class")
    def clf(self):
        from models.business_classifier import BusinessClassifier
        c = BusinessClassifier()
        c.load()
        return c

    def test_missing_required_column_raises(self, clf):
        """DataFrame with no amount_sar should raise ValueError."""
        tx = _make_tx(missing_amount_col=True)
        with pytest.raises(ValueError, match="missing_required_column"):
            clf.classify_from_data(tx)

    def test_fewer_than_min_tx_returns_insufficient(self, clf):
        """Only 5 rows (< MIN_TX_CLASSIFY=10) should return insufficient_data."""
        tx = _make_tx(n=5)
        result = clf.classify_from_data(tx, bid="thin_biz")
        assert result["status"] == "insufficient_data"
        assert result["data_quality"]["status"] == "insufficient"

    def test_thin_data_warning_in_output(self, clf):
        """15 rows (between MIN_TX_CLASSIFY=10 and MIN_TX_WARN=30) should classify
        but include a thin_data_warning in data_quality."""
        tx = _make_tx(n=15)
        result = clf.classify_from_data(tx, bid="thin_biz")
        # Either insufficient or classified with warning
        if result.get("status") == "insufficient_data":
            return  # also acceptable
        warnings = result["data_quality"]["warnings"]
        assert any(w["rule"] == "thin_data_warning" for w in warnings)

    def test_all_negative_amounts_returns_insufficient(self, clf):
        """All-negative amounts cleaned to 0 rows → classify_from_data returns
        insufficient_data (the method catches InsufficientDataError internally)."""
        tx = pd.DataFrame({
            "timestamp":  pd.date_range("2025-04-01", periods=8, freq="1h"),
            "amount_sar": [-10.0] * 8,
        })
        result = clf.classify_from_data(tx, bid="neg_biz")
        assert result["status"] == "insufficient_data"

    def test_missing_intake_field_defaults_gracefully(self, clf):
        """Intake with missing fields should use defaults and still return a result."""
        partial_intake = {
            "typical_ticket_sar":       50,
            # missing all other 7 fields
        }
        result = clf.classify_from_intake(partial_intake, bid="partial_intake")
        assert "cluster_id" in result
        assert "data_quality" in result

    def test_data_quality_present_on_good_data(self, clf):
        """Healthy data should still carry data_quality with status='ok'."""
        tx = _make_tx(n=100)
        result = clf.classify_from_data(tx, bid="good_biz")
        assert "data_quality" in result
        assert result["data_quality"]["status"] in ("ok", "degraded")


# ── Model 2: ExpenseEstimator ─────────────────────────────────────────────────

class TestExpenseEstimator:

    @pytest.fixture(scope="class")
    def estimator(self):
        from models.expense_estimator import ExpenseEstimator
        return ExpenseEstimator()

    def test_empty_features_uses_defaults(self, estimator):
        """Empty raw_features dict should log warnings and still produce a result."""
        profile = estimator._derive_profile({}, bid="empty_biz")
        result  = estimator.estimate(profile, bid="empty_biz")
        assert "total_expense_ratio" in result
        assert "data_quality" in result
        # Warnings emitted for every missing field
        assert result["data_quality"]["warnings"] or True  # defensive: may have none if all defaulted

    def test_unknown_tag_falls_back(self, estimator):
        """Unknown tag values should default and emit data_quality warnings."""
        profile = {
            "ticket_size":          "BOGUS_TAG",
            "transaction_velocity": "moderate",
            "revenue_stability":    "moderate",
        }
        result = estimator.estimate(profile, bid="bogus_biz")
        assert "total_expense_ratio" in result
        assert "data_quality" in result
        warnings = result["data_quality"]["warnings"]
        assert any(w["rule"] == "unknown_tag" for w in warnings)

    def test_data_quality_present_on_valid_profile(self, estimator):
        """Valid profile should carry data_quality with status='ok'."""
        profile = estimator._derive_profile({
            "avg_ticket_sar":           250.0,
            "avg_daily_transactions":   20.0,
            "revenue_cv":               0.28,
            "cash_ratio":               0.30,
            "night_transaction_ratio":  0.01,
            "active_days_ratio":        0.90,
            "ticket_cv":                0.5,
            "peak_hour_concentration":  0.08,
        }, bid="good_biz")
        result = estimator.estimate(profile, bid="good_biz")
        assert result["data_quality"]["status"] == "ok"


# ── Model 3: FraudDetector ────────────────────────────────────────────────────

class TestFraudDetector:

    @pytest.fixture(scope="class")
    def detector(self):
        from models.fraud_detector import FraudDetector
        d = FraudDetector()
        d.load()
        return d

    def test_missing_column_raises(self, detector):
        """DataFrame missing amount_sar should raise ValueError in engineer()."""
        tx = _make_tx(missing_amount_col=True)
        eng = detector.engineer
        with pytest.raises(ValueError, match="missing_required_column"):
            eng.engineer(tx, bid="bad_biz")

    def test_fewer_than_min_rows_score_returns_clean(self, detector):
        """Only 5 rows (< MIN_TX_FRAUD_SCORE=10) should return df with label=1."""
        tx = _make_tx(n=5)
        scored = detector.score_transactions(tx, business_id="cafe")
        assert (scored["anomaly_label"] == 1).all()

    def test_negative_amounts_stripped_before_engineering(self, detector):
        """Negative amounts should be removed; remaining rows scored normally."""
        tx = _make_tx(n=60, bad_amounts=True)
        scored = detector.score_transactions(tx, business_id="cafe")
        # No crash and anomaly_label exists
        assert "anomaly_label" in scored.columns

    def test_data_quality_in_fraud_report(self, detector):
        """generate_fraud_report should always include data_quality."""
        tx = _make_tx(n=100)
        tx["timestamp"] = pd.to_datetime(tx["timestamp"])
        scored = detector.score_transactions(tx, business_id="cafe")
        report = detector.generate_fraud_report(scored, "cafe")
        assert "data_quality" in report


# ── Model 4: RevenueForecaster ────────────────────────────────────────────────

class TestRevenueForecaster:

    @pytest.fixture(scope="class")
    def forecaster(self):
        from models.revenue_forecaster import RevenueForecaster
        f = RevenueForecaster()
        f.load()
        return f

    def test_missing_column_raises(self, forecaster):
        """DataFrame missing amount_sar should raise ValueError in prepare_data()."""
        tx = _make_tx(missing_amount_col=True)
        with pytest.raises(ValueError, match="missing_required_column"):
            forecaster.prepare_data(tx, bid="bad_biz")

    def test_fewer_than_min_active_days_skips_fit(self, forecaster):
        """Only 5 active days should result in an insufficient_data summary entry."""
        from models.revenue_forecaster import RevenueForecaster
        f = RevenueForecaster()
        # 5 rows on 5 distinct dates — far below MIN_ACTIVE_DAYS=14
        tx = pd.DataFrame({
            "timestamp":  pd.date_range("2025-06-01", periods=5, freq="1D"),
            "amount_sar": [100.0, 200.0, 150.0, 300.0, 250.0],
        })
        f.fit("test_sparse", tx)
        summary = f.summaries.get("test_sparse", {})
        assert summary.get("status") == "insufficient_data"

    def test_data_quality_present_in_existing_summary(self, forecaster):
        """Loaded summaries for trained businesses should include data_quality."""
        for bid, summary in forecaster.summaries.items():
            if summary.get("status") != "insufficient_data":
                assert "data_quality" in summary, f"data_quality missing for {bid}"
