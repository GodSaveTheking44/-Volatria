import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional

def calculate_cagr(portfolio_values: np.ndarray, n_days: int) -> float:
    if len(portfolio_values) < 2 or portfolio_values[0] <= 0:
        return 0.0
    years = n_days / 252.0
    if years <= 0:
        return 0.0
    cagr = (portfolio_values[-1] / portfolio_values[0]) ** (1.0 / years) - 1.0
    return float(cagr)

def calculate_max_drawdown(portfolio_values: np.ndarray) -> float:
    if len(portfolio_values) == 0:
        return 0.0
    peak = portfolio_values[0]
    max_dd = 0.0
    for v in portfolio_values:
        if v > peak:
            peak = v
        dd = (v - peak) / peak
        if dd < max_dd:
            max_dd = dd
    return float(max_dd)

def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.0, annualization_factor: float = 252.0) -> float:
    if len(returns) == 0:
        return 0.0
    # Annualize returns and standard deviation
    mean_ret = np.mean(returns)
    std_ret = np.std(returns)
    if std_ret < 1e-8:
        return 0.0
    # Sharpe = (mean_ret - rf_daily) / std_ret * sqrt(252)
    rf_daily = risk_free_rate / annualization_factor
    sharpe = (mean_ret - rf_daily) / std_ret * np.sqrt(annualization_factor)
    return float(sharpe)

def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.0, annualization_factor: float = 252.0) -> float:
    if len(returns) == 0:
        return 0.0
    mean_ret = np.mean(returns)
    rf_daily = risk_free_rate / annualization_factor
    downside_returns = returns[returns < rf_daily]
    if len(downside_returns) == 0:
        return 0.0
    downside_std = np.std(downside_returns)
    if downside_std < 1e-8:
        return 0.0
    sortino = (mean_ret - rf_daily) / downside_std * np.sqrt(annualization_factor)
    return float(sortino)

def calculate_calmar_ratio(cagr: float, max_dd: float) -> float:
    abs_dd = abs(max_dd)
    if abs_dd < 1e-8:
        return 0.0
    return float(cagr / abs_dd)

def calculate_alpha_beta(strategy_returns: np.ndarray, benchmark_returns: np.ndarray, risk_free_rate: float = 0.0) -> Tuple[float, float]:
    """
    Computes annualized Alpha and Beta coefficients against a benchmark index.
    """
    if len(strategy_returns) != len(benchmark_returns) or len(strategy_returns) == 0:
        return 0.0, 1.0
        
    cov = np.cov(strategy_returns, benchmark_returns)
    beta = cov[0, 1] / cov[1, 1] if cov[1, 1] > 1e-8 else 1.0
    
    # Annualized mean returns
    ann_strat = np.mean(strategy_returns) * 252.0
    ann_bench = np.mean(benchmark_returns) * 252.0
    
    alpha = (ann_strat - risk_free_rate) - beta * (ann_bench - risk_free_rate)
    return float(alpha), float(beta)

def calculate_information_ratio(strategy_returns: np.ndarray, benchmark_returns: np.ndarray) -> float:
    if len(strategy_returns) != len(benchmark_returns) or len(strategy_returns) == 0:
        return 0.0
    active_returns = strategy_returns - benchmark_returns
    mean_active = np.mean(active_returns)
    std_active = np.std(active_returns)
    if std_active < 1e-8:
        return 0.0
    ir = mean_active / std_active * np.sqrt(252.0)
    return float(ir)

def generate_backtest_metrics_summary(portfolio_values: np.ndarray, trades_pnl: List[float], benchmark_values: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """
    Consolidates performance attribution metrics for a portfolio simulation run.
    """
    p_series = pd.Series(portfolio_values)
    returns = p_series.pct_change().dropna().values
    
    n_days = len(portfolio_values)
    cagr = calculate_cagr(portfolio_values, n_days)
    max_dd = calculate_max_drawdown(portfolio_values)
    sharpe = calculate_sharpe_ratio(returns)
    sortino = calculate_sortino_ratio(returns)
    calmar = calculate_calmar_ratio(cagr, max_dd)
    
    # Trade specific win rate
    win_rate = 0.0
    if trades_pnl:
        positive_trades = sum(1 for t in trades_pnl if t > 0)
        win_rate = positive_trades / len(trades_pnl)
        
    summary = {
        "cagr": cagr,
        "max_drawdown": max_dd,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "calmar_ratio": calmar,
        "win_rate": win_rate,
        "total_trades": len(trades_pnl)
    }
    
    if benchmark_values is not None and len(benchmark_values) == len(portfolio_values):
        b_series = pd.Series(benchmark_values)
        b_returns = b_series.pct_change().dropna().values
        alpha, beta = calculate_alpha_beta(returns, b_returns)
        ir = calculate_information_ratio(returns, b_returns)
        summary.update({
            "alpha": alpha,
            "beta": beta,
            "information_ratio": ir
        })
        
    return summary
