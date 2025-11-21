import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

class PredictorDemanda:
    def __init__(self, algorithm ="random_forest", random_state=42):

        pass

    def train(self, X_train, y_train):
        # Entrena el modelo con datos de entrada (características de estudiantes/cursos).
        # Cambia un flag interno (self.is_trained = True) para saber si el modelo ya fue entrenado.
        self.is_trained = True

        return self.is_trained

    def predict_demanda(self, X_test):
        #Predice la demanda esperada de matrícula para un curso o sección específica.
        #Parámetros
        #----------
        #course_features : dict
        #Diccionario con las características relevantes del curso/sección.
        #Ejemplo:
        #{
        #    "course_id": "MAT101",
        #    "semester": "2025-1",
        #    "credits": 4,
        #    "faculty": "Ingeniería",
        #    "historical_enrollment": [50, 60, 55, 70],
        #    "pass_rate": 0.85,
        #    "professor_popularity": 0.9,
        #    "time_slot": "08:00-10:00",
        #    "turn_queue": 120
        #}

        #Retorna
        #dict
        #{
        #    "expected_enrollment": int,   # número estimado de estudiantes
        #    "confidence_interval": tuple, # (min, max) intervalo de confianza
        #    "probability_distribution": list # opcional, probabilidad por rango
        #}
        n_estudiantes = int(np.mean(X_test))  

        if n_estudiantes > 40:
            indicador = "Muy alto"
        elif 30 < n_estudiantes <= 40:
            indicador = "Alto"
        elif 15 < n_estudiantes <= 30:
            indicador = "Medio"
        else:
            indicador = "Bajo"

        return {
            "expected_enrollment": n_estudiantes,
            "indicator": indicador
        }
    
        if not self.is_trained:
            raise Exception("El modelo no ha sido entrenado. Por favor, entrena el modelo antes de predecir.")
        pass

    def evaluate(self, X_test, y_test):
        
        if not self.is_trained:
            raise Exception("El modelo no ha sido entrenado. Por favor, entrena el modelo antes de evaluar.")
        pass

