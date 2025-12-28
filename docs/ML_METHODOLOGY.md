# Machine Learning Methodology: Incoming Auction Bids Forecast

## Overview
The bot uses machine learning models to forecast **incoming auction demand** (incoming bids) for Indonesian government bonds (SBN). The models are trained and evaluated in `20251208_podem2026_sbn_v01.ipynb`.

## Data Source
- **File**: `20251207_db01.xlsx`
- **Sheet**: `train_sbn` (historical auction data)
- **Target Variable**: `incoming_bio_log` (log of incoming demand in billions IDR)

## Feature Engineering

### Input Features (6 selected features)
The model uses these macroeconomic and auction-specific features:

1. **number_series** - Which bond series (FR95-FR104)
2. **dpk_bio_log** - Bank deposits (log scale, billions IDR)
3. **move** - MOVE index (bond market volatility indicator)
4. **auction_month** - Month of auction (seasonal effect)
5. **long_holiday** - Binary flag for long holiday periods
6. **inflation_rate** - Current inflation rate

### Feature Selection Method
- **Stepwise Selection**: Forward selection with p-value threshold (α = 0.09)
- **Multicollinearity Test**: VIF (Variance Inflation Factor) analysis to ensure VIF < 10
- **Statistical Significance**: Only statistically significant features included

## Model Comparison

The notebook trains and compares **6 different models**:

| Model | Type | Status |
|-------|------|--------|
| **Random Forest** | Ensemble (Bagging) | ✓ Tuned |
| **Gradient Boosting** | Ensemble (Boosting) | ✓ Tuned |
| **AdaBoost** | Adaptive Boosting | ✓ Tuned |
| **Linear Regression** | Baseline (OLS) | ✓ Reference |
| **Lasso Regression** | Regularized Linear | Optional |
| **Deep Learning** | Neural Network (128-64 nodes) | ✓ Tested |

## Hyperparameter Tuning

### Random Forest Hyperparameters
```python
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [10, 20, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}
```

### AdaBoost Hyperparameters
```python
param_grid = {
    'n_estimators': [100, 150, 200],
    'learning_rate': [0.01, 0.05, 0.1, 0.2]
}
```

### Tuning Method
- **GridSearchCV**: Exhaustive search over parameter combinations
- **Cross-Validation**: 5-fold CV for robust evaluation
- **Metric**: R² Score (coefficient of determination)

## Data Processing Pipeline

1. **Data Loading**: 
   - Read from Excel sheet `train_sbn`
   - Extract features and target

2. **Train-Test Split**:
   - 80% training, 20% testing
   - Random state: 42 (reproducible)

3. **Feature Scaling**:
   - StandardScaler: Mean = 0, Std = 1
   - Applied to train data, then transformed on test data

4. **Model Training**:
   - Scikit-learn models on scaled features
   - Deep learning with Keras Sequential API

## Model Performance Evaluation

### Metrics
- **R² Score**: How well the model explains variance in incoming bids
- **Mean Squared Error (MSE)**: Average squared prediction error
- **Feature Importance**: Which features drive the predictions (via SHAP)

### Result Analysis
- Models compared across metrics
- Best performing model selected
- Residual analysis for diagnostic checks

## Forecast Generation

### Prediction Process
1. New macroeconomic data prepared for forecasting dates
2. Features scaled using fitted StandardScaler
3. All 6 trained models generate predictions
4. Results averaged or best model selected
5. Log predictions converted back to billions IDR (exp transformation)

### Output
**File**: `20251224_auction_forecast.csv`
- **incoming_billions**: Predicted incoming demand (billions IDR)
- **incoming_millions**: Same in millions
- **awarded_billions**: Predicted awarded amount
- **Number of forecasts**: Dec 2025 - Dec 2026 (monthly)

## Key Variables in Output

| Column | Description | Unit |
|--------|-------------|------|
| `date` | Auction date | YYYY-MM-DD |
| `auction_month` | Month (1-12) | Integer |
| `auction_year` | Year | Integer |
| `incoming_billions` | **Predicted incoming demand** | Billions IDR |
| `awarded_billions` | **Predicted awarded amount** | Billions IDR |
| `bid_to_cover` | Predicted bid-to-cover ratio | Ratio |
| `bi_rate` | BI Repo Rate | % |
| `yield05_ibpa` | 5-year yield | % |
| `yield10_ibpa` | 10-year yield | % |
| `inflation_rate` | Inflation forecast | % |

## How the Bot Uses These Forecasts

When you query `/kei auction demand January 2026`:

1. Bot reads `20251224_auction_forecast.csv`
2. Filters for January 2026 forecasts
3. Kei (LLM) analyzes the predicted demand and macro factors
4. Returns quantitative analysis with:
   - Predicted incoming bids (from ML model)
   - Confidence based on historical accuracy
   - Market context (yields, inflation, volatility)

## Model Accuracy Notes

- **R² on test set**: Typically 0.75-0.90 (depends on model)
- **Out-of-sample performance**: Tested on 20% holdout
- **Seasonal patterns**: Captured via `auction_month` feature
- **Economic shocks**: Limited to observed historical patterns

## Updating Forecasts

To regenerate forecasts with new data:

```bash
python3 export_auction_forecast.py
```

This:
1. Loads updated `20251207_db01.xlsx`
2. Extracts the latest predictions from notebook
3. Exports to `20251224_auction_forecast.csv`
4. Bot automatically uses updated data

---

**Research Date**: Dec 2025  
**Model Type**: Ensemble learning (Random Forest + Gradient Boosting)  
**Features**: Macroeconomic + Auction characteristics  
**Target**: Incoming auction demand (log-transformed)  
**Deployment**: Integrated with Telegram bot via CSV lookup
