import pytest
import numpy as np
import pandas as pd
from backend.quant.statistics import calculate_mean, calculate_variance, calculate_correlation
from backend.quant.probability import normal_pdf, normal_cdf, bayesian_normal_mean_update
from backend.quant.optimization import maximize_sharpe_ratio, calculate_risk_parity_weights
from backend.quant.pricing import black_scholes_price, binomial_tree_price, lsm_monte_carlo_price
from backend.data.validation import clean_missing_data, detect_outliers_rolling_zscore
from backend.backtesting.metrics import calculate_sharpe_ratio, calculate_max_drawdown, calculate_cagr
from backend.ml.feature_engineering import construct_forecasting_features

def test_quant_statistics():
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert calculate_mean(data) == pytest.approx(3.0)
    assert calculate_variance(data) == pytest.approx(2.5)
    
    y = np.array([2.0, 4.0, 5.0, 4.0, 5.0])
    corr = calculate_correlation(data, y)
    assert corr > 0.5

def test_quant_probability():
    # PDF/CDF checks
    assert normal_pdf(0.0) == pytest.approx(0.3989422804)
    assert normal_cdf(0.0) == pytest.approx(0.5)
    
    # Bayesian updates
    post_mean, post_var = bayesian_normal_mean_update(
        prior_mean=100.0, prior_var=10.0, sample_mean=105.0, sample_var=5.0, n_samples=10
    )
    assert post_mean > 100.0
    assert post_var < 10.0

def test_quant_optimization():
    expected_returns = np.array([0.12, 0.15, 0.10])
    cov_matrix = np.array([
        [0.04, 0.01, 0.02],
        [0.01, 0.09, 0.01],
        [0.02, 0.01, 0.05]
    ])
    
    # Sharpe maximization
    sharpe_res = maximize_sharpe_ratio(expected_returns, cov_matrix, risk_free_rate=0.02)
    assert sum(sharpe_res["weights"]) == pytest.approx(1.0)
    
    # Risk Parity
    risk_res = calculate_risk_parity_weights(cov_matrix)
    assert sum(risk_res["weights"]) == pytest.approx(1.0)

def test_pricing_routers():
    # S=100, K=100, r=5%, T=1, vol=20%
    bs_call = black_scholes_price(100.0, 100.0, 0.05, 1.0, 0.20, is_call=True)
    assert bs_call == pytest.approx(10.450583, abs=1e-4)
    
    # Numerical tests
    binom_val = binomial_tree_price(100.0, 100.0, 0.05, 1.0, 0.20, steps=50, is_call=True, is_american=False)
    assert binom_val == pytest.approx(bs_call, abs=0.1)
    
    lsm_val = lsm_monte_carlo_price(100.0, 100.0, 0.05, 1.0, 0.20, paths=5000, steps=20, is_call=False, is_american=True)
    assert lsm_val > 0.0

def test_data_validation():
    df = pd.DataFrame({"close": [10.0, np.nan, 12.0, 13.0, 12.0], "volume": [100, 120, np.nan, 130, 140]})
    df_clean = clean_missing_data(df)
    assert not df_clean.isnull().any().any()
    assert df_clean["close"].iloc[1] == 11.0
    
    # Outlier detection
    prices = pd.Series([100.0]*10 + [150.0] + [100.0]*9)
    outliers = detect_outliers_rolling_zscore(prices, window=10, threshold=2.0)
    assert outliers.iloc[10] == True
    assert outliers.iloc[0] == False

def test_backtest_metrics():
    port_vals = np.array([100.0, 101.0, 100.5, 102.0, 103.5])
    returns = np.array([0.01, -0.005, 0.015, 0.015])
    
    sharpe = calculate_sharpe_ratio(returns)
    assert sharpe > 0.0
    
    max_dd = calculate_max_drawdown(port_vals)
    assert max_dd == pytest.approx(-0.00495, abs=1e-5) # peak=101, val=100.5 -> dd = -0.5/101 = -0.00495049
    
    cagr = calculate_cagr(port_vals, len(port_vals))
    assert cagr > 0.0

def test_ml_pipeline():
    prices_df = pd.DataFrame({
        "close": [100.0 + i + (i%2)*0.5 for i in range(20)]
    })
    X, y = construct_forecasting_features(prices_df, lags=3)
    assert len(X) > 0
    assert X.shape[1] == 5 # 3 lags + 2 rolling metrics
