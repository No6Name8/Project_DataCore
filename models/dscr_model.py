"""
dscr_model.py  --  DataCore AI Engine: DSCR + Fraud Assessment
Reads transaction and energy CSVs and computes real scores from scratch.
"""

import os, sys
import numpy as np
import pandas as pd

ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
sys.path.insert(0, ROOT)

from models.business_classifier import BusinessClassifier
from models.expense_estimator   import ExpenseEstimator

# Industry expense ratios (fraction of revenue consumed by operating costs)
EXPENSE_RATIOS = {
    "laundromat": 0.55,   # utilities, rent, staff
    "cafe":       0.68,   # COGS 35%, staff 20%, rent 13%
    "minimarket": 0.78,   # COGS is dominant for grocery
    "realestate": 0.35,   # mostly staff, near-zero COGS
    "cardealer":  0.82,   # vehicle COGS is massive
    "motorbike":  0.72,   # inventory cost
}

BASE_RATE     = 0.065
LOAN_TERM     = 36        # months
LOAN_PCT      = 0.40      # 40% of annual revenue -- more realistic loan size
PERIOD_DAYS   = 30
ALL_DATES     = pd.date_range("2025-06-01", "2025-06-30").strftime("%Y-%m-%d").tolist()

CREDIT_CEILINGS = {
    "laundromat":   500_000,
    "cafe":         400_000,
    "minimarket": 1_500_000,
    "realestate": 2_000_000,
    "cardealer":  5_000_000,
    "motorbike":  1_000_000,
}


class DSCRModel:

    def __init__(self):
        self.classifier = BusinessClassifier()
        self.classifier.load()
        self.estimator  = ExpenseEstimator()

    # ── Data loading ──────────────────────────────────────────────────────────

    def load_data(self, business_id):
        tx = pd.read_csv(os.path.join(DATA_DIR, f"{business_id}_transactions.csv"))
        en = pd.read_csv(os.path.join(DATA_DIR, f"{business_id}_energy.csv"))
        tx["timestamp"]  = pd.to_datetime(tx["timestamp"])
        tx["amount_sar"] = tx["amount_sar"].astype(float)
        tx["date"]       = tx["timestamp"].dt.strftime("%Y-%m-%d")
        return tx, en

    # ── Revenue metrics ───────────────────────────────────────────────────────

    def compute_revenue_metrics(self, tx):
        daily = tx.groupby("date")["amount_sar"].sum().reindex(ALL_DATES, fill_value=0.0)

        total_revenue    = float(tx["amount_sar"].sum())
        avg_daily        = total_revenue / PERIOD_DAYS
        std_dev          = float(daily.std())

        # Linear trend: positive slope = growing revenue
        x     = np.arange(len(daily))
        slope = float(np.polyfit(x, daily.values, 1)[0])

        # Weekend multiplier (Thu=3 / Fri=4 as Saudi consumer weekend)
        tx_copy = tx.copy()
        tx_copy["is_wknd"] = tx_copy["timestamp"].dt.weekday.isin([3, 4])
        day_type = tx_copy.groupby(["date", "is_wknd"])["amount_sar"].sum().reset_index()
        wknd_avg = day_type[day_type["is_wknd"]]["amount_sar"].mean()
        wkdy_avg = day_type[~day_type["is_wknd"]]["amount_sar"].mean()
        wknd_mult = round(float(wknd_avg / wkdy_avg), 3) if wkdy_avg > 0 else 1.0

        tx_dates = set(tx["date"].tolist())
        # For real estate offices, Fri/Sat are legitimate non-working days.
        # Only count zero-revenue days on actual business days (Sun-Thu).
        # weekday(): Mon=0 Tue=1 Wed=2 Thu=3 Fri=4 Sat=5 Sun=6
        business_days     = [d for d in ALL_DATES if pd.Timestamp(d).weekday() not in [4, 5]]
        zero_revenue_days = sum(1 for d in business_days if d not in tx_dates)

        peak_d = daily.idxmax()
        low_d  = daily.idxmin()

        return {
            "total_revenue":       round(total_revenue, 2),
            "avg_daily_revenue":   round(avg_daily, 2),
            "revenue_std_dev":     round(std_dev, 2),
            "revenue_trend":       round(slope, 4),
            "weekend_multiplier":  wknd_mult,
            "peak_day":            peak_d,
            "low_day":             low_d,
            "zero_revenue_days":   zero_revenue_days,
        }

    # ── Operating expenses ────────────────────────────────────────────────────

    def compute_operating_expenses(self, tx, business_id):
        try:
            expense_result    = self.estimator.estimate_from_classifier(
                tx, self.classifier)
            expense_ratio     = expense_result["total_expense_ratio"]
            source            = "ai_derived"
            breakdown         = expense_result["breakdown"]
            model2_confidence = expense_result["confidence"]
        except Exception as e:
            print(f"  [WARN] Model 2 fallback for {business_id}: {e}")
            expense_ratio     = EXPENSE_RATIOS[business_id]
            source            = "hardcoded_fallback"
            breakdown         = {
                "cogs_ratio":     round(expense_ratio * 0.6, 4),
                "labor_ratio":    round(expense_ratio * 0.3, 4),
                "overhead_ratio": 0.08,
                "stability_adj":  0.0,
            }
            model2_confidence = 0.5

        total_revenue = float(tx["amount_sar"].sum())
        expenses      = total_revenue * expense_ratio
        noi           = total_revenue - expenses

        return {
            "estimated_monthly_expenses": round(expenses, 2),
            "net_operating_income":       round(noi, 2),
            "expense_ratio":              expense_ratio,
            "expense_source":             source,
            "expense_breakdown":          breakdown,
            "model2_confidence":          model2_confidence,
        }

    # ── DSCR calculation ──────────────────────────────────────────────────────

    def compute_dscr(self, noi_30d, avg_daily_revenue):
        # Annualise the 30-day figures (treat period as 1 month)
        annual_noi     = noi_30d * 12
        annual_revenue = avg_daily_revenue * 365
        loan_amount    = annual_revenue * LOAN_PCT

        # Standard amortisation: P*r(1+r)^n / ((1+r)^n - 1)
        r = BASE_RATE / 12
        n = LOAN_TERM
        factor          = r * (1 + r) ** n / ((1 + r) ** n - 1)
        monthly_payment = loan_amount * factor
        annual_debt_svc = monthly_payment * 12

        dscr = annual_noi / annual_debt_svc if annual_debt_svc > 0 else 0.0

        if   dscr >= 2.0:  risk_tier = "very_low"
        elif dscr >= 1.5:  risk_tier = "low"
        elif dscr >= 1.25: risk_tier = "medium"
        elif dscr >= 1.0:  risk_tier = "high"
        else:              risk_tier = "critical"

        return {
            "dscr_score":            round(dscr, 4),
            "risk_tier":             risk_tier,
            "loan_requested_sar":    round(loan_amount, 2),
            "annual_debt_service_sar": round(annual_debt_svc, 2),
            "annual_noi_sar":        round(annual_noi, 2),
        }

    # ── Credit limit ──────────────────────────────────────────────────────────

    def compute_credit_limit(self, avg_daily, dscr_score, risk_tier, std_dev, business_id):
        multipliers = {
            "very_low": 1.5, "low": 1.2, "medium": 0.9,
            "high": 0.6, "critical": 0.0,
        }
        base  = avg_daily * 90
        limit = base * multipliers[risk_tier]

        # Volatility penalty: high std_dev / avg_daily signals unstable income
        if avg_daily > 0 and (std_dev / avg_daily) > 0.5:
            limit *= 0.85

        ceiling = CREDIT_CEILINGS.get(business_id, 2_000_000)
        limit   = min(limit, ceiling)
        return int(round(limit / 5000) * 5000)

    # ── Sustainability discount ───────────────────────────────────────────────

    def compute_sustainability_discount(self, en):
        avg_eff   = float(en["energy_efficiency_score"].mean())
        green_cnt = int((en["energy_efficiency_score"] > 0.75).sum())

        if   avg_eff > 0.70 and green_cnt >= 3: discount = 0.010
        elif avg_eff > 0.60 and green_cnt >= 2: discount = 0.005
        else:                                    discount = 0.0

        return {
            "discount":               discount,
            "avg_efficiency":         round(avg_eff, 4),
            "green_days":             green_cnt,
            "sustainability_eligible": discount > 0,
        }

    # ── Fraud detection ───────────────────────────────────────────────────────

    def detect_fraud(self, tx, business_id=""):
        tx    = tx.copy()
        tx["hour"] = tx["timestamp"].dt.hour
        tx["date"] = tx["timestamp"].dt.strftime("%Y-%m-%d")
        anomalies  = []

        # CHECK 1 -- Off-hours spike (11PM-5AM = hours 23, 0-4)
        off = tx[tx["hour"].isin([23, 0, 1, 2, 3, 4])]
        off_by_day = off.groupby("date").size().reindex(ALL_DATES, fill_value=0)
        baseline   = float(off_by_day.mean())

        for date, count in off_by_day.items():
            if count > max(baseline * 4, 1) and count > 5:
                severity = "critical" if count > 15 else ("high" if count > 8 else "medium")
                ratio    = count / baseline if baseline > 0 else count
                anomalies.append({
                    "date":       date,
                    "type":       "off_hours_spike",
                    "description": (f"{int(count)} transactions between 11PM-5AM "
                                    f"(baseline {baseline:.1f}/day, {ratio:.1f}x above)"),
                    "severity":   severity,
                    "amount_if_applicable": None,
                })

        # CHECK 2 -- Statistical amount outlier (context-aware per business type)
        # High-ticket businesses have naturally large variance; use looser sigma.
        HIGH_TICKET      = {"cardealer", "realestate"}
        sigma_threshold  = 5.0 if business_id in HIGH_TICKET else 3.5

        mean_amt  = tx["amount_sar"].mean()
        std_amt   = tx["amount_sar"].std()
        threshold = mean_amt + sigma_threshold * std_amt
        outliers  = tx[tx["amount_sar"] > threshold]

        # Apply a percentile guard to suppress false positives from high-end
        # but legitimate products at the tail of the price distribution.
        if business_id in HIGH_TICKET:
            # Cardealer/realestate: must be > 3x the p95 (fleet sale, not a big deal)
            p95      = tx["amount_sar"].quantile(0.95)
            outliers = outliers[outliers["amount_sar"] > p95 * 3]
        else:
            # All others: must be > 2x the p99 so valid high-end SKUs (dry-clean,
            # premium bike) are never flagged — only true outliers like 4500 SAR
            # cash at a minimarket clear this bar.
            p99      = tx["amount_sar"].quantile(0.99)
            outliers = outliers[outliers["amount_sar"] > p99 * 2]

        for _, row in outliers.iterrows():
            sigmas   = (row["amount_sar"] - mean_amt) / std_amt if std_amt > 0 else 0
            severity = "critical" if sigmas > 8 else "high"
            anomalies.append({
                "date":       str(row["date"]),
                "type":       "amount_outlier",
                "description": (f"Transaction SAR {row['amount_sar']:,.2f} is "
                                f"{sigmas:.1f} std above mean (mean SAR {mean_amt:,.2f})"),
                "severity":   severity,
                "amount_if_applicable": float(row["amount_sar"]),
            })

        # CHECK 3 -- Revenue volatility spike (daily > 7-day rolling avg * 3.5)
        daily_rev = tx.groupby("date")["amount_sar"].sum().reindex(ALL_DATES, fill_value=0.0)
        # Shift by 1 so we compare today's revenue to the PREVIOUS 7-day average
        rolling7  = daily_rev.rolling(7, min_periods=1).mean().shift(1)

        for date in ALL_DATES:
            rev  = daily_rev.get(date, 0.0)
            roll = rolling7.get(date, np.nan)
            if pd.notna(roll) and roll > 100 and rev > roll * 3.5:
                anomalies.append({
                    "date":       date,
                    "type":       "revenue_spike",
                    "description": (f"Daily revenue SAR {rev:,.2f} is "
                                    f"{rev/roll:.1f}x above 7-day rolling avg (SAR {roll:,.2f})"),
                    "severity":   "medium",
                    "amount_if_applicable": float(rev),
                })

        # Fraud score
        sev_pts = {"critical": 40, "high": 25, "medium": 10}
        fraud_score = min(100, sum(sev_pts.get(a["severity"], 10) for a in anomalies))

        approval_frozen = fraud_score > 55
        overall_status  = "clear" if fraud_score == 0 else ("frozen" if approval_frozen else "flagged")

        return {
            "anomalies":           anomalies,
            "anomalies_detected":  len(anomalies),
            "fraud_score":         fraud_score,
            "approval_frozen":     approval_frozen,
            "overall_status":      overall_status,
        }

    # ── Full assessment ───────────────────────────────────────────────────────

    def run(self, business_id):
        tx, en = self.load_data(business_id)

        rev    = self.compute_revenue_metrics(tx)
        exp    = self.compute_operating_expenses(tx, business_id)
        dscr   = self.compute_dscr(exp["net_operating_income"], rev["avg_daily_revenue"])
        limit  = self.compute_credit_limit(
                     rev["avg_daily_revenue"], dscr["dscr_score"],
                     dscr["risk_tier"], rev["revenue_std_dev"], business_id)
        sus    = self.compute_sustainability_discount(en)
        fraud  = self.detect_fraud(tx, business_id)

        final_rate = round(BASE_RATE - sus["discount"], 4)

        return {
            "business_id":           business_id,
            "computed_at":           "2025-06-30",
            "revenue_metrics":       rev,
            "expense_ratio":         exp["expense_ratio"],
            "expense_source":        exp["expense_source"],
            "expense_breakdown":     exp["expense_breakdown"],
            "model2_confidence":     exp["model2_confidence"],
            "net_operating_income":  exp["net_operating_income"],
            "dscr_score":            dscr["dscr_score"],
            "risk_tier":             dscr["risk_tier"],
            "credit_limit_sar":      limit,
            "loan_requested_sar":    dscr["loan_requested_sar"],
            "annual_debt_service_sar": dscr["annual_debt_service_sar"],
            "interest_rate_base":    BASE_RATE,
            "sustainability_discount": sus["discount"],
            "final_interest_rate":   final_rate,
            "sustainability_eligible": sus["sustainability_eligible"],
            "avg_energy_efficiency": sus["avg_efficiency"],
            "green_days_count":      sus["green_days"],
            "fraud_assessment":      fraud,
        }
