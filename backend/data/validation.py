import pandas as pd
import numpy as np

def validate_ohlcv_schema(df: pd.DataFrame) -> bool:
    required_cols = {"open", "high", "low", "close", "volume"}
    return required_cols.issubset(df.columns)

def clean_missing_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans DataFrame by interpolating missing numeric values and forward/backward filling remaining gaps.
    """
    df_clean = df.copy()
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    
    # Interpolate intermediate gaps
    df_clean[numeric_cols] = df_clean[numeric_cols].interpolate(method="linear")
    # Forward-fill and backward-fill boundary gaps
    df_clean[numeric_cols] = df_clean[numeric_cols].ffill().bfill()
    
    return df_clean

def detect_outliers_rolling_zscore(series: pd.Series, window: int = 20, threshold: float = 3.0) -> pd.Series:
    """
    Returns boolean series where True indicates the value is an outlier (beyond threshold std devs from rolling mean).
    """
    rolling_mean = series.rolling(window=window, min_periods=1).mean()
    rolling_std = series.rolling(window=window, min_periods=1).std().fillna(0.0)
    
    z_scores = np.abs((series - rolling_mean) / np.where(rolling_std == 0, 1.0, rolling_std))
    return z_scores > threshold
