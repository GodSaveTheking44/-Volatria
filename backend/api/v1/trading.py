from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.models import Order, Trade, Portfolio, Position, Security
from pydantic import BaseModel

router = APIRouter(prefix="/trading", tags=["Trading"])

class OrderSubmitSchema(BaseModel):
    symbol: str
    side: str # BUY, SELL
    type: str # LIMIT, MARKET
    quantity: int
    price: float

@router.get("/orders")
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.timestamp.desc()).all()
    return [{
        "id": o.id,
        "symbol": o.symbol,
        "side": o.side,
        "type": o.type,
        "price": o.price,
        "quantity": o.quantity,
        "status": o.status,
        "timestamp": o.timestamp
    } for o in orders]

@router.post("/submit")
def submit_order(payload: OrderSubmitSchema, db: Session = Depends(get_db)):
    # 1. Register order record
    order = Order(
        symbol=payload.symbol.upper(),
        side=payload.side.upper(),
        type=payload.type.upper(),
        price=payload.price,
        quantity=payload.quantity,
        status="FILLED" # Auto-match/fill for trading simulation ease
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # 2. Register trade execution
    trade = Trade(
        order_id=order.id,
        side=order.side,
        price=order.price,
        quantity=float(order.quantity),
        realized_pnl=0.0
    )
    db.add(trade)
    
    # 3. Update Portfolio cash and position holdings
    port = db.query(Portfolio).first()
    if port:
        sec = db.query(Security).filter_by(symbol=order.symbol).first()
        if not sec:
            sec = Security(symbol=order.symbol, name=order.symbol, asset_class="Equity")
            db.add(sec)
            db.commit()
            db.refresh(sec)
            
        pos = db.query(Position).filter_by(portfolio_id=port.id, security_id=sec.id).first()
        cost = order.price * order.quantity
        
        if order.side == "BUY":
            port.cash -= cost
            if pos:
                new_qty = pos.quantity + order.quantity
                pos.average_cost = (pos.quantity * pos.average_cost + cost) / new_qty
                pos.quantity = new_qty
            else:
                pos = Position(portfolio_id=port.id, security_id=sec.id, quantity=float(order.quantity), average_cost=order.price)
                db.add(pos)
        else:
            port.cash += cost
            if pos:
                pos.quantity -= order.quantity
                if pos.quantity <= 0:
                    db.delete(pos)
                    
        db.commit()
        db.refresh(port)
        
    return {
        "order_id": order.id,
        "status": order.status,
        "exec_price": order.price,
        "quantity": order.quantity
    }
