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


def _harvard_header(headline: str, hook: str) -> list[str]:
    lines = [headline]
    if hook:
        lines.append(f"<blockquote>{hook}</blockquote>")
        lines.append("")
    return lines


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

    # Build hook
    hook = f"b={beta:.2f}, R2={r2:.2f}, n={n_obs}"
    report = _harvard_header(f"📊 INDOGB {tenor.upper()} — AR(1) Regression", hook)
    report.append(f"Period: {start} to {end} ({n_obs} observations)\n")
    
    # Model specification
    report.append("<b>Model:</b> y_t = a + b*y_(t-1) + e\n")
    
    # Coefficients
    report.append("<b>Regression Results:</b>")
    
    # Alpha (intercept)
    alpha_sig = "***" if alpha_pval < 0.01 else ("**" if alpha_pval < 0.05 else ("*" if alpha_pval < 0.10 else ""))
    report.append(f"  a (intercept) = {alpha:.6f} (SE: {alpha_se:.6f}, p={alpha_pval:.4f}) {alpha_sig}")
    
    # Beta (persistence)
    beta_sig = "***" if beta_pval < 0.01 else ("**" if beta_pval < 0.05 else ("*" if beta_pval < 0.10 else ""))
    report.append(f"  b (persistence) = {beta:.6f} (SE: {beta_se:.6f}, p={beta_pval:.4f}) {beta_sig}")
    
    report.append(f"  R2 = {r2:.4f} | Adjusted R2 = {adj_r2:.4f}\n")
    
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
    
    report.append(f"  * The coefficient b = {beta:.4f} indicates <b>{persistence_desc}</b>.")
    report.append(f"    Yesterday's yield explains {r2*100:.1f}% of today's yield variation.")
    
    # Mean-reversion or random walk
    if beta >= 0.98:
        report.append(f"  * Process is close to a <b>random walk</b> (b approx 1), with little mean reversion.")
    elif beta < 0.80:
        half_life = -np.log(2) / np.log(beta) if beta > 0 and beta < 1 else np.inf
        report.append(f"  * <b>Half-life of shocks:</b> ~{half_life:.1f} days (time for shock decay to 50%).")
    
    # Series description
    report.append(f"\n<b>Yield Characteristics:</b>")
    report.append(f"  * Average: {y_mean:.2f}% | Std Dev: {y_std:.2f}%")
    report.append(f"  * Range: {y_min:.2f}% to {y_max:.2f}%")
    
    # Residual diagnostics
    report.append(f"\n<b>Residual Diagnostics:</b>")
    report.append(f"  * Mean: {resid_mean:.6f} (should be ~0)")
    report.append(f"  * Std Dev: {resid_std:.4f}%")
    
    # Normality
    if jb_pval < 0.05:
        report.append(f"  * <b>Normality:</b> Rejected (Jarque-Bera p={jb_pval:.4f})")
        report.append(f"    → Residuals have fat tails or skewness (common during regime shifts)")
    else:
        report.append(f"  * <b>Normality:</b> Not rejected (Jarque-Bera p={jb_pval:.4f})")
    
    # Autocorrelation
    if lb_pval < 0.05:
        report.append(f"  * <b>Autocorrelation:</b> Detected (Ljung-Box p={lb_pval:.4f})")
        report.append(f"    → Residuals show serial correlation; AR(1) may be insufficient")
    else:
        report.append(f"  * <b>Autocorrelation:</b> None (Ljung-Box p={lb_pval:.4f})")
    
    # Heteroskedasticity
    if not np.isnan(arch_pval):
        if arch_pval < 0.05:
            report.append(f"  * <b>Heteroskedasticity:</b> Detected (ARCH test p={arch_pval:.4f})")
            report.append(f"    → Volatility clustering present (variance changes over time)")
        else:
            report.append(f"  * <b>Heteroskedasticity:</b> None (ARCH test p={arch_pval:.4f})")
    
    # Conclusion
    report.append(f"\n<i>*** p less than 0.01, ** p less than 0.05, * p less than 0.10</i>")
    
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
    
    # Generate hook from model statistics
    hook = f"R²={r2:.2f}, F-stat={f_stat:.2f}, n={n_obs}"
    
    # Build report
    report = _harvard_header("📊 INDOGB — Multiple Regression", hook)
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
    
    report.append(f"<b>Model:</b> {y_name} = a + " + " + ".join([f"b{i+1}*{name}" for i, name in enumerate(predictor_labels)]) + " + e\n")
    
    # Coefficients table
    report.append("<b>Regression Coefficients:</b>")
    
    # Intercept
    alpha_coef = coeffs['const']
    alpha_sig = "***" if alpha_coef['pval'] < 0.01 else ("**" if alpha_coef['pval'] < 0.05 else ("*" if alpha_coef['pval'] < 0.10 else ""))
    report.append(f"  a (intercept) = {alpha_coef['coef']:.6f} (SE: {alpha_coef['se']:.6f}, t={alpha_coef['tstat']:.2f}, p={alpha_coef['pval']:.4f}) {alpha_sig}")
    
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
        report.append(f"  b{i+1} ({var_display}) = {coef['coef']:.6f} (SE: {coef['se']:.6f}, t={coef['tstat']:.2f}, p={coef['pval']:.4f}) {sig}")
    
    report.append("")
    
    # Model fit
    report.append("<b>Model Fit:</b>")
    report.append(f"  * R2 = {r2:.4f} | Adjusted R2 = {adj_r2:.4f}")
    report.append(f"  * F-statistic = {f_stat:.2f} (p={f_pval:.4f})")
    f_sig = "highly significant" if f_pval < 0.01 else ("significant" if f_pval < 0.05 else "not significant")
    report.append(f"  * Overall model is <b>{f_sig}</b>")
    report.append(f"  * Predictors explain {adj_r2*100:.1f}% of yield variation\n")
    
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
            report.append(f"  * A 1-unit increase in <b>{var_display}</b> {direction} {y_name} by {abs(coef_val):.4f} percentage points (significant)")
        else:
            report.append(f"  * <b>{var_display}</b> has no significant effect (p={coef_pval:.4f})")
    
    report.append("")
    
    # Multicollinearity check
    report.append("<b>Multicollinearity (VIF):</b>")
    max_vif = max(vif.values()) if vif else 0
    for var in x_vars:
        vif_val = vif.get(var, np.nan)
        # Format with lag notation
        if var.endswith('_lag1'):
            base = var.replace('_lag1', '').replace('_', ' ').upper()
            var_label = f"{base}(t-1)"
        else:
            var_label = var.replace('_', ' ').upper()
        
        if np.isnan(vif_val):
            report.append(f"  * {var_label}: VIF = N/A")
        else:
            vif_status = "OK" if vif_val < 5 else ("Moderate" if vif_val < 10 else "High")
            report.append(f"  * {var_label}: VIF = {vif_val:.2f} {vif_status}")
    
    if max_vif < 5:
        report.append(f"  → <b>No multicollinearity issues</b> (all VIF less than 5)")
    elif max_vif < 10:
        report.append(f"  → <b>Moderate multicollinearity</b> (some VIF between 5-10)")
    else:
        report.append(f"  → <b>High multicollinearity</b> (VIF greater than 10 detected)")
    
    report.append("")
    
    # Dependent variable description
    report.append(f"<b>{y_name.title()} Characteristics:</b>")
    report.append(f"  * Average: {y_mean:.2f}% | Std Dev: {y_std:.2f}%")
    
    # Residual diagnostics
    report.append(f"\n<b>Residual Diagnostics:</b>")
    report.append(f"  * Mean: {resid_mean:.6f} (should be ~0)")
    report.append(f"  * Std Dev: {resid_std:.4f}%")
    
    # Normality
    if jb_pval < 0.05:
        report.append(f"  * <b>Normality:</b> Rejected (Jarque-Bera p={jb_pval:.4f})")
        report.append(f"    → Residuals have fat tails or skewness")
    else:
        report.append(f"  * <b>Normality:</b> Not rejected (Jarque-Bera p={jb_pval:.4f})")
    
    # Autocorrelation
    if lb_pval < 0.05:
        report.append(f"  * <b>Autocorrelation:</b> Detected (Ljung-Box p={lb_pval:.4f})")
        report.append(f"    → Consider adding lagged dependent variable")
    else:
        report.append(f"  * <b>Autocorrelation:</b> None (Ljung-Box p={lb_pval:.4f})")
    
    # Heteroskedasticity
    if not np.isnan(arch_pval):
        if arch_pval < 0.05:
            report.append(f"  * <b>Heteroskedasticity:</b> Detected (ARCH test p={arch_pval:.4f})")
            report.append(f"    → Robust standard errors used (HC0)")
        else:
            report.append(f"  * <b>Heteroskedasticity:</b> None (ARCH test p={arch_pval:.4f})")
    
    # Conclusion
    report.append(f"\n<i>*** p&lt;0.01, ** p&lt;0.05, * p&lt;0.10</i>")
    
    return "\n".join(report)


# =============================
# Granger Causality & VAR/IRF
# =============================
from statsmodels.tsa.stattools import grangercausalitytests
from statsmodels.tsa.api import VAR


def event_study(
    target: pd.Series,
    event_date: date,
    market: Optional[pd.Series] = None,
    estimation_window: int = 60,
    window_pre: int = 5,
    window_post: int = 5,
    method: str = "risk",
) -> Dict:
    """Simple event study for a single series with optional market adjustment.

    Args:
        target: Price/return series indexed by datetime.
        event_date: Event date.
        market: Optional market index series (same frequency/index domain).
        estimation_window: Days before the event used for estimation.
        window_pre: Days before event included in observation window.
        window_post: Days after event included in observation window.
        method: 'mean' | 'market' | 'risk'.

    Returns:
        Dict with abnormal returns (AR), cumulative AR (CAR), t-stats, and metadata.
    """
    method = method.lower()
    if method not in {"mean", "market", "risk"}:
        return {"error": "Invalid method; choose mean, market, or risk."}

    # Ensure chronological order and returns
    target = target.sort_index().dropna()
    target_ret = target.pct_change().dropna()

    event_ts = pd.to_datetime(event_date)
    est_start = event_ts - pd.Timedelta(days=estimation_window)
    est_end = event_ts - pd.Timedelta(days=1)

    est_ret = target_ret.loc[(target_ret.index >= est_start) & (target_ret.index <= est_end)]
    if len(est_ret) < max(20, window_pre + window_post):
        return {"error": "Insufficient estimation window data for event study."}

    obs_start = event_ts - pd.Timedelta(days=window_pre)
    obs_end = event_ts + pd.Timedelta(days=window_post)
    obs_ret = target_ret.loc[(target_ret.index >= obs_start) & (target_ret.index <= obs_end)]
    if obs_ret.empty:
        return {"error": "No observations in event window."}

    sigma = None
    expected_obs = None

    if method == "mean":
        mu = est_ret.mean()
        expected_obs = pd.Series(mu, index=obs_ret.index)
        resid = est_ret - mu
        sigma = resid.std(ddof=1)
    else:
        if market is None:
            return {"error": "Market series required for market/risk methods."}
        market = market.sort_index().dropna()
        market_ret = market.pct_change().dropna()

        est_join = pd.concat([est_ret.rename("y"), market_ret.rename("m")], axis=1).dropna()
        obs_join = pd.concat([obs_ret.rename("y"), market_ret.rename("m")], axis=1).dropna()

        if est_join.empty or obs_join.empty:
            return {"error": "Insufficient overlapping data with market series."}

        if method == "market":
            expected_obs = obs_join["m"]
            sigma = (est_join["y"] - est_join["m"]).std(ddof=1)
        else:  # risk-adjusted
            X = sm.add_constant(est_join["m"])
            model = sm.OLS(est_join["y"], X).fit(cov_type="HC0")
            expected_obs = model.predict(sm.add_constant(obs_join["m"], has_constant="add"))
            sigma = model.resid.std(ddof=1)
        # Align expected to obs_ret index
        expected_obs = expected_obs.reindex(obs_ret.index).interpolate(limit_direction="both")

    if sigma is None or sigma == 0:
        sigma = np.nan

    ar = obs_ret - expected_obs
    car = ar.cumsum()
    t_stats = ar / sigma if not np.isnan(sigma) else pd.Series([np.nan] * len(ar), index=ar.index)

    return {
        "event_date": event_ts.date(),
        "method": method,
        "estimation_window": estimation_window,
        "window_pre": window_pre,
        "window_post": window_post,
        "ar": ar,
        "car": car,
        "t_stats": t_stats,
        "sigma": sigma,
    }


def format_event_study(res: Dict, label: str) -> str:
    if "error" in res:
        return f"❌ {res['error']}"

    ar = res["ar"]
    car = res["car"]
    t_stats = res["t_stats"]
    event_date = res["event_date"]
    window_pre = res["window_pre"]
    window_post = res["window_post"]
    method = res["method"]
    sigma = res["sigma"]

    # Extract key points
    event_ts = pd.to_datetime(event_date)
    ar_event = ar.get(event_ts, np.nan)
    car_last = car.iloc[-1]
    max_post = ar.iloc[ar.index >= event_ts].max()
    min_post = ar.iloc[ar.index >= event_ts].min()

    hook = f"AR0={ar_event:.4f}, CAR={car_last:.4f}, method={method}"
    lines = _harvard_header(f"📈 Event Study — {label}", hook)
    lines.append(f"Event date: {event_date} | Window: -{window_pre} to +{window_post} days")
    lines.append(f"Method: {method}-adjusted | Estimation: {res['estimation_window']} days | sigma(resid)={sigma:.4f}")
    lines.append("")
    lines.append(f"Event-day abnormal return: {ar_event:.4f}")
    lines.append(f"Cumulative abnormal return (end of window): {car_last:.4f}")
    lines.append(f"Post-event AR range: [{min_post:.4f}, {max_post:.4f}]")
    lines.append("")
    lines.append("Daily AR and t-stat:")
    for ts, val in ar.items():
        tval = t_stats.get(ts, np.nan)
        day = int((ts.normalize() - event_ts.normalize()) / pd.Timedelta(days=1))
        lines.append(f"  * Day {day:+d}: AR={val:.4f}, t={tval:.2f}")
    
    # Plain English explanation
    lines.append("")
    lines.append("<b>What This Means:</b>")
    lines.append(f"  * Abnormal Return (AR): The security's return minus what was expected based on historical risk.")
    lines.append(f"  * Cumulative Abnormal Return (CAR): Total abnormal return over the entire event window.")
    if abs(car_last) > 0.01:
        direction = "positive" if car_last > 0 else "negative"
        lines.append(f"  * CAR of {car_last:.4f} suggests a {direction} market reaction to the event.")
    else:
        lines.append(f"  * CAR of {car_last:.4f} suggests minimal market reaction to the event.")
    
    return "\n".join(lines)


def granger_causality(y: pd.Series, x: pd.Series, max_lag: int = 5) -> Dict:
    """Test if x Granger-causes y (does lagged x improve prediction?)."""
    df = pd.concat([y.rename("y"), x.rename("x")], axis=1).dropna()
    if len(df) < max_lag + 20:
        return {"error": f"Insufficient data for Granger causality (need at least {max_lag + 20} observations)"}

    results = grangercausalitytests(df[["y", "x"]], maxlag=max_lag, verbose=False)
    pvals = {lag: res[0]["ssr_ftest"][1] for lag, res in results.items()}
    best_lag = min(pvals, key=pvals.get)
    best_p = pvals[best_lag]

    return {
        "pvalues": pvals,
        "best_lag": best_lag,
        "best_p": best_p,
        "n_obs": len(df),
    }


def format_granger_results(res: Dict, x_name: str, y_name: str) -> str:
    if "error" in res:
        return f"❌ {res['error']}"

    best_lag = res["best_lag"]
    best_p = res["best_p"]
    n_obs = res["n_obs"]

    if best_p < 0.01:
        sig = "strong evidence"
    elif best_p < 0.05:
        sig = "evidence"
    elif best_p < 0.10:
        sig = "weak evidence"
    else:
        sig = "no evidence"

    hook = f"Lag {best_lag}, p={best_p:.3f}, n={n_obs} ({sig})"
    lines = _harvard_header(f"📊 Granger: {x_name} → {y_name}?", hook)
    lines.append(f"Sample: {n_obs} observations")
    lines.append(f"Best lag: {best_lag} | p-value: {best_p:.4f} → {sig}")
    lines.append("")
    lines.append("Lag-by-lag p-values (F-test):")
    for lag in sorted(res["pvalues"].keys()):
        lines.append(f"  * lag {lag}: p={res['pvalues'][lag]:.4f}")
    
    # Plain English explanation
    lines.append("")
    lines.append("<b>What This Means:</b>")
    if best_p < 0.05:
        lines.append(f"  * {x_name} Granger-causes {y_name} (p={best_p:.4f})")
        lines.append(f"    Past values of {x_name} help predict {y_name} beyond its own history.")
        lines.append(f"    Lag {best_lag} shows the strongest predictive power.")
    else:
        lines.append(f"  * {x_name} does NOT Granger-cause {y_name} (p={best_p:.4f})")
        lines.append(f"    Past values of {x_name} do not significantly improve predictions of {y_name}.")
    
    return "\n".join(lines)


def var_with_irf(series_dict: Dict[str, pd.Series], max_lag: int = 5, horizon: int = 10) -> Dict:
    """Fit VAR and compute impulse responses."""
    df = pd.concat(series_dict.values(), axis=1)
    df.columns = list(series_dict.keys())
    df = df.dropna()
    if len(df) < max_lag + 30:
        return {"error": f"Insufficient data for VAR (need at least {max_lag + 30} observations)"}

    model = VAR(df)
    fit = model.fit(maxlags=max_lag, ic="aic")
    irf = fit.irf(horizon)

    irf_summary = {}
    for shock in df.columns:
        for target in df.columns:
            path = irf.irfs[:, df.columns.get_loc(target), df.columns.get_loc(shock)]
            peak_idx = int(np.argmax(np.abs(path)))
            irf_summary[(shock, target)] = {
                "peak": float(path[peak_idx]),
                "peak_horizon": peak_idx,
            }

    return {
        "n_obs": len(df),
        "lag_order": fit.k_ar,
        "aic": fit.aic,
        "irf": irf_summary,
    }


def format_var_irf_results(res: Dict) -> str:
    if "error" in res:
        return f"❌ {res['error']}"

    # Find strongest peak for hook
    strongest = None
    for (shock, target), info in res["irf"].items():
        magnitude = abs(info["peak"])
        if strongest is None or magnitude > strongest[0]:
            strongest = (magnitude, shock, target, info["peak"], info["peak_horizon"])
    if strongest:
        _, shock_s, target_s, peak_val, horizon = strongest
        hook = f"Peak {shock_s}→{target_s}={peak_val:.4f} at h{horizon}; lag k={res['lag_order']}"
    else:
        hook = f"Lag k={res['lag_order']} | AIC={res['aic']:.3f}"

    lines = _harvard_header("📊 VAR with Impulse Responses", hook)
    lines.append(f"Observations: {res['n_obs']} | Selected lag order: {res['lag_order']} | AIC={res['aic']:.3f}")
    lines.append("")
    lines.append("Peak impulse responses (shock → target):")
    for (shock, target), info in res["irf"].items():
        lines.append(f"  * {shock} → {target}: peak {info['peak']:.4f} at horizon {info['peak_horizon']}")
    
    # Plain English explanation
    lines.append("")
    lines.append("<b>What This Means:</b>")
    lines.append(f"  * A VAR (Vector Autoregression) model captures dynamic relationships between variables.")
    lines.append(f"  * Impulse responses show how a 1-unit shock to one variable affects others over time.")
    if strongest:
        _, shock_s, target_s, peak_val, horizon = strongest
        direction = "increases" if peak_val > 0 else "decreases"
        lines.append(f"  * Strongest effect: {shock_s} shock {direction} {target_s} by {abs(peak_val):.4f} at period {horizon}.")
    
    return "\n".join(lines)


def arima_model(series: pd.Series, order: tuple = (1, 1, 1), 
                start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict:
    """
    Run ARIMA(p, d, q) model for integrated differencing and forecasting.
    
    Args:
        series: Time series with datetime index
        order: (p, d, q) tuple; default (1,1,1)
        start_date, end_date: Date range filters
    
    Returns:
        Dictionary with ARIMA results
    """
    from statsmodels.tsa.arima.model import ARIMA
    
    if start_date or end_date:
        if start_date:
            series = series[series.index >= pd.to_datetime(start_date)]
        if end_date:
            series = series[series.index <= pd.to_datetime(end_date)]
    
    if len(series) < 60:
        return {'error': 'Insufficient data (need ≥60 observations)'}
    
    try:
        model = ARIMA(series, order=order)
        result = model.fit()
        
        return {
            'order': order,
            'aic': result.aic,
            'bic': result.bic,
            'rmse': np.sqrt(result.mse),
            'coef': dict(result.params),
            'pvalues': dict(result.pvalues),
            'diagnostics': {
                'ljung_box_pval': acorr_ljungbox(result.resid, lags=5).iloc[-1, 0] if len(result.resid) > 5 else np.nan,
                'mean_residual': result.resid.mean(),
                'residual_std': result.resid.std()
            },
            'n_obs': len(series),
            'start': series.index[0].strftime('%Y-%m-%d'),
            'end': series.index[-1].strftime('%Y-%m-%d'),
            'forecast_next_5': list(result.get_forecast(steps=5).predicted_mean)
        }
    except Exception as e:
        return {'error': f'ARIMA fitting failed: {str(e)}'}


def garch_volatility(series: pd.Series, p: int = 1, q: int = 1,
                     start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict:
    """
    Run GARCH(p, q) model for time-varying volatility.
    
    Args:
        series: Time series (returns or yield changes) with datetime index
        p, q: GARCH order parameters
        start_date, end_date: Date range filters
    
    Returns:
        Dictionary with GARCH results
    """
    try:
        from arch import arch_model
    except ImportError:
        return {'error': 'GARCH requires arch package. Install: pip install arch'}
    
    if start_date or end_date:
        if start_date:
            series = series[series.index >= pd.to_datetime(start_date)]
        if end_date:
            series = series[series.index <= pd.to_datetime(end_date)]
    
    if len(series) < 60:
        return {'error': 'Insufficient data (need ≥60 observations)'}
    
    try:
        # Convert yields to returns (daily changes)
        returns = series.diff().dropna() * 100  # in basis points
        
        model = arch_model(returns, vol='Garch', p=p, q=q)
        result = model.fit(disp='off')
        
        # Conditional volatility
        cond_vol = result.conditional_volatility
        
        # Calculate persistence (α + β)
        try:
            alpha_vals = [v for k, v in result.params.items() if 'alpha' in k.lower()]
            beta_vals = [v for k, v in result.params.items() if 'beta' in k.lower()]
            persistence = sum(alpha_vals) + sum(beta_vals)
        except:
            persistence = np.nan
        
        # Forecast using variance forecast (different API for arch)
        try:
            forecast = result.forecast(horizon=5)
            forecast_vol_5d = list((forecast.variance.values[-1, :] ** 0.5).flatten())
        except:
            forecast_vol_5d = [float(cond_vol.iloc[-1])] * 5  # Fallback to current vol
        
        return {
            'order': (p, q),
            'mean_volatility': float(cond_vol.mean()),
            'max_volatility': float(cond_vol.max()),
            'min_volatility': float(cond_vol.min()),
            'alpha': dict(result.params.get('alpha', {})) if 'alpha' in result.params else {},
            'beta': result.params.get('beta', {}) if 'beta' in result.params else {},
            'aic': float(result.aic),
            'bic': float(result.bic),
            'log_likelihood': float(result.loglikelihood),
            'persistence': float(persistence),
            'n_obs': len(returns),
            'start': series.index[0].strftime('%Y-%m-%d'),
            'end': series.index[-1].strftime('%Y-%m-%d'),
            'current_volatility': float(cond_vol.iloc[-1]),
            'forecast_volatility_5d': forecast_vol_5d
        }
    except Exception as e:
        return {'error': f'GARCH fitting failed: {str(e)}'}


def cointegration_test(series_dict: Dict[str, pd.Series],
                       start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict:
    """
    Test for cointegration (long-run relationships) between multiple series using Johansen test.
    
    Args:
        series_dict: Dictionary of series {name: pd.Series}
        start_date, end_date: Date range filters
    
    Returns:
        Dictionary with Johansen test results
    """
    try:
        from statsmodels.tsa.vector_ar.vecm import coint_johansen
    except ImportError:
        return {'error': 'Cointegration test requires statsmodels vector_ar module'}
    
    # Merge series and filter dates
    df = pd.concat(series_dict, axis=1)
    df.columns = list(series_dict.keys())
    
    if start_date or end_date:
        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df.index <= pd.to_datetime(end_date)]
    
    if len(df) < 60:
        return {'error': 'Insufficient data (need ≥60 observations)'}
    
    df = df.dropna()
    if len(df) < 60:
        return {'error': 'Insufficient data after dropping NaN values'}
    
    try:
        # Johansen test: trace and eigenvalue tests
        result = coint_johansen(df, det_order=0, k_ar_diff=1)
        
        # Extract cointegrating rank at 5% significance
        # result.trace_stat_crit_vals shape: (n_vars, 3) for different significance levels
        trace_stats = result.trace_stat  # Test statistics
        crit_vals = result.trace_stat_crit_vals[:, 0]  # 5% critical values (column 0)
        rank = sum(trace_stats > crit_vals)  # Number of cointegrating relationships
        
        # Store eigenvalues and eigenvectors (cointegrating combinations)
        eigen_vals = result._eig  # Eigenvalues
        eigen_vecs = result.evec  # Eigenvectors (2D array)
        
        return {
            'n_variables': len(series_dict),
            'n_obs': len(df),
            'rank': int(rank),
            'trace_statistics': list(trace_stats),
            'critical_values_5pct': list(crit_vals),
            'eigenvalues': list(eigen_vals),
            'cointegrating_vectors': eigen_vecs.tolist(),
            'series_names': list(series_dict.keys()),
            'start': df.index[0].strftime('%Y-%m-%d'),
            'end': df.index[-1].strftime('%Y-%m-%d')
        }
    except Exception as e:
        return {'error': f'Johansen test failed: {str(e)}'}


def rolling_regression(y_series: pd.Series, X_dict: Dict[str, pd.Series], window: int = 90,
                       start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict:
    """
    Run rolling regression with time-varying coefficients.
    
    Args:
        y_series: Dependent variable
        X_dict: Dictionary of regressors {name: pd.Series}
        window: Rolling window size (days)
        start_date, end_date: Date range filters
    
    Returns:
        Dictionary with rolling coefficient estimates
    """
    # Merge data
    df = pd.concat([y_series.rename('y')] + [s.rename(name) for name, s in X_dict.items()], axis=1)
    
    if start_date or end_date:
        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df.index <= pd.to_datetime(end_date)]
    
    df = df.dropna()
    
    if len(df) < window + 10:
        return {'error': f'Insufficient data for rolling regression with window={window}'}
    
    rolling_params = {name: [] for name in X_dict.keys()}
    rolling_r2 = []
    rolling_dates = []
    
    for i in range(window, len(df)):
        window_data = df.iloc[i - window:i]
        y = window_data['y']
        X = sm.add_constant(window_data[list(X_dict.keys())])
        
        try:
            model = sm.OLS(y, X).fit()
            for name in X_dict.keys():
                rolling_params[name].append(model.params.get(name, np.nan))
            rolling_r2.append(model.rsquared)
            rolling_dates.append(window_data.index[-1].strftime('%Y-%m-%d'))
        except:
            for name in X_dict.keys():
                rolling_params[name].append(np.nan)
            rolling_r2.append(np.nan)
            rolling_dates.append(window_data.index[-1].strftime('%Y-%m-%d'))
    
    return {
        'window': window,
        'n_windows': len(rolling_dates),
        'dates': rolling_dates,
        'rolling_coef': rolling_params,
        'rolling_r2': rolling_r2,
        'mean_coef': {name: np.nanmean(vals) for name, vals in rolling_params.items()},
        'std_coef': {name: np.nanstd(vals) for name, vals in rolling_params.items()},
        'regressors': list(X_dict.keys())
    }


def structural_break_test(series: pd.Series, break_date: Optional[str] = None,
                          start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict:
    """
    Test for structural breaks using Chow test.
    
    Args:
        series: Time series with datetime index
        break_date: Hypothesized break date (YYYY-MM-DD); if None, test AR(1) break
        start_date, end_date: Date range filters
    
    Returns:
        Dictionary with Chow test results
    """
    if start_date or end_date:
        if start_date:
            series = series[series.index >= pd.to_datetime(start_date)]
        if end_date:
            series = series[series.index <= pd.to_datetime(end_date)]
    
    if len(series) < 100:
        return {'error': 'Insufficient data for structural break test (need ≥100)'}
    
    # Prepare AR(1) data
    df = pd.DataFrame({'y': series})
    df['y_lag1'] = df['y'].shift(1)
    df = df.dropna()
    
    if not break_date:
        # Use midpoint as default break
        break_idx = len(df) // 2
    else:
        break_dt = pd.to_datetime(break_date)
        try:
            break_idx = (df.index <= break_dt).sum()
        except:
            return {'error': 'Invalid break_date format'}
    
    if break_idx < 30 or len(df) - break_idx < 30:
        return {'error': 'Break point too close to start or end; need ≥30 obs each side'}
    
    # Split data and fit AR(1) separately
    df1 = df.iloc[:break_idx]
    df2 = df.iloc[break_idx:]
    
    X1 = sm.add_constant(df1['y_lag1'])
    y1 = df1['y']
    model1 = sm.OLS(y1, X1).fit(cov_type='HC0')
    
    X2 = sm.add_constant(df2['y_lag1'])
    y2 = df2['y']
    model2 = sm.OLS(y2, X2).fit(cov_type='HC0')
    
    # Full model
    X_full = sm.add_constant(df['y_lag1'])
    y_full = df['y']
    model_full = sm.OLS(y_full, X_full).fit(cov_type='HC0')
    
    # Chow test statistic
    rss_full = np.sum(model_full.resid ** 2)
    rss_restricted = np.sum(model1.resid ** 2) + np.sum(model2.resid ** 2)
    k = 2  # Number of parameters in AR(1)
    n = len(df)
    
    chow_stat = ((rss_full - rss_restricted) / k) / ((rss_restricted) / (n - 2 * k))
    chow_pval = 1 - stats.f.cdf(chow_stat, k, n - 2 * k)
    
    return {
        'break_date': df.index[break_idx].strftime('%Y-%m-%d') if break_idx < len(df) else 'end',
        'break_index': break_idx,
        'n_before': len(df1),
        'n_after': len(df2),
        'beta_before': model1.params['y_lag1'],
        'beta_after': model2.params['y_lag1'],
        'r2_before': model1.rsquared,
        'r2_after': model2.rsquared,
        'r2_full': model_full.rsquared,
        'rss_full': rss_full,
        'rss_restricted': rss_restricted,
        'chow_statistic': chow_stat,
        'chow_pval': chow_pval,
        'significant_5pct': chow_pval < 0.05,
        'start': df.index[0].strftime('%Y-%m-%d'),
        'end': df.index[-1].strftime('%Y-%m-%d')
    }


def aggregate_frequency(series: pd.Series, freq: str = 'M',
                        start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict:
    """
    Aggregate time series to different frequencies (monthly, quarterly, etc.)
    
    Args:
        series: Time series with datetime index
        freq: 'D'=daily, 'W'=weekly, 'M'=monthly, 'Q'=quarterly, 'Y'=yearly
        start_date, end_date: Date range filters
    
    Returns:
        Dictionary with aggregated series and descriptive stats
    """
    if start_date or end_date:
        if start_date:
            series = series[series.index >= pd.to_datetime(start_date)]
        if end_date:
            series = series[series.index <= pd.to_datetime(end_date)]
    
    freq_map = {'D': 'D', 'W': 'W', 'M': 'M', 'Q': 'Q', 'Y': 'A'}
    if freq not in freq_map:
        return {'error': f'Invalid frequency. Use: {", ".join(freq_map.keys())}'}
    
    # Resample: take last value of each period
    agg = series.resample(freq_map[freq]).last()
    agg = agg.dropna()
    
    if len(agg) < 10:
        return {'error': f'Too few periods after aggregation (only {len(agg)})'}
    
    # Compute autocorrelation at aggregated frequency
    acf_vals = [agg.autocorr(lag=i) for i in range(1, min(6, len(agg)))]
    
    return {
        'frequency': freq,
        'freq_full': {'D': 'Daily', 'W': 'Weekly', 'M': 'Monthly', 'Q': 'Quarterly', 'Y': 'Yearly'}.get(freq),
        'n_original': len(series),
        'n_aggregated': len(agg),
        'values': agg.tolist(),
        'dates': [d.strftime('%Y-%m-%d') for d in agg.index],
        'mean': agg.mean(),
        'std': agg.std(),
        'min': agg.min(),
        'max': agg.max(),
        'autocorr': acf_vals,
        'start': series.index[0].strftime('%Y-%m-%d'),
        'end': series.index[-1].strftime('%Y-%m-%d')
    }


# ============================================================
# Output Formatters for Advanced Methods
# ============================================================


def format_arima(res: Dict) -> str:
    """Format ARIMA results."""
    if 'error' in res:
        return res['error']
    
    p, d, q = res['order']
    hook = f"ARIMA({p},{d},{q}): AIC={res['aic']:.2f}, RMSE={res['rmse']:.6f}, LB p={res['diagnostics']['ljung_box_pval']:.4f}"
    
    lines = _harvard_header(f"📊 ARIMA({p},{d},{q}) Model; {res['start']}–{res['end']}", hook)
    lines.append(f"Observations: {res['n_obs']} | AIC={res['aic']:.2f} | BIC={res['bic']:.2f} | RMSE={res['rmse']:.6f}")
    lines.append("")
    lines.append("<b>Model coefficients:</b>")
    for coef, val in res['coef'].items():
        pval = res['pvalues'].get(coef, np.nan)
        sig = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.10 else ""
        lines.append(f"  {coef}: {val:.6f} (p={pval:.4f}) {sig}")
    lines.append("")
    lines.append(f"<b>Diagnostics:</b> Mean residual = {res['diagnostics']['mean_residual']:.6f}, Std = {res['diagnostics']['residual_std']:.6f}")
    lines.append(f"Ljung-Box test (lag 5): p = {res['diagnostics']['ljung_box_pval']:.4f}")
    lines.append("")
    lines.append("<b>5-step ahead forecast:</b>")
    for i, fc in enumerate(res['forecast_next_5'], 1):
        lines.append(f"  t+{i}: {fc:.6f}")
    lines.append("")
    return "\n".join(lines)


def format_garch(res: Dict) -> str:
    """Format GARCH results."""
    if 'error' in res:
        return res['error']
    
    p, q = res['order']
    persist = res.get('persistence', 0)
    hook = f"GARCH({p},{q}): Mean vol={res['mean_volatility']:.4f}%, Persistence={persist:.4f}"
    
    lines = _harvard_header(f"📊 GARCH({p},{q}) Volatility Model; {res['start']}–{res['end']}", hook)
    lines.append(f"Observations: {res['n_obs']} | AIC={res['aic']:.2f} | BIC={res['bic']:.2f}")
    lines.append("")
    lines.append("<b>Volatility Statistics (basis points):</b>")
    lines.append(f"  Mean: {res['mean_volatility']:.4f}% | Max: {res['max_volatility']:.4f}% | Min: {res['min_volatility']:.4f}%")
    lines.append(f"  Current: {res['current_volatility']:.4f}%")
    lines.append("")
    lines.append(f"<b>Persistence (α+β):</b> {persist:.4f} {'[mean-reverting]' if persist < 1 else '[explosive]'}")
    lines.append("")
    lines.append("<b>5-day volatility forecast (%):</b>")
    for i, vol in enumerate(res['forecast_volatility_5d'], 1):
        lines.append(f"  t+{i}: {vol:.4f}")
    lines.append("")
    return "\n".join(lines)


def format_cointegration(res: Dict) -> str:
    """Format Johansen cointegration results."""
    if 'error' in res:
        return res['error']
    
    rank = res['rank']
    hook = f"Johansen test: {res['n_variables']} variables, rank={rank}, {res['n_obs']} obs"
    
    lines = _harvard_header(f"📊 Cointegration (Johansen); {res['start']}–{res['end']}", hook)
    lines.append(f"Variables: {', '.join(res['series_names'])} | Observations: {res['n_obs']}")
    lines.append("")
    lines.append("Cointegrating rank at 5% significance: " + str(rank))
    lines.append("")
    lines.append("Trace test statistics vs 5% critical values:")
    for i, (trace, crit) in enumerate(zip(res['trace_statistics'], res['critical_values_5pct'])):
        sig = "***" if trace > crit else ""
        lines.append(f"  r&lt;={i}: Trace={trace:.2f}, CV={crit:.2f} {sig}")
    lines.append("")
    if rank > 0:
        lines.append(f"First {min(rank, 2)} cointegrating vector(s):")
        for i, vec in enumerate(res['cointegrating_vectors'][:min(rank, 2)]):
            lines.append(f"  CV{i+1}: {vec}")
    
    # Plain English explanation
    lines.append("")
    lines.append("<b>What This Means:</b>")
    if rank > 0:
        lines.append(f"  * Variables share {rank} cointegrating relationship(s): they move together long-term.")
        lines.append(f"  * Even if individual variables drift, cointegrating combinations revert to equilibrium.")
    else:
        lines.append(f"  * No cointegration found: variables drift independently with no long-run equilibrium.")
    lines.append("")
    return "\n".join(lines)


def format_rolling_regression(res: Dict) -> str:
    """Format rolling regression results in Harvard style."""
    if 'error' in res:
        return res['error']
    
    mean_r2 = np.mean([r for r in res['rolling_r2'] if not np.isnan(r)])
    hook = f"Rolling regression (window={res['window']}d): Mean R2={mean_r2:.4f}, {res['n_windows']} windows"
    
    lines = _harvard_header(f"📊 Rolling Regression; {res['regressors']}", hook)
    lines.append(f"Window size: {res['window']} days | Number of windows: {res['n_windows']} | Mean R2: {mean_r2:.4f}")
    lines.append("")
    lines.append("<b>Time-varying coefficient estimates:</b>")
    for reg_name, coefs in res['rolling_coef'].items():
        mean_c = np.nanmean(coefs)
        std_c = np.nanstd(coefs)
        lines.append(f"  {reg_name}: mean={mean_c:.6f}, std={std_c:.6f}")
    lines.append("")
    lines.append(f"Period: {res['dates'][0]} to {res['dates'][-1]}")
    lines.append("")
    return "\n".join(lines)


def format_structural_break(res: Dict) -> str:
    """Format structural break (Chow test) results in Harvard style."""
    if 'error' in res:
        return res['error']
    
    sig_str = "SIGNIFICANT" if res['significant_5pct'] else "NOT significant"
    hook = f"Chow test at {res['break_date']}: F={res['chow_statistic']:.4f}, p={res['chow_pval']:.4f} [{sig_str}]"
    
    lines = _harvard_header(f"📊 Structural Break Test (Chow); {res['start']}–{res['end']}", hook)
    lines.append(f"Hypothesized break: {res['break_date']} | Before: {res['n_before']} obs | After: {res['n_after']} obs")
    lines.append("")
    lines.append("<b>AR(1) persistence before vs after break:</b>")
    lines.append(f"  Before: beta={res['beta_before']:.6f}, R2={res['r2_before']:.4f}")
    lines.append(f"  After:  beta={res['beta_after']:.6f}, R2={res['r2_after']:.4f}")
    lines.append(f"  Full:   R2={res['r2_full']:.4f}")
    lines.append("")
    lines.append(f"<b>Chow test:</b> F-statistic = {res['chow_statistic']:.4f}, p-value = {res['chow_pval']:.4f}")
    lines.append(f"Result: Structural break is {sig_str} at 5% level")
    lines.append("")
    return "\n".join(lines)
    return "\n".join(lines)


def format_aggregation(res: Dict) -> str:
    """Format frequency aggregation results in Harvard style."""
    if 'error' in res:
        return res['error']
    
    freq_full = res['freq_full']
    hook = f"Aggregated to {freq_full}: {res['n_original']} daily → {res['n_aggregated']} periods, mean={res['mean']:.6f}"
    
    lines = _harvard_header(f"📊 {freq_full} Aggregation; {res['start']}–{res['end']}", hook)
    lines.append(f"Original (daily): {res['n_original']} obs | Aggregated ({freq_full}): {res['n_aggregated']} obs")
    lines.append("")
    lines.append(f"<b>Summary statistics ({freq_full}):</b>")
    lines.append(f"  Mean:   {res['mean']:.6f}")
    lines.append(f"  Std:    {res['std']:.6f}")
    lines.append(f"  Min:    {res['min']:.6f}")
    lines.append(f"  Max:    {res['max']:.6f}")
    lines.append("")
    lines.append("<b>Autocorrelation at aggregated frequency:</b>")
    for i, acf in enumerate(res['autocorr'], 1):
        lines.append(f"  lag {i}: {acf:.4f}")
    lines.append("")
    return "\n".join(lines)
