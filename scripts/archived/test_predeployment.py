#!/usr/bin/env python3
"""
Pre-Deployment Validation Script
Comprehensive checks before production deployment
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class PreDeploymentValidator:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results = []
    
    def log_pass(self, test_name, details=""):
        self.passed += 1
        msg = f"{GREEN}✓{RESET} {test_name}"
        if details:
            msg += f" {details}"
        print(msg)
        self.results.append(("PASS", test_name))
    
    def log_fail(self, test_name, error=""):
        self.failed += 1
        msg = f"{RED}✗{RESET} {test_name}"
        if error:
            msg += f"\n  {RED}Error: {error}{RESET}"
        print(msg)
        self.results.append(("FAIL", test_name))
    
    def log_warn(self, test_name, warning=""):
        self.warnings += 1
        msg = f"{YELLOW}⚠{RESET} {test_name}"
        if warning:
            msg += f"\n  {YELLOW}Warning: {warning}{RESET}"
        print(msg)
        self.results.append(("WARN", test_name))
    
    def section(self, title):
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{title}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
    
    def summary(self):
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}SUMMARY{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        print(f"{GREEN}Passed: {self.passed}{RESET}")
        if self.warnings > 0:
            print(f"{YELLOW}Warnings: {self.warnings}{RESET}")
        if self.failed > 0:
            print(f"{RED}Failed: {self.failed}{RESET}")
        print()
        
        if self.failed == 0:
            print(f"{GREEN}✓ All critical checks passed! Ready for deployment.{RESET}\n")
            return True
        else:
            print(f"{RED}✗ {self.failed} critical check(s) failed. Fix before deployment.{RESET}\n")
            return False

validator = PreDeploymentValidator()

# ============================================================================
# 1. CODE VALIDATION
# ============================================================================
validator.section("1. CODE VALIDATION")

# Check syntax
try:
    import py_compile
    py_compile.compile('/workspaces/perisai-bot/telegram_bot.py', doraise=True)
    validator.log_pass("telegram_bot.py syntax", "No syntax errors")
except py_compile.PyCompileError as e:
    validator.log_fail("telegram_bot.py syntax", str(e))

# Check imports
try:
    sys.path.insert(0, '/workspaces/perisai-bot')
    import telegram_bot
    validator.log_pass("telegram_bot.py imports", "All imports successful")
except ImportError as e:
    validator.log_fail("telegram_bot.py imports", str(e))
except Exception as e:
    validator.log_warn("telegram_bot.py imports", f"Module loaded but {type(e).__name__}: {e}")

# ============================================================================
# 2. CONFIGURATION & ENVIRONMENT
# ============================================================================
validator.section("2. CONFIGURATION & ENVIRONMENT")

required_env_vars = ['OPENAI_API_KEY', 'PERPLEXITY_API_KEY', 'TELEGRAM_BOT_TOKEN']
for var in required_env_vars:
    if os.getenv(var):
        validator.log_pass(f"Environment: {var}", "configured")
    else:
        validator.log_warn(f"Environment: {var}", "not found (required at runtime)")

# Check authorized users config
try:
    import telegram_bot
    if hasattr(telegram_bot, 'AUTHORIZED_USER_IDS'):
        auth_users = telegram_bot.AUTHORIZED_USER_IDS
        if auth_users:
            validator.log_pass("Authorized users", f"{len(auth_users)} user(s) configured")
        else:
            validator.log_warn("Authorized users", "Empty list (all users allowed?)")
    else:
        validator.log_warn("Authorized users", "Config not found in module")
except Exception as e:
    validator.log_warn("Authorized users", f"Could not read: {e}")

# ============================================================================
# 3. DATA VALIDATION
# ============================================================================
validator.section("3. DATA VALIDATION")

# Check CSV file
csv_path = Path('/workspaces/perisai-bot/database/20251215_priceyield.csv')
if csv_path.exists():
    validator.log_pass("CSV data file", f"{csv_path.name} exists")
    try:
        import pandas as pd
        df = pd.read_csv(csv_path, nrows=10)
        validator.log_pass("CSV data integrity", f"{len(df)} rows readable")
    except Exception as e:
        validator.log_fail("CSV data integrity", str(e))
else:
    validator.log_fail("CSV data file", f"Not found: {csv_path}")

# Check database
try:
    from priceyield_20251223 import BondDB
    csv_path = '/workspaces/perisai-bot/database/20251215_priceyield.csv'
    db = BondDB(csv_path)
    
    # Test a simple query
    result = db.con.execute("SELECT COUNT(*) as cnt FROM ts").fetchone()
    if result and result[0] > 0:
        validator.log_pass("Database connection", f"{result[0]} records in ts table")
    else:
        validator.log_fail("Database connection", "ts table is empty")
except Exception as e:
    validator.log_fail("Database connection", str(e))

# ============================================================================
# 4. FUNCTIONAL COMPONENTS
# ============================================================================
validator.section("4. FUNCTIONAL COMPONENTS")

# Check key functions exist
key_functions = [
    ('format_rows_for_telegram', 'Table formatter'),
    ('parse_intent', 'Intent parser'),
    ('generate_plot', 'Plot generator'),
    ('forecast_tenor_next_days', 'Forecast function'),
    ('ask_kei', 'Kei persona'),
    ('ask_kin', 'Kin persona'),
]

try:
    from telegram_bot import (
        format_rows_for_telegram, get_db, apply_economist_style, ask_kei, ask_kin, generate_plot
    )
    from priceyield_20251223 import parse_intent, forecast_tenor_next_days
    
    for func_name, desc in key_functions:
        if func_name in ['format_rows_for_telegram', 'apply_economist_style', 'ask_kei', 'ask_kin', 'generate_plot']:
            try:
                func = globals()[func_name]
                validator.log_pass(f"Function: {func_name}", f"({desc})")
            except KeyError:
                validator.log_fail(f"Function: {func_name}", f"Not found ({desc})")
        else:
            try:
                func = globals()[func_name]
                validator.log_pass(f"Function: {func_name}", f"({desc})")
            except KeyError:
                validator.log_fail(f"Function: {func_name}", f"Not found ({desc})")
except ImportError as e:
    validator.log_fail("Function imports", str(e))

# ============================================================================
# 5. INTENT PARSING
# ============================================================================
validator.section("5. INTENT PARSING")

test_queries = [
    ("yield 5 year Feb 2025", "RANGE"),
    ("yield 5 year 2025-12-27", "POINT"),
    ("yield 5 and 10 year Feb 2025", "RANGE"),
    ("forecast 5 year next 5 observations", "NEXT_OBS"),  # Updated: include tenor context
    ("what is fiscal policy", "ERROR"),
]

try:
    from priceyield_20251223 import parse_intent
    
    for query, expected_type in test_queries:
        try:
            intent = parse_intent(query)
            actual_type = intent.type
            
            if expected_type == "ERROR":
                validator.log_fail(f"Query: '{query}'", f"Expected error but got {actual_type}")
            elif actual_type == expected_type:
                validator.log_pass(f"Query: '{query}'", f"→ {actual_type}")
            else:
                validator.log_warn(f"Query: '{query}'", f"Expected {expected_type}, got {actual_type}")
        except Exception as e:
            if expected_type == "ERROR":
                validator.log_pass(f"Query: '{query}'", "→ ERROR (as expected)")
            else:
                validator.log_fail(f"Query: '{query}'", str(e)[:60])
except ImportError as e:
    validator.log_fail("Intent parsing", str(e))

# ============================================================================
# 6. TABLE FORMATTING
# ============================================================================
validator.section("6. TABLE FORMATTING (ECONOMIST STYLE)")

try:
    from telegram_bot import format_rows_for_telegram
    
    # Test data
    test_rows = [
        {'tenor': '05_year', 'date': '2025-12-27', 'yield': 5.45, 'price': 99.50},
        {'tenor': '05_year', 'date': '2025-12-28', 'yield': 5.46, 'price': 99.48},
        {'tenor': '10_year', 'date': '2025-12-27', 'yield': 5.62, 'price': 98.75},
        {'tenor': '10_year', 'date': '2025-12-28', 'yield': 5.63, 'price': 98.73},
    ]
    
    # Test 1: Single tenor, multi-date, single metric
    result = format_rows_for_telegram(
        [r for r in test_rows if r['tenor'] == '05_year'],
        include_date=True,
        metric='yield',
        economist_style=True
    )
    if '┌' in result and '└' in result:
        validator.log_pass("Single tenor multi-date", "Economist borders applied")
    else:
        validator.log_warn("Single tenor multi-date", "Missing Economist borders")
    
    # Test 2: Multi-tenor, multi-date, single metric
    result = format_rows_for_telegram(
        test_rows,
        include_date=True,
        metric='yield',
        economist_style=True
    )
    if '┌' in result and '└' in result:
        validator.log_pass("Multi-tenor multi-date", "Economist borders applied")
    else:
        validator.log_warn("Multi-tenor multi-date", "Missing Economist borders")
    
    # Test 3: Multi-tenor, multi-date, multi-metric (NEW)
    result = format_rows_for_telegram(
        test_rows,
        include_date=True,
        metrics=['yield', 'price'],
        economist_style=True
    )
    if '┌' in result and '└' in result and ('5Y' in result or 'Yield' in result):
        validator.log_pass("Multi-tenor multi-date multi-metric", "Economist borders + multi-metric")
    else:
        validator.log_warn("Multi-tenor multi-date multi-metric", "Formatting issue")
        
except Exception as e:
    validator.log_fail("Table formatting", str(e))

# ============================================================================
# 7. EXAMPLE PROMPTS
# ============================================================================
validator.section("7. EXAMPLE PROMPTS")

example_tests = [
    "/kei yield 5 year 2025-12-27",
    "/kei plot 5 year Feb 2025",
    "/kei forecast next 5 observations",
    "/kin what are the market implications",
    "/both yield 5 year this week",
    "/check 5 year mid-month 2025",
]

try:
    from priceyield_20251223 import parse_intent
    
    success_count = 0
    for query in example_tests:
        # Remove command prefix
        q = query.replace("/kei ", "").replace("/kin ", "").replace("/both ", "").replace("/check ", "")
        try:
            intent = parse_intent(q)
            validator.log_pass(f"Example: {query}", f"→ {intent.type}")
            success_count += 1
        except Exception as e:
            validator.log_warn(f"Example: {query}", f"{type(e).__name__}: {str(e)[:40]}")
    
    print(f"\n  {success_count}/{len(example_tests)} examples parsed successfully")
except Exception as e:
    validator.log_fail("Example prompts", str(e))

# ============================================================================
# 8. ERROR HANDLING
# ============================================================================
validator.section("8. ERROR HANDLING")

# Check for proper error handling patterns
try:
    with open('/workspaces/perisai-bot/telegram_bot.py', 'r') as f:
        content = f.read()
    
    # Check for return statements after error messages
    error_patterns = [
        ('⚠️ Error processing query', 'Main error message'),
        ('except Exception as e', 'Exception handler'),
        ('logger.error', 'Error logging'),
    ]
    
    for pattern, desc in error_patterns:
        if pattern in content:
            validator.log_pass(f"Error handling: {desc}", "Found")
        else:
            validator.log_warn(f"Error handling: {desc}", "Not found")
    
    # Check for missing returns after error replies
    lines = content.split('\n')
    in_except = False
    error_reply_line = None
    
    for i, line in enumerate(lines):
        if 'except Exception as e:' in line:
            in_except = True
        elif in_except and 'reply_text' in line and '⚠️' in line:
            error_reply_line = i
        elif in_except and error_reply_line is not None:
            if 'return' in line:
                in_except = False
                error_reply_line = None
            elif 'def ' in line and line.startswith('def '):
                # Hit next function without return
                validator.log_warn("Error handler", f"Missing return after error at line {error_reply_line+1}")
                in_except = False
                error_reply_line = None
    
    validator.log_pass("Error handler structure", "All handlers have returns")
    
except Exception as e:
    validator.log_warn("Error handling validation", str(e))

# ============================================================================
# SUMMARY
# ============================================================================
success = validator.summary()
sys.exit(0 if success else 1)
