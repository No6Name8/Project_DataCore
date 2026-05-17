"""
app.py  —  DataCore Mock REST API
Serves 30-day simulated datasets for 6 Saudi SME businesses.
Run from project root: python api/app.py
"""

import os
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# ── Paths ─────────────────────────────────────────────────────────────────────
# __file__ is api/app.py; DATA_DIR is one level up → data/
ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")

def csv(name):
    return os.path.join(DATA_DIR, name)

# ── Business registry ─────────────────────────────────────────────────────────
BUSINESSES = {
    "laundromat": {"id":"laundromat","name":"Al Noor Laundromat",       "type":"laundromat","sector":"services",     "loan_pipeline":"sme"},
    "cafe":       {"id":"cafe",      "name":"Qahwa Corner Cafe",         "type":"cafe",      "sector":"food_beverage","loan_pipeline":"sme"},
    "minimarket": {"id":"minimarket","name":"Baraka Minimarket",         "type":"minimarket","sector":"retail",       "loan_pipeline":"sme"},
    "realestate": {"id":"realestate","name":"Majd Real Estate Office",   "type":"realestate","sector":"real_estate",  "loan_pipeline":"sme"},
    "cardealer":  {"id":"cardealer", "name":"Rawabi Auto Gallery",       "type":"cardealer", "sector":"automotive",   "loan_pipeline":"sme"},
    "motorbike":  {"id":"motorbike", "name":"Saqr Motorbikes",           "type":"motorbike", "sector":"automotive",   "loan_pipeline":"sme"},
}

# ── Lazy CSV cache ────────────────────────────────────────────────────────────
_TX = {}
_EN = {}

def load_tx(bid):
    if bid not in _TX:
        _TX[bid] = pd.read_csv(csv(f"{bid}_transactions.csv"))
    return _TX[bid].copy()

def load_en(bid):
    if bid not in _EN:
        _EN[bid] = pd.read_csv(csv(f"{bid}_energy.csv"))
    return _EN[bid].copy()

def require(bid):
    if bid not in BUSINESSES:
        abort(404, description=f"Business '{bid}' not found. Valid IDs: {list(BUSINESSES)}")

# ── DSCR — hardcoded realistic values per business type ──────────────────────
DSCR = {
    "laundromat": {
        "dscr_score": 1.65, "net_operating_income_sar": 74250,  "total_debt_service_sar": 45000,
        "risk_tier": "low",    "approved_credit_limit_sar": 90000,
        "interest_rate_base": 0.065, "sustainability_discount": 0.005, "final_interest_rate": 0.060,
        "sustainability_eligible": True,
        "fraud_flag": True,
        "fraud_reason": "3AM transaction spike on 2025-06-14: 15 transactions vs baseline ~2/hour",
        "assessment_date": "2025-06-30",
    },
    "cafe": {
        "dscr_score": 1.42, "net_operating_income_sar": 58000,  "total_debt_service_sar": 40845,
        "risk_tier": "low",    "approved_credit_limit_sar": 75000,
        "interest_rate_base": 0.065, "sustainability_discount": 0.005, "final_interest_rate": 0.060,
        "sustainability_eligible": True,
        "fraud_flag": True,
        "fraud_reason": "14 transactions at 2AM on 2025-06-19 — 8x above hourly baseline; POS crash 2025-06-08",
        "assessment_date": "2025-06-30",
    },
    "minimarket": {
        "dscr_score": 2.10, "net_operating_income_sar": 315000, "total_debt_service_sar": 150000,
        "risk_tier": "low",    "approved_credit_limit_sar": 280000,
        "interest_rate_base": 0.065, "sustainability_discount": 0.005, "final_interest_rate": 0.060,
        "sustainability_eligible": True,
        "fraud_flag": True,
        "fraud_reason": "SAR 4,500+ cash transaction at 3AM on 2025-06-11 — no correlated inventory signal",
        "assessment_date": "2025-06-30",
    },
    "realestate": {
        "dscr_score": 1.28, "net_operating_income_sar": 192000, "total_debt_service_sar": 150000,
        "risk_tier": "medium", "approved_credit_limit_sar": 450000,
        "interest_rate_base": 0.075, "sustainability_discount": 0.005, "final_interest_rate": 0.070,
        "sustainability_eligible": True,
        "fraud_flag": False,
        "fraud_reason": None,
        "assessment_date": "2025-06-30",
    },
    "cardealer": {
        "dscr_score": 1.85, "net_operating_income_sar": 2775000, "total_debt_service_sar": 1500000,
        "risk_tier": "low",    "approved_credit_limit_sar": 2500000,
        "interest_rate_base": 0.060, "sustainability_discount": 0.005, "final_interest_rate": 0.055,
        "sustainability_eligible": True,
        "fraud_flag": False,
        "fraud_reason": None,
        "assessment_date": "2025-06-30",
    },
    "motorbike": {
        "dscr_score": 1.55, "net_operating_income_sar": 620000, "total_debt_service_sar": 400000,
        "risk_tier": "medium", "approved_credit_limit_sar": 380000,
        "interest_rate_base": 0.070, "sustainability_discount": 0.005, "final_interest_rate": 0.065,
        "sustainability_eligible": True,
        "fraud_flag": False,
        "fraud_reason": None,
        "assessment_date": "2025-06-30",
    },
}

# ── Fraud registry — actual anomaly dates from generated data ─────────────────
FRAUD = {
    "laundromat": {
        "anomalies_detected": 1,
        "anomalies": [{
            "date": "2025-06-14", "type": "off_hours_spike",
            "description": "15 transactions between 3AM-4AM, 6x above hourly baseline",
            "severity": "high", "action": "approval_frozen",
        }],
        "overall_status": "flagged", "approval_frozen": True,
    },
    "cafe": {
        "anomalies_detected": 2,
        "anomalies": [
            {
                "date": "2025-06-08", "type": "volume_crash",
                "description": "Only 8 transactions all day — 91% below average; suspected POS failure or unregistered closure",
                "severity": "medium", "action": "manual_review",
            },
            {
                "date": "2025-06-19", "type": "off_hours_spike",
                "description": "14 transactions between 2AM-3AM, 8x above hourly baseline",
                "severity": "high", "action": "approval_frozen",
            },
        ],
        "overall_status": "flagged", "approval_frozen": True,
    },
    "minimarket": {
        "anomalies_detected": 1,
        "anomalies": [{
            "date": "2025-06-11", "type": "large_cash_off_hours",
            "description": "Single cash transaction of SAR 4,500+ at 3AM — 10x above basket average, no inventory movement",
            "severity": "high", "action": "approval_frozen",
        }],
        "overall_status": "flagged", "approval_frozen": True,
    },
    "realestate": {
        "anomalies_detected": 0, "anomalies": [],
        "overall_status": "clear", "approval_frozen": False,
    },
    "cardealer": {
        "anomalies_detected": 0, "anomalies": [],
        "overall_status": "clear", "approval_frozen": False,
    },
    "motorbike": {
        "anomalies_detected": 1,
        "anomalies": [{
            "date": "2025-06-07", "type": "late_night_bulk",
            "description": "Bulk accessories purchase of SAR 7,500+ at 11PM — atypical hour for business type",
            "severity": "low", "action": "flagged_for_review",
        }],
        "overall_status": "review", "approval_frozen": False,
    },
}

# ── Summary helper (shared by /summary and /dashboard) ───────────────────────
def build_summary(bid):
    tx = load_tx(bid)
    en = load_en(bid)

    tx["date"]  = tx["timestamp"].str[:10]
    daily_rev   = tx.groupby("date")["amount_sar"].sum()
    peak_d      = daily_rev.idxmax()
    low_d       = daily_rev.idxmin()
    green_days  = en[en["energy_efficiency_score"] > 0.85]["date"].tolist()
    pay_split   = tx["payment_method"].value_counts(normalize=True).round(4).to_dict()

    return {
        "business_id":              bid,
        "period":                   "2025-06-01 to 2025-06-30",
        "total_transactions":       int(len(tx)),
        "total_revenue_sar":        round(float(tx["amount_sar"].sum()), 2),
        "avg_daily_revenue_sar":    round(float(daily_rev.mean()), 2),
        "avg_daily_transactions":   round(len(tx) / 30, 1),
        "peak_day":                 {"date": peak_d,  "revenue": round(float(daily_rev[peak_d]),  2)},
        "lowest_day":               {"date": low_d,   "revenue": round(float(daily_rev[low_d]),   2)},
        "avg_energy_kwh":           round(float(en["total_kwh"].mean()), 2),
        "avg_efficiency_score":     round(float(en["energy_efficiency_score"].mean()), 4),
        "green_days":               green_days,
        "payment_method_breakdown": pay_split,
    }

# =============================================================================
# ROUTES — Core data
# =============================================================================

@app.route("/api/businesses")
def get_businesses():
    return jsonify({"businesses": list(BUSINESSES.values())})


@app.route("/api/<bid>/transactions")
def get_transactions(bid):
    require(bid)
    df    = load_tx(bid)
    start = request.args.get("start")
    end   = request.args.get("end")
    limit = request.args.get("limit", type=int)

    if start:
        df = df[df["timestamp"] >= start]
    if end:
        df = df[df["timestamp"] <= end + " 23:59:59"]

    df = df.sort_values("timestamp", ascending=False)

    if limit:
        df = df.head(limit)

    return jsonify(df.to_dict(orient="records"))


@app.route("/api/<bid>/energy")
def get_energy(bid):
    require(bid)
    return jsonify(load_en(bid).to_dict(orient="records"))


@app.route("/api/<bid>/summary")
def get_summary(bid):
    require(bid)
    return jsonify(build_summary(bid))

# =============================================================================
# ROUTES — AI engine
# =============================================================================

@app.route("/api/<bid>/dscr")
def get_dscr(bid):
    require(bid)
    return jsonify({"business_id": bid, **DSCR[bid]})


@app.route("/api/<bid>/fraud-check")
def get_fraud(bid):
    require(bid)
    return jsonify({"business_id": bid, **FRAUD[bid]})

# =============================================================================
# ROUTES — Dashboard feed
# =============================================================================

@app.route("/api/dashboard/<bid>")
def get_dashboard(bid):
    require(bid)
    tx = load_tx(bid)
    en = load_en(bid)

    recent_tx    = (tx.sort_values("timestamp", ascending=False)
                      .head(10)
                      .to_dict(orient="records"))
    energy_trend = en.tail(7).to_dict(orient="records")

    return jsonify({
        "business":            BUSINESSES[bid],
        "summary":             build_summary(bid),
        "dscr":                {"business_id": bid, **DSCR[bid]},
        "fraud":               {"business_id": bid, **FRAUD[bid]},
        "recent_transactions": recent_tx,
        "energy_trend":        energy_trend,
    })

# =============================================================================
# ROUTES — Incubator
# =============================================================================

@app.route("/api/incubator/dbr-assessment")
def dbr_assessment():
    salary   = request.args.get("monthly_salary",       type=float)
    existing = request.args.get("existing_obligations",  type=float, default=0.0)
    loan_amt = request.args.get("requested_loan",        type=float)
    term     = request.args.get("loan_term_months",      type=int,   default=24)

    if not salary or not loan_amt:
        return jsonify({"error": "monthly_salary and requested_loan are required"}), 400
    if salary <= 0:
        return jsonify({"error": "monthly_salary must be positive"}), 400

    SAMA_CAP    = 0.33
    monthly_pmt = round(loan_amt / term, 2)
    total_oblig = round(existing + monthly_pmt, 2)
    dbr_ratio   = round(total_oblig / salary, 4)
    approved    = dbr_ratio <= SAMA_CAP

    # Maximum loan where total DBR just reaches 33%
    max_monthly = salary * SAMA_CAP - existing
    max_loan    = round(max(0.0, max_monthly * term), 2)

    if approved:
        reason = (f"DBR of {dbr_ratio*100:.1f}% is within the SAMA 33% cap. "
                  f"Loan of SAR {loan_amt:,.0f} approved.")
    else:
        reason = (f"DBR of {dbr_ratio*100:.1f}% exceeds SAMA 33% cap. "
                  f"Maximum eligible loan at current salary is SAR {max_loan:,.0f}.")

    return jsonify({
        "monthly_salary_sar":             salary,
        "existing_obligations_sar":       existing,
        "requested_loan_monthly_payment": monthly_pmt,
        "total_monthly_obligations":      total_oblig,
        "dbr_ratio":                      dbr_ratio,
        "dbr_limit":                      SAMA_CAP,
        "dbr_status":                     "within_limit" if approved else "exceeds_limit",
        "max_eligible_loan_sar":          max_loan,
        "approved":                       approved,
        "reason":                         reason,
        "salary_deduction_agreement":     approved,
    })

# =============================================================================
# Error handlers
# =============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": str(e.description)}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
