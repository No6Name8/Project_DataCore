"""
run_models.py  --  DataCore AI Engine: Full Report Runner
Runs DSCRModel and DBRModel against all 6 businesses and prints a report.
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.dscr_model import DSCRModel
from models.dbr_model  import DBRModel

BUSINESS_IDS = ["laundromat", "cafe", "minimarket", "realestate", "cardealer", "motorbike"]
NAMES = {
    "laundromat": "Al Noor Laundromat",
    "cafe":       "Qahwa Corner Cafe",
    "minimarket": "Baraka Minimarket",
    "realestate": "Majd Real Estate",
    "cardealer":  "Rawabi Auto Gallery",
    "motorbike":  "Saqr Motorbikes",
}

W = 110

def divider(char="-"): print(char * W)

def run():
    dscr_model = DSCRModel()
    dbr_model  = DBRModel()

    print("=" * W)
    print("DATACORE  --  AI ENGINE FULL REPORT")
    print("=" * W)

    # ── DSCR table ────────────────────────────────────────────────────────────
    print()
    print("SECTION 1: DSCR ASSESSMENT  (computed live from CSV data)")
    divider()
    hdr = (f"{'Business':<24} {'Revenue (SAR)':>15} {'NOI (SAR)':>13} "
           f"{'DSCR':>7} {'Risk':<10} {'Credit Limit':>14} "
           f"{'Rate':>6} {'Sus':>4} {'Fraud':>8} {'Score':>6}")
    print(hdr)
    divider()

    results = {}
    for bid in BUSINESS_IDS:
        r  = dscr_model.run(bid)
        results[bid] = r
        fr = r["fraud_assessment"]
        print(
            f"{NAMES[bid]:<24} "
            f"{r['revenue_metrics']['total_revenue']:>15,.0f} "
            f"{r['net_operating_income']:>13,.0f} "
            f"{r['dscr_score']:>7.2f} "
            f"{r['risk_tier']:<10} "
            f"{r['credit_limit_sar']:>14,} "
            f"{r['final_interest_rate']*100:>5.2f}% "
            f"{'Yes' if r['sustainability_eligible'] else 'No ':>4} "
            f"{fr['overall_status']:>8} "
            f"{fr['fraud_score']:>6}"
        )

    # ── Fraud detail ──────────────────────────────────────────────────────────
    print()
    print("SECTION 2: FRAUD ANOMALY DETAIL")
    divider()
    for bid in BUSINESS_IDS:
        fr = results[bid]["fraud_assessment"]
        if not fr["anomalies"]:
            print(f"  {NAMES[bid]:<24}  [CLEAR]  no anomalies detected")
        else:
            print(f"  {NAMES[bid]:<24}  [{'FROZEN' if fr['approval_frozen'] else 'FLAGGED'}]  "
                  f"score={fr['fraud_score']}  anomalies={fr['anomalies_detected']}")
            for a in fr["anomalies"]:
                print(f"    * {a['date']}  {a['type']:<22}  [{a['severity'].upper()}]  {a['description'][:70]}")

    # ── DBR scenarios ─────────────────────────────────────────────────────────
    print()
    print("SECTION 3: DBR SCENARIOS  (SAMA 33% cap)")
    divider()
    scenarios = [
        ("A -- Fresh Grad (tight)",          12_000,  2_000, 40_000, 24),
        ("B -- Mid-Career (comfortable)",    25_000,  5_000, 80_000, 36),
        ("C -- Low Income (likely denied)",   8_000,  3_500, 30_000, 24),
    ]
    for label, sal, ex, loan, term in scenarios:
        r = dbr_model.assess(sal, ex, loan, term)
        status = "APPROVED" if r["approved"] else "DENIED  "
        extra  = (f"  |  max eligible: SAR {r['max_eligible_loan_sar']:>10,.2f}"
                  if not r["approved"] else "")
        print(f"  Scenario {label}")
        print(f"    Salary SAR {sal:>8,}  |  Existing SAR {ex:>6,}  |  "
              f"Loan SAR {loan:>8,}  |  {term}m  |  "
              f"DBR {r['dbr_ratio']*100:.1f}%  |  [{status}]{extra}")
        print()

    # ── Transition readiness ──────────────────────────────────────────────────
    print()
    print("SECTION 4: INCUBATOR -> SME TRANSITION READINESS")
    divider()
    for bid in BUSINESS_IDS:
        tr = dbr_model.transition_readiness(bid)
        tag = "READY    -> SME" if tr["ready"] else "NOT READY -> INCUBATOR"
        print(f"  {NAMES[bid]:<24}  [{tag}]")
        print(f"    {tr['reason']}")
        print()

    print("=" * W)
    print("Report complete.")
    print("=" * W)


if __name__ == "__main__":
    run()
