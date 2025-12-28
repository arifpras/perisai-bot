# Plot Examples

These prompts render line charts (Plotly) in the chat. Examples mirror the `/kin plot ...` commands listed in the bot’s `/examples`.

Note: Plot rendering requires Plotly; in local CLI runs you may see a warning if Plotly is not available. In Telegram/Streamlit, plots render inline.

## Single Tenor — Monthly Window

Prompt:

/kin plot yield 5 year in Jan 2025

Expected: One line (5Y yield) over Jan 2025 trading days.

## Multi-Tenor — Range

Prompt:

/kin plot yield 5 and 10 year from Oct 2024 to Mar 2025

Expected: Two lines (5Y & 10Y yields) over the period.

## Price Plots

Prompt:

/kin plot price 5 year in Q3 2025

Expected: Price series for 5Y across Q3 2025.

## Tips
- Use `yield` or `price` with one or two tenors.
- Periods: month names/numbers, quarters (Q1–Q4), or years.
- Use `from X to Y` for ranges or `in X` for single periods.
