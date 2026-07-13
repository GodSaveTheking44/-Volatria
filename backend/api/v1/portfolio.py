from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.models import Portfolio, Position, Security

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

def seed_default_portfolio_if_empty(db: Session) -> Portfolio:
    port = db.query(Portfolio).first()
    if not port:
        # Create portfolio
        port = Portfolio(name="Default Institutional Portfolio", cash=150000.0, net_asset_value=250000.0)
        db.add(port)
        db.commit()
        db.refresh(port)
        
        # Populate securities
        securities_list = [
            {"symbol": "AAPL", "name": "Apple Inc.", "asset_class": "Equity", "sector": "Technology", "qty": 100, "cost": 175.0},
            {"symbol": "MSFT", "name": "Microsoft Corp.", "asset_class": "Equity", "sector": "Technology", "qty": 50, "cost": 380.0},
            {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "asset_class": "Equity", "sector": "Financials", "qty": 120, "cost": 155.0},
            {"symbol": "TSLA", "name": "Tesla Inc.", "asset_class": "Equity", "sector": "Consumer Cyclical", "qty": 80, "cost": 210.0}
        ]
        
        for item in securities_list:
            sec = db.query(Security).filter_by(symbol=item["symbol"]).first()
            if not sec:
                sec = Security(symbol=item["symbol"], name=item["name"], asset_class=item["asset_class"], sector=item["sector"])
                db.add(sec)
                db.commit()
                db.refresh(sec)
                
            pos = Position(portfolio_id=port.id, security_id=sec.id, quantity=item["qty"], average_cost=item["cost"])
            db.add(pos)
            
        db.commit()
        db.refresh(port)
        
    return port

@router.get("/summary")
def get_portfolio_summary(db: Session = Depends(get_db)):
    port = seed_default_portfolio_if_empty(db)
    
    positions = db.query(Position).filter_by(portfolio_id=port.id).all()
    holdings = []
    total_market_val = 0.0
    sector_exposure = {}
    
    # Prices proxy for current price calculation
    price_proxy = {"AAPL": 180.20, "MSFT": 395.50, "JPM": 170.10, "TSLA": 190.50}
    
    for pos in positions:
        sec = pos.security
        curr_price = price_proxy.get(sec.symbol, pos.average_cost * 1.05)
        mkt_val = pos.quantity * curr_price
        total_market_val += mkt_val
        
        unrealized_pnl = mkt_val - (pos.quantity * pos.average_cost)
        
        # Sector allocations
        sec_name = sec.sector or "Other"
        sector_exposure[sec_name] = sector_exposure.get(sec_name, 0.0) + mkt_val
        
        holdings.append({
            "symbol": sec.symbol,
            "name": sec.name,
            "quantity": pos.quantity,
            "average_cost": pos.average_cost,
            "current_price": curr_price,
            "market_value": mkt_val,
            "unrealized_pnl": unrealized_pnl,
            "sector": sec_name
        })
        
    nav = port.cash + total_market_val
    # Keep DB nav updated
    port.net_asset_value = nav
    db.commit()
    
    # Calculate sector exposure percentages
    sector_percentage = {}
    if nav > 0:
        for sec, val in sector_exposure.items():
            sector_percentage[sec] = val / nav
            
    return {
        "portfolio_name": port.name,
        "cash": port.cash,
        "total_market_value": total_market_val,
        "net_asset_value": nav,
        "holdings": holdings,
        "sector_exposure_pct": sector_percentage
    }
