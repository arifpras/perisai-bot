# 2026 Auction Demand Forecasting - Quick Reference

## 📊 System Overview

**Purpose**: Monthly incoming bids (auction demand) forecast for 2026  
**Approach**: ML ensemble of 4 models (RF, GB, AdaBoost, Stepwise Regression)  
**Data**: Historical 186 auctions (2010-2025) from `auction_database.csv`  
**Output**: 12 monthly forecasts Jan-Dec 2026 in `auction_database.csv`  

## 🚀 Quick Start

### Method 1: Query from Unified Database

```python
import pandas as pd

# Load unified database (includes 2026 forecast)
df = pd.read_csv('database/auction_database.csv')

# Filter for 2026 forecast data
forecast_2026 = df[df['auction_year'] == 2026]

# Each month's incoming bids (ensemble mean)
for _, row in forecast_2026.iterrows():
    month = int(row['auction_month'])
    incoming = row['incoming_trillions']
    print(f"Month {month}: Rp {incoming:.2f} T")
```

### Method 2: Telegram Bot Integration

```python
from telegram_bot import get_2026_demand_forecast

forecast = get_2026_demand_forecast()  # Loads from auction_database.csv
print(f"Total: Rp {forecast['total_2026_incoming_billions']:,.0f} billion")

for month in forecast['monthly']:
    print(f"{month['month']}: {month['incoming_billions']:,.0f}B")
```

### Method 3: Run Test Script

```bash
cd /workspaces/perisai-bot
python auction_demand_forecast.py
```

## 📈 4-Model Ensemble

| # | Model | Type | 2026 Total (T) |
|----|-------|------|----------------|
| 1️⃣ | **Stepwise Regression** | Statistical Selection | **3,510.558 T** ⭐ Highest |
| 2️⃣ | **Gradient Boosting** | Sequential Ensemble | 3,442.524 T |
| 3️⃣ | **Random Forest** | Parallel Ensemble | 3,348.689 T |
| 4️⃣ | **AdaBoost** | Adaptive Boosting | 2,933.791 T |

**Final Prediction (Ensemble Average)**: **3,285.718 T** (Average of 4 models)

## 📊 Input Features (6)

| Feature | Example | Range | Role |
|---------|---------|-------|------|
| `number_series` | 15 | 1-52 | Auction frequency per year |
| `dpk_bio_log` | 5.2 | 4-6 | Deposits (log scale) |
| `move` | 75.5 | 50-100 | Bond duration/movement |
| `auction_month` | 1-12 | 1-12 | Seasonality (Q4 higher) |
| `long_holiday` | 0/1 | Binary | Holiday impact on liquidity |
| `inflation_rate` | 2.7 | 0-4 | Macro environment |

**Target**: `incoming_bio_log` (log10 of billions IDR)

## 🎯 Typical 2026 Forecast

```
Total Expected Incoming Bids:  3,285.718 Trillion IDR
Average Monthly:                273.810 Trillion IDR

Breakdown by Quarter:
Q1: 805.331 T (24.5%)  | Q2: 887.257 T (27.0%) 
Q3: 899.785 T (27.4%)  | Q4: 693.345 T (21.1%)

Monthly Range: 172.365 T (Dec) to 362.394 T (Feb)
```

*Note: Q3 shows peak demand, Q4 shows seasonal trough*

## 📁 File Structure

```
/workspaces/perisai-bot/
├── auction_demand_forecast.py      ← Core ML module
├── test_demand_forecast.py         ← Test script
├── AUCTION_DEMAND_FORECAST.md      ← Full documentation
├── models/                         ← Saved models (auto-created)
│   ├── demand_scaler.pkl
│   ├── demand_random_forest.pkl
│   ├── demand_gradient_boosting.pkl
│   ├── demand_adaboost.pkl
│   └── demand_stepwise_model.pkl
└── database/
    ├── auction_train.csv           ← 186 historical auctions (2010-2025)
    ├── auction_predict.csv         ← 12 months feature set for 2026
    └── auction_database.csv        ← Unified: historical + 2026 forecast (FINAL)
        └── incoming_trillions      ← 2026 months: ensemble mean forecast
```

## 🔄 Model Training

**Original training process** (already completed):
- Data source: `auction_train.csv` (186 historical records, 2010-2025)
- Models: Random Forest, Gradient Boosting, AdaBoost, Stepwise Regression
- R² scores: RF=0.7596, GB=0.7886✓, AdaBoost=0.7351, Stepwise=0.7884
- Ensemble: Simple mean of 4 model predictions
- Forecast period: Jan-Dec 2026 (12 months)

**Current workflow**:
- Forecast data: Stored in `auction_database.csv` (ready to use)
- No model training needed (data already generated)
- Simply query 2026 rows from `auction_database.csv`

## 📊 Interpreting Results

### 2026 Forecast Values
```python
incoming_trillions  # Rp Trillions (ensemble mean forecast for each month)
```

### Confidence Band
```python
ensemble_std_billions   # Uncertainty (std dev of 5 models)
# Low std (< 50B)  → High confidence (models agree)
# High std (> 200B) → Low confidence (divergent predictions)
```

### Feature Importance
Which variables most influence demand:
```
1. Auction Month       (Seasonality)
2. Inflation Rate      (Macro environment)
3. Deposits            (Investor liquidity)
4. Number of Series    (Auction frequency)
5. Bond Movement       (Duration impact)
6. Holiday Flag        (Liquidity constraints)
```

## ⚡ Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Train ensemble | 3-5 min | From scratch |
| Load models | 0.5 sec | From disk cache |
| Predict 12 months | 0.2 sec | Using loaded models |
| Retrain (cached) | 1 sec | Check models fresh |

## 🔧 Troubleshooting

### "Could not find Excel file"
```python
# Use unified database (2026 data already computed)
df = pd.read_csv('database/auction_database.csv')
forecast_2026 = df[df['auction_year'] == 2026]
```

### "How do I update 2026 forecast?"
```python
# Re-run auction_demand_forecast.py to regenerate all 2026 predictions
# This will overwrite auction_database.csv with new ensemble forecasts
python auction_demand_forecast.py
```

### "Can I see individual model predictions?"
```python
# Yes - auction_database.csv includes columns:
# - Random Forest (Rp T)
# - Gradient Boosting (Rp T)
# - AdaBoost (Rp T)
# - Stepwise Regression (Rp T)
# Plus incoming_trillions = ensemble mean
```

## 📚 Full Documentation

See [AUCTION_DEMAND_FORECAST.md](AUCTION_DEMAND_FORECAST.md) for:
- Architecture deep-dive
- Model specifications
- Data format specifications
- Feature engineering details
- Model interpretation
- Future enhancements

## 🎯 Key Improvements from Old System

| Aspect | Old (Excel sheets) | New (Unified DB) |
|--------|-------------------|------------------|
| Data source | 20251207_db01.xlsx | auction_database.csv |
| Historical records | 185 | 186 (2010-2025) |
| Forecast records | 12 (separate) | 12 (integrated into main DB) |
| Access method | Multi-step (train + predict) | Simple query (filter year==2026) |
| Unit consistency | Mixed (billions/log scale) | Unified (Rp Trillions) |
| Other columns | Excel sheets | Integrated (dates, BtC ratio, etc.) |

## ✅ Next Steps

1. **Verify data**: Check `auction_database.csv` has 198 rows (186+12)
2. **Query 2026**: Filter `auction_year==2026` to get 12 monthly forecasts
3. **Check values**: `incoming_trillions` = ensemble forecast for each month
4. **Update models**: Re-run `auction_demand_forecast.py` if needing fresh forecast
5. **Monitor**: Use bot `/kei analyze incoming` to fetch 2026 data

## 📞 Support

For questions on:
- **Usage**: See code comments in `auction_demand_forecast.py` and `telegram_bot.py`
- **Theory**: See notebook `20251208_podem2026_sbn_v01.ipynb`
- **Integration**: See `telegram_bot.py` function `get_2026_demand_forecast()`
- **Data**: Check `database/auction_database.csv` structure
