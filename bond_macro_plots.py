"""
Multi-Variable Bond & Macroeconomic Plots

Create professional plots showing bond prices/yields alongside FX and/or VIX 
for contextual macroeconomic analysis.

Usage:
    plotter = BondMacroPlotter('10_year', '2023-01-02', '2025-12-31')
    fig = plotter.plot_with_fx_vix()
    plotter.save_and_return_image('output.png')
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
from io import BytesIO


class BondMacroPlotter:
    """Create multi-variable plots: bond prices/yields + FX/VIX."""

    def __init__(self, tenor: str, start_date: str, end_date: str):
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
        """
        self.tenor = tenor
        self.tenor_label = "5-Year" if tenor == "05_year" else "10-Year"
        self.start_date = self._parse_date(start_date)
        self.end_date = self._parse_date(end_date)
        self.bond_data = None
        self.fx_data = None
        self.fig = None
        self._load_data()

    def _parse_date(self, date_str: str) -> datetime:
        """Parse YYYY-MM-DD to datetime."""
        if isinstance(date_str, str):
            return datetime.strptime(date_str, '%Y-%m-%d')
        return date_str

    def _load_data(self):
        """Load bond and macro data from CSV files."""
        db_path = os.path.join(os.path.dirname(__file__), 'database')
        
        # Load bond data
        bond_file = os.path.join(db_path, '20251215_priceyield.csv')
        if not os.path.exists(bond_file):
            raise FileNotFoundError(f"Bond data not found: {bond_file}")
        
        df_bond = pd.read_csv(bond_file)
        df_bond['date'] = pd.to_datetime(df_bond['date'], format='%d/%m/%Y')
        
        self.bond_data = df_bond[
            (df_bond['tenor'] == self.tenor) &
            (df_bond['date'] >= self.start_date) &
            (df_bond['date'] <= self.end_date)
        ].sort_values('date').reset_index(drop=True)
        
        # Load macro data (FX & VIX)
        macro_file = os.path.join(db_path, '20260102_daily01.csv')
        if not os.path.exists(macro_file):
            raise FileNotFoundError(f"Macro data not found: {macro_file}")
        
        df_macro = pd.read_csv(macro_file)
        df_macro['date'] = pd.to_datetime(df_macro['date'], format='%d/%m/%Y')
        
        self.fx_data = df_macro[
            (df_macro['date'] >= self.start_date) &
            (df_macro['date'] <= self.end_date)
        ].sort_values('date').reset_index(drop=True)

    def _normalize(self, series: pd.Series) -> pd.Series:
        """Normalize series to 0-100 scale for overlay visualization."""
        min_val = series.min()
        max_val = series.max()
        if max_val == min_val:
            return pd.Series([50] * len(series), index=series.index)
        return ((series - min_val) / (max_val - min_val)) * 100

    def plot_with_fx(self) -> plt.Figure:
        """Plot bond price with IDR/USD overlay (dual-axis)."""
        if len(self.bond_data) < 2 or len(self.fx_data) < 2:
            raise ValueError("Insufficient data for plotting")
        
        fig, ax1 = plt.subplots(figsize=(14, 7))
        
        # Bond price on left axis
        color_bond = '#1f77b4'
        ax1.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax1.set_ylabel(f'{self.tenor_label} Bond Price', color=color_bond, fontsize=11, fontweight='bold')
        line1 = ax1.plot(self.bond_data['date'], self.bond_data['price'], 
                         color=color_bond, linewidth=2.5, label=f'{self.tenor_label} Price')
        ax1.tick_params(axis='y', labelcolor=color_bond)
        ax1.grid(True, alpha=0.3)
        
        # FX on right axis
        color_fx = '#d62728'
        ax2 = ax1.twinx()
        ax2.set_ylabel('IDR/USD Exchange Rate', color=color_fx, fontsize=11, fontweight='bold')
        line2 = ax2.plot(self.fx_data['date'], self.fx_data['idrusd'], 
                         color=color_fx, linewidth=2.5, linestyle='--', label='IDR/USD')
        ax2.tick_params(axis='y', labelcolor=color_fx)
        
        # Title and legend
        plt.title(f'🌍 {self.tenor_label} Indonesia Bonds & Currency (IDR/USD)\n{self.start_date.strftime("%b %d, %Y")} – {self.end_date.strftime("%b %d, %Y")}',
                  fontsize=13, fontweight='bold', pad=20)
        
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left', fontsize=10, framealpha=0.95)
        
        fig.tight_layout()
        return fig

    def plot_with_vix(self) -> plt.Figure:
        """Plot bond price with VIX overlay (dual-axis, VIX normalized)."""
        if len(self.bond_data) < 2 or len(self.fx_data) < 2:
            raise ValueError("Insufficient data for plotting")
        
        # Normalize VIX for comparison (typically 10-80, map to bond price range)
        vix_norm = self._normalize(self.fx_data['vix_index'])
        bond_min, bond_max = self.bond_data['price'].min(), self.bond_data['price'].max()
        vix_scaled = bond_min + (vix_norm / 100) * (bond_max - bond_min)
        
        fig, ax1 = plt.subplots(figsize=(14, 7))
        
        # Bond price on left axis
        color_bond = '#1f77b4'
        ax1.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax1.set_ylabel(f'{self.tenor_label} Bond Price', color=color_bond, fontsize=11, fontweight='bold')
        line1 = ax1.plot(self.bond_data['date'], self.bond_data['price'], 
                         color=color_bond, linewidth=2.5, label=f'{self.tenor_label} Price')
        ax1.tick_params(axis='y', labelcolor=color_bond)
        ax1.grid(True, alpha=0.3)
        
        # VIX on right axis (normalized)
        color_vix = '#ff7f0e'
        ax2 = ax1.twinx()
        ax2.set_ylabel('VIX Volatility Index (Normalized)', color=color_vix, fontsize=11, fontweight='bold')
        line2 = ax2.plot(self.fx_data['date'], self.fx_data['vix_index'], 
                         color=color_vix, linewidth=2.5, linestyle='--', label='VIX')
        ax2.tick_params(axis='y', labelcolor=color_vix)
        
        # Title and legend
        plt.title(f'🌍 {self.tenor_label} Indonesia Bonds & Global Risk Sentiment (VIX)\n{self.start_date.strftime("%b %d, %Y")} – {self.end_date.strftime("%b %d, %Y")}',
                  fontsize=13, fontweight='bold', pad=20)
        
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left', fontsize=10, framealpha=0.95)
        
        fig.tight_layout()
        return fig

    def plot_with_fx_vix(self) -> plt.Figure:
        """Plot bond price with both FX and VIX overlays (triple-axis)."""
        if len(self.bond_data) < 2 or len(self.fx_data) < 2:
            raise ValueError("Insufficient data for plotting")
        
        fig, ax1 = plt.subplots(figsize=(14, 7))
        
        # Bond price on left axis
        color_bond = '#1f77b4'
        ax1.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax1.set_ylabel(f'{self.tenor_label} Bond Price', color=color_bond, fontsize=11, fontweight='bold')
        line1 = ax1.plot(self.bond_data['date'], self.bond_data['price'], 
                         color=color_bond, linewidth=2.5, label=f'{self.tenor_label} Price')
        ax1.tick_params(axis='y', labelcolor=color_bond)
        ax1.grid(True, alpha=0.3)
        
        # FX on second right axis
        color_fx = '#d62728'
        ax2 = ax1.twinx()
        ax2.set_ylabel('IDR/USD Exchange Rate', color=color_fx, fontsize=11, fontweight='bold')
        line2 = ax2.plot(self.fx_data['date'], self.fx_data['idrusd'], 
                         color=color_fx, linewidth=2.0, linestyle='--', label='IDR/USD', alpha=0.8)
        ax2.tick_params(axis='y', labelcolor=color_fx)
        ax2.spines['right'].set_position(('outward', 60))
        
        # VIX on third right axis
        color_vix = '#ff7f0e'
        ax3 = ax1.twinx()
        ax3.set_ylabel('VIX Volatility Index', color=color_vix, fontsize=11, fontweight='bold')
        line3 = ax3.plot(self.fx_data['date'], self.fx_data['vix_index'], 
                         color=color_vix, linewidth=2.0, linestyle=':', label='VIX', alpha=0.8)
        ax3.tick_params(axis='y', labelcolor=color_vix)
        ax3.spines['right'].set_position(('outward', 120))
        
        # Title and legend
        plt.title(f'🌍 {self.tenor_label} Indonesia Bonds: Price, Currency & Risk Sentiment\n{self.start_date.strftime("%b %d, %Y")} – {self.end_date.strftime("%b %d, %Y")}',
                  fontsize=13, fontweight='bold', pad=20)
        
        lines = line1 + line2 + line3
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left', fontsize=10, framealpha=0.95)
        
        fig.tight_layout()
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


def create_bond_macro_plot(tenor: str, start_date: str, end_date: str, 
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
    include_fx : bool
        Include IDR/USD exchange rate overlay
    include_vix : bool
        Include VIX volatility overlay
    
    Returns:
    --------
    BytesIO : Image buffer for Telegram
    """
    try:
        plotter = BondMacroPlotter(tenor, start_date, end_date)
        
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
    # Test: Create all three plot types
    print("Testing bond macro plots...")
    
    plotter = BondMacroPlotter('10_year', '2023-01-02', '2025-12-31')
    
    # Plot 1: With FX
    print("  Creating 10Y bond + FX plot...")
    plotter.fig = plotter.plot_with_fx()
    plotter.save_and_return_image('test_bond_fx.png')
    print("  ✓ Saved: test_bond_fx.png")
    
    # Plot 2: With VIX
    print("  Creating 10Y bond + VIX plot...")
    plotter.fig = plotter.plot_with_vix()
    plotter.save_and_return_image('test_bond_vix.png')
    print("  ✓ Saved: test_bond_vix.png")
    
    # Plot 3: With FX & VIX
    print("  Creating 10Y bond + FX + VIX plot...")
    plotter.fig = plotter.plot_with_fx_vix()
    plotter.save_and_return_image('test_bond_fx_vix.png')
    print("  ✓ Saved: test_bond_fx_vix.png")
    
    print("\n✅ All plots generated successfully!")
