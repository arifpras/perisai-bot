#!/usr/bin/env python3
"""Debug multi-tenor data"""

import sys
sys.path.insert(0, '/workspaces/perisai-bot')

from datetime import date
from app_fastapi import get_db
import pandas as pd

print("🔍 Debugging multi-tenor data\n")

db = get_db("database/20251215_priceyield.csv")
start_date = date(2024, 1, 1)
end_date = date(2024, 12, 31)
metric = 'yield'
tenors = ['05_year', '10_year']

# Query data
params = [start_date.isoformat(), end_date.isoformat()]
where = 'obs_date BETWEEN ? AND ?'
tenor_placeholders = ', '.join('?' * len(tenors))
where += f' AND tenor IN ({tenor_placeholders})'
params.extend(tenors)

rows = db.con.execute(
    f'SELECT series, tenor, obs_date, price, "yield" FROM ts WHERE {where} ORDER BY obs_date ASC, series',
    params
).fetchall()

print(f"Total rows: {len(rows)}")

# Convert to dataframe
df = pd.DataFrame(rows, columns=['series', 'tenor', 'obs_date', 'price', 'yield'])
df['obs_date'] = pd.to_datetime(df['obs_date'])

print(f"\nUnique tenors: {df['tenor'].unique()}")
print(f"Tenor counts:\n{df['tenor'].value_counts()}")

# Process like in _plot_range_to_png
all_dates = pd.date_range(start_date, end_date, freq='D')
filled = []
for (s, t), g in df.groupby(['series', 'tenor']):
    g2 = g.set_index('obs_date').reindex(all_dates)
    g2['series'] = s
    g2['tenor'] = t
    g2[['price', 'yield']] = g2[['price', 'yield']].ffill()
    filled.append(g2.reset_index().rename(columns={'index': 'obs_date'}))

filled = pd.concat(filled, ignore_index=True)
daily = filled.groupby(['obs_date', 'tenor'])[metric].mean().reset_index()

print(f"\nDaily data shape: {daily.shape}")
print(f"Daily unique tenors: {daily['tenor'].unique()}")
print(f"\nFirst few rows:")
print(daily.head(10))
print(f"\nTenor value counts in daily:")
print(daily['tenor'].value_counts())
