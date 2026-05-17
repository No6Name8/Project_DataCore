"""
app.py  --  DataCore Mock REST API
Serves 30-day simulated datasets for 6 Saudi SME businesses.
DSCR and fraud endpoints now use live DSCRModel computation.
Run from project root: python api/app.py
"""

import os, sys
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import pandas as pd

# Allow importing models/ from project root
ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
sys.path.insert(0, ROOT)

from models.dscr_model import DSCRModel
from models.dbr_model  import DBRModel

app = Flask(__name__)
CORS(app)

# ── Business registry ─────────────────────────────────────────────────────────
BUSINESSES = {
    "laundromat": {"id":"laundromat","name":"Al Noor Laundromat",       "type":"laundromat","sector":"services",     "loan_pipeline":"sme"},
    "cafe":       {"id":"cafe",      "name":"Qahwa Corner Cafe",         "type":"cafe",      "sector":"food_beverage","loan_pipeline":"sme"},
    "minimarket": {"id":"minimarket","name":"Baraka Minimarket",         "type":"minimarket","sector":"retail",       "loan_pipeline":"sme"},
    "realestate": {"id":"realestate","name":"Majd Real Estate Office",   "type":"realestate","sector":"real_estate",  "loan_pipeline":"sme"},
    "cardealer":  {"id":"cardealer", "name":"Rawabi Auto Gallery",       "type":"cardealer", "sector":"automotive",   "loan_pipeline":"sme"},
    "motorbike":  {"id":"motorbike", "name":"Saqr Motorbikes",           "type":"motorbike", "sector":"automotive",   "loan_pipeline":"sme"},
}

# ── Model instances ───────────────────────────────────────────────────────────
_dscr_model = DSCRModel()
_dbr_model  = DBRModel()

# ── Model result cache (computed once per business per process lifetime) ──────
_MODEL_CACHE = {}

def get_model_result(bid):
    if bid not in _MODEL_CACHE:
        _MODEL_CACHE[bid] = _dscr_model.run(bid)
    return _MODEL_CACHE[bid]

# ── Raw CSV cache ─────────────────────────────────────────────────────────────
_TX = {}
_EN = {}

def csv_path(name):
    return os.path.join(DATA_DIR, name)

def load_tx(bid):
    if bid not in _TX:
        _TX[bid] = pd.read_csv(csv_path(f"{bid}_transactions.csv"))
    return _TX[bid].copy()

def load_en(bid):
    if bid not in _EN:
        _EN[bid] = pd.read_csv(csv_path(f"{bid}_energy.csv"))
    return _EN[bid].copy()

def require(bid):
    if bid not in BUSINESSES:
        abort(404, description=f"Business '{bid}' not found. Valid IDs: {list(BUSINESSES)}")

# ── Summary helper ────────────────────────────────────────────────────────────
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

# ── DSCR response shaper ──────────────────────────────────────────────────────
def shape_dscr(bid, r):
    fr = r["fraud_assessment"]
    first_reason = fr["anomalies"][0]["description"] if fr["anomalies"] else None
    return {
        "business_id":              bid,
        "computed_at":              r["computed_at"],
        "dscr_score":               r["dscr_score"],
        "net_operating_income_sar": r["net_operating_income"],
        "annual_debt_service_sar":  r["annual_debt_service_sar"],
        "loan_requested_sar":       r["loan_requested_sar"],
        "risk_tier":                r["risk_tier"],
        "approved_credit_limit_sar": r["credit_limit_sar"],
        "interest_rate_base":       r["interest_rate_base"],
        "sustainability_discount":  r["sustainability_discount"],
        "final_interest_rate":      r["final_interest_rate"],
        "sustainability_eligible":  r["sustainability_eligible"],
        "avg_energy_efficiency":    r["avg_energy_efficiency"],
        "green_days_count":         r["green_days_count"],
        "expense_ratio":            r["expense_ratio"],
        "revenue_metrics":          r["revenue_metrics"],
        "fraud_flag":               fr["approval_frozen"] or fr["fraud_score"] > 0,
        "fraud_reason":             first_reason,
        "assessment_date":          r["computed_at"],
    }

# ── Fraud response shaper ─────────────────────────────────────────────────────
def shape_fraud(bid, r):
    fr = r["fraud_assessment"]
    return {"business_id": bid, **fr}

# =============================================================================
# ROUTES -- Core data
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
# ROUTES -- AI engine (live model output)
# =============================================================================

@app.route("/api/<bid>/dscr")
def get_dscr(bid):
    require(bid)
    return jsonify(shape_dscr(bid, get_model_result(bid)))


@app.route("/api/<bid>/fraud-check")
def get_fraud(bid):
    require(bid)
    return jsonify(shape_fraud(bid, get_model_result(bid)))

# =============================================================================
# ROUTES -- Dashboard feed
# =============================================================================

@app.route("/api/dashboard/<bid>")
def get_dashboard(bid):
    require(bid)
    tx  = load_tx(bid)
    en  = load_en(bid)
    r   = get_model_result(bid)

    recent_tx    = (tx.sort_values("timestamp", ascending=False)
                      .head(10)
                      .to_dict(orient="records"))
    energy_trend = en.tail(7).to_dict(orient="records")

    return jsonify({
        "business":             BUSINESSES[bid],
        "summary":              build_summary(bid),
        "dscr":                 shape_dscr(bid, r),
        "fraud":                shape_fraud(bid, r),
        "recent_transactions":  recent_tx,
        "energy_trend":         energy_trend,
    })

# =============================================================================
# ROUTES -- Incubator
# =============================================================================

@app.route("/api/incubator/dbr-assessment")
def dbr_assessment():
    salary   = request.args.get("monthly_salary",      type=float)
    existing = request.args.get("existing_obligations", type=float, default=0.0)
    loan_amt = request.args.get("requested_loan",       type=float)
    term     = request.args.get("loan_term_months",     type=int,   default=24)

    if not salary or not loan_amt:
        return jsonify({"error": "monthly_salary and requested_loan are required"}), 400
    if salary <= 0:
        return jsonify({"error": "monthly_salary must be positive"}), 400

    return jsonify(_dbr_model.assess(salary, existing, loan_amt, term))


@app.route("/api/incubator/transition-check/<bid>")
def transition_check(bid):
    require(bid)
    return jsonify(_dbr_model.transition_readiness(bid))

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
