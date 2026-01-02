"""
Macroeconomic Data Table Formatting for Kei

Provides economist-style formatting of FX (IDR/USD) and VIX volatility data
for /kei tab queries.

Usage:
    formatter = MacroDataFormatter()
    table = formatter.format_idrusd_table('2023-01-02', '2025-12-31')
    table = formatter.format_vix_table('2023-01-02', '2025-12-31')
"""

import pandas as pd
import os
from datetime import datetime, date
from typing import Optional, Tuple
import statistics as stats_module


class MacroDataFormatter:
    """Format macroeconomic data as economist-style tables."""
    
    def __init__(self):
        """Initialize data loader."""
        self.db_path = os.path.join(os.path.dirname(__file__), 'database')
        self.macro_data = None
        self._load_macro_data()
    
    def _load_macro_data(self):
        """Load macroeconomic data from CSV."""
        macro_file = os.path.join(self.db_path, '20260102_daily01.csv')
        if not os.path.exists(macro_file):
            raise FileNotFoundError(f"Macro data not found: {macro_file}")
        
        df = pd.read_csv(macro_file)
        df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y').dt.date
        self.macro_data = df.sort_values('date').reset_index(drop=True)
    
    def _parse_date(self, date_str: str) -> date:
        """Parse YYYY-MM-DD to date."""
        if isinstance(date_str, str):
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        return date_str if isinstance(date_str, date) else date_str.date()
    
    def _format_economist_table(self, rows: list, headers: list, value_col: int = 1) -> str:
        """Format data as economist-style table with right-aligned numbers."""
        if not rows:
            return "⚠️ No data found for the specified period."
        
        # Determine column widths
        col_widths = [max(len(h), max(len(str(row[i])) for row in rows)) 
                      for i, h in enumerate(headers)]
        
        # Build table
        border = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
        header_row = "│" + "│".join(f" {h:^{col_widths[i]}} " for i, h in enumerate(headers)) + "│"
        separator = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
        
        table = border + "\n" + header_row + "\n" + separator + "\n"
        
        # Add data rows with right-aligned numbers
        for row in rows:
            formatted_row = []
            for i, cell in enumerate(row):
                if i == 0:  # Date column (left-aligned)
                    formatted_row.append(f" {str(cell):<{col_widths[i]}} ")
                else:  # Value columns (right-aligned)
                    formatted_row.append(f" {str(cell):>{col_widths[i]}} ")
            table += "│" + "│".join(formatted_row) + "│\n"
        
        # Summary stats row
        values = [float(row[value_col]) for row in rows 
                 if row[value_col] not in ['N/A', None, 'nan'] and 'nan' not in str(row[value_col]).lower()]
        if values:
            stats_row = ["Count", f"{len(values)}"]
            stats_row.extend(["" for _ in range(len(headers) - 2)])
            formatted_row = []
            for i, cell in enumerate(stats_row):
                if i == 0:
                    formatted_row.append(f" {str(cell):<{col_widths[i]}} ")
                else:
                    formatted_row.append(f" {str(cell):>{col_widths[i]}} ")
            
            table += separator + "\n" + "│" + "│".join(formatted_row) + "│\n"
            
            # Min row
            min_val = min(values)
            table += f"│ {'Min':<{col_widths[0]}} │ {min_val:>{col_widths[1]}.2f} │\n"
            
            # Max row
            max_val = max(values)
            table += f"│ {'Max':<{col_widths[0]}} │ {max_val:>{col_widths[1]}.2f} │\n"
            
            # Avg row
            avg_val = sum(values) / len(values)
            table += f"│ {'Avg':<{col_widths[0]}} │ {avg_val:>{col_widths[1]}.2f} │\n"
            
            # Std row
            if len(values) > 1:
                mean_val = avg_val
                variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)
                std_val = variance ** 0.5
                table += f"│ {'Std':<{col_widths[0]}} │ {std_val:>{col_widths[1]}.2f} │\n"
        
        table += "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"
        return table
    
    def format_idrusd_table(self, start_date: str, end_date: str) -> str:
        """Format IDR/USD exchange rate table."""
        start = self._parse_date(start_date)
        end = self._parse_date(end_date)
        
        df = self.macro_data[
            (self.macro_data['date'] >= start) &
            (self.macro_data['date'] <= end)
        ].copy()
        
        if df.empty:
            return "⚠️ No IDR/USD data found for the specified period."
        
        # Select every Nth row to limit table size (show ~20 rows max)
        step = max(1, len(df) // 20)
        df = df.iloc[::step].reset_index(drop=True)
        
        rows = []
        for _, row in df.iterrows():
            rows.append([
                row['date'].strftime('%d %b %Y'),
                f"{row['idrusd']:.2f}"
            ])
        
        return "💱 **IDR/USD Exchange Rate**\n```\n" + \
               self._format_economist_table(rows, ['Date', 'IDR/USD'], value_col=1) + \
               "\n```"
    
    def format_vix_table(self, start_date: str, end_date: str) -> str:
        """Format VIX volatility index table."""
        start = self._parse_date(start_date)
        end = self._parse_date(end_date)
        
        df = self.macro_data[
            (self.macro_data['date'] >= start) &
            (self.macro_data['date'] <= end)
        ].copy()
        
        if df.empty:
            return "⚠️ No VIX data found for the specified period."
        
        # Select every Nth row to limit table size (show ~20 rows max)
        step = max(1, len(df) // 20)
        df = df.iloc[::step].reset_index(drop=True)
        
        rows = []
        for _, row in df.iterrows():
            rows.append([
                row['date'].strftime('%d %b %Y'),
                f"{row['vix_index']:.2f}"
            ])
        
        return "📊 **VIX Volatility Index**\n```\n" + \
               self._format_economist_table(rows, ['Date', 'VIX'], value_col=1) + \
               "\n```"
    
    def format_macro_combined_table(self, start_date: str, end_date: str) -> str:
        """Format combined IDR/USD and VIX table."""
        start = self._parse_date(start_date)
        end = self._parse_date(end_date)
        
        df = self.macro_data[
            (self.macro_data['date'] >= start) &
            (self.macro_data['date'] <= end)
        ].copy()
        
        if df.empty:
            return "⚠️ No macro data found for the specified period."
        
        # Select every Nth row to limit table size (show ~20 rows max)
        step = max(1, len(df) // 20)
        df = df.iloc[::step].reset_index(drop=True)
        
        rows = []
        for _, row in df.iterrows():
            rows.append([
                row['date'].strftime('%d %b %Y'),
                f"{row['idrusd']:.2f}",
                f"{row['vix_index']:.2f}"
            ])
        
        return "🌍 **Macroeconomic Indicators: Currency & Volatility**\n```\n" + \
               self._format_economist_table(rows, ['Date', 'IDR/USD', 'VIX'], value_col=1) + \
               "\n```"


def format_macro_table(metric: str, start_date: str, end_date: str) -> str:
    """
    Convenience function to format macro data table.
    
    Parameters:
    -----------
    metric : str
        'idrusd', 'fx', 'vix', or 'both'/'combined'
    start_date : str
        'YYYY-MM-DD' format
    end_date : str
        'YYYY-MM-DD' format
    
    Returns:
    --------
    str : Formatted economist-style table
    """
    try:
        formatter = MacroDataFormatter()
        
        if metric.lower() in ['idrusd', 'fx']:
            return formatter.format_idrusd_table(start_date, end_date)
        elif metric.lower() == 'vix':
            return formatter.format_vix_table(start_date, end_date)
        elif metric.lower() in ['both', 'combined', 'all']:
            return formatter.format_macro_combined_table(start_date, end_date)
        else:
            return f"❌ Unknown metric: {metric}. Supported: idrusd, fx, vix, both"
    
    except Exception as e:
        return f"❌ Error formatting macro table: {str(e)}"


if __name__ == "__main__":
    # Test: Format all table types
    print("Testing macro data table formatting...\n")
    
    formatter = MacroDataFormatter()
    
    print("IDR/USD Table (2023-2025):")
    print(formatter.format_idrusd_table('2023-01-02', '2025-12-31'))
    print("\n" + "="*60 + "\n")
    
    print("VIX Table (2023-2025):")
    print(formatter.format_vix_table('2023-01-02', '2025-12-31'))
    print("\n" + "="*60 + "\n")
    
    print("Combined Macro Table (2023-2025):")
    print(formatter.format_macro_combined_table('2023-01-02', '2025-12-31'))
    
    print("\n✅ All macro tables formatted successfully!")
