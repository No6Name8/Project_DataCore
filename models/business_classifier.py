"""
business_classifier.py  --  DataCore AI Engine: Model 1
Unsupervised business classifier using HDBSCAN + PCA.
Classifies any business by behavioral fingerprint alone.
Zero hardcoded business-type labels in the inference pipeline.
"""

import os, sys, warnings
import numpy as np
import pandas as pd
import joblib
from collections import OrderedDict

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

warnings.filterwarnings("ignore")

try:
    import hdbscan
except ImportError:
    sys.exit("ERROR: hdbscan not installed. Run: pip install hdbscan")

ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(ROOT, "data", "processed")
SAVED_DIR = os.path.join(ROOT, "models", "saved")
sys.path.insert(0, ROOT)

ALL_DATES = pd.date_range("2025-04-01", "2025-06-30").strftime("%Y-%m-%d").tolist()

# ── Stage 1: Feature extractor ────────────────────────────────────────────────

class BusinessFeatureExtractor:
    """Converts raw transaction CSV into a 15-dim behavioral fingerprint."""

    def extract(self, tx: pd.DataFrame) -> dict:
        tx = tx.copy()
        tx["timestamp"] = pd.to_datetime(tx["timestamp"])
        tx["amount_sar"] = tx["amount_sar"].astype(float)
        tx["hour"]  = tx["timestamp"].dt.hour
        tx["date"]  = tx["timestamp"].dt.strftime("%Y-%m-%d")
        tx["wday"]  = tx["timestamp"].dt.weekday   # Mon=0 ... Sun=6

        amounts = tx["amount_sar"]
        n       = len(tx)

        # Ticket size features
        avg_ticket    = float(amounts.mean())
        median_ticket = float(amounts.median())
        ticket_cv     = float(amounts.std() / avg_ticket) if avg_ticket > 0 else 0.0
        p10 = float(amounts.quantile(0.10))
        p90 = float(amounts.quantile(0.90))
        ticket_p90_p10 = (p90 / p10) if p10 > 0 else p90

        # Transaction volume features
        days_active          = tx["date"].nunique()
        n_hist_days          = float(len(ALL_DATES))
        avg_daily_tx         = n / n_hist_days
        transaction_velocity = float(avg_daily_tx / 24.0)
        active_days_ratio    = days_active / n_hist_days

        # Temporal pattern features
        hour_counts = tx["hour"].value_counts()
        peak_hour_share = float(hour_counts.max() / n) if n > 0 else 0.0

        night_mask  = tx["hour"].isin([23, 0, 1, 2, 3, 4])
        night_ratio = float(night_mask.sum() / n) if n > 0 else 0.0

        # Weekend lift: Saudi consumer weekend is Thu(3)/Fri(4)
        wknd_mask = tx["wday"].isin([3, 4])
        wknd_rev  = tx[wknd_mask]["amount_sar"].sum()
        wkdy_rev  = tx[~wknd_mask]["amount_sar"].sum()
        wknd_ct   = wknd_mask.sum()
        wkdy_ct   = (~wknd_mask).sum()
        wknd_avg  = wknd_rev / wknd_ct if wknd_ct > 0 else 0.0
        wkdy_avg  = wkdy_rev / wkdy_ct if wkdy_ct > 0 else 0.0
        weekend_lift = (wknd_avg / wkdy_avg) if wkdy_avg > 0 else 1.0

        # Shannon entropy over hourly distribution (normalized 0-1)
        probs = (hour_counts / n).values
        raw_entropy  = -float(np.sum(probs * np.log2(probs + 1e-12)))
        hour_entropy = raw_entropy / np.log2(24)

        # Revenue variability
        daily_rev  = tx.groupby("date")["amount_sar"].sum().reindex(ALL_DATES, fill_value=0.0)
        rev_mean   = float(daily_rev.mean())
        revenue_cv = float(daily_rev.std() / rev_mean) if rev_mean > 0 else 0.0

        # Inter-transaction gap variability (minutes between consecutive transactions)
        if n > 1:
            sorted_ts = tx["timestamp"].sort_values().reset_index(drop=True)
            gaps_min  = sorted_ts.diff().dt.total_seconds().dropna() / 60.0
            gap_mean  = float(gaps_min.mean())
            itg_cv    = float(gaps_min.std() / gap_mean) if gap_mean > 0 else 0.0
        else:
            itg_cv = 0.0

        # Payment method features
        if "payment_method" in tx.columns:
            pm = tx["payment_method"].str.lower()
            digital_ratio = float(pm.isin(["mada", "credit_card", "apple_pay"]).sum() / n)
            cash_ratio    = float((pm == "cash").sum() / n)
        else:
            digital_ratio = 0.5
            cash_ratio    = 0.5

        return {
            "avg_ticket_sar":            round(avg_ticket, 4),
            "median_ticket_sar":         round(median_ticket, 4),
            "ticket_cv":                 round(ticket_cv, 4),
            "ticket_p90_p10_ratio":      round(float(ticket_p90_p10), 4),
            "avg_daily_transactions":    round(avg_daily_tx, 4),
            "transaction_velocity":      round(transaction_velocity, 6),
            "active_days_ratio":         round(active_days_ratio, 4),
            "peak_hour_concentration":   round(peak_hour_share, 4),
            "night_transaction_ratio":   round(night_ratio, 4),
            "weekend_lift":              round(float(weekend_lift), 4),
            "hour_entropy":              round(hour_entropy, 4),
            "revenue_cv":                round(revenue_cv, 4),
            "inter_transaction_gap_cv":  round(itg_cv, 4),
            "digital_payment_ratio":     round(digital_ratio, 4),
            "cash_ratio":                round(cash_ratio, 4),
        }

    def extract_from_intake(self, intake_dict: dict) -> OrderedDict:
        """
        Maps intake form answers to the same 15-feature vector format
        as extract(). Used for Track 2 (zero transaction history).
        """
        t          = intake_dict
        ticket     = float(t["typical_ticket_sar"])
        daily_tx   = float(t["expected_daily_customers"])
        hours      = float(t["operating_hours_per_day"])
        consumer   = bool(t["is_consumer_facing"])
        high_value = bool(t["sells_high_value_items"])
        payment    = t["expected_payment_mix"]
        late_night = bool(t["operates_late_night"])
        biz_days   = float(t["business_days_per_week"])

        digital_ratio = 0.2 if payment == "mostly_cash" else (0.8 if payment == "mostly_digital" else 0.5)
        cash_ratio    = 0.7 if payment == "mostly_cash" else (0.1 if payment == "mostly_digital" else 0.35)

        return OrderedDict([
            ("avg_ticket_sar",            ticket),
            ("median_ticket_sar",         ticket * 0.85),
            ("ticket_cv",                 0.8 if high_value else 0.3),
            ("ticket_p90_p10_ratio",      8.0 if high_value else 2.5),
            ("avg_daily_transactions",    daily_tx),
            ("transaction_velocity",      daily_tx / hours),
            ("active_days_ratio",         biz_days / 7.0),
            ("peak_hour_concentration",   0.10 if consumer else 0.16),
            ("night_transaction_ratio",   0.015 if late_night else 0.005),
            ("weekend_lift",              1.05 if consumer else 0.80),
            ("hour_entropy",              0.80 if consumer else 0.60),
            ("revenue_cv",                0.65 if high_value else 0.28),
            ("inter_transaction_gap_cv",  1.30 if high_value else (3.00 if ticket < 50 else 1.60)),
            ("digital_payment_ratio",     digital_ratio),
            ("cash_ratio",                cash_ratio),
        ])

    def blend(self, real_features: dict, intake_features: dict,
              real_data_days: int) -> OrderedDict:
        """
        Blends real data features with intake features during transition.
        Weight shifts from intake toward real data as days accumulate.
        At 30 days: 100% real data. At 0 days: 100% intake.
        """
        weight_real   = min(real_data_days / 30.0, 1.0)
        weight_intake = 1.0 - weight_real
        blended = OrderedDict()
        for key in real_features:
            blended[key] = (real_features[key] * weight_real +
                            intake_features[key] * weight_intake)
        return blended

FEATURE_COLS = [
    "avg_ticket_sar", "median_ticket_sar", "ticket_cv", "ticket_p90_p10_ratio",
    "avg_daily_transactions", "transaction_velocity", "active_days_ratio",
    "peak_hour_concentration", "night_transaction_ratio", "weekend_lift",
    "hour_entropy", "revenue_cv", "inter_transaction_gap_cv",
    "digital_payment_ratio", "cash_ratio",
]

# Indices of features to log1p-transform before scaling (wide-range ticket + volume)
_LOG_COLS = [0, 1, 4, 5]  # avg_ticket, median_ticket, avg_daily_tx, velocity

# ── Stage 2: Synthetic business generator ────────────────────────────────────
# Archetype means are calibrated against the real extracted feature values
# for the 6 known Saudi SME businesses. The other 6 archetypes are positioned
# to be distinct from the anchors and from each other.
#
# Each spec tuple: (mean, tight_std) — std is ~5% of mean so blobs don't bleed.

ARCHETYPES = {

    # ── Anchored to real extracted data ──────────────────────────────────────

    "A": {  # Qahwa Corner Cafe   (real: ticket=33, daily_tx=97, itg_cv=3.29)
        "label": "high_freq_low_ticket_food",
        "avg_ticket": (33, 2.0), "ticket_cv": (0.46, 0.03), "p90p10": (3.4, 0.2),
        "avg_daily_tx": (97, 6), "active_days": (0.99, 0.01),
        "peak_hour_conc": (0.10, 0.008), "night_ratio": (0.010, 0.001),
        "weekend_lift": (1.00, 0.04), "hour_entropy": (0.84, 0.015),
        "revenue_cv": (0.28, 0.02), "itg_cv": (3.30, 0.15),
        "digital": (0.64, 0.03), "cash": (0.21, 0.02),
    },
    "B": {  # Baraka Minimarket   (real: ticket=101, daily_tx=218, p90p10=18, itg_cv=2.16)
        "label": "high_freq_mid_ticket_retail",
        "avg_ticket": (101, 6), "ticket_cv": (1.22, 0.07), "p90p10": (18.3, 1.0),
        "avg_daily_tx": (218, 13), "active_days": (0.99, 0.01),
        "peak_hour_conc": (0.08, 0.006), "night_ratio": (0.050, 0.004),
        "weekend_lift": (0.99, 0.04), "hour_entropy": (0.93, 0.012),
        "revenue_cv": (0.23, 0.02), "itg_cv": (2.16, 0.12),
        "digital": (0.51, 0.03), "cash": (0.39, 0.03),
    },
    "C": {  # Rawabi Auto Gallery (real: ticket=157552, daily_tx=4.07, digital=0.0, itg_cv=1.19)
        "label": "low_freq_high_ticket_automotive",
        "avg_ticket": (157552, 8000), "ticket_cv": (0.88, 0.05), "p90p10": (5.7, 0.4),
        "avg_daily_tx": (4.07, 0.30), "active_days": (0.99, 0.01),
        "peak_hour_conc": (0.12, 0.010), "night_ratio": (0.000, 0.0005),
        "weekend_lift": (1.14, 0.05), "hour_entropy": (0.78, 0.015),
        "revenue_cv": (0.69, 0.04), "itg_cv": (1.19, 0.08),
        "digital": (0.00, 0.005), "cash": (0.30, 0.02),
    },
    "D": {  # Majd Real Estate    (real: ticket=26843, daily_tx=1.33, active=0.57, digital=0.0)
        "label": "sparse_high_ticket_brokerage",
        "avg_ticket": (26843, 2000), "ticket_cv": (1.31, 0.08), "p90p10": (56.9, 4.0),
        "avg_daily_tx": (1.33, 0.10), "active_days": (0.57, 0.04),
        "peak_hour_conc": (0.17, 0.012), "night_ratio": (0.000, 0.0005),
        "weekend_lift": (0.61, 0.05), "hour_entropy": (0.66, 0.020),
        "revenue_cv": (1.54, 0.08), "itg_cv": (2.17, 0.14),
        "digital": (0.00, 0.005), "cash": (0.12, 0.02),
    },
    "F": {  # Al Noor Laundromat  (real: ticket=37, daily_tx=70, night=0.04, itg_cv=1.99, h_ent=0.92)
        "label": "low_ticket_steady_essential",
        "avg_ticket": (37, 2.0), "ticket_cv": (0.54, 0.03), "p90p10": (3.4, 0.2),
        "avg_daily_tx": (70, 4), "active_days": (0.99, 0.01),
        "peak_hour_conc": (0.08, 0.006), "night_ratio": (0.040, 0.003),
        "weekend_lift": (1.04, 0.04), "hour_entropy": (0.92, 0.012),
        "revenue_cv": (0.27, 0.02), "itg_cv": (1.99, 0.12),
        "digital": (0.60, 0.03), "cash": (0.25, 0.02),
    },
    "I": {  # Saqr Motorbikes     (real: ticket=15461, p90p10=65, daily_tx=7.1, digital=0.46)
        "label": "low_freq_mid_ticket_dealer",
        "avg_ticket": (15461, 900), "ticket_cv": (1.29, 0.07), "p90p10": (65.0, 4.0),
        "avg_daily_tx": (7.10, 0.50), "active_days": (0.99, 0.01),
        "peak_hour_conc": (0.11, 0.008), "night_ratio": (0.000, 0.0005),
        "weekend_lift": (1.22, 0.05), "hour_entropy": (0.78, 0.015),
        "revenue_cv": (0.81, 0.05), "itg_cv": (1.52, 0.10),
        "digital": (0.46, 0.03), "cash": (0.35, 0.03),
    },

    # ── Positioned to fill distinct regions of feature space ─────────────────

    "E": {  # mid_ticket_mid_freq_services  (workshops, salons, clinics)
        "label": "mid_ticket_mid_freq_services",
        "avg_ticket": (250, 15), "ticket_cv": (0.55, 0.04), "p90p10": (5.0, 0.4),
        "avg_daily_tx": (20, 1.5), "active_days": (0.88, 0.03),
        "peak_hour_conc": (0.14, 0.010), "night_ratio": (0.010, 0.001),
        "weekend_lift": (1.05, 0.04), "hour_entropy": (0.65, 0.020),
        "revenue_cv": (0.30, 0.02), "itg_cv": (1.50, 0.10),
        "digital": (0.72, 0.03), "cash": (0.18, 0.02),
    },
    "G": {  # high_freq_high_ticket_supermarket  (large hypermarket)
        "label": "high_freq_high_ticket_supermarket",
        "avg_ticket": (380, 22), "ticket_cv": (0.50, 0.03), "p90p10": (5.0, 0.4),
        "avg_daily_tx": (420, 25), "active_days": (0.99, 0.01),
        "peak_hour_conc": (0.07, 0.005), "night_ratio": (0.010, 0.001),
        "weekend_lift": (1.28, 0.05), "hour_entropy": (0.88, 0.012),
        "revenue_cv": (0.13, 0.01), "itg_cv": (0.60, 0.06),
        "digital": (0.76, 0.03), "cash": (0.17, 0.02),
    },
    "H": {  # mid_freq_high_ticket_electronics  (consumer electronics retailer)
        "label": "mid_freq_high_ticket_electronics",
        "avg_ticket": (1800, 100), "ticket_cv": (0.80, 0.05), "p90p10": (9.0, 0.7),
        "avg_daily_tx": (12, 0.9), "active_days": (0.82, 0.03),
        "peak_hour_conc": (0.15, 0.010), "night_ratio": (0.005, 0.001),
        "weekend_lift": (1.15, 0.05), "hour_entropy": (0.62, 0.020),
        "revenue_cv": (0.40, 0.03), "itg_cv": (1.80, 0.12),
        "digital": (0.68, 0.03), "cash": (0.15, 0.02),
    },
    "J": {  # mid_freq_low_ticket_personal_services  (barbershop, dry cleaner pickup)
        "label": "mid_freq_low_ticket_personal_services",
        "avg_ticket": (30, 1.8), "ticket_cv": (0.35, 0.03), "p90p10": (2.8, 0.2),
        "avg_daily_tx": (25, 1.8), "active_days": (0.90, 0.02),
        "peak_hour_conc": (0.13, 0.010), "night_ratio": (0.005, 0.001),
        "weekend_lift": (1.20, 0.05), "hour_entropy": (0.68, 0.018),
        "revenue_cv": (0.20, 0.02), "itg_cv": (1.00, 0.08),
        "digital": (0.55, 0.03), "cash": (0.35, 0.03),
    },
    "K": {  # low_freq_high_value_medical  (specialist clinic, dental)
        "label": "low_freq_high_value_medical",
        "avg_ticket": (800, 50), "ticket_cv": (0.70, 0.05), "p90p10": (7.0, 0.6),
        "avg_daily_tx": (8, 0.6), "active_days": (0.85, 0.03),
        "peak_hour_conc": (0.16, 0.012), "night_ratio": (0.002, 0.0005),
        "weekend_lift": (0.75, 0.05), "hour_entropy": (0.58, 0.020),
        "revenue_cv": (0.32, 0.02), "itg_cv": (1.60, 0.10),
        "digital": (0.85, 0.03), "cash": (0.08, 0.01),
    },
    "L": {  # mid_freq_mid_ticket_fashion  (boutique, clothing)
        "label": "mid_freq_mid_ticket_fashion",
        "avg_ticket": (320, 18), "ticket_cv": (0.65, 0.04), "p90p10": (6.0, 0.5),
        "avg_daily_tx": (18, 1.3), "active_days": (0.86, 0.03),
        "peak_hour_conc": (0.13, 0.010), "night_ratio": (0.007, 0.001),
        "weekend_lift": (1.38, 0.05), "hour_entropy": (0.64, 0.018),
        "revenue_cv": (0.28, 0.02), "itg_cv": (1.70, 0.11),
        "digital": (0.78, 0.03), "cash": (0.14, 0.02),
    },
}


def _pos(rng, mu, sigma):
    return max(1e-6, float(rng.normal(mu, sigma)))


def generate_synthetic_businesses(n_per_archetype=150, seed=42):
    rng  = np.random.default_rng(seed)
    rows = []

    for arch_id, spec in ARCHETYPES.items():
        for _ in range(n_per_archetype):
            avg_t   = _pos(rng, *spec["avg_ticket"])
            med_t   = avg_t * float(rng.uniform(0.80, 0.98))
            t_cv    = _pos(rng, *spec["ticket_cv"])
            p90p10  = _pos(rng, *spec["p90p10"])
            avg_dtx = _pos(rng, *spec["avg_daily_tx"])
            vel     = avg_dtx / 24.0
            act_d   = float(np.clip(rng.normal(*spec["active_days"]), 0.10, 1.0))
            peak_h  = float(np.clip(rng.normal(*spec["peak_hour_conc"]), 0.04, 0.50))
            ngt_r   = float(np.clip(rng.normal(*spec["night_ratio"]), 0.0, 0.30))
            wk_l    = _pos(rng, *spec["weekend_lift"])
            h_ent   = float(np.clip(rng.normal(*spec["hour_entropy"]), 0.0, 1.0))
            rev_cv  = _pos(rng, *spec["revenue_cv"])
            itg_cv  = _pos(rng, *spec["itg_cv"])
            dig     = float(np.clip(rng.normal(*spec["digital"]), 0.0, 1.0))
            cash    = float(np.clip(rng.normal(*spec["cash"]), 0.0, 1.0 - dig))

            rows.append({
                "archetype":                arch_id,
                "avg_ticket_sar":           avg_t,
                "median_ticket_sar":        med_t,
                "ticket_cv":                t_cv,
                "ticket_p90_p10_ratio":     p90p10,
                "avg_daily_transactions":   avg_dtx,
                "transaction_velocity":     vel,
                "active_days_ratio":        act_d,
                "peak_hour_concentration":  peak_h,
                "night_transaction_ratio":  ngt_r,
                "weekend_lift":             wk_l,
                "hour_entropy":             h_ent,
                "revenue_cv":               rev_cv,
                "inter_transaction_gap_cv": itg_cv,
                "digital_payment_ratio":    dig,
                "cash_ratio":               cash,
            })

    return pd.DataFrame(rows)

# ── Stage 3-9: Classifier ─────────────────────────────────────────────────────

class BusinessClassifier:

    def __init__(self):
        self.scaler    = StandardScaler()
        self.pca       = PCA(n_components=8, random_state=42)
        self.clusterer = hdbscan.HDBSCAN(
            min_cluster_size=15,
            min_samples=5,
            cluster_selection_epsilon=0.05,
            cluster_selection_method="leaf",
            prediction_data=True,
        )
        self.cluster_profiles  = {}
        self.trained           = False
        self.extractor         = BusinessFeatureExtractor()
        self.feature_names     = FEATURE_COLS
        self.outlier_threshold = 4.0

    # Stage 4: train
    def train(self, df: pd.DataFrame):
        X = df[FEATURE_COLS].values.astype(float)
        X[:, _LOG_COLS] = np.log1p(X[:, _LOG_COLS])

        X_scaled = self.scaler.fit_transform(X)
        X_pca    = self.pca.fit_transform(X_scaled)
        labels   = self.clusterer.fit_predict(X_pca)

        self._X_pca    = X_pca
        self._labels   = labels
        self._train_df = df.copy()
        self._train_df["cluster"] = labels

        self.characterize_clusters()
        self.trained = True

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        noise_pct  = (labels == -1).sum() / len(labels) * 100
        expl_var   = self.pca.explained_variance_ratio_.cumsum()[-1]
        print(f"  Training: {len(df)} samples | {n_clusters} clusters | "
              f"noise {noise_pct:.1f}% | PCA var {expl_var*100:.1f}%")
        return self

    # Stage 5: characterize clusters by majority archetype
    def characterize_clusters(self):
        df = self._train_df.copy()
        for cid in sorted(c for c in df["cluster"].unique() if c != -1):
            mask    = df["cluster"] == cid
            subset  = df[mask]
            majority_arch = subset["archetype"].value_counts().idxmax()
            self.cluster_profiles[cid] = {
                "cluster_id":         cid,
                "dominant_archetype": majority_arch,
                "archetype_label":    ARCHETYPES[majority_arch]["label"],
                "size":               int(mask.sum()),
                "purity":             round(float((subset["archetype"] == majority_arch).mean()), 4),
                "centroid":           subset[FEATURE_COLS].mean().to_dict(),
            }

    # Stage 6: classify a new business
    def classify(self, features: dict) -> dict:
        if not self.trained:
            raise RuntimeError("Model not trained. Call train() or load() first.")

        x = np.array([features[c] for c in FEATURE_COLS], dtype=float)
        x[_LOG_COLS] = np.log1p(x[_LOG_COLS])

        x_scaled = self.scaler.transform(x.reshape(1, -1))
        x_pca    = self.pca.transform(x_scaled)

        labels, probs = hdbscan.approximate_predict(self.clusterer, x_pca)
        cluster_id    = int(labels[0])
        confidence    = float(probs[0]) if len(probs) > 0 else 0.0
        was_noise     = (cluster_id == -1)

        if was_noise or cluster_id not in self.cluster_profiles:
            # Fall back to nearest cluster centroid in PCA space
            best_cid, best_dist = -1, float("inf")
            for cid, prof in self.cluster_profiles.items():
                cent = np.array([prof["centroid"][c] for c in FEATURE_COLS], dtype=float)
                cent[_LOG_COLS] = np.log1p(cent[_LOG_COLS])
                c_pca = self.pca.transform(self.scaler.transform(cent.reshape(1, -1)))
                dist  = float(np.linalg.norm(x_pca - c_pca))
                if dist < best_dist:
                    best_dist, best_cid = dist, cid
            cluster_id = best_cid
            confidence = max(0.0, 1.0 - best_dist / 4.0)

        profile = self.cluster_profiles[cluster_id]
        return {
            "cluster_id":         cluster_id,
            "dominant_archetype": profile["dominant_archetype"],
            "archetype_label":    profile["archetype_label"],
            "cluster_purity":     profile["purity"],
            "confidence":         round(confidence, 4),
            "was_noise":          was_noise,
        }

    def _find_nearest_cluster(self, pca_point: np.ndarray):
        """Returns (cluster_id, distance) for the closest cluster centroid."""
        best_cid, best_dist = -1, float("inf")
        for cid, prof in self.cluster_profiles.items():
            cent = np.array([prof["centroid"][c] for c in FEATURE_COLS], dtype=float)
            cent[_LOG_COLS] = np.log1p(cent[_LOG_COLS])
            c_pca = self.pca.transform(self.scaler.transform(cent.reshape(1, -1)))[0]
            dist  = float(np.linalg.norm(pca_point - c_pca))
            if dist < best_dist:
                best_dist, best_cid = dist, cid
        return best_cid, best_dist

    def classify_from_data(self, transactions_df: pd.DataFrame,
                           period_days: int = 30) -> dict:
        """Extracts features from a real transaction DataFrame, classifies, and enriches output."""
        features = self.extractor.extract(transactions_df)
        result   = self.classify(features)

        tx = transactions_df.copy()
        tx["timestamp"] = pd.to_datetime(tx["timestamp"])
        data_days = min(int(tx["timestamp"].dt.date.nunique()), period_days)

        if   data_days >= 25: refinement_status = "mature"
        elif data_days >= 14: refinement_status = "developing"
        elif data_days >= 7:  refinement_status = "early"
        else:                 refinement_status = "predicted"

        result["profile_source"]    = "real_data"
        result["data_days"]         = data_days
        result["refinement_status"] = refinement_status
        result["raw_features"]      = {k: round(float(v), 4) for k, v in features.items()}
        return result

    def classify_from_intake(self, intake_dict: dict) -> dict:
        """
        Track 2: classify a brand new business with zero transaction history.
        Uses intake form answers mapped to the same 15-feature vector.
        Max confidence capped at 0.65 — model is honest about uncertainty.
        """
        features = self.extractor.extract_from_intake(intake_dict)
        x = np.array([features[f] for f in self.feature_names], dtype=float).reshape(1, -1)

        x_log              = x.copy()
        x_log[:, _LOG_COLS] = np.log1p(x_log[:, _LOG_COLS])
        x_scaled = self.scaler.transform(x_log)
        x_pca    = self.pca.transform(x_scaled)

        cluster_id, distance = self._find_nearest_cluster(x_pca[0])
        is_outlier = distance > self.outlier_threshold
        confidence = float(np.clip(
            (1.0 - (distance / self.outlier_threshold)) * 0.65,
            0.05, 0.65))

        profile = self.cluster_profiles.get(cluster_id, {})
        return {
            "cluster_id":              cluster_id,
            "cluster_size":            profile.get("size", 0),
            "behavioral_profile":      profile.get("tags", {}),
            "archetype_description":   profile.get("archetype_label", "unknown"),
            "profile_source":          "intake_form",
            "confidence":              round(confidence, 4),
            "data_days":               0,
            "is_outlier":              is_outlier,
            "distance_to_centroid":    round(float(distance), 4),
            "refinement_status":       "predicted",
            "raw_features":            {k: round(float(v), 4) for k, v in features.items()},
        }

    def classify_hybrid(self, transactions_df: pd.DataFrame,
                        intake_dict: dict, period_days: int = 30) -> dict:
        """
        Track 2 transition: blend real data with intake form.
        As real data accumulates the intake form weight approaches zero.
        This is the refinement loop — runs during the first 30 days.
        """
        real_result   = self.classify_from_data(transactions_df, period_days)
        intake_result = self.classify_from_intake(intake_dict)

        data_days = real_result["data_days"]
        blended   = self.extractor.blend(
                        real_result["raw_features"],
                        intake_result["raw_features"],
                        data_days)

        x = np.array([blended[f] for f in self.feature_names], dtype=float).reshape(1, -1)
        x_log              = x.copy()
        x_log[:, _LOG_COLS] = np.log1p(x_log[:, _LOG_COLS])
        x_scaled = self.scaler.transform(x_log)
        x_pca    = self.pca.transform(x_scaled)

        cluster_id, distance = self._find_nearest_cluster(x_pca[0])
        blend_weight = min(data_days / 30.0, 1.0)
        confidence   = float(np.clip(
            real_result["confidence"]   * blend_weight +
            intake_result["confidence"] * (1 - blend_weight),
            0.05, 0.99))

        if   data_days >= 25: refinement_status = "mature"
        elif data_days >= 14: refinement_status = "developing"
        elif data_days >= 7:  refinement_status = "early"
        else:                 refinement_status = "predicted"

        profile = self.cluster_profiles.get(cluster_id, {})
        return {
            "cluster_id":              cluster_id,
            "behavioral_profile":      profile.get("tags", {}),
            "archetype_description":   profile.get("archetype_label", "unknown"),
            "profile_source":          "hybrid",
            "confidence":              round(confidence, 4),
            "data_days":               data_days,
            "blend_weight_real_data":  round(blend_weight, 2),
            "is_outlier":              distance > self.outlier_threshold,
            "distance_to_centroid":    round(float(distance), 4),
            "refinement_status":       refinement_status,
            "raw_features":            {k: round(float(v), 4) for k, v in blended.items()},
        }

    # Stage 7: validate against known archetypes in synthetic data
    def validate(self) -> dict:
        df        = self._train_df.copy()
        non_noise = df[df["cluster"] != -1]

        correct, total = 0, 0
        for cid, prof in self.cluster_profiles.items():
            mask     = non_noise["cluster"] == cid
            correct += int((non_noise[mask]["archetype"] == prof["dominant_archetype"]).sum())
            total   += int(mask.sum())

        return {
            "n_clusters":       len(self.cluster_profiles),
            "n_samples":        len(df),
            "noise_rate":       round((df["cluster"] == -1).sum() / len(df), 4),
            "archetype_purity": round(correct / total if total > 0 else 0.0, 4),
            "cluster_profiles": list(self.cluster_profiles.values()),
        }

    # Stage 8: save / load
    def save(self, path: str = None):
        if path is None:
            os.makedirs(SAVED_DIR, exist_ok=True)
            path = os.path.join(SAVED_DIR, "business_classifier.pkl")
        joblib.dump({
            "scaler":           self.scaler,
            "pca":              self.pca,
            "clusterer":        self.clusterer,
            "cluster_profiles": self.cluster_profiles,
            "trained":          self.trained,
        }, path)
        print(f"  Model saved -> {path}")

    def load(self, path: str = None):
        if path is None:
            path = os.path.join(SAVED_DIR, "business_classifier.pkl")
        obj = joblib.load(path)
        self.scaler           = obj["scaler"]
        self.pca              = obj["pca"]
        self.clusterer        = obj["clusterer"]
        self.cluster_profiles = obj["cluster_profiles"]
        self.trained          = obj["trained"]
        print(f"  Model loaded <- {path}")
        return self

# ── Stage 9: end-to-end runner ────────────────────────────────────────────────

BUSINESS_IDS = ["laundromat", "cafe", "minimarket", "realestate", "cardealer", "motorbike"]
NAMES = {
    "laundromat": "Al Noor Laundromat",
    "cafe":       "Qahwa Corner Cafe",
    "minimarket": "Baraka Minimarket",
    "realestate": "Majd Real Estate",
    "cardealer":  "Rawabi Auto Gallery",
    "motorbike":  "Saqr Motorbikes",
}
EXPECTED_ARCH = {
    "laundromat": "F", "cafe": "A", "minimarket": "B",
    "realestate": "D", "cardealer": "C", "motorbike": "I",
}

W = 110


def run():
    extractor  = BusinessFeatureExtractor()
    classifier = BusinessClassifier()

    print("=" * W)
    print("DATACORE  --  MODEL 1: UNSUPERVISED BUSINESS CLASSIFIER")
    print("=" * W)

    # Stage 2: generate synthetic training data
    print("\n[1/4] Generating 1800 synthetic businesses (12 archetypes x 150)...")
    synth_df = generate_synthetic_businesses(n_per_archetype=150, seed=42)
    print(f"  Shape: {synth_df.shape}  |  Archetypes: {sorted(synth_df['archetype'].unique())}")

    # Stages 3-5: scale -> PCA -> HDBSCAN -> characterize
    print("\n[2/4] Training: StandardScaler -> PCA(8) -> HDBSCAN...")
    classifier.train(synth_df)

    # Stage 7: validation report
    val = classifier.validate()
    print(f"\n[3/4] Validation:")
    print(f"  Clusters found:    {val['n_clusters']}")
    print(f"  Noise rate:        {val['noise_rate']*100:.1f}%")
    print(f"  Archetype purity:  {val['archetype_purity']*100:.1f}%")
    print()
    print(f"  {'Cluster':>8}  {'Arch':<6}  {'Label':<44}  {'Purity':>7}  {'Size':>5}")
    print("  " + "-" * 82)
    for prof in sorted(val["cluster_profiles"], key=lambda p: p["dominant_archetype"]):
        print(f"  {prof['cluster_id']:>8}  {prof['dominant_archetype']:<6}  "
              f"{prof['archetype_label']:<44}  {prof['purity']*100:>6.1f}%  {prof['size']:>5}")

    # Stage 8: save model
    print("\n[4/4] Saving model...")
    classifier.save()

    # Stage 9: classify all 6 real businesses
    print()
    print("=" * W)
    print("REAL BUSINESS CLASSIFICATION RESULTS")
    print("=" * W)
    print(f"\n  {'Business':<26}  {'Predicted':<12}  {'Label':<44}  {'Conf':>6}  {'Expected':<10}  Result")
    print("  " + "-" * 108)

    correct = 0
    for bid in BUSINESS_IDS:
        tx_path = os.path.join(DATA_DIR, f"{bid}_transactions.csv")
        if not os.path.exists(tx_path):
            print(f"  {NAMES[bid]:<26}  [ERROR: no transaction data]")
            continue

        tx       = pd.read_csv(tx_path)
        features = extractor.extract(tx)
        result   = classifier.classify(features)

        predicted = result["dominant_archetype"]
        expected  = EXPECTED_ARCH.get(bid, "?")
        match     = "CORRECT" if predicted == expected else "MISS"
        if match == "CORRECT":
            correct += 1

        print(f"  {NAMES[bid]:<26}  {predicted:<12}  "
              f"{result['archetype_label']:<44}  {result['confidence']:>5.2f}  "
              f"{expected:<10}  {match}")

    print()
    acc = correct / len(BUSINESS_IDS) * 100
    print(f"  Accuracy on 6 real businesses: {correct}/{len(BUSINESS_IDS)} ({acc:.0f}%)")
    print()
    print("=" * W)
    print("Model 1 complete.")
    print("=" * W)


if __name__ == "__main__":
    run()

    print("\n" + "=" * 60)
    print("TRACK 2 -- INTAKE FORM (new businesses, zero history)")
    print("=" * 60)

    test_intakes = [
        ("New Shawarma Shop", {
            "typical_ticket_sar":        28,
            "expected_daily_customers":  85,
            "operating_hours_per_day":   14,
            "is_consumer_facing":        True,
            "sells_high_value_items":    False,
            "expected_payment_mix":      "mixed",
            "operates_late_night":       True,
            "business_days_per_week":    7,
        }),
        ("New Luxury Car Showroom", {
            "typical_ticket_sar":        160000,
            "expected_daily_customers":  3,
            "operating_hours_per_day":   12,
            "is_consumer_facing":        True,
            "sells_high_value_items":    True,
            "expected_payment_mix":      "mostly_digital",
            "operates_late_night":       False,
            "business_days_per_week":    6,
        }),
        ("New Dental Clinic", {
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

    clf2 = BusinessClassifier()
    clf2.load()

    for name, intake in test_intakes:
        r = clf2.classify_from_intake(intake)
        print(f"\n{name}")
        print(f"  Cluster   : {r['cluster_id']} | Confidence: {r['confidence']:.2f}")
        print(f"  Profile   : {r['archetype_description']}")
        print(f"  Source    : {r['profile_source']} | Status: {r['refinement_status']}")

    print("\n" + "=" * 60)
    print("HYBRID -- Cafe with only 7 days real data + intake form")
    print("=" * 60)

    tx_cafe = pd.read_csv(os.path.join(DATA_DIR, "cafe_transactions.csv"))
    tx_cafe["timestamp"] = pd.to_datetime(tx_cafe["timestamp"])
    tx_7days = tx_cafe[tx_cafe["timestamp"] < "2025-06-08"].copy()

    cafe_intake = {
        "typical_ticket_sar":        30,
        "expected_daily_customers":  90,
        "operating_hours_per_day":   14,
        "is_consumer_facing":        True,
        "sells_high_value_items":    False,
        "expected_payment_mix":      "mostly_digital",
        "operates_late_night":       False,
        "business_days_per_week":    7,
    }

    r = clf2.classify_hybrid(tx_7days, cafe_intake)
    print(f"  Cluster   : {r['cluster_id']} | Confidence: {r['confidence']:.2f}")
    print(f"  Profile   : {r['archetype_description']}")
    print(f"  Source    : {r['profile_source']} (real weight: {r['blend_weight_real_data']})")
    print(f"  Status    : {r['refinement_status']}")
