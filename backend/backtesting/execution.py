class TransactionCostModel:
    def __init__(self, commission_pct: float = 0.0005, slippage_pct: float = 0.0002, market_impact_coef: float = 0.0):
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        self.market_impact_coef = market_impact_coef

    def calculate_execution_price(self, quote_price: float, side: str, quantity: float) -> float:
        """
        Applies execution slippage and market impact (price penalty for large trade size).
        """
        direction = 1 if side.upper() == "BUY" else -1
        
        # Slippage penalty
        slippage = quote_price * self.slippage_pct * direction
        
        # Market impact model (proportional to square root of trade quantity proxy)
        impact = quote_price * self.market_impact_coef * (quantity ** 0.5) * direction
        
        exec_price = quote_price + slippage + impact
        return exec_price

    def calculate_commission(self, price: float, quantity: float) -> float:
        """
        Calculates brokerage commission.
        """
        return price * quantity * self.commission_pct
