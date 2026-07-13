import numpy as np
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.api.v1.portfolio import seed_default_portfolio_if_empty
from backend.domain.risk.exposure import (
    calculate_parametric_var,
    calculate_historical_var,
    calculate_expected_shortfall,
    run_stress_scenarios
)

router = APIRouter(prefix="/risk", tags=["Risk Management"])

@router.get("/metrics")
def get_risk_analysis(db: Session = Depends(get_db)):
    port = seed_default_portfolio_if_empty(db)
    portfolio_value = port.net_asset_value
    
    # Generate 252 trading days of simulated historical daily returns (drift=5% annually, volatility=15% annually)
    np.random.seed(101)
    daily_returns = np.random.normal(0.05 / 252.0, 0.15 / np.sqrt(252.0), 252)
    
    # Calculate VaR and ES
    param_var_95 = calculate_parametric_var(portfolio_value, daily_returns, 0.95)
    hist_var_95 = calculate_historical_var(portfolio_value, daily_returns, 0.95)
    es_95 = calculate_expected_shortfall(portfolio_value, daily_returns, 0.95)
    
    # Scenario stresses: estimate option greeks exposure mapping
    # Delta exposure: total equity market value (approx portfolio_value - cash)
    delta_exp = portfolio_value - port.cash
    vega_exp = 25000.0 # simulated vega exposure of option hedges
    rho_exp = 10000.0 # simulated interest rate exposure
    
    stress_results = run_stress_scenarios(portfolio_value, delta_exp, vega_exp, rho_exp)
    
    return {
        "portfolio_value": portfolio_value,
        "metrics_95_pct": {
            "parametric_var": param_var_95,
            "historical_var": hist_var_95,
            "expected_shortfall": es_95
        },
        "stress_scenarios": stress_results
    }
