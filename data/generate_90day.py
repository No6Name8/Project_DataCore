"""
generate_90day.py
Generates 90-day datasets for all 6 Saudi SME businesses.
Date range: 2025-04-01 to 2025-06-30
Same business parameters as the 30-day scripts — extended window only.
Saves to data/processed/ replacing existing files.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "processed")

START_DATE = datetime(2025, 4, 1)
DATES      = [START_DATE + timedelta(days=i) for i in range(90)]

def out(filename):
    return os.path.join(DATA_DIR, filename)

def is_thu_fri(dt):
    return dt.weekday() in (3, 4)   # Saudi consumer weekend

def is_fri_sat(dt):
    return dt.weekday() in (4, 5)   # Official Saudi weekend (real estate)

def is_end_of_month(dt, n=3):
    """True if dt is within last n days of its month."""
    next_month = dt.replace(day=28) + timedelta(days=4)
    last_day   = (next_month - timedelta(days=next_month.day)).day
    return dt.day >= (last_day - n + 1)

def peak_day(tx_df):
    tmp = tx_df.copy()
    tmp["date"] = tmp["timestamp"].str[:10]
    day_rev = tmp.groupby("date")["amount_sar"].sum()
    d = day_rev.idxmax()
    return d, day_rev[d]

# =============================================================================
# BUSINESS 1 — LAUNDROMAT
# =============================================================================

LAUN_HOUR_W = np.array([
    0.10, 0.05, 0.03, 0.02, 0.02, 0.05,
    0.20, 0.60, 1.00, 0.90, 0.70, 0.50,
    0.90, 0.95, 0.70, 0.50, 0.40, 0.70,
    0.85, 0.95, 1.00, 0.80, 0.50, 0.20,
])
LAUN_HOUR_W /= LAUN_HOUR_W.sum()

LAUN_CYCLES = {"quick_wash": (15, 25), "standard": (25, 40),
               "heavy_duty": (40, 65), "dry_clean": (50, 120)}
LAUN_CYC_W  = [0.30, 0.40, 0.20, 0.10]
LAUN_PAY    = ["mada", "cash", "credit"]
LAUN_PAY_W  = [0.60, 0.25, 0.15]
LAUN_MACH   = [f"M{str(i).zfill(2)}" for i in range(1, 9)]

# 3 green days spread across 90 days
LAUN_GREENS  = {datetime(2025, 4, 22).date(),
                datetime(2025, 5, 15).date(),
                datetime(2025, 6, 10).date()}
# Anomaly in April for history context; main anomaly in June (final 30 days)
LAUN_SPIKE1  = datetime(2025, 4, 30).date()   # smaller 3AM spike
LAUN_SPIKE2  = datetime(2025, 6, 14).date()   # main 3AM spike — shows in dashboard

def gen_laun_tx():
    rows = []
    for day in DATES:
        is_wknd = is_thu_fri(day)
        if is_wknd:
            count = np.random.randint(65, 111)
        else:
            count = np.random.randint(45, 81)
        if not is_wknd and np.random.rand() < 0.125:
            count = int(count * np.random.uniform(0.4, 0.65))

        hours = np.random.choice(24, size=count, p=LAUN_HOUR_W)
        tss   = [day.replace(hour=int(h), minute=np.random.randint(0, 60),
                              second=np.random.randint(0, 60)) for h in hours]

        if day.date() == LAUN_SPIKE1:
            for _ in range(np.random.randint(8, 12)):
                tss.append(day.replace(hour=3, minute=np.random.randint(0, 60),
                                       second=np.random.randint(0, 60)))
        if day.date() == LAUN_SPIKE2:
            for _ in range(np.random.randint(15, 21)):
                tss.append(day.replace(hour=3, minute=np.random.randint(0, 60),
                                       second=np.random.randint(0, 60)))
        tss.sort()

        for i, ts in enumerate(tss):
            cyc    = np.random.choice(list(LAUN_CYCLES), p=LAUN_CYC_W)
            lo, hi = LAUN_CYCLES[cyc]
            rows.append({
                "transaction_id": f"TXN-{day.strftime('%Y%m%d')}-{i+1:04d}",
                "timestamp":      ts.strftime("%Y-%m-%d %H:%M:%S"),
                "amount_sar":     round(np.random.uniform(lo, hi), 2),
                "payment_method": np.random.choice(LAUN_PAY, p=LAUN_PAY_W),
                "machine_id":     np.random.choice(LAUN_MACH),
                "cycle_type":     cyc,
            })
    return pd.DataFrame(rows)

def gen_laun_energy(tx_df):
    rows = []
    for day in DATES:
        ds  = day.strftime("%Y-%m-%d")
        n   = (tx_df["timestamp"].str.startswith(ds)).sum()
        base  = np.random.uniform(80, 120)
        total = round(base + n * np.random.uniform(0.8, 1.5), 2)
        pk_f  = np.random.uniform(0.55, 0.70)
        pk    = round(total * pk_f, 2)
        kwh_per_tx = total / max(n, 1)
        raw_eff    = 1.0 - (kwh_per_tx - 1.5) / (4.0 - 1.5)
        eff        = float(np.clip(raw_eff, 0.0, 1.0))
        if day.date() in LAUN_GREENS:
            eff = round(np.random.uniform(0.86, 0.95), 4)
        else:
            eff = round(eff, 4)
        rows.append({"date": ds, "total_kwh": total, "peak_hour_kwh": pk,
                     "off_peak_kwh": round(total - pk, 2),
                     "energy_efficiency_score": eff})
    return pd.DataFrame(rows)

# =============================================================================
# BUSINESS 2 — CAFE
# =============================================================================

CAFE_HOUR_W = np.array([
    0.01, 0.01, 0.01, 0.01, 0.01, 0.03,
    0.10, 0.80, 1.00, 0.85, 0.50, 0.40,
    0.80, 0.95, 0.90, 0.50, 0.80, 0.90,
    0.60, 0.30, 0.15, 0.08, 0.04, 0.02,
])
CAFE_HOUR_W /= CAFE_HOUR_W.sum()

CAFE_CATS  = {"coffee_drinks": (12, 28), "food_items": (18, 55),
              "combo_meals": (35, 75), "specialty_drinks": (22, 45)}
CAFE_CAT_W = [0.40, 0.25, 0.20, 0.15]
CAFE_PAY   = ["mada", "cash", "credit"]
CAFE_PAY_W = [0.65, 0.20, 0.15]
CAFE_STAFF = [f"STF{str(i).zfill(2)}" for i in range(1, 7)]

CAFE_CLOSURE = datetime(2025, 4, 12).date()   # POS failure
CAFE_FRAUD   = datetime(2025, 6, 19).date()   # 2AM spike — FINAL 30 DAYS
CAFE_GREENS  = {datetime(2025, 4, 10).date(),
                datetime(2025, 5, 18).date(),
                datetime(2025, 6, 25).date()}

def gen_cafe_tx():
    rows = []
    for day in DATES:
        if day.date() == CAFE_CLOSURE:
            count = 8
        elif is_thu_fri(day):
            count = np.random.randint(90, 151)
        else:
            count = np.random.randint(70, 121)

        hours = np.random.choice(24, size=count, p=CAFE_HOUR_W)
        tss   = [day.replace(hour=int(h), minute=np.random.randint(0, 60),
                              second=np.random.randint(0, 60)) for h in hours]

        if day.date() == CAFE_FRAUD:
            for _ in range(np.random.randint(10, 16)):
                tss.append(day.replace(hour=2, minute=np.random.randint(0, 60),
                                       second=np.random.randint(0, 60)))
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
        eff   = float(np.clip(1.0 - (total / max(n, 1) - 0.5) / 2.5, 0, 1))
        if day.date() in CAFE_GREENS:
            eff = round(np.random.uniform(0.86, 0.95), 4)
        else:
            eff = round(eff, 4)
        rows.append({"date": ds, "total_kwh": total, "peak_hour_kwh": pk,
                     "off_peak_kwh": round(total - pk, 2),
                     "energy_efficiency_score": eff})
    return pd.DataFrame(rows)

# =============================================================================
# BUSINESS 3 — MINIMARKET
# =============================================================================

MINI_HOUR_W = np.array([
    0.20, 0.10, 0.05, 0.03, 0.02, 0.08,
    0.15, 0.60, 0.85, 0.80, 0.60, 0.55,
    0.85, 0.90, 0.80, 0.60, 0.70, 0.85,
    0.95, 1.00, 0.90, 0.70, 0.40, 0.25,
])
MINI_HOUR_W /= MINI_HOUR_W.sum()

MINI_BASKETS = {"small_basket": (8, 45), "medium_basket": (45, 180),
                "large_basket": (180, 450)}
MINI_BSK_W   = [0.50, 0.35, 0.15]
MINI_PAY     = ["mada", "cash", "credit"]
MINI_PAY_W   = [0.50, 0.40, 0.10]
MINI_CATS    = ["groceries", "beverages", "household", "personal_care", "snacks"]
MINI_CAT_W   = [0.35, 0.25, 0.15, 0.10, 0.15]

MINI_FRAUD1 = datetime(2025, 5,  5).date()   # smaller early anomaly
MINI_FRAUD2 = datetime(2025, 6, 11).date()   # main 3AM cash fraud — FINAL 30 DAYS
MINI_GREENS = {datetime(2025, 4, 15).date(),
               datetime(2025, 5, 10).date(),
               datetime(2025, 6, 20).date()}

def gen_mini_tx():
    rows = []
    for day in DATES:
        count = (np.random.randint(200, 321) if is_thu_fri(day)
                 else np.random.randint(150, 251))
        hours = np.random.choice(24, size=count, p=MINI_HOUR_W)
        tss   = sorted([day.replace(hour=int(h), minute=np.random.randint(0, 60),
                                    second=np.random.randint(0, 60)) for h in hours])

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

        if day.date() == MINI_FRAUD1:
            ft = day.replace(hour=3, minute=np.random.randint(0, 60),
                             second=np.random.randint(0, 60))
            rows.append({
                "transaction_id": f"MINI-{day.strftime('%Y%m%d')}-FRAUD1",
                "timestamp":      ft.strftime("%Y-%m-%d %H:%M:%S"),
                "amount_sar":     round(np.random.uniform(2_000, 3_200), 2),
                "payment_method": "cash",
                "basket_size":    "large_basket",
                "category":       "groceries",
            })

        if day.date() == MINI_FRAUD2:
            ft = day.replace(hour=3, minute=np.random.randint(0, 60),
                             second=np.random.randint(0, 60))
            rows.append({
                "transaction_id": f"MINI-{day.strftime('%Y%m%d')}-FRAUD2",
                "timestamp":      ft.strftime("%Y-%m-%d %H:%M:%S"),
                "amount_sar":     round(np.random.uniform(4_500, 6_000), 2),
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
        base  = max(100.0, np.random.uniform(120, 180))
        total = round(base + n * np.random.uniform(0.1, 0.2), 2)
        off_f = np.random.uniform(0.45, 0.50)
        off   = round(total * off_f, 2)
        eff   = float(np.clip(1.0 - (total / max(n, 1) - 0.5) / 1.5, 0, 1))
        if day.date() in MINI_GREENS:
            eff = round(np.random.uniform(0.86, 0.95), 4)
        else:
            eff = round(eff, 4)
        rows.append({"date": ds, "total_kwh": total,
                     "peak_hour_kwh": round(total - off, 2),
                     "off_peak_kwh": off, "energy_efficiency_score": eff})
    return pd.DataFrame(rows)

# =============================================================================
# BUSINESS 4 — REAL ESTATE OFFICE
# Closed Fri/Sat throughout. Commission = property_value × 0.025
# =============================================================================

RE_DEALS = {
    "apartment_rental": ("rental",  "apartment",   35_000,    85_000),
    "villa_rental":     ("rental",  "villa",        80_000,   200_000),
    "apartment_sale":   ("sale",    "apartment",   600_000, 1_400_000),
    "villa_sale":       ("sale",    "villa",      1_800_000, 5_500_000),
    "commercial_lease": ("lease",   "commercial",  120_000,   500_000),
    "land_sale":        ("sale",    "land",        800_000, 3_000_000),
}
RE_PAY   = ["bank_transfer", "credit", "cash"]
RE_PAY_W = [0.70, 0.20, 0.10]

RE_BIG_DAY = datetime(2025, 6, 16).date()   # 2 villa sales + commercial — FINAL 30 DAYS
RE_ANOMALY = datetime(2025, 6, 10).date()   # large villa commission — FINAL 30 DAYS
RE_DRY_S   = datetime(2025, 6, 22).date()   # dry spell start
RE_DRY_E   = datetime(2025, 6, 26).date()   # dry spell end (5 business days)
RE_GREENS  = {datetime(2025, 4,  5).date(),
              datetime(2025, 5, 12).date(),
              datetime(2025, 6,  5).date()}

def _re_make_deal(day, idx, key, fixed_value=None):
    dtype, ptype, lo, hi = RE_DEALS[key]
    pval = fixed_value if fixed_value else round(np.random.uniform(lo, hi), 0)
    comm = round(pval * 0.025, 2)
    ts   = day.replace(hour=np.random.randint(9, 18),
                       minute=np.random.randint(0, 60),
                       second=np.random.randint(0, 60))
    return {
        "transaction_id":     f"RE-{day.strftime('%Y%m%d')}-{idx:03d}",
        "timestamp":          ts.strftime("%Y-%m-%d %H:%M:%S"),
        "amount_sar":         comm,
        "payment_method":     np.random.choice(RE_PAY, p=RE_PAY_W),
        "deal_type":          dtype,
        "property_type":      ptype,
        "property_value_sar": pval,
        "commission_rate":    0.025,
    }

def gen_re_tx():
    rows = []
    for day in DATES:
        if is_fri_sat(day):
            continue

        if RE_DRY_S <= day.date() <= RE_DRY_E:
            continue

        if day.date() == RE_BIG_DAY:
            deals = [("villa_sale", None), ("villa_sale", None), ("commercial_lease", None)]
        elif day.date() == RE_ANOMALY:
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
        if day.date() in RE_GREENS:
            eff = round(np.random.uniform(0.86, 0.95), 4)
        rows.append({"date": ds, "total_kwh": total, "peak_hour_kwh": pk,
                     "off_peak_kwh": round(total - pk, 2),
                     "energy_efficiency_score": eff})
    return pd.DataFrame(rows)

# =============================================================================
# BUSINESS 5 — CAR DEALERSHIP
# End-of-month spike on last 3 days of April, May, June.
# Fleet purchase in June (anomaly in final 30 days).
# =============================================================================

CAR_VTYPES = {
    "economy_new":   ("new",  ["Toyota Yaris", "Toyota Corolla"],                    63_000,   125_000),
    "midrange_new":  ("new",  ["Toyota Camry", "Toyota Hilux", "Toyota Highlander"], 105_000,  208_000),
    "luxury_new":    ("new",  ["Toyota Land Cruiser", "Lexus LX"],                   250_000,  614_000),
    "used_economy":  ("used", ["Used Economy"],                                       25_000,    90_000),
    "used_midrange": ("used", ["Used Mid/High"],                                      90_000,   200_000),
}
CAR_VT_W  = [0.25, 0.30, 0.15, 0.20, 0.10]
CAR_FIN   = ["bank_loan", "cash", "dealer_financing", "lease"]
CAR_FIN_W = [0.45, 0.30, 0.15, 0.10]
CAR_PAY   = ["bank_transfer", "cash", "credit"]
CAR_PAY_W = [0.60, 0.25, 0.15]

CAR_FLEET  = datetime(2025, 6, 12).date()   # fleet: 3 Land Cruisers — FINAL 30 DAYS
CAR_GREENS = {datetime(2025, 4, 18).date(),
              datetime(2025, 5, 18).date(),
              datetime(2025, 6, 18).date()}

def gen_car_tx():
    rows = []
    for day in DATES:
        if is_end_of_month(day):
            count = np.random.randint(6, 11)   # end-of-month spike
        else:
            count = np.random.randint(2, 7)

        if day.date() == CAR_FLEET:
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
                                  minute=np.random.randint(0, 60),
                                  second=np.random.randint(0, 60))
                      for _ in range(count)])

        for i, ts in enumerate(tss):
            vt                    = np.random.choice(list(CAR_VTYPES), p=CAR_VT_W)
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
        eff   = round(np.random.uniform(0.40, 0.75), 4)
        if day.date() in CAR_GREENS:
            eff = round(np.random.uniform(0.86, 0.95), 4)
        rows.append({"date": ds, "total_kwh": total, "peak_hour_kwh": pk,
                     "off_peak_kwh": round(total - pk, 2),
                     "energy_efficiency_score": eff})
    return pd.DataFrame(rows)

# =============================================================================
# BUSINESS 6 — MOTORBIKE DEALERSHIP
# =============================================================================

MOTO_TYPES = {
    "scooter":          ( 4_500,   8_000),
    "entry_bike":       (10_000,  15_000),
    "mid_sport":        (15_000,  30_000),
    "large_sport":      (28_000,  50_000),
    "premium":          (42_000, 100_000),
    "accessories_only": (   150,   2_500),
}
MOTO_TYP_W = [0.12, 0.13, 0.15, 0.10, 0.10, 0.40]
MOTO_PAY   = ["mada", "cash", "bank_transfer", "credit"]
MOTO_PAY_W = [0.45, 0.35, 0.15, 0.05]

MOTO_SLOW_S = datetime(2025, 4, 10).date()   # slow week in April
MOTO_SLOW_E = datetime(2025, 4, 14).date()
MOTO_BULK   = datetime(2025, 6,  7).date()   # bulk accessories 11PM — FINAL 30 DAYS
MOTO_GREENS = {datetime(2025, 4, 23).date(),
               datetime(2025, 5, 23).date(),
               datetime(2025, 6, 20).date()}

def gen_moto_tx():
    rows = []
    for day in DATES:
        slow = MOTO_SLOW_S <= day.date() <= MOTO_SLOW_E
        if is_thu_fri(day):
            count = int(np.random.randint(3, 11) * 1.5)
        elif slow:
            count = np.random.randint(1, 3)
        else:
            count = np.random.randint(3, 11)

        tss = sorted([day.replace(hour=np.random.randint(10, 22),
                                  minute=np.random.randint(0, 60),
                                  second=np.random.randint(0, 60))
                      for _ in range(count)])

        for i, ts in enumerate(tss):
            btype  = np.random.choice(list(MOTO_TYPES), p=MOTO_TYP_W)
            lo, hi = MOTO_TYPES[btype]
            is_acc = (btype == "accessories_only")
            stype  = "accessories" if is_acc else np.random.choice(["new", "used"], p=[0.70, 0.30])
            rows.append({
                "transaction_id":       f"MOTO-{day.strftime('%Y%m%d')}-{i+1:03d}",
                "timestamp":            ts.strftime("%Y-%m-%d %H:%M:%S"),
                "amount_sar":           round(np.random.uniform(lo, hi), 2),
                "payment_method":       np.random.choice(MOTO_PAY, p=MOTO_PAY_W),
                "bike_type":            btype,
                "sale_type":            stype,
                "accessories_included": is_acc or (np.random.rand() < 0.30),
            })

        if day.date() == MOTO_BULK:
            bt = day.replace(hour=23, minute=np.random.randint(0, 60),
                             second=np.random.randint(0, 60))
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
        eff   = float(np.clip(1.0 - (total / max(n, 1) - 2.0) / 13.0, 0, 1))
        if day.date() in MOTO_GREENS:
            eff = round(np.random.uniform(0.86, 0.95), 4)
        else:
            eff = round(eff, 4)
        rows.append({"date": ds, "total_kwh": total, "peak_hour_kwh": pk,
                     "off_peak_kwh": round(total - pk, 2),
                     "energy_efficiency_score": eff})
    return pd.DataFrame(rows)

# =============================================================================
# GENERATE ALL
# =============================================================================

os.makedirs(DATA_DIR, exist_ok=True)

print(f"Generating 90-day datasets ({START_DATE.date()} to "
      f"{(START_DATE + timedelta(days=89)).date()}) ...")

laun_tx = gen_laun_tx()
laun_tx.to_csv(out("laundromat_transactions.csv"), index=False)
gen_laun_energy(laun_tx).to_csv(out("laundromat_energy.csv"), index=False)
print("  [OK] laundromat")

cafe_tx = gen_cafe_tx()
cafe_tx.to_csv(out("cafe_transactions.csv"), index=False)
gen_cafe_energy(cafe_tx).to_csv(out("cafe_energy.csv"), index=False)
print("  [OK] cafe")

mini_tx = gen_mini_tx()
mini_tx.to_csv(out("minimarket_transactions.csv"), index=False)
gen_mini_energy(mini_tx).to_csv(out("minimarket_energy.csv"), index=False)
print("  [OK] minimarket")

re_tx = gen_re_tx()
re_tx.to_csv(out("realestate_transactions.csv"), index=False)
gen_re_energy().to_csv(out("realestate_energy.csv"), index=False)
print("  [OK] realestate")

car_tx = gen_car_tx()
car_tx.to_csv(out("cardealer_transactions.csv"), index=False)
gen_car_energy().to_csv(out("cardealer_energy.csv"), index=False)
print("  [OK] cardealer")

moto_tx = gen_moto_tx()
moto_tx.to_csv(out("motorbike_transactions.csv"), index=False)
gen_moto_energy(moto_tx).to_csv(out("motorbike_energy.csv"), index=False)
print("  [OK] motorbike")

# =============================================================================
# SUMMARY TABLE
# =============================================================================

all_biz = [
    ("laundromat", "Al Noor Laundromat",    laun_tx),
    ("cafe",       "Qahwa Corner Cafe",     cafe_tx),
    ("minimarket", "Baraka Minimarket",     mini_tx),
    ("realestate", "Majd Real Estate",      re_tx),
    ("cardealer",  "Rawabi Auto Gallery",   car_tx),
    ("motorbike",  "Saqr Motorbikes",       moto_tx),
]

total_all = 0
print()
print("=" * 80)
print(f"DATACORE — 90-DAY BUSINESS DATASET SUMMARY")
print("=" * 80)
print(f"{'Business':<24} {'Transactions':>13} {'Revenue SAR':>18} "
      f"{'Avg Daily TX':>13} {'Period'}")
print("-" * 80)

for bid, name, df in all_biz:
    n_tx    = len(df)
    revenue = df["amount_sar"].sum()
    avg_tx  = n_tx / 90.0
    total_all += n_tx
    print(f"  {name:<22} {n_tx:>13,} {revenue:>18,.0f} "
          f"{avg_tx:>13.1f}   2025-04-01 to 2025-06-30")

print("-" * 80)
print(f"  {'TOTAL':<22} {total_all:>13,}")
print("=" * 80)
print(f"\n12 CSV files written to data/processed/")
