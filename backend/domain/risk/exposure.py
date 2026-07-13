import numpy as np
from typing import Dict, Any

def calculate_parametric_var(portfolio_value: float, returns: np.ndarray, confidence_level: float = 0.95) -> float:
    """
    Computes parametric Value at Risk (VaR) using normal distribution assumption.
    """
    if len(returns) == 0:
        return 0.0
    mean_ret = np.mean(returns)
    std_ret = np.std(returns)
    
    # Z-score for confidence level
    z_score = 1.64485 if confidence_level == 0.95 else 2.32635
    var_percent = z_score * std_ret - mean_ret
    return float(max(0.0, var_percent * portfolio_value))

def calculate_historical_var(portfolio_value: float, returns: np.ndarray, confidence_level: float = 0.95) -> float:
    """
    Computes historical Value at Risk (VaR) from actual return distributions.
    """
    if len(returns) == 0:
        return 0.0
    percentile = (1.0 - confidence_level) * 100
    var_percent = -np.percentile(returns, percentile)
    return float(max(0.0, var_percent * portfolio_value))

def calculate_expected_shortfall(portfolio_value: float, returns: np.ndarray, confidence_level: float = 0.95) -> float:
    """
    Computes Expected Shortfall (ES) / Conditional VaR.
    """
    if len(returns) == 0:
        return 0.0
    percentile = (1.0 - confidence_level) * 100
    cutoff = np.percentile(returns, percentile)
    
    tail_returns = returns[returns <= cutoff]
    if len(tail_returns) == 0:
        return 0.0
    es_percent = -np.mean(tail_returns)
    return float(max(0.0, es_percent * portfolio_value))

def run_stress_scenarios(portfolio_value: float, delta_exposure: float, vega_exposure: float, rho_exposure: float) -> Dict[str, float]:
    """
    Simulates portfolio shocks and estimates P&L impact.
    """
    # 1. Market Crash: Spot decreases by 10%
    crash_impact = delta_exposure * (-0.10)
    
    # 2. Volatility Spike: Volatility increases by 50%
    vol_impact = vega_exposure * (0.50)
    
    # 3. Interest Rate Shock: Rates increase by 2.0% (+200 bps)
    rate_impact = rho_exposure * (0.02)
    
    return {
        "market_crash_impact": float(crash_impact),
        "volatility_spike_impact": float(vol_impact),
        "interest_rate_shock_impact": float(rate_impact),
        "post_crash_value": float(portfolio_value + crash_impact),
        "post_vol_spike_value": float(portfolio_value + vol_impact),
        "post_rate_shock_value": float(portfolio_value + rate_impact)
    }
