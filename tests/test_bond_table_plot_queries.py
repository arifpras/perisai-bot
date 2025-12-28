"""Test bond table and plot queries for /kei tab and /kin plot commands."""
import pytest
from datetime import date
from unittest.mock import Mock, MagicMock, patch
from telegram.constants import ParseMode

# Import the parsers and test via the telegram_bot module
import sys
sys.path.insert(0, '/workspaces/perisai-bot')

from telegram_bot import parse_bond_table_query, parse_bond_plot_query


class TestParseBondTableQuery:
    """Test parse_bond_table_query for various scenarios."""
    
    def test_single_tenor_single_metric_single_month(self):
        """Test: /kei tab yield 5 year in feb 2025"""
        q = "/kei tab yield 5 year in feb 2025"
        result = parse_bond_table_query(q)
        assert result is not None
        assert result['metrics'] == ['yield']
        assert result['tenors'] == ['05_year']
        assert result['start_date'] == date(2025, 2, 1)
        assert result['end_date'] == date(2025, 2, 28)
    
    def test_single_tenor_single_metric_single_quarter(self):
        """Test: /kei tab price 5 year in q1 2025"""
        q = "/kei tab price 5 year in q1 2025"
        result = parse_bond_table_query(q)
        assert result is not None
        assert result['metrics'] == ['price']
        assert result['tenors'] == ['05_year']
        assert result['start_date'] == date(2025, 1, 1)
        assert result['end_date'] == date(2025, 3, 31)
    
    def test_single_tenor_single_metric_single_year(self):
        """Test: /kei tab yield 10 year in 2025"""
        q = "/kei tab yield 10 year in 2025"
        result = parse_bond_table_query(q)
        assert result is not None
        assert result['metrics'] == ['yield']
        assert result['tenors'] == ['10_year']
        assert result['start_date'] == date(2025, 1, 1)
        assert result['end_date'] == date(2025, 12, 31)
    
    def test_multi_tenor_single_metric_single_month(self):
        """Test: /kei tab yield 5 and 10 year in apr 2024"""
        q = "/kei tab yield 5 and 10 year in apr 2024"
        result = parse_bond_table_query(q)
        assert result is not None
        assert result['metrics'] == ['yield']
        assert result['tenors'] == ['05_year', '10_year']
        assert result['start_date'] == date(2024, 4, 1)
        assert result['end_date'] == date(2024, 4, 30)
    
    def test_multi_tenor_single_metric_month_range(self):
        """Test: /kei tab yield 5 and 10 year from oct 2023 to mar 2024"""
        q = "/kei tab yield 5 and 10 year from oct 2023 to mar 2024"
        result = parse_bond_table_query(q)
        assert result is not None
        assert result['metrics'] == ['yield']
        assert result['tenors'] == ['05_year', '10_year']
        assert result['start_date'] == date(2023, 10, 1)
        assert result['end_date'] == date(2024, 3, 31)
    
    def test_multi_tenor_single_metric_quarter_range(self):
        """Test: /kei tab price 5 and 10 year from q3 2023 to q2 2024"""
        q = "/kei tab price 5 and 10 year from q3 2023 to q2 2024"
        result = parse_bond_table_query(q)
        assert result is not None
        assert result['metrics'] == ['price']
        assert result['tenors'] == ['05_year', '10_year']
        assert result['start_date'] == date(2023, 7, 1)  # Q3 start
        assert result['end_date'] == date(2024, 6, 30)   # Q2 end
    
    def test_multi_tenor_single_metric_year_range(self):
        """Test: /kei tab yield 5 and 10 year from 2023 to 2024"""
        q = "/kei tab yield 5 and 10 year from 2023 to 2024"
        result = parse_bond_table_query(q)
        assert result is not None
        assert result['metrics'] == ['yield']
        assert result['tenors'] == ['05_year', '10_year']
        assert result['start_date'] == date(2023, 1, 1)
        assert result['end_date'] == date(2024, 12, 31)
    
    def test_single_tenor_dual_metrics_single_month(self):
        """Test: /kei tab yield and price 5 year in apr 2023"""
        q = "/kei tab yield and price 5 year in apr 2023"
        result = parse_bond_table_query(q)
        assert result is not None
        assert result['metrics'] == ['yield', 'price']
        assert result['tenors'] == ['05_year']
        assert result['start_date'] == date(2023, 4, 1)
        assert result['end_date'] == date(2023, 4, 30)
    
    def test_single_tenor_dual_metrics_single_quarter(self):
        """Test: /kei tab yield and price 5 year in q3 2023"""
        q = "/kei tab yield and price 5 year in q3 2023"
        result = parse_bond_table_query(q)
        assert result is not None
        assert result['metrics'] == ['yield', 'price']
        assert result['tenors'] == ['05_year']
        assert result['start_date'] == date(2023, 7, 1)
        assert result['end_date'] == date(2023, 9, 30)
    
    def test_single_tenor_dual_metrics_single_year(self):
        """Test: /kei tab yield and price 5 year in 2023"""
        q = "/kei tab yield and price 5 year in 2023"
        result = parse_bond_table_query(q)
        assert result is not None
        assert result['metrics'] == ['yield', 'price']
        assert result['tenors'] == ['05_year']
        assert result['start_date'] == date(2023, 1, 1)
        assert result['end_date'] == date(2023, 12, 31)
    
    def test_multi_tenor_dual_metrics_month_range(self):
        """Test: /kei tab yield and price 5 and 10 year from apr 2024 to feb 2025"""
        q = "/kei tab yield and price 5 and 10 year from apr 2024 to feb 2025"
        result = parse_bond_table_query(q)
        assert result is not None
        assert result['metrics'] == ['yield', 'price']
        assert result['tenors'] == ['05_year', '10_year']
        assert result['start_date'] == date(2024, 4, 1)
        assert result['end_date'] == date(2025, 2, 28)
    
    def test_not_a_tab_query(self):
        """Test: query without 'tab' should return None"""
        q = "/kei yield 5 year in jan 2025"
        result = parse_bond_table_query(q)
        assert result is None
    
    def test_missing_tenor(self):
        """Test: query with no tenor should return None"""
        q = "/kei tab yield in jan 2025"
        result = parse_bond_table_query(q)
        assert result is None
    
    def test_missing_metric(self):
        """Test: query with no metric should return None"""
        q = "/kei tab 5 and 10 year in jan 2025"
        result = parse_bond_table_query(q)
        assert result is None


class TestParseBondPlotQuery:
    """Test parse_bond_plot_query for various scenarios."""
    
    def test_single_tenor_single_metric_single_month(self):
        """Test: /kin plot yield 5 year in jan 2025"""
        q = "/kin plot yield 5 year in jan 2025"
        result = parse_bond_plot_query(q)
        assert result is not None
        assert result['metric'] == 'yield'
        assert result['tenors'] == ['05_year']
        assert result['start_date'] == date(2025, 1, 1)
        assert result['end_date'] == date(2025, 1, 31)
    
    def test_single_tenor_single_metric_single_quarter(self):
        """Test: /kin plot price 10 year in q3 2025"""
        q = "/kin plot price 10 year in q3 2025"
        result = parse_bond_plot_query(q)
        assert result is not None
        assert result['metric'] == 'price'
        assert result['tenors'] == ['10_year']
        assert result['start_date'] == date(2025, 7, 1)
        assert result['end_date'] == date(2025, 9, 30)
    
    def test_multi_tenor_single_metric_month_range(self):
        """Test: /kin plot yield 5 and 10 year from oct 2024 to mar 2025"""
        q = "/kin plot yield 5 and 10 year from oct 2024 to mar 2025"
        result = parse_bond_plot_query(q)
        assert result is not None
        assert result['metric'] == 'yield'
        assert result['tenors'] == ['05_year', '10_year']
        assert result['start_date'] == date(2024, 10, 1)
        assert result['end_date'] == date(2025, 3, 31)
    
    def test_multi_tenor_single_metric_quarter_range(self):
        """Test: /kin plot price 5 and 10 year from q2 2024 to q1 2025"""
        q = "/kin plot price 5 and 10 year from q2 2024 to q1 2025"
        result = parse_bond_plot_query(q)
        assert result is not None
        assert result['metric'] == 'price'
        assert result['tenors'] == ['05_year', '10_year']
        assert result['start_date'] == date(2024, 4, 1)  # Q2 start
        assert result['end_date'] == date(2025, 3, 31)   # Q1 end
    
    def test_multi_tenor_single_metric_year_range(self):
        """Test: /kin plot yield 5 and 10 year from 2023 to 2024"""
        q = "/kin plot yield 5 and 10 year from 2023 to 2024"
        result = parse_bond_plot_query(q)
        assert result is not None
        assert result['metric'] == 'yield'
        assert result['tenors'] == ['05_year', '10_year']
        assert result['start_date'] == date(2023, 1, 1)
        assert result['end_date'] == date(2024, 12, 31)
    
    def test_not_a_plot_query(self):
        """Test: query without 'plot' should return None"""
        q = "/kin yield 5 year in jan 2025"
        result = parse_bond_plot_query(q)
        assert result is None
    
    def test_missing_tenor_in_plot(self):
        """Test: plot query with no tenor should return None"""
        q = "/kin plot yield in jan 2025"
        result = parse_bond_plot_query(q)
        assert result is None
    
    def test_missing_metric_in_plot(self):
        """Test: plot query with no metric should return None"""
        q = "/kin plot 5 and 10 year in jan 2025"
        result = parse_bond_plot_query(q)
        assert result is None


class TestMonthNameParsing:
    """Test that month names are correctly parsed."""
    
    @pytest.mark.parametrize("month_str,expected_month", [
        ("jan", 1),
        ("january", 1),
        ("feb", 2),
        ("february", 2),
        ("mar", 3),
        ("march", 3),
        ("apr", 4),
        ("april", 4),
        ("may", 5),
        ("jun", 6),
        ("june", 6),
        ("jul", 7),
        ("july", 7),
        ("aug", 8),
        ("august", 8),
        ("sep", 9),
        ("september", 9),
        ("oct", 10),
        ("october", 10),
        ("nov", 11),
        ("november", 11),
        ("dec", 12),
        ("december", 12),
    ])
    def test_month_names(self, month_str, expected_month):
        """Test all month name variations."""
        q = f"/kei tab yield 5 year in {month_str} 2025"
        result = parse_bond_table_query(q)
        assert result is not None
        assert result['start_date'].month == expected_month
        assert result['start_date'].year == 2025


class TestQuarterParsing:
    """Test quarter period parsing."""
    
    @pytest.mark.parametrize("quarter,expected_months", [
        ("q1", (1, 3)),
        ("q2", (4, 6)),
        ("q3", (7, 9)),
        ("q4", (10, 12)),
    ])
    def test_quarters(self, quarter, expected_months):
        """Test all quarter variations."""
        q = f"/kei tab yield 5 year in {quarter} 2025"
        result = parse_bond_table_query(q)
        assert result is not None
        assert result['start_date'].month == expected_months[0]
        assert result['end_date'].month == expected_months[1]
        assert result['start_date'].year == 2025
        assert result['end_date'].year == 2025


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
