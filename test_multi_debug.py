#!/usr/bin/env python3
"""Generate multi-tenor plot with debug output"""

import sys
sys.path.insert(0, '/workspaces/perisai-bot')

from datetime import date
import pandas as pd
import matplotlib.pyplot as plt
from app_fastapi import get_db, ECONOMIST_PALETTE, apply_economist_style

print("🎨 Generating multi-tenor plot with debug output\n")

db = get_db("20251215_priceyield.csv")
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

df = pd.DataFrame(rows, columns=['series', 'tenor', 'obs_date', 'price', 'yield'])
df['obs_date'] = pd.to_datetime(df['obs_date'])

# Process data
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

print(f"Data prepared:")
print(f"  Unique tenors: {list(daily['tenor'].unique())}")
print(f"  Data points per tenor: {daily.groupby('tenor').size().to_dict()}")

# Plot
fig, ax = plt.subplots(figsize=(10, 6))
apply_economist_style(fig, ax)

print(f"\nPlotting lines:")
for idx, tenor_val in enumerate(sorted(daily['tenor'].unique())):
    tenor_data = daily[daily['tenor'] == tenor_val]
    tenor_label = tenor_val.replace('_', ' ').replace('05 ', '5 ').replace('10 ', '10 ')
    color = ECONOMIST_PALETTE[idx % len(ECONOMIST_PALETTE)]
    
    print(f"  Line {idx+1}: {tenor_label}")
    print(f"    Color: {color}")
    print(f"    Data points: {len(tenor_data)}")
    print(f"    Y-range: {tenor_data[metric].min():.2f} - {tenor_data[metric].max():.2f}")
    
    ax.plot(tenor_data['obs_date'], tenor_data[metric], 
           linewidth=2.5, label=tenor_label, color=color)

ax.legend(frameon=False, fontsize=10, loc='best', labelcolor='#696969')
ax.set_title(f'Yield 5 year, 10 year\n1 Jan 2024 to 31 Dec 2024', pad=15, loc='left')
ax.set_xlabel('')
ax.set_ylabel('Yield (%)', fontsize=9)

from matplotlib.dates import DateFormatter
date_formatter = DateFormatter('%-d %b\n%Y')
ax.xaxis.set_major_formatter(date_formatter)
fig.autofmt_xdate(rotation=0, ha='center')

fig.tight_layout()
fig.savefig('test_plot_multi_debug.png', format='png', dpi=150, facecolor='white')
plt.close(fig)

print(f"\n✅ Generated: test_plot_multi_debug.png")
