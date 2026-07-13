import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from backend.backtesting.execution import TransactionCostModel
from backend.backtesting.metrics import generate_backtest_metrics_summary

class EventDrivenBacktestEngine:
    def __init__(self, initial_cash: float = 100000.0, commission_pct: float = 0.0005, slippage_pct: float = 0.0002):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.execution_model = TransactionCostModel(commission_pct=commission_pct, slippage_pct=slippage_pct)
        
        # Portfolio state
        self.pos_x = 0.0
        self.pos_y = 0.0
        self.portfolio_values: List[float] = []
        self.trades_pnl: List[float] = []
        self.trade_logs: List[Dict[str, Any]] = []
        
        # Active trade tracker
        self.active_trade = None  # None, "LONG_SPREAD", or "SHORT_SPREAD"
        self.entry_cash_val = 0.0
        self.entry_beta = 0.0
        self.entry_price_x = 0.0
        self.entry_price_y = 0.0

    def get_portfolio_value(self, price_x: float, price_y: float) -> float:
        return self.cash + (self.pos_x * price_x) + (self.pos_y * price_y)

    def execute_buy_spread(self, price_x: float, price_y: float, beta: float, timestamp: Any):
        """
        Long the spread: buy Asset Y and sell beta * Asset X
        """
        qty_y = 100.0
        qty_x = qty_y * beta
        
        # Slippage + impact prices
        exec_price_y = self.execution_model.calculate_execution_price(price_y, "BUY", qty_y)
        exec_price_x = self.execution_model.calculate_execution_price(price_x, "SELL", qty_x)
        
        # Commissions
        comm_y = self.execution_model.calculate_commission(exec_price_y, qty_y)
        comm_x = self.execution_model.calculate_commission(exec_price_x, qty_x)
        
        # Update cash
        self.cash -= (qty_y * exec_price_y)  # bought Y
        self.cash += (qty_x * exec_price_x)  # shorted X
        self.cash -= (comm_y + comm_x)        # fees
        
        self.pos_y += qty_y
        self.pos_x -= qty_x
        
        self.active_trade = "LONG_SPREAD"
        self.entry_cash_val = self.get_portfolio_value(price_x, price_y)
        self.entry_beta = beta
        self.entry_price_x = price_x
        self.entry_price_y = price_y
        
        self.trade_logs.append({
            "timestamp": str(timestamp),
            "type": "ENTRY_LONG",
            "price_x": price_x,
            "price_y": price_y,
            "qty_x": -qty_x,
            "qty_y": qty_y,
            "cash": self.cash
        })

    def execute_sell_spread(self, price_x: float, price_y: float, beta: float, timestamp: Any):
        """
        Short the spread: sell Asset Y and buy beta * Asset X
        """
        qty_y = 100.0
        qty_x = qty_y * beta
        
        # Slippage + impact prices
        exec_price_y = self.execution_model.calculate_execution_price(price_y, "SELL", qty_y)
        exec_price_x = self.execution_model.calculate_execution_price(price_x, "BUY", qty_x)
        
        # Commissions
        comm_y = self.execution_model.calculate_commission(exec_price_y, qty_y)
        comm_x = self.execution_model.calculate_commission(exec_price_x, qty_x)
        
        # Update cash
        self.cash += (qty_y * exec_price_y)  # shorted Y
        self.cash -= (qty_x * exec_price_x)  # bought X
        self.cash -= (comm_y + comm_x)        # fees
        
        self.pos_y -= qty_y
        self.pos_x += qty_x
        
        self.active_trade = "SHORT_SPREAD"
        self.entry_cash_val = self.get_portfolio_value(price_x, price_y)
        self.entry_beta = beta
        self.entry_price_x = price_x
        self.entry_price_y = price_y
        
        self.trade_logs.append({
            "timestamp": str(timestamp),
            "type": "ENTRY_SHORT",
            "price_x": price_x,
            "price_y": price_y,
            "qty_x": qty_x,
            "qty_y": -qty_y,
            "cash": self.cash
        })

    def execute_exit(self, price_x: float, price_y: float, timestamp: Any):
        """
        Close all active spread positions.
        """
        if self.active_trade is None:
            return
            
        qty_y = abs(self.pos_y)
        qty_x = abs(self.pos_x)
        
        # Unwind Y
        side_y = "SELL" if self.pos_y > 0 else "BUY"
        exec_price_y = self.execution_model.calculate_execution_price(price_y, side_y, qty_y)
        comm_y = self.execution_model.calculate_commission(exec_price_y, qty_y)
        
        if side_y == "SELL":
            self.cash += (qty_y * exec_price_y)
        else:
            self.cash -= (qty_y * exec_price_y)
        self.cash -= comm_y
        
        # Unwind X
        side_x = "SELL" if self.pos_x > 0 else "BUY"
        exec_price_x = self.execution_model.calculate_execution_price(price_x, side_x, qty_x)
        comm_x = self.execution_model.calculate_commission(exec_price_x, qty_x)
        
        if side_x == "SELL":
            self.cash += (qty_x * exec_price_x)
        else:
            self.cash -= (qty_x * exec_price_x)
        self.cash -= comm_x
        
        # Clear positions
        self.pos_x = 0.0
        self.pos_y = 0.0
        
        exit_val = self.get_portfolio_value(price_x, price_y)
        pnl = exit_val - self.entry_cash_val
        self.trades_pnl.append(pnl)
        
        self.trade_logs.append({
            "timestamp": str(timestamp),
            "type": "EXIT",
            "price_x": price_x,
            "price_y": price_y,
            "pnl": pnl,
            "cash": self.cash
        })
        self.active_trade = None

    def run_backtest(
        self, df_prices: pd.DataFrame, z_scores: List[float], betas: List[float], entry_z: float = 2.0, exit_z: float = 0.5
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Executes event-driven backtest on Asset_X and Asset_Y.
        """
        n_bars = len(df_prices)
        x_prices = df_prices["Asset_X"].values
        y_prices = df_prices["Asset_Y"].values
        timestamps = df_prices.index.values
        
        # Reset state
        self.cash = self.initial_cash
        self.pos_x = 0.0
        self.pos_y = 0.0
        self.portfolio_values = []
        self.trades_pnl = []
        self.trade_logs = []
        self.active_trade = None
        
        # Replay event loop
        for t in range(n_bars):
            price_x = x_prices[t]
            price_y = y_prices[t]
            z = z_scores[t]
            beta = betas[t]
            ts = timestamps[t]
            
            # 1. State assessment & trade exits
            if self.active_trade == "LONG_SPREAD" and z >= -exit_z:
                self.execute_exit(price_x, price_y, ts)
            elif self.active_trade == "SHORT_SPREAD" and z <= exit_z:
                self.execute_exit(price_x, price_y, ts)
                
            # 2. Trade entry signals
            if self.active_trade is None:
                if z <= -entry_z:
                    self.execute_buy_spread(price_x, price_y, beta, ts)
                elif z >= entry_z:
                    self.execute_sell_spread(price_x, price_y, beta, ts)
                    
            # 3. Mark to market portfolio value
            current_val = self.get_portfolio_value(price_x, price_y)
            self.portfolio_values.append(current_val)
            
        # Clean up exit at final step if still holding
        if self.active_trade is not None:
            self.execute_exit(x_prices[-1], y_prices[-1], timestamps[-1])
            self.portfolio_values[-1] = self.get_portfolio_value(x_prices[-1], y_prices[-1])
            
        port_values_arr = np.array(self.portfolio_values)
        metrics = generate_backtest_metrics_summary(port_values_arr, self.trades_pnl)
        
        return port_values_arr, metrics
