import sys
from pathlib import Path
sys.path.append(str(Path('/workspaces/perisai-bot')))

from priceyield_20251223 import BondDB, forecast_tenor_next_days

def main():
    db = BondDB('database/20251215_priceyield.csv')
    res = forecast_tenor_next_days(db, '10_year', days=5, last_obs_count=5, series=None)

    print('Latest 5 observations:')
    for d, v in res.get('last_obs', []):
        print(f'{d}: {v:.4f}')

    print('\nForecasts:')
    for item in res.get('forecasts', []):
        label = item.get('label')
        date = item.get('date')
        avg = item.get('average')
        if isinstance(avg, float):
            print(f'{label} ({date}) average={avg:.4f}')
        else:
            print(f'{label} ({date}) average={avg}')
        models = item.get('models', {})
        for m in ['arima','ets','random_walk','monte_carlo','ma5','var','prophet','gru']:
            val = models.get(m)
            if isinstance(val, float):
                print(f'  {m}: {val:.6f}')
            else:
                print(f'  {m}: {val}')

if __name__ == '__main__':
    main()
