"""
Multi-Variable Bond & Macroeconomic Plots

Create professional plots showing bond prices/yields alongside FX and/or VIX 
for contextual macroeconomic analysis with Economist-style formatting.

Usage:
    plotter = BondMacroPlotter('10_year', '2023-01-02', '2025-12-31', metric='price')
    fig = plotter.plot_with_fx_vix()
    plotter.save_and_return_image('output.png')
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, date
import os
from io import BytesIO
from utils.economist_style import ECONOMIST_COLORS, apply_economist_style, add_economist_caption


class BondMacroPlotter:
    """Create multi-variable plots: bond prices/yields + FX/VIX with Economist styling."""
    
    # Indonesia public holidays 2023-2026 (when bond markets are closed)
    INDONESIA_HOLIDAYS = {
        date(2023, 1, 1), date(2023, 1, 22), date(2023, 2, 18), date(2023, 3, 22),
        date(2023, 4, 7), date(2023, 4, 22), date(2023, 4, 23), date(2023, 5, 1),
        date(2023, 5, 18), date(2023, 6, 1), date(2023, 6, 4), date(2023, 6, 29),
        date(2023, 7, 19), date(2023, 8, 17), date(2023, 9, 28), date(2023, 12, 25),
        date(2023, 1, 23), date(2023, 3, 23), date(2023, 4, 21), date(2023, 4, 24),
        date(2023, 4, 25), date(2023, 4, 26), date(2023, 6, 2), date(2023, 12, 26),
        date(2024, 1, 1), date(2024, 2, 8), date(2024, 2, 10), date(2024, 3, 11),
        date(2024, 3, 29), date(2024, 3, 31), date(2024, 4, 10), date(2024, 4, 11),
        date(2024, 5, 1), date(2024, 5, 9), date(2024, 5, 23), date(2024, 6, 1),
        date(2024, 6, 17), date(2024, 7, 7), date(2024, 8, 17), date(2024, 9, 16),
        date(2024, 12, 25), date(2024, 2, 9), date(2024, 3, 12), date(2024, 4, 8),
        date(2024, 4, 9), date(2024, 4, 12), date(2024, 4, 15), date(2024, 5, 10),
        date(2024, 5, 24), date(2024, 6, 18), date(2024, 12, 26),
        date(2025, 1, 1), date(2025, 1, 27), date(2025, 1, 29), date(2025, 3, 29),
        date(2025, 3, 31), date(2025, 4, 1), date(2025, 4, 18), date(2025, 4, 20),
        date(2025, 5, 1), date(2025, 5, 12), date(2025, 5, 29), date(2025, 6, 1),
        date(2025, 6, 6), date(2025, 6, 27), date(2025, 8, 17), date(2025, 9, 5),
        date(2025, 12, 25), date(2025, 1, 28), date(2025, 3, 28), date(2025, 4, 2),
        date(2025, 4, 3), date(2025, 5, 2), date(2025, 5, 13), date(2025, 5, 30),
        date(2025, 6, 2), date(2025, 6, 7), date(2025, 6, 28), date(2025, 12, 26),
    }

    def __init__(self, tenor: str, start_date: str, end_date: str, metric: str = 'price'):
        """
        Initialize bond macro plotter.
        
        Parameters:
        -----------
        tenor : str
            '05_year' or '10_year'
        start_date : str
            'YYYY-MM-DD' format
        end_date : str
            'YYYY-MM-DD' format
        metric : str
            'price' or 'yield'
        """
        self.tenor = tenor
        self.metric = metric.lower()
        self.tenor_label = "5-Year" if tenor == "05_year" else "10-Year"
        self.metric_label = "Yield (%)" if self.metric == 'yield' else "Price"
        self.start_date = self._parse_date(start_date)
        self.end_date = self._parse_date(end_date)
        self.bond_data = None
        self.fx_data = None
        self.fig = None
        self._load_data()

    def _parse_date(self, date_str: str) -> date:
        """Parse YYYY-MM-DD to date."""
        if isinstance(date_str, str):
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        return date_str if isinstance(date_str, date) else date_str.date()
    
    def _is_business_day(self, d: date) -> bool:
        """Check if date is a business day (exclude weekends and Indonesia holidays)."""
        if d.weekday() >= 5:  # Saturday or Sunday
            return False
        if d in self.INDONESIA_HOLIDAYS:
            return False
        return True

    def _load_data(self):
        """Load bond and macro data from CSV files, interpolate missing values."""
        db_path = os.path.join(os.path.dirname(__file__), 'database')
        
        # Load bond data
        bond_file = os.path.join(db_path, '20251215_priceyield.csv')
        if not os.path.exists(bond_file):
            raise FileNotFoundError(f"Bond data not found: {bond_file}")
        
        df_bond = pd.read_csv(bond_file)
        df_bond['date'] = pd.to_datetime(df_bond['date'], format='%d/%m/%Y').dt.date
        
        self.bond_data = df_bond[
            (df_bond['tenor'] == self.tenor) &
            (df_bond['date'] >= self.start_date) &
            (df_bond['date'] <= self.end_date)
        ].sort_values('date').reset_index(drop=True)
        
        # Interpolate missing values in bond data
        if len(self.bond_data) > 0:
            df_temp = self.bond_data.copy()
            df_temp['date'] = pd.to_datetime(df_temp['date'])
            df_temp = df_temp.set_index('date')
            df_temp = df_temp.asfreq('D')  # Daily frequency
            # Interpolate price and yield linearly
            for col in ['price', 'yield']:
                if col in df_temp.columns:
                    df_temp[col] = df_temp[col].interpolate(method='linear')
            df_temp = df_temp.reset_index()
            df_temp['date'] = df_temp['date'].dt.date
            self.bond_data = df_temp[df_temp['date'].notna()].reset_index(drop=True)
        
        # Load macro data (FX & VIX)
        macro_file = os.path.join(db_path, '20260102_daily01.csv')
        if not os.path.exists(macro_file):
            raise FileNotFoundError(f"Macro data not found: {macro_file}")
        
        df_macro = pd.read_csv(macro_file)
        # Parse date from yyyy/mm/dd format
        df_macro['date'] = pd.to_datetime(df_macro['date'], format='%Y/%m/%d').dt.date
        
        self.fx_data = df_macro[
            (df_macro['date'] >= self.start_date) &
            (df_macro['date'] <= self.end_date)
        ].sort_values('date').reset_index(drop=True)
        
        # Interpolate missing values in macro data
        if len(self.fx_data) > 0:
            df_temp = self.fx_data.copy()
            df_temp['date'] = pd.to_datetime(df_temp['date'])
            df_temp = df_temp.set_index('date')
            df_temp = df_temp.asfreq('D')
            for col in ['idrusd', 'vix_index']:
                if col in df_temp.columns:
                    df_temp[col] = df_temp[col].interpolate(method='linear')
            df_temp = df_temp.reset_index()
            df_temp['date'] = df_temp['date'].dt.date
            self.fx_data = df_temp[df_temp['date'].notna()].reset_index(drop=True)

    def _normalize(self, series: pd.Series) -> pd.Series:
        """Normalize series to 0-100 scale for overlay visualization."""
        min_val = series.min()
        max_val = series.max()
        if max_val == min_val:
            return pd.Series([50] * len(series), index=series.index)
        return ((series - min_val) / (max_val - min_val)) * 100

    def plot_with_fx(self) -> plt.Figure:
        """Plot bond metric with IDR/USD overlay (dual-axis, Economist style)."""
        if len(self.bond_data) < 2 or len(self.fx_data) < 2:
            raise ValueError("Insufficient data for plotting")
        
        fig, ax1 = plt.subplots(figsize=(14, 7))
        
        # Bond metric on left axis
        metric_col = 'yield' if self.metric == 'yield' else 'price'
        bond_dates = pd.to_datetime(self.bond_data['date'])
        bond_values = self.bond_data[metric_col]
        
        ax1.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax1.set_ylabel(f'{self.tenor_label} {self.metric_label}', 
                       color=ECONOMIST_COLORS['blue'], fontsize=11, fontweight='bold')
        line1 = ax1.plot(bond_dates, bond_values, 
                        color=ECONOMIST_COLORS['blue'], linewidth=2.5, 
                        label=f'{self.tenor_label} {self.metric_label}')
        ax1.tick_params(axis='y', labelcolor=ECONOMIST_COLORS['blue'])
        
        # FX on right axis
        fx_dates = pd.to_datetime(self.fx_data['date'])
        fx_values = self.fx_data['idrusd']
        
        color_fx = ECONOMIST_COLORS['red']
        ax2 = ax1.twinx()
        ax2.set_ylabel('IDR/USD Exchange Rate', color=color_fx, fontsize=11, fontweight='bold')
        line2 = ax2.plot(fx_dates, fx_values, 
                        color=color_fx, linewidth=2.5, linestyle='--', label='IDR/USD')
        ax2.tick_params(axis='y', labelcolor=color_fx)
        
        # Apply Economist styling
        apply_economist_style(fig, ax1)
        
        # Title
        title = f'{self.tenor_label} Indonesia Bonds & Currency (IDR/USD)'
        plt.title(title, fontsize=13, fontweight='bold', pad=20, color=ECONOMIST_COLORS['black'])
        
        # Legend
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left', fontsize=10, framealpha=0.95, frameon=True)
        
        # Caption
        add_economist_caption(fig, text=f"Source: PerisAI analytics | {self.start_date.strftime('%d %b %Y')} – {self.end_date.strftime('%d %b %Y')}")
        
        return fig

    def plot_with_vix(self) -> plt.Figure:
        """Plot bond metric with VIX overlay (dual-axis, Economist style)."""
        if len(self.bond_data) < 2 or len(self.fx_data) < 2:
            raise ValueError("Insufficient data for plotting")
        
        fig, ax1 = plt.subplots(figsize=(14, 7))
        
        # Bond metric on left axis
        metric_col = 'yield' if self.metric == 'yield' else 'price'
        bond_dates = pd.to_datetime(self.bond_data['date'])
        bond_values = self.bond_data[metric_col]
        
        ax1.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax1.set_ylabel(f'{self.tenor_label} {self.metric_label}', 
                       color=ECONOMIST_COLORS['blue'], fontsize=11, fontweight='bold')
        line1 = ax1.plot(bond_dates, bond_values, 
                        color=ECONOMIST_COLORS['blue'], linewidth=2.5, 
                        label=f'{self.tenor_label} {self.metric_label}')
        ax1.tick_params(axis='y', labelcolor=ECONOMIST_COLORS['blue'])
        
        # VIX on right axis
        fx_dates = pd.to_datetime(self.fx_data['date'])
        vix_values = self.fx_data['vix_index']
        
        color_vix = ECONOMIST_COLORS['yellow']
        ax2 = ax1.twinx()
        ax2.set_ylabel('VIX Volatility Index', color=color_vix, fontsize=11, fontweight='bold')
        line2 = ax2.plot(fx_dates, vix_values, 
                        color=color_vix, linewidth=2.5, linestyle='--', label='VIX')
        ax2.tick_params(axis='y', labelcolor=color_vix)
        
        # Apply Economist styling
        apply_economist_style(fig, ax1)
        
        # Title
        title = f'{self.tenor_label} Indonesia Bonds & Global Risk Sentiment (VIX)'
        plt.title(title, fontsize=13, fontweight='bold', pad=20, color=ECONOMIST_COLORS['black'])
        
        # Legend
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left', fontsize=10, framealpha=0.95, frameon=True)
        
        # Caption
        add_economist_caption(fig, text=f"Source: PerisAI analytics | {self.start_date.strftime('%d %b %Y')} – {self.end_date.strftime('%d %b %Y')}")
        
        return fig

    def plot_with_fx_vix(self) -> plt.Figure:
        """Plot bond metric with both FX and VIX overlays (triple-axis, Economist style)."""
        if len(self.bond_data) < 2 or len(self.fx_data) < 2:
            raise ValueError("Insufficient data for plotting")
        
        fig, ax1 = plt.subplots(figsize=(14, 7))
        
        # Bond metric on left axis
        metric_col = 'yield' if self.metric == 'yield' else 'price'
        bond_dates = pd.to_datetime(self.bond_data['date'])
        bond_values = self.bond_data[metric_col]
        
        ax1.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax1.set_ylabel(f'{self.tenor_label} {self.metric_label}', 
                       color=ECONOMIST_COLORS['blue'], fontsize=11, fontweight='bold')
        line1 = ax1.plot(bond_dates, bond_values, 
                        color=ECONOMIST_COLORS['blue'], linewidth=2.5, 
                        label=f'{self.tenor_label} {self.metric_label}')
        ax1.tick_params(axis='y', labelcolor=ECONOMIST_COLORS['blue'])
        
        # FX on second right axis
        fx_dates = pd.to_datetime(self.fx_data['date'])
        fx_values = self.fx_data['idrusd']
        
        ax2 = ax1.twinx()
        ax2.set_ylabel('IDR/USD Exchange Rate', color=ECONOMIST_COLORS['red'], fontsize=11, fontweight='bold')
        line2 = ax2.plot(fx_dates, fx_values, 
                        color=ECONOMIST_COLORS['red'], linewidth=2.0, linestyle='--', 
                        label='IDR/USD', alpha=0.8)
        ax2.tick_params(axis='y', labelcolor=ECONOMIST_COLORS['red'])
        ax2.spines['right'].set_position(('outward', 60))
        
        # VIX on third right axis
        vix_values = self.fx_data['vix_index']
        
        ax3 = ax1.twinx()
        ax3.set_ylabel('VIX Volatility Index', color=ECONOMIST_COLORS['yellow'], fontsize=11, fontweight='bold')
        line3 = ax3.plot(fx_dates, vix_values, 
                        color=ECONOMIST_COLORS['yellow'], linewidth=2.0, linestyle=':', 
                        label='VIX', alpha=0.8)
        ax3.tick_params(axis='y', labelcolor=ECONOMIST_COLORS['yellow'])
        ax3.spines['right'].set_position(('outward', 120))
        
        # Apply Economist styling
        apply_economist_style(fig, ax1)
        
        # Title
        title = f'{self.tenor_label} Indonesia Bonds: Yield & Price, Currency & Risk Sentiment'
        plt.title(title, fontsize=13, fontweight='bold', pad=20, color=ECONOMIST_COLORS['black'])
        
        # Legend
        lines = line1 + line2 + line3
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left', fontsize=10, framealpha=0.95, frameon=True)
        
        # Caption
        add_economist_caption(fig, text=f"Source: PerisAI analytics | {self.start_date.strftime('%d %b %Y')} – {self.end_date.strftime('%d %b %Y')}")
        
        return fig

    def save_and_return_image(self, filename: str = None) -> BytesIO:
        """Save figure and return as BytesIO for Telegram."""
        if self.fig is None:
            raise ValueError("No plot generated. Call plot_with_fx/vix first.")
        
        buffer = BytesIO()
        self.fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        
        if filename:
            self.fig.savefig(filename, format='png', dpi=150, bbox_inches='tight')
        
        return buffer


def create_bond_macro_plot(tenor: str, start_date: str, end_date: str, metric: str = 'price',
                           include_fx: bool = False, include_vix: bool = False) -> BytesIO:
    """
    Convenience function to create bond macro plot.
    
    Parameters:
    -----------
    tenor : str
        '05_year' or '10_year'
    start_date : str
        'YYYY-MM-DD' format
    end_date : str
        'YYYY-MM-DD' format
    metric : str
        'price' or 'yield'
    include_fx : bool
        Include IDR/USD exchange rate overlay
    include_vix : bool
        Include VIX volatility overlay
    
    Returns:
    --------
    BytesIO : Image buffer for Telegram
    """
    try:
        plotter = BondMacroPlotter(tenor, start_date, end_date, metric=metric)
        
        if include_fx and include_vix:
            plotter.fig = plotter.plot_with_fx_vix()
        elif include_fx:
            plotter.fig = plotter.plot_with_fx()
        elif include_vix:
            plotter.fig = plotter.plot_with_vix()
        else:
            raise ValueError("Must include FX and/or VIX")
        
        return plotter.save_and_return_image()
    
    except Exception as e:
        print(f"❌ Plot generation error: {str(e)}")
        raise


if __name__ == "__main__":
    # Test: Create all plot types for both price and yield
    print("Testing bond macro plots (price)...")
    
    # Test price plots
    plotter_price = BondMacroPlotter('10_year', '2023-01-02', '2025-12-31', metric='price')
    
    print("  Creating 10Y price + FX plot...")
    plotter_price.fig = plotter_price.plot_with_fx()
    plotter_price.save_and_return_image('test_bond_price_fx.png')
    print("  ✓ Saved: test_bond_price_fx.png")
    
    print("  Creating 10Y price + VIX plot...")
    plotter_price.fig = plotter_price.plot_with_vix()
    plotter_price.save_and_return_image('test_bond_price_vix.png')
    print("  ✓ Saved: test_bond_price_vix.png")
    
    print("  Creating 10Y price + FX + VIX plot...")
    plotter_price.fig = plotter_price.plot_with_fx_vix()
    plotter_price.save_and_return_image('test_bond_price_fx_vix.png')
    print("  ✓ Saved: test_bond_price_fx_vix.png")
    
    # Test yield plots
    print("\nTesting bond macro plots (yield)...")
    plotter_yield = BondMacroPlotter('10_year', '2023-01-02', '2025-12-31', metric='yield')
    
    print("  Creating 10Y yield + FX plot...")
    plotter_yield.fig = plotter_yield.plot_with_fx()
    plotter_yield.save_and_return_image('test_bond_yield_fx.png')
    print("  ✓ Saved: test_bond_yield_fx.png")
    
    print("  Creating 10Y yield + VIX plot...")
    plotter_yield.fig = plotter_yield.plot_with_vix()
    plotter_yield.save_and_return_image('test_bond_yield_vix.png')
    print("  ✓ Saved: test_bond_yield_vix.png")
    
    print("  Creating 10Y yield + FX + VIX plot...")
    plotter_yield.fig = plotter_yield.plot_with_fx_vix()
    plotter_yield.save_and_return_image('test_bond_yield_fx_vix.png')
    print("  ✓ Saved: test_bond_yield_fx_vix.png")
    
    print("\n✅ All plots generated successfully!")
