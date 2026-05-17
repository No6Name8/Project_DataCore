"""
generate_all_businesses.py
Generates 30-day realistic mock datasets for 5 Saudi businesses.
Each business: {name}_transactions.csv + {name}_energy.csv in the same data/ directory.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

DATA_DIR   = os.path.dirname(os.path.abspath(__file__))
START_DATE = datetime(2025, 6, 1)
DATES      = [START_DATE + timedelta(days=i) for i in range(30)]

def out(filename):
    return os.path.join(DATA_DIR, filename)

def is_thu_fri(dt):
    """Thu=3, Fri=4 — Saudi consumer weekend used by cafe/minimarket/motorbike."""
    return dt.weekday() in (3, 4)

def is_fri_sat(dt):
    """Fri=4, Sat=5 — official Saudi weekend used by real estate office."""
    return dt.weekday() in (4, 5)

def peak_day(tx_df):
    tmp = tx_df.copy()
    tmp["date"] = tmp["timestamp"].str[:10]
    day_rev = tmp.groupby("date")["amount_sar"].sum()
    d = day_rev.idxmax()
    return d, day_rev[d]

# =============================================================================
# BUSINESS 1 — CAFE
# =============================================================================

CAFE_HOUR_W = np.array([
    0.01, 0.01, 0.01, 0.01, 0.01, 0.03,   # 0-5  near-zero (dead hours 11PM-5AM)
    0.10, 0.80, 1.00, 0.85, 0.50, 0.40,   # 6-11 breakfast peak 7-9
    0.80, 0.95, 0.90, 0.50, 0.80, 0.90,   # 12-17 lunch 12-14, evening starts 16-17
    0.60, 0.30, 0.15, 0.08, 0.04, 0.02,   # 18-23 tapering; 18=6PM end of evening peak
])
CAFE_HOUR_W /= CAFE_HOUR_W.sum()

CAFE_CATS    = {"coffee_drinks": (12, 28), "food_items": (18, 55),
                "combo_meals": (35, 75), "specialty_drinks": (22, 45)}
CAFE_CAT_W   = [0.40, 0.25, 0.20, 0.15]
CAFE_PAY     = ["mada", "cash", "credit"]
CAFE_PAY_W   = [0.65, 0.20, 0.15]
CAFE_STAFF   = [f"STF{str(i).zfill(2)}" for i in range(1, 7)]

CAFE_CLOSURE = datetime(2025, 6,  8)   # POS failure / closure — only 8 txns all day
CAFE_FRAUD   = datetime(2025, 6, 19)   # 2AM spike (10-15 extra txns)
CAFE_GREEN   = datetime(2025, 6, 25)

def gen_cafe_tx():
    rows = []
    for day in DATES:
        if day.date() == CAFE_CLOSURE.date():
            count = 8
        elif is_thu_fri(day):
            count = np.random.randint(90, 151)
        else:
            count = np.random.randint(70, 121)

        hours = np.random.choice(24, size=count, p=CAFE_HOUR_W)
        tss   = [day.replace(hour=int(h), minute=np.random.randint(0,60),
                              second=np.random.randint(0,60)) for h in hours]

        # Fraud: 10-15 transactions at 2AM
        if day.date() == CAFE_FRAUD.date():
            for _ in range(np.random.randint(10, 16)):
                tss.append(day.replace(hour=2, minute=np.random.randint(0,60),
                                       second=np.random.randint(0,60)))
        tss.sort()

        for i, ts in enumerate(tss):
            cat    = np.random.choice(list(CAFE_CATS), p=CAFE_CAT_W)
            lo, hi = CAFE_CATS[cat]
            rows.append({
                "transaction_id": f"CAFE-{day.strftime('%Y%m%d')}-{i+1:04d}",
                "timestamp":      ts.strftime("%Y-%m-%d %H:%M:%S"),
                "amount_sar":     round(np.random.uniform(lo, hi), 2),
                "payment_method": np.random.choice(CAFE_PAY, p=CAFE_PAY_W),
                "item_category":  cat,
                "staff_id":       np.random.choice(CAFE_STAFF),
            })
    return pd.DataFrame(rows)

def gen_cafe_energy(tx_df):
    rows = []
    for day in DATES:
        ds    = day.strftime("%Y-%m-%d")
        n     = (tx_df["timestamp"].str.startswith(ds)).sum()
        base  = np.random.uniform(60, 90)
        total = round(base + n * np.random.uniform(0.3, 0.6), 2)
        pk_f  = np.random.uniform(0.55, 0.70)
        pk    = round(total * pk_f, 2)
        eff   = float(np.clip(1.0 - (total / max(n,1) - 0.5) / 2.5, 0, 1))
        eff   = round(np.random.uniform(0.86, 0.95), 4) if day.date() == CAFE_GREEN.date() else round(eff, 4)
        rows.append({"date": ds, "total_kwh": total, "peak_hour_kwh": pk,
                     "off_peak_kwh": round(total - pk, 2), "energy_efficiency_score": eff})
    return pd.DataFrame(rows)

# =============================================================================
# BUSINESS 2 — MINIMARKET
# =============================================================================

MINI_HOUR_W = np.array([
    0.20, 0.10, 0.05, 0.03, 0.02, 0.08,   # 0-5  some 24h night traffic, dead 1-5
    0.15, 0.60, 0.85, 0.80, 0.60, 0.55,   # 6-11 morning peak 7-9
    0.85, 0.90, 0.80, 0.60, 0.70, 0.85,   # 12-17 lunch 12-14, evening builds
    0.95, 1.00, 0.90, 0.70, 0.40, 0.25,   # 18-23 long evening peak 17-21
])
MINI_HOUR_W /= MINI_HOUR_W.sum()

MINI_BASKETS = {"small_basket": (8, 45), "medium_basket": (45, 180), "large_basket": (180, 450)}
MINI_BSK_W   = [0.50, 0.35, 0.15]
MINI_PAY     = ["mada", "cash", "credit"]
MINI_PAY_W   = [0.50, 0.40, 0.10]
MINI_CATS    = ["groceries", "beverages", "household", "personal_care", "snacks"]
MINI_CAT_W   = [0.35, 0.25, 0.15, 0.10, 0.15]

MINI_FRAUD   = datetime(2025, 6, 11)   # single 4500+ SAR cash txn at 3AM
MINI_GREEN   = datetime(2025, 6, 20)

def gen_mini_tx():
    rows = []
    for day in DATES:
        count = np.random.randint(200, 321) if is_thu_fri(day) else np.random.randint(150, 251)

        hours = np.random.choice(24, size=count, p=MINI_HOUR_W)
        tss   = sorted([day.replace(hour=int(h), minute=np.random.randint(0,60),
                                    second=np.random.randint(0,60)) for h in hours])

        for i, ts in enumerate(tss):
            bsk    = np.random.choice(list(MINI_BASKETS), p=MINI_BSK_W)
            lo, hi = MINI_BASKETS[bsk]
            rows.append({
                "transaction_id": f"MINI-{day.strftime('%Y%m%d')}-{i+1:04d}",
                "timestamp":      ts.strftime("%Y-%m-%d %H:%M:%S"),
                "amount_sar":     round(np.random.uniform(lo, hi), 2),
                "payment_method": np.random.choice(MINI_PAY, p=MINI_PAY_W),
                "basket_size":    bsk,
                "category":       np.random.choice(MINI_CATS, p=MINI_CAT_W),
            })

        # Fraud: 4500+ SAR cash at 3AM
        if day.date() == MINI_FRAUD.date():
            ft = day.replace(hour=3, minute=np.random.randint(0,60), second=np.random.randint(0,60))
            rows.append({
                "transaction_id": f"MINI-{day.strftime('%Y%m%d')}-FRAUD",
                "timestamp":      ft.strftime("%Y-%m-%d %H:%M:%S"),
                "amount_sar":     round(np.random.uniform(4500, 6000), 2),
                "payment_method": "cash",
                "basket_size":    "large_basket",
                "category":       "groceries",
            })
    return pd.DataFrame(rows)

def gen_mini_energy(tx_df):
    rows = []
    for day in DATES:
        ds    = day.strftime("%Y-%m-%d")
        n     = (tx_df["timestamp"].str.startswith(ds)).sum()
        # Fridges never turn off — floor is 100 kWh
        base  = max(100.0, np.random.uniform(120, 180))
        total = round(base + n * np.random.uniform(0.1, 0.2), 2)
        # Flat profile: off_peak is high (refrigeration runs 24h)
        off_f = np.random.uniform(0.45, 0.50)
        off   = round(total * off_f, 2)
        eff   = float(np.clip(1.0 - (total / max(n,1) - 0.5) / 1.5, 0, 1))
        eff   = round(np.random.uniform(0.86, 0.95), 4) if day.date() == MINI_GREEN.date() else round(eff, 4)
        rows.append({"date": ds, "total_kwh": total, "peak_hour_kwh": round(total - off, 2),
                     "off_peak_kwh": off, "energy_efficiency_score": eff})
    return pd.DataFrame(rows)

# =============================================================================
# BUSINESS 3 — REAL ESTATE OFFICE
# Commission = property_value * 0.025 (Saudi law cap, fixed)
# Work days: Sun-Thu; closed Fri/Sat
# =============================================================================

RE_DEALS = {
    "apartment_rental": ("rental",  "apartment",  35_000,    85_000),
    "villa_rental":     ("rental",  "villa",       80_000,   200_000),
    "apartment_sale":   ("sale",    "apartment",  600_000, 1_400_000),
    "villa_sale":       ("sale",    "villa",     1_800_000, 5_500_000),
    "commercial_lease": ("lease",   "commercial", 120_000,   500_000),
    "land_sale":        ("sale",    "land",       800_000, 3_000_000),
}
RE_PAY   = ["bank_transfer", "credit", "cash"]
RE_PAY_W = [0.70, 0.20, 0.10]

RE_BIG_DAY  = datetime(2025, 6, 16)   # 2 villa sales + 1 commercial lease
RE_DRY_S    = datetime(2025, 6, 22)   # dry spell start (Sun)
RE_DRY_E    = datetime(2025, 6, 26)   # dry spell end   (Thu) — 5 business days
RE_ANOMALY  = datetime(2025, 6, 10)   # single villa_sale at 5.2M SAR -> 130k commission
RE_GREEN    = datetime(2025, 6,  5)

def _re_make_deal(day, idx, key, fixed_value=None):
    dtype, ptype, lo, hi = RE_DEALS[key]
    pval = fixed_value if fixed_value else round(np.random.uniform(lo, hi), 0)
    comm = round(pval * 0.025, 2)
    ts   = day.replace(hour=np.random.randint(9, 18),
                       minute=np.random.randint(0, 60),
                       second=np.random.randint(0, 60))
    return {
        "transaction_id":   f"RE-{day.strftime('%Y%m%d')}-{idx:03d}",
        "timestamp":        ts.strftime("%Y-%m-%d %H:%M:%S"),
        "amount_sar":       comm,
        "payment_method":   np.random.choice(RE_PAY, p=RE_PAY_W),
        "deal_type":        dtype,
        "property_type":    ptype,
        "property_value_sar": pval,
        "commission_rate":  0.025,
    }

def gen_re_tx():
    rows = []
    for day in DATES:
        if is_fri_sat(day):
            continue   # office closed

        if RE_DRY_S.date() <= day.date() <= RE_DRY_E.date():
            continue   # 5-day dry spell

        if day.date() == RE_BIG_DAY.date():
            deals = [("villa_sale", None), ("villa_sale", None), ("commercial_lease", None)]
        elif day.date() == RE_ANOMALY.date():
            deals = [("villa_sale", 5_200_000)]
        else:
            n = np.random.randint(0, 5)
            if n == 0:
                continue
            deals = [(np.random.choice(list(RE_DEALS)), None) for _ in range(n)]

        for i, (key, fval) in enumerate(deals):
            rows.append(_re_make_deal(day, i + 1, key, fval))

    return pd.DataFrame(rows)

def gen_re_energy():
    rows = []
    for day in DATES:
        ds = day.strftime("%Y-%m-%d")
        if is_fri_sat(day):
            total = round(np.random.uniform(2, 6), 2)
            pk    = round(total * 0.3, 2)
            eff   = round(np.random.uniform(0.10, 0.30), 4)
        else:
            total = round(np.random.uniform(15, 35), 2)
            pk    = round(total * np.random.uniform(0.60, 0.75), 2)
            eff   = round(np.random.uniform(0.60, 0.80), 4)
        if day.date() == RE_GREEN.date():
            eff = round(np.random.uniform(0.86, 0.95), 4)
        rows.append({"date": ds, "total_kwh": total, "peak_hour_kwh": pk,
                     "off_peak_kwh": round(total - pk, 2), "energy_efficiency_score": eff})
    return pd.DataFrame(rows)

# =============================================================================
# BUSINESS 4 — CAR DEALERSHIP
# Real 2025 Saudi market prices; open daily 9AM-9PM
# =============================================================================

CAR_VTYPES = {
    "economy_new":  ("new",  ["Toyota Yaris", "Toyota Corolla"],          63_000,   125_000),
    "midrange_new": ("new",  ["Toyota Camry","Toyota Hilux","Toyota Highlander"], 105_000, 208_000),
    "luxury_new":   ("new",  ["Toyota Land Cruiser", "Lexus LX"],        250_000,   614_000),
    "used_economy": ("used", ["Used Economy"],                             25_000,    90_000),
    "used_midrange":("used", ["Used Mid/High"],                            90_000,   200_000),
}
CAR_VT_W   = [0.25, 0.30, 0.15, 0.20, 0.10]
CAR_FIN    = ["bank_loan", "cash", "dealer_financing", "lease"]
CAR_FIN_W  = [0.45, 0.30, 0.15, 0.10]
CAR_PAY    = ["bank_transfer", "cash", "credit"]
CAR_PAY_W  = [0.60, 0.25, 0.15]

CAR_FLEET  = datetime(2025, 6, 12)   # fleet: 3 Land Cruisers, 980k+ SAR
CAR_GREEN  = datetime(2025, 6, 18)

def gen_car_tx():
    rows = []
    for day in DATES:
        day_num = (day - START_DATE).days + 1
        count   = np.random.randint(6, 10) if day_num >= 28 else np.random.randint(2, 7)

        # Fleet purchase injected separately
        if day.date() == CAR_FLEET.date():
            fts = day.replace(hour=np.random.randint(10, 17),
                              minute=np.random.randint(0, 60),
                              second=np.random.randint(0, 60))
            rows.append({
                "transaction_id": f"CAR-{day.strftime('%Y%m%d')}-FLEET",
                "timestamp":      fts.strftime("%Y-%m-%d %H:%M:%S"),
                "amount_sar":     round(np.random.uniform(980_000, 1_100_000), 2),
                "payment_method": "bank_transfer",
                "vehicle_type":   "luxury_new",
                "vehicle_model":  "Toyota Land Cruiser x3 (Fleet)",
                "sale_type":      "new",
                "financing_type": "bank_loan",
            })

        tss = sorted([day.replace(hour=np.random.randint(9, 21),
                                  minute=np.random.randint(0,60),
                                  second=np.random.randint(0,60))
                      for _ in range(count)])

        for i, ts in enumerate(tss):
            vt             = np.random.choice(list(CAR_VTYPES), p=CAR_VT_W)
            stype, models, lo, hi = CAR_VTYPES[vt]
            rows.append({
                "transaction_id": f"CAR-{day.strftime('%Y%m%d')}-{i+1:03d}",
                "timestamp":      ts.strftime("%Y-%m-%d %H:%M:%S"),
                "amount_sar":     round(np.random.uniform(lo, hi), 2),
                "payment_method": np.random.choice(CAR_PAY, p=CAR_PAY_W),
                "vehicle_type":   vt,
                "vehicle_model":  np.random.choice(models),
                "sale_type":      stype,
                "financing_type": np.random.choice(CAR_FIN, p=CAR_FIN_W),
            })
    return pd.DataFrame(rows)

def gen_car_energy():
    rows = []
    for day in DATES:
        ds    = day.strftime("%Y-%m-%d")
        base  = np.random.uniform(200, 350) * (1.05 if is_thu_fri(day) else 1.0)
        total = round(base, 2)
        pk    = round(total * np.random.uniform(0.60, 0.72), 2)
        # Energy doesn't correlate strongly with sales count
        eff   = round(np.random.uniform(0.40, 0.75), 4)
        if day.date() == CAR_GREEN.date():
            eff = round(np.random.uniform(0.86, 0.95), 4)
        rows.append({"date": ds, "total_kwh": total, "peak_hour_kwh": pk,
                     "off_peak_kwh": round(total - pk, 2), "energy_efficiency_score": eff})
    return pd.DataFrame(rows)

# =============================================================================
# BUSINESS 5 — MOTORBIKE DEALERSHIP
# Real 2025 Saudi prices; open 10AM-10PM; Thu/Fri enthusiast weekend
# =============================================================================

MOTO_TYPES = {
    "scooter":         (4_500,   8_000),
    "entry_bike":     (10_000,  15_000),
    "mid_sport":      (15_000,  30_000),
    "large_sport":    (28_000,  50_000),
    "premium":        (42_000, 100_000),
    "accessories_only":   (150,  2_500),
}
# accessories_only = 40% of all transactions
MOTO_TYP_W  = [0.12, 0.13, 0.15, 0.10, 0.10, 0.40]
MOTO_PAY    = ["mada", "cash", "bank_transfer", "credit"]
MOTO_PAY_W  = [0.45, 0.35, 0.15, 0.05]

MOTO_BULK   = datetime(2025, 6,  7)   # bulk accessories 7500+ SAR at 11PM
MOTO_SLOW_S = datetime(2025, 6, 10)   # slow week: days 10-14
MOTO_SLOW_E = datetime(2025, 6, 14)
MOTO_GREEN  = datetime(2025, 6, 23)

def gen_moto_tx():
    rows = []
    for day in DATES:
        slow = MOTO_SLOW_S.date() <= day.date() <= MOTO_SLOW_E.date()
        if is_thu_fri(day):
            count = int(np.random.randint(3, 11) * 1.5)
        elif slow:
            count = np.random.randint(1, 3)
        else:
            count = np.random.randint(3, 11)

        tss = sorted([day.replace(hour=np.random.randint(10, 22),
                                  minute=np.random.randint(0,60),
                                  second=np.random.randint(0,60))
                      for _ in range(count)])

        for i, ts in enumerate(tss):
            btype  = np.random.choice(list(MOTO_TYPES), p=MOTO_TYP_W)
            lo, hi = MOTO_TYPES[btype]
            is_acc = (btype == "accessories_only")
            stype  = "accessories" if is_acc else np.random.choice(["new","used"], p=[0.70,0.30])
            rows.append({
                "transaction_id":       f"MOTO-{day.strftime('%Y%m%d')}-{i+1:03d}",
                "timestamp":            ts.strftime("%Y-%m-%d %H:%M:%S"),
                "amount_sar":           round(np.random.uniform(lo, hi), 2),
                "payment_method":       np.random.choice(MOTO_PAY, p=MOTO_PAY_W),
                "bike_type":            btype,
                "sale_type":            stype,
                "accessories_included": is_acc or (np.random.rand() < 0.30),
            })

        # Bulk accessories at 11PM (separate injection)
        if day.date() == MOTO_BULK.date():
            bt = day.replace(hour=23, minute=np.random.randint(0,60),
                             second=np.random.randint(0,60))
            rows.append({
                "transaction_id":       f"MOTO-{day.strftime('%Y%m%d')}-BULK",
                "timestamp":            bt.strftime("%Y-%m-%d %H:%M:%S"),
                "amount_sar":           round(np.random.uniform(7_500, 9_500), 2),
                "payment_method":       "cash",
                "bike_type":            "accessories_only",
                "sale_type":            "accessories",
                "accessories_included": True,
            })

    return pd.DataFrame(rows)

def gen_moto_energy(tx_df):
    rows = []
    for day in DATES:
        ds    = day.strftime("%Y-%m-%d")
        n     = (tx_df["timestamp"].str.startswith(ds)).sum()
        base  = np.random.uniform(80, 140)
        total = round(base + n * np.random.uniform(0.5, 1.2), 2)
        pk    = round(total * np.random.uniform(0.55, 0.70), 2)
        eff   = float(np.clip(1.0 - (total / max(n,1) - 2.0) / 13.0, 0, 1))
        eff   = round(np.random.uniform(0.86, 0.95), 4) if day.date() == MOTO_GREEN.date() else round(eff, 4)
        rows.append({"date": ds, "total_kwh": total, "peak_hour_kwh": pk,
                     "off_peak_kwh": round(total - pk, 2), "energy_efficiency_score": eff})
    return pd.DataFrame(rows)

# =============================================================================
# GENERATE ALL
# =============================================================================

print("Generating datasets...")

cafe_tx  = gen_cafe_tx();   cafe_tx.to_csv(out("cafe_transactions.csv"),  index=False)
cafe_en  = gen_cafe_energy(cafe_tx); cafe_en.to_csv(out("cafe_energy.csv"), index=False)
print("  [OK] cafe")

mini_tx  = gen_mini_tx();   mini_tx.to_csv(out("minimarket_transactions.csv"), index=False)
mini_en  = gen_mini_energy(mini_tx); mini_en.to_csv(out("minimarket_energy.csv"), index=False)
print("  [OK] minimarket")

re_tx    = gen_re_tx();     re_tx.to_csv(out("realestate_transactions.csv"), index=False)
re_en    = gen_re_energy(); re_en.to_csv(out("realestate_energy.csv"), index=False)
print("  [OK] realestate")

car_tx   = gen_car_tx();    car_tx.to_csv(out("cardealer_transactions.csv"), index=False)
car_en   = gen_car_energy(); car_en.to_csv(out("cardealer_energy.csv"), index=False)
print("  [OK] cardealer")

moto_tx  = gen_moto_tx();   moto_tx.to_csv(out("motorbike_transactions.csv"), index=False)
moto_en  = gen_moto_energy(moto_tx); moto_en.to_csv(out("motorbike_energy.csv"), index=False)
print("  [OK] motorbike")

# =============================================================================
# SUMMARY TABLE
# =============================================================================

businesses = [
    ("Cafe",                cafe_tx,
     f"{CAFE_CLOSURE.strftime('%Y-%m-%d')} (POS closure), "
     f"{CAFE_FRAUD.strftime('%Y-%m-%d')} (2AM fraud spike)",
     CAFE_GREEN.strftime("%Y-%m-%d")),

    ("Minimarket",          mini_tx,
     f"{MINI_FRAUD.strftime('%Y-%m-%d')} (3AM cash fraud 4500+ SAR)",
     MINI_GREEN.strftime("%Y-%m-%d")),

    ("Real Estate Office",  re_tx,
     f"{RE_BIG_DAY.strftime('%Y-%m-%d')} (2 villa sales + commercial), "
     f"{RE_ANOMALY.strftime('%Y-%m-%d')} (5.2M villa -> 130k commission)",
     RE_GREEN.strftime("%Y-%m-%d")),

    ("Car Dealership",      car_tx,
     f"{CAR_FLEET.strftime('%Y-%m-%d')} (fleet: 3 Land Cruisers 980k+)",
     CAR_GREEN.strftime("%Y-%m-%d")),

    ("Motorbike Dealership",moto_tx,
     f"{MOTO_BULK.strftime('%Y-%m-%d')} (bulk accessories 7500+ at 11PM), "
     f"slow week {MOTO_SLOW_S.strftime('%Y-%m-%d')} to {MOTO_SLOW_E.strftime('%Y-%m-%d')}",
     MOTO_GREEN.strftime("%Y-%m-%d")),
]

print()
print("=" * 78)
print("DATACORE — BUSINESS DATASET SUMMARY")
print("=" * 78)

for name, df, anomaly, green in businesses:
    total   = len(df)
    revenue = df["amount_sar"].sum()
    avg     = total / 30
    pd_, pr = peak_day(df)
    print(f"\n  Business       : {name}")
    print(f"  Total txns     : {total:,}")
    print(f"  Total revenue  : {revenue:>20,.2f} SAR")
    print(f"  Avg daily txns : {avg:.1f}")
    print(f"  Peak day       : {pd_}  ({pr:,.2f} SAR)")
    print(f"  Anomaly date   : {anomaly}")
    print(f"  Green day      : {green}")

print()
print("=" * 78)
print("10 CSV files written to data/")
print("=" * 78)
