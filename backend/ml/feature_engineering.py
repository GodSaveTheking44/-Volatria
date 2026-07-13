import pandas as pd
import numpy as np
from typing import Tuple

def construct_forecasting_features(df_prices: pd.DataFrame, lags: int = 5) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Constructs lags and rolling indicators for model training.
    df_prices must contain 'close'.
    Returns (features_df, target_series).
    """
    df = df_prices.copy()
    df["returns"] = df["close"].pct_change()
    
    feature_cols = []
    # Create lag features
    for lag in range(1, lags + 1):
        col_name = f"lag_{lag}"
        df[col_name] = df["returns"].shift(lag)
        feature_cols.append(col_name)
        
    # Create rolling volatility and momentum
    df["rolling_std"] = df["returns"].rolling(window=10).std()
    df["rolling_mean"] = df["returns"].rolling(window=10).mean()
    
    feature_cols.extend(["rolling_std", "rolling_mean"])
    
    # Target is next step return
    df["target"] = df["returns"].shift(-1)
    
    df.dropna(inplace=True)
    
    return df[feature_cols], df["target"]

def scale_features_minmax(features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs standard min-max scaling of columns.
    """
    df = features_df.copy()
    for col in df.columns:
        col_min = df[col].min()
        col_max = df[col].max()
        if col_max - col_min > 1e-8:
            df[col] = (df[col] - col_min) / (col_max - col_min)
        else:
            df[col] = 0.0
    return df
