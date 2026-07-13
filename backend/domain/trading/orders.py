from dataclasses import dataclass
from datetime import datetime

@dataclass
class OrderRequest:
    symbol: str
    side: str # BUY, SELL
    type: str # LIMIT, MARKET
    quantity: int
    price: float = 0.0
    time_in_force: str = "GTC" # GTC, IOC, FOK
    stp_mode: str = "NONE"
    
@dataclass
class OrderState:
    order_id: int
    symbol: str
    side: str
    price: float
    quantity: int
    remaining_quantity: int
    status: str # NEW, PARTIALLY_FILLED, FILLED, CANCELLED, REJECTED
    timestamp: datetime = datetime.utcnow()
