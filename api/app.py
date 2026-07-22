"""
app.py  --  DataCore Mock REST API
Serves 30-day simulated datasets for 6 Saudi SME businesses.
AI engine: DSCR, fraud (Isolation Forest), revenue forecast (Prophet).
Run from project root: python api/app.py
"""

import os, sys, json
try:
    from flask import Flask, jsonify, request, abort
    from flask_cors import CORS
except ImportError as exc:
    raise ImportError(
        "Flask and Flask-CORS are required to run this application. "
        "Install them with `pip install flask flask-cors`."
    ) from exc
import pandas as pd

ROOT          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR      = os.path.join(ROOT, "data", "processed")
PORTFOLIO_DIR = os.path.join(ROOT, "data", "portfolio")
sys.path.insert(0, ROOT)

from models.dscr_model          import DSCRModel
from models.dbr_model           import DBRModel
from models.fraud_detector      import FraudDetector
from models.revenue_forecaster  import RevenueForecaster
from models.business_classifier import BusinessClassifier
from models.expense_estimator   import ExpenseEstimator

app = Flask(__name__)

# ALLOWED_ORIGINS env var: comma-separated list of allowed origins, or "*" (default).
# Set to your Vercel domain on Railway: ALLOWED_ORIGINS=https://your-app.vercel.app
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "*")
_cors_origins = "*" if _raw_origins == "*" else [o.strip() for o in _raw_origins.split(",")]
CORS(app, origins=_cors_origins)

# ── Business registry ─────────────────────────────────────────────────────────
# Optional demo location assignments (Part 3). Districts chosen to surface a
# mix of enriched outcomes: minimarket in an underserved area (market-gap flag),
# cafe in a saturated area, and Rawabi in a low-income district where its
# large car sales also trip the fraud district-scale signal. These are demo
# placements — production would use the bank's own customer address data.
_LOC = lambda district, lat, lng: {
    "location_district": district, "location_city": "Riyadh",
    "location_lat": lat, "location_lng": lng,
}
_REG = lambda cat, status, date, cr, name: {
    "license_category": cat, "license_status": status, "registration_date": date,
    "registration_number": cr, "registered_business_name": name,
}
# Optional demo registration/licensing (Part 3). Five carry consistent, active
# licenses registered > 2 years ago; Al Noor Laundromat is DELIBERATELY declared
# under a food_beverage license (transactions look like a personal service) to
# showcase the classifier's license-vs-inference cross-check "inconsistent" path;
# Rawabi is registered < 180 days before its data window so the fraud detector's
# new-business-high-volume flag stacks on its existing signals. Demo values.
BUSINESSES = {
    "laundromat":   {"id":"laundromat",  "name":"Al Noor Laundromat",     "type":"laundromat", "sector":"services",     "loan_pipeline":"sme", "location": _LOC("Al Malaz",       24.6636, 46.7361), "registration": _REG("food_beverage",    "active", "2020-08-05", "1010384756", "Al Noor Laundromat Est.")},
    "cafe":         {"id":"cafe",        "name":"Qahwa Corner Cafe",       "type":"cafe",       "sector":"food_beverage","loan_pipeline":"sme", "location": _LOC("Al Olaya",       24.6908, 46.6853), "registration": _REG("food_beverage",    "active", "2021-05-10", "1010556677", "Qahwa Corner Cafe Co.")},
    "minimarket":   {"id":"minimarket",  "name":"Baraka Minimarket",       "type":"minimarket", "sector":"retail",       "loan_pipeline":"sme", "location": _LOC("Al Naseem",      24.7736, 46.8294), "registration": _REG("retail_general",   "active", "2019-11-01", "1010223344", "Baraka Minimarket Trading")},
    "realestate":   {"id":"realestate",  "name":"Majd Real Estate Office", "type":"realestate", "sector":"real_estate",  "loan_pipeline":"sme", "location": _LOC("Al Sulimaniyah", 24.7050, 46.6900), "registration": _REG("real_estate",      "active", "2018-03-20", "1010119988", "Majd Real Estate Office")},
    "cardealer":    {"id":"cardealer",   "name":"Rawabi Auto Gallery",     "type":"cardealer",  "sector":"automotive",   "loan_pipeline":"sme", "location": _LOC("Al Batha",       24.6300, 46.7150), "registration": _REG("retail_specialty", "active", "2025-03-15", "1010778899", "Rawabi Auto Gallery")},
    "motorbike":    {"id":"motorbike",   "name":"Saqr Motorbikes",         "type":"motorbike",  "sector":"automotive",   "loan_pipeline":"sme", "location": _LOC("Al Aziziyah",    24.5680, 46.7800), "registration": _REG("retail_specialty", "active", "2022-01-15", "1010667788", "Saqr Motorbikes Co.")},
    "hilal_bakery": {"id":"hilal_bakery","name":"Hilal Bakery",            "type":"bakery",     "sector":"food_beverage","loan_pipeline":"sme"},
}
VALID_BUSINESSES = list(BUSINESSES.keys())

# ── Global model registry ─────────────────────────────────────────────────────
_dscr      = None
_dbr       = None
_detector  = None
_forecaster = None
_classifier = None
_estimator  = None
_models_loaded = False


def load_models():
    global _dscr, _dbr, _detector, _forecaster, _classifier, _estimator, _models_loaded
    if _models_loaded:
        return

    saved = os.path.join(ROOT, "models", "saved")
    print("[startup] Loading AI models...")

    _dscr       = DSCRModel()
    _dbr        = DBRModel()

    _detector   = FraudDetector()
    _detector.load(os.path.join(saved, "fraud_detector.pkl"))

    _forecaster = RevenueForecaster()
    _forecaster.load(os.path.join(saved, "revenue_forecaster.pkl"))

    _classifier = BusinessClassifier()
    _classifier.load(os.path.join(saved, "business_classifier.pkl"))

    _estimator  = ExpenseEstimator()

    _models_loaded = True
    print("[startup] All models ready.")


# ── Model result cache (computed once per business per process lifetime) ──────
_MODEL_CACHE      = {}
_FRAUD_CACHE      = {}
_TRANSITION_CACHE = {}


def get_model_result(bid):
    if bid not in _MODEL_CACHE:
        _MODEL_CACHE[bid] = _dscr.run(bid)
    return _MODEL_CACHE[bid]


def get_fraud_result(bid):
    if bid not in _FRAUD_CACHE:
        # Optional location + registration enrichment (demo district / license, if any)
        meta = BUSINESSES.get(bid, {})
        _FRAUD_CACHE[bid] = _detector.assess(
            bid, location=meta.get("location"), registration=meta.get("registration"),
            business_type=meta.get("type"))
    return _FRAUD_CACHE[bid]


_CLASSIFY_CACHE = {}


def get_classification_result(bid):
    """Classifier output enriched with optional location context (additive metadata)."""
    if bid not in _CLASSIFY_CACHE:
        meta = BUSINESSES.get(bid, {})
        _CLASSIFY_CACHE[bid] = _classifier.classify_from_data(
            load_tx(bid), bid=bid,
            location=meta.get("location"), business_type=meta.get("type"),
            registration=meta.get("registration"))
    return _CLASSIFY_CACHE[bid]


def get_transition_result(bid):
    if bid not in _TRANSITION_CACHE:
        _TRANSITION_CACHE[bid] = _dbr.transition_readiness(bid)
    return _TRANSITION_CACHE[bid]


# ── Raw CSV cache ─────────────────────────────────────────────────────────────
_TX = {}
_EN = {}


def load_tx(bid):
    if bid not in _TX:
        _TX[bid] = pd.read_csv(os.path.join(DATA_DIR, f"{bid}_transactions.csv"))
    return _TX[bid].copy()


def load_en(bid):
    if bid not in _EN:
        _EN[bid] = pd.read_csv(os.path.join(DATA_DIR, f"{bid}_energy.csv"))
    return _EN[bid].copy()


def _records(df):
    """to_dict(records) with NaN → None so the output is strict-valid JSON.
    (Optional columns like counterparty_raw are blank on some rows → NaN.)"""
    return df.astype(object).where(pd.notnull(df), None).to_dict(orient="records")


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
    dynamic      = _forecaster.compute_dynamic_credit_limit(bid, r["credit_limit_sar"])
    transition   = get_transition_result(bid)
    return {
        "business_id":               bid,
        "computed_at":               r["computed_at"],
        "dscr_score":                r["dscr_score"],
        "net_operating_income_sar":  r["net_operating_income"],
        "annual_debt_service_sar":   r["annual_debt_service_sar"],
        "loan_requested_sar":        r["loan_requested_sar"],
        "risk_tier":                 r["risk_tier"],
        "approved_credit_limit_sar": r["credit_limit_sar"],
        "dynamic_credit_limit":      dynamic,
        "interest_rate_base":        r["interest_rate_base"],
        "sustainability_discount":   r["sustainability_discount"],
        "final_interest_rate":       r["final_interest_rate"],
        "sustainability_eligible":   r["sustainability_eligible"],
        "avg_energy_efficiency":     r["avg_energy_efficiency"],
        "green_days_count":          r["green_days_count"],
        "expense_ratio":             r["expense_ratio"],
        "expense_breakdown":         r.get("expense_breakdown"),
        "expense_source":            r.get("expense_source"),
        "archetype_description":     r.get("archetype_description"),
        "revenue_metrics":           r["revenue_metrics"],
        "fraud_flag":                fr["approval_frozen"] or fr["fraud_score"] > 0,
        "fraud_reason":              first_reason,
        "assessment_date":           r["computed_at"],
        "transition_readiness": {
            "decision":          transition["decision"],
            "blocking_reasons":  transition["blocking_reasons"],
            "gates_passed":      transition["gates_passed"],
            "recommended_pipeline": transition["recommended_pipeline"],
        },
    }

# =============================================================================
# ROUTES -- Health check (no model dependency — responds immediately)
# =============================================================================

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "models_loaded": _models_loaded}), 200

# =============================================================================
# ROUTES -- Core data
# =============================================================================

@app.route("/api/businesses")
def get_businesses():
    try:
        return jsonify({"businesses": list(BUSINESSES.values())})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/<business_id>/transactions")
def get_transactions(business_id):
    try:
        if business_id not in VALID_BUSINESSES:
            return jsonify({"error": f"Unknown business: {business_id}"}), 404
        df    = load_tx(business_id)
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

        return jsonify(_records(df))
    except Exception as e:
        return jsonify({"error": str(e), "business_id": business_id}), 500


@app.route("/api/<business_id>/energy")
def get_energy(business_id):
    try:
        if business_id not in VALID_BUSINESSES:
            return jsonify({"error": f"Unknown business: {business_id}"}), 404
        return jsonify(load_en(business_id).to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e), "business_id": business_id}), 500


@app.route("/api/<business_id>/summary")
def get_summary(business_id):
    try:
        if business_id not in VALID_BUSINESSES:
            return jsonify({"error": f"Unknown business: {business_id}"}), 404
        return jsonify(build_summary(business_id))
    except Exception as e:
        return jsonify({"error": str(e), "business_id": business_id}), 500

# =============================================================================
# ROUTES -- AI engine (live model output)
# =============================================================================

@app.route("/api/<business_id>/dscr")
def get_dscr(business_id):
    try:
        if business_id not in VALID_BUSINESSES:
            return jsonify({"error": f"Unknown business: {business_id}"}), 404
        return jsonify(shape_dscr(business_id, get_model_result(business_id)))
    except Exception as e:
        return jsonify({"error": str(e), "business_id": business_id}), 500


@app.route("/api/<business_id>/fraud-check")
def get_fraud(business_id):
    try:
        if business_id not in VALID_BUSINESSES:
            return jsonify({"error": f"Unknown business: {business_id}"}), 404
        return jsonify(get_fraud_result(business_id))
    except Exception as e:
        return jsonify({"error": str(e), "business_id": business_id}), 500


@app.route("/api/<business_id>/forecast")
def get_forecast(business_id):
    try:
        if business_id not in VALID_BUSINESSES:
            return jsonify({"error": f"Unknown business: {business_id}"}), 404
        base_limit = get_model_result(business_id)["credit_limit_sar"]
        return jsonify({
            "business_id":    business_id,
            "summary":        _forecaster.summaries[business_id],
            "series":         _forecaster.get_forecast_series(business_id),
            "dynamic_credit": _forecaster.compute_dynamic_credit_limit(business_id, base_limit),
        })
    except Exception as e:
        return jsonify({"error": str(e), "business_id": business_id}), 500

# =============================================================================
# ROUTES -- Dashboard feed
# =============================================================================

@app.route("/api/dashboard/<business_id>")
def get_dashboard(business_id):
    try:
        if business_id not in VALID_BUSINESSES:
            return jsonify({"error": f"Unknown business: {business_id}"}), 404

        tx  = load_tx(business_id)
        en  = load_en(business_id)
        r   = get_model_result(business_id)

        recent_tx    = _records(tx.sort_values("timestamp", ascending=False).head(10))
        energy_trend = _records(en.tail(7))

        fc_summary = _forecaster.summaries[business_id]
        fc_series  = _forecaster.get_forecast_series(business_id)[:7]

        return jsonify({
            "business":            BUSINESSES[business_id],
            "summary":             build_summary(business_id),
            "dscr":                shape_dscr(business_id, r),
            "fraud":               get_fraud_result(business_id),
            "classification":      get_classification_result(business_id),
            "forecast": {
                "summary": fc_summary,
                "series":  fc_series,
            },
            "recent_transactions": recent_tx,
            "energy_trend":        energy_trend,
        })
    except Exception as e:
        return jsonify({"error": str(e), "business_id": business_id}), 500

# =============================================================================
# ROUTES -- Incubator
# =============================================================================

@app.route("/api/incubator/dbr-assessment")
def dbr_assessment():
    try:
        salary          = request.args.get("monthly_salary",       type=float)
        existing        = request.args.get("existing_obligations",  type=float, default=0.0)
        loan_amt        = request.args.get("requested_loan",        type=float)
        term            = request.args.get("loan_term_months",      type=int,   default=24)
        holds_inventory = request.args.get("holds_inventory", "false").lower() == "true"

        if not salary or not loan_amt:
            return jsonify({"error": "monthly_salary and requested_loan are required"}), 400
        if salary <= 0:
            return jsonify({"error": "monthly_salary must be positive"}), 400

        result = _dbr.assess(salary, existing, loan_amt, term)
        result["holds_inventory_flag"] = holds_inventory
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/incubator/business-profile")
def intake_business_profile():
    try:
        ticket     = request.args.get("typical_ticket_sar",        type=float)
        customers  = request.args.get("expected_daily_customers",   type=int)
        hours      = request.args.get("operating_hours_per_day",    type=int)
        consumer   = request.args.get("is_consumer_facing",    "true").lower()  == "true"
        high_value = request.args.get("sells_high_value_items", "false").lower() == "true"
        payment    = request.args.get("expected_payment_mix",       default="mixed")
        late_night = request.args.get("operates_late_night",   "false").lower() == "true"
        biz_days   = request.args.get("business_days_per_week",     type=int, default=6)
        holds_inv  = request.args.get("holds_physical_inventory","false").lower() == "true"

        if not ticket or not customers or not hours:
            return jsonify({"error": (
                "typical_ticket_sar, expected_daily_customers, "
                "and operating_hours_per_day are required")}), 400

        intake = {
            "typical_ticket_sar":        ticket,
            "expected_daily_customers":  customers,
            "operating_hours_per_day":   hours,
            "is_consumer_facing":        consumer,
            "sells_high_value_items":    high_value,
            "expected_payment_mix":      payment,
            "operates_late_night":       late_night,
            "business_days_per_week":    biz_days,
            "holds_physical_inventory":  holds_inv,
        }

        clf_result = _classifier.classify_from_intake(intake)
        expense    = _estimator.estimate_from_intake(intake, _classifier)

        net_margin = expense["net_margin_estimate"]
        stab_tag   = expense["tags_used"].get("revenue_stability", "moderate")
        if net_margin > 0.35 and stab_tag in ("stable", "very_stable"):
            risk_ind = "low"
        elif net_margin > 0.20:
            risk_ind = "medium"
        else:
            risk_ind = "high"

        return jsonify({
            "cluster_id":            int(clf_result["cluster_id"]),
            "archetype_description": clf_result.get("archetype_description", "unknown"),
            "confidence":            float(clf_result["confidence"]),
            "refinement_status":     "predicted",
            "behavioral_profile":    expense["tags_used"],
            "expense_estimate": {
                "total_expense_ratio": expense["total_expense_ratio"],
                "breakdown":           expense["breakdown"],
                "net_margin_estimate": expense["net_margin_estimate"],
                "holds_inventory":     expense["holds_inventory"],
            },
            "preliminary_credit_profile": {
                "risk_indication": risk_ind,
                "note": ("Based on intake form only. "
                         "Connect POS data for full assessment."),
            },
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/incubator/transition-check/<business_id>")
def transition_check(business_id):
    try:
        if business_id not in VALID_BUSINESSES:
            return jsonify({"error": f"Unknown business: {business_id}"}), 404
        return jsonify(get_transition_result(business_id))
    except Exception as e:
        return jsonify({"error": str(e), "business_id": business_id}), 500


@app.route("/api/<business_id>/classify")
def get_classify(business_id):
    try:
        if business_id not in VALID_BUSINESSES:
            return jsonify({"error": f"Unknown business: {business_id}"}), 404
        tx = load_tx(business_id)
        tx["timestamp"] = pd.to_datetime(tx["timestamp"])
        meta = BUSINESSES[business_id]
        result = _classifier.classify_from_data(
            tx, bid=business_id,
            location=meta.get("location"), business_type=meta.get("type"),
            registration=meta.get("registration"))
        result["business_id"] = business_id
        result["business_name"] = meta["name"]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "business_id": business_id}), 500

# =============================================================================
# Portfolio endpoints
# =============================================================================

_portfolio_summary_cache = None

def _load_portfolio_summary():
    global _portfolio_summary_cache
    if _portfolio_summary_cache is None:
        summary_path = os.path.join(PORTFOLIO_DIR, "portfolio_summary.json")
        if not os.path.exists(summary_path):
            return None
        with open(summary_path, "r", encoding="utf-8") as f:
            _portfolio_summary_cache = json.load(f)
    return _portfolio_summary_cache


@app.route("/api/portfolio/summary")
def portfolio_summary():
    data = _load_portfolio_summary()
    if data is None:
        return jsonify({"error": "Portfolio not generated yet. Run data/generate_portfolio.py"}), 404
    return jsonify(data)


@app.route("/api/portfolio/stats")
def portfolio_stats():
    data = _load_portfolio_summary()
    if data is None:
        return jsonify({"error": "Portfolio not generated yet."}), 404

    from collections import Counter
    total          = len(data)
    risk_counts    = Counter(r["risk_tier"]    for r in data)
    fraud_counts   = Counter(r["fraud_status"] for r in data)
    arch_counts    = Counter(r["archetype_key"] for r in data)
    trend_counts   = Counter(r["revenue_trend"] for r in data)
    sme_ready      = sum(1 for r in data if r["sme_transition_ready"])
    avg_dscr       = round(sum(r["dscr_score"] for r in data) / total, 4)
    avg_daily_rev  = round(sum(r["avg_daily_revenue_sar"] for r in data) / total, 2)
    total_portfolio_rev = round(sum(r["avg_daily_revenue_sar"] * 365 for r in data), 0)

    return jsonify({
        "total_businesses":     total,
        "sme_transition_ready": sme_ready,
        "avg_dscr_score":       avg_dscr,
        "avg_daily_revenue_sar": avg_daily_rev,
        "total_portfolio_annual_revenue_sar": total_portfolio_rev,
        "risk_tier_distribution":    dict(risk_counts),
        "fraud_status_distribution": dict(fraud_counts),
        "archetype_distribution":    dict(arch_counts),
        "revenue_trend_distribution": dict(trend_counts),
    })


@app.route("/api/portfolio/business/<bid>")
def portfolio_business(bid):
    detail_path = os.path.join(PORTFOLIO_DIR, f"{bid}_detail.json")
    if not os.path.exists(detail_path):
        return jsonify({"error": f"Business {bid} not found in portfolio"}), 404
    with open(detail_path, "r", encoding="utf-8") as f:
        detail = json.load(f)
    return jsonify(detail)


# =============================================================================
# Error handlers
# =============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": str(e.description)}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# Load models at import time so gunicorn workers are warm on first request.
# The _models_loaded flag ensures this is a no-op on subsequent calls.
load_models()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
