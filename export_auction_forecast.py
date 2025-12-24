#!/usr/bin/env python3
"""
Export auction forecasts from Excel to CSV for bot integration
"""

import pandas as pd
import numpy as np

# Load prediction data
df = pd.read_excel('20251207_db01.xlsx', sheet_name='predict_sbn')

# Select key columns for bot queries
columns_to_export = [
    'date',
    'auction_month',
    'auction_year',
    'bi_rate',
    'yield01_ibpa',
    'yield05_ibpa',
    'yield10_ibpa',
    'inflation_rate',
    'idprod_rate',
    'jkse_avg',
    'idrusd_avg',
    'incoming_bio_log',  # Target: predicted incoming demand (log)
    'awarded_bio_log',   # Predicted awarded amount (log)
    'incoming_mio_log',  # In millions (log)
    'awarded_mio_log',
    'number_series',
    'bid_to_cover',
    'move',              # MOVE index volatility
    'forh_avg',          # Foreign holdings
    'dpk_bio_log',       # Bank deposits
]

df_export = df[columns_to_export].copy()

# Add human-readable values (inverse log transform)
df_export['incoming_billions'] = np.exp(df['incoming_bio_log'])
df_export['awarded_billions'] = np.exp(df['awarded_bio_log'])
df_export['incoming_millions'] = np.exp(df['incoming_mio_log'])
df_export['awarded_millions'] = np.exp(df['awarded_mio_log'])

# Format date
df_export['date'] = pd.to_datetime(df_export['date']).dt.strftime('%Y-%m-%d')

# Save to CSV
output_file = '20251224_auction_forecast.csv'
df_export.to_csv(output_file, index=False)

print(f"✓ Exported {len(df_export)} forecasts to {output_file}")
print(f"  Date range: {df_export['date'].min()} to {df_export['date'].max()}")
print(f"  Columns: {len(df_export.columns)}")
