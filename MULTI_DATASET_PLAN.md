# Multi-Dataset Architecture Plan

## Current System (Single Dataset)
- **Data Source:** `20251215_priceyield.csv` (bonds only)
- **Structure:** date, series, tenor, price, yield
- **Query Format:** `yield 5 year june 2025` → auto-parsed
- **Intent Parser:** `20251223_priceyield.py` with hardcoded bond logic
- **Database:** DuckDB table `ts` with fixed schema
- **Metrics:** price, yield only
- **Tenors:** 05_year, 10_year

---

## Proposed Multi-Dataset System

### 1. **Three Datasets**

| Dataset | Columns | Metrics | Time Grouping | Key Identifiers |
|---------|---------|---------|---|---|
| **bonds** | date, series, tenor, price, yield, coupon | price, yield | date, tenor, series | series, tenor |
| **macro** | date, indicator, value | inflation, gdp_growth, unemployment, rate | date only | indicator name |
| **behavior** | date, series, buyer_type, volume, holding_period, transactions | volume, holding_period, transactions | date, series | series, buyer_type |

### 2. **Dataset Registry Configuration**

**New file: `datasets.json`** (or Python dict)
```json
{
  "bonds": {
    "file": "20251215_priceyield.csv",
    "table": "bonds_ts",
    "date_column": "date",
    "date_format": "%d/%m/%Y",
    "columns": {
      "date": "DATE",
      "series": "VARCHAR",
      "tenor": "VARCHAR",
      "price": "FLOAT",
      "yield": "FLOAT",
      "coupon": "FLOAT"
    },
    "metrics": ["price", "yield"],
    "dimensions": ["series", "tenor"],
    "valid_tenors": ["05_year", "10_year"],
    "valid_series": ["FR95", "FR100", "FR101", "FR103", "FR104", "FR96"],
    "aggregatable": true
  },
  
  "macro": {
    "file": "macroeconomic_indicators.csv",
    "table": "macro_ts",
    "date_column": "date",
    "date_format": "%Y-%m-%d",
    "columns": {
      "date": "DATE",
      "inflation": "FLOAT",
      "gdp_growth": "FLOAT",
      "unemployment": "FLOAT",
      "rate": "FLOAT"
    },
    "metrics": ["inflation", "gdp_growth", "unemployment", "rate"],
    "dimensions": [],
    "valid_values": null,
    "aggregatable": true
  },
  
  "behavior": {
    "file": "bondholder_behavior.csv",
    "table": "behavior_ts",
    "date_column": "date",
    "date_format": "%d/%m/%Y",
    "columns": {
      "date": "DATE",
      "series": "VARCHAR",
      "buyer_type": "VARCHAR",
      "volume": "FLOAT",
      "holding_period": "FLOAT",
      "transactions": "INTEGER"
    },
    "metrics": ["volume", "holding_period", "transactions"],
    "dimensions": ["series", "buyer_type"],
    "valid_buyer_types": ["domestic_bank", "foreign", "central_bank", "insurance"],
    "aggregatable": true
  }
}
```

---

## Architecture Changes

### A. **Intent Parser Enhancement** (`20251223_priceyield.py`)

**Current:**
```python
class Intent:
    type: str  # POINT, RANGE, AGG_RANGE, PLOT
    point_date: Optional[date]
    start_date: Optional[date]
    end_date: Optional[date]
    metric: str  # "price", "yield"
    agg: Optional[str]  # "min", "max", "avg", "stdev"
    series: Optional[str]  # "FR95", "FR103"
    tenor: Optional[str]  # "05_year", "10_year"
```

**Proposed:**
```python
class Intent:
    dataset: str  # "bonds", "macro", "behavior" ← NEW
    type: str
    point_date: Optional[date]
    start_date: Optional[date]
    end_date: Optional[date]
    metric: str
    agg: Optional[str]
    series: Optional[str]
    tenor: Optional[str]
    buyer_type: Optional[str]  # NEW (for behavior dataset)
    indicator: Optional[str]  # NEW (for macro dataset)
```

**Changes:**
1. Add dataset prefix parsing: `bonds: yield...` or `macro: inflation...`
2. Route to dataset-specific parser logic
3. Validate metric/dimension against dataset registry
4. Return enhanced Intent with dataset name

---

### B. **Database Layer** (`20251223_priceyield.py` → `datasets_manager.py`)

**Current Architecture:**
```
BondDB
├── load_data() → DuckDB
├── get_ts() → SQL query
└── aggregate() → compute stats
```

**Proposed Architecture:**
```
DatasetManager (singleton)
├── registry: Dict[dataset_name, DatasetConfig]
├── con: DuckDB connection
├── load_all_datasets()
│   ├── for each dataset:
│   │   ├── read CSV with correct date_format
│   │   ├── create table with schema from registry
│   │   └── validate data
├── get_dataset(name) → DatasetConfig
├── query(dataset, sql_params) → execute on correct table
└── aggregate(dataset, metric, ...) → dataset-aware stats
```

**New class: `DatasetConfig`**
```python
@dataclass
class DatasetConfig:
    name: str
    file: str
    table: str
    date_column: str
    date_format: str
    columns: Dict[str, str]
    metrics: List[str]
    dimensions: List[str]
    valid_values: Dict[str, List[str]]  # for validation
    aggregatable: bool
    
    def validate_metric(self, metric: str) -> bool
    def validate_dimension(self, dim: str, value: str) -> bool
    def get_table_name(self) -> str
```

---

### C. **Query Routing** (`telegram_bot.py` changes)

**Current flow:**
```
user query → parse_intent() → BondDB.get_ts() → format → reply
```

**Proposed flow:**
```
user query 
  → extract dataset prefix (bonds:, macro:, behavior:)
  → parse_intent(dataset) 
  → DatasetManager.query(dataset, ...)
  → dataset-specific formatting
  → reply
```

**Where to change:**
1. **`handle_message()` (line ~313)**
   - Before: calls `parse_intent(text)` directly
   - After: extract dataset prefix, route to correct parser
   
2. **`ask_admin_command()` (line ~163)**
   - Before: calls `db.aggregate()` assuming bonds
   - After: `DatasetManager.get_dataset(dataset).aggregate(...)`

3. **`generate_plot()` (line ~510)**
   - Before: hardcoded bonds visualization
   - After: dataset-aware plot formatting (macro might be line chart, behavior stacked bar, etc.)

---

## Implementation Phases

### **Phase 1: Setup (1-2 hours)**
- [ ] Create `datasets.json` with registry
- [ ] Create `datasets_manager.py` with `DatasetManager` class
- [ ] Create tables in DuckDB for all three datasets
- [ ] Create sample test files (or use placeholder data)
- **Commit:** `feat: add dataset registry and DatasetManager skeleton`

### **Phase 2: Intent Parser (2-3 hours)**
- [ ] Enhance `Intent` dataclass with `dataset` field
- [ ] Update `parse_intent()` to extract dataset prefix
- [ ] Add dataset-specific parsing logic (tenor for bonds, indicator for macro, buyer_type for behavior)
- [ ] Add validation against registry
- **Commit:** `feat: enhance intent parser for multi-dataset support`

### **Phase 3: Database Queries (1-2 hours)**
- [ ] Implement `DatasetManager.query(dataset, sql_template, params)`
- [ ] Refactor `BondDB` methods to use DatasetManager
- [ ] Update `aggregate()` to be dataset-aware
- [ ] Test queries for all three datasets
- **Commit:** `refactor: centralize database access via DatasetManager`

### **Phase 4: Telegram Bot Updates (2-3 hours)**
- [ ] Update `handle_message()` with dataset prefix extraction
- [ ] Update `ask_admin_command()` to handle multi-dataset data summaries
- [ ] Update `generate_plot()` with dataset-aware formatting
- [ ] Update `/examples` to show all three datasets with sample queries
- **Commit:** `feat: enable multi-dataset support in telegram handlers`

### **Phase 5: Testing & Documentation (1-2 hours)**
- [ ] Test queries for each dataset separately
- [ ] Test mixed queries (bonds + macro context)
- [ ] Test /ask_admin with each dataset
- [ ] Test plot generation for each dataset type
- [ ] Update README with multi-dataset instructions
- **Commit:** `test: add multi-dataset test cases and update docs`

**Total: ~9-12 hours of development**

---

## Files to Create/Modify

### **New Files:**
1. `datasets.json` — Registry configuration
2. `datasets_manager.py` — `DatasetManager` class (~200 lines)

### **Modify Existing:**
1. `20251223_priceyield.py` — Add `Intent.dataset`, enhance parser (~100 line changes)
2. `telegram_bot.py` — Dataset routing in handlers (~150 line changes)
   - `handle_message()`
   - `ask_admin_command()`
   - `generate_plot()`
   - `/examples` handler
3. `app_fastapi.py` — Optional: Dataset metadata endpoint for frontend
4. `README.md` — Document multi-dataset usage

---

## Query Examples (Post-Implementation)

### **Current (bonds only):**
```
yield 5 year june 2025
avg yield 10 year 2024
plot price 5 year Q2 2025
```

### **New (multi-dataset):**
```
bonds: yield 5 year june 2025
macro: inflation rate 2024
behavior: volume FR103 june 2025
bonds: avg yield 10 year 2024
macro: avg inflation rate Q1 2025
behavior: transactions FR95 domestic_bank 2024

/ask_admin bonds: compare yield trend vs macro: inflation 2024-2025
```

---

## Error Handling Strategy

**Invalid dataset:**
```
❌ Unknown dataset 'stocks'. Available: bonds, macro, behavior
Use: bonds: <query>, macro: <query>, behavior: <query>
```

**Invalid metric for dataset:**
```
❌ Dataset 'macro' has no metric 'price'
Available metrics: inflation, gdp_growth, unemployment, rate
```

**Invalid dimension:**
```
❌ Dataset 'macro' has no dimension 'series'
Available dimensions: none (macro is time-series only)
```

**Missing required file:**
```
⚠️ Dataset 'behavior' requires file: bondholder_behavior.csv
Please add the file and restart the bot
```

---

## Database Schema

### **bonds_ts table**
```sql
CREATE TABLE bonds_ts (
    obs_date DATE,
    series VARCHAR,
    tenor VARCHAR,
    price FLOAT,
    yield FLOAT,
    coupon FLOAT
);
```

### **macro_ts table**
```sql
CREATE TABLE macro_ts (
    obs_date DATE,
    inflation FLOAT,
    gdp_growth FLOAT,
    unemployment FLOAT,
    rate FLOAT
);
```

### **behavior_ts table**
```sql
CREATE TABLE behavior_ts (
    obs_date DATE,
    series VARCHAR,
    buyer_type VARCHAR,
    volume FLOAT,
    holding_period FLOAT,
    transactions INTEGER
);
```

---

## Questions to Resolve

1. **Data availability:** Do you have the macroeconomic and behavior CSV files ready? If not, should I create sample/mock data?

2. **Query precedence:** If user asks `/ask_admin compare bonds and macro`, should the system:
   - Query both datasets and present side-by-side?
   - Have GPT correlate them?
   - Currently only support single-dataset queries per /ask_admin call?
   → **Recommendation:** Start with single-dataset per query, add cross-dataset later if needed

3. **Time alignment:** Should macro (might be monthly) and behavior (might be daily) align with bonds (daily)?
   → **Recommendation:** Each dataset maintains its own date granularity; no forced alignment

4. **Plot types:**
   - Bonds: Line chart (time series with highlighting) ✓ (current)
   - Macro: Line chart (multiple indicators) or bar chart?
   - Behavior: Stacked bar? Pie chart? Area chart?
   → **Recommendation:** Start with line charts for all; customize later

5. **Access control:** Should all users have access to all datasets, or restrict by dataset?
   → **Recommendation:** Unified ALLOWED_USER_IDS for now; add per-dataset ACL later if needed

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| CSV files missing | Create sample/mock data files first |
| Date parsing breaks | Validate date_format in registry, test each format |
| Query performance | Index obs_date and key dimensions in each table |
| Backward compatibility | Support old query format (auto-default to bonds) |
| LLM confusion | Keep /ask_admin dataset prefix explicit, test with GPT |
| Test coverage gaps | Write integration tests for each dataset query type |

---

## Success Criteria

- ✅ Three datasets load without errors at startup
- ✅ Single-dataset queries work for all three datasets
- ✅ /ask_admin returns correct data summaries per dataset
- ✅ /examples shows sample queries for all three datasets
- ✅ Statistics (min/max/avg/stdev) compute correctly per metric/dataset
- ✅ Plot generation works for each dataset
- ✅ Invalid queries produce clear error messages
- ✅ Deployment to Render succeeds with new code

---

## Next Steps

1. **If proceeding:** Do you have the CSV files for macro and behavior datasets? If not, should I create mock data?
2. **Scope confirmation:** Confirm the three datasets and their structures match my assumptions
3. **Start Phase 1:** Create registry and DatasetManager
4. **Iterate through phases** with testing at each step

---

