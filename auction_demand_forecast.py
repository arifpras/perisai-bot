"""
Auction Demand Forecasting: ML Ensemble Approach

Forecasts incoming bids (auction demand) for 2026 using an ensemble of machine learning models.
Combines predictions from Random Forest, Gradient Boosting, AdaBoost, Linear Regression, and Stepwise Regression.

Key Features:
- Trains on historical auction data (train_sbn sheet)
- Uses 6 macroeconomic and auction-specific features
- Provides ensemble predictions with model uncertainty
- Hyperparameters tuned via GridSearchCV (see 20251208_podem2026_sbn_v01.ipynb)
- Generates monthly forecasts for 2026 with 4-model ensemble average
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
        
        # Define hyperparameter grids (from notebook GridSearchCV tuning)
        param_grids = {
            "Random Forest": {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            },
            "Gradient Boosting": {
                'n_estimators': [100, 150, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7],
                'subsample': [0.8, 1.0]
            },
            "AdaBoost": {
                'n_estimators': [50, 100, 150],
                'learning_rate': [0.01, 0.1, 1.0]
            },
        }
        
        # Initialize base models (without hyperparameters)
        base_models = {
            "Random Forest": RandomForestRegressor(random_state=random_state),
            "Gradient Boosting": GradientBoostingRegressor(random_state=random_state),
            "AdaBoost": AdaBoostRegressor(random_state=random_state),
            "Linear Regression": LinearRegression(),
        }
        
        # Train models with GridSearchCV tuning
        for model_name, model in base_models.items():
            if model_name in param_grids:
                print(f"  Tuning {model_name}...", end=" ")
                grid_search = GridSearchCV(
                    model, 
                    param_grids[model_name], 
                    cv=5, 
                    scoring='neg_mean_squared_error', 
                    verbose=0
                )
                grid_search.fit(X_train_scaled, y_train)
                tuned_model = grid_search.best_estimator_
                self.models[model_name] = tuned_model
                print(f"✓ Best params: {grid_search.best_params_}")
            else:
                print(f"  Training {model_name}...", end=" ")
                model.fit(X_train_scaled, y_train)
                self.models[model_name] = model
                print(f"✓")
            
            # Calculate metrics
            y_pred = self.models[model_name].predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            self.metrics[model_name] = {'mse': mse, 'r2': r2}
            
            # Feature importance
            if hasattr(self.models[model_name], 'feature_importances_'):
                self.feature_importances[model_name] = self.models[model_name].feature_importances_
            
            print(f"    MSE={mse:.4f}, R²={r2:.4f}")
        
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
        
        # Add ensemble mean and std (in log scale)
        all_predictions = np.column_stack([predictions[m] for m in ['Random Forest', 'Gradient Boosting', 'AdaBoost', 'Stepwise Regression']])
        results['ensemble_mean'] = np.mean(all_predictions, axis=1)
        results['ensemble_std'] = np.std(all_predictions, axis=1)
        
        # Convert ensemble mean to billions
        results['ensemble_mean_billions'] = self.convert_to_billions(results['ensemble_mean'])
        results['ensemble_std_billions'] = results['ensemble_std']  # Std stays in log scale
        
        return results
    
    def convert_to_billions(self, log_values: np.ndarray) -> np.ndarray:
        """Convert log-scale values back to billions."""
        return 10 ** log_values
    
    def get_2026_forecast(self, forecast_data: pd.DataFrame) -> dict:
        """
        Generate 2026 monthly forecast summary.
        
        Generates predictions using all 4 models (AdaBoost, Stepwise Regression, 
        Gradient Boosting, Random Forest) and computes ensemble average.
        
        Args:
            forecast_data: DataFrame with 2026 monthly data (predict_sbn sheet)
        
        Returns:
            Dictionary with monthly predictions from each model and ensemble mean
        """
        predictions_df = self.predict(forecast_data)
        
        # Convert from log scale to billions for all models
        model_cols = ['Random Forest', 'Gradient Boosting', 'AdaBoost', 'Linear Regression', 'Stepwise Regression']
        for col in model_cols:
            if col in predictions_df.columns:
                predictions_df[f'{col}_billions'] = self.convert_to_billions(predictions_df[col])
        
        # Create monthly summary with predictions from each model
        months = pd.date_range(start='2026-01-01', end='2026-12-31', freq='M')
        monthly_forecast = []
        
        # Extract only 2026 data (skip if Dec 2025 exists at index 0)
        forecast_2026 = predictions_df
        if len(forecast_2026) > 12 and 'date' in forecast_2026.columns:
            forecast_2026 = forecast_2026[forecast_2026['date'].dt.year == 2026].reset_index(drop=True)
        elif len(forecast_2026) > 12:
            forecast_2026 = forecast_2026.iloc[-12:].reset_index(drop=True)
        
        for idx, month in enumerate(months):
            if idx < len(forecast_2026):
                row = forecast_2026.iloc[idx]
                monthly_forecast.append({
                    'month': month.strftime('%B %Y'),
                    'month_num': month.month,
                    'date': month.date(),
                    'adaboost_billions': row.get('AdaBoost_billions', np.nan),
                    'stepwise_billions': row.get('Stepwise Regression_billions', np.nan),
                    'gradient_boosting_billions': row.get('Gradient Boosting_billions', np.nan),
                    'random_forest_billions': row.get('Random Forest_billions', np.nan),
                    'ensemble_mean_billions': row.get('ensemble_mean_billions', np.nan),
                })
        
        # Calculate totals
        model_forecasts = {
            'AdaBoost': sum(m['adaboost_billions'] for m in monthly_forecast if not np.isnan(m['adaboost_billions'])),
            'Stepwise Regression': sum(m['stepwise_billions'] for m in monthly_forecast if not np.isnan(m['stepwise_billions'])),
            'Gradient Boosting': sum(m['gradient_boosting_billions'] for m in monthly_forecast if not np.isnan(m['gradient_boosting_billions'])),
            'Random Forest': sum(m['random_forest_billions'] for m in monthly_forecast if not np.isnan(m['random_forest_billions'])),
        }
        
        total_ensemble = sum(m['ensemble_mean_billions'] for m in monthly_forecast if not np.isnan(m['ensemble_mean_billions']))
        ensemble_avg = total_ensemble / len(monthly_forecast) if monthly_forecast else 0
        
        return {
            'monthly': monthly_forecast,
            'total_2026_billions': total_ensemble,
            'average_monthly_billions': ensemble_avg,
            'total_by_model': model_forecasts,
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
    """
    Main execution: Train ensemble models and forecast 2026 monthly incoming bids.
    
    Data files:
    - Training: database/auction_train.csv
    - Prediction features: database/auction_predict.csv
    - Output: database/auction_forecast.csv
    """
    import os
    from pathlib import Path
    
    print("=" * 80)
    print("2026 AUCTION DEMAND FORECASTING - MONTHLY BASIS")
    print("=" * 80)
    print()
    
    # File paths
    train_file = "database/auction_train.csv"
    predict_file = "database/auction_predict.csv"
    output_file = "database/auction_forecast.csv"
    
    # Verify input files exist
    for f in [train_file, predict_file]:
        if not Path(f).exists():
            print(f"❌ Error: {f} not found!")
            exit(1)
    
    print(f"✓ Loading training data from {train_file}")
    train_data = pd.read_csv(train_file)
    print(f"  Loaded {len(train_data)} historical records")
    
    print(f"✓ Loading 2026 prediction features from {predict_file}")
    predict_data = pd.read_csv(predict_file)
    print(f"  Loaded {len(predict_data)} months for 2026")
    print()
    
    # Initialize forecaster
    forecaster = AuctionDemandForecaster()
    
    # Train models
    print("🚀 Training ensemble models...")
    forecaster.train(train_data, test_size=0.2, random_state=42)
    print()
    
    # Generate predictions
    print("📊 Generating 2026 monthly forecasts...")
    predictions_df = forecaster.predict(predict_data)
    print(f"  Generated predictions for {len(predictions_df)} months")
    print()
    
    # Convert log-scale predictions to billions for all models
    for model_name in ['Random Forest', 'Gradient Boosting', 'AdaBoost', 'Stepwise Regression']:
        if model_name in predictions_df.columns:
            predictions_df[f'{model_name}_billions'] = forecaster.convert_to_billions(
                predictions_df[model_name].values
            )
    
    # Create output dataframe with monthly forecasts
    forecast_results = []
    
    for idx, (_, row) in enumerate(predictions_df.iterrows(), 1):
        month_date = row.get('date', f"2026-{idx:02d}-01")
        
        result = {
            'month': idx,
            'date': month_date,
            'auction_month': row.get('auction_month', idx),
            'auction_year': row.get('auction_year', 2026),
            'Random Forest (Rp T)': row.get('Random Forest_billions', np.nan),
            'Gradient Boosting (Rp T)': row.get('Gradient Boosting_billions', np.nan),
            'AdaBoost (Rp T)': row.get('AdaBoost_billions', np.nan),
            'Stepwise Regression (Rp T)': row.get('Stepwise Regression_billions', np.nan),
            'Ensemble Mean (Rp T)': row.get('ensemble_mean_billions', np.nan),
        }
        forecast_results.append(result)
    
    # Create results DataFrame
    results_df = pd.DataFrame(forecast_results)
    
    # Calculate totals and averages
    print("📈 Computing 2026 summary statistics...")
    
    rf_total = results_df['Random Forest (Rp T)'].sum()
    gb_total = results_df['Gradient Boosting (Rp T)'].sum()
    ada_total = results_df['AdaBoost (Rp T)'].sum()
    stepwise_total = results_df['Stepwise Regression (Rp T)'].sum()
    ensemble_total = results_df['Ensemble Mean (Rp T)'].sum()
    
    rf_avg = rf_total / len(results_df)
    gb_avg = gb_total / len(results_df)
    ada_avg = ada_total / len(results_df)
    stepwise_avg = stepwise_total / len(results_df)
    ensemble_avg = ensemble_total / len(results_df)
    
    print(f"  Random Forest Total: Rp {rf_total:,.2f}T (Avg: {rf_avg:,.2f}T/month)")
    print(f"  Gradient Boosting Total: Rp {gb_total:,.2f}T (Avg: {gb_avg:,.2f}T/month)")
    print(f"  AdaBoost Total: Rp {ada_total:,.2f}T (Avg: {ada_avg:,.2f}T/month)")
    print(f"  Stepwise Regression Total: Rp {stepwise_total:,.2f}T (Avg: {stepwise_avg:,.2f}T/month)")
    print(f"  Ensemble Mean Total: Rp {ensemble_total:,.2f}T (Avg: {ensemble_avg:,.2f}T/month)")
    print()
    
    # Add summary rows with same columns as merged dataframe
    summary_row_total = {'month': 'TOTAL', 'date': '2026 Full Year'}
    summary_row_avg = {'month': 'AVG', 'date': 'Monthly Average'}
    
    # Add NaN for feature columns
    for col in results_df.columns:
        if col not in ['month', 'date', 'Random Forest (Rp T)', 'Gradient Boosting (Rp T)', 'AdaBoost (Rp T)', 'Stepwise Regression (Rp T)', 'Ensemble Mean (Rp T)']:
            summary_row_total[col] = np.nan
            summary_row_avg[col] = np.nan
    
    # Add forecast totals/averages
    summary_row_total['Random Forest (Rp T)'] = rf_total
    summary_row_total['Gradient Boosting (Rp T)'] = gb_total
    summary_row_total['AdaBoost (Rp T)'] = ada_total
    summary_row_total['Stepwise Regression (Rp T)'] = stepwise_total
    summary_row_total['Ensemble Mean (Rp T)'] = ensemble_total
    
    summary_row_avg['Random Forest (Rp T)'] = rf_avg
    summary_row_avg['Gradient Boosting (Rp T)'] = gb_avg
    summary_row_avg['AdaBoost (Rp T)'] = ada_avg
    summary_row_avg['Stepwise Regression (Rp T)'] = stepwise_avg
    summary_row_avg['Ensemble Mean (Rp T)'] = ensemble_avg
    
    # Concat with matching columns
    summary_df = pd.DataFrame([summary_row_total, summary_row_avg])
    summary_df = summary_df[results_df.columns]
    results_df = pd.concat([results_df, summary_df], ignore_index=True)
    
    # Export to CSV
    print(f"💾 Exporting results to {output_file}")
    results_df.to_csv(output_file, index=False)
    print(f"✅ Successfully saved {len(results_df)-2} months + 2 summary rows to {output_file}")
    print()
    
    # Print model performance
    print("📊 Model Performance (Test Set):")
    for model_name, metrics in forecaster.metrics.items():
        print(f"  {model_name:25s} | R² = {metrics['r2']:.4f} | MSE = {metrics['mse']:.4f}")
    print()
    
    print("=" * 80)
    print("✅ FORECASTING COMPLETE")
    print("=" * 80)
    print(f"\nForecast file: {output_file}")
    print(f"Models trained: {', '.join(forecaster.models.keys())}, Stepwise Regression")
    print(f"2026 Ensemble Forecast: Rp {ensemble_total:,.2f}T")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create merged auction database
    print("=" * 80)
    print("CREATING MERGED AUCTION DATABASE")
    print("=" * 80)
    print()
    
    print("✓ Merging historical and forecast data...")
    
    # Select columns from training data (without date)
    train_cols = ['auction_month', 'auction_year', 'incoming_bio_log', 'awarded_bio_log', 'bid_to_cover']
    train_selected = train_data[train_cols].copy()
    
    # Select columns from forecast results (only the 12 monthly rows, not summary)
    forecast_cols = ['auction_month', 'auction_year', 'Random Forest (Rp T)', 'Gradient Boosting (Rp T)', 
                     'AdaBoost (Rp T)', 'Stepwise Regression (Rp T)', 'Ensemble Mean (Rp T)']
    forecast_selected = results_df.iloc[:12][forecast_cols].copy()
    
    # Merge by auction_month and auction_year
    merged_db = pd.merge(
        train_selected,
        forecast_selected,
        on=['auction_month', 'auction_year'],
        how='outer'
    )
    
    # Sort by year and month
    merged_db = merged_db.sort_values(['auction_year', 'auction_month']).reset_index(drop=True)
    
    # Transform data: create date, unlog, and convert to trillion units
    print("✓ Transforming data...")
    
    # 1. Create date column (end of month) from auction_month and auction_year
    from dateutil.relativedelta import relativedelta
    
    def get_end_of_month(row):
        """Get end of month date from auction_month and auction_year."""
        year = int(row['auction_year'])
        month = int(row['auction_month'])
        # First day of next month minus one day = last day of current month
        return pd.Timestamp(year=year, month=month, day=1) + relativedelta(months=1) - relativedelta(days=1)
    
    merged_db['date'] = merged_db.apply(get_end_of_month, axis=1)
    
    # 2. Unlog incoming_bio_log and awarded_bio_log (they are in log10 scale)
    merged_db['incoming_bio_log'] = 10 ** merged_db['incoming_bio_log']
    merged_db['awarded_bio_log'] = 10 ** merged_db['awarded_bio_log']
    
    # 3. Convert to trillion units (divide by 1000)
    # Historical data columns
    merged_db['incoming_bio_log'] = merged_db['incoming_bio_log'] / 1000
    merged_db['awarded_bio_log'] = merged_db['awarded_bio_log'] / 1000
    
    # Forecast columns
    forecast_cols_to_divide = ['Random Forest (Rp T)', 'Gradient Boosting (Rp T)', 
                                'AdaBoost (Rp T)', 'Stepwise Regression (Rp T)', 'Ensemble Mean (Rp T)']
    for col in forecast_cols_to_divide:
        if col in merged_db.columns:
            merged_db[col] = merged_db[col] / 1000
    
    # Reorder columns: date first, then auction_month, auction_year, then rest
    cols_order = ['date', 'auction_month', 'auction_year', 'incoming_bio_log', 'awarded_bio_log', 'bid_to_cover',
                  'Random Forest (Rp T)', 'Gradient Boosting (Rp T)', 'AdaBoost (Rp T)', 
                  'Stepwise Regression (Rp T)', 'Ensemble Mean (Rp T)']
    merged_db = merged_db[cols_order]
    
    # Export merged database
    database_file = "database/auction_database.csv"
    print(f"💾 Exporting transformed database to {database_file}")
    merged_db.to_csv(database_file, index=False)
    print(f"✅ Successfully created {database_file}")
    print(f"   Total records: {len(merged_db)} (historical + forecast)")
    print(f"   Transformations applied:")
    print(f"     - Added end-of-month date from auction_month and auction_year")
    print(f"     - Unlogged incoming_bio_log and awarded_bio_log (from log10 to billions)")
    print(f"     - Converted all to trillion units (divided by 1000)")
    print()
    
    print("=" * 80)
    print("✅ ALL OPERATIONS COMPLETE")
    print("=" * 80)
    print(f"\nOutput files created:")
    print(f"  1. {output_file}")
    print(f"     - 2026 monthly forecasts with ensemble predictions")
    print(f"  2. {database_file}")
    print(f"     - Merged historical data + 2026 forecasts (transformed)")
    print(f"\n2026 Ensemble Forecast: Rp {ensemble_total:,.2f}T")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
