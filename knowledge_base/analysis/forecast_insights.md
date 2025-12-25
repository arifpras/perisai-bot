
# Auction Demand Forecasting Rules

## Key Demand Drivers
1. **Yields vs alternatives**: Higher yields attract more demand
2. **Maturity structure**: New issues in short tenors (2-5Y) typically see higher demand
3. **Macro backdrop**: Risk-off environment → flight to safety → higher demand for long-dated bonds
4. **Seasonal patterns**: 
   - Q1: Higher demand (CNY effects, year-start portfolio rebalancing)
   - Q2: Moderate demand
   - Q3-Q4: Higher demand (year-end rebalancing, BI policy accommodation)

## Bid-to-Cover Thresholds
- **Strong demand**: BTC > 4.0x → Expect undersubscription unlikely
- **Normal demand**: BTC 3.0-4.0x → Auction likely to succeed
- **Weak demand**: BTC < 2.5x → Watch for acceptance rates, spread widening
- **Very weak**: BTC < 2.0x → Potential demand crisis signal

## ML Model Features (for your ensemble)
Primary drivers for auction forecast:
- Previous auction BTC ratio
- BI rate level and trend
- Inflation rate (YoY)
- Rupiah USD/IDR level
- Market volatility (VIX-like measure)
- Global yields (US 10Y TNX)
- Domestic credit spreads

## Accuracy Notes
- 1-month forward forecasts: ~75-80% accuracy
- 2-3 month forward: ~70-75% accuracy
- Beyond 3 months: Accuracy drops significantly, use with caution
