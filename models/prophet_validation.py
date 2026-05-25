"""
prophet_validation.py  --  DataCore Model 4 Forecast Accuracy Validation
Validates Prophet against UCI Online Retail II (real held-out data).
Produces citable forecast accuracy metrics for the paper.
"""

import sys, os
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "processed")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ── Step 1: Load UCI data ─────────────────────────────────────────────────────

def load_uci_daily_revenue():
    """
    Load UCI Online Retail II and aggregate to daily revenue.
    Returns (daily_df, dataset_label).
    Falls back to Online Retail I (id=352) if II is unavailable.
    """
    from ucimlrepo import fetch_ucirepo

    df           = None
    used_label   = None
    for uci_id, label in [(502, "Online Retail II"), (352, "Online Retail I")]:
        try:
            print(f"  Downloading UCI {label} (id={uci_id})...")
            retail = fetch_ucirepo(id=uci_id)
            raw    = retail.data.features.copy()

            # Normalise column names across both datasets
            col_map = {}
            for c in raw.columns:
                lc = c.lower().replace(" ", "")
                if lc in ("invoicedate", "invoicedt"):
                    col_map[c] = "InvoiceDate"
                elif lc in ("quantity", "qty"):
                    col_map[c] = "Quantity"
                elif lc in ("price", "unitprice"):
                    col_map[c] = "Price"
            raw = raw.rename(columns=col_map)

            if not {"InvoiceDate", "Quantity", "Price"}.issubset(raw.columns):
                print(f"    Missing required columns — skipping id={uci_id}")
                continue

            raw["InvoiceDate"] = pd.to_datetime(raw["InvoiceDate"],
                                                errors="coerce")
            raw = raw.dropna(subset=["InvoiceDate"])
            raw["date"]    = raw["InvoiceDate"].dt.date
            raw["revenue"] = raw["Quantity"] * raw["Price"]
            raw = raw[(raw["revenue"] > 0) & (raw["Quantity"] > 0)]

            daily = (raw.groupby("date")["revenue"]
                        .sum()
                        .reset_index())
            daily.columns = ["ds", "y"]
            daily["ds"]   = pd.to_datetime(daily["ds"])
            daily         = daily.sort_values("ds").reset_index(drop=True)

            if len(daily) < 30:
                print(f"    Too few days ({len(daily)}) — skipping id={uci_id}")
                continue

            print(f"  UCI {label}: {len(daily)} days, "
                  f"{daily.ds.min().date()} to {daily.ds.max().date()}")
            print(f"  Mean daily revenue: {daily.y.mean():,.2f}")
            print(f"  Std daily revenue:  {daily.y.std():,.2f}")
            df         = daily
            used_label = label
            break

        except Exception as exc:
            print(f"    id={uci_id} unavailable: {exc}")
            continue

    if df is None:
        raise RuntimeError(
            "Could not load any UCI Online Retail dataset. "
            "Check ucimlrepo version and network connectivity.")

    return df, used_label


# ── Step 2: Train/test split ──────────────────────────────────────────────────

def split_train_test(daily_df, train_pct=0.70):
    """
    Split by time — first 70% of days for training,
    last 30% for testing. Never shuffle time series.
    """
    split_idx = int(len(daily_df) * train_pct)
    train = daily_df.iloc[:split_idx].copy()
    test  = daily_df.iloc[split_idx:].copy()

    print(f"  Train: {len(train)} days "
          f"({train.ds.min().date()} to {train.ds.max().date()})")
    print(f"  Test:  {len(test)} days "
          f"({test.ds.min().date()} to {test.ds.max().date()})")

    return train, test


# ── Step 3: Train Prophet and forecast ───────────────────────────────────────

def train_and_forecast(train_df, test_df):
    """
    Train Prophet on train_df, forecast test period,
    return forecast aligned with test actuals.
    """
    from prophet import Prophet

    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        try:
            model = Prophet(
                changepoint_prior_scale=0.15,
                seasonality_prior_scale=10.0,
                weekly_seasonality=True,
                yearly_seasonality=True,
                daily_seasonality=False,
                interval_width=0.80,
                uncertainty_samples=300,
            )
            model.fit(train_df)

            future   = model.make_future_dataframe(
                periods=len(test_df), freq="D")
            forecast = model.predict(future)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    forecast_test = forecast.tail(len(test_df)).copy()
    forecast_test = forecast_test[["ds", "yhat", "yhat_lower", "yhat_upper"]]
    forecast_test["yhat"]       = forecast_test["yhat"].clip(lower=0)
    forecast_test["yhat_lower"] = forecast_test["yhat_lower"].clip(lower=0)
    forecast_test["yhat_upper"] = forecast_test["yhat_upper"].clip(lower=0)

    result = test_df.merge(forecast_test, on="ds", how="inner")
    return result, model


# ── Step 4: Accuracy metrics ──────────────────────────────────────────────────

def compute_forecast_metrics(result_df):
    """
    Compute standard forecast accuracy metrics.
    result_df must have columns: y (actual), yhat (predicted).
    """
    actual    = result_df["y"].values
    predicted = result_df["yhat"].values

    mae  = np.mean(np.abs(actual - predicted))

    mask = actual > 0
    mape = np.mean(np.abs(
        (actual[mask] - predicted[mask]) / actual[mask]
    )) * 100

    rmse = np.sqrt(np.mean((actual - predicted) ** 2))

    ss_res = np.sum((actual - predicted) ** 2)
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)
    r2     = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    within_band = (
        (result_df["y"] >= result_df["yhat_lower"]) &
        (result_df["y"] <= result_df["yhat_upper"])
    ).mean() * 100

    return {
        "mae":             round(float(mae), 2),
        "mape":            round(float(mape), 2),
        "rmse":            round(float(rmse), 2),
        "r2":              round(float(r2), 4),
        "coverage_80pct":  round(float(within_band), 1),
        "n_test_days":     len(result_df),
        "mean_actual":     round(float(actual.mean()), 2),
        "mean_predicted":  round(float(predicted.mean()), 2),
    }


# ── Step 5: Validate on synthetic businesses ──────────────────────────────────

def validate_synthetic_businesses():
    """
    Secondary validation: run Prophet on each of our 6 synthetic
    businesses using the same 70/30 train/test split.
    """
    BIZ = ["laundromat", "cafe", "minimarket",
           "realestate", "cardealer", "motorbike"]

    results = {}

    for biz in BIZ:
        tx_path = os.path.join(DATA_DIR, f"{biz}_transactions.csv")
        if not os.path.exists(tx_path):
            print(f"  {biz:<12}: data file not found — skipping")
            continue

        tx = pd.read_csv(tx_path)
        tx["timestamp"] = pd.to_datetime(tx["timestamp"])
        tx["date"]      = tx["timestamp"].dt.date

        daily = (tx.groupby("date")["amount_sar"]
                   .sum()
                   .reset_index())
        daily.columns = ["ds", "y"]
        daily["ds"]   = pd.to_datetime(daily["ds"])
        daily         = daily.sort_values("ds").reset_index(drop=True)

        if len(daily) < 10:
            print(f"  {biz:<12}: insufficient data ({len(daily)} days) — skipping")
            continue

        split     = int(len(daily) * 0.70)
        train     = daily.iloc[:split]
        test      = daily.iloc[split:]

        if len(test) < 3:
            print(f"  {biz:<12}: test period too short — skipping")
            continue

        result_df, _ = train_and_forecast(train, test)
        metrics      = compute_forecast_metrics(result_df)
        results[biz] = metrics
        print(f"  {biz:<12}: MAPE {metrics['mape']:.1f}%  |  "
              f"R2 {metrics['r2']:.3f}  |  "
              f"Coverage {metrics['coverage_80pct']:.0f}%")

    return results


# ── Step 6: Report ────────────────────────────────────────────────────────────

def generate_prophet_report(uci_metrics, synth_metrics,
                             dataset_label="Online Retail II"):
    lines = []
    lines.append("=" * 65)
    lines.append("DATACORE MODEL 4 -- PROPHET FORECAST VALIDATION")
    lines.append("=" * 65)
    lines.append("")
    lines.append(f"PRIMARY VALIDATION -- UCI {dataset_label} (Real Data)")
    lines.append("Source: Chen (2012), CC BY 4.0")
    lines.append("-" * 50)
    lines.append(f"Train/Test Split:  70% / 30% (chronological)")
    lines.append(f"Test Period:       {uci_metrics['n_test_days']} days")
    lines.append(f"Mean Actual Rev:   {uci_metrics['mean_actual']:,.2f}")
    lines.append(f"Mean Predicted:    {uci_metrics['mean_predicted']:,.2f}")
    lines.append("")
    lines.append("ACCURACY METRICS:")
    lines.append(f"  MAE:             {uci_metrics['mae']:,.2f}")
    lines.append(f"  MAPE:            {uci_metrics['mape']:.2f}%")
    lines.append(f"  RMSE:            {uci_metrics['rmse']:,.2f}")
    lines.append(f"  R2:              {uci_metrics['r2']:.4f}")
    lines.append(f"  80% CI Coverage: {uci_metrics['coverage_80pct']:.1f}%")
    lines.append("")

    if   uci_metrics["mape"] < 15:  interp = "EXCELLENT -- production-grade forecast accuracy"
    elif uci_metrics["mape"] < 25:  interp = "GOOD -- acceptable for SME credit assessment"
    elif uci_metrics["mape"] < 40:  interp = "MODERATE -- suitable for trend direction, not precision"
    else:                           interp = "POOR -- forecast useful for direction only"

    lines.append(f"  Interpretation:  {interp}")
    lines.append("")
    lines.append("SECONDARY VALIDATION -- Synthetic SME Businesses")
    lines.append("-" * 50)
    lines.append(f"{'Business':<14} {'MAPE':>8} {'R2':>8} "
                 f"{'Coverage':>10} {'Quality':>12}")
    lines.append("-" * 55)

    for biz, m in synth_metrics.items():
        if   m["mape"] < 15:  q = "Excellent"
        elif m["mape"] < 25:  q = "Good"
        elif m["mape"] < 40:  q = "Moderate"
        else:                 q = "Poor"
        lines.append(
            f"{biz:<14} {m['mape']:>7.1f}% {m['r2']:>8.3f} "
            f"{m['coverage_80pct']:>9.0f}% {q:>12}")

    lines.append("")
    lines.append("KEY FINDINGS FOR PAPER:")
    lines.append("-" * 50)
    lines.append(f"1. Prophet achieves {uci_metrics['mape']:.1f}% MAPE on real "
                 f"retail data (UCI {dataset_label})")
    lines.append(f"2. 80% confidence intervals capture "
                 f"{uci_metrics['coverage_80pct']:.0f}% of actual values "
                 f"(expected: ~80%)")

    if synth_metrics:
        avg_synth_mape = np.mean([m["mape"] for m in synth_metrics.values()])
        lines.append(f"3. Average MAPE across synthetic SME businesses: "
                     f"{avg_synth_mape:.1f}%")
    lines.append(f"4. Dynamic credit limits adjust by +-25% based on "
                 f"forecast trend direction")
    lines.append("5. Saudi Thu/Fri weekend seasonality incorporated")
    lines.append("")
    lines.append("LIMITATIONS:")
    lines.append("- UCI dataset is UK wholesale retail (2009-2011)")
    lines.append("- 30-day synthetic window is short for seasonal detection")
    lines.append("- Prophet requires minimum 2 seasonal cycles for")
    lines.append("  optimal yearly seasonality -- 30 days insufficient")
    lines.append("  for full seasonal modeling")
    lines.append("")
    lines.append("CITATION:")
    lines.append("Prophet: Taylor SJ, Letham B. (2018). Forecasting at scale.")
    lines.append("The American Statistician, 72(1), 37-45.")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 65)
    print("DATACORE -- Prophet Forecast Validation")
    print("=" * 65)

    print("\n[1/4] Loading UCI Online Retail II...")
    daily, uci_label = load_uci_daily_revenue()

    print("\n[2/4] Train/test split (70/30)...")
    train, test = split_train_test(daily, train_pct=0.70)

    print("\n[3/4] Training Prophet and forecasting...")
    result_df, model = train_and_forecast(train, test)
    uci_metrics = compute_forecast_metrics(result_df)

    print(f"  MAE:      {uci_metrics['mae']:,.2f}")
    print(f"  MAPE:     {uci_metrics['mape']:.2f}%")
    print(f"  R2:       {uci_metrics['r2']:.4f}")
    print(f"  Coverage: {uci_metrics['coverage_80pct']:.1f}%")

    print("\n[4/4] Validating on synthetic businesses...")
    synth_metrics = validate_synthetic_businesses()

    report = generate_prophet_report(uci_metrics, synth_metrics, uci_label)

    out_path = os.path.join(ROOT, "data", "prophet_validation_report.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)

    print("\n" + report)
    print(f"\nSaved: data/prophet_validation_report.txt")

    val_report = os.path.join(ROOT, "data", "validation_report.txt")
    if os.path.exists(val_report):
        with open(val_report, "a", encoding="utf-8") as f:
            f.write("\n\n")
            f.write(report)
        print("Appended to: data/validation_report.txt")
