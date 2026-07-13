class PortfolioPosition:
    def __init__(self, symbol: str, quantity: float = 0.0, average_cost: float = 0.0):
        self.symbol = symbol
        self.quantity = quantity
        self.average_cost = average_cost

    def update_position(self, qty_change: float, execution_price: float) -> float:
        """
        Updates quantity and average cost. Returns realized P&L if reducing/closing position.
        """
        realized_pnl = 0.0
        
        # Opening/adding position
        if self.quantity == 0 or (self.quantity > 0 and qty_change > 0) or (self.quantity < 0 and qty_change < 0):
            new_qty = self.quantity + qty_change
            if new_qty != 0:
                self.average_cost = (self.quantity * self.average_cost + qty_change * execution_price) / new_qty
            self.quantity = new_qty
            
        # Closing/reducing position
        else:
            if abs(qty_change) >= abs(self.quantity): # Closing or flipping
                realized_pnl = self.quantity * (execution_price - self.average_cost)
                remainder = qty_change + self.quantity
                self.quantity = remainder
                self.average_cost = execution_price if remainder != 0 else 0.0
            else: # Reducing partially
                realized_pnl = (-qty_change) * (execution_price - self.average_cost)
                self.quantity += qty_change
                
        return realized_pnl

    def get_unrealized_pnl(self, current_price: float) -> float:
        return self.quantity * (current_price - self.average_cost)
