"""
Yield Forecast Models: ARIMA, ETS, Prophet, LSTM, GRU
"""
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from prophet import Prophet
from keras.models import Sequential
from keras.layers import LSTM, GRU, Dense
import torch

# --- ARIMA ---
def forecast_arima(series, forecast_date, order=(1,1,1)):
    model = ARIMA(series, order=order)
    fit = model.fit()
    # Ensure both dates are pandas.Timestamp for subtraction
    last_date = series.index[-1]
    if not isinstance(last_date, pd.Timestamp):
        last_date = pd.to_datetime(last_date)
    target_date = pd.to_datetime(forecast_date)
    steps = (target_date - last_date).days
    if steps < 1:
        raise ValueError("Target forecast date must be after last date in series.")
    pred = fit.get_forecast(steps=steps)
    forecast = pred.predicted_mean.iloc[-1]
    conf_int = pred.conf_int().iloc[-1]
    return float(forecast), tuple(conf_int)

# --- ETS ---
def forecast_ets(series, forecast_date, seasonal=None):
    model = ExponentialSmoothing(series, trend='add', seasonal=seasonal, seasonal_periods=12)
    fit = model.fit()
    last_date = series.index[-1]
    if not isinstance(last_date, pd.Timestamp):
        last_date = pd.to_datetime(last_date)
    target_date = pd.to_datetime(forecast_date)
    steps = (target_date - last_date).days
    if steps < 1:
        raise ValueError("Target forecast date must be after last date in series.")
    forecast = fit.forecast(steps)[-1]
    return float(forecast)

# --- Prophet ---
def forecast_prophet(series, forecast_date):
    df = pd.DataFrame({'ds': series.index, 'y': series.values})
    m = Prophet()
    m.fit(df)
    future = pd.DataFrame({'ds': [forecast_date]})
    forecast = m.predict(future)
    yhat = forecast['yhat'].iloc[0]
    return float(yhat)

# --- LSTM ---
def forecast_lstm(series, forecast_date, epochs=20):
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
    # Build model
    model = Sequential()
    model.add(LSTM(32, input_shape=(X.shape[1], X.shape[2])))
    model.add(Dense(1))
    model.compile(loss='mse', optimizer='adam')
    model.fit(X, y, epochs=epochs, verbose=0)
    # Forecast
    last = data[-1].reshape((1, 1, 1))
    forecast = model.predict(last)[0][0]
    return float(forecast)

# --- GRU ---
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
    # Build model
    model = Sequential()
    model.add(GRU(32, input_shape=(X.shape[1], X.shape[2])))
    model.add(Dense(1))
    model.compile(loss='mse', optimizer='adam')
    model.fit(X, y, epochs=epochs, verbose=0)
    # Forecast
    last = data[-1].reshape((1, 1, 1))
    forecast = model.predict(last)[0][0]
    return float(forecast)
