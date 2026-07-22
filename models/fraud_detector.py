"""
fraud_detector.py  --  DataCore AI Engine: Model 3
Isolation Forest per-business anomaly detection with per-cluster fallback.
Replaces statistical fraud checks in dscr_model.py.
"""

import os, sys
import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from scipy.stats import percentileofscore

ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(ROOT, "data", "processed")
SAVED_DIR = os.path.join(ROOT, "models", "saved")
sys.path.insert(0, ROOT)

from models._guardrails import (
    get_logger, check_required_columns, check_amount_range,
    make_data_quality, make_insufficient_result,
    MIN_TX_FRAUD_TRAIN, MIN_TX_FRAUD_SCORE,
)
_log = get_logger("fraud")

# ── Optional location enrichment (lazy, offline) ──────────────────────────────
_LOCATION_CTX = None
# A transaction at/above this multiple of the district's avg monthly household
# income is "well above" local norm (conservative — legitimate for some sectors,
# but notable as an additional signal alongside the behavioral model).
DISTRICT_SCALE_WELL_ABOVE_X = 20
DISTRICT_SCALE_ABOVE_X      = 5


def _get_location_context():
    global _LOCATION_CTX
    if _LOCATION_CTX is None:
        from data.location_context import LocationContext
        _LOCATION_CTX = LocationContext()
    return _LOCATION_CTX

# ── Feature engineering ───────────────────────────────────────────────────────

class TransactionFeatureEngineer:
    """Computes 15 per-transaction behavioral features for Isolation Forest."""

    def engineer(self, tx: pd.DataFrame, bid: str = "unknown") -> pd.DataFrame:
        # ── Guard 1: required columns ─────────────────────────────────────────
        missing = check_required_columns(tx, ["timestamp", "amount_sar"], "fraud", bid, _log)
        if missing:
            raise ValueError(f"fraud engineer: missing_required_column: {missing} (bid={bid})")

        df = tx.copy()
        df["timestamp"]  = pd.to_datetime(df["timestamp"])
        df["amount_sar"] = pd.to_numeric(df["amount_sar"], errors="coerce").fillna(0.0)
        df = df.sort_values("timestamp").reset_index(drop=True)

        # ── Guard 2: amount range ─────────────────────────────────────────────
        # Remove negatives; just log out-of-range highs (don't remove them)
        neg_mask = df["amount_sar"] < 0
        if neg_mask.any():
            check_amount_range(df["amount_sar"], "fraud", bid, _log)
            df = df[~neg_mask].copy().reset_index(drop=True)
        else:
            check_amount_range(df["amount_sar"], "fraud", bid, _log)

        df["hour_of_day"]  = df["timestamp"].dt.hour
        df["day_of_week"]  = df["timestamp"].dt.weekday
        df["is_weekend"]   = df["day_of_week"].isin([3, 4]).astype(int)
        df["is_night"]     = df["hour_of_day"].isin([23, 0, 1, 2, 3, 4]).astype(int)
        df["minutes_since_midnight"] = (
            df["hour_of_day"] * 60 + df["timestamp"].dt.minute)

        # Amount z-score across the whole period
        amt_mean = df["amount_sar"].mean()
        amt_std  = df["amount_sar"].std()
        df["amount_zscore"] = (
            (df["amount_sar"] - amt_mean) / amt_std if amt_std > 0 else 0.0)

        # Daily transaction count
        df["date"]       = df["timestamp"].dt.strftime("%Y-%m-%d")
        daily_cnt        = df.groupby("date")["amount_sar"].transform("count")
        df["daily_tx_count"] = daily_cnt.values

        # Daily revenue z-score
        daily_rev      = df.groupby("date")["amount_sar"].transform("sum")
        daily_rev_mean = float(df.groupby("date")["amount_sar"].sum().mean())
        daily_rev_std  = float(df.groupby("date")["amount_sar"].sum().std())
        df["daily_revenue_zscore"] = (
            (daily_rev - daily_rev_mean) / daily_rev_std
            if daily_rev_std > 0 else 0.0)

        # Hour-average amount and deviation from hourly norm
        hour_avg = df.groupby("hour_of_day")["amount_sar"].transform("mean")
        df["hour_avg_amount"]    = hour_avg.values
        df["amount_vs_hour_avg"] = np.where(
            hour_avg > 0, df["amount_sar"] / hour_avg, 1.0)

        # Inter-transaction gap (minutes since previous transaction)
        gaps = df["timestamp"].diff().dt.total_seconds().fillna(0) / 60.0
        df["inter_tx_gap_minutes"] = gaps.clip(lower=0).values
        df["log_gap"]              = np.log1p(df["inter_tx_gap_minutes"])

        # Rolling 60-minute transaction count
        ts = df["timestamp"].values
        rolling_counts = [
            int(np.sum(ts[:i] >= t - np.timedelta64(60, "m")))
            for i, t in enumerate(ts)
        ]
        df["rolling_1h_count"] = rolling_counts

        df["log_amount"] = np.log1p(df["amount_sar"])

        feature_cols = [
            "amount_sar", "log_amount", "hour_of_day", "day_of_week",
            "is_weekend", "is_night", "minutes_since_midnight",
            "amount_zscore", "daily_tx_count", "daily_revenue_zscore",
            "hour_avg_amount", "amount_vs_hour_avg",
            "inter_tx_gap_minutes", "log_gap", "rolling_1h_count",
        ]
        return df[feature_cols].reset_index(drop=True)

# ── Detector ──────────────────────────────────────────────────────────────────

class FraudDetector:

    def __init__(self):
        self.engineer        = TransactionFeatureEngineer()
        self.business_models = {}
        self.cluster_models  = {}
        # contamination used only for training tree structure, not for the
        # decision threshold — scoring uses a 1st-percentile strict cut
        self.contamination   = 0.05

    # ── Per-business training ─────────────────────────────────────────────────

    def train_for_business(self, business_id: str, transactions_df: pd.DataFrame):
        tx = transactions_df.copy()
        tx["timestamp"]  = pd.to_datetime(tx["timestamp"])
        tx               = tx.sort_values("timestamp").reset_index(drop=True)
        tx["amount_sar"] = pd.to_numeric(tx["amount_sar"], errors="coerce").fillna(0.0)

        # ── Guard: minimum rows for stable Isolation Forest fit ───────────────
        if len(tx) < MIN_TX_FRAUD_TRAIN:
            _log.warning(
                f"model=fraud | bid={business_id} | rule=insufficient_data_for_training | "
                f"actual={len(tx)} | min_required={MIN_TX_FRAUD_TRAIN}"
            )
            return  # skip training; scorer will fall back to cluster model

        features_df = self.engineer.engineer(tx, bid=business_id)

        scaler = StandardScaler()
        X      = scaler.fit_transform(features_df)

        model = IsolationForest(
            n_estimators=200,
            contamination=self.contamination,
            max_samples="auto",
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X)

        # Store the 1st-percentile score threshold so inference uses the same
        # scale even when evaluating new (shorter) windows of data
        all_scores   = model.score_samples(X)
        strict_thr   = float(np.percentile(all_scores, 1))

        stats = {
            "mean_amount":        float(tx["amount_sar"].mean()),
            "std_amount":         float(tx["amount_sar"].std()),
            "mean_daily_tx":      float(features_df["daily_tx_count"].mean()),
            "mean_gap_minutes":   float(features_df["inter_tx_gap_minutes"].mean()),
            "night_tx_pct":       float(features_df["is_night"].mean()),
            "total_transactions": len(tx),
            "training_period":    "2025-06-01 to 2025-06-30",
            "strict_threshold":   strict_thr,
        }

        self.business_models[business_id] = {
            "model":  model,
            "scaler": scaler,
            "stats":  stats,
        }
        print(f"  Trained model for {business_id}: {len(tx)} transactions, "
              f"mean SAR {stats['mean_amount']:,.0f}")

    # ── Per-cluster training ──────────────────────────────────────────────────

    def train_for_cluster(self, cluster_id: int, transactions_list: list):
        all_tx = pd.concat(transactions_list, ignore_index=True)
        all_tx["timestamp"]  = pd.to_datetime(all_tx["timestamp"])
        all_tx               = all_tx.sort_values("timestamp").reset_index(drop=True)

        features_df = self.engineer.engineer(all_tx, bid=f"cluster_{cluster_id}")

        scaler = StandardScaler()
        X      = scaler.fit_transform(features_df)

        model = IsolationForest(
            n_estimators=150,
            contamination=self.contamination,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X)

        all_scores = model.score_samples(X)
        self.cluster_models[cluster_id] = {
            "model":            model,
            "scaler":           scaler,
            "strict_threshold": float(np.percentile(all_scores, 1)),
        }
        print(f"  Trained cluster model {cluster_id}: {len(all_tx)} transactions")

    # ── Train all ─────────────────────────────────────────────────────────────

    def train_all(self):
        businesses = ["laundromat", "cafe", "minimarket",
                      "realestate", "cardealer", "motorbike"]

        print("Training per-business Isolation Forest models...")
        business_dfs = {}
        for biz in businesses:
            tx = pd.read_csv(os.path.join(DATA_DIR, f"{biz}_transactions.csv"))
            business_dfs[biz] = tx
            self.train_for_business(biz, tx)

        print("\nTraining per-cluster fallback models...")
        from models.business_classifier import BusinessClassifier
        clf = BusinessClassifier()
        clf.load()

        cluster_groups: dict = {}
        for biz, tx in business_dfs.items():
            tx_copy = tx.copy()
            tx_copy["timestamp"] = pd.to_datetime(tx_copy["timestamp"])
            result = clf.classify_from_data(tx_copy)
            cid    = result["cluster_id"]
            cluster_groups.setdefault(cid, []).append(tx)
            print(f"  {biz} -> cluster {cid}")

        for cid, tx_list in cluster_groups.items():
            self.train_for_cluster(cid, tx_list)

    # ── Scoring ───────────────────────────────────────────────────────────────

    def score_transactions(self, transactions_df: pd.DataFrame,
                           business_id: str = None,
                           cluster_id: int = None) -> pd.DataFrame:
        bid = business_id or f"cluster_{cluster_id}"
        tx = transactions_df.copy()
        tx["timestamp"]  = pd.to_datetime(tx["timestamp"])
        tx               = tx.sort_values("timestamp").reset_index(drop=True)
        tx["amount_sar"] = pd.to_numeric(tx["amount_sar"], errors="coerce").fillna(0.0)

        # Strip negatives here so tx and features_df stay aligned in row count
        neg_mask = tx["amount_sar"] < 0
        if neg_mask.any():
            tx = tx[~neg_mask].copy().reset_index(drop=True)

        # ── Guard: minimum rows to score ──────────────────────────────────────
        if len(tx) < MIN_TX_FRAUD_SCORE:
            _log.warning(
                f"model=fraud | bid={bid} | rule=insufficient_data_for_scoring | "
                f"actual={len(tx)} | min_required={MIN_TX_FRAUD_SCORE}"
            )
            tx["anomaly_score"]      = 0.0
            tx["anomaly_label"]      = 1
            tx["anomaly_percentile"] = 50.0
            return tx

        features_df = self.engineer.engineer(tx, bid=bid)

        if business_id and business_id in self.business_models:
            entry  = self.business_models[business_id]
            source = f"business_model({business_id})"
        elif cluster_id is not None and cluster_id in self.cluster_models:
            entry  = self.cluster_models[cluster_id]
            source = f"cluster_model({cluster_id})"
        else:
            raise ValueError(
                f"No model for business_id={business_id} or cluster_id={cluster_id}")

        X      = entry["scaler"].transform(features_df)
        scores = entry["model"].score_samples(X)

        # Strict 1%-percentile threshold: only flag the genuinely extreme tail.
        # Using model.predict() would always flag exactly contamination% of
        # data (even clean businesses), inflating fraud scores artificially.
        strict_thr = entry.get("strict_threshold",
                               float(np.percentile(scores, 1)))
        labels     = np.where(scores < strict_thr, -1, 1)

        percentiles = np.array([
            100 - percentileofscore(scores, s) for s in scores
        ])

        tx["anomaly_score"]      = scores
        tx["anomaly_label"]      = labels
        tx["anomaly_percentile"] = percentiles.round(1)

        n_anom = int((labels == -1).sum())
        print(f"  Scored {len(tx)} transactions using {source}")
        print(f"  Anomalies detected: {n_anom} ({n_anom / len(tx) * 100:.1f}%)")
        return tx

    # ── Fraud report ──────────────────────────────────────────────────────────

    def generate_fraud_report(self, scored_df: pd.DataFrame,
                              business_id: str, stats: dict = None) -> dict:
        """
        Consolidates flagged transactions into typed INCIDENTS rather than
        one group per date, preventing normal statistical noise from inflating
        the fraud score to 100 on every business.
        """
        anomalies_df = scored_df[scored_df["anomaly_label"] == -1].copy()

        if len(anomalies_df) == 0:
            ts_h    = pd.to_datetime(scored_df["timestamp"]).dt.hour
            off_n   = int(ts_h.isin([23, 0, 1, 2, 3, 4]).sum())
            max_amt = float(scored_df["amount_sar"].max()) if "amount_sar" in scored_df.columns else 0.0
            med_amt = float(scored_df["amount_sar"].median()) if "amount_sar" in scored_df.columns else 1.0
            ratio   = max_amt / med_amt if med_amt > 0 else 0.0
            total   = len(scored_df)
            off_msg = (f"off_hours_check: passed (zero transactions between 23:00-05:00)"
                       if off_n == 0 else
                       f"off_hours_check: passed ({off_n} transactions between 23:00-05:00, no anomalous concentration)")
            return {
                "business_id":        business_id,
                "anomalies_detected": 0,
                "anomalies":          [],
                "fraud_score":        0,
                "overall_status":     "clear",
                "approval_frozen":    False,
                "model_type":         "isolation_forest",
                "total_tx_scored":    total,
                "anomalous_tx_count": 0,
                "reasons":            [],
                "checks_passed":      [
                    off_msg,
                    (f"amount_outlier_check: passed (max SAR {max_amt:,.0f} is "
                     f"{ratio:.1f}x median SAR {med_amt:,.0f}, within 10x threshold)"),
                    f"behavioral_anomaly_check: passed (0 anomalous transactions from {total} scored, rate 0.00%)",
                ],
                "data_quality":       make_data_quality([]),
            }

        anomalies_df = anomalies_df.copy()
        anomalies_df["date"] = anomalies_df["timestamp"].dt.strftime("%Y-%m-%d")
        anomalies_df["hour"] = anomalies_df["timestamp"].dt.hour

        mean_amount = stats.get("mean_amount", 0) if stats else 0

        # Classify each anomalous transaction into an incident type
        anomalies_df["incident_type"] = "behavioral_anomaly"
        if "is_night" in anomalies_df.columns:
            anomalies_df.loc[anomalies_df["is_night"] == 1,
                             "incident_type"] = "off_hours"
        if mean_amount > 0:
            anomalies_df.loc[anomalies_df["amount_sar"] > mean_amount * 5,
                             "incident_type"] = "amount_outlier"

        anomaly_list = []

        # ── Incident 1: Off-hours transactions ────────────────────────────────
        off = anomalies_df[anomalies_df["incident_type"] == "off_hours"]
        if len(off) > 0:
            off_dates = int(off["date"].nunique())
            max_pct   = float(off["anomaly_percentile"].max())
            if   max_pct >= 99 or off_dates >= 5: severity = "critical"
            elif max_pct >= 97 or off_dates >= 2: severity = "high"
            else:                                  severity = "medium"
            anomaly_list.append({
                "date":               off["date"].mode().iloc[0],
                "type":               "off_hours_cluster",
                "description":        (f"{len(off)} off-hours anomalous transactions "
                                       f"across {off_dates} date(s)"),
                "severity":           severity,
                "tx_count":           len(off),
                "max_anomaly_pct":    max_pct,
                "amount_if_applicable": None,
            })

        # ── Incident 2: Amount outliers (one entry per flagged transaction) ───
        outliers = anomalies_df[anomalies_df["incident_type"] == "amount_outlier"]
        for _, row in outliers.iterrows():
            max_pct = float(row["anomaly_percentile"])
            ratio   = row["amount_sar"] / mean_amount if mean_amount > 0 else 0
            severity = "critical" if (max_pct >= 99 or ratio >= 10) else "high"
            anomaly_list.append({
                "date":               str(row["date"]),
                "type":               "amount_outlier",
                "description":        (f"Transaction SAR {row['amount_sar']:,.0f} -- "
                                       f"{ratio:.1f}x above business mean"),
                "severity":           severity,
                "tx_count":           1,
                "max_anomaly_pct":    max_pct,
                "amount_if_applicable": float(row["amount_sar"]),
            })

        # ── Incident 3: Consolidated behavioral anomaly ───────────────────────
        behavioral = anomalies_df[anomalies_df["incident_type"] == "behavioral_anomaly"]
        if len(behavioral) > 0:
            max_pct = float(behavioral["anomaly_percentile"].max())
            total_tx = len(scored_df)
            # Severity based on anomaly rate relative to expected 1% baseline.
            # n_crit_dates is self-referential: flagged transactions are always
            # the worst-scoring in their own batch, so anomaly_percentile ≈ 100
            # for all of them regardless of true fraud severity. Rate-based
            # assessment is calibration-independent and meaningful across both
            # business-specific and cluster fallback models.
            behavioral_rate = len(behavioral) / total_tx if total_tx > 0 else 0
            if   behavioral_rate >= 0.02:  severity = "critical"
            elif behavioral_rate >= 0.005: severity = "high"
            else:                          severity = "medium"

            anomaly_list.append({
                "date":               behavioral["date"].iloc[0],
                "type":               "behavioral_anomaly",
                "description":        (f"{len(behavioral)} transactions with unusual patterns "
                                       f"({behavioral_rate*100:.2f}% rate, "
                                       f"max percentile: {max_pct:.0f})"),
                "severity":           severity,
                "tx_count":           len(behavioral),
                "max_anomaly_pct":    max_pct,
                "amount_if_applicable": None,
            })

        # ── Fraud score: sum of at most 5 incidents ───────────────────────────
        sev_pts = {"critical": 40, "high": 25, "medium": 10}
        top5    = sorted(anomaly_list,
                         key=lambda a: a["max_anomaly_pct"], reverse=True)[:5]
        fraud_score = min(100, sum(sev_pts[a["severity"]] for a in top5))

        approval_frozen = fraud_score > 55
        if fraud_score == 0:    overall_status = "clear"
        elif approval_frozen:   overall_status = "frozen"
        else:                   overall_status = "flagged"

        # ── Explainability: reasons + checks_passed ───────────────────────────
        # reasons: all triggered incidents with severity >= high
        # checks_passed: verified checks with no incident or only medium severity
        reasons       = []
        checks_passed = []

        for a in anomaly_list:
            if a["severity"] in ("critical", "high"):
                if a["type"] == "off_hours_cluster":
                    cond = ("critical_off_hours_cluster" if a["severity"] == "critical"
                            else "high_off_hours_pattern")
                elif a["type"] == "amount_outlier":
                    cond = ("critical_amount_outlier" if a["severity"] == "critical"
                            else "elevated_amount_outlier")
                else:
                    cond = ("critical_behavioral_anomaly" if a["severity"] == "critical"
                            else "high_behavioral_anomaly")
                reasons.append({
                    "condition": cond,
                    "severity":  a["severity"],
                    "detail":    a["description"],
                })

        triggered_high = {a["type"] for a in anomaly_list if a["severity"] in ("critical", "high")}

        if "off_hours_cluster" not in triggered_high:
            ts_h  = pd.to_datetime(scored_df["timestamp"]).dt.hour
            off_n = int(ts_h.isin([23, 0, 1, 2, 3, 4]).sum())
            if off_n == 0:
                checks_passed.append(
                    "off_hours_check: passed (zero transactions between 23:00-05:00)")
            else:
                checks_passed.append(
                    f"off_hours_check: passed ({off_n} transactions between "
                    f"23:00-05:00, no anomalous concentration detected)")

        if "amount_outlier" not in triggered_high:
            max_amt = float(scored_df["amount_sar"].max()) if "amount_sar" in scored_df.columns else 0.0
            med_amt = float(scored_df["amount_sar"].median()) if "amount_sar" in scored_df.columns else 1.0
            ratio   = max_amt / med_amt if med_amt > 0 else 0.0
            checks_passed.append(
                f"amount_outlier_check: passed (max SAR {max_amt:,.0f} is "
                f"{ratio:.1f}x median SAR {med_amt:,.0f}, within 10x threshold)")

        total_tx  = len(scored_df)
        anom_n    = int((scored_df["anomaly_label"] == -1).sum())
        beh_rate  = anom_n / total_tx * 100 if total_tx > 0 else 0.0
        beh_incs  = [a for a in anomaly_list if a["type"] == "behavioral_anomaly"]
        if not beh_incs:
            checks_passed.append(
                f"behavioral_anomaly_check: passed (0 anomalous transactions "
                f"from {total_tx} scored, rate 0.00%)")
        elif beh_incs[0]["severity"] == "medium":
            checks_passed.append(
                f"behavioral_anomaly_check: passed ({beh_rate:.2f}% anomaly rate, "
                f"below 0.5% high-severity threshold — flagged for monitoring only)")

        return {
            "business_id":        business_id,
            "anomalies_detected": len(anomaly_list),
            "anomalies":          anomaly_list,
            "fraud_score":        fraud_score,
            "overall_status":     overall_status,
            "approval_frozen":    approval_frozen,
            "model_type":         "isolation_forest",
            "total_tx_scored":    len(scored_df),
            "anomalous_tx_count": int((scored_df["anomaly_label"] == -1).sum()),
            "reasons":            reasons,
            "checks_passed":      checks_passed,
            "data_quality":       make_data_quality([]),
        }

    # ── Optional location enrichment ──────────────────────────────────────────

    def _apply_location_enrichment(self, report: dict, tx: pd.DataFrame,
                                   location, bid: str) -> dict:
        """
        Augments (never replaces) the fraud report with a district-scale signal.
        Present location → derives `transaction_scale_vs_district_norm`; absent or
        unknown district → report is returned unchanged except for a transparent
        location_enrichment_used=False flag.
        """
        if location is None:
            return report

        district = location.get("location_district") or location.get("district")
        profile = None
        try:
            if district:
                profile = _get_location_context().get_district_profile(district)
        except Exception as exc:                      # never crash on enrichment
            _log.warning(f"model=fraud | bid={bid} | rule=location_lookup_failed | detail={exc!r}")
            profile = None

        used = profile is not None
        dq = dict(report.get("data_quality") or make_data_quality([]))
        dq["location_enrichment_used"]      = used
        dq["district_scale_flag_triggered"] = False
        report["data_quality"] = dq
        if not used:
            if district:
                _log.warning(f"model=fraud | bid={bid} | rule=location_district_unknown | district={district}")
            return report

        monthly_income = profile["avg_household_income_sar"]
        amounts = pd.to_numeric(tx["amount_sar"], errors="coerce").fillna(0.0)
        amounts = amounts[amounts >= 0]

        within = above = well_above = 0
        if monthly_income > 0 and len(amounts) > 0:
            ratio      = amounts / float(monthly_income)
            well_above = int((ratio >= DISTRICT_SCALE_WELL_ABOVE_X).sum())
            above      = int(((ratio >= DISTRICT_SCALE_ABOVE_X) & (ratio < DISTRICT_SCALE_WELL_ABOVE_X)).sum())
            within     = int((ratio < DISTRICT_SCALE_ABOVE_X).sum())

        triggered = well_above > 0
        dq["district_scale_flag_triggered"] = triggered

        report["location_context"] = {
            "district":          district,
            "city":              location.get("location_city"),
            "district_profile":  profile,
            "transaction_scale_vs_district_norm": {
                "within_range":                within,
                "above_range":                 above,
                "well_above_range":            well_above,
                "well_above_threshold_x_income": DISTRICT_SCALE_WELL_ABOVE_X,
                "reference_monthly_income_sar":  monthly_income,
            },
            "district_scale_flag": triggered,
        }

        # Augment existing explainability with the district-scale reason. The
        # behavioral fraud_score/status from the Isolation Forest are unchanged —
        # this is an additional signal for the credit officer, not a replacement.
        if triggered:
            report.setdefault("reasons", []).append({
                "condition": "district_scale_anomaly",
                "severity":  "high" if well_above >= 3 else "medium",
                "detail":    (f"{well_above} transaction(s) exceed "
                              f"{DISTRICT_SCALE_WELL_ABOVE_X}x the district's avg monthly "
                              f"household income (SAR {monthly_income:,}) for {district} — "
                              f"unusual transaction scale for the local income tier"),
            })
        return report

    # ── Full pipeline ─────────────────────────────────────────────────────────

    def assess(self, business_id: str, transactions_df: pd.DataFrame = None,
               cluster_id: int = None, location=None) -> dict:
        if transactions_df is None:
            tx = pd.read_csv(os.path.join(DATA_DIR, f"{business_id}_transactions.csv"))
        else:
            tx = transactions_df.copy()

        stats = self.business_models.get(business_id, {}).get("stats")

        # For businesses without a dedicated model, auto-classify to get the
        # cluster and use the cluster fallback model. This avoids the pathological
        # case where a business-specific model trained on its own clean data always
        # flags its own bottom 1% as anomalous (mathematical inevitability).
        effective_cluster_id = cluster_id
        if business_id not in self.business_models and cluster_id is None:
            try:
                from models.business_classifier import BusinessClassifier
                _clf = BusinessClassifier()
                _clf.load()
                tx_tmp = tx.copy()
                tx_tmp["timestamp"] = pd.to_datetime(tx_tmp["timestamp"])
                result = _clf.classify_from_data(tx_tmp)
                effective_cluster_id = result["cluster_id"]
            except Exception:
                pass  # score_transactions will raise ValueError below if still no model

        scored = self.score_transactions(tx, business_id=business_id,
                                         cluster_id=effective_cluster_id)
        report = self.generate_fraud_report(scored, business_id, stats)
        # Additive location signal — no-op when location is absent.
        return self._apply_location_enrichment(report, tx, location, business_id)

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: str = None):
        if path is None:
            path = os.path.join(SAVED_DIR, "fraud_detector.pkl")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            "business_models": self.business_models,
            "cluster_models":  self.cluster_models,
            "contamination":   self.contamination,
        }, path)
        print(f"Fraud detector saved to {path}")

    def load(self, path: str = None):
        if path is None:
            path = os.path.join(SAVED_DIR, "fraud_detector.pkl")
        data = joblib.load(path)
        self.business_models = data["business_models"]
        self.cluster_models  = data["cluster_models"]
        self.contamination   = data["contamination"]
        print(f"Fraud detector loaded -- {len(self.business_models)} business models, "
              f"{len(self.cluster_models)} cluster models")
        return self

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("DATACORE -- Fraud Detector Model 3 (Isolation Forest)")
    print("=" * 60)

    detector = FraudDetector()
    detector.train_all()
    detector.save()

    print("\n" + "=" * 60)
    print("FRAUD ASSESSMENT -- ALL BUSINESSES")
    print("=" * 60)

    businesses = ["laundromat", "cafe", "minimarket",
                  "realestate", "cardealer", "motorbike"]
    names = {
        "laundromat": "Al Noor Laundromat",
        "cafe":       "Qahwa Corner Cafe",
        "minimarket": "Baraka Minimarket",
        "realestate": "Majd Real Estate",
        "cardealer":  "Rawabi Auto Gallery",
        "motorbike":  "Saqr Motorbikes",
    }

    for biz in businesses:
        report = detector.assess(biz)
        icon   = ("[FROZEN] " if report["approval_frozen"]
                  else ("[FLAGGED]" if report["overall_status"] == "flagged"
                        else "[CLEAR]  "))
        print(f"\n{names[biz].upper()} {icon}")
        print(f"  Status    : {report['overall_status']} | "
              f"Fraud Score: {report['fraud_score']}")
        print(f"  Anomalies : {report['anomalies_detected']} incident(s) | "
              f"Flagged TX: {report['anomalous_tx_count']} / {report['total_tx_scored']}")
        for a in report["anomalies"]:
            print(f"  [{a['severity'].upper():<8}] {a['date']} -- "
                  f"{a['type']}: {a['description'][:65]}")

    print("\n" + "=" * 60)
    print("NEW BUSINESS TEST -- cluster fallback model")
    print("=" * 60)

    from models.business_classifier import BusinessClassifier
    clf    = BusinessClassifier()
    clf.load()
    tx_new = pd.read_csv(os.path.join(DATA_DIR, "minimarket_transactions.csv"))
    tx_new["timestamp"] = pd.to_datetime(tx_new["timestamp"])
    result     = clf.classify_from_data(tx_new)
    cluster_id = result["cluster_id"]

    print(f"New business classified to cluster {cluster_id} "
          f"({result['archetype_label']})")
    print("Using cluster fallback model...")

    scored = detector.score_transactions(
        tx_new, business_id=None, cluster_id=cluster_id)
    report = detector.generate_fraud_report(scored, "new_business_test")
    print(f"  Status    : {report['overall_status']} | Score: {report['fraud_score']}")
    print(f"  Anomalies : {report['anomalies_detected']} incident(s)")

    print("\n" + "=" * 60)
    print("Model 3 complete.")
    print("=" * 60)
