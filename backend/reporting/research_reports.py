from typing import Dict, Any

def generate_research_html_report(pair_name: str, EG_pvalue: float, beta: float, alpha: float, ADF_pvalue: float) -> str:
    """
    Generates a stylized HTML research report for a cointegration analysis.
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Volatria Quantitative Research Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #121212; color: #e0e0e0; margin: 30px; }}
            h1, h2 {{ color: #00e5ff; }}
            .card {{ background-color: #1f1f1f; padding: 20px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #00e5ff; }}
            .val {{ font-size: 18px; font-weight: bold; color: #00ff66; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ border: 1px solid #333; padding: 10px; text-align: left; }}
            th {{ background-color: #1a1a1a; }}
        </style>
    </head>
    <body>
        <h1>VOLATRIA RESEARCH REPORT</h1>
        <hr style="border: 1px solid #333;" />
        
        <h2>Cointegration Analysis: {pair_name}</h2>
        <div class="card">
            <p>This report summarizes the statistical validity of the screened spread relationship for the pair <strong>{pair_name}</strong>.</p>
            <table>
                <thead>
                    <tr>
                        <th>Statistical Test / Parameter</th>
                        <th>Value</th>
                        <th>Threshold / Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Engle-Granger P-Value</td>
                        <td class="val">{EG_pvalue:.6f}</td>
                        <td>{ "PASSED (Coint)" if EG_pvalue < 0.05 else "FAILED (No Coint)" }</td>
                    </tr>
                    <tr>
                        <td>Hedge Ratio (Beta)</td>
                        <td class="val">{beta:.4f}</td>
                        <td>OLS Fitted Slope</td>
                    </tr>
                    <tr>
                        <td>Spread Intercept (Alpha)</td>
                        <td class="val">{alpha:.4f}</td>
                        <td>OLS Fitted Intercept</td>
                    </tr>
                    <tr>
                        <td>ADF Residual P-Value</td>
                        <td class="val">{ADF_pvalue:.6f}</td>
                        <td>{ "PASSED (Stationary)" if ADF_pvalue < 0.05 else "FAILED (Unit-Root)" }</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return html
