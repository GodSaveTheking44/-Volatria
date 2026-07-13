import pandas as pd
import numpy as np

def calculate_momentum_factor(prices: pd.Series, window: int = 14) -> pd.Series:
    """
    Computes Rate of Change (ROC) momentum factor.
    """
    return prices.pct_change(periods=window)

def calculate_volatility_factor(returns: pd.Series, window: int = 14) -> pd.Series:
    """
    Computes rolling realized volatility factor.
    """
    return returns.rolling(window=window).std() * np.sqrt(252)

def calculate_rsi_factor(prices: pd.Series, window: int = 14) -> pd.Series:
    """
    Computes Relative Strength Index (RSI) momentum factor.
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / np.where(loss == 0, 1e-8, loss)
    rsi = 100 - (100 / (1 + rs))
    return rsi
