import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.models import Security, Price

def ingest_historical_prices(db: Session, symbol: str, name: str, df: pd.DataFrame, asset_class: str = "Equity"):
    """
    Ingests price data from a pandas DataFrame and saves it into SQL database models.
    df must contain columns: [Date/timestamp, open, high, low, close, volume]
    """
    # 1. Fetch or create security record
    security = db.query(Security).filter_by(symbol=symbol).first()
    if not security:
        security = Security(symbol=symbol, name=name, asset_class=asset_class)
        db.add(security)
        db.commit()
        db.refresh(security)
        
    # 2. Bulk insert prices
    prices_to_insert = []
    for idx, row in df.iterrows():
        # Handle timestamp parsing
        ts = idx
        if not isinstance(ts, datetime):
            ts = pd.to_datetime(ts).to_pydatetime()
            
        price_rec = Price(
            security_id=security.id,
            timestamp=ts,
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row["volume"])
        )
        prices_to_insert.append(price_rec)
        
    db.bulk_save_objects(prices_to_insert)
    db.commit()

def fetch_prices_dataframe(db: Session, symbol: str) -> pd.DataFrame:
    """
    Retrieves historical price records for a symbol and returns a sorted pandas DataFrame.
    """
    security = db.query(Security).filter_by(symbol=symbol).first()
    if not security:
        return pd.DataFrame()
        
    query = db.query(Price).filter_by(security_id=security.id).order_by(Price.timestamp.asc())
    records = []
    for p in query.all():
        records.append({
            "timestamp": p.timestamp,
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "close": p.close,
            "volume": p.volume
        })
        
    if not records:
        return pd.DataFrame()
        
    df = pd.DataFrame(records)
    df.set_index("timestamp", inplace=True)
    return df
