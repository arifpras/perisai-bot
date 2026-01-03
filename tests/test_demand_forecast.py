"""
Test script for Auction Demand Forecasting module
"""
import pandas as pd
from auction_demand_forecast import AuctionDemandForecaster


def test_demand_forecaster():
    """Test basic functionality of AuctionDemandForecaster."""
    
    print("=" * 80)
    print("TESTING AUCTION DEMAND FORECASTER")
    print("=" * 80)
    print()
    
    try:
        # Initialize forecaster
        forecaster = AuctionDemandForecaster()
        print("✓ Forecaster initialized")
        
        # Load training data
        print("\n📚 Loading training data...")
        train_df = pd.read_excel('database/20251207_db01.xlsx', sheet_name='train_sbn')
        print(f"  Loaded {len(train_df)} historical records")
        print(f"  Features: {forecaster.FEATURE_COLUMNS}")
        print(f"  Target: {forecaster.TARGET_COLUMN}")
        
        # Train models
        print("\n🚀 Training ensemble models...")
        forecaster.train(train_df)
        
        # Load forecast data
        print("\n📊 Loading 2026 forecast data...")
        forecast_df = pd.read_excel('database/20251207_db01.xlsx', sheet_name='predict_sbn')
        print(f"  Loaded {len(forecast_df)} months for forecasting")
        
        # Generate 2026 forecast
        print("\n🔮 Generating 2026 demand forecast...")
        forecast_results = forecaster.get_2026_forecast(forecast_df)
        
        print("\n" + "=" * 80)
        print("📈 2026 FORECAST RESULTS")
        print("=" * 80)
        print(f"\nTotal Expected Incoming Bids (2026): {forecast_results['total_2026_billions']:,.2f} billion")
        print(f"Average Monthly: {forecast_results['average_monthly_billions']:,.2f} billion")
        
        print("\n📅 Monthly Breakdown:")
        print(f"{'Month':<15} {'Ensemble Mean':>15} {'Std Dev':>15} {'RF':>12} {'GB':>12}")
        print("-" * 70)
        for monthly in forecast_results['monthly']:
            if pd.notna(monthly['ensemble_mean_billions']):
                print(f"{monthly['month']:<15} {monthly['ensemble_mean_billions']:>15,.2f} "
                      f"{monthly['ensemble_std_billions']:>15,.2f} {monthly['rf_billions']:>12,.2f} "
                      f"{monthly['gb_billions']:>12,.2f}")
        
        print("\n📊 Model Performance:")
        print(f"{'Model':<25} {'R² Score':>15} {'MSE':>15}")
        print("-" * 55)
        for model_name, metrics in forecast_results['metrics'].items():
            print(f"{model_name:<25} {metrics['r2']:>15.4f} {metrics['mse']:>15.4f}")
        
        # Save models
        print("\n💾 Saving trained models...")
        forecaster.save("models")
        print("  ✓ Models saved to ./models/")
        
        # Test loading
        print("\n🔄 Testing model loading...")
        forecaster2 = AuctionDemandForecaster()
        forecaster2.load("models")
        print("  ✓ Models loaded successfully")
        
        # Predict with loaded model
        print("\n🔮 Making predictions with loaded model...")
        predictions = forecaster2.predict(forecast_df)
        print(f"  ✓ Generated predictions for {len(predictions)} months")
        
        print("\n✅ ALL TESTS PASSED!")
        print("=" * 80)
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
        print("   Make sure database/20251207_db01.xlsx exists with 'train_sbn' and 'predict_sbn' sheets")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_demand_forecaster()
