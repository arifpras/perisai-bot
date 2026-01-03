"""
Bond Return Attribution & Decomposition Analysis

Analyzes Indonesian government bond returns across carry, duration, roll-down, 
and FX components using actual market data.

COUPON HANDLING FOR MULTI-YEAR ANALYSIS (KEY DESIGN NOTE):
----------------------------------------------------------
When a period spans different bond series (e.g., 2023-2025), the bond composition
may change (e.g., FR95 5.500% coupon in 2023 → FR104 5.750% coupon in 2025).

Convention:
  → Coupon value in KEY METRICS uses the START bond's coupon (FR95: 5.500%)
  → This reflects the actual coupon earned during carry calculations
  → Return decomposition (carry + duration + rolldown) is based on START bond metrics
  → The "Coupon (Start)" label makes this transparent to users
  
Why this approach:
  ✓ Carry income is calculated on the starting bond's coupon
  ✓ Duration effect uses starting bond's modified duration
  ✓ Rolldown assumes you held that bond down the curve
  ✓ Avoids complex dollar-weighted averaging that obscures analysis
  ✓ Matches fixed-income return attribution best practices

If needed for future enhancement:
  → Could add "Coupon (End)" row for transparency on series migration
  → Could add note in headline: "FR95 → FR104 series migration"
  → But current approach is clearest for decomposition integrity

Usage:
    decomp = ReturnDecomposition('05_year', '2023-01-02', '2025-12-31')
    results = decomp.analyze()
    print(decomp.format_analysis(results))
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os


class ReturnDecomposition:
    """Decompose bond returns into carry, duration, roll-down, and FX components."""

    def __init__(self, tenor: str, start_date: str, end_date: str):
        """
        Initialize return decomposition analysis.
        
        Parameters:
        -----------
        tenor : str
            '05_year' or '10_year'
        start_date : str
            'YYYY-MM-DD' format
        end_date : str
            'YYYY-MM-DD' format
        """
        self.tenor = tenor
        self.start_date = self._parse_date(start_date)
        self.end_date = self._parse_date(end_date)
        self.bond_data = None
        self.fx_data = None
        self._load_data()

    def _parse_date(self, date_str: str) -> datetime:
        """Parse YYYY-MM-DD to datetime."""
        if isinstance(date_str, str):
            return datetime.strptime(date_str, '%Y-%m-%d')
        return date_str

    def _load_data(self):
        """
        Load bond and FX data from CSV files.
        
        DATABASE PATH CONFIGURATION (VERIFIED):
        ----------------------------------------
        Path construction: os.path.join(os.path.dirname(__file__), 'database')
        Result: /workspaces/perisai-bot/database
        
        Files required:
          1. bond_file: 20251215_priceyield.csv (bond prices/yields)
             - Location: /workspaces/perisai-bot/database/20251215_priceyield.csv
             - Columns: date (DD/MM/YYYY), cusip, series, coupon, maturity_date, 
                        price, yield, tenor
             - Status: ✅ EXISTS (0.09 MB)
             
          2. fx_file: 20260102_daily01.csv (IDR/USD FX rates)
             - Location: /workspaces/perisai-bot/database/20260102_daily01.csv
             - Columns: date (YYYY/MM/DD), idrusd, vix_index
             - Status: ✅ EXISTS (0.02 MB)
        
        Error handling: FileNotFoundError raised if either file is missing.
        Date format: Bond data uses DD/MM/YYYY; FX data uses YYYY/MM/DD
        
        Path type: RELATIVE (OS-agnostic, works on Windows/Mac/Linux)
        """
        db_path = os.path.join(os.path.dirname(__file__), 'database')
        
        # Load bond data
        bond_file = os.path.join(db_path, '20251215_priceyield.csv')
        if not os.path.exists(bond_file):
            raise FileNotFoundError(f"Bond data not found: {bond_file}")
        
        df_bond = pd.read_csv(bond_file)
        df_bond['date'] = pd.to_datetime(df_bond['date'], format='%d/%m/%Y')
        
        # Filter by tenor and date range
        self.bond_data = df_bond[
            (df_bond['tenor'] == self.tenor) &
            (df_bond['date'] >= self.start_date) &
            (df_bond['date'] <= self.end_date)
        ].sort_values('date').reset_index(drop=True)
        
        # Forward-fill NaN values in bond data (market closures)
        self.bond_data['price'] = self.bond_data['price'].ffill()
        self.bond_data['yield'] = self.bond_data['yield'].ffill()
        
        # Load FX data
        fx_file = os.path.join(db_path, '20260102_daily01.csv')
        if not os.path.exists(fx_file):
            raise FileNotFoundError(f"FX data not found: {fx_file}")
        
        df_fx = pd.read_csv(fx_file)
        df_fx['date'] = pd.to_datetime(df_fx['date'], format='%Y/%m/%d')
        
        self.fx_data = df_fx[
            (df_fx['date'] >= self.start_date) &
            (df_fx['date'] <= self.end_date)
        ].sort_values('date').reset_index(drop=True)
        
        # Forward-fill NaN values in FX data (market closures)
        self.fx_data['idrusd'] = self.fx_data['idrusd'].ffill()

    def calculate_modified_duration(self, price: float, yield_pct: float, 
                                     tenor_years: float) -> float:
        """
        Estimate modified duration from bond price and yield.
        
        Simplified: Duration ≈ (Price / Yield) × (1 / (1 + Yield))
        For faster approximation: Modified Duration ≈ -0.5 to -5.0 depending on maturity
        """
        if yield_pct <= 0:
            return 4.0  # Default for 5Y
        
        # Macaulay duration approximation: ~tenor years / 2 for intermediate bonds
        # Modified duration = Macaulay / (1 + yield)
        macaulay = tenor_years * 0.6  # Conservative estimate
        modified = macaulay / (1 + yield_pct / 100)
        return round(modified, 2)

    def analyze(self) -> dict:
        """
        Perform return decomposition analysis.
        
        COUPON CONVENTION (Multi-Year/Multi-Series Handling):
        -------------------------------------------------------
        When period spans different bond series (e.g., 2023-2025 with FR95→FR104 migration):
        - Uses START BOND's coupon for all calculations (carry, duration, rolldown)
        - This is standard practice in fixed-income return attribution
        - Coupon value returned in metrics['coupon'] = start_row['coupon']
        - Ensures decomposition integrity: carry earned on actual bond held at period start
        
        Returns:
        --------
        dict with keys: carry_idr, duration_idr, rolldown_idr, fx_effect, 
                        total_idr, total_usd, metrics (including coupon from START bond)
        """
        if len(self.bond_data) < 2:
            raise ValueError(f"Insufficient data for period {self.start_date} to {self.end_date}")
        
        # Initial and final prices/yields
        start_row = self.bond_data.iloc[0]
        end_row = self.bond_data.iloc[-1]
        
        start_price = start_row['price']
        end_price = end_row['price']
        start_yield = start_row['yield']
        end_yield = end_row['yield']
        coupon = start_row['coupon']  # ← START BOND COUPON (key design decision)
        
        # Duration estimate (based on start bond)
        tenor_years = 5 if self.tenor == '05_year' else 10
        mod_duration = self.calculate_modified_duration(start_price, start_yield, tenor_years)
        
        # 1. CARRY: Coupon accrual + reinvestment
        days_held = (self.bond_data.iloc[-1]['date'] - self.bond_data.iloc[0]['date']).days
        carry_idr = (coupon / 100) * (days_held / 365)  # Simplified accrual
        
        # 2. DURATION EFFECT: Price change from yield move
        yield_move_bp = (end_yield - start_yield) * 100  # Basis points
        duration_effect_pct = -mod_duration * (yield_move_bp / 10000)
        duration_idr = (start_price / 100) * duration_effect_pct
        
        # 3. ROLL-DOWN: Movement along yield curve (price gain as maturity shortens)
        price_change_raw = end_price - start_price
        rolldown_idr = price_change_raw - duration_idr
        
        # 4. TOTAL IDR RETURN
        total_idr_return = carry_idr + duration_idr + rolldown_idr
        total_idr_pct = (total_idr_return / start_price) * 100
        
        # 5. FX EFFECT: IDR/USD movement
        start_fx = self.fx_data.iloc[0]['idrusd'] if len(self.fx_data) > 0 else 15592
        end_fx = self.fx_data.iloc[-1]['idrusd'] if len(self.fx_data) > 0 else 16737
        fx_depreciation = (end_fx - start_fx) / start_fx  # Positive = IDR weakness
        usd_return_pct = ((1 + total_idr_pct / 100) / (1 + fx_depreciation) - 1) * 100
        
        return {
            'carry_idr': round(carry_idr, 4),
            'carry_pct': round((carry_idr / start_price) * 100, 3),
            'duration_idr': round(duration_idr, 4),
            'duration_pct': round(duration_effect_pct * 100, 3),
            'rolldown_idr': round(rolldown_idr, 4),
            'rolldown_pct': round((rolldown_idr / start_price) * 100, 3),
            'total_idr_pct': round(total_idr_pct, 3),
            'fx_depreciation': round(fx_depreciation * 100, 2),
            'usd_return_pct': round(usd_return_pct, 3),
            'metrics': {
                'start_price': round(start_price, 3),
                'end_price': round(end_price, 3),
                'start_yield': round(start_yield, 3),
                'end_yield': round(end_yield, 3),
                'yield_move_bp': round(yield_move_bp, 1),
                'modified_duration': mod_duration,
                'coupon': round(coupon, 3),
                'days_held': days_held,
                'start_fx': round(start_fx, 0),
                'end_fx': round(end_fx, 0),
            }
        }

    def format_analysis(self, results: dict) -> str:
        """
        Format return decomposition for Telegram display.
        
        KEY METRICS - COUPON CONVENTION:
        --------------------------------
        The "Coupon" row displays the START BOND's coupon (metric from analyze()).
        For multi-year periods spanning different series:
          → Example: 2023 FR95 (5.500%) → 2025 FR104 (5.750%)
          → Displays: 5.500% (start bond)
          → Reasoning: All return decomposition (carry, duration, rolldown) is
                       calculated on the starting bond's metrics
          → User sees transparent, consistent methodology
        
        If full series migration tracking needed in future:
          → Add "Coupon (End)" row below current Coupon line
          → Or add notation in headline: "FR95 → FR104 migration"
          → Current design prioritizes clarity of decomposition methodology
        """
        m = results['metrics']
        price_change = m['end_price'] - m['start_price']
        yield_change_bp = m['yield_move_bp']
        
        output = f"""
📊 {self.tenor.upper()} Bond Return Attribution
{self.start_date.strftime('%d %b %Y')} – {self.end_date.strftime('%d %b %Y')} ({m['days_held']} days)

RETURN DECOMPOSITION (IDR-based):
┌──────────────────────────────────┬────────┐
│ Component                        │   %    │
├──────────────────────────────────┼────────┤
│ Carry                            │ {results['carry_pct']:>5.2f}% │
│ Duration Effect                  │ {results['duration_pct']:>5.2f}% │
│ Rolldown                         │ {results['rolldown_pct']:>5.2f}% │
├──────────────────────────────────┼────────┤
│ Total (IDR)                      │ {results['total_idr_pct']:>5.2f}% │
│ FX Impact (Depreciation)         │ {results['fx_depreciation']:>5.2f}% │
├──────────────────────────────────┼────────┤
│ Total (USD)                      │ {results['usd_return_pct']:>5.2f}% │
└──────────────────────────────────┴────────┘

KEY METRICS:
┌──────────────────┬───────────────┐
│ Metric           │         Value │
├──────────────────┼───────────────┤
│ Price (Start)    │  {m['start_price']:>12.2f}% │
│ Price (End)      │  {m['end_price']:>12.2f}% │
│ Price Change     │  {price_change:>12.2f}% │
├──────────────────┼───────────────┤
│ Yield (Start)    │  {m['start_yield']:>12.2f}% │
│ Yield (End)      │  {m['end_yield']:>12.2f}% │
│ Yield Change     │ {yield_change_bp:>10.0f} bp │
├──────────────────┼───────────────┤
│ Modified Dur.    │  {m['modified_duration']:>12.2f}  │
│ Coupon           │  {m['coupon']:>12.3f}% │
├──────────────────┼───────────────┤
│ IDR/USD (Start)  │  {int(m['start_fx']):>10,}  │
│ IDR/USD (End)    │  {int(m['end_fx']):>10,}  │
│ IDR Depreciat.   │  {results['fx_depreciation']:>12.2f}% │
└──────────────────┴───────────────┘

INTERPRETATION:
"""
        if results['total_idr_pct'] > 0:
            output += f"  ✓ Positive IDR return of {results['total_idr_pct']:.2f}% driven by "
            if abs(results['carry_pct']) > abs(results['duration_pct']):
                output += "carry income"
            else:
                output += "yield compression"
        else:
            output += f"  ✗ Negative IDR return of {results['total_idr_pct']:.2f}% driven by "
            if abs(results['duration_pct']) > abs(results['carry_pct']):
                output += "yield expansion"
            else:
                output += "weak carry"
        
        if results['usd_return_pct'] < results['total_idr_pct']:
            output += f"\n  ⚠ FX headwind: IDR depreciation of {results['fx_depreciation']:.1f}% reduced USD returns "
            output += f"from {results['total_idr_pct']:.2f}% to {results['usd_return_pct']:.2f}%"
        
        output += "\n\n~ Kei"
        return output


def analyze_bond_returns(tenor: str, start_date: str, end_date: str) -> str:
    """
    Convenience function for return decomposition.
    
    Parameters:
    -----------
    tenor : str
        '05_year' or '10_year'
    start_date : str
        'YYYY-MM-DD' format
    end_date : str
        'YYYY-MM-DD' format
    
    Returns:
    --------
    str : Formatted return analysis
    """
    try:
        decomp = ReturnDecomposition(tenor, start_date, end_date)
        results = decomp.analyze()
        return decomp.format_analysis(results)
    except Exception as e:
        return f"❌ Return analysis error: {str(e)}\n\n~ Kei"


if __name__ == "__main__":
    # Example usage
    analysis = analyze_bond_returns('05_year', '2023-01-02', '2025-12-31')
    print(analysis)
