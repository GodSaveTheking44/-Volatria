import os
import json
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.models import Strategy, Backtest
from backend.quant.forecasting import fit_linear_regression
from backend.quant.statistics import calculate_rolling_statistics
from backend.backtesting.engine import EventDrivenBacktestEngine
from backend.reporting.performance_reports import generate_performance_html_report

router = APIRouter(prefix="/backtests", tags=["Backtests"])

def ensure_pairs_data() -> pd.DataFrame:
    """
    Returns the cointegrated pairs dataframe. Generates it dynamically if missing.
    """
    path = "research/results/pairs_data.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
        
    # Generate synthetic cointegrated prices
    np.random.seed(42)
    N = 500
    x = 100.0 + np.cumsum(np.random.normal(0, 1.0, N))
    z = np.zeros(N)
    for t in range(1, N):
        z[t] = 0.8 * z[t-1] + np.random.normal(0, 0.5)
        
    y = 1.5 * x + 10.0 + z
    df = pd.DataFrame({
        "Date": [f"2026-01-{i:03d}" for i in range(1, N+1)],
        "Asset_X": x,
        "Asset_Y": y
    })
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    return df

@router.post("/run")
def run_backtest_endpoint(
    strategy_name: str = Query("Stat-Arb Pairs", description="Name of strategy"),
    entry_z: float = 2.0,
    exit_z: float = 0.5,
    db: Session = Depends(get_db)
):
    # Ensure strategy exists in DB
    strategy = db.query(Strategy).filter_by(name=strategy_name).first()
    if not strategy:
        strategy = Strategy(name=strategy_name, description="Auto-registered during backtest")
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        
    df = ensure_pairs_data()
    
    # 1. Engle-Granger regression fit
    x = df["Asset_X"].values
    y = df["Asset_Y"].values
    
    # Fit OLS
    beta, alpha = fit_linear_regression(x.reshape(-1, 1), y)
    spread = y - (beta * x + alpha)
    
    # 2. Compute rolling z-score of spread
    rolling_mean, rolling_std = calculate_rolling_statistics(spread, window=20)
    # Prevent divide by zero
    rolling_std = np.where(rolling_std == 0, 1.0, rolling_std)
    z_scores = ((spread - rolling_mean) / rolling_std).tolist()
    betas = [float(beta[0])] * len(df)
    
    # 3. Execute backtest engine
    engine = EventDrivenBacktestEngine()
    portfolio_values, metrics = engine.run_backtest(df, z_scores, betas, entry_z=entry_z, exit_z=exit_z)
    
    # 4. Save backtest run results to database
    backtest_rec = Backtest(
        strategy_id=strategy.id,
        name=f"Run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        start_date=pd.to_datetime(df["Date"].iloc[0]).to_pydatetime() if "-" in str(df["Date"].iloc[0]) else datetime.utcnow(),
        end_date=pd.to_datetime(df["Date"].iloc[-1]).to_pydatetime() if "-" in str(df["Date"].iloc[-1]) else datetime.utcnow(),
        sharpe=metrics["sharpe_ratio"],
        max_drawdown=metrics["max_drawdown"],
        cagr=metrics["cagr"],
        win_rate=metrics["win_rate"]
    )
    db.add(backtest_rec)
    db.commit()
    db.refresh(backtest_rec)
    
    return {
        "backtest_id": backtest_rec.id,
        "metrics": metrics,
        "trades": engine.trade_logs[-50:],
        "portfolio_values": portfolio_values.tolist()
    }

@router.get("/report", response_class=HTMLResponse)
def get_backtest_report_html(entry_z: float = 2.0, exit_z: float = 0.5):
    df = ensure_pairs_data()
    x = df["Asset_X"].values
    y = df["Asset_Y"].values
    
    beta, alpha = fit_linear_regression(x.reshape(-1, 1), y)
    spread = y - (beta * x + alpha)
    
    rolling_mean, rolling_std = calculate_rolling_statistics(spread, window=20)
    rolling_std = np.where(rolling_std == 0, 1.0, rolling_std)
    z_scores = ((spread - rolling_mean) / rolling_std).tolist()
    betas = [float(beta[0])] * len(df)
    
    engine = EventDrivenBacktestEngine()
    _, metrics = engine.run_backtest(df, z_scores, betas, entry_z=entry_z, exit_z=exit_z)
    
    html = generate_performance_html_report(metrics, engine.trade_logs)
    return html

# We need datetime for DB model insertions
from datetime import datetime
