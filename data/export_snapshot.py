#!/usr/bin/env python
"""
data/export_snapshot.py
Generates static JSON data for Vercel deployment (no live backend needed).
Run from project root: python data/export_snapshot.py

Outputs
-------
frontend/src/data/snapshot.json           - 6 business dashboards (JS bundle)
frontend/src/data/portfolio-summary.json  - 507 portfolio summaries (JS bundle)
frontend/public/data/portfolio/*.json     - per-business detail files (on-demand fetch)
"""
import os, sys, json, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

OUT_SRC       = os.path.join(ROOT, "frontend", "src", "data")
OUT_PUBLIC    = os.path.join(ROOT, "frontend", "public", "data", "portfolio")
PORTFOLIO_DIR = os.path.join(ROOT, "data", "portfolio")

os.makedirs(OUT_SRC,    exist_ok=True)
os.makedirs(OUT_PUBLIC, exist_ok=True)

DEMO_BUSINESSES = ["cafe", "minimarket", "laundromat", "realestate", "cardealer", "motorbike"]

print("Loading models via Flask app context...")
from api.app import app  # triggers load_models() at module level

print("\nGenerating 6-business dashboard snapshot...")
snapshot = {}
with app.test_client() as client:
    for bid in DEMO_BUSINESSES:
        print(f"  {bid}...", end=" ", flush=True)

        dash_resp = client.get(f"/api/dashboard/{bid}")
        if dash_resp.status_code != 200:
            print(f"FAILED ({dash_resp.status_code})")
            sys.exit(1)
        dash = dash_resp.get_json()

        fore_resp = client.get(f"/api/{bid}/forecast")
        fore = fore_resp.get_json() if fore_resp.status_code == 200 else {}

        snapshot[bid] = {
            "business":            dash["business"],
            "summary":             dash["summary"],
            "dscr":                dash["dscr"],
            "fraud":               dash["fraud"],
            "classification":      dash.get("classification"),
            "forecast": {
                "summary": fore.get("summary", dash["forecast"]["summary"]),
                "series":  fore.get("series",  dash["forecast"]["series"]),
            },
            "recent_transactions": dash["recent_transactions"],
            "energy_trend":        dash["energy_trend"],
        }
        print("ok")

snap_path = os.path.join(OUT_SRC, "snapshot.json")
with open(snap_path, "w", encoding="utf-8") as f:
    json.dump(snapshot, f, separators=(",", ":"))
print(f"  => snapshot.json ({os.path.getsize(snap_path) // 1024} KB)\n")

print("Copying portfolio summary...")
src = os.path.join(PORTFOLIO_DIR, "portfolio_summary.json")
dst = os.path.join(OUT_SRC, "portfolio-summary.json")
shutil.copy2(src, dst)
print(f"  => portfolio-summary.json ({os.path.getsize(dst) // 1024} KB)\n")

print("Copying portfolio detail files...")
count = 0
for fn in sorted(os.listdir(PORTFOLIO_DIR)):
    if fn.endswith("_detail.json"):
        shutil.copy2(os.path.join(PORTFOLIO_DIR, fn), os.path.join(OUT_PUBLIC, fn))
        count += 1
total_kb = sum(
    os.path.getsize(os.path.join(OUT_PUBLIC, f)) for f in os.listdir(OUT_PUBLIC)
) // 1024
print(f"  => {count} detail files ({total_kb} KB total)\n")

print("All done. Run: cd frontend && npm run build")
