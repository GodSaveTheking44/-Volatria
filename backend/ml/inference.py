import numpy as np
from sklearn.ensemble import RandomForestRegressor

class ForecastingModelInference:
    def __init__(self, trained_model: RandomForestRegressor):
        self.model = trained_model

    def predict_next_return(self, feature_row: np.ndarray) -> float:
        """
        Predicts next step return.
        feature_row: shape (n_features,) or (1, n_features)
        """
        row = feature_row.reshape(1, -1) if feature_row.ndim == 1 else feature_row
        pred = self.model.predict(row)
        return float(pred[0])
