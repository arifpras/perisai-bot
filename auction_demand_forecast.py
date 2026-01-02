"""
Auction Demand Forecasting: ML Ensemble Approach

Forecasts incoming bids (auction demand) for 2026 using an ensemble of machine learning models.
Combines predictions from Random Forest, Gradient Boosting, AdaBoost, Linear Regression, and Stepwise Regression.

Key Features:
- Trains on historical auction data (train_sbn sheet)
- Uses 6 macroeconomic and auction-specific features
- Provides ensemble predictions with model uncertainty
- Generates monthly forecasts for 2026
"""

import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV

import statsmodels.api as sm


class AuctionDemandForecaster:
    """
    Ensemble forecasting model for auction incoming bids.
    
    Models:
    - Random Forest (ensemble tree-based)
    - Gradient Boosting (sequential ensemble)
    - AdaBoost (adaptive boosting)
    - Linear Regression (baseline)
    - Stepwise Regression (statistical feature selection)
    """
    
    # Features and target for demand forecasting
    FEATURE_COLUMNS = ['number_series', 'dpk_bio_log', 'move', 'auction_month', 'long_holiday', 'inflation_rate']
    TARGET_COLUMN = 'incoming_bio_log'
    
    def __init__(self):
        """Initialize forecaster with empty models and scaler."""
        self.models = {}
        self.scaler = StandardScaler()
        self.stepwise_model = None
        self.stepwise_features = None
        self.metrics = {}
        self.feature_importances = {}
        self.is_fitted = False
    
    def train(self, train_data: pd.DataFrame, test_size=0.2, random_state=42):
        """
        Train ensemble models on historical auction data.
        
        Args:
            train_data: DataFrame with historical auction data (train_sbn sheet)
            test_size: Fraction for test set (default 0.2)
            random_state: Seed for reproducibility
        """
        print("🚀 Starting Auction Demand Forecast Training...")
        
        # Prepare features and target
        X = train_data[self.FEATURE_COLUMNS].copy()
        y = train_data[self.TARGET_COLUMN].copy()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Standardize features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Convert to DataFrames for compatibility
        X_train_scaled = pd.DataFrame(X_train_scaled, index=X_train.index, columns=self.FEATURE_COLUMNS)
        X_test_scaled = pd.DataFrame(X_test_scaled, index=X_test.index, columns=self.FEATURE_COLUMNS)
        
        # Define models with hyperparameters
        models_config = {
            "Random Forest": RandomForestRegressor(
                n_estimators=200, max_depth=20, min_samples_split=5, 
                min_samples_leaf=2, random_state=random_state
            ),
            "Gradient Boosting": GradientBoostingRegressor(
                n_estimators=200, learning_rate=0.1, max_depth=5, 
                subsample=0.8, random_state=random_state
            ),
            "AdaBoost": AdaBoostRegressor(
                n_estimators=100, learning_rate=0.1, random_state=random_state
            ),
            "Linear Regression": LinearRegression(),
        }
        
        # Train models
        for model_name, model in models_config.items():
            print(f"  Training {model_name}...", end=" ")
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            
            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            self.models[model_name] = model
            self.metrics[model_name] = {'mse': mse, 'r2': r2}
            
            # Feature importance
            if hasattr(model, 'feature_importances_'):
                self.feature_importances[model_name] = model.feature_importances_
            
            print(f"✓ MSE={mse:.4f}, R²={r2:.4f}")
        
        # Train Stepwise Regression
        print(f"  Training Stepwise Regression...", end=" ")
        self.stepwise_features = self._stepwise_selection(X_train_scaled, y_train)
        
        X_train_stepwise = sm.add_constant(X_train_scaled[self.stepwise_features])
        self.stepwise_model = sm.OLS(y_train, X_train_stepwise).fit(cov_type='HC0')
        
        X_test_stepwise = sm.add_constant(X_test_scaled[self.stepwise_features], has_constant='add')
        y_pred_stepwise = self.stepwise_model.predict(X_test_stepwise)
        
        mse_stepwise = mean_squared_error(y_test, y_pred_stepwise)
        r2_stepwise = r2_score(y_test, y_pred_stepwise)
        self.metrics["Stepwise Regression"] = {'mse': mse_stepwise, 'r2': r2_stepwise}
        
        print(f"✓ MSE={mse_stepwise:.4f}, R²={r2_stepwise:.4f}")
        
        # Linear regression coefficients for feature importance
        lr_model = self.models["Linear Regression"]
        self.feature_importances["Linear Regression"] = np.abs(lr_model.coef_) / np.sum(np.abs(lr_model.coef_))
        
        self.is_fitted = True
        print("\n✅ Training Complete!\n")
        self._print_model_ranking()
    
    def predict(self, new_data: pd.DataFrame) -> pd.DataFrame:
        """
        Forecast incoming bids using ensemble of trained models.
        
        Args:
            new_data: DataFrame with features for prediction (predict_sbn sheet)
        
        Returns:
            DataFrame with predictions from all models and ensemble mean
        """
        if not self.is_fitted:
            raise ValueError("Model must be trained before prediction. Call train() first.")
        
        # Standardize features
        new_data_scaled = self.scaler.transform(new_data[self.FEATURE_COLUMNS])
        new_data_scaled = pd.DataFrame(new_data_scaled, columns=self.FEATURE_COLUMNS)
        
        # Get predictions from each model
        predictions = {}
        for model_name, model in self.models.items():
            predictions[model_name] = model.predict(new_data_scaled)
        
        # Stepwise regression predictions
        new_data_stepwise = sm.add_constant(new_data_scaled[self.stepwise_features], has_constant='add')
        predictions["Stepwise Regression"] = self.stepwise_model.predict(new_data_stepwise)
        
        # Create results DataFrame
        results = new_data.copy()
        for model_name, preds in predictions.items():
            results[model_name] = preds
        
        # Add ensemble mean and std
        all_predictions = np.column_stack([predictions[m] for m in predictions.keys()])
        results['ensemble_mean'] = np.mean(all_predictions, axis=1)
        results['ensemble_std'] = np.std(all_predictions, axis=1)
        
        return results
    
    def convert_to_billions(self, log_values: np.ndarray) -> np.ndarray:
        """Convert log-scale values back to billions."""
        return 10 ** log_values
    
    def get_2026_forecast(self, forecast_data: pd.DataFrame) -> dict:
        """
        Generate 2026 monthly forecast summary.
        
        Args:
            forecast_data: DataFrame with 2026 monthly data (predict_sbn sheet)
        
        Returns:
            Dictionary with monthly and total forecasts
        """
        predictions_df = self.predict(forecast_data)
        
        # Convert from log scale to billions
        for col in ['Random Forest', 'Gradient Boosting', 'AdaBoost', 'Linear Regression', 'Stepwise Regression', 'ensemble_mean']:
            if col in predictions_df.columns:
                predictions_df[f'{col}_billions'] = self.convert_to_billions(predictions_df[col])
        
        # Create monthly summary
        months = pd.date_range(start='2026-01-01', end='2026-12-31', freq='M')
        monthly_forecast = []
        
        for idx, month in enumerate(months):
            if idx < len(predictions_df):
                row = predictions_df.iloc[idx]
                monthly_forecast.append({
                    'month': month.strftime('%B %Y'),
                    'date': month.date(),
                    'ensemble_mean_billions': row.get('ensemble_mean_billions', np.nan),
                    'ensemble_std_billions': row.get('ensemble_std_billions', np.nan),
                    'rf_billions': row.get('Random Forest_billions', np.nan),
                    'gb_billions': row.get('Gradient Boosting_billions', np.nan),
                    'ada_billions': row.get('AdaBoost_billions', np.nan),
                })
        
        # Calculate totals
        total_ensemble = sum(m['ensemble_mean_billions'] for m in monthly_forecast if not np.isnan(m['ensemble_mean_billions']))
        
        return {
            'monthly': monthly_forecast,
            'total_2026_billions': total_ensemble,
            'average_monthly_billions': total_ensemble / len(monthly_forecast),
            'metrics': self.metrics
        }
    
    def save(self, output_dir: str = "models"):
        """Save trained models and scaler to disk."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save scaler
        joblib.dump(self.scaler, output_path / "demand_scaler.pkl")
        
        # Save sklearn models
        for name, model in self.models.items():
            joblib.dump(model, output_path / f"demand_{name.lower().replace(' ', '_')}.pkl")
        
        # Save stepwise model (statsmodels)
        joblib.dump(self.stepwise_model, output_path / "demand_stepwise_model.pkl")
        joblib.dump(self.stepwise_features, output_path / "demand_stepwise_features.pkl")
        
        # Save metadata
        metadata = {
            'feature_columns': self.FEATURE_COLUMNS,
            'target_column': self.TARGET_COLUMN,
            'metrics': self.metrics,
            'trained_date': datetime.now().isoformat()
        }
        joblib.dump(metadata, output_path / "demand_metadata.pkl")
        
        print(f"✅ Models saved to {output_path}/")
    
    def load(self, model_dir: str = "models"):
        """Load trained models and scaler from disk."""
        model_path = Path(model_dir)
        
        # Load scaler
        self.scaler = joblib.load(model_path / "demand_scaler.pkl")
        
        # Load sklearn models
        for name in ["Random Forest", "Gradient Boosting", "AdaBoost", "Linear Regression"]:
            model_file = model_path / f"demand_{name.lower().replace(' ', '_')}.pkl"
            if model_file.exists():
                self.models[name] = joblib.load(model_file)
        
        # Load stepwise model
        if (model_path / "demand_stepwise_model.pkl").exists():
            self.stepwise_model = joblib.load(model_path / "demand_stepwise_model.pkl")
            self.stepwise_features = joblib.load(model_path / "demand_stepwise_features.pkl")
        
        # Load metadata
        if (model_path / "demand_metadata.pkl").exists():
            metadata = joblib.load(model_path / "demand_metadata.pkl")
            self.metrics = metadata.get('metrics', {})
        
        self.is_fitted = True
        print(f"✅ Models loaded from {model_path}/")
    
    def _stepwise_selection(self, X, y, threshold_in=0.09, threshold_out=0.09):
        """Forward-backward stepwise feature selection."""
        included = []
        while True:
            changed = False
            
            # Forward step
            excluded = list(set(X.columns) - set(included))
            new_pval = pd.Series(index=excluded)
            for col in excluded:
                model = sm.OLS(y, sm.add_constant(X[included + [col]])).fit()
                new_pval[col] = model.pvalues[col]
            best_pval = new_pval.min()
            if best_pval < threshold_in:
                best_feature = new_pval.idxmin()
                included.append(best_feature)
                changed = True
            
            # Backward step
            if included:
                model = sm.OLS(y, sm.add_constant(X[included])).fit()
                pvalues = model.pvalues.iloc[1:]  # Exclude intercept
                if len(pvalues) > 0:
                    worst_pval = pvalues.max()
                    if worst_pval > threshold_out:
                        changed = True
                        worst_feature = pvalues.idxmax()
                        included.remove(worst_feature)
            
            if not changed:
                break
        
        return included
    
    def _print_model_ranking(self):
        """Print models ranked by R² score."""
        print("📊 Model Performance Ranking:")
        sorted_metrics = sorted(self.metrics.items(), key=lambda x: x[1]['r2'], reverse=True)
        for rank, (model_name, metrics) in enumerate(sorted_metrics, 1):
            print(f"  {rank}. {model_name:25s} | R² = {metrics['r2']:.4f} | MSE = {metrics['mse']:.4f}")


if __name__ == "__main__":
    # Example usage
    import openpyxl
    
    print("=" * 70)
    print("AUCTION DEMAND FORECASTING SYSTEM")
    print("=" * 70)
    print()
    
    # Load training data
    try:
        train_file = "20251207_db01.xlsx"  # Update path as needed
        train_data = pd.read_excel(train_file, sheet_name='train_sbn')
        forecast_data = pd.read_excel(train_file, sheet_name='predict_sbn')
        
        # Initialize and train
        forecaster = AuctionDemandForecaster()
        forecaster.train(train_data)
        
        # Generate 2026 forecast
        forecast_results = forecaster.get_2026_forecast(forecast_data)
        
        print("\n📈 2026 FORECAST SUMMARY:")
        print(f"  Total Expected Incoming Bids (2026): {forecast_results['total_2026_billions']:,.2f} billion")
        print(f"  Average Monthly: {forecast_results['average_monthly_billions']:,.2f} billion")
        print()
        
        # Save models
        forecaster.save("models")
        
    except FileNotFoundError as e:
        print(f"⚠️  Data file not found: {e}")
        print("   Update the file path and run again.")
