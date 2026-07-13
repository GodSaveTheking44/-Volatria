import numpy as np
from typing import Tuple

def fit_linear_regression(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Fits an OLS linear regression model.
    X: matrix of shape (n_samples, n_features)
    y: vector of shape (n_samples,)
    Returns (coefficients, intercept).
    """
    n_samples, n_features = X.shape
    # Add intercept column
    X_design = np.hstack([np.ones((n_samples, 1)), X])
    
    # Solve (XT * X) * beta = XT * y
    beta = np.linalg.solve(np.dot(X_design.T, X_design), np.dot(X_design.T, y))
    
    intercept = float(beta[0])
    coefficients = beta[1:]
    
    return coefficients, intercept

def forecast_ar1(values: np.ndarray) -> float:
    """
    Fits an AR(1) model to a time series and forecasts the next step.
    y_t = alpha + beta * y_t-1 + epsilon
    """
    if len(values) < 3:
        return float(values[-1])
        
    x_train = values[:-1].reshape(-1, 1)
    y_train = values[1:]
    
    coef, intercept = fit_linear_regression(x_train, y_train)
    beta = float(coef[0])
    
    next_val = intercept + beta * values[-1]
    return next_val
