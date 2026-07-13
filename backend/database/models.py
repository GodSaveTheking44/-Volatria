from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.db import Base

class Security(Base):
    __tablename__ = "securities"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    asset_class = Column(String, nullable=False) # e.g. Equity, Option, Crypto
    sector = Column(String, nullable=True)
    
    prices = relationship("Price", back_populates="security", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="security")

class Price(Base):
    __tablename__ = "prices"
    
    id = Column(Integer, primary_key=True, index=True)
    security_id = Column(Integer, ForeignKey("securities.id"), nullable=False)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    security = relationship("Security", back_populates="prices")

class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    cash = Column(Float, default=100000.0)
    net_asset_value = Column(Float, default=100000.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    security_id = Column(Integer, ForeignKey("securities.id"), nullable=False)
    quantity = Column(Float, default=0.0)
    average_cost = Column(Float, default=0.0)
    
    portfolio = relationship("Portfolio", back_populates="positions")
    security = relationship("Security", back_populates="positions")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    side = Column(String, nullable=False) # BUY, SELL
    type = Column(String, nullable=False) # LIMIT, MARKET
    price = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=False)
    status = Column(String, default="NEW") # NEW, FILLED, CANCELLED, REJECTED
    participant_id = Column(Integer, default=1)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    trades = relationship("Trade", back_populates="order")

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    side = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    realized_pnl = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    order = relationship("Order", back_populates="trades")

class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    backtests = relationship("Backtest", back_populates="strategy", cascade="all, delete-orphan")

class Backtest(Base):
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    name = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    sharpe = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    cagr = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    run_at = Column(DateTime, default=datetime.utcnow)
    
    strategy = relationship("Strategy", back_populates="backtests")

class ModelMetadata(Base):
    __tablename__ = "model_experiments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    version = Column(String, nullable=False)
    metrics_json = Column(Text, nullable=True) # JSON dump of training/validation scores
    logged_at = Column(DateTime, default=datetime.utcnow)
