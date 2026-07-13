import json
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sqlalchemy.orm import Session
from backend.database.models import ModelMetadata

def train_and_log_model(
    db: Session, model_name: str, version: str, X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray
) -> RandomForestRegressor:
    """
    Fits a RandomForestRegressor, evaluates validation scores, and commits experiments metadata to SQL DB.
    """
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)
    
    # Validation predictions
    preds = model.predict(X_val)
    mse = float(mean_squared_error(y_val, preds))
    r2 = float(r2_score(y_val, preds))
    
    metrics = {
        "val_mse": mse,
        "val_r2": r2,
        "n_samples": len(y_train)
    }
    
    # Save model experiment metadata to database
    meta = ModelMetadata(
        name=model_name,
        version=version,
        metrics_json=json.dumps(metrics)
    )
    db.add(meta)
    db.commit()
    db.refresh(meta)
    
    return model
