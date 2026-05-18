# DataCore — iz Business AI Lending Engine

> Alinma Bank Hackathon 2025 — SME & Incubator lending powered by real-time POS + energy data.

## Overview

DataCore is a dual-pipeline AI credit assessment system built for Saudi SMEs. It ingests 30-day POS transaction data and energy consumption logs to compute real-time creditworthiness — replacing static loan applications with live behavioral signals.

## Architecture

```
POS + Energy CSVs  →  AI Engine (4 models)  →  Flask REST API  →  React Dashboard
```

### Two Lending Pipelines

| Pipeline | Target | Method |
|----------|--------|--------|
| **SME Pipeline** | Existing businesses with live POS data | DSCR + Fraud Detection + Revenue Forecast |
| **Incubator Pipeline** | New entrepreneurs, salary-backed | DBR (Debt Burden Ratio) + graduation criteria |

## AI Models

| # | Model | Algorithm | Output |
|---|-------|-----------|--------|
| 1 | Business Classifier | HDBSCAN (12 archetypes, 150 samples/cluster) | Behavioral archetype |
| 2 | Expense Estimator | Zero-label behavioral tags (ticket × velocity) | Expense ratio breakdown |
| 3 | Fraud Detector | Isolation Forest (1st-percentile threshold) | Anomaly incidents + fraud score |
| 4 | Revenue Forecaster | Prophet + Saudi weekly seasonality (Thu/Fri) | 30-day forecast + dynamic credit limit |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask 3, Pandas, NumPy |
| ML / AI | scikit-learn, HDBSCAN, Prophet, Joblib |
| Frontend | React 19, Vite 6, Tailwind CSS v4, Recharts |
| Data | 6 synthetic Saudi SME datasets (June 2025, 30 days) |

## Businesses

| ID | Name | Sector |
|----|------|--------|
| `cafe` | Qahwa Corner Cafe | Food & Beverage |
| `minimarket` | Baraka Minimarket | Retail |
| `laundromat` | Al Noor Laundromat | Services |
| `realestate` | Majd Real Estate Office | Real Estate |
| `cardealer` | Rawabi Auto Gallery | Automotive |
| `motorbike` | Saqr Motorbikes | Automotive |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/businesses` | List all registered businesses |
| `GET /api/<id>/summary` | 30-day revenue & energy summary |
| `GET /api/<id>/dscr` | Full DSCR + credit limit assessment |
| `GET /api/<id>/fraud-check` | Isolation Forest fraud report |
| `GET /api/<id>/forecast` | Prophet revenue forecast series |
| `GET /api/dashboard/<id>` | Combined dashboard feed (single call) |
| `GET /api/incubator/dbr-assessment` | DBR calculator (salary + loan params) |
| `GET /api/incubator/business-profile` | Intake form → archetype + expense estimate |
| `GET /api/incubator/transition-check/<id>` | SME graduation readiness check |

## Running Locally

### Backend

```bash
cd Project_DataCore
pip install -r requirements.txt
python models/train_all.py       # train & save all 4 models
python api/app.py                # Flask API on :5000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                      # Vite dev server on :5173
```

## Key Features

- **Real-time DSCR** — Annualised NOI vs debt service from raw POS data
- **Dynamic Credit Limits** — Forecast-adjusted: growing trend +25%, declining −20%
- **Sustainability Discount** — 0.5–1.0% interest rate reduction for green energy days
- **Fraud Detection** — 3 typed anomaly checks (off-hours, amount outlier, revenue spike)
- **Bilingual UI** — English / Arabic with full RTL layout (Tajawal font)
- **Incubator Program** — Salary-backed seed loans with graduation criteria to SME pipeline
- **Mobile-first** — Responsive design with bottom navigation on mobile
