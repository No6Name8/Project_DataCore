"""
dbr_model.py  --  DataCore Incubator Pipeline: DBR Assessment
Implements SAMA 33% DBR cap and SME transition readiness checks.
"""

import os, sys
import pandas as pd

ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "processed")
sys.path.insert(0, ROOT)

ALL_DATES = pd.date_range("2025-06-01", "2025-06-30").strftime("%Y-%m-%d").tolist()


class DBRModel:

    SAMA_CAP = 0.33   # SAMA's maximum allowed DBR for retail banking

    # ── DBR assessment ────────────────────────────────────────────────────────

    def assess(self, monthly_salary, existing_obligations, requested_loan,
               loan_term_months, include_interest=False, annual_rate=0.065):

        if include_interest:
            r = annual_rate / 12
            n = loan_term_months
            monthly_payment = requested_loan * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
        else:
            # Seed loan: simplified, no interest
            monthly_payment = requested_loan / loan_term_months

        monthly_payment = round(monthly_payment, 2)
        total_oblig     = round(existing_obligations + monthly_payment, 2)
        dbr_ratio       = round(total_oblig / monthly_salary, 4)
        approved        = dbr_ratio <= self.SAMA_CAP

        max_allowed_pmt = monthly_salary * self.SAMA_CAP - existing_obligations

        if not approved:
            if include_interest and max_allowed_pmt > 0:
                r = annual_rate / 12
                n = loan_term_months
                max_loan = max_allowed_pmt * ((1 + r) ** n - 1) / (r * (1 + r) ** n)
            elif max_allowed_pmt > 0:
                max_loan = max_allowed_pmt * loan_term_months
            else:
                max_loan = 0.0
            max_loan = round(max_loan, 2)
        else:
            max_loan = None

        if   dbr_ratio <= 0.15: risk_tier = "very_low"
        elif dbr_ratio <= 0.25: risk_tier = "low"
        elif dbr_ratio <= 0.33: risk_tier = "medium"
        else:                   risk_tier = "exceeds_limit"

        if approved:
            reason = (f"DBR of {dbr_ratio*100:.1f}% is within the SAMA 33% cap. "
                      f"Loan of SAR {requested_loan:,.0f} approved.")
        else:
            reason = (f"DBR of {dbr_ratio*100:.1f}% exceeds SAMA 33% cap. "
                      f"Maximum eligible loan at current salary: SAR {max_loan:,.2f}.")

        return {
            "monthly_salary_sar":             monthly_salary,
            "existing_obligations_sar":       existing_obligations,
            "requested_loan_sar":             requested_loan,
            "loan_term_months":               loan_term_months,
            "include_interest":               include_interest,
            "annual_rate":                    annual_rate if include_interest else None,
            "monthly_payment":                monthly_payment,
            "total_monthly_obligations":      total_oblig,
            "dbr_ratio":                      dbr_ratio,
            "dbr_limit":                      self.SAMA_CAP,
            "dbr_status":                     "within_limit" if approved else "exceeds_limit",
            "risk_tier":                      risk_tier,
            "approved":                       approved,
            "max_eligible_loan_sar":          max_loan,
            "salary_deduction_agreement":     approved,
            "reason":                         reason,
        }

    # ── Transition readiness ──────────────────────────────────────────────────

    def transition_readiness(self, business_id):
        tx_path = os.path.join(DATA_DIR, f"{business_id}_transactions.csv")

        if not os.path.exists(tx_path):
            return {
                "business_id":          business_id,
                "ready":                False,
                "reason":               "No transaction data found.",
                "recommended_pipeline": "continue_incubator",
            }

        tx = pd.read_csv(tx_path)
        tx["timestamp"]  = pd.to_datetime(tx["timestamp"])
        tx["amount_sar"] = tx["amount_sar"].astype(float)
        tx["date"]       = tx["timestamp"].dt.strftime("%Y-%m-%d")

        # Rule 1: at least 14 days with transactions
        unique_days = tx["date"].nunique()
        if unique_days < 14:
            return {
                "business_id":          business_id,
                "ready":                False,
                "reason":               f"Only {unique_days} days of transaction data (minimum: 14).",
                "recommended_pipeline": "continue_incubator",
            }

        # Rule 2: avg daily revenue > 500 SAR
        avg_daily = float(tx.groupby("date")["amount_sar"].sum().mean())
        if avg_daily <= 500:
            return {
                "business_id":          business_id,
                "ready":                False,
                "reason":               f"Avg daily revenue SAR {avg_daily:,.2f} below SAR 500 threshold.",
                "recommended_pipeline": "continue_incubator",
            }

        # Rule 3: zero-revenue days < 5
        # Use only Sun-Thu (business days in Saudi Arabia) so that legitimate
        # Fri/Sat closures (real estate, offices) are not penalised.
        tx_dates   = set(tx["date"].tolist())
        biz_days   = [d for d in ALL_DATES if pd.Timestamp(d).weekday() not in [4, 5]]
        zero_days  = sum(1 for d in biz_days if d not in tx_dates)
        if zero_days >= 5:
            return {
                "business_id":          business_id,
                "ready":                False,
                "reason":               (f"{zero_days} zero-revenue days detected "
                                         f"(maximum allowed: 4) -- inconsistent cash flow."),
                "recommended_pipeline": "continue_incubator",
            }

        # Rule 4: no critical fraud flags
        from models.dscr_model import DSCRModel
        fraud    = DSCRModel().detect_fraud(tx)
        critical = [a for a in fraud["anomalies"] if a["severity"] == "critical"]
        if critical:
            return {
                "business_id":          business_id,
                "ready":                False,
                "reason":               (f"{len(critical)} critical fraud flag(s) detected -- "
                                         f"manual review required before pipeline transition."),
                "recommended_pipeline": "continue_incubator",
            }

        return {
            "business_id":          business_id,
            "ready":                True,
            "reason":               (f"All criteria met: {unique_days} days of data, "
                                     f"avg daily revenue SAR {avg_daily:,.2f}, "
                                     f"{zero_days} zero-revenue days, "
                                     f"no critical fraud flags."),
            "recommended_pipeline": "sme",
        }
