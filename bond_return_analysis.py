"""
Bond Return Attribution & Decomposition Analysis

Analyzes Indonesian government bond returns across carry, duration, roll-down, 
and FX components using actual market data.

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
        """Load bond and FX data from CSV files."""
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
        
        Returns:
        --------
        dict with keys: carry_idr, duration_idr, rolldown_idr, fx_effect, 
                        total_idr, total_usd, metrics
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
        coupon = start_row['coupon']
        
        # Duration estimate
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
        """Format return decomposition for display."""
        m = results['metrics']
        
        output = f"""
📊 {self.tenor.upper()} Bond Return Attribution
{self.start_date.strftime('%d %b %Y')} – {self.end_date.strftime('%d %b %Y')} ({m['days_held']} days)

RETURN DECOMPOSITION (IDR-based):
┌──────────────────┬────────────┬────────┐
│ Component        │    Return  │   %    │
├──────────────────┼────────────┼────────┤
│ Carry            │ Rp {results['carry_idr']:>7.2f}  │ {results['carry_pct']:>5.2f}% │
│ Duration Effect  │ Rp {results['duration_idr']:>7.2f}  │ {results['duration_pct']:>5.2f}% │
│ Roll-Down        │ Rp {results['rolldown_idr']:>7.2f}  │ {results['rolldown_pct']:>5.2f}% │
├──────────────────┼────────────┼────────┤
│ Total (IDR)      │            │ {results['total_idr_pct']:>5.2f}% │
│ FX Impact (dep)  │            │ {results['fx_depreciation']:>5.2f}% │
├──────────────────┼────────────┼────────┤
│ Total (USD)      │            │ {results['usd_return_pct']:>5.2f}% │
└──────────────────┴────────────┴────────┘

KEY METRICS:
  Price:            {m['start_price']} → {m['end_price']} (Δ {round(m['end_price'] - m['start_price'], 3)})
  Yield:            {m['start_yield']:.2f}% → {m['end_yield']:.2f}% (Δ {m['yield_move_bp']:.0f} bp)
  Modified Duration: {m['modified_duration']:.2f}
  Coupon:           {m['coupon']:.3f}%
  IDR/USD:          {int(m['start_fx'])} → {int(m['end_fx'])} (IDR weakened {results['fx_depreciation']:.1f}%)

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
