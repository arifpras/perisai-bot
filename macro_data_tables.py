"""
Macroeconomic Data Table Formatting for Kei

Provides economist-style formatting of FX (IDR/USD) and VIX volatility data
for /kei tab queries with proper formatting: FX with thousand separators (no decimals),
VIX with 2 decimals, and complete summary statistics.

Usage:
    formatter = MacroDataFormatter()
    table = formatter.format_idrusd_table('2023-01-02', '2025-12-31')
    table = formatter.format_vix_table('2023-01-02', '2025-12-31')
"""

import pandas as pd
import os
from datetime import datetime, date
from typing import Optional, List, Dict


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
        # Parse date from yyyy/mm/dd format
        df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d').dt.date
        self.macro_data = df.sort_values('date').reset_index(drop=True)
    
    def _parse_date(self, date_str: str) -> date:
        """Parse YYYY-MM-DD to date."""
        if isinstance(date_str, str):
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        return date_str if isinstance(date_str, date) else date_str.date()
    
    def _format_economist_table(self, rows: list, headers: list, 
                               col_formats: Dict[int, str] = None) -> str:
        """Format data as economist-style table with right-aligned numbers.
        
        Parameters:
        -----------
        rows : list
            List of row data
        headers : list
            Column headers
        col_formats : dict
            Format specification per column: {col_idx: 'fx'|'vix'|'text'}
            'fx': thousand separator, no decimals
            'vix': 2 decimal places
            'text': text formatting
        """
        if not rows:
            return "⚠️ No data found for the specified period."
        
        if col_formats is None:
            col_formats = {}
        
        # Determine column widths - need to account for formatted values
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i in col_formats:
                    if col_formats[i] == 'fx':
                        # Format: 15,592 (thousand separator, no decimals)
                        try:
                            formatted = f"{float(cell):,.0f}"
                        except (ValueError, TypeError):
                            formatted = str(cell)
                    elif col_formats[i] == 'vix':
                        # Format: 21.67 (2 decimals)
                        try:
                            formatted = f"{float(cell):.2f}"
                        except (ValueError, TypeError):
                            formatted = str(cell)
                    else:
                        formatted = str(cell)
                else:
                    formatted = str(cell)
                col_widths[i] = max(col_widths[i], len(formatted))
        
        # Build table
        border = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
        header_row = "│" + "│".join(f" {h:^{col_widths[i]}} " for i, h in enumerate(headers)) + "│"
        separator = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
        
        table = border + "\n" + header_row + "\n" + separator + "\n"
        
        # Add data rows
        for row in rows:
            formatted_row = []
            for i, cell in enumerate(row):
                if i == 0:  # Date column (left-aligned)
                    formatted = str(cell)
                    formatted_row.append(f" {formatted:<{col_widths[i]}} ")
                elif i in col_formats:
                    if col_formats[i] == 'fx':
                        try:
                            formatted = f"{float(cell):,.0f}"
                        except (ValueError, TypeError):
                            formatted = str(cell)
                    elif col_formats[i] == 'vix':
                        try:
                            formatted = f"{float(cell):.2f}"
                        except (ValueError, TypeError):
                            formatted = str(cell)
                    else:
                        formatted = str(cell)
                    formatted_row.append(f" {formatted:>{col_widths[i]}} ")
                else:
                    formatted_row.append(f" {str(cell):>{col_widths[i]}} ")
            table += "│" + "│".join(formatted_row) + "│\n"
        
        # Calculate statistics for each numeric column
        numeric_cols = {i: [] for i in col_formats.keys() if col_formats[i] in ['fx', 'vix']}
        
        for row in rows:
            for col_idx in numeric_cols.keys():
                try:
                    val = float(row[col_idx])
                    if not (val != val):  # Skip NaN
                        numeric_cols[col_idx].append(val)
                except (ValueError, TypeError):
                    pass
        
        if numeric_cols and any(numeric_cols.values()):
            table += separator + "\n"
            
            # Count row
            count_row = ["Count"] + ["" for _ in range(len(headers) - 1)]
            for col_idx, values in numeric_cols.items():
                if values:
                    count_row[col_idx] = str(len(values))
            formatted_row = []
            for i, cell in enumerate(count_row):
                if i == 0:
                    formatted_row.append(f" {str(cell):<{col_widths[i]}} ")
                else:
                    formatted_row.append(f" {str(cell):>{col_widths[i]}} ")
            table += "│" + "│".join(formatted_row) + "│\n"
            
            # Min row
            min_row = ["Min"] + ["" for _ in range(len(headers) - 1)]
            for col_idx, values in numeric_cols.items():
                if values:
                    min_val = min(values)
                    if col_formats[col_idx] == 'fx':
                        min_row[col_idx] = f"{min_val:,.0f}"
                    else:
                        min_row[col_idx] = f"{min_val:.2f}"
            formatted_row = []
            for i, cell in enumerate(min_row):
                if i == 0:
                    formatted_row.append(f" {str(cell):<{col_widths[i]}} ")
                else:
                    formatted_row.append(f" {str(cell):>{col_widths[i]}} ")
            table += "│" + "│".join(formatted_row) + "│\n"
            
            # Max row
            max_row = ["Max"] + ["" for _ in range(len(headers) - 1)]
            for col_idx, values in numeric_cols.items():
                if values:
                    max_val = max(values)
                    if col_formats[col_idx] == 'fx':
                        max_row[col_idx] = f"{max_val:,.0f}"
                    else:
                        max_row[col_idx] = f"{max_val:.2f}"
            formatted_row = []
            for i, cell in enumerate(max_row):
                if i == 0:
                    formatted_row.append(f" {str(cell):<{col_widths[i]}} ")
                else:
                    formatted_row.append(f" {str(cell):>{col_widths[i]}} ")
            table += "│" + "│".join(formatted_row) + "│\n"
            
            # Avg row
            avg_row = ["Avg"] + ["" for _ in range(len(headers) - 1)]
            for col_idx, values in numeric_cols.items():
                if values:
                    avg_val = sum(values) / len(values)
                    if col_formats[col_idx] == 'fx':
                        avg_row[col_idx] = f"{avg_val:,.0f}"
                    else:
                        avg_row[col_idx] = f"{avg_val:.2f}"
            formatted_row = []
            for i, cell in enumerate(avg_row):
                if i == 0:
                    formatted_row.append(f" {str(cell):<{col_widths[i]}} ")
                else:
                    formatted_row.append(f" {str(cell):>{col_widths[i]}} ")
            table += "│" + "│".join(formatted_row) + "│\n"
            
            # Std row
            std_row = ["Std"] + ["" for _ in range(len(headers) - 1)]
            for col_idx, values in numeric_cols.items():
                if values and len(values) > 1:
                    mean_val = sum(values) / len(values)
                    variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)
                    std_val = variance ** 0.5
                    if col_formats[col_idx] == 'fx':
                        std_row[col_idx] = f"{std_val:,.0f}"
                    else:
                        std_row[col_idx] = f"{std_val:.2f}"
            formatted_row = []
            for i, cell in enumerate(std_row):
                if i == 0:
                    formatted_row.append(f" {str(cell):<{col_widths[i]}} ")
                else:
                    formatted_row.append(f" {str(cell):>{col_widths[i]}} ")
            table += "│" + "│".join(formatted_row) + "│\n"
        
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
        
        # Filter out NaN values (holidays/missing data)
        df = df.dropna(subset=['idrusd']).copy()
        
        if df.empty:
            return "⚠️ No valid IDR/USD data found for the specified period (may be holiday)."
        
        rows = []
        for _, row in df.iterrows():
            rows.append([
                row['date'].strftime('%d %b %Y'),
                row['idrusd']
            ])
        
        return "💱 IDR/USD Exchange Rate\n```\n" + \
               self._format_economist_table(rows, ['Date', 'IDR/USD'], {1: 'fx'}) + \
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
        
        # Filter out NaN values (holidays/missing data)
        df = df.dropna(subset=['vix_index']).copy()
        
        if df.empty:
            return "⚠️ No valid VIX data found for the specified period (may be holiday)."
        
        rows = []
        for _, row in df.iterrows():
            rows.append([
                row['date'].strftime('%d %b %Y'),
                row['vix_index']
            ])
        
        return "📊 VIX Volatility Index\n```\n" + \
               self._format_economist_table(rows, ['Date', 'VIX'], {1: 'vix'}) + \
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
        
        # Filter out rows with any NaN values (holidays/missing data)
        df = df.dropna(subset=['idrusd', 'vix_index']).copy()
        
        if df.empty:
            return "⚠️ No valid macro data found for the specified period (may be holiday)."
        
        rows = []
        for _, row in df.iterrows():
            rows.append([
                row['date'].strftime('%d %b %Y'),
                row['idrusd'],
                row['vix_index']
            ])
        
        return "🌍 Macroeconomic Indicators: Currency & Volatility\n```\n" + \
               self._format_economist_table(rows, ['Date', 'IDR/USD', 'VIX'], {1: 'fx', 2: 'vix'}) + \
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
