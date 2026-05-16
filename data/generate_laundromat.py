"""
generate_laundromat.py
Generates 30 days of realistic mock data for a laundromat business.
Outputs two CSV files: laundromat_transactions.csv and laundromat_energy.csv
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

# ── Date range ──────────────────────────────────────────────────────────────
START_DATE = datetime(2025, 6, 1)
END_DATE   = datetime(2025, 6, 30)
DATES      = [START_DATE + timedelta(days=i) for i in range(30)]

# ── Machine IDs ─────────────────────────────────────────────────────────────
MACHINES = [f"M{str(i).zfill(2)}" for i in range(1, 9)]  # M01–M08

# ── Cycle types and SAR ranges ───────────────────────────────────────────────
CYCLE_TYPES = {
    "quick_wash":  (15,  25),
    "standard":    (25,  40),
    "heavy_duty":  (40,  65),
    "dry_clean":   (50, 120),
}
# Probability of each cycle type being selected
CYCLE_WEIGHTS = [0.30, 0.40, 0.20, 0.10]

# ── Payment method probabilities ─────────────────────────────────────────────
PAYMENT_METHODS  = ["mada", "cash", "credit"]
PAYMENT_WEIGHTS  = [0.60,   0.25,   0.15]

# ── Hour-of-day traffic weights ──────────────────────────────────────────────
# Index = hour (0–23). Higher = more likely to have transactions.
HOUR_WEIGHTS = np.array([
    0.10, 0.05, 0.03, 0.02, 0.02, 0.05,  # 0–5  (late night / pre-dawn low)
    0.20, 0.60, 1.00, 0.90, 0.70, 0.50,  # 6–11 (morning ramp -> peak 8–10)
    0.90, 0.95, 0.70, 0.50, 0.40, 0.70,  # 12–17 (lunch peak 12–14)
    0.85, 0.95, 1.00, 0.80, 0.50, 0.20,  # 18–23 (evening peak 17–20)
])
HOUR_WEIGHTS /= HOUR_WEIGHTS.sum()  # normalise to probabilities

# ── Special dates ────────────────────────────────────────────────────────────
# Saudi weekends are Thursday (weekday=3) and Friday (weekday=4)
ANOMALY_DATE = datetime(2025, 6, 14)   # 3AM spike for fraud detection demo
GREEN_DAY    = datetime(2025, 6, 22)   # high efficiency day for sustainability demo


def is_saudi_weekend(dt: datetime) -> bool:
    return dt.weekday() in (3, 4)  # Thursday=3, Friday=4


def generate_transactions_for_day(date: datetime) -> list[dict]:
    """Return a list of transaction dicts for a single day."""
    rows = []

    # Base transaction count; weekends get 40% more
    if is_saudi_weekend(date):
        base_count = np.random.randint(65, 111)
    else:
        base_count = np.random.randint(45, 81)

    # Occasional slow day (roughly 1 in 8 weekdays)
    if not is_saudi_weekend(date) and np.random.rand() < 0.125:
        base_count = int(base_count * np.random.uniform(0.4, 0.65))

    # Anomaly day: inject a 3AM spike of 15–20 extra transactions
    anomaly_extra = []
    if date.date() == ANOMALY_DATE.date():
        spike_count = np.random.randint(15, 21)
        for _ in range(spike_count):
            # Cluster between 03:00–03:59
            hour   = 3
            minute = np.random.randint(0, 60)
            second = np.random.randint(0, 60)
            ts     = date.replace(hour=hour, minute=minute, second=second)
            anomaly_extra.append(ts)

    # Sample hours for the regular transactions
    hours = np.random.choice(24, size=base_count, p=HOUR_WEIGHTS)

    all_timestamps = []
    for h in hours:
        minute = np.random.randint(0, 60)
        second = np.random.randint(0, 60)
        all_timestamps.append(date.replace(hour=int(h), minute=minute, second=second))
    all_timestamps.extend(anomaly_extra)
    all_timestamps.sort()

    for i, ts in enumerate(all_timestamps):
        cycle = np.random.choice(list(CYCLE_TYPES.keys()), p=CYCLE_WEIGHTS)
        low, high = CYCLE_TYPES[cycle]
        amount    = round(np.random.uniform(low, high), 2)
        payment   = np.random.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS)
        machine   = np.random.choice(MACHINES)

        rows.append({
            "transaction_id": f"TXN-{date.strftime('%Y%m%d')}-{str(i+1).zfill(4)}",
            "timestamp":      ts.strftime("%Y-%m-%d %H:%M:%S"),
            "amount_sar":     amount,
            "payment_method": payment,
            "machine_id":     machine,
            "cycle_type":     cycle,
        })

    return rows


def generate_energy_for_day(date: datetime, tx_count: int) -> dict:
    """Return an energy reading dict correlated with transaction volume."""
    # Base load (lighting, compressors at idle, etc.)
    base_kwh = np.random.uniform(80, 120)

    # Each transaction adds ~0.8–1.5 kWh depending on cycle mix
    tx_kwh = tx_count * np.random.uniform(0.8, 1.5)

    total_kwh     = round(base_kwh + tx_kwh, 2)
    peak_fraction = np.random.uniform(0.55, 0.70)   # most energy during peak hours
    peak_kwh      = round(total_kwh * peak_fraction, 2)
    off_peak_kwh  = round(total_kwh - peak_kwh, 2)

    # Efficiency: lower kwh_per_transaction = more efficient
    kwh_per_tx = total_kwh / max(tx_count, 1)
    # Normalise: best observed ≈ 1.5 kwh/tx, worst ≈ 4.0 kwh/tx
    raw_score  = 1.0 - (kwh_per_tx - 1.5) / (4.0 - 1.5)
    efficiency = float(np.clip(raw_score, 0.0, 1.0))

    # Green day override: very high efficiency
    if date.date() == GREEN_DAY.date():
        efficiency = round(np.random.uniform(0.86, 0.95), 4)
    else:
        efficiency = round(efficiency, 4)

    return {
        "date":                   date.strftime("%Y-%m-%d"),
        "total_kwh":              total_kwh,
        "peak_hour_kwh":          peak_kwh,
        "off_peak_kwh":           off_peak_kwh,
        "energy_efficiency_score": efficiency,
    }


# ── Main generation loop ─────────────────────────────────────────────────────
all_transactions = []
all_energy       = []

for day in DATES:
    day_txns = generate_transactions_for_day(day)
    all_transactions.extend(day_txns)

    energy_row = generate_energy_for_day(day, len(day_txns))
    all_energy.append(energy_row)

# ── Build DataFrames and write CSVs ──────────────────────────────────────────
tx_df  = pd.DataFrame(all_transactions)
eng_df = pd.DataFrame(all_energy)

TX_PATH  = "data/laundromat_transactions.csv"
ENG_PATH = "data/laundromat_energy.csv"

tx_df.to_csv(TX_PATH,  index=False)
eng_df.to_csv(ENG_PATH, index=False)

# ── Summary ──────────────────────────────────────────────────────────────────
total_txns    = len(tx_df)
total_revenue = tx_df["amount_sar"].sum()
date_range    = f"{tx_df['timestamp'].min()[:10]} -> {tx_df['timestamp'].max()[:10]}"
avg_daily     = total_txns / 30

# Find the anomaly date by locating the day with 3AM transactions
tx_df["ts_dt"] = pd.to_datetime(tx_df["timestamp"])
anomaly_day_str = ANOMALY_DATE.strftime("%Y-%m-%d")
green_day_str   = GREEN_DAY.strftime("%Y-%m-%d")

print("=" * 50)
print("DataCore — Laundromat Dataset Summary")
print("=" * 50)
print(f"Total transactions : {total_txns:,}")
print(f"Total revenue      : {total_revenue:,.2f} SAR")
print(f"Date range         : {date_range}")
print(f"Avg daily txns     : {avg_daily:.1f}")
print(f"Anomaly date       : {anomaly_day_str}  (3AM spike injected)")
print(f"Green day          : {green_day_str}  (efficiency > 0.85)")
print(f"\nFiles written:")
print(f"  {TX_PATH}")
print(f"  {ENG_PATH}")
print("=" * 50)
