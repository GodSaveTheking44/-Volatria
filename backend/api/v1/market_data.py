from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.quant.pricing import HAS_CPP_KERNELS

router = APIRouter(prefix="/market-data", tags=["Market Data"])

# Initialize compiled order book or pure-python wrapper
ob = None
if HAS_CPP_KERNELS:
    import volatria_core_py as vc
    ob = vc.OrderBook()
    # Pre-populate some orders
    ob.submit_order_vals(vc.Side.BUY, vc.OrderType.LIMIT, 99.8, 100, 1, vc.TimeInForce.GTC, vc.STPMode.NONE_)
    ob.submit_order_vals(vc.Side.BUY, vc.OrderType.LIMIT, 99.5, 250, 1, vc.TimeInForce.GTC, vc.STPMode.NONE_)
    ob.submit_order_vals(vc.Side.SELL, vc.OrderType.LIMIT, 100.2, 120, 2, vc.TimeInForce.GTC, vc.STPMode.NONE_)
    ob.submit_order_vals(vc.Side.SELL, vc.OrderType.LIMIT, 100.5, 300, 2, vc.TimeInForce.GTC, vc.STPMode.NONE_)

@router.get("/orderbook")
def get_order_book(depth: int = Query(5, description="Depth level depth")):
    if ob is None:
        # Python mock response
        return {
            "mid_price": 100.0,
            "spread": 0.4,
            "bids": [{"price": 99.8, "qty": 100}, {"price": 99.5, "qty": 250}],
            "asks": [{"price": 100.2, "qty": 120}, {"price": 100.5, "qty": 300}]
        }
        
    bids = ob.get_bids(depth)
    asks = ob.get_asks(depth)
    
    return {
        "mid_price": ob.mid_price(),
        "spread": ob.spread(),
        "best_bid": ob.best_bid(),
        "best_ask": ob.best_ask(),
        "bids": [{"price": level.price, "qty": level.total_quantity, "orders": level.order_count} for level in bids],
        "asks": [{"price": level.price, "qty": level.total_quantity, "orders": level.order_count} for level in asks]
    }

@router.get("/prices")
def get_prices(symbol: str = "SPY"):
    # Return a simulated time series for standard charting
    dates = [f"2026-07-{i:02d}" for i in range(1, 11)]
    closes = [100.0, 101.2, 100.8, 102.1, 101.5, 103.0, 102.4, 104.1, 103.5, 105.0]
    return {
        "symbol": symbol,
        "prices": [{"date": d, "close": c} for d, c in zip(dates, closes)]
    }
