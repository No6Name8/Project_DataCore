"""
test_counterparty_enrichment.py — 4th enrichment layer (counterparty/supplier).

Covers the forgiving normalization utility, the classifier supplier_profile
(coverage-gated), the fraud instability + concentration flags (business-type
aware), Rawabi's six-signal stack, and byte-identical behaviour when the
counterparty_raw column is absent.

Run:  python -m pytest tests/test_counterparty_enrichment.py -v
"""

import sys, os
import pytest
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DATA_DIR = os.path.join(ROOT, "data", "processed")

LOC_RAWABI = {"location_district": "Al Batha", "location_city": "Riyadh"}


def _tx(bid):
    tx = pd.read_csv(os.path.join(DATA_DIR, f"{bid}_transactions.csv"))
    tx["timestamp"] = pd.to_datetime(tx["timestamp"])
    return tx


def _tx_with_counterparty(n=60, coverage=1.0, names=None, seed=1):
    rng = np.random.default_rng(seed)
    ts  = pd.date_range("2025-04-01", periods=n, freq="4h")
    amt = rng.lognormal(mean=3.5, sigma=0.8, size=n)
    names = names or ["STARBUCKS #1", "ALMARAI 22", "SADAD BILL 33", "STC 44", "TAMIMI 55"]
    cp = [names[i % len(names)] if rng.random() < coverage else "" for i in range(n)]
    return pd.DataFrame({"timestamp": ts, "amount_sar": amt, "counterparty_raw": cp})


def _tx_counterparty_sequence(seq):
    n = len(seq)
    ts  = pd.date_range("2025-04-01", periods=n, freq="2h")
    amt = np.linspace(40, 60, n)
    return pd.DataFrame({"timestamp": ts, "amount_sar": amt, "counterparty_raw": list(seq)})


# ── Normalization utility (forgiving, never crashes) ──────────────────────────

class TestCounterpartyNormalization:

    def _u(self):
        import data.counterparty_utils as u
        return u

    def test_ascii_merchant_with_pos_noise(self):
        u = self._u()
        assert u.counterparty_fingerprint("STARBUCKS #4421") == "starbucks"
        assert u.counterparty_fingerprint("STARBUCKS 8271") == "starbucks"
        assert u.classify_counterparty_kind("STARBUCKS #4421") == "merchant"

    def test_arabic_only_preserved_not_crashed(self):
        u = self._u()
        fp = u.counterparty_fingerprint("شركة الراجحي للتجارة")
        assert fp != ""
        assert "الراجحي" in fp
        assert u.classify_counterparty_kind("شركة الراجحي للتجارة") == "merchant"

    def test_mixed_arabic_english_handled(self):
        u = self._u()
        raw = "POS PURCHASE 8271 شركة النخيل RIYADH"
        assert isinstance(u.normalize_counterparty(raw), str)   # no crash
        assert u.counterparty_fingerprint(raw) != ""

    def test_empty_and_whitespace_return_empty(self):
        u = self._u()
        for raw in ["", "   ", None, "nan"]:
            assert u.normalize_counterparty(raw) == ""
            assert u.counterparty_fingerprint(raw) == ""
            assert u.classify_counterparty_kind(raw) == "unknown"

    def test_sadad_and_utility_classified(self):
        u = self._u()
        assert u.classify_counterparty_kind("SADAD BILL PAYMENT 8827162") == "utility"
        assert u.classify_counterparty_kind("STC INVOICE 4471") == "utility"
        assert u.classify_counterparty_kind("SEC ELECTRICITY BILL 22") == "utility"

    def test_government_classified(self):
        u = self._u()
        assert u.classify_counterparty_kind("GAZT ZATCA VAT PAYMENT") == "government"
        assert u.classify_counterparty_kind("MOI TRAFFIC FINE 88") == "government"

    def test_internal_transfer_classified(self):
        u = self._u()
        assert u.classify_counterparty_kind("TRF FROM 1234567890") == "bank_internal"
        assert u.classify_counterparty_kind("TRANSFER TO 998 INTERNAL") == "bank_internal"

    def test_unrecognized_noise_is_unknown(self):
        u = self._u()
        assert u.classify_counterparty_kind("998877") == "unknown"
        assert u.classify_counterparty_kind("#@!!") == "unknown"


# ── Classifier: supplier_profile generation vs coverage ───────────────────────

class TestClassifierSupplierProfile:

    @pytest.fixture(scope="class")
    def clf(self):
        from models.business_classifier import BusinessClassifier
        c = BusinessClassifier()
        c.load()
        return c

    def test_profile_generated_on_demo_business(self, clf):
        r = clf.classify_from_data(_tx("cafe"), bid="cafe")
        assert r["data_quality"]["supplier_profile_generated"] is True
        assert r["data_quality"]["counterparty_coverage_pct"] >= 20.0
        sp = r["supplier_profile"]
        assert sp["distinct_suppliers_count"] > 0
        assert isinstance(sp["top_supplier_fingerprints"], list)
        assert isinstance(sp["supplier_kind_distribution"], dict)

    def test_profile_generated_on_synthetic_full_coverage(self, clf):
        tx = _tx_with_counterparty(n=80, coverage=1.0)
        r = clf.classify_from_data(tx, bid="synthetic")
        assert r["data_quality"]["supplier_profile_generated"] is True
        assert "supplier_profile" in r

    def test_profile_not_generated_below_threshold(self, clf):
        tx = _tx_with_counterparty(n=100, coverage=0.10, seed=3)
        r = clf.classify_from_data(tx, bid="thin_cp")
        assert r["data_quality"]["supplier_profile_generated"] is False
        assert "supplier_profile" not in r
        assert r["data_quality"]["counterparty_coverage_pct"] < 20.0

    def test_coverage_reported_even_when_sparse(self, clf):
        tx = _tx_with_counterparty(n=100, coverage=0.05, seed=7)
        r = clf.classify_from_data(tx, bid="very_thin_cp")
        assert "counterparty_coverage_pct" in r["data_quality"]
        assert r["data_quality"]["supplier_profile_generated"] is False

    def test_no_counterparty_column_identical(self, clf):
        tx = _tx("cafe").drop(columns=["counterparty_raw"])
        r = clf.classify_from_data(tx, bid="cafe")
        assert "supplier_profile" not in r
        assert "counterparty_enrichment_used" not in r["data_quality"]


# ── Fraud: instability + concentration flags ──────────────────────────────────

class TestFraudCounterparty:

    @pytest.fixture(scope="class")
    def det(self):
        from models.fraud_detector import FraudDetector
        d = FraudDetector()
        d.load()
        return d

    def test_instability_flag_fires_on_erratic_new_suppliers(self, det):
        seq = ["STEADY SUPPLIER 1"] * 70 + [f"NEW PAYEE {i}" for i in range(30)]
        rep = det.assess("cafe", transactions_df=_tx_counterparty_sequence(seq),
                         business_type="cafe")
        assert rep["data_quality"]["supplier_instability_flag"] is True
        assert rep["data_quality"]["supplier_instability_ratio"] > 0.40

    def test_instability_flag_quiet_on_stable_suppliers(self, det):
        names = ["SUPPLIER A", "SUPPLIER B", "SUPPLIER C"]
        seq = [names[i % 3] for i in range(120)]
        rep = det.assess("cafe", transactions_df=_tx_counterparty_sequence(seq),
                         business_type="cafe")
        assert rep["data_quality"]["supplier_instability_flag"] is False

    def test_concentration_flag_fires_for_unexpected_type(self, det):
        seq = ["ONE BIG SUPPLIER"] * 95 + [f"OTHER {i}" for i in range(5)]
        rep = det.assess("cafe", transactions_df=_tx_counterparty_sequence(seq),
                         business_type="minimarket")
        assert rep["data_quality"]["top_concentration_ratio"] > 0.90
        assert rep["data_quality"]["counterparty_concentration_flag"] is True

    def test_concentration_expected_for_real_estate_no_flag(self, det):
        seq = ["ONE PROPERTY MANAGER"] * 95 + [f"OTHER {i}" for i in range(5)]
        rep = det.assess("cafe", transactions_df=_tx_counterparty_sequence(seq),
                         business_type="realestate")
        assert rep["data_quality"]["top_concentration_ratio"] > 0.90
        assert rep["data_quality"]["counterparty_concentration_flag"] is False

    def test_no_counterparty_column_identical(self, det):
        synth = pd.DataFrame({
            "timestamp": pd.date_range("2025-04-01", periods=60, freq="4h"),
            "amount_sar": np.random.default_rng(1).lognormal(3.5, 0.8, 60),
        })
        rep = det.assess("cafe", transactions_df=synth)
        assert "counterparty_context" not in rep
        assert not any(k.startswith("counterparty") or k.startswith("supplier")
                       for k in rep["data_quality"])


# ── Cross-model: Rawabi now stacks SIX signals ────────────────────────────────

def test_rawabi_stacks_six_signals():
    from models.fraud_detector import FraudDetector
    d = FraudDetector()
    d.load()
    reg = {"license_category": "retail_specialty", "license_status": "active",
           "registration_date": "2025-03-15"}
    rep = d.assess("cardealer", location=LOC_RAWABI, registration=reg,
                   business_type="cardealer")
    conditions = {r["condition"] for r in rep.get("reasons", [])}
    expected = {"critical_amount_outlier", "high_behavioral_anomaly",
                "district_scale_anomaly", "new_business_high_volume",
                "supplier_instability", "counterparty_concentration"}
    assert expected.issubset(conditions), f"missing: {expected - conditions}"
    assert rep["data_quality"]["supplier_instability_flag"] is True
    assert rep["data_quality"]["counterparty_concentration_flag"] is True
