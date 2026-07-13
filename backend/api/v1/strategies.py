from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.models import Strategy
from pydantic import BaseModel

router = APIRouter(prefix="/strategies", tags=["Strategies"])

class StrategyCreateSchema(BaseModel):
    name: str
    description: str = ""

@router.get("")
def list_strategies(db: Session = Depends(get_db)):
    strategies = db.query(Strategy).all()
    return [{"id": s.id, "name": s.name, "description": s.description, "created_at": s.created_at} for s in strategies]

@router.post("")
def create_strategy(payload: StrategyCreateSchema, db: Session = Depends(get_db)):
    existing = db.query(Strategy).filter_by(name=payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Strategy name already exists")
        
    strat = Strategy(name=payload.name, description=payload.description)
    db.add(strat)
    db.commit()
    db.refresh(strat)
    return {"id": strat.id, "name": strat.name, "description": strat.description}
