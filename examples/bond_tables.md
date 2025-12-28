# Bond Tables (Economist-style)

Below are real outputs rendered by the bot for common table queries. Numeric columns are right-aligned, with summary statistics (Count/Min/Max/Avg/Std).

## Single Tenor, Multi-Metric (Monthly)

Prompt:

/kei tab yield and price 5 year Feb 2025

Output:

```
┌───────────────────────────────────────┐
│ Date         |      Yield |      Price│
├───────────────────────────────────────┤
│ 03 Feb 2025  |       6.88 |      98.31│
│ 04 Feb 2025  |       6.79 |      98.69│
│ 05 Feb 2025  |       6.72 |      99.02│
│ 06 Feb 2025  |       6.68 |      99.19│
│ 07 Feb 2025  |       6.62 |      99.45│
│ 10 Feb 2025  |       6.60 |      99.55│
│ 11 Feb 2025  |       6.59 |      99.59│
│ 12 Feb 2025  |       6.60 |      99.53│
│ 13 Feb 2025  |       6.61 |      99.49│
│ 14 Feb 2025  |       6.55 |      99.78│
│ 17 Feb 2025  |       6.53 |      99.84│
│ 18 Feb 2025  |       6.51 |      99.94│
│ 19 Feb 2025  |       6.55 |      99.75│
│ 20 Feb 2025  |       6.52 |      99.89│
│ 21 Feb 2025  |       6.51 |      99.92│
│ 24 Feb 2025  |       6.53 |      99.85│
│ 25 Feb 2025  |       6.64 |      99.37│
│ 26 Feb 2025  |       6.65 |      99.32│
│ 27 Feb 2025  |       6.74 |      98.93│
│ 28 Feb 2025  |       6.73 |      98.97│
├───────────────────────────────────────┤
│ Count        |         20 |         20│
│ Min          |       6.51 |      98.31│
│ Max          |       6.88 |      99.94│
│ Avg          |       6.63 |      99.42│
│ Std          |       0.10 |       0.45│
└───────────────────────────────────────┘
```

## Multi-Tenor, Single Metric (Quarter-to-Quarter)

Prompt:

/kei tab yield 5 and 10 year from q3 2023 to q2 2024

Output (head + summary shown):

```
┌───────────────────────────────────────┐
│ Date         |    05 year |    10 year│
├───────────────────────────────────────┤
│ 03 Jul 2023  |       5.86 |       6.22│
│ 04 Jul 2023  |       5.87 |       6.19│
│ 05 Jul 2023  |       5.87 |       6.16│
│ 06 Jul 2023  |       5.88 |       6.18│
│ 07 Jul 2023  |       5.94 |       6.23│
│ ...          |        ... |        ...│
│ 28 Jun 2024  |       6.93 |       7.04│
├───────────────────────────────────────┤
│ Count        |        260 |        260│
│ Min          |       5.83 |       6.16│
│ Max          |       7.13 |       7.22│
│ Avg          |       6.54 |       6.69│
│ Std          |       0.32 |       0.26│
└───────────────────────────────────────┘
```

## Multi-Tenor, Single Metric (Month-to-Month)

Prompt:

/kei tab yield 5 and 10 year from oct 2023 to mar 2024

Output (head + summary shown):

```
┌───────────────────────────────────────┐
│ Date         |    05 year |    10 year│
├───────────────────────────────────────┤
│ 02 Oct 2023  |       6.60 |       6.97│
│ 03 Oct 2023  |       6.70 |       7.00│
│ 04 Oct 2023  |       6.85 |       7.08│
│ 05 Oct 2023  |       6.82 |       7.02│
│ 06 Oct 2023  |       6.76 |       6.99│
│ ...          |        ... |        ...│
│ 29 Mar 2024  |       6.58 |       6.69│
├───────────────────────────────────────┤
│ Count        |        130 |        130│
│ Min          |       6.40 |       6.45│
│ Max          |       7.12 |       7.22│
│ Avg          |       6.59 |       6.70│
│ Std          |       0.16 |       0.18│
└───────────────────────────────────────┘
```

## Prices Across Tenors (Month Range)

Prompt:

/kei tab price 5 and 10 year from apr 2023 to feb 2024

Output (head + summary shown):

```
┌───────────────────────────────────────┐
│ Date         |    05 year |    10 year│
├───────────────────────────────────────┤
│ 03 Apr 2023  |     100.13 |     101.72│
│ 04 Apr 2023  |     100.22 |     102.08│
│ 05 Apr 2023  |     100.23 |     102.29│
│ 06 Apr 2023  |     100.26 |     102.50│
│ 07 Apr 2023  |     100.26 |     102.50│
│ ...          |        ... |        ...│
│ 29 Feb 2024  |     100.47 |     103.09│
├───────────────────────────────────────┤
│ Count        |        239 |        239│
│ Min          |      96.99 |      98.50│
│ Max          |     102.38 |     106.03│
│ Avg          |     100.57 |     102.64│
│ Std          |       1.34 |       2.05│
└───────────────────────────────────────┘
```

## Prices Across Tenors (Quarter-to-Quarter)

Prompt:

/kei tab price 5 and 10 year from q3 2023 to q2 2024

Output (head + summary shown):

```
┌───────────────────────────────────────┐
│ Date         |    05 year |    10 year│
├───────────────────────────────────────┤
│ 03 Jul 2023  |     102.23 |     105.56│
│ 04 Jul 2023  |     102.21 |     105.81│
│ 05 Jul 2023  |     102.19 |     106.02│
│ 06 Jul 2023  |     102.13 |     105.85│
│ 07 Jul 2023  |     101.88 |     105.50│
│ ...          |        ... |        ...│
│ 28 Jun 2024  |       6.93 |       7.04│
├───────────────────────────────────────┤
│ Count        |        260 |        260│
│ Min          |      96.99 |      95.87│
│ Max          |     102.38 |     106.03│
│ Avg          |     100.37 |     100.88│
│ Std          |       1.28 |       2.61│
└───────────────────────────────────────┘
```

Notes:
- Parser accepts single-period queries without explicit "in" (e.g., "/kei tab yield and price 5 year Feb 2025").
- Tables keep right-edge borders aligned, with fixed-width columns.
- Missing values display as "-"; stats skip missing entries.
