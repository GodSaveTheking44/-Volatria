import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

def calculate_mean(values: np.ndarray) -> float:
    return float(np.mean(values))

def calculate_variance(values: np.ndarray, ddof: int = 1) -> float:
    return float(np.var(values, ddof=ddof))

def calculate_covariance(x: np.ndarray, y: np.ndarray, ddof: int = 1) -> float:
    return float(np.cov(x, y, ddof=ddof)[0, 1])

def calculate_correlation(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.corrcoef(x, y)[0, 1])

def analyze_distribution(values: np.ndarray) -> Dict[str, float]:
    """
    Computes summary metrics for a return distribution, including skewness and kurtosis.
    """
    series = pd.Series(values)
    return {
        "mean": float(series.mean()),
        "std": float(series.std()),
        "skewness": float(series.skew()),
        "kurtosis": float(series.kurtosis()),
        "median": float(series.median()),
        "min": float(series.min()),
        "max": float(series.max())
    }

def calculate_rolling_statistics(values: np.ndarray, window: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes rolling mean and standard deviation.
    """
    series = pd.Series(values)
    rolling_mean = series.rolling(window=window, min_periods=1).mean().values
    rolling_std = series.rolling(window=window, min_periods=1).std().fillna(0.0).values
    return rolling_mean, rolling_std
