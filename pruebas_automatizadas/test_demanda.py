import numpy as np
import pytest
from predictor_demanda import PredictorDemanda

def test_train_sets_is_trained_flag():
    X_train = np.array([[20, 3, 14], [40, 6, 11], [60, 9, 10]])
    y_train = np.array([1, 0, 1])

    model = PredictorDemanda()
    result = model.train(X_train, y_train)

    assert result is True
    assert model.is_trained is True


def test_predict_demanda_returns_indicator():
    X_train = np.array([[20, 3, 14], [40, 6, 11]])
    y_train = np.array([1, 0])
    model = PredictorDemanda()
    model.train(X_train, y_train)

    # Simulamos datos de prueba
    X_test = np.array([[45, 10, 20]])  # promedio ~25 → debería dar "Medio"
    result = model.predict_demanda(X_test)

    assert "expected_enrollment" in result
    assert "indicator" in result
    assert result["indicator"] in ["Muy alto", "Alto", "Medio", "Bajo"]
