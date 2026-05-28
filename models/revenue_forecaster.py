"""
revenue_forecaster.py  --  DataCore AI Engine: Model 4
Prophet-based 30-day revenue forecasting with dynamic credit limit adjustment.
"""

import os, sys
import numpy as np
import pandas as pd
import joblib
from contextlib import contextmanager

ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(ROOT, "data", "processed")
SAVED_DIR = os.path.join(ROOT, "models", "saved")
sys.path.insert(0, ROOT)

ALL_HIST_DATES = pd.date_range("2025-04-01", "2025-06-30").strftime("%Y-%m-%d").tolist()
FORECAST_START = "2025-07-01"
FORECAST_END   = "2025-07-30"

CREDIT_CEILINGS = {
    "laundromat":   500_000,
    "cafe":         400_000,
    "minimarket": 1_500_000,
    "realestate": 2_000_000,
    "cardealer":  5_000_000,
    "motorbike":  1_000_000,
}


@contextmanager
def suppress_stdout_stderr():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


class RevenueForecaster:

    def __init__(self):
        self.models    = {}   # {business_id: fitted Prophet model}
        self.forecasts = {}   # {business_id: forecast DataFrame}
        self.summaries = {}   # {business_id: summary dict}

    # ── Data preparation ──────────────────────────────────────────────────────

    def prepare_data(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        tx = transactions_df.copy()
        tx["timestamp"]  = pd.to_datetime(tx["timestamp"])
        tx["amount_sar"] = tx["amount_sar"].astype(float)
        tx["date"]       = tx["timestamp"].dt.strftime("%Y-%m-%d")

        daily = (tx.groupby("date")["amount_sar"]
                   .sum()
                   .reindex(ALL_HIST_DATES, fill_value=0.0)
                   .reset_index())
        daily.columns = ["ds", "y"]
        daily["ds"]   = pd.to_datetime(daily["ds"])
        return daily

    # ── Fit ───────────────────────────────────────────────────────────────────

    def fit(self, business_id: str, transactions_df: pd.DataFrame):
        from prophet import Prophet

        df = self.prepare_data(transactions_df)

        model = Prophet(
            changepoint_prior_scale=0.15,
            seasonality_prior_scale=10.0,
            holidays_prior_scale=10.0,
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=False,
            interval_width=0.80,
            uncertainty_samples=500,
        )
        model.add_seasonality(name="saudi_weekly", period=7, fourier_order=3)

        with suppress_stdout_stderr():
            model.fit(df)

        self.models[business_id] = model
        self.forecast(business_id)
        print(f"  Fitted Prophet model for {business_id}")

    # ── Forecast ──────────────────────────────────────────────────────────────

    def forecast(self, business_id: str, periods: int = 30) -> pd.DataFrame:
        model = self.models[business_id]

        future       = model.make_future_dataframe(periods=periods)
        forecast_df  = model.predict(future)

        # Extract only the future period (last `periods` rows)
        future_fc = forecast_df.tail(periods).copy()
        future_fc["yhat"]       = future_fc["yhat"].clip(lower=0)
        future_fc["yhat_lower"] = future_fc["yhat_lower"].clip(lower=0)
        future_fc["yhat_upper"] = future_fc["yhat_upper"].clip(lower=0)

        self.forecasts[business_id] = future_fc

        # Historical baseline from the fitted data
        hist_df = model.history
        historical_avg = float(hist_df["y"].mean())

        forecast_avg   = float(future_fc["yhat"].mean())
        forecast_total = float(future_fc["yhat"].sum())
        upper_total    = float(future_fc["yhat_upper"].sum())
        lower_total    = float(future_fc["yhat_lower"].sum())
        band_width     = float((future_fc["yhat_upper"] - future_fc["yhat_lower"]).mean())

        peak_idx    = future_fc["yhat"].idxmax()
        peak_date   = str(future_fc.loc[peak_idx, "ds"].strftime("%Y-%m-%d"))
        peak_amount = float(future_fc.loc[peak_idx, "yhat"])

        if historical_avg > 0:
            pct_change = (forecast_avg - historical_avg) / historical_avg * 100
        else:
            pct_change = 0.0

        if   pct_change > 5:   trend = "growing"
        elif pct_change < -5:  trend = "declining"
        else:                  trend = "flat"

        self.summaries[business_id] = {
            "business_id":           business_id,
            "historical_avg_daily":  round(historical_avg, 2),
            "forecast_avg_daily":    round(forecast_avg, 2),
            "forecast_total_30d":    round(forecast_total, 2),
            "forecast_upper_30d":    round(upper_total, 2),
            "forecast_lower_30d":    round(lower_total, 2),
            "trend_direction":       trend,
            "trend_pct_change":      round(pct_change, 2),
            "peak_forecast_date":    peak_date,
            "peak_forecast_amount":  round(peak_amount, 2),
            "confidence_band_width": round(band_width, 2),
            "forecast_period":       f"{FORECAST_START} to {FORECAST_END}",
        }

        return future_fc

    # ── Dynamic credit limit ──────────────────────────────────────────────────

    def compute_dynamic_credit_limit(self, business_id: str,
                                     base_dscr_limit: float) -> dict:
        s = self.summaries[business_id]

        pct = s["trend_pct_change"]
        if s["trend_direction"] == "growing":
            multiplier = 1.0 + min(pct / 100, 0.25)
        elif s["trend_direction"] == "declining":
            multiplier = 1.0 + max(pct / 100, -0.20)
        else:
            multiplier = 1.0

        # Confidence penalty: wide uncertainty band reduces limit
        if s["forecast_avg_daily"] > 0:
            band_ratio = s["confidence_band_width"] / s["forecast_avg_daily"]
            if band_ratio > 1.5:
                multiplier *= 0.90

        raw_limit = base_dscr_limit * multiplier
        ceiling   = CREDIT_CEILINGS.get(business_id, 2_000_000)
        final     = min(raw_limit, ceiling)
        final     = int(round(final / 5000) * 5000)

        return {
            "base_limit_sar":     int(base_dscr_limit),
            "trend_multiplier":   round(multiplier, 4),
            "dynamic_limit_sar":  final,
            "trend_direction":    s["trend_direction"],
            "trend_pct_change":   s["trend_pct_change"],
            "forecast_avg_daily": s["forecast_avg_daily"],
            "limit_change_sar":   final - int(base_dscr_limit),
            "limit_change_pct":   round(
                (final - base_dscr_limit) / base_dscr_limit * 100, 2)
                if base_dscr_limit > 0 else 0.0,
        }

    # ── Fit all ───────────────────────────────────────────────────────────────

    def fit_all(self):
        businesses = ["laundromat", "cafe", "minimarket",
                      "realestate", "cardealer", "motorbike"]
        print("Fitting Prophet models for all businesses...")
        for biz in businesses:
            tx = pd.read_csv(os.path.join(DATA_DIR, f"{biz}_transactions.csv"))
            self.fit(biz, tx)

    # ── Forecast series for API ───────────────────────────────────────────────

    def get_forecast_series(self, business_id: str) -> list:
        fc = self.forecasts[business_id]
        return [
            {
                "date":              row["ds"].strftime("%Y-%m-%d"),
                "predicted_revenue": round(float(row["yhat"]), 2),
                "lower_bound":       round(float(row["yhat_lower"]), 2),
                "upper_bound":       round(float(row["yhat_upper"]), 2),
            }
            for _, row in fc.iterrows()
        ]

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: str = None):
        if path is None:
            path = os.path.join(SAVED_DIR, "revenue_forecaster.pkl")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            "models":    self.models,
            "forecasts": self.forecasts,
            "summaries": self.summaries,
        }, path)
        print(f"Revenue forecaster saved — {len(self.models)} business models")

    def load(self, path: str = None):
        if path is None:
            path = os.path.join(SAVED_DIR, "revenue_forecaster.pkl")
        data = joblib.load(path)
        self.models    = data["models"]
        self.forecasts = data["forecasts"]
        self.summaries = data["summaries"]
        print(f"Revenue forecaster loaded — {len(self.models)} business models")
        return self


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("DATACORE -- Revenue Forecaster Model 4 (Prophet)")
    print("=" * 60)

    forecaster = RevenueForecaster()
    forecaster.fit_all()
    forecaster.save()

    print("\n" + "=" * 60)
    print("FORECAST SUMMARY -- ALL BUSINESSES")
    print("=" * 60)

    from models.dscr_model import DSCRModel

    dscr = DSCRModel()

    businesses = ["laundromat", "cafe", "minimarket",
                  "realestate", "cardealer", "motorbike"]

    for biz in businesses:
        s = forecaster.summaries[biz]
        print(f"\n{biz.upper()}")
        print(f"  Historical avg/day : SAR {s['historical_avg_daily']:>12,.0f}")
        print(f"  Forecast avg/day   : SAR {s['forecast_avg_daily']:>12,.0f}")
        print(f"  Trend              : {s['trend_direction']} ({s['trend_pct_change']:+.1f}%)")
        print(f"  Forecast 30d total : SAR {s['forecast_total_30d']:>12,.0f}")
        print(f"  Peak forecast date : {s['peak_forecast_date']} "
              f"(SAR {s['peak_forecast_amount']:,.0f})")

        result     = dscr.run(biz)
        base_limit = result["credit_limit_sar"]
        dynamic    = forecaster.compute_dynamic_credit_limit(biz, base_limit)

        print(f"  Base DSCR limit    : SAR {dynamic['base_limit_sar']:>12,.0f}")
        print(f"  Dynamic limit      : SAR {dynamic['dynamic_limit_sar']:>12,.0f}  "
              f"({dynamic['limit_change_pct']:+.1f}%)")

    print("\n" + "=" * 60)
    print("SAMPLE FORECAST SERIES -- CAFE (first 7 days)")
    print("=" * 60)
    series = forecaster.get_forecast_series("cafe")
    for day in series[:7]:
        print(f"  {day['date']}: SAR {day['predicted_revenue']:>8,.0f}  "
              f"[{day['lower_bound']:,.0f} -- {day['upper_bound']:,.0f}]")

    print("\n" + "=" * 60)
    print("Model 4 complete.")
    print("=" * 60)
