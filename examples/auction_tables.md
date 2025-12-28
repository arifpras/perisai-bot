# Auction Tables (Economist-style)

Real outputs rendered by the bot for common auction queries. Tables show totals in Rp Trillions (T). If `Awarded` is unavailable for a period, it is shown as `-`.

## Incoming Bid — Single Month

Prompt:

/kei tab incoming bid in May 2025

Output:

```
┌────────────────────────────────┐
│ Period         | Incoming      │
├────────────────────────────────┤
│ May 2025       |     Rp 241.30T│
└────────────────────────────────┘
```

## Awarded Bid — Two Months

Prompt:

/kei tab awarded bid in Apr 2025 and Jun 2025

Output:

```
┌────────────────────────────────┐
│ Period         | Awarded       │
├────────────────────────────────┤
│ Apr 2025       |              -│
│ Jun 2025       |              -│
└────────────────────────────────┘
```

Note: Awarded totals may be unavailable in forecast-only months.

## Incoming and Awarded — Two Quarters

Prompt:

/kei tab incoming and awarded bid from Q2 2025 to Q3 2025

Output:

```
┌─────────────────────────────────────────────────┐
│ Period         | Incoming       | Awarded       │
├─────────────────────────────────────────────────┤
│ Q2 2025        |     Rp 622.41T |              -│
│ Q3 2025        |   Rp 1,110.33T |              -│
└─────────────────────────────────────────────────┘
```

Tips:
- Use month names or numbers, quarters (Q1–Q4), or years.
- Combine metrics: `incoming and awarded`.
- Compare periods with `in X and Y` or `from X to Y`.
