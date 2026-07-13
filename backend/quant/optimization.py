import numpy as np
from scipy.optimize import minimize
from typing import Dict, Any, List, Tuple

def calculate_portfolio_performance(weights: np.ndarray, expected_returns: np.ndarray, cov_matrix: np.ndarray) -> Tuple[float, float]:
    port_return = np.dot(weights, expected_returns)
    port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    return port_return, port_vol

def maximize_sharpe_ratio(
    expected_returns: np.ndarray, cov_matrix: np.ndarray, risk_free_rate: float = 0.0, max_weight: float = 1.0
) -> Dict[str, Any]:
    n_assets = len(expected_returns)
    
    # Objective function is negative Sharpe ratio
    def objective(weights):
        p_ret, p_vol = calculate_portfolio_performance(weights, expected_returns, cov_matrix)
        if p_vol < 1e-8:
            return 0.0
        return - (p_ret - risk_free_rate) / p_vol
        
    bounds = tuple((0.0, max_weight) for _ in range(n_assets))
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    
    init_weights = np.ones(n_assets) / n_assets
    result = minimize(objective, init_weights, method="SLSQP", bounds=bounds, constraints=constraints)
    
    opt_weights = result.x
    p_ret, p_vol = calculate_portfolio_performance(opt_weights, expected_returns, cov_matrix)
    
    return {
        "weights": opt_weights.tolist(),
        "expected_return": p_ret,
        "volatility": p_vol,
        "sharpe_ratio": (p_ret - risk_free_rate) / p_vol if p_vol > 0 else 0.0
    }

def minimize_portfolio_variance(expected_returns: np.ndarray, cov_matrix: np.ndarray) -> Dict[str, Any]:
    n_assets = len(expected_returns)
    
    def objective(weights):
        return np.dot(weights.T, np.dot(cov_matrix, weights))
        
    bounds = tuple((0.0, 1.0) for _ in range(n_assets))
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    
    init_weights = np.ones(n_assets) / n_assets
    result = minimize(objective, init_weights, method="SLSQP", bounds=bounds, constraints=constraints)
    
    opt_weights = result.x
    p_ret, p_vol = calculate_portfolio_performance(opt_weights, expected_returns, cov_matrix)
    
    return {
        "weights": opt_weights.tolist(),
        "expected_return": p_ret,
        "volatility": p_vol,
        "variance": p_vol**2
    }

def calculate_risk_parity_weights(cov_matrix: np.ndarray) -> Dict[str, Any]:
    """
    Computes portfolio weights such that the risk contribution of each asset is equal.
    """
    n_assets = cov_matrix.shape[0]
    
    def objective(weights):
        # Marginal risk contribution
        port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        marginal_contrib = np.dot(cov_matrix, weights) / port_vol
        # Asset risk contribution
        risk_contrib = weights * marginal_contrib
        # We want to minimize the sum of squared differences of risk contributions
        diffs = risk_contrib[:, None] - risk_contrib[None, :]
        return float(np.sum(diffs**2))
        
    bounds = tuple((0.0, 1.0) for _ in range(n_assets))
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    
    init_weights = np.ones(n_assets) / n_assets
    result = minimize(objective, init_weights, method="SLSQP", bounds=bounds, constraints=constraints)
    
    opt_weights = result.x
    port_vol = np.sqrt(np.dot(opt_weights.T, np.dot(cov_matrix, opt_weights)))
    
    return {
        "weights": opt_weights.tolist(),
        "volatility": port_vol
    }

def generate_efficient_frontier(
    expected_returns: np.ndarray, cov_matrix: np.ndarray, n_points: int = 20
) -> List[Tuple[float, float]]:
    """
    Generates a list of (volatility, return) tuples representing the Efficient Frontier.
    """
    min_ret = float(np.min(expected_returns))
    max_ret = float(np.max(expected_returns))
    
    target_returns = np.linspace(min_ret, max_ret, n_points)
    n_assets = len(expected_returns)
    frontier_points = []
    
    for target in target_returns:
        def objective(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))
            
        bounds = tuple((0.0, 1.0) for _ in range(n_assets))
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
            {"type": "eq", "fun": lambda w: np.dot(w, expected_returns) - target}
        ]
        
        init_weights = np.ones(n_assets) / n_assets
        result = minimize(objective, init_weights, method="SLSQP", bounds=bounds, constraints=constraints)
        
        if result.success:
            p_vol = np.sqrt(result.fun)
            frontier_points.append((float(p_vol), float(target)))
            
    return frontier_points
