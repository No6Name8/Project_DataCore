"""
pipeline.py  --  DataCore AI Engine: Unified Pipeline Runner
Runs all 4 models in sequence for all 6 businesses and prints a full report.
Models: BusinessClassifier (1), ExpenseEstimator (2), FraudDetector (3),
        RevenueForecaster (4), DSCRModel (DSCR + fraud), DBRModel (incubator).
"""

import os, sys
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from models.business_classifier import BusinessClassifier
from models.expense_estimator   import ExpenseEstimator
from models.fraud_detector      import FraudDetector
from models.revenue_forecaster  import RevenueForecaster
from models.dscr_model          import DSCRModel
from models.dbr_model           import DBRModel

BUSINESS_IDS = ["laundromat", "cafe", "minimarket", "realestate", "cardealer", "motorbike"]
NAMES = {
    "laundromat": "Al Noor Laundromat",
    "cafe":       "Qahwa Corner Cafe",
    "minimarket": "Baraka Minimarket",
    "realestate": "Majd Real Estate",
    "cardealer":  "Rawabi Auto Gallery",
    "motorbike":  "Saqr Motorbikes",
}

W = 120

def divider(char="-"): print(char * W)
def header(title):
    print()
    print("=" * W)
    print(f"  {title}")
    print("=" * W)


def run():
    header("DATACORE  --  UNIFIED AI PIPELINE  (Models 1-4 + DSCR + DBR)")

    # ── Load saved models ─────────────────────────────────────────────────────
    print("\nLoading saved models...")
    saved = os.path.join(ROOT, "models", "saved")

    classifier = BusinessClassifier()
    classifier.load(os.path.join(saved, "business_classifier.pkl"))

    detector = FraudDetector()
    detector.load(os.path.join(saved, "fraud_detector.pkl"))

    forecaster = RevenueForecaster()
    forecaster.load(os.path.join(saved, "revenue_forecaster.pkl"))

    dscr_model = DSCRModel()   # loads classifier + estimator internally
    dbr_model  = DBRModel()
    estimator  = ExpenseEstimator()

    print("  All models loaded.\n")

    # ── Per-business processing ───────────────────────────────────────────────
    header("SECTION 1: PER-BUSINESS MODEL OUTPUTS")

    results = {}
    for bid in BUSINESS_IDS:
        print(f"\n{'-'*W}")
        print(f"  {NAMES[bid].upper()}  ({bid})")
        print(f"{'-'*W}")

        data_dir = os.path.join(ROOT, "data", "processed")
        tx = pd.read_csv(os.path.join(data_dir, f"{bid}_transactions.csv"))
        tx["timestamp"] = pd.to_datetime(tx["timestamp"])

        # Model 1: classification
        clf_result = classifier.classify_from_data(tx)
        print(f"  [Model 1 - Classifier]  cluster={clf_result['cluster_id']}  "
              f"archetype={clf_result.get('archetype_description','unknown')[:40]}  "
              f"conf={clf_result['confidence']:.2f}")

        # Model 2: expense estimation
        profile    = estimator._derive_profile(clf_result["raw_features"])
        ticket     = profile.get("ticket_size", "low")
        velocity   = profile.get("transaction_velocity", "moderate")
        active_days = clf_result["raw_features"].get("active_days_ratio", 0.9)
        holds_inv  = (
            ticket in ["high", "very_high"] and
            velocity in ["low", "very_low", "moderate"] and
            active_days >= 0.75
        ) or (
            ticket in ["mid"] and velocity in ["very_low", "low"]
        )
        exp_result = estimator.estimate_from_classifier(tx, classifier, holds_inventory=holds_inv)
        print(f"  [Model 2 - Expenses  ]  expense_ratio={exp_result['total_expense_ratio']:.3f}  "
              f"net_margin={exp_result['net_margin_estimate']:.3f}  "
              f"inventory={holds_inv}  conf={exp_result['confidence']:.2f}")
        print(f"    breakdown: COGS={exp_result['breakdown']['cogs_ratio']:.2f}  "
              f"labor={exp_result['breakdown']['labor_ratio']:.2f}  "
              f"overhead={exp_result['breakdown']['overhead_ratio']:.2f}")

        # Model 3: fraud detection
        fa = detector.assess(bid)
        print(f"  [Model 3 - Fraud     ]  status={fa['overall_status']}  "
              f"score={fa['fraud_score']}  anomalies={fa['anomalies_detected']}  "
              f"frozen={fa['approval_frozen']}")

        # Model 4: forecast
        fc_summary = forecaster.summaries[bid]
        print(f"  [Model 4 - Forecast  ]  trend={fc_summary['trend_direction']} "
              f"({fc_summary['trend_pct_change']:+.1f}%)  "
              f"avg_daily=SAR {fc_summary['forecast_avg_daily']:,.0f}  "
              f"30d_total=SAR {fc_summary['forecast_total_30d']:,.0f}")

        # DSCR (uses Model 2 internally)
        dscr_result = dscr_model.run(bid)
        dynamic     = forecaster.compute_dynamic_credit_limit(bid, dscr_result["credit_limit_sar"])
        print(f"  [DSCR               ]  score={dscr_result['dscr_score']:.4f}  "
              f"tier={dscr_result['risk_tier']}  "
              f"credit=SAR {dscr_result['credit_limit_sar']:>10,}  "
              f"dynamic=SAR {dynamic['dynamic_limit_sar']:>10,}  "
              f"rate={dscr_result['final_interest_rate']*100:.2f}%")

        results[bid] = {
            "dscr":     dscr_result,
            "dynamic":  dynamic,
            "fraud":    fa,
            "forecast": fc_summary,
            "expense":  exp_result,
        }

    # ── Summary table ─────────────────────────────────────────────────────────
    header("SECTION 2: SUMMARY TABLE")
    divider()
    print(f"  {'Business':<22} {'DSCR':>6} {'Risk':<10} {'Credit Limit':>13} "
          f"{'Dynamic Limit':>14} {'Rate':>6} {'Fraud':>8} {'Trend':>9} {'Margin':>7}")
    divider()
    for bid in BUSINESS_IDS:
        r  = results[bid]
        dr = r["dscr"]
        dy = r["dynamic"]
        fa = r["fraud"]
        fc = r["forecast"]
        ex = r["expense"]
        print(f"  {NAMES[bid]:<22} "
              f"{dr['dscr_score']:>6.2f} "
              f"{dr['risk_tier']:<10} "
              f"SAR {dr['credit_limit_sar']:>9,} "
              f"SAR {dy['dynamic_limit_sar']:>10,} "
              f"{dr['final_interest_rate']*100:>5.2f}% "
              f"{fa['overall_status']:>8} "
              f"{fc['trend_direction']:>9} "
              f"{ex['net_margin_estimate']:>6.1%}")
    divider()

    # ── Forecast series sample ────────────────────────────────────────────────
    header("SECTION 3: FORECAST SERIES SAMPLE  (all businesses, first 5 days)")
    for bid in BUSINESS_IDS:
        series = forecaster.get_forecast_series(bid)
        print(f"\n  {NAMES[bid]}")
        for day in series[:5]:
            print(f"    {day['date']}  SAR {day['predicted_revenue']:>10,.0f}  "
                  f"[{day['lower_bound']:>8,.0f} -- {day['upper_bound']:>10,.0f}]")

    # ── Fraud anomaly detail ──────────────────────────────────────────────────
    header("SECTION 4: FRAUD ANOMALY DETAIL")
    for bid in BUSINESS_IDS:
        fa = results[bid]["fraud"]
        status_tag = "FROZEN" if fa["approval_frozen"] else ("FLAGGED" if fa["fraud_score"] > 0 else "CLEAR")
        print(f"\n  {NAMES[bid]:<24}  [{status_tag}]  score={fa['fraud_score']}  "
              f"anomalies={fa['anomalies_detected']}")
        for a in fa["anomalies"]:
            print(f"    * {a['date']}  {a['type']:<22}  [{a['severity'].upper():<8}]  "
                  f"{a['description'][:70]}")

    # ── DBR demo ──────────────────────────────────────────────────────────────
    header("SECTION 5: DBR ASSESSMENT  (SAMA 33% cap demo)")
    scenarios = [
        ("A -- Fresh Grad (tight)",        12_000, 2_000,  40_000, 24),
        ("B -- Mid-Career (comfortable)",  25_000, 5_000,  80_000, 36),
        ("C -- Low Income (likely denied)", 8_000, 3_500,  30_000, 24),
        ("D -- High Earner (easy)",        45_000, 8_000, 200_000, 48),
    ]
    divider()
    for label, sal, ex, loan, term in scenarios:
        r      = dbr_model.assess(sal, ex, loan, term)
        status = "APPROVED" if r["approved"] else "DENIED  "
        extra  = (f"  max eligible: SAR {r['max_eligible_loan_sar']:>10,.2f}"
                  if not r["approved"] else "")
        print(f"  Scenario {label}")
        print(f"    Salary {sal:>8,}  |  Existing {ex:>6,}  |  "
              f"Loan {loan:>8,}  |  {term}m  |  "
              f"DBR {r['dbr_ratio']*100:.1f}%  |  [{status}]{extra}")
        print()

    # ── Transition readiness ──────────────────────────────────────────────────
    header("SECTION 6: INCUBATOR -> SME TRANSITION READINESS")
    divider()
    for bid in BUSINESS_IDS:
        tr  = dbr_model.transition_readiness(bid)
        tag = "READY    -> SME" if tr["ready"] else "NOT READY -> INCUBATOR"
        print(f"  {NAMES[bid]:<24}  [{tag}]")
        print(f"    {tr['reason']}")
        print()

    print("=" * W)
    print("Pipeline complete.")
    print("=" * W)


if __name__ == "__main__":
    run()
