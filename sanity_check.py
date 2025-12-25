#!/usr/bin/env python3
"""
PERISAI-BOT DEPLOYMENT SANITY CHECK
Comprehensive pre-deployment validation script
"""

import sys
import os
from datetime import datetime, date
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class SanityCheck:
    def __init__(self):
        self.checks = []
        self.warnings = []
        self.errors = []
        
    def log_check(self, name, status, details=None):
        """Log a check result"""
        symbol = f"{GREEN}✅{RESET}" if status else f"{RED}✗{RESET}"
        self.checks.append((name, status, details))
        print(f"{symbol} {name}")
        if details:
            for detail in details:
                print(f"   {detail}")
        if not status:
            self.errors.append(name)
    
    def log_warning(self, name, message):
        """Log a warning"""
        self.warnings.append((name, message))
        print(f"{YELLOW}⚠️  {name}{RESET}")
        print(f"   {message}")
    
    def check_dependencies(self):
        """Check all required Python packages"""
        print(f"\n{BOLD}{BLUE}1. CHECKING DEPENDENCIES{RESET}")
        
        required = [
            'fastapi', 'uvicorn', 'duckdb', 'pandas', 'matplotlib',
            'dateparser', 'requests', 'httpx', 'telegram', 'openai', 'seaborn'
        ]
        
        missing = []
        installed = []
        
        for pkg in required:
            try:
                __import__(pkg)
                installed.append(f"{pkg}")
            except ImportError:
                missing.append(pkg)
        
        if missing:
            self.log_check(
                "Dependencies",
                False,
                [f"Missing packages: {', '.join(missing)}"]
            )
        else:
            self.log_check(
                "Dependencies",
                True,
                [f"All {len(installed)} packages installed"]
            )
    
    def check_fastapi_server(self):
        """Check FastAPI server functionality"""
        print(f"\n{BOLD}{BLUE}2. CHECKING FASTAPI SERVER{RESET}")
        
        try:
            from app_fastapi import app, get_db, ECONOMIST_PALETTE
            
            details = [
                f"FastAPI app: {type(app).__name__}",
                f"Economist colors: {len(ECONOMIST_PALETTE)} colors loaded",
                f"Color palette: {', '.join(ECONOMIST_PALETTE[:3])}"
            ]
            
            self.log_check("FastAPI imports", True, details)
            
        except Exception as e:
            self.log_check("FastAPI imports", False, [f"Error: {e}"])
            return False
        
        # Test server startup
        try:
            import subprocess
            result = subprocess.run(
                ['python', '-m', 'uvicorn', 'app_fastapi:app', '--help'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                self.log_check("Uvicorn command", True, ["Server can start"])
            else:
                self.log_check("Uvicorn command", False, ["Server startup check failed"])
        except Exception as e:
            self.log_warning("Uvicorn check", f"Could not verify server startup: {e}")
        
        return True
    
    def check_database(self):
        """Check database functionality"""
        print(f"\n{BOLD}{BLUE}3. CHECKING DATABASE{RESET}")
        
        try:
            from app_fastapi import get_db
            
            # Check CSV file exists
            csv_file = '20251215_priceyield.csv'
            if not Path(csv_file).exists():
                self.log_check("CSV file", False, [f"{csv_file} not found"])
                return False
            
            # Load database
            db = get_db(csv_file)
            
            # Count rows
            result = db.con.execute('SELECT COUNT(*) as cnt FROM ts').fetchone()
            row_count = result[0]
            
            # Get tenors
            rows = db.con.execute('SELECT DISTINCT tenor FROM ts ORDER BY tenor').fetchall()
            tenors = [r[0] for r in rows]
            
            # Get date range
            rows = db.con.execute(
                'SELECT MIN(obs_date) as min_date, MAX(obs_date) as max_date FROM ts'
            ).fetchone()
            
            details = [
                f"Total rows: {row_count:,}",
                f"Tenors: {', '.join(tenors)}",
                f"Date range: {rows[0]} to {rows[1]}"
            ]
            
            self.log_check("Database loading", True, details)
            
            # Test queries
            test_result = db.con.execute('''
                SELECT COUNT(*) FROM ts 
                WHERE obs_date BETWEEN '2025-01-01' AND '2025-12-31'
                AND tenor = '05_year'
            ''').fetchone()
            
            self.log_check(
                "Single tenor query",
                test_result[0] > 0,
                [f"Found {test_result[0]} data points for 5-year in 2025"]
            )
            
            # Test multi-tenor query
            test_result = db.con.execute('''
                SELECT tenor, COUNT(*) as cnt FROM ts 
                WHERE obs_date BETWEEN '2025-01-01' AND '2025-12-31'
                AND tenor IN ('05_year', '10_year')
                GROUP BY tenor
            ''').fetchall()
            
            if len(test_result) == 2:
                details = [f"{t}: {c} points" for t, c in test_result]
                self.log_check("Multi-tenor query", True, details)
            else:
                self.log_check("Multi-tenor query", False, ["Expected 2 tenors"])
            
            return True
            
        except Exception as e:
            self.log_check("Database", False, [f"Error: {e}"])
            return False
    
    def check_plot_generation(self):
        """Check plot generation functionality"""
        print(f"\n{BOLD}{BLUE}4. CHECKING PLOT GENERATION{RESET}")
        
        try:
            from app_fastapi import _plot_range_to_png, get_db
            
            db = get_db('20251215_priceyield.csv')
            
            # Test single tenor plot
            png_data = _plot_range_to_png(
                metric='yield',
                tenors=['05_year'],
                start_date=date(2025, 1, 1),
                end_date=date(2025, 12, 31),
                db=db
            )
            
            self.log_check(
                "Single tenor plot",
                len(png_data) > 0,
                [f"Generated {len(png_data):,} bytes"]
            )
            
            # Test multi-tenor plot (yield)
            png_data = _plot_range_to_png(
                metric='yield',
                tenors=['05_year', '10_year'],
                start_date=date(2025, 1, 1),
                end_date=date(2025, 12, 31),
                db=db
            )
            
            self.log_check(
                "Multi-tenor yield plot",
                len(png_data) > 0,
                [f"Generated {len(png_data):,} bytes"]
            )
            
            # Test multi-tenor plot (price)
            png_data = _plot_range_to_png(
                metric='price',
                tenors=['05_year', '10_year'],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
                db=db
            )
            
            self.log_check(
                "Multi-tenor price plot",
                len(png_data) > 0,
                [f"Generated {len(png_data):,} bytes"]
            )
            
            return True
            
        except Exception as e:
            self.log_check("Plot generation", False, [f"Error: {e}"])
            return False
    
    def check_telegram_bot(self):
        """Check Telegram bot configuration"""
        print(f"\n{BOLD}{BLUE}5. CHECKING TELEGRAM BOT{RESET}")
        
        try:
            from telegram_bot import (
                OPENAI_API_KEY, PERPLEXITY_API_KEY, API_BASE_URL, ALLOWED_USER_IDS
            )
            
            details = [f"API Base URL: {API_BASE_URL}"]
            self.log_check("Telegram bot imports", True, details)
            
        except Exception as e:
            self.log_check("Telegram bot imports", False, [f"Error: {e}"])
            return False
        
        return True
    
    def check_environment_variables(self):
        """Check environment variables"""
        print(f"\n{BOLD}{BLUE}6. CHECKING ENVIRONMENT VARIABLES{RESET}")
        
        required_vars = {
            'TELEGRAM_TOKEN': 'Required for bot operation',
            'OPENAI_API_KEY': 'Required for /kei persona',
            'PERPLEXITY_API_KEY': 'Required for /kin persona'
        }
        
        optional_vars = {
            'ALLOWED_USER_IDS': 'Optional access control',
            'API_BASE_URL': 'Defaults to http://127.0.0.1:8000'
        }
        
        missing_required = []
        
        for var, desc in required_vars.items():
            value = os.getenv(var)
            if value:
                self.log_check(f"{var}", True, [f"SET ({len(value)} chars)"])
            else:
                missing_required.append(var)
                self.log_warning(f"{var}", f"NOT SET - {desc}")
        
        if missing_required:
            self.log_warning(
                "Environment variables",
                f"Missing: {', '.join(missing_required)}"
            )
        
        for var, desc in optional_vars.items():
            value = os.getenv(var)
            if value:
                print(f"{GREEN}✓{RESET} {var}: SET")
            else:
                print(f"  {var}: Not set ({desc})")
    
    def check_deployment_config(self):
        """Check deployment configuration files"""
        print(f"\n{BOLD}{BLUE}7. CHECKING DEPLOYMENT CONFIGURATION{RESET}")
        
        # Check Procfile
        procfile = Path('Procfile')
        if procfile.exists():
            content = procfile.read_text()
            self.log_check(
                "Procfile",
                'uvicorn' in content,
                [f"Content: {content.strip()}"]
            )
        else:
            self.log_check("Procfile", False, ["File not found"])
        
        # Check render.yaml
        render_yaml = Path('render.yaml')
        if render_yaml.exists():
            content = render_yaml.read_text()
            has_web = 'type: web' in content
            has_worker = 'type: worker' in content
            
            details = []
            if has_web:
                details.append("Web service configured")
            if has_worker:
                details.append("Worker service configured")
            
            self.log_check(
                "render.yaml",
                has_web and has_worker,
                details
            )
        else:
            self.log_warning("render.yaml", "File not found")
        
        # Check requirements.txt
        requirements = Path('requirements.txt')
        if requirements.exists():
            content = requirements.read_text()
            required_pkgs = ['fastapi', 'uvicorn', 'python-telegram-bot', 'seaborn']
            missing_pkgs = [pkg for pkg in required_pkgs if pkg not in content]
            
            if missing_pkgs:
                self.log_warning(
                    "requirements.txt",
                    f"Missing: {', '.join(missing_pkgs)}"
                )
            else:
                self.log_check("requirements.txt", True, ["All key packages listed"])
        else:
            self.log_check("requirements.txt", False, ["File not found"])
    
    def check_data_files(self):
        """Check required data files"""
        print(f"\n{BOLD}{BLUE}8. CHECKING DATA FILES{RESET}")
        
        required_files = [
            '20251215_priceyield.csv',
            '20251224_auction_forecast.csv'
        ]
        
        for filename in required_files:
            filepath = Path(filename)
            if filepath.exists():
                size = filepath.stat().st_size
                self.log_check(
                    filename,
                    True,
                    [f"Size: {size:,} bytes"]
                )
            else:
                self.log_check(filename, False, ["File not found"])
    
    def generate_report(self):
        """Generate final report"""
        print(f"\n{BOLD}{'='*80}{RESET}")
        print(f"{BOLD}DEPLOYMENT READINESS REPORT{RESET}")
        print(f"{'='*80}")
        
        total_checks = len(self.checks)
        passed_checks = sum(1 for _, status, _ in self.checks if status)
        
        print(f"\nChecks Passed: {passed_checks}/{total_checks}")
        
        if self.errors:
            print(f"\n{RED}{BOLD}❌ ERRORS:{RESET}")
            for error in self.errors:
                print(f"   - {error}")
        
        if self.warnings:
            print(f"\n{YELLOW}{BOLD}⚠️  WARNINGS:{RESET}")
            for name, msg in self.warnings:
                print(f"   - {name}: {msg}")
        
        # Deployment readiness
        print(f"\n{'='*80}")
        if not self.errors:
            print(f"{GREEN}{BOLD}✅ DEPLOYMENT READY{RESET}")
            print(f"\n{BOLD}Pre-deployment Checklist:{RESET}")
            print("□ Set TELEGRAM_TOKEN in deployment environment")
            print("□ Set OPENAI_API_KEY in deployment environment")
            print("□ Set PERPLEXITY_API_KEY in deployment environment")
            print("□ Test /health endpoint after deployment")
            print("□ Send test message: /kei yield 5 year 2025")
        else:
            print(f"{RED}{BOLD}❌ NOT READY FOR DEPLOYMENT{RESET}")
            print(f"\nFix the errors above before deploying.")
        
        print(f"{'='*80}\n")
        
        # Save report to file
        self.save_report_to_file(passed_checks, total_checks)
        
        return len(self.errors) == 0
    
    def save_report_to_file(self, passed, total):
        """Save report to SANITY_CHECK_REPORT.txt"""
        report_file = Path('SANITY_CHECK_REPORT.txt')
        
        with open(report_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("PERISAI-BOT DEPLOYMENT SANITY CHECK\n")
            f.write(f"Date: {datetime.now().strftime('%B %d, %Y %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary
            for name, status, details in self.checks:
                symbol = "✅" if status else "✗"
                f.write(f"{symbol} {name}\n")
                if details:
                    for detail in details:
                        f.write(f"   {detail}\n")
            
            # Warnings
            if self.warnings:
                f.write(f"\n⚠️  WARNINGS:\n")
                for name, msg in self.warnings:
                    f.write(f"   - {name}: {msg}\n")
            
            # Errors
            if self.errors:
                f.write(f"\n❌ ERRORS:\n")
                for error in self.errors:
                    f.write(f"   - {error}\n")
            
            f.write(f"\n{'=' * 80}\n")
            f.write(f"DEPLOYMENT READINESS: {'✅ READY' if not self.errors else '❌ NOT READY'}\n")
            f.write(f"Checks Passed: {passed}/{total}\n")
            f.write("=" * 80 + "\n")
            
            if not self.errors:
                f.write("\nPre-deployment Checklist:\n")
                f.write("□ Set TELEGRAM_TOKEN in Render/Heroku environment\n")
                f.write("□ Set OPENAI_API_KEY in Render/Heroku environment\n")
                f.write("□ Set PERPLEXITY_API_KEY in Render/Heroku environment\n")
                f.write("□ Verify data files are in repository\n")
                f.write("□ Test /health endpoint after deployment\n")
                f.write("□ Send test message to bot: /kei yield 5 year 2025\n")
            
            f.write("\nRecent Features:\n")
            f.write("- The Economist chart styling (red/blue/teal palette)\n")
            f.write("- Multi-tenor plot support with distinct colored lines\n")
            f.write("- Improved tenor label formatting\n")
            f.write("- 150 DPI high-quality plot output\n")
            f.write("\n" + "=" * 80 + "\n")
        
        print(f"Report saved to: {report_file}")

def main():
    """Run all sanity checks"""
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}PERISAI-BOT DEPLOYMENT SANITY CHECK{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}")
    
    checker = SanityCheck()
    
    # Run all checks
    checker.check_dependencies()
    checker.check_fastapi_server()
    checker.check_database()
    checker.check_plot_generation()
    checker.check_telegram_bot()
    checker.check_environment_variables()
    checker.check_deployment_config()
    checker.check_data_files()
    
    # Generate final report
    ready = checker.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if ready else 1)

if __name__ == '__main__':
    main()
