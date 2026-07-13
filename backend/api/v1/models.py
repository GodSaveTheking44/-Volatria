import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.models import ModelMetadata

router = APIRouter(prefix="/models", tags=["Machine Learning"])

def seed_experiments_if_empty(db: Session):
    count = db.query(ModelMetadata).count()
    if count == 0:
        exp1 = ModelMetadata(
            name="RandomForestRegressor",
            version="v1.0.0",
            metrics_json=json.dumps({"val_mse": 0.000412, "val_r2": 0.045, "n_samples": 450})
        )
        exp2 = ModelMetadata(
            name="GradientBoostingRegressor",
            version="v1.0.0",
            metrics_json=json.dumps({"val_mse": 0.000398, "val_r2": 0.078, "n_samples": 450})
        )
        db.add(exp1)
        db.add(exp2)
        db.commit()

@router.get("/experiments")
def list_experiments(db: Session = Depends(get_db)):
    seed_experiments_if_empty(db)
    runs = db.query(ModelMetadata).all()
    results = []
    for r in runs:
        results.append({
            "id": r.id,
            "name": r.name,
            "version": r.version,
            "metrics": json.loads(r.metrics_json) if r.metrics_json else {},
            "logged_at": r.logged_at
        })
    return results
