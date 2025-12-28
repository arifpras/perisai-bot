# Quick Reference: Bond Table & Plot Queries

## Command Syntax

### `/kei tab` - Bond Data Tables
```
/kei tab [METRIC] [TENOR(S)] [PERIOD]
```

**Metrics:**
- `yield` – Bond yield (%)
- `price` – Bond price
- `yield and price` – Both metrics

**Tenors:**
- Single: `5 year`, `10 year`
- Multiple: `5 and 10 year`

**Periods:**
- Single month: `in feb 2025` (any month name)
- Single quarter: `in q2 2025` (q1, q2, q3, q4)
- Single year: `in 2025`
- Month range: `from oct 2024 to mar 2025`
- Quarter range: `from q2 2024 to q1 2025`
- Year range: `from 2023 to 2024`

### `/kin plot` - Bond Plots
```
/kin plot [METRIC] [TENOR(S)] [PERIOD]
```

Same syntax as `/kei tab` but generates a professional plot instead of a table.

---

## Examples by Category

### Single Month Tables
```
/kei tab yield 5 year in feb 2025
/kei tab price 10 year in q1 2025
```

### Single Year Tables
```
/kei tab yield 5 year in 2025
/kei tab price 5 and 10 year in 2024
```

### Month Range Tables
```
/kei tab yield 5 and 10 year from oct 2024 to mar 2025
/kei tab price 5 year from jan 2025 to apr 2025
```

### Quarter Range Tables
```
/kei tab yield 5 and 10 year from q3 2023 to q2 2024
/kei tab price 5 year from q1 2025 to q3 2025
```

### Year Range Tables
```
/kei tab yield 5 and 10 year from 2023 to 2024
/kei tab price 5 and 10 year from 2023 to 2025
```

### Multi-Metric Tables
```
/kei tab yield and price 5 year in apr 2023
/kei tab yield and price 5 and 10 year in q2 2025
/kei tab yield and price 5 year from oct 2024 to mar 2025
```

### Single Month Plots
```
/kin plot yield 5 year in jan 2025
/kin plot price 10 year in q3 2025
```

### Multi-Tenor Plots
```
/kin plot yield 5 and 10 year from jan 2025 to mar 2025
/kin plot price 5 and 10 year from q2 2024 to q1 2025
```

### Year Range Plots
```
/kin plot yield 5 and 10 year from 2023 to 2024
/kin plot price 5 year from 2024 to 2025
```

---

## Month Names

Short form: `jan`, `feb`, `mar`, `apr`, `may`, `jun`, `jul`, `aug`, `sep`, `oct`, `nov`, `dec`

Long form: `january`, `february`, `march`, `april`, `may`, `june`, `july`, `august`, `september`, `october`, `november`, `december`

---

## Quarters

| Quarter | Months          | Example      |
|---------|-----------------|--------------|
| Q1      | Jan – Mar       | `in q1 2025` |
| Q2      | Apr – Jun       | `in q2 2025` |
| Q3      | Jul – Sep       | `in q3 2025` |
| Q4      | Oct – Dec       | `in q4 2025` |

---

## Table Output Format

```
┌──────────────────────────────────────────────────┐
│ Date         | Yield (%)  | Price           │
├──────────────────────────────────────────────────┤
│ 01 Feb 2025  |      4.25  | 102.35          │
│ 02 Feb 2025  |      4.27  | 102.28          │
│ 03 Feb 2025  |      4.24  | 102.42          │
│ ...          |       ...  | ...             │
└──────────────────────────────────────────────────┘
```

---

## Plot Output Format

Professional Economist-style chart showing:
- Time series lines (one per tenor)
- Color-coded tenors
- Grid styling
- Date and metric labels
- Proper scaling

---

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| ❌ No bond data found | Period not in database | Try recent dates (2024-2025) |
| Invalid query | Wrong syntax | Check metric, tenor, period format |
| Parse error | Malformed input | Use space-separated values |

---

## Tips & Tricks

1. **Flexible month names:** Both `jan` and `january` work
2. **Tenor formats:** `5 year`, `10year` (both work due to flexible parsing)
3. **Range shortcuts:** `from 2023 to 2024` is shorter than month ranges
4. **Compare periods:** Generate separate queries and compare tables manually
5. **Multi-metric insight:** Use `yield and price` to see correlation visually

---

## Related Commands

- `/kei yield X year [DATE]` – Point-in-time bond data
- `/kei auction demand [YEAR]` – Auction forecasts
- `/kin what is [TOPIC]` – Economic context
- `/check [DATE] [TENOR]` – Quick lookup
- `/examples` – More query examples
