# Database Migration Summary

## Overview
Successfully organized all CSV and XLSX data files into a dedicated `database/` folder for improved project structure and maintainability.

## Files Moved
The following 5 data files have been moved from root to `database/` folder:

1. **auction_train.csv** (70 KB)
   - Historical auction data (2015-2024)
   - Contains 202 rows of auction records

2. **20251215_priceyield.csv** (99 KB)
   - Price and yield time series for Indonesian government bonds (INDOGB)
   - Contains FR-series data (FR95–FR104) with supported tenors

3. **20251224_auction_forecast.csv** (5 KB)
   - Auction forecast predictions for 2025-2026
   - Incoming forecast data only

4. **20251224_auction_forecast_ensemble.csv** (6 KB)
   - Weighted ensemble forecast combining multiple models
   - Alternative forecast dataset

5. **20251207_db01.xlsx** (2.5 MB)
   - Training and prediction data for ML models
   - Contains sheets: train_sbn, predict_sbn

## Code Changes

### Core Application Files

#### 1. **priceyield_20251223.py**
- Line 23: Updated `CSV_PATH_DEFAULT` to `"database/20251215_priceyield.csv"`

#### 2. **telegram_bot.py**
- Line 384: `get_db()` default parameter → `"database/20251215_priceyield.csv"`
- Line 390: `get_auction_db()` default parameter → `"database/20251224_auction_forecast.csv"`
- Line 401: Quarterly auction query → `'database/auction_train.csv'`
- Line 452: Monthly auction query → `'database/auction_train.csv'`
- Line 491: Yearly auction query → `'database/auction_train.csv'`
- Line 1025: Multi-year historical query → `'database/auction_train.csv'`

#### 3. **app_fastapi.py**
- Added constants for default CSV paths (referenced in dynamic imports)

#### 4. **.env.example**
- Line 13: Updated comment example → `"database/20251215_priceyield.csv"`

### Test Files

#### 5. **tests/test_auction_compare_forecast.py**
- Line 19: Test data loading → `'database/20251224_auction_forecast.csv'`

#### 6. **scripts/test_next5.py**
- Line 8: BondDB initialization → `'database/20251215_priceyield.csv'`

### Archived Scripts

#### 7. **scripts/archived/export_auction_forecast.py**
- Lines 53-54: Excel data loading → `'database/20251207_db01.xlsx'`
- Line 152: Output file path → `'database/20251224_auction_forecast.csv'`

#### 8. **scripts/archived/generate_weighted_ensemble.py**
- Lines 50-51: Excel data loading → `'database/20251207_db01.xlsx'`
- Line 129: Output file path → `'database/20251224_auction_forecast_ensemble.csv'`

#### 9. **scripts/archived/debug_multi_tenor.py**
- Line 13: Database initialization → `"database/20251215_priceyield.csv"`

#### 10. **scripts/archived/sanity_check.py**
- Lines 120, 189, 357-358: All data file path references updated to use `database/` prefix

#### 11. **scripts/archived/test_predeployment.py**
- Lines 130, 145: CSV path specifications → `'/workspaces/perisai-bot/database/20251215_priceyield.csv'`

## Verification

✅ All 5 data files successfully moved to `database/` folder
✅ All Python files compile without syntax errors
✅ AuctionDB successfully loads forecast CSV from new location
✅ Historical auction data successfully loads from new location
✅ All 11 code files updated with correct path references

## Impact

### No Breaking Changes
- All relative paths use `database/` prefix (works from project root)
- Default parameters in functions automatically point to new locations
- Backward compatibility maintained through environment variable fallback (if used)

### Benefits
- **Organization**: All data files in dedicated folder
- **Clarity**: Clear separation between code and data
- **Scalability**: Easier to add new datasets
- **Maintenance**: Simpler to manage data file lifecycle

## Deployment Notes

When deploying:
1. Ensure `database/` folder is included in deployment package
2. All 5 data files must be present in `database/` folder
3. No changes needed in environment configuration (relative paths work)
4. For Docker: Ensure COPY/ADD commands include `database/` folder

## Related Documentation

- See `README.md` for dataset descriptions
- See individual script docstrings for usage details
- All paths are relative to project root (`/workspaces/perisai-bot/`)
