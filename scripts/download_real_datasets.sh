#!/usr/bin/env bash
# download_real_datasets.sh
# Re-downloads the raw validation datasets used in models/real_data_validation.py.
# These files are excluded from git (data/real/ is in .gitignore) because two of
# them exceed GitHub's 100MB per-file hard limit:
#   real_cardealer_auto_sales.csv  ~224 MB
#   real_retail_general.csv        ~162 MB
#
# Usage:
#   bash scripts/download_real_datasets.sh
#
# Requirements:
#   pip install kaggle          (for Kaggle downloads)
#   kaggle.json in ~/.kaggle/   (API credentials from kaggle.com/settings)

set -e
DATA_DIR="$(cd "$(dirname "$0")/.." && pwd)/data/real"
mkdir -p "$DATA_DIR"
cd "$DATA_DIR"

echo "=== Downloading DataCore real validation datasets ==="
echo "Destination: $DATA_DIR"
echo ""

# ── 1. Coffee Shop Sales (Kaggle, ~14 MB) ────────────────────────────────────
# Source: https://www.kaggle.com/datasets/ahmedabbas757/coffee-sales
# Output: real_cafe_coffee_shop.csv
echo "[1/5] Coffee Shop Sales (~14 MB)..."
kaggle datasets download -d ahmedabbas757/coffee-sales --unzip -p "$DATA_DIR" 2>/dev/null || \
  echo "  SKIP: set up kaggle.json credentials first (see README in data/real/)"

# ── 2. Supermarket Sales (Kaggle, ~137 KB) ───────────────────────────────────
# Source: https://www.kaggle.com/datasets/aungpyaeap/supermarket-sales
# Output: real_minimarket_supermarket.csv
echo "[2/5] Supermarket Sales (~137 KB)..."
kaggle datasets download -d aungpyaeap/supermarket-sales --unzip -p "$DATA_DIR" 2>/dev/null || \
  echo "  SKIP"

# ── 3. General Retail / UCI Online Retail II (UCI ML Repo, ~162 MB) ──────────
# Source: https://archive.ics.uci.edu/dataset/502/online+retail+ii
# Output: real_retail_general.csv
# This file is too large for direct curl on some connections; download manually.
echo "[3/5] UCI Online Retail II (~162 MB) — download manually if curl fails..."
curl -L --retry 3 -o "real_retail_general.zip" \
  "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip" 2>/dev/null && \
  unzip -o real_retail_general.zip "*.csv" && \
  mv *.csv real_retail_general.csv && rm -f real_retail_general.zip || \
  echo "  SKIP: download from https://archive.ics.uci.edu/dataset/502/online+retail+ii"

# ── 4. Car Dealer / Auto Sales (Kaggle, ~224 MB) ─────────────────────────────
# Source: https://www.kaggle.com/datasets/syedanwarafridi/vehicle-sales-data
# Output: real_cardealer_auto_sales.csv
echo "[4/5] Vehicle Sales Data (~224 MB)..."
kaggle datasets download -d syedanwarafridi/vehicle-sales-data --unzip -p "$DATA_DIR" 2>/dev/null || \
  echo "  SKIP"

# ── 5. Real Estate Transactions (Kaggle) ─────────────────────────────────────
# Source: https://www.kaggle.com/datasets/hm-land-registry/uk-housing-prices-paid
# OR: data was a local file (real_realestate_property.csv, ~899 KB)
# Small enough to re-add to git if needed.
echo "[5/5] Real Estate Transactions (~899 KB) — small enough to commit directly."

echo ""
echo "=== Done. Verify with: ls -lh data/real/ ==="
echo ""
echo "NOTE: After downloading, run the validation suite:"
echo "  python models/real_data_validation.py"
