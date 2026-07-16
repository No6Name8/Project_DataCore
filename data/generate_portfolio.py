#!/usr/bin/env python3
"""
generate_portfolio.py — DataCore Portfolio Generator
Generates 500 synthetic Saudi SME businesses across 12 behavioral archetypes.
Run from project root: python data/generate_portfolio.py
Outputs:
  data/portfolio/{bid}_transactions.csv
  data/portfolio/{bid}_energy.csv
  data/portfolio/portfolio_summary.json
"""

import os, sys, json, math, time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
PORTFOLIO_DIR = os.path.join(ROOT, "data", "portfolio")
os.makedirs(PORTFOLIO_DIR, exist_ok=True)

from models.business_classifier import BusinessClassifier, ARCHETYPES
from models.expense_estimator import ExpenseEstimator

# ── Seed ─────────────────────────────────────────────────────────────────────
SEED = 2025
rng  = np.random.default_rng(SEED)

START_DATE = datetime(2024, 10, 1)
N_DAYS     = 91

# DSCR constants (same as dscr_model.py)
BASE_RATE  = 0.065
LOAN_TERM  = 36
LOAN_PCT   = 0.40
_r = BASE_RATE / 12
_n = LOAN_TERM
AMORT_FACTOR       = _r * (1 + _r) ** _n / ((1 + _r) ** _n - 1)
ANNUAL_DEBT_FACTOR = AMORT_FACTOR * 12 * LOAN_PCT   # ≈ 0.1484

# ── Archetype distribution (507 total) ───────────────────────────────────────
ARCH_DIST = {
    "A": 111, "B": 71,  "C": 20,  "D": 40,
    "E": 31,  "F": 51,  "G": 36,  "H": 30,
    "I": 20,  "J": 31,  "K": 25,  "L": 41,
}
assert sum(ARCH_DIST.values()) == 507

# ── Hour weight templates (24 bins, normalized) ───────────────────────────────
def _hw(*v):
    a = np.array(v, dtype=float)
    return a / a.sum()

HW = {
    "A": _hw(0.01,0.01,0.01,0.01,0.01,0.02, 0.08,0.70,0.90,0.75,0.45,0.38,
             0.75,0.88,0.80,0.45,0.75,0.88, 0.60,0.32,0.15,0.08,0.04,0.02),
    "B": _hw(0.18,0.09,0.04,0.02,0.02,0.07, 0.14,0.56,0.80,0.75,0.56,0.52,
             0.80,0.88,0.76,0.58,0.68,0.82, 0.92,0.98,0.88,0.68,0.38,0.22),
    "C": _hw(0.00,0.00,0.00,0.00,0.00,0.00, 0.00,0.00,0.01,0.35,0.50,0.55,
             0.60,0.55,0.50,0.40,0.35,0.30, 0.25,0.15,0.05,0.01,0.00,0.00),
    "D": _hw(0.00,0.00,0.00,0.00,0.00,0.00, 0.00,0.00,0.01,0.25,0.45,0.50,
             0.50,0.45,0.40,0.30,0.20,0.15, 0.10,0.02,0.00,0.00,0.00,0.00),
    "E": _hw(0.00,0.00,0.00,0.00,0.00,0.00, 0.00,0.00,0.15,0.50,0.70,0.80,
             0.60,0.50,0.55,0.65,0.70,0.60, 0.40,0.20,0.05,0.01,0.00,0.00),
    "F": _hw(0.15,0.08,0.04,0.03,0.02,0.05, 0.12,0.50,0.75,0.72,0.55,0.50,
             0.80,0.85,0.78,0.58,0.68,0.82, 0.90,0.95,0.85,0.65,0.35,0.22),
    "G": _hw(0.10,0.05,0.03,0.02,0.02,0.06, 0.15,0.60,0.85,0.80,0.62,0.58,
             0.88,0.92,0.82,0.62,0.72,0.85, 0.95,1.00,0.90,0.70,0.40,0.25),
    "H": _hw(0.00,0.00,0.00,0.00,0.00,0.00, 0.00,0.00,0.01,0.10,0.25,0.40,
             0.55,0.60,0.65,0.70,0.80,0.90, 1.00,0.95,0.80,0.55,0.30,0.10),
    "I": _hw(0.00,0.00,0.00,0.00,0.00,0.00, 0.00,0.00,0.01,0.20,0.35,0.45,
             0.50,0.55,0.60,0.65,0.70,0.75, 0.80,0.85,0.80,0.60,0.35,0.10),
    "J": _hw(0.00,0.00,0.00,0.00,0.00,0.00, 0.00,0.02,0.15,0.55,0.75,0.80,
             0.65,0.55,0.60,0.70,0.75,0.70, 0.55,0.35,0.15,0.05,0.01,0.00),
    "K": _hw(0.00,0.00,0.00,0.00,0.00,0.00, 0.00,0.00,0.10,0.55,0.80,0.90,
             0.70,0.55,0.60,0.75,0.80,0.65, 0.35,0.10,0.02,0.00,0.00,0.00),
    "L": _hw(0.00,0.00,0.00,0.00,0.00,0.00, 0.00,0.00,0.01,0.05,0.15,0.30,
             0.50,0.60,0.70,0.80,0.90,1.00, 0.95,0.85,0.65,0.40,0.15,0.05),
}

# Payment methods [mada, cash, credit_card, bank_transfer]
PAY_M = ["mada", "cash", "credit_card", "bank_transfer"]
PAY_W = {
    "A": [0.65,0.20,0.15,0.00], "B": [0.50,0.40,0.10,0.00],
    "C": [0.00,0.25,0.15,0.60], "D": [0.00,0.10,0.20,0.70],
    "E": [0.70,0.18,0.12,0.00], "F": [0.60,0.25,0.15,0.00],
    "G": [0.76,0.17,0.07,0.00], "H": [0.68,0.15,0.17,0.00],
    "I": [0.46,0.35,0.04,0.15], "J": [0.55,0.35,0.10,0.00],
    "K": [0.85,0.08,0.07,0.00], "L": [0.78,0.14,0.08,0.00],
}

# Energy base kWh per day per archetype
ENERGY_BASE = {
    "A": (60, 90),  "B": (120,180), "C": (200,350), "D": (15,35),
    "E": (25,55),   "F": (35,65),   "G": (300,500), "H": (80,160),
    "I": (80,140),  "J": (20,45),   "K": (40,80),   "L": (30,60),
}

# ── Name pools ────────────────────────────────────────────────────────────────
NAMES_FOOD = [
    "Al Waha Restaurant","Riyadh Coffee House","Nakheel Cafe","Tamr Cafe",
    "Al Salam Grill","Shaheen Restaurant","Qahwa Al Khobar","Bader Pastry",
    "Najd Kitchen","Al Reem Sandwich","Faisal Sweets","Oasis Coffee",
    "Al Jazeera Grill","Ahlan Bakehouse","Noura Fast Food","Mazoon Cafe",
    "Turki Shawarma","Layla Sweets","Watan Kitchen","Aseel Restaurant",
    "Hana Coffee","Al Ula Cafe","Rawabi Grill","Zaid Burgers",
    "Saqar Shawarma","Al Rasheed Meals","Jouri Kitchen","Durra Cafe",
    "Reef Restaurant","Majd Pastries","Hilal Grill","Al Nada Cafe",
    "Qamar Kitchen","Tariq Sweets","Bayan Restaurant","Rayan Coffee",
    "Baraka Grill","Sanad Cafe","Shams Fast Bites","Al Zuhoor Cafe",
    "Rayhan Sweets","Mukhtar Grill","Joha Bites","Wail Coffee Corner",
    "Salwa Restaurant","Sultan Kitchen","Nouf Pastry","Saffron Cafe",
    "Al Yamamah Food Court","Layan Shawarma","Dalal Kitchen","Farida Cafe",
    "Ghaith Restaurant","Nour Sweets","Masoud Grill","Rima Bakery Cafe",
    "Hessa Kitchen","Abad Coffee","Manar Restaurant","Falak Cafe",
    "Salam Shawarma","Walid Grill House","Sana Pastry","Nura Cafe",
    "Al Ameen Kitchen","Zuhair Sweets","Elan Restaurant","Bawadi Cafe",
    "Rawdah Fast Food","Omar Grill","Wijdan Kitchen","Arwa Sweets",
    "Siraj Restaurant","Hamad Grill","Rawan Kitchen","Asma Cafe",
    "Mansour Restaurant","Shatha Fast Food","Bahaa Coffee","Mona Sweets",
    "Al Bushra Kitchen","Ibrahim Grill","Doaa Cafe","Lutuf Restaurant",
    "Adel Sweets","Abdulaziz Kitchen","Ola Grill House","Renad Coffee",
    "Yara Restaurant","Khuzama Cafe","Majed Kitchen","Rand Sweets",
    "Abeer Restaurant","Marzouq Grill","Safaa Kitchen","Fuad Cafe",
    "Badr Pastry Coffee","Manal Restaurant","Nadia Kitchen","Taif Cafe",
    "Khaled Grill","Layla Kitchen","Yusuf Sweets","Deema Restaurant",
    "Faris Cafe","Hanadi Kitchen","Saif Grill","Munirah Restaurant",
    "Amer Fast Food","Basim Sweets Cafe","Rayyan Kitchen","Ghaida Grill",
    "Jaber Restaurant","Lujain Cafe",
]
NAMES_RETAIL = [
    "Al Baraka Minimarket","Jomhoor Superstore","Al Majd General Store",
    "Nakheel Mini Mart","Riyadh Daily Needs","Hilal Minimarket",
    "Al Safa Provisions","Tamim Supermarket","Bader General Store",
    "Wafi Mini Mart","Rawabi Provisions","Al Saad Daily Store",
    "Nour Minimarket","Samar General Goods","Alia Provisions",
    "Al Khaleej Superstore","Dana Mini Mart","Zidane General Store",
    "Al Rayyan Minimarket","Manar Provisions","Sami Market",
    "Al Wafa Minimarket","Baraka General Store","Faris Daily Market",
    "Hamza Provisions","Sara Mini Mart","Luban Superstore",
    "Saif General Goods","Omar Daily Store","Ghanim Minimarket",
    "Al Watan Provisions","Khalid General Store","Rami Superstore",
    "Abdulla Mini Mart","Nouf Provisions","Yusuf Daily Needs",
    "Amal Minimarket","Fawwaz General Store","Nadia Provisions",
    "Turki Market","Maha Minimarket","Sulaiman General Store",
    "Hind Provisions","Mishary Mini Mart","Al Rawdah Superstore",
    "Saba General Goods","Zayed Daily Store","Hessa Minimarket",
    "Ghaida Provisions","Manal General Store","Reem Market",
    "Abdulrahman Mini Mart","Lubna Provisions","Fahad Superstore",
    "Munira General Goods","Talib Daily Market","Hanan Minimarket",
    "Waleed Provisions","Jumana General Store","Faten Market",
    "Malik Mini Mart","Zahra Superstore","Khaled Daily Store",
    "Sabah Provisions","Omar General Goods","Lina Minimarket",
    "Basem Provisions","Ramadan General Store","Deema Market",
    "Saad Mini Mart","Fatema Superstore","Mansour Daily Store",
    "Dana General Goods","Ibtisam Minimarket","Samer Provisions",
]
NAMES_AUTO_CAR = [
    "Al Rawabi Auto Gallery","Tariq Motors","Majed Auto Trading",
    "Saad Car Center","Riyadh Auto Hub","Al Salam Motors",
    "Fahd Auto Gallery","Juba Motors","Al Majd Car Center",
    "Najd Auto Trading","Bader Motors","Sultan Auto Gallery",
    "Khalid Car Center","Watan Motors","Hamza Auto Trading",
    "Al Hilal Auto Gallery","Saif Motors","Turki Car Center",
    "Faris Auto Trading","Wafi Motors",
]
NAMES_REALESTATE = [
    "Majd Real Estate","Al Ittifaq Properties","Rawabi Realty",
    "Sanad Real Estate","Al Baraka Properties","Ghaith Realty",
    "Talal Real Estate","Nakheel Properties","Bayan Realty",
    "Zuhair Real Estate","Madar Properties","Firas Realty",
    "Al Watan Real Estate","Mawared Properties","Isnad Realty",
    "Hashem Real Estate","Maskan Properties","Aqarat Riyadh",
    "Al Jawhara Properties","Dar Al Salam Realty","Istismar Realty",
    "Aqari Solutions","Al Qimam Properties","Dimah Real Estate",
    "Modon Properties","Sakan Realty","Mukhtat Properties",
    "Al Aoun Real Estate","Fath Properties","Khulood Realty",
    "Wafaa Real Estate","Abdulaziz Properties","Rayan Realty",
    "Fahad Real Estate","Jomana Properties","Sulaiman Realty",
    "Hanan Real Estate","Khalid Properties","Sami Realty",
    "Turki Real Estate",
]
NAMES_SERVICES = [
    "Noura Beauty Salon","Lama Spa Beauty","Al Noor Laundromat",
    "Clean City Laundry","Baraka Clinic","Zahra Dental Center",
    "Salam Medical Center","Al Shifa Pharmacy","Rawabi Laundromat",
    "Hana Beauty Studio","Dana Spa","Nakheel Laundry",
    "Sara Physiotherapy","Tariq Optical Center","Joha Barbershop",
    "Hatem Hair Salon","Dalal Beauty Lounge","Randa Nail Studio",
    "Faraj Barbershop","Maha Wellness Center","Al Reem Laundry",
    "Basim Dry Cleaning","Lina Beauty Center","Ola Hair Studio",
    "Widad Clinic","Arwa Dental Center","Rima Pharmacy",
    "Ibtisam Optical","Nadia Salon","Hessa Beauty Lounge",
    "Majed Barbershop","Samir Hair Center","Jouri Spa",
    "Sabah Beauty Studio","Rawdah Laundry","Wafa Nail Center",
    "Al Watan Optical","Fatema Clinic","Ghaida Physiotherapy",
    "Lujain Beauty Center","Marzouq Optical","Nawaf Clinic",
    "Munira Pharmacy","Turki Laundromat","Khalid Barbershop",
    "Tariq Hair Center","Nour Spa Beauty","Yousif Clinic",
    "Suad Beauty Lounge","Abeer Dental Center",
]
NAMES_ELECTRONICS = [
    "Reem Electronics","Al Nakheel Tech Hub","Saad IT Solutions",
    "Bader Gadgets","Rawabi Electronics","Tech Corner Riyadh",
    "Al Majd Digital","Smart World Electronics","Faris Tech Hub",
    "Turki Gadgets","Nour Electronics","Jomhoor Tech",
    "Al Watan Digital","Majed Gadgets","Khalid IT Hub",
    "Saif Electronics","Amer Digital Corner","Omar Tech World",
    "Hamza Electronics","Zaid Gadgets Center","Samir IT Hub",
    "Al Rasheed Tech","Dana Electronics","Ghaida Digital",
    "Sulaiman Gadgets","Wafi Electronics","Tariq Tech Hub",
    "Mishary Digital","Nawaf Gadgets","Basim Electronics",
]
NAMES_MOTO = [
    "Al Waha Motorbikes","Saqar Cycles","Qasem Bikes",
    "Hamad Motorbike Center","Turki Two Wheels","Zaid Cycles",
    "Al Jazeera Bikes","Faris Motorbike Trading","Saif Cycles",
    "Basim Two Wheels","Nawaf Motorbikes","Khalid Bikes",
    "Mishary Cycles","Saad Two Wheels","Omar Motorbike Center",
    "Al Rasheed Bikes","Majed Cycles","Wafi Motorbikes",
    "Yousif Bikes","Sultan Cycles",
]
NAMES_FASHION = [
    "Sarah Boutique","Lama Fashion","Deema Mode","Jumana Boutique",
    "Amal Fashion House","Noor Collection","Rana Boutique",
    "Hessa Fashion","Dalal Mode","Randa Style",
    "Lina Boutique","Rawan Collection","Ghaida Fashion",
    "Sabah Boutique","Jouri Mode","Noura Style",
    "Dana Boutique","Hana Collection","Arwa Fashion",
    "Ola Boutique","Lujain Mode","Fatema Style",
    "Salma Boutique","Munira Collection","Suad Fashion",
    "Widad Boutique","Abeer Mode","Renad Style",
    "Khulood Boutique","Farah Collection","Shaima Fashion",
    "Asma Boutique","Rima Mode","Nadia Style",
    "Bayan Boutique","Ibtisam Collection","Wafa Fashion",
    "Shahd Boutique","Rand Mode","Jumana Style",
]

NAME_POOLS = {
    "A": NAMES_FOOD,        "B": NAMES_RETAIL,
    "C": NAMES_AUTO_CAR,    "D": NAMES_REALESTATE,
    "E": NAMES_SERVICES,    "F": NAMES_SERVICES,
    "G": NAMES_RETAIL,      "H": NAMES_ELECTRONICS,
    "I": NAMES_MOTO,        "J": NAMES_SERVICES,
    "K": NAMES_SERVICES,    "L": NAMES_FASHION,
}

# ── Lognormal parameters ──────────────────────────────────────────────────────
def lognormal_params(mean, cv):
    """Return (mu_ln, sigma_ln) such that E[X]=mean and CV(X)=cv."""
    sigma_ln = math.sqrt(math.log(1 + cv ** 2))
    mu_ln    = math.log(mean) - sigma_ln ** 2 / 2
    return mu_ln, sigma_ln


# ── Transaction generator ─────────────────────────────────────────────────────
def gen_transactions(arch_key, spec, bid):
    avg_ticket   = float(rng.normal(*spec["avg_ticket"]))
    ticket_cv    = max(0.05, float(rng.normal(*spec["ticket_cv"])))
    avg_daily_tx = max(1.0, float(rng.normal(*spec["avg_daily_tx"])))
    active_ratio = float(np.clip(rng.normal(*spec["active_days"]), 0.10, 1.0))

    mu_ln, sigma_ln = lognormal_params(max(1, avg_ticket), ticket_cv)
    hw  = HW[arch_key]
    pw  = PAY_W[arch_key]

    ts_list, amt_list, pay_list = [], [], []
    for d in range(N_DAYS):
        if rng.random() > active_ratio:
            continue
        day   = START_DATE + timedelta(days=d)
        n_tx  = max(1, int(rng.normal(avg_daily_tx, max(1, avg_daily_tx * 0.20))))
        hours = rng.choice(24, size=n_tx, p=hw)
        mins  = rng.integers(0, 60, size=n_tx)
        secs  = rng.integers(0, 60, size=n_tx)
        amts  = rng.lognormal(mu_ln, sigma_ln, size=n_tx)
        amts  = np.clip(amts, 1.0, avg_ticket * 15)
        pays  = rng.choice(PAY_M, size=n_tx, p=pw)
        for h, m, s, a, p in zip(hours, mins, secs, amts, pays):
            ts_list.append(day.replace(hour=int(h), minute=int(m), second=int(s))
                           .strftime("%Y-%m-%d %H:%M:%S"))
            amt_list.append(round(float(a), 2))
            pay_list.append(p)

    if not ts_list:
        # Fallback: at least 1 day of transactions
        day = START_DATE + timedelta(days=N_DAYS // 2)
        n = max(1, int(avg_daily_tx))
        for i in range(n):
            ts_list.append(day.replace(hour=10+i%12, minute=0).strftime("%Y-%m-%d %H:%M:%S"))
            amt_list.append(round(float(np.exp(mu_ln)), 2))
            pay_list.append(PAY_M[0])

    df = pd.DataFrame({
        "transaction_id": [f"{bid}-{i+1:06d}" for i in range(len(ts_list))],
        "timestamp":      ts_list,
        "amount_sar":     amt_list,
        "payment_method": pay_list,
    })
    return df.sort_values("timestamp").reset_index(drop=True)


def gen_energy(arch_key, tx_df):
    lo, hi = ENERGY_BASE[arch_key]
    rows = []
    all_dates = [START_DATE + timedelta(days=d) for d in range(N_DAYS)]
    for day in all_dates:
        ds     = day.strftime("%Y-%m-%d")
        n_tx   = int((tx_df["timestamp"].str.startswith(ds)).sum())
        base   = rng.uniform(lo, hi)
        total  = round(float(base + n_tx * rng.uniform(0.05, 0.3)), 2)
        pk_f   = rng.uniform(0.50, 0.72)
        pk     = round(total * pk_f, 2)
        eff    = round(float(np.clip(rng.normal(0.65, 0.12), 0.20, 0.99)), 4)
        rows.append({"date": ds, "total_kwh": total,
                     "peak_hour_kwh": pk, "off_peak_kwh": round(total-pk, 2),
                     "energy_efficiency_score": eff})
    return pd.DataFrame(rows)


# ── DSCR computation (inline) ─────────────────────────────────────────────────
def compute_dscr(total_revenue_30d, expense_ratio):
    """Compute DSCR from 30-day (or period) revenue and expense ratio."""
    annual_revenue = total_revenue_30d * (365 / N_DAYS)
    noi_annual     = annual_revenue * (1 - expense_ratio)
    loan_amount    = annual_revenue * LOAN_PCT
    ann_debt_svc   = loan_amount * ANNUAL_DEBT_FACTOR
    dscr           = noi_annual / ann_debt_svc if ann_debt_svc > 0 else 0.0

    if   dscr >= 2.0: risk_tier = "very_low"
    elif dscr >= 1.5: risk_tier = "low"
    elif dscr >= 1.25: risk_tier = "medium"
    elif dscr >= 1.0: risk_tier = "high"
    else:             risk_tier = "critical"

    mults = {"very_low":1.5, "low":1.2, "medium":0.9, "high":0.6, "critical":0.0}
    avg_daily = annual_revenue / 365
    limit     = round(avg_daily * 90 * mults[risk_tier], 0)

    return {
        "dscr_score":       round(dscr, 4),
        "risk_tier":        risk_tier,
        "credit_limit_sar": limit,
        "annual_noi_sar":   round(noi_annual, 2),
        "annual_revenue":   round(annual_revenue, 2),
    }


# ── Fraud assignment ──────────────────────────────────────────────────────────
# Target: ~68% clean, ~24% flagged, ~8% frozen
FRAUD_ROLL = rng.random(507)

def assign_fraud(idx):
    r = FRAUD_ROLL[idx]
    if r < 0.68:
        return {"status": "clean",   "score": int(rng.integers(0, 26))}
    elif r < 0.92:
        return {"status": "flagged", "score": int(rng.integers(30, 71))}
    else:
        return {"status": "frozen",  "score": int(rng.integers(75, 101))}


# ── Revenue trend ─────────────────────────────────────────────────────────────
def revenue_trend(tx_df):
    tx_df = tx_df.copy()
    tx_df["date"] = tx_df["timestamp"].str[:10]
    daily = tx_df.groupby("date")["amount_sar"].sum()
    dates = sorted(daily.index)
    if len(dates) < 10:
        return "steady"
    mid = len(dates) // 2
    first_half = float(daily.iloc[:mid].mean())
    last_half  = float(daily.iloc[mid:].mean())
    if first_half <= 0:
        return "steady"
    ratio = last_half / first_half
    if ratio > 1.08:
        return "growing"
    elif ratio < 0.92:
        return "declining"
    return "steady"


# ── Weekday multiplier patterns (Mon=0 … Sun=6, Saudi Thu/Fri weekend) ────────
_WDAY = {
    # arch → [Mon, Tue, Wed, Thu,  Fri,  Sat,  Sun]
    "A": [0.80, 0.90, 1.00, 1.30, 1.35, 1.10, 0.55],  # food — Thu/Fri peak
    "B": [0.75, 0.85, 0.95, 1.30, 1.40, 1.05, 0.70],  # retail
    "C": [1.05, 1.10, 1.10, 0.85, 0.50, 0.90, 1.00],  # auto — closed Fri
    "D": [1.05, 1.10, 1.10, 0.70, 0.40, 0.90, 1.00],  # real estate
    "E": [1.05, 1.10, 1.10, 0.80, 0.50, 0.90, 1.05],  # services
    "F": [0.85, 0.90, 1.00, 1.20, 1.25, 1.10, 0.70],  # laundromat
    "G": [0.80, 0.85, 0.95, 1.30, 1.45, 1.10, 0.55],  # supermarket
    "H": [0.90, 0.95, 1.05, 1.20, 1.10, 1.10, 0.70],  # electronics
    "I": [1.00, 1.05, 1.05, 1.15, 0.75, 1.05, 0.95],  # vehicle dealer
    "J": [0.90, 0.95, 1.00, 1.20, 1.10, 1.10, 0.75],  # personal services
    "K": [1.10, 1.15, 1.15, 0.75, 0.35, 0.85, 1.00],  # medical
    "L": [0.80, 0.85, 0.95, 1.30, 1.40, 1.10, 0.60],  # fashion
}

# ── Forecast series with weekday variation, noise, widening CI ───────────────
def make_forecast_series(avg_daily_rev, trend_dir, arch_key="A", n=30):
    trend_rate = {"growing": 0.005, "steady": 0.0, "declining": -0.004}[trend_dir]
    wday_mults = _WDAY.get(arch_key, _WDAY["A"])
    base_date  = datetime(2025, 7, 1)
    series = []
    for i in range(n):
        fdate        = base_date + timedelta(days=i)
        wday         = fdate.weekday()
        trend_factor = math.exp(trend_rate * i)
        noise        = float(rng.normal(1.0, 0.06))          # ±6% noise
        pred         = max(0.0, avg_daily_rev * trend_factor * wday_mults[wday] * noise)
        uncertainty  = 0.12 + i * 0.004                      # widens with horizon
        series.append({
            "date":              fdate.strftime("%Y-%m-%d"),
            "predicted_revenue": round(pred, 2),
            "upper_bound":       round(pred * (1 + uncertainty), 2),
            "lower_bound":       round(max(0.0, pred * (1 - uncertainty)), 2),
        })
    return series


# ── Main generation loop ──────────────────────────────────────────────────────
def main():
    t0 = time.time()

    # Load models once
    print("Loading models...")
    clf = BusinessClassifier()
    clf.load()
    est = ExpenseEstimator()
    print("  Models loaded.\n")

    # Build list of (arch_key, index_in_pool)
    biz_list = []
    for arch_key, count in ARCH_DIST.items():
        pool = NAME_POOLS[arch_key]
        indices = list(range(count))
        rng.shuffle(indices)
        biz_list.extend([(arch_key, i % len(pool)) for i in indices])
    rng.shuffle(biz_list)

    summary_rows = []
    name_counters = {k: 0 for k in ARCH_DIST}

    for biz_idx, (arch_key, pool_idx) in enumerate(biz_list):
        bid      = f"biz_{biz_idx+1:04d}"
        spec     = ARCHETYPES[arch_key]
        name_ctr = name_counters[arch_key]
        pool     = NAME_POOLS[arch_key]
        # Disambiguate names that would repeat
        base_name = pool[pool_idx % len(pool)]
        name      = base_name if name_ctr < len(pool) else f"{base_name} {name_ctr//len(pool)+1}"
        name_counters[arch_key] += 1

        # Generate data
        tx_df  = gen_transactions(arch_key, spec, bid)
        en_df  = gen_energy(arch_key, tx_df)

        # Classify
        tx_clf = tx_df.copy()
        tx_clf["timestamp"] = pd.to_datetime(tx_clf["timestamp"])
        try:
            clf_result = clf.classify_from_data(tx_clf)
            cluster_id  = int(clf_result.get("cluster_id", -1))
            confidence  = round(float(clf_result.get("confidence", 0.0)), 4)
            archetype   = clf_result.get("archetype_description",
                                        spec.get("label", "unknown"))
            raw_feats   = clf_result.get("raw_features", {})
        except Exception as e:
            print(f"  WARN: classify failed for {bid}: {e}")
            cluster_id, confidence, archetype, raw_feats = -1, 0.0, spec.get("label",""), {}

        # Expense ratio
        try:
            profile       = est._derive_profile(raw_feats)
            is_commission = profile.get("is_commission_based", False)
            exp_result    = est.estimate(profile, holds_inventory=(arch_key in ["B","C","G","H","I"]))
            expense_ratio = exp_result["total_expense_ratio"]
        except Exception:
            is_commission = (arch_key == "D")
            expense_ratio = 0.35 if arch_key == "D" else 0.65

        # DSCR
        total_rev  = float(tx_df["amount_sar"].sum())
        dscr_data  = compute_dscr(total_rev, expense_ratio)

        # Revenue metrics
        tx_df["_date"] = tx_df["timestamp"].str[:10]
        daily_rev = tx_df.groupby("_date")["amount_sar"].sum()
        avg_daily = round(float(daily_rev.mean()), 2)
        trend_dir = revenue_trend(tx_df)
        tx_df.drop(columns=["_date"], inplace=True)

        # Fraud
        fraud_info = assign_fraud(biz_idx)
        sme_ready  = (
            dscr_data["risk_tier"] in ("very_low", "low") and
            fraud_info["status"] != "frozen" and
            trend_dir in ("growing", "steady")
        )

        # Energy summary
        avg_eff = round(float(en_df["energy_efficiency_score"].mean()), 4)
        green_days = int((en_df["energy_efficiency_score"] > 0.85).sum())

        # ── Build detail JSON (same shape as /api/dashboard/{bid}) ────────────
        recent_tx = tx_df.tail(10).to_dict(orient="records")
        energy_trend_data = en_df.tail(7).to_dict(orient="records")
        forecast_series   = make_forecast_series(avg_daily, trend_dir, arch_key)

        detail = {
            "business": {
                "id": bid, "name": name,
                "type": arch_key.lower(),
                "sector": spec.get("label", "unknown"),
                "archetype": archetype,
                "loan_pipeline": "sme",
            },
            "summary": {
                "business_id":           bid,
                "period":                f"{START_DATE.strftime('%Y-%m-%d')} to "
                                         f"{(START_DATE+timedelta(days=N_DAYS-1)).strftime('%Y-%m-%d')}",
                "total_transactions":    int(len(tx_df)),
                "total_revenue_sar":     round(total_rev, 2),
                "avg_daily_revenue_sar": avg_daily,
                "avg_daily_transactions": round(float(len(tx_df)) / N_DAYS, 1),
                "avg_energy_kwh":        round(float(en_df["total_kwh"].mean()), 2),
                "avg_efficiency_score":  avg_eff,
                "green_days":            [r["date"] for r in en_df[en_df["energy_efficiency_score"]>0.85].to_dict("records")],
                "payment_method_breakdown": tx_df["payment_method"].value_counts(normalize=True).round(4).to_dict(),
            },
            "dscr": {
                "business_id":               bid,
                "dscr_score":                dscr_data["dscr_score"],
                "risk_tier":                 dscr_data["risk_tier"],
                "approved_credit_limit_sar": dscr_data["credit_limit_sar"],
                "dynamic_credit_limit":      {
                    "adjusted_credit_limit": dscr_data["credit_limit_sar"],
                    "trend_direction": trend_dir,
                    "adjustment_multiplier": 1.10 if trend_dir=="growing" else (0.90 if trend_dir=="declining" else 1.0),
                },
                "expense_ratio":             expense_ratio,
                "expense_source":            "commission_based_lookup" if is_commission else "ai_derived",
                "archetype_description":     archetype,
                "net_operating_income_sar":  round(dscr_data["annual_noi_sar"] / 12, 2),
                "interest_rate_base":        BASE_RATE,
                "final_interest_rate":       BASE_RATE - (0.005 if green_days >= 2 else 0),
                "sustainability_eligible":   green_days >= 2,
                "revenue_metrics": {
                    "total_revenue":     round(total_rev, 2),
                    "avg_daily_revenue": avg_daily,
                    "revenue_trend":     trend_dir,
                },
                "transition_readiness": {
                    "decision":         "approve" if sme_ready else "decline",
                    "blocking_reasons": [] if sme_ready else ["DSCR or fraud threshold not met"],
                    "gates_passed":     ["revenue_verified","archetype_classified"] + (["dscr_sufficient"] if sme_ready else []),
                    "recommended_pipeline": "sme_loan" if sme_ready else "monitor",
                },
            },
            "fraud": {
                "business_id":    bid,
                "overall_status": fraud_info["status"],
                "fraud_score":    fraud_info["score"],
                "approval_frozen": fraud_info["status"] == "frozen",
                "anomalies":       [],
                "checks_passed":  ["amount_range","hour_pattern","payment_method"],
                "reasons":        [] if fraud_info["status"] == "clean" else
                                  ["Behavioral anomaly detected"] if fraud_info["status"] == "flagged" else
                                  ["Critical anomaly — review required"],
            },
            "forecast": {
                "summary": {
                    "trend_direction": trend_dir,
                    "avg_predicted_revenue": avg_daily,
                    "confidence": round(confidence, 4),
                },
                "series": forecast_series,
            },
            "recent_transactions": recent_tx,
            "energy_trend":        energy_trend_data,
        }

        # ── Write files ───────────────────────────────────────────────────────
        tx_df.to_csv(os.path.join(PORTFOLIO_DIR, f"{bid}_transactions.csv"), index=False)
        en_df.to_csv(os.path.join(PORTFOLIO_DIR, f"{bid}_energy.csv"),       index=False)
        with open(os.path.join(PORTFOLIO_DIR, f"{bid}_detail.json"), "w", encoding="utf-8") as f:
            json.dump(detail, f)

        # ── Summary row ───────────────────────────────────────────────────────
        summary_rows.append({
            "business_id":         bid,
            "name":                name,
            "archetype":           archetype,
            "archetype_key":       arch_key,
            "cluster_id":          cluster_id,
            "confidence":          confidence,
            "dscr_score":          dscr_data["dscr_score"],
            "risk_tier":           dscr_data["risk_tier"],
            "fraud_status":        fraud_info["status"],
            "fraud_score":         fraud_info["score"],
            "credit_limit_sar":    dscr_data["credit_limit_sar"],
            "revenue_trend":       trend_dir,
            "sme_transition_ready": sme_ready,
            "commission_based":    is_commission,
            "days_active":         N_DAYS,
            "avg_daily_revenue_sar": avg_daily,
            "expense_ratio":       round(expense_ratio, 4),
        })

        if (biz_idx + 1) % 50 == 0:
            elapsed = time.time() - t0
            print(f"  [{biz_idx+1:3d}/500] {elapsed:.1f}s elapsed")

    # ── Write summary ─────────────────────────────────────────────────────────
    summary_path = os.path.join(PORTFOLIO_DIR, "portfolio_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_rows, f)

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s. Files written to data/portfolio/")
    print(f"Total businesses: {len(summary_rows)}")

    # Distribution report
    from collections import Counter
    arch_counts = Counter(r["archetype_key"] for r in summary_rows)
    print("\nArchetype distribution:")
    for k, n in sorted(arch_counts.items()):
        print(f"  {k}: {ARCHETYPES[k]['label']:45s}  {n:3d}")

    fraud_counts = Counter(r["fraud_status"] for r in summary_rows)
    total = len(summary_rows)
    print(f"\nFraud status:")
    for s in ("clean","flagged","frozen"):
        c = fraud_counts.get(s, 0)
        print(f"  {s:8s}: {c:3d}  ({c/total*100:.1f}%)")

    risk_counts = Counter(r["risk_tier"] for r in summary_rows)
    print(f"\nRisk tiers:")
    for t in ("very_low","low","medium","high","critical"):
        c = risk_counts.get(t, 0)
        print(f"  {t:10s}: {c:3d}  ({c/total*100:.1f}%)")

    sme_ready = sum(1 for r in summary_rows if r["sme_transition_ready"])
    print(f"\nSME transition ready: {sme_ready} ({sme_ready/total*100:.1f}%)")
    comm = sum(1 for r in summary_rows if r["commission_based"])
    print(f"Commission-based:     {comm}")


if __name__ == "__main__":
    main()
