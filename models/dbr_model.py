"""
dbr_model.py  --  DataCore Incubator Pipeline: DBR Assessment
Implements SAMA 33% DBR cap and SME transition readiness checks.
"""

import os, sys
import pandas as pd

ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "processed")
sys.path.insert(0, ROOT)

ALL_DATES = pd.date_range("2025-04-01", "2025-06-30").strftime("%Y-%m-%d").tolist()


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
        tx_path      = os.path.join(DATA_DIR, f"{business_id}_transactions.csv")
        gates_passed = []

        if not os.path.exists(tx_path):
            return {
                "business_id":          business_id,
                "ready":                False,
                "decision":             "NOT_READY",
                "reason":               "No transaction data found.",
                "blocking_reasons":     ["No transaction data found for this business ID"],
                "gates_passed":         gates_passed,
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
                "decision":             "NOT_READY",
                "reason":               f"Only {unique_days} days of transaction data (minimum: 14).",
                "blocking_reasons":     [f"Insufficient data: {unique_days} days of transactions "
                                         f"(minimum 14 required to establish reliable patterns)"],
                "gates_passed":         gates_passed,
                "recommended_pipeline": "continue_incubator",
            }
        gates_passed.append(f"Data window gate: {unique_days} days of transaction history "
                            f"(minimum 14)")

        # Rule 2: avg daily revenue > 500 SAR
        avg_daily = float(tx.groupby("date")["amount_sar"].sum().mean())
        if avg_daily <= 500:
            return {
                "business_id":          business_id,
                "ready":                False,
                "decision":             "NOT_READY",
                "reason":               f"Avg daily revenue SAR {avg_daily:,.2f} below SAR 500 threshold.",
                "blocking_reasons":     [f"Average daily revenue SAR {avg_daily:,.0f} below "
                                         f"minimum SAR 500 threshold"],
                "gates_passed":         gates_passed,
                "recommended_pipeline": "continue_incubator",
            }
        gates_passed.append(f"Revenue gate: avg daily revenue SAR {avg_daily:,.0f} "
                            f"(minimum SAR 500)")

        # Rule 3: zero-revenue days < 5
        # Use only Sun-Thu (business days in Saudi Arabia) so that legitimate
        # Fri/Sat closures (real estate, offices) are not penalised.
        tx_dates  = set(tx["date"].tolist())
        biz_days  = [d for d in ALL_DATES if pd.Timestamp(d).weekday() not in [4, 5]]
        zero_days = sum(1 for d in biz_days if d not in tx_dates)
        if zero_days >= 5:
            return {
                "business_id":          business_id,
                "ready":                False,
                "decision":             "NOT_READY",
                "reason":               (f"{zero_days} zero-revenue days detected "
                                         f"(maximum allowed: 4) -- inconsistent cash flow."),
                "blocking_reasons":     [f"{zero_days} zero-revenue business days (Sun-Thu) detected "
                                         f"out of {len(biz_days)} business days — maximum allowed is 4; "
                                         f"suggests inconsistent trading or incomplete POS data"],
                "gates_passed":         gates_passed,
                "recommended_pipeline": "continue_incubator",
            }
        gates_passed.append(f"Cash flow gate: {zero_days} zero-revenue business days "
                            f"in {len(biz_days)} business days (maximum 4)")

        # Rule 4: fraud gate — use the trained Isolation Forest model (FraudDetector).
        from models.fraud_detector import FraudDetector
        _saved_pkl = os.path.join(ROOT, "models", "saved", "fraud_detector.pkl")
        _detector  = FraudDetector()
        _detector.load(_saved_pkl)
        fraud = _detector.assess(business_id)

        if fraud["approval_frozen"]:
            blocking = (f"Fraud gate blocked: approval frozen — fraud score {fraud['fraud_score']}/100 "
                        f"with {fraud['anomalies_detected']} anomaly incident(s) detected "
                        f"(threshold >55); manual review required before pipeline transition")
            if fraud.get("reasons"):
                blocking += " [" + "; ".join(r["detail"] for r in fraud["reasons"][:2]) + "]"
            return {
                "business_id":          business_id,
                "ready":                False,
                "decision":             "NOT_READY",
                "reason":               (f"Approval frozen: fraud score {fraud['fraud_score']} with "
                                         f"{fraud['anomalies_detected']} anomaly(ies) detected -- "
                                         f"manual review required before pipeline transition."),
                "blocking_reasons":     [blocking],
                "gates_passed":         gates_passed,
                "recommended_pipeline": "continue_incubator",
            }

        critical = [a for a in fraud["anomalies"] if a["severity"] == "critical"]
        if fraud["overall_status"] == "flagged" and critical:
            details = "; ".join(
                r["detail"] for r in fraud.get("reasons", [])
                if r.get("severity") == "critical"
            )[:200]
            return {
                "business_id":          business_id,
                "ready":                False,
                "decision":             "NOT_READY",
                "reason":               (f"{len(critical)} critical fraud flag(s) detected "
                                         f"(score {fraud['fraud_score']}) -- "
                                         f"manual review required before pipeline transition."),
                "blocking_reasons":     [f"Fraud gate blocked: {len(critical)} critical anomaly(ies) — "
                                         + (details if details else "see anomalies list")],
                "gates_passed":         gates_passed,
                "recommended_pipeline": "continue_incubator",
            }

        if fraud["overall_status"] == "flagged" and fraud["fraud_score"] >= 60:
            return {
                "business_id":          business_id,
                "ready":                False,
                "decision":             "NOT_READY",
                "reason":               (f"High fraud risk score {fraud['fraud_score']} -- "
                                         f"manual review required before pipeline transition."),
                "blocking_reasons":     [f"Fraud gate blocked: high risk score {fraud['fraud_score']}/100 "
                                         f"(threshold 60); elevated anomaly rate requires review"],
                "gates_passed":         gates_passed,
                "recommended_pipeline": "continue_incubator",
            }

        fraud_gate_msg = (f"Fraud gate: passed (score {fraud['fraud_score']}/100, "
                          f"{fraud['anomalous_tx_count']}/{fraud['total_tx_scored']} "
                          f"flagged transactions, no critical anomalies)")
        if fraud.get("checks_passed"):
            fraud_gate_msg += " — " + " | ".join(fraud["checks_passed"])
        gates_passed.append(fraud_gate_msg)

        return {
            "business_id":          business_id,
            "ready":                True,
            "decision":             "READY",
            "reason":               (f"All criteria met: {unique_days} days of data, "
                                     f"avg daily revenue SAR {avg_daily:,.2f}, "
                                     f"{zero_days} zero-revenue days, "
                                     f"no critical fraud flags."),
            "blocking_reasons":     [],
            "gates_passed":         gates_passed,
            "recommended_pipeline": "sme",
        }
