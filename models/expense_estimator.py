"""
expense_estimator.py  --  DataCore AI Engine: Model 2
Derives expense ratios from behavioral profiles.
Replaces all hardcoded EXPENSE_RATIOS. Zero hardcoded business-type labels.
"""

import os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class ExpenseEstimator:

    def __init__(self):
        # COGS lookup by ticket_size tag
        self.cogs_by_ticket = {
            "very_low":  0.55,   # product-heavy, razor-thin margins
            "low":       0.45,   # mixed product/service
            "mid":       0.30,   # more service than product
            "high":      0.15,   # asset or high-value service
            "very_high": 0.08,   # asset sale (COGS already in vehicle/property price)
        }

        # Labor lookup by transaction_velocity tag
        self.labor_by_velocity = {
            "very_high": 0.22,   # needs large staff to handle volume
            "high":      0.18,
            "moderate":  0.12,
            "low":       0.07,
            "very_low":  0.04,   # minimal staff, appointment-based
        }

        # Stability adjustment by revenue_stability tag
        self.stability_adjustment = {
            "very_stable":    -0.02,   # predictable = more efficient deployment
            "stable":          0.00,
            "moderate":        0.01,
            "volatile":        0.03,   # needs larger buffer
            "highly_volatile": 0.06,   # maximum buffer needed
        }

        self.overhead  = 0.08    # flat for all businesses
        self.min_ratio = 0.25    # floor — no business runs on <25% expenses
        self.max_ratio = 0.92    # ceiling — no viable business spends >92%

    # ── Tag derivation ────────────────────────────────────────────────────────

    def _derive_profile(self, raw_features: dict,
                        profile_source: str = "real_data",
                        is_outlier: bool = False) -> dict:
        """
        Maps the 15-dim raw feature dict from Model 1 into behavioral tags
        consumed by estimate(). Called by estimate_from_classifier/intake.
        """
        avg_ticket = raw_features.get("avg_ticket_sar", 100.0)
        daily_tx   = raw_features.get("avg_daily_transactions", 20.0)
        rev_cv     = raw_features.get("revenue_cv", 0.30)
        cash_ratio = raw_features.get("cash_ratio", 0.30)
        night      = raw_features.get("night_transaction_ratio", 0.01)

        # Ticket size → COGS proxy
        if   avg_ticket < 50:      ticket_size = "very_low"
        elif avg_ticket < 500:     ticket_size = "low"
        elif avg_ticket < 5_000:   ticket_size = "mid"
        elif avg_ticket < 50_000:  ticket_size = "high"
        else:                      ticket_size = "very_high"

        # Daily transactions → labor demand proxy
        if   daily_tx >= 150:  velocity_tag = "very_high"
        elif daily_tx >= 50:   velocity_tag = "high"
        elif daily_tx >= 10:   velocity_tag = "moderate"
        elif daily_tx >= 3:    velocity_tag = "low"
        else:                  velocity_tag = "very_low"

        # Revenue CV → stability tag
        if   rev_cv < 0.15:  stability_tag = "very_stable"
        elif rev_cv < 0.25:  stability_tag = "stable"
        elif rev_cv < 0.40:  stability_tag = "moderate"
        elif rev_cv < 0.80:  stability_tag = "volatile"
        else:                stability_tag = "highly_volatile"

        # Cash ratio → payment mix tag
        if   cash_ratio >= 0.35:  payment_mix = "cash_heavy"
        elif cash_ratio < 0.15:   payment_mix = "digital_heavy"
        else:                     payment_mix = "mixed"

        # Night ratio → nocturnal tag
        if   night >= 0.05:  nocturnal = "high"
        elif night >= 0.02:  nocturnal = "moderate"
        else:                nocturnal = "minimal"

        return {
            "ticket_size":          ticket_size,
            "transaction_velocity": velocity_tag,
            "revenue_stability":    stability_tag,
            "payment_mix":          payment_mix,
            "nocturnal_activity":   nocturnal,
            "profile_source":       profile_source,
            "is_outlier":           is_outlier,
        }

    # ── Core estimate ─────────────────────────────────────────────────────────

    def estimate(self, behavioral_profile: dict) -> dict:
        """
        Derives an expense ratio from behavioral tags.
        Input dict must contain: ticket_size, transaction_velocity,
        revenue_stability. Optional: payment_mix, nocturnal_activity,
        profile_source, is_outlier.
        """
        ticket_size  = behavioral_profile.get("ticket_size",          "low")
        velocity_tag = behavioral_profile.get("transaction_velocity",  "moderate")
        stability_tag = behavioral_profile.get("revenue_stability",    "moderate")
        payment_mix  = behavioral_profile.get("payment_mix",          "mixed")
        nocturnal    = behavioral_profile.get("nocturnal_activity",    "minimal")
        profile_src  = behavioral_profile.get("profile_source",       "real_data")
        is_outlier   = behavioral_profile.get("is_outlier",           False)

        cogs_ratio  = self.cogs_by_ticket.get(ticket_size, 0.35)
        labor_ratio = self.labor_by_velocity.get(velocity_tag, 0.12)
        stab_adj    = self.stability_adjustment.get(stability_tag, 0.01)

        # Payment mix adjustment: cash handling raises labor cost
        if payment_mix == "cash_heavy":
            labor_ratio += 0.03

        # Nocturnal adjustment: night shifts require extra staffing
        if   nocturnal == "high":     labor_ratio += 0.04
        elif nocturnal == "moderate": labor_ratio += 0.02

        total = cogs_ratio + labor_ratio + self.overhead + stab_adj
        total = float(np.clip(total, self.min_ratio, self.max_ratio))

        # Breakdown reflects all adjustments
        adjusted_labor = labor_ratio + (stab_adj if stab_adj > 0 else 0)

        # Confidence: start at 0.85, apply penalties
        confidence = 0.85
        if profile_src == "intake_form":  confidence *= 0.75
        if is_outlier:                    confidence *= 0.70
        if stability_tag == "highly_volatile": confidence *= 0.90
        confidence = float(np.clip(confidence, 0.30, 0.95))

        return {
            "total_expense_ratio": round(total, 4),
            "breakdown": {
                "cogs_ratio":     round(cogs_ratio, 4),
                "labor_ratio":    round(adjusted_labor, 4),
                "overhead_ratio": self.overhead,
                "stability_adj":  round(stab_adj, 4),
            },
            "net_margin_estimate": round(1.0 - total, 4),
            "confidence":          round(confidence, 4),
            "tags_used": {
                "ticket_size":          ticket_size,
                "transaction_velocity": velocity_tag,
                "revenue_stability":    stability_tag,
                "payment_mix":          payment_mix,
                "nocturnal_activity":   nocturnal,
            },
            "derived_from":  "behavioral_profile",
            "profile_source": profile_src,
        }

    # ── Full pipeline: real transaction data ──────────────────────────────────

    def estimate_from_classifier(self, transactions_df, classifier) -> dict:
        """Full pipeline: classify business then estimate expenses."""
        result  = classifier.classify_from_data(transactions_df)
        profile = self._derive_profile(
            result["raw_features"],
            profile_source=result.get("profile_source", "real_data"),
            is_outlier=result.get("was_noise", False),
        )
        expense = self.estimate(profile)
        expense["profile_source"]            = result.get("profile_source", "real_data")
        expense["cluster_id"]                = result["cluster_id"]
        expense["archetype"]                 = result.get(
            "archetype_description", result.get("archetype_label", "unknown"))
        expense["classification_confidence"] = result["confidence"]
        return expense

    # ── Full pipeline: intake form ────────────────────────────────────────────

    def estimate_from_intake(self, intake_dict: dict, classifier) -> dict:
        """For new businesses using intake form."""
        result  = classifier.classify_from_intake(intake_dict)
        profile = self._derive_profile(
            result["raw_features"],
            profile_source="intake_form",
            is_outlier=result.get("is_outlier", False),
        )
        expense = self.estimate(profile)
        expense["profile_source"]  = "intake_form"
        expense["confidence"]     *= 0.75   # additional intake penalty
        expense["confidence"]      = round(
            float(np.clip(expense["confidence"], 0.30, 0.95)), 4)
        expense["archetype"]       = result.get("archetype_description", "unknown")
        return expense


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import pandas as pd

    print("=" * 60)
    print("DATACORE -- Expense Estimator Model 2")
    print("=" * 60)

    from models.business_classifier import BusinessClassifier
    from models.dscr_model import DSCRModel, EXPENSE_RATIOS

    clf       = BusinessClassifier()
    clf.load()
    estimator = ExpenseEstimator()

    print("\n" + "=" * 60)
    print("MODEL 2 vs HARDCODED -- comparison")
    print("=" * 60)
    print(f"{'Business':<14} {'Hardcoded':>10} {'AI-Derived':>10} "
          f"{'Diff':>8} {'Confidence':>11} {'Source'}")
    print("-" * 70)

    businesses = ["laundromat", "cafe", "minimarket",
                  "realestate", "cardealer", "motorbike"]

    for biz in businesses:
        tx = pd.read_csv(os.path.join(ROOT, "data", f"{biz}_transactions.csv"))
        tx["timestamp"] = pd.to_datetime(tx["timestamp"])

        result   = estimator.estimate_from_classifier(tx, clf)
        ai_ratio = result["total_expense_ratio"]
        hc_ratio = EXPENSE_RATIOS[biz]
        diff     = ai_ratio - hc_ratio

        print(f"{biz:<14} {hc_ratio:>10.3f} {ai_ratio:>10.3f} "
              f"{diff:>+8.3f} {result['confidence']:>10.2f}  "
              f"{result['archetype'][:25]}")

    print("\n" + "=" * 60)
    print("FULL DSCR WITH MODEL 2 -- live run")
    print("=" * 60)

    dscr = DSCRModel()
    for biz in businesses:
        r = dscr.run(biz)
        print(f"\n{biz.upper()}")
        print(f"  Expense ratio  : {r['expense_ratio']:.3f} ({r['expense_source']})")
        print(f"  Breakdown      : COGS {r['expense_breakdown']['cogs_ratio']:.2f} | "
              f"Labor {r['expense_breakdown']['labor_ratio']:.2f} | "
              f"Overhead {r['expense_breakdown']['overhead_ratio']:.2f}")
        print(f"  NOI            : SAR {r['net_operating_income']:>12,.0f}")
        print(f"  DSCR           : {r['dscr_score']:.4f} ({r['risk_tier']})")
        print(f"  Credit limit   : SAR {r['credit_limit_sar']:>12,.0f}")
        print(f"  Model 2 conf   : {r['model2_confidence']:.2f}")

    print("\n" + "=" * 60)
    print("INTAKE FORM TEST -- new businesses")
    print("=" * 60)

    test_intakes = [
        ("Shawarma Shop", {
            "typical_ticket_sar":        28,
            "expected_daily_customers":  85,
            "operating_hours_per_day":   14,
            "is_consumer_facing":        True,
            "sells_high_value_items":    False,
            "expected_payment_mix":      "mixed",
            "operates_late_night":       True,
            "business_days_per_week":    7,
        }),
        ("Dental Clinic", {
            "typical_ticket_sar":        420,
            "expected_daily_customers":  18,
            "operating_hours_per_day":   9,
            "is_consumer_facing":        True,
            "sells_high_value_items":    False,
            "expected_payment_mix":      "mostly_digital",
            "operates_late_night":       False,
            "business_days_per_week":    6,
        }),
    ]

    for name, intake in test_intakes:
        result = estimator.estimate_from_intake(intake, clf)
        print(f"\n{name}")
        print(f"  Expense ratio : {result['total_expense_ratio']:.3f}")
        print(f"  Breakdown     : COGS {result['breakdown']['cogs_ratio']:.2f} | "
              f"Labor {result['breakdown']['labor_ratio']:.2f} | "
              f"Overhead {result['breakdown']['overhead_ratio']:.2f}")
        print(f"  Net margin    : {result['net_margin_estimate']:.1%}")
        print(f"  Confidence    : {result['confidence']:.2f}")
        print(f"  Archetype     : {result.get('archetype', 'unknown')}")

    print("\n" + "=" * 60)
    print("Model 2 complete.")
    print("=" * 60)
