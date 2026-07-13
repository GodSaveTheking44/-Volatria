from typing import Dict, Any, List

def generate_performance_html_report(metrics: Dict[str, Any], trade_logs: List[Dict[str, Any]]) -> str:
    """
    Generates a stylized HTML performance report summarizing backtest results.
    """
    trade_rows = ""
    for idx, t in enumerate(trade_logs[-50:]): # Show last 50 trades
        pnl_val = t.get("pnl", "-")
        pnl_str = f"{pnl_val:.2f}" if isinstance(pnl_val, (int, float)) else str(pnl_val)
        trade_rows += f"""
        <tr>
            <td>{t.get("timestamp")}</td>
            <td>{t.get("type")}</td>
            <td>{t.get("price_x", 0.0):.2f}</td>
            <td>{t.get("price_y", 0.0):.2f}</td>
            <td>{pnl_str}</td>
            <td>{t.get("cash", 0.0):.2f}</td>
        </tr>
        """
        
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Volatria Backtest Performance Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #121212; color: #e0e0e0; margin: 30px; }}
            h1, h2 {{ color: #ff9f1c; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #333; padding: 10px; text-align: left; }}
            th {{ background-color: #1f1f1f; color: #ff9f1c; }}
            tr:nth-child(even) {{ background-color: #1a1a1a; }}
            .metrics-card {{ display: inline-block; background-color: #1f1f1f; padding: 15px; border-radius: 5px; margin: 10px; min-width: 150px; border-left: 4px solid #ff9f1c; }}
            .metric-val {{ font-size: 20px; font-weight: bold; color: #00ff66; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <h1>VOLATRIA PERFORMANCE REPORT</h1>
        <hr style="border: 1px solid #333;" />
        
        <h2>Attribution Metrics</h2>
        <div>
            <div class="metrics-card">
                <div>Sharpe Ratio</div>
                <div class="metric-val">{metrics.get("sharpe_ratio", 0.0):.4f}</div>
            </div>
            <div class="metrics-card">
                <div>Max Drawdown</div>
                <div class="metric-val">{metrics.get("max_drawdown", 0.0)*100:.2f}%</div>
            </div>
            <div class="metrics-card">
                <div>CAGR</div>
                <div class="metric-val">{metrics.get("cagr", 0.0)*100:.2f}%</div>
            </div>
            <div class="metrics-card">
                <div>Win Rate</div>
                <div class="metric-val">{metrics.get("win_rate", 0.0)*100:.1f}%</div>
            </div>
            <div class="metrics-card">
                <div>Total Trades</div>
                <div class="metric-val">{metrics.get("total_trades", 0)}</div>
            </div>
        </div>
        
        <h2>Recent Trade Log Execution</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Type</th>
                    <th>Asset X Price</th>
                    <th>Asset Y Price</th>
                    <th>P&L</th>
                    <th>Cash Balance</th>
                </tr>
            </thead>
            <tbody>
                {trade_rows}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html
