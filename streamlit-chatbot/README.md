## Streamlit Chatbot: Bond Price & Yield Assistant

This Streamlit app provides a chat interface for querying Indonesian government bond prices, yields, and auction forecasts, with support for:

- **Economist-style table formatting** for historical and multi-tenor queries, making data easy to read and share.
- **Professional summary blocks** for statistics (min, max, average, std dev) in a concise, aligned style.
- **8 forecasting models**: ARIMA, ETS, RANDOM_WALK, MONTE_CARLO, MA5, VAR, PROPHET, GRU (LSTM removed).
- **Business-day horizons**: "Next N observations" automatically skip weekends.
- **Improved reliability**: ARIMA 3-level fallback, Prophet clamping, 3×MAD outlier filtering.
- **Telegram and web compatibility**: All outputs are formatted for optimal display in both Telegram and the Streamlit web UI.

### Example Table Output
```
Date         | 5 Year   | 10 Year  
-----------------------------------
2025-01-01   | 6.72%    | 7.10%    
2025-01-02   | 6.73%    | 7.11%    
...          | ...      | ...      
2025-01-31   | 7.02%    | 7.40%    
```

### Example Summary Block
```
Summary (Yield)
Records  :    23
Min      :   6.78%
Max      :   7.13%
Average  :   6.94%
Std Dev  :   0.11%
```

### Forecasting Models
- **8 models**: ARIMA (with 3-level fallback), ETS, RANDOM_WALK, MONTE_CARLO, MA5, VAR, PROPHET (clamped ≥0), GRU (deep learning)
- **LSTM**: Completely removed from codebase
- **Ensemble**: Excludes negatives and 3×MAD outliers for robust averaging
- **Business days**: T+N horizons skip weekends automatically using pandas business day calendar

For more details, see the main project README.md.
