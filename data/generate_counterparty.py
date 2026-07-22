#!/usr/bin/env python
"""
data/generate_counterparty.py
Adds a realistic, DELIBERATELY MESSY `counterparty_raw` column to the six demo
transaction CSVs so the counterparty enrichment layer is exercised in the demo
(not just in tests). Run from project root:  python data/generate_counterparty.py

Story design:
  * 4 businesses (cafe, laundromat, realestate, motorbike): diverse, stable
    supplier mix (merchants + utility + government + landlord), concentration
    below the flag threshold, suppliers spread across the whole window.
  * Baraka Minimarket: wholesale food/bev distributors + utility + one landlord.
  * Rawabi Auto Gallery: crafted so BOTH fraud flags fire —
      - ~92% of supplier tx go to the top-3 counterparties (concentration), and
      - most distinct "suppliers" are one-off payees that only appear in the
        recent third of the window (instability).

Values are intentionally in raw bank-statement formats: uppercase merchant names
with POS/terminal noise, SADAD/utility patterns, some Arabic strings.
Idempotent: re-running rebuilds the column deterministically (seeded).
"""
import os, sys
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "processed")
sys.path.insert(0, ROOT)

# ── Supplier pools (raw messy formats). (name, weight) ────────────────────────
POOLS = {
    "cafe": [
        ("SAUDI COFFEE WHOLESALE CO 4421", 22), ("ALMARAI DAIRY POS 8837", 16),
        ("شركة المخابز الطازجة", 12), ("TAMIMI MARKETS RIYADH 03421", 8),
        ("SADAD BILL PAYMENT 8827162", 7), ("STC INVOICE 44710", 6),
        ("SEC ELECTRICITY BILL 22981", 6), ("POS PURCHASE 8271 AL OLAYA RIYADH", 6),
        ("AL OTHAIM PACKAGING 552", 5), ("GAZT ZATCA VAT PAYMENT", 4),
        ("مؤسسة النخيل للعقار", 4), ("MADA PURCHASE CLEANING SUPPLIES 771", 4),
    ],
    "laundromat": [
        ("HENKEL DETERGENTS SUPPLY 3312", 20), ("شركة المنظفات الوطنية", 15),
        ("SADAD BILL PAYMENT 5521099", 10), ("STC INVOICE 88120", 8),
        ("SEC ELECTRICITY BILL 41220", 9), ("NWC WATER AUTHORITY 6621", 8),
        ("POS PURCHASE 2214 AL MALAZ", 7), ("PACKAGING SUPPLIES CO 118", 6),
        ("مؤسسة الإيجار العقارية", 6), ("GAZT ZATCA VAT PAYMENT", 4),
        ("SPARE PARTS TRADING 902", 4), ("MADA PURCHASE HANGERS 55", 3),
    ],
    "realestate": [
        ("MAJD PROPERTY MANAGEMENT 001", 62),   # one dominant property manager (expected)
        ("شركة مجد لإدارة الأملاك", 14),
        ("SADAD BILL PAYMENT 7712", 6), ("STC INVOICE 3391", 5),
        ("SEC ELECTRICITY BILL 8890", 5), ("GAZT ZATCA VAT PAYMENT", 4),
        ("MARKETING LISTINGS PORTAL 221", 4),
    ],
    "motorbike": [
        ("YAMAHA PARTS DISTRIBUTOR 4410", 20), ("HONDA MOTORS SUPPLY 2231", 17),
        ("شركة قطع الغيار المتحدة", 12), ("TRF TO 6612231 SUPPLIER", 8),
        ("SADAD BILL PAYMENT 9921", 7), ("STC INVOICE 5541", 6),
        ("SEC ELECTRICITY BILL 3320", 6), ("POS PURCHASE 4412 AL AZIZIYAH", 6),
        ("HELMET IMPORTS TRADING 88", 6), ("مؤسسة الإيجار التجاري", 5),
        ("GAZT ZATCA VAT PAYMENT", 4), ("LUBRICANTS WHOLESALE 337", 3),
    ],
    "minimarket": [
        ("PANDA RETAIL WHOLESALE 5521", 16), ("ALMARAI DISTRIBUTION 8832", 15),
        ("NADEC FOODS SUPPLY 2214", 13), ("شركة أغذية الطازج للتوزيع", 11),
        ("COCA COLA BOTTLING RIYADH 771", 9), ("SADAD BILL PAYMENT 33120", 6),
        ("STC INVOICE 66120", 5), ("SEC ELECTRICITY BILL 22190", 6),
        ("POS PURCHASE 8891 AL NASEEM", 5), ("مؤسسة العقار للإيجار", 5),
        ("GAZT ZATCA VAT PAYMENT", 4), ("CLEANING SUPPLIES CO 902", 5),
    ],
}

# Rawabi one-off "shell-like" payees (unique fingerprints, recent window only).
RAWABI_ONEOFFS = [
    "NAJD MOTORS 88", "SAHARA CARS TRADING 12", "TABUK AUTO 341", "HAIL MOTORS 55",
    "QASSIM CARS 907", "JEDDAH AUTO HOUSE 22", "DAMMAM MOTORS 61", "ASIR CARS 88",
    "NORTHERN AUTO 43", "شركة الصحراء للسيارات", "GULF MOTORS TRADING 71",
    "DESERT AUTO GALLERY 19", "OASIS CARS 82", "SUMMIT MOTORS 33", "FALCON AUTO 27",
    "شركة النسر للسيارات", "RIYADH SPEED CARS 90", "ELITE MOTORS 14", "PRIME AUTO 66",
    "ROYAL CARS TRADING 51", "STAR MOTORS 78", "شركة الماس للسيارات",
    "VICTORY AUTO 39", "HORIZON CARS 84", "PEARL MOTORS 20", "CROWN AUTO 47",
    "IMPERIAL CARS 73", " zenith motors 58", "APEX AUTO TRADING 11",
    "شركة القمة للسيارات", "MERIDIAN CARS 95", "VANTAGE MOTORS 62",
]
RAWABI_DOMINANT   = "AL RAJHI AUTO FINANCE 4471"     # ~82% of tx
RAWABI_SECONDARY  = "ABDULLAH CARS TRADING #22"      # ~10% of tx

COVERAGE = {  # fraction of rows that carry a counterparty (rest left blank)
    "cafe": 0.92, "laundromat": 0.90, "realestate": 0.95,
    "motorbike": 0.93, "minimarket": 0.90, "cardealer": 1.00,
}


def _assign_pool(n, pool, rng, coverage):
    names   = [p[0] for p in pool]
    weights = np.array([p[1] for p in pool], dtype=float)
    weights /= weights.sum()
    out = rng.choice(names, size=n, p=weights).astype(object)
    # Blank out (1 - coverage) of rows to keep coverage honest / realistic.
    if coverage < 1.0:
        blank_mask = rng.random(n) > coverage
        out[blank_mask] = ""
    return out


def _assign_rawabi(df, rng):
    """Concentration >90% to top-3 AND most distinct suppliers new in recent 30%."""
    df = df.sort_values("timestamp").reset_index(drop=True)
    n = len(df)
    cutoff = int(n * 0.70)                       # recent window = last 30%
    cp = np.empty(n, dtype=object)

    # Older 70%: dominant + secondary only (builds the concentration).
    for i in range(cutoff):
        cp[i] = RAWABI_DOMINANT if rng.random() < 0.85 else RAWABI_SECONDARY

    # Recent 30%: mostly still dominant, but sprinkle unique one-off payees so
    # they are numerous (distinct) yet small in share (keeps concentration high).
    recent_idx = list(range(cutoff, n))
    rng.shuffle(recent_idx)
    n_oneoff = min(len(RAWABI_ONEOFFS), max(1, int(len(recent_idx) * 0.30)))
    oneoff_positions = recent_idx[:n_oneoff]
    for k, i in enumerate(oneoff_positions):
        cp[i] = RAWABI_ONEOFFS[k]
    for i in recent_idx[n_oneoff:]:
        cp[i] = RAWABI_DOMINANT if rng.random() < 0.8 else RAWABI_SECONDARY

    df["counterparty_raw"] = cp
    return df


def run():
    from data.counterparty_utils import build_supplier_profile, supplier_instability_ratio
    print("Adding counterparty_raw to demo transaction CSVs...\n")
    for bid, pool in POOLS.items():
        path = os.path.join(DATA, f"{bid}_transactions.csv")
        df = pd.read_csv(path)
        if "counterparty_raw" in df.columns:
            df = df.drop(columns=["counterparty_raw"])
        rng = np.random.default_rng(hash(bid) % (2**32))
        df["counterparty_raw"] = _assign_pool(len(df), pool, rng, COVERAGE[bid])
        df.to_csv(path, index=False, encoding="utf-8")
        prof = build_supplier_profile(df["counterparty_raw"].tolist())
        print(f"  {bid:11} cov={prof['coverage_pct']:5.1f}%  distinct={prof['distinct_suppliers_count']:>3}  "
              f"conc={prof['concentration_ratio']*100:5.1f}%  kinds={prof['supplier_kind_distribution']}")

    # Rawabi (cardealer) — crafted flags
    path = os.path.join(DATA, "cardealer_transactions.csv")
    df = pd.read_csv(path)
    if "counterparty_raw" in df.columns:
        df = df.drop(columns=["counterparty_raw"])
    rng = np.random.default_rng(1234)
    df = _assign_rawabi(df, rng)
    df.to_csv(path, index=False, encoding="utf-8")
    prof = build_supplier_profile(df["counterparty_raw"].tolist())
    instab = supplier_instability_ratio(df.sort_values("timestamp")["counterparty_raw"].tolist())
    print(f"  {'cardealer':11} cov={prof['coverage_pct']:5.1f}%  distinct={prof['distinct_suppliers_count']:>3}  "
          f"conc={prof['concentration_ratio']*100:5.1f}%  instability={instab*100:.1f}%")
    print("\nDone. Now regenerate the snapshot: python data/export_snapshot.py")


if __name__ == "__main__":
    run()
