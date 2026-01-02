"""
Yield Forecast Models: ARIMA, ETS, Prophet, GRU
"""
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from prophet import Prophet

# --- Helper: business-day step count ---
def _bdays_between(last_date, target_date):
    last = pd.to_datetime(last_date).date()
    target = pd.to_datetime(target_date).date()
    steps = np.busday_count(last, target)
    return steps

# --- Helper: ensure business-day frequency with LOCF ---
def _ensure_business_freq(series: pd.Series) -> pd.Series:
    s = series.copy()
    # Ensure datetime index
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    # Regularize to business-day frequency, forward-fill gaps
    try:
        s = s.asfreq('B', method='pad')
    except Exception:
        # Fallback: leave as-is if frequency cannot be enforced
        pass
    return s

# --- ARIMA ---
def forecast_arima(series, forecast_date, order=(1,1,1)):
    # Prefer business-day step counting for horizon alignment
    series = _ensure_business_freq(series)
    model = ARIMA(series, order=order)
    fit = model.fit()
    # Ensure both dates are pandas.Timestamp for subtraction
    last_date = series.index[-1]
    if not isinstance(last_date, pd.Timestamp):
        last_date = pd.to_datetime(last_date)
    target_date = pd.to_datetime(forecast_date)
    steps = max(_bdays_between(last_date, target_date), 1)
    try:
        pred = fit.get_forecast(steps=steps)
        forecast = pred.predicted_mean.iloc[-1]
        conf_int = pred.conf_int().iloc[-1]
        return float(forecast), tuple(conf_int)
    except Exception:
        try:
            # Fallback to simple forecast array if date alignment fails
            fc = fit.forecast(steps=steps)
            if isinstance(fc, (pd.Series, pd.DataFrame)):
                val = fc.iloc[-1]
                if hasattr(val, "item"):
                    val = val.item()
            else:
                val = float(fc[-1])
            return float(val), (np.nan, np.nan)
        except Exception:
            # Last resort: use last observed value
            return float(series.iloc[-1]), (np.nan, np.nan)

# --- ETS ---
def forecast_ets(series, forecast_date, seasonal=None):
    series = _ensure_business_freq(series)
    model = ExponentialSmoothing(series, trend='add', seasonal=seasonal, seasonal_periods=12)
    fit = model.fit()
    last_date = series.index[-1]
    if not isinstance(last_date, pd.Timestamp):
        last_date = pd.to_datetime(last_date)
    target_date = pd.to_datetime(forecast_date)
    steps = max(_bdays_between(last_date, target_date), 1)
    # Use positional indexing to avoid deprecated label-based behavior
    forecast = fit.forecast(steps).iloc[-1]
    return float(forecast)

# --- Prophet ---
def forecast_prophet(series, forecast_date):
    df = pd.DataFrame({'ds': series.index, 'y': series.values})
    m = Prophet()
    m.fit(df)
    future = pd.DataFrame({'ds': [forecast_date]})
    forecast = m.predict(future)
    yhat = forecast['yhat'].iloc[0]
    # Clamp to zero to avoid negative yield forecasts from Prophet noise
    return float(max(yhat, 0.0))

# --- Random Walk with Drift ---
def forecast_random_walk(series, forecast_date):
    """Random walk with drift component calculated from ALL observations.
    
    Formula: forecast = last_value * (1 + drift)^steps
    Drift = average daily change across all observations
    """
    if len(series) < 2:
        return float(series.iloc[-1])
    
    # Calculate drift from ALL observations
    changes = series.pct_change().dropna()
    if changes.empty:
        return float(series.iloc[-1])
    
    # Drift = average percentage change per period
    drift = changes.mean()
    last_val = series.iloc[-1]
    
    # Steps to forecast date
    steps = max((pd.to_datetime(forecast_date) - series.index[-1]).days, 1)
    
    # Apply drift: forecast = last_value * (1 + drift)^steps
    forecast = last_val * ((1 + drift) ** steps)
    
    # Clamp to reasonable range (avoid extreme negative yields)
    return float(max(forecast, 0.0))

# --- Monte Carlo (random walk with historical drift + volatility) ---
def forecast_monte_carlo(series, forecast_date, sims=500, seed=42):
    """Monte Carlo simulation using ALL historical returns for drift and volatility.
    
    Method:
    1. Calculate drift from ALL observations (long-term trend)
    2. Calculate volatility from ALL observations (risk measure)
    3. Run 500 simulations of random walks with both drift and stochastic shocks
    4. Return mean of final values
    """
    import random
    np.random.seed(seed)
    random.seed(seed)
    
    if len(series) < 2:
        return float(series.iloc[-1])
    
    # Calculate returns from ALL observations
    returns = series.pct_change().dropna()
    if returns.empty:
        return float(series.iloc[-1])
    
    # Drift and volatility from ALL observations
    mu = returns.mean()      # Average return (long-term trend)
    sigma = returns.std(ddof=0)  # Volatility (uncertainty)
    last_val = series.iloc[-1]
    
    # Calculate steps to forecast date
    steps = max((pd.to_datetime(forecast_date) - series.index[-1]).days, 1)
    
    # Run simulations using ALL historical information
    finals = []
    for _ in range(sims):
        # Random shocks with drift included
        shocks = np.random.normal(mu, sigma, steps)
        # Path = last_value * product(1 + each_shock)
        path = last_val * np.prod(1 + shocks)
        finals.append(path)
    
    # Return mean forecast, clamped to avoid negative yields
    mean_forecast = float(np.mean(finals))
    return max(mean_forecast, 0.0)

# --- 5-day Moving Average ---
def forecast_ma5(series, forecast_date):
    if len(series) < 5:
        return float(series.iloc[-1])
    return float(series.tail(5).mean())

# --- VAR (yield with its lag) ---
def forecast_var(series, forecast_date, lags=1):
    from statsmodels.tsa.api import VAR
    series = _ensure_business_freq(series)
    df = pd.DataFrame({"y": series})
    df["y_lag"] = df["y"].shift(1)
    df = df.dropna()
    if len(df) < 10:
        return float(series.iloc[-1])
    model = VAR(df)
    fit = model.fit(maxlags=lags)
    # Business-day horizon
    steps = _bdays_between(series.index[-1], pd.to_datetime(forecast_date))
    steps = max(steps, 1)
    # We forecast steps days ahead; take last forecasted y
    fc = fit.forecast(df.values[-fit.k_ar:], steps=steps)
    return float(fc[-1][0])

# --- GRU (only deep learning model) ---
def forecast_gru(series, forecast_date, epochs=20):
    # Set random seed for reproducibility
    import random
    import tensorflow as tf
    np.random.seed(42)
    random.seed(42)
    tf.random.set_seed(42)
    # Prepare data
    data = series.values.reshape(-1, 1)
    X, y = [], []
    for i in range(len(data)-1):
        X.append(data[i])
        y.append(data[i+1])
    X = np.array(X)
    y = np.array(y)
    X = X.reshape((X.shape[0], 1, X.shape[1]))
    # Build model with explicit Input to avoid warnings
    model = Sequential()
    model.add(Input(shape=(X.shape[1], X.shape[2])))
    model.add(GRU(32))
    model.add(Dense(1))
    model.compile(loss='mse', optimizer='adam')
    model.fit(X, y, epochs=epochs, verbose=0)
    # Forecast
    last = data[-1].reshape((1, 1, 1))
    forecast = model.predict(last)[0][0]
    return float(forecast)
