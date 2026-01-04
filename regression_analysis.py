"""
Regression Analysis for Bond Yields

Provides AR(1) and other regression diagnostics for yield time series.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import date
import statsmodels.api as sm
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from scipy import stats


def ar1_regression(series: pd.Series, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict:
    """
    Run AR(1) regression: y_t = α + β y_{t-1} + ε_t
    
    Args:
        series: Time series of yields with datetime index
        start_date: Optional start date filter
        end_date: Optional end date filter
    
    Returns:
        Dictionary with regression results and diagnostics
    """
    # Filter by date range if specified
    if start_date or end_date:
        if start_date:
            series = series[series.index >= pd.to_datetime(start_date)]
        if end_date:
            series = series[series.index <= pd.to_datetime(end_date)]
    
    if len(series) < 60:
        return {'error': 'Insufficient data for regression (need at least 60 observations)'}
    
    # Prepare AR(1) data: y_t and y_{t-1}
    df = pd.DataFrame({'y': series})
    df['y_lag1'] = df['y'].shift(1)
    df = df.dropna()
    
    if len(df) < 60:
        return {'error': 'Insufficient data after creating lagged variable'}
    
    # Run OLS regression
    X = sm.add_constant(df['y_lag1'])
    y = df['y']
    model = sm.OLS(y, X).fit(cov_type='HC0')  # Heteroskedasticity-robust standard errors
    
    # Extract key statistics
    alpha = model.params['const']
    beta = model.params['y_lag1']
    alpha_se = model.bse['const']
    beta_se = model.bse['y_lag1']
    alpha_pval = model.pvalues['const']
    beta_pval = model.pvalues['y_lag1']
    r_squared = model.rsquared
    adj_r_squared = model.rsquared_adj
    
    # Residual diagnostics
    residuals = model.resid
    resid_mean = residuals.mean()
    resid_std = residuals.std()
    
    # Normality test (Jarque-Bera)
    jb_stat, jb_pval = stats.jarque_bera(residuals)
    
    # Autocorrelation test (Ljung-Box at lag 5)
    lb_result = acorr_ljungbox(residuals, lags=5, return_df=True)
    lb_pval_lag1 = lb_result['lb_pvalue'].iloc[0] if len(lb_result) > 0 else np.nan
    
    # Heteroskedasticity test (ARCH LM test)
    try:
        arch_test = het_arch(residuals, nlags=5)
        arch_pval = arch_test[1]
    except:
        arch_pval = np.nan
    
    # Descriptive stats of y
    y_mean = series.mean()
    y_std = series.std()
    y_min = series.min()
    y_max = series.max()
    
    # Period info
    start = series.index[0].strftime('%Y-%m-%d')
    end = series.index[-1].strftime('%Y-%m-%d')
    n_obs = len(df)
    
    return {
        # Regression coefficients
        'alpha': alpha,
        'beta': beta,
        'alpha_se': alpha_se,
        'beta_se': beta_se,
        'alpha_pval': alpha_pval,
        'beta_pval': beta_pval,
        'r_squared': r_squared,
        'adj_r_squared': adj_r_squared,
        
        # Residual diagnostics
        'resid_mean': resid_mean,
        'resid_std': resid_std,
        'jb_stat': jb_stat,
        'jb_pval': jb_pval,
        'lb_pval_lag1': lb_pval_lag1,
        'arch_pval': arch_pval,
        
        # Series descriptives
        'y_mean': y_mean,
        'y_std': y_std,
        'y_min': y_min,
        'y_max': y_max,
        
        # Sample info
        'n_obs': n_obs,
        'start_date': start,
        'end_date': end,
    }


def format_ar1_results(results: Dict, tenor: str) -> str:
    """
    Format AR(1) regression results in plain English with proper statistics.
    
    Args:
        results: Dictionary from ar1_regression()
        tenor: Tenor label (e.g., '05 year')
    
    Returns:
        Formatted text report
    """
    if 'error' in results:
        return f"❌ {results['error']}"
    
    # Extract values
    alpha = results['alpha']
    beta = results['beta']
    alpha_se = results['alpha_se']
    beta_se = results['beta_se']
    alpha_pval = results['alpha_pval']
    beta_pval = results['beta_pval']
    r2 = results['r_squared']
    adj_r2 = results['adj_r_squared']
    
    resid_mean = results['resid_mean']
    resid_std = results['resid_std']
    jb_pval = results['jb_pval']
    lb_pval = results['lb_pval_lag1']
    arch_pval = results['arch_pval']
    
    y_mean = results['y_mean']
    y_std = results['y_std']
    y_min = results['y_min']
    y_max = results['y_max']
    
    n_obs = results['n_obs']
    start = results['start_date']
    end = results['end_date']
    
    # Build report
    report = []
    report.append(f"📊 INDOGB {tenor.upper()}: AR(1) Regression Analysis")
    report.append(f"Period: {start} to {end} ({n_obs} observations)\n")
    
    # Model specification
    report.append("<b>Model:</b> y<sub>t</sub> = α + β y<sub>t-1</sub> + ε<sub>t</sub>\n")
    
    # Coefficients
    report.append("<b>Regression Results:</b>")
    
    # Alpha (intercept)
    alpha_sig = "***" if alpha_pval < 0.01 else ("**" if alpha_pval < 0.05 else ("*" if alpha_pval < 0.10 else ""))
    report.append(f"  α (intercept) = {alpha:.6f} (SE: {alpha_se:.6f}, p={alpha_pval:.4f}) {alpha_sig}")
    
    # Beta (persistence)
    beta_sig = "***" if beta_pval < 0.01 else ("**" if beta_pval < 0.05 else ("*" if beta_pval < 0.10 else ""))
    report.append(f"  β (persistence) = {beta:.6f} (SE: {beta_se:.6f}, p={beta_pval:.4f}) {beta_sig}")
    
    report.append(f"  R² = {r2:.4f} | Adjusted R² = {adj_r2:.4f}\n")
    
    # Interpretation
    report.append("<b>Interpretation:</b>")
    
    # Beta interpretation
    if beta > 0.95:
        persistence_desc = "very high persistence (near unit root)"
    elif beta > 0.80:
        persistence_desc = "high persistence"
    elif beta > 0.50:
        persistence_desc = "moderate persistence"
    else:
        persistence_desc = "low persistence (mean-reverting)"
    
    report.append(f"  • The coefficient β = {beta:.4f} indicates <b>{persistence_desc}</b>.")
    report.append(f"    Yesterday's yield explains {r2*100:.1f}% of today's yield variation.")
    
    # Mean-reversion or random walk
    if beta >= 0.98:
        report.append(f"  • Process is close to a <b>random walk</b> (β ≈ 1), with little mean reversion.")
    elif beta < 0.80:
        half_life = -np.log(2) / np.log(beta) if beta > 0 and beta < 1 else np.inf
        report.append(f"  • <b>Half-life of shocks:</b> ~{half_life:.1f} days (time for a shock to decay by 50%).")
    
    # Series description
    report.append(f"\n<b>Yield Characteristics:</b>")
    report.append(f"  • Average: {y_mean:.2f}% | Std Dev: {y_std:.2f}%")
    report.append(f"  • Range: {y_min:.2f}% to {y_max:.2f}%")
    
    # Residual diagnostics
    report.append(f"\n<b>Residual Diagnostics:</b>")
    report.append(f"  • Mean: {resid_mean:.6f} (should be ~0)")
    report.append(f"  • Std Dev: {resid_std:.4f}%")
    
    # Normality
    if jb_pval < 0.05:
        report.append(f"  • <b>Normality:</b> Rejected (Jarque-Bera p={jb_pval:.4f})")
        report.append(f"    → Residuals have fat tails or skewness (common during regime shifts)")
    else:
        report.append(f"  • <b>Normality:</b> Not rejected (Jarque-Bera p={jb_pval:.4f})")
    
    # Autocorrelation
    if lb_pval < 0.05:
        report.append(f"  • <b>Autocorrelation:</b> Detected (Ljung-Box p={lb_pval:.4f})")
        report.append(f"    → Residuals show serial correlation; AR(1) may be insufficient")
    else:
        report.append(f"  • <b>Autocorrelation:</b> None (Ljung-Box p={lb_pval:.4f})")
    
    # Heteroskedasticity
    if not np.isnan(arch_pval):
        if arch_pval < 0.05:
            report.append(f"  • <b>Heteroskedasticity:</b> Detected (ARCH test p={arch_pval:.4f})")
            report.append(f"    → Volatility clustering present (variance changes over time)")
        else:
            report.append(f"  • <b>Heteroskedasticity:</b> None (ARCH test p={arch_pval:.4f})")
    
    # Conclusion
    report.append(f"\n<i>*** p&lt;0.01, ** p&lt;0.05, * p&lt;0.10</i>")
    
    return "\n".join(report)


def multiple_regression(y_series: pd.Series, X_dict: Dict[str, pd.Series], 
                       start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict:
    """
    Run multiple regression: y_t = α + β₁ X₁_t + β₂ X₂_t + ... + ε_t
    
    Args:
        y_series: Dependent variable (e.g., 5-year yield)
        X_dict: Dictionary of independent variables {name: series}
                e.g., {'10_year': series1, 'idrusd': series2, 'vix': series3}
        start_date: Optional start date filter
        end_date: Optional end date filter
    
    Returns:
        Dictionary with regression results and diagnostics
    """
    # Combine all series into a DataFrame
    df = pd.DataFrame({'y': y_series})
    for name, series in X_dict.items():
        df[name] = series
    
    # Filter by date range
    if start_date:
        df = df[df.index >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df.index <= pd.to_datetime(end_date)]
    
    # Drop missing values
    df = df.dropna()
    
    if len(df) < 60:
        return {'error': 'Insufficient data for regression (need at least 60 observations)'}
    
    # Prepare X and y
    X_vars = list(X_dict.keys())
    X = sm.add_constant(df[X_vars])
    y = df['y']
    
    # Run OLS regression with robust standard errors
    model = sm.OLS(y, X).fit(cov_type='HC0')
    
    # Extract coefficients
    coefficients = {}
    for var in ['const'] + X_vars:
        coefficients[var] = {
            'coef': model.params[var],
            'se': model.bse[var],
            'tstat': model.tvalues[var],
            'pval': model.pvalues[var],
        }
    
    # Model fit
    r_squared = model.rsquared
    adj_r_squared = model.rsquared_adj
    f_stat = model.fvalue
    f_pval = model.f_pvalue
    
    # Residual diagnostics
    residuals = model.resid
    resid_mean = residuals.mean()
    resid_std = residuals.std()
    
    # Normality test (Jarque-Bera)
    jb_stat, jb_pval = stats.jarque_bera(residuals)
    
    # Autocorrelation test (Ljung-Box)
    lb_result = acorr_ljungbox(residuals, lags=5, return_df=True)
    lb_pval_lag1 = lb_result['lb_pvalue'].iloc[0] if len(lb_result) > 0 else np.nan
    
    # Heteroskedasticity test (ARCH LM)
    try:
        arch_test = het_arch(residuals, nlags=5)
        arch_pval = arch_test[1]
    except:
        arch_pval = np.nan
    
    # Multicollinearity: Variance Inflation Factor (VIF)
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    vif_data = {}
    try:
        for i, var in enumerate(X_vars):
            vif_data[var] = variance_inflation_factor(X.values, i + 1)  # +1 to skip constant
    except:
        vif_data = {var: np.nan for var in X_vars}
    
    # Descriptive stats
    y_mean = y.mean()
    y_std = y.std()
    
    # Period info
    start = df.index[0].strftime('%Y-%m-%d')
    end = df.index[-1].strftime('%Y-%m-%d')
    n_obs = len(df)
    
    return {
        # Model specification
        'x_vars': X_vars,
        'coefficients': coefficients,
        
        # Model fit
        'r_squared': r_squared,
        'adj_r_squared': adj_r_squared,
        'f_stat': f_stat,
        'f_pval': f_pval,
        
        # Residual diagnostics
        'resid_mean': resid_mean,
        'resid_std': resid_std,
        'jb_stat': jb_stat,
        'jb_pval': jb_pval,
        'lb_pval_lag1': lb_pval_lag1,
        'arch_pval': arch_pval,
        
        # Multicollinearity
        'vif': vif_data,
        
        # Dependent variable stats
        'y_mean': y_mean,
        'y_std': y_std,
        
        # Sample info
        'n_obs': n_obs,
        'start_date': start,
        'end_date': end,
    }


def format_multiple_regression_results(results: Dict, y_name: str) -> str:
    """
    Format multiple regression results in plain English with proper statistics.
    
    Args:
        results: Dictionary from multiple_regression()
        y_name: Name of dependent variable (e.g., '05 year yield')
    
    Returns:
        Formatted text report
    """
    if 'error' in results:
        return f"❌ {results['error']}"
    
    # Extract values
    x_vars = results['x_vars']
    coeffs = results['coefficients']
    r2 = results['r_squared']
    adj_r2 = results['adj_r_squared']
    f_stat = results['f_stat']
    f_pval = results['f_pval']
    
    resid_mean = results['resid_mean']
    resid_std = results['resid_std']
    jb_pval = results['jb_pval']
    lb_pval = results['lb_pval_lag1']
    arch_pval = results['arch_pval']
    vif = results['vif']
    
    y_mean = results['y_mean']
    y_std = results['y_std']
    n_obs = results['n_obs']
    start = results['start_date']
    end = results['end_date']
    
    # Build report
    report = []
    report.append(f"📊 INDOGB: Multiple Regression Analysis")
    report.append(f"<b>Dependent Variable:</b> {y_name}")
    report.append(f"Period: {start} to {end} ({n_obs} observations)\n")
    
    # Model specification with proper lag notation
    predictor_labels = []
    for var in x_vars:
        if var.endswith('_lag1'):
            base = var.replace('_lag1', '').replace('_', ' ').upper()
            predictor_labels.append(f"{base}(t-1)")
        else:
            predictor_labels.append(var.replace('_', ' ').upper())
    
    report.append(f"<b>Model:</b> {y_name} = α + " + " + ".join([f"β{i+1}·{name}" for i, name in enumerate(predictor_labels)]) + " + ε\n")
    
    # Coefficients table
    report.append("<b>Regression Coefficients:</b>")
    
    # Intercept
    alpha_coef = coeffs['const']
    alpha_sig = "***" if alpha_coef['pval'] < 0.01 else ("**" if alpha_coef['pval'] < 0.05 else ("*" if alpha_coef['pval'] < 0.10 else ""))
    report.append(f"  α (intercept) = {alpha_coef['coef']:.6f} (SE: {alpha_coef['se']:.6f}, t={alpha_coef['tstat']:.2f}, p={alpha_coef['pval']:.4f}) {alpha_sig}")
    
    # Independent variables
    for i, var in enumerate(x_vars):
        coef = coeffs[var]
        sig = "***" if coef['pval'] < 0.01 else ("**" if coef['pval'] < 0.05 else ("*" if coef['pval'] < 0.10 else ""))
        # Format with lag notation if applicable
        if var.endswith('_lag1'):
            base = var.replace('_lag1', '').replace('_', ' ').upper()
            var_display = f"{base}(t-1)"
        else:
            var_display = var.replace('_', ' ').upper()
        report.append(f"  β{i+1} ({var_display}) = {coef['coef']:.6f} (SE: {coef['se']:.6f}, t={coef['tstat']:.2f}, p={coef['pval']:.4f}) {sig}")
    
    report.append("")
    
    # Model fit
    report.append("<b>Model Fit:</b>")
    report.append(f"  • R² = {r2:.4f} | Adjusted R² = {adj_r2:.4f}")
    report.append(f"  • F-statistic = {f_stat:.2f} (p={f_pval:.4f})")
    f_sig = "highly significant" if f_pval < 0.01 else ("significant" if f_pval < 0.05 else "not significant")
    report.append(f"  • Overall model is <b>{f_sig}</b>")
    report.append(f"  • Predictors explain {adj_r2*100:.1f}% of yield variation\n")
    
    # Economic interpretation
    report.append("<b>Economic Interpretation:</b>")
    for i, var in enumerate(x_vars):
        coef_val = coeffs[var]['coef']
        coef_pval = coeffs[var]['pval']
        
        # Format variable name with lag notation
        if var.endswith('_lag1'):
            base = var.replace('_lag1', '').replace('_', ' ')
            var_display = f"{base} (lagged 1 period)"
        else:
            var_display = var.replace('_', ' ')
        
        if coef_pval < 0.05:
            direction = "increases" if coef_val > 0 else "decreases"
            report.append(f"  • A 1-unit increase in <b>{var_display}</b> {direction} {y_name} by {abs(coef_val):.4f} percentage points (significant)")
        else:
            report.append(f"  • <b>{var_display}</b> has no significant effect (p={coef_pval:.4f})")
    
    report.append("")
    # Format with lag notation
        if var.endswith('_lag1'):
            base = var.replace('_lag1', '').replace('_', ' ').upper()
            var_label = f"{base}(t-1)"
        else:
            var_label = var.replace('_', ' ').upper()
        
        if np.isnan(vif_val):
            report.append(f"  • {var_label}: VIF = N/A")
        else:
            vif_status = "✓ OK" if vif_val < 5 else ("⚠ Moderate" if vif_val < 10 else "⛔ High")
            report.append(f"  • {var_label
        vif_val = vif.get(var, np.nan)
        if np.isnan(vif_val):
            report.append(f"  • {var.replace('_', ' ').upper()}: VIF = N/A")
        else:
            vif_status = "✓ OK" if vif_val < 5 else ("⚠ Moderate" if vif_val < 10 else "⛔ High")
            report.append(f"  • {var.replace('_', ' ').upper()}: VIF = {vif_val:.2f} {vif_status}")
    
    if max_vif < 5:
        report.append(f"  → <b>No multicollinearity issues</b> (all VIF < 5)")
    elif max_vif < 10:
        report.append(f"  → <b>Moderate multicollinearity</b> (some VIF between 5-10)")
    else:
        report.append(f"  → <b>High multicollinearity</b> (VIF > 10 detected)")
    
    report.append("")
    
    # Dependent variable description
    report.append(f"<b>{y_name.title()} Characteristics:</b>")
    report.append(f"  • Average: {y_mean:.2f}% | Std Dev: {y_std:.2f}%")
    
    # Residual diagnostics
    report.append(f"\n<b>Residual Diagnostics:</b>")
    report.append(f"  • Mean: {resid_mean:.6f} (should be ~0)")
    report.append(f"  • Std Dev: {resid_std:.4f}%")
    
    # Normality
    if jb_pval < 0.05:
        report.append(f"  • <b>Normality:</b> Rejected (Jarque-Bera p={jb_pval:.4f})")
        report.append(f"    → Residuals have fat tails or skewness")
    else:
        report.append(f"  • <b>Normality:</b> Not rejected (Jarque-Bera p={jb_pval:.4f})")
    
    # Autocorrelation
    if lb_pval < 0.05:
        report.append(f"  • <b>Autocorrelation:</b> Detected (Ljung-Box p={lb_pval:.4f})")
        report.append(f"    → Consider adding lagged dependent variable")
    else:
        report.append(f"  • <b>Autocorrelation:</b> None (Ljung-Box p={lb_pval:.4f})")
    
    # Heteroskedasticity
    if not np.isnan(arch_pval):
        if arch_pval < 0.05:
            report.append(f"  • <b>Heteroskedasticity:</b> Detected (ARCH test p={arch_pval:.4f})")
            report.append(f"    → Robust standard errors used (HC0)")
        else:
            report.append(f"  • <b>Heteroskedasticity:</b> None (ARCH test p={arch_pval:.4f})")
    
    # Conclusion
    report.append(f"\n<i>*** p&lt;0.01, ** p&lt;0.05, * p&lt;0.10</i>")
    
    return "\n".join(report)
