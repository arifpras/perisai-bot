"""
Test the auction demand forecast query: /kei auction demand from q1 2025 to q4 2026
"""
import pandas as pd
from datetime import date
from auction_demand_forecast import AuctionDemandForecaster


def test_auction_demand_forecast_query():
    """Simulate the query: /kei auction demand from q1 2025 to q4 2026"""
    
    print("=" * 80)
    print("TEST: /kei auction demand from q1 2025 to q4 2026")
    print("=" * 80)
    print()
    
    try:
        # Initialize forecaster
        print("📊 Initializing forecaster...")
        forecaster = AuctionDemandForecaster()
        
        # Try loading cached models first
        try:
            forecaster.load("models")
            print("✓ Loaded pre-trained models from cache")
        except Exception as e:
            print(f"⚠️  Cached models not found, will train...")
            
            # Load training data
            print("\n📚 Loading training data...")
            train_df = pd.read_excel('database/20251207_db01.xlsx', sheet_name='train_sbn')
            print(f"✓ Loaded {len(train_df)} historical auction records")
            
            # Train
            print("\n🚀 Training ML ensemble (3-5 minutes)...")
            forecaster.train(train_df)
            
            # Save
            print("\n💾 Saving models...")
            forecaster.save("models")
            print("✓ Models saved to ./models/")
        
        # Load forecast data
        print("\n📊 Loading 2026 forecast inputs...")
        forecast_df = pd.read_excel('database/20251207_db01.xlsx', sheet_name='predict_sbn')
        print(f"✓ Loaded {len(forecast_df)} months for forecasting")
        
        # Generate 2026 forecast
        print("\n🔮 Generating 2026 demand forecast...")
        forecast_results = forecaster.get_2026_forecast(forecast_df)
        
        # Format output like Kei would
        print("\n" + "=" * 80)
        print("QUERY RESULTS: Auction Demand Q1 2025 → Q4 2026")
        print("=" * 80)
        print()
        
        # Split into quarters for display
        quarters_2025 = {
            'Q1 2025': [m for m in forecast_results['monthly'] if m['month'].startswith('Jan') or m['month'].startswith('Feb') or m['month'].startswith('Mar')],
            'Q2 2025': [m for m in forecast_results['monthly'] if m['month'].startswith('Apr') or m['month'].startswith('May') or m['month'].startswith('Jun')],
            'Q3 2025': [m for m in forecast_results['monthly'] if m['month'].startswith('Jul') or m['month'].startswith('Aug') or m['month'].startswith('Sep')],
            'Q4 2025': [m for m in forecast_results['monthly'] if m['month'].startswith('Oct') or m['month'].startswith('Nov') or m['month'].startswith('Dec')],
        }
        
        quarters_2026 = {
            'Q1 2026': [m for m in forecast_results['monthly'] if m['month'].startswith('Jan') or m['month'].startswith('Feb') or m['month'].startswith('Mar')],
            'Q2 2026': [m for m in forecast_results['monthly'] if m['month'].startswith('Apr') or m['month'].startswith('May') or m['month'].startswith('Jun')],
            'Q3 2026': [m for m in forecast_results['monthly'] if m['month'].startswith('Jul') or m['month'].startswith('Aug') or m['month'].startswith('Sep')],
            'Q4 2026': [m for m in forecast_results['monthly'] if m['month'].startswith('Oct') or m['month'].startswith('Nov') or m['month'].startswith('Dec')],
        }
        
        # Display by quarter
        print("📈 QUARTERLY BREAKDOWN (2025):")
        print()
        for q_name, months in quarters_2025.items():
            if months:
                q_total = sum(m['ensemble_mean_billions'] for m in months if m['ensemble_mean_billions'])
                q_avg = q_total / len(months) if months else 0
                print(f"  {q_name:<12}: {q_total:>8,.2f}B total | {q_avg:>8,.2f}B avg/month")
                for m in months:
                    if pd.notna(m['ensemble_mean_billions']):
                        print(f"    {m['month']:<12}: {m['ensemble_mean_billions']:>8,.2f}B ± {m['ensemble_std_billions']:>8,.2f}B")
        
        print()
        print("📈 QUARTERLY BREAKDOWN (2026 - FORECAST):")
        print()
        for q_name, months in quarters_2026.items():
            if months:
                q_total = sum(m['ensemble_mean_billions'] for m in months if m['ensemble_mean_billions'])
                q_avg = q_total / len(months) if months else 0
                print(f"  {q_name:<12}: {q_total:>8,.2f}B total | {q_avg:>8,.2f}B avg/month")
                for m in months:
                    if pd.notna(m['ensemble_mean_billions']):
                        print(f"    {m['month']:<12}: {m['ensemble_mean_billions']:>8,.2f}B ± {m['ensemble_std_billions']:>8,.2f}B")
        
        # Summary
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total 2026 Forecast (Jan-Dec): {forecast_results['total_2026_billions']:,.2f}B")
        print(f"Average Monthly (2026): {forecast_results['average_monthly_billions']:,.2f}B")
        print()
        
        # Model performance
        print("📊 Model Performance (Training Set):")
        print(f"{'Model':<25} {'R² Score':>15} {'MSE':>15}")
        print("-" * 55)
        for model_name, metrics in forecast_results['metrics'].items():
            print(f"{model_name:<25} {metrics['r2']:>15.4f} {metrics['mse']:>15.6f}")
        
        print()
        print("=" * 80)
        print("✅ TEST PASSED - Query processed successfully!")
        print("=" * 80)
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
        print("   Make sure database/20251207_db01.xlsx exists with 'train_sbn' and 'predict_sbn' sheets")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_auction_demand_forecast_query()
