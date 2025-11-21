"""
utilidades_modelo.py

Funciones compartidas para la carga de datos, preprocesamiento, entrenamiento,
evaluación y guardado de modelos de predicción de demanda.

Autor: Sistema de Predicción de Demanda UNI
Fecha: 2025-11-13
"""

import logging
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Columnas esperadas en el CSV
REQUIRED_COLUMNS = [
    'curso_ofertado_id', 'nombre_seccion', 'codigo_curso', 'semestre', 'creditos', 
    'tipo_curso', 'profesor_id', 'alumnos_previos', 'variacion_matricula', 
    'num_prerrequisitos', 'tasa_aprobacion', 'franja_horaria', 
    'cupo_maximo', 'alumnos_matriculados'
]

OPTIONAL_COLUMNS = ['profesor_popularidad', 'alumnos_elegibles']

# Features por defecto para el modelo
DEFAULT_FEATURES = [
    'creditos', 'alumnos_previos', 'variacion_matricula', 'num_prerrequisitos',
    'tasa_aprobacion', 'franja_horaria', 'alumnos_elegibles',
    'cupo_maximo', 'tipo_curso'
]


def cargar_datos_csv(path: str) -> pd.DataFrame:
    """
    Lee un archivo CSV con datos de matrícula de cursos y valida las columnas.
    
    Parameters
    ----------
    path : str
        Ruta al archivo CSV con los datos de matrícula.
    
    Returns
    -------
    pd.DataFrame
        DataFrame con los datos cargados y validados.
    
    Raises
    ------
    FileNotFoundError
        Si el archivo no existe.
    ValueError
        Si faltan columnas obligatorias.
    """
    logger.info(f"Cargando datos desde: {path}")
    
    if not Path(path).exists():
        raise FileNotFoundError(f"El archivo no existe: {path}")
    
    try:
        df = pd.read_csv(path)
        logger.info(f"Archivo cargado. Shape: {df.shape}")
    except Exception as e:
        logger.error(f"Error al leer el archivo CSV: {e}")
        raise
    
    # Validar columnas obligatorias
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Faltan columnas obligatorias: {missing_cols}")
    
    logger.info(f"Columnas encontradas: {list(df.columns)}")
    logger.info(f"Primeras filas:\n{df.head()}")
    logger.info(f"Info del DataFrame:\n{df.info()}")
    
    return df


def get_data_from_db(conn_params: Dict[str, Any]) -> pd.DataFrame:
    """
    Obtiene datos desde la base de datos (función stub para futuro uso).
    
    NOTA: Esta función será implementada cuando se prefiera obtener los datos
    directamente desde una vista SQL que ya incluya el cálculo de alumnos_elegibles
    y otras métricas.
    
    Parameters
    ----------
    conn_params : dict
        Parámetros de conexión a la base de datos.
        Ejemplo: {'host': 'localhost', 'database': 'uni', 'user': 'admin', ...}
    
    Returns
    -------
    pd.DataFrame
        DataFrame con los datos de la vista SQL.
    
    Raises
    ------
    NotImplementedError
        Esta función aún no está implementada.
    """
    logger.warning("get_data_from_db no está implementada aún.")
    raise NotImplementedError(
        "Esta función será implementada cuando se use una vista SQL. "
        "Por ahora, usar cargar_datos_csv()."
    )


def calcular_alumnos_elegibles(
    df: pd.DataFrame,
    tablas_aux: Optional[Dict[str, pd.DataFrame]] = None
) -> pd.DataFrame:
    """
    Calcula la columna 'alumnos_elegibles' en base a datos disponibles.
    
    LÓGICA ACTUAL (versión pandas):
    - Si ya existe la columna y tiene valores, no hace nada.
    - Si falta o tiene NaN, usa una aproximación:
      alumnos_elegibles = max(alumnos_previos * 1.2, cupo_maximo)
    
    FUTURO (con vista SQL):
    Esta función será reemplazada por get_data_from_db() que devolverá
    directamente la columna calculada mediante:
        SELECT COUNT(DISTINCT estudiante_id)
        FROM estudiantes_aprobados_prerrequisitos
        WHERE NOT EXISTS (SELECT 1 FROM aprobados WHERE curso = X)
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame con datos de cursos.
    tablas_aux : dict, optional
        Diccionario con tablas auxiliares (estudiantes, prerrequisitos, etc.)
        No se usa en la implementación actual.
    
    Returns
    -------
    pd.DataFrame
        DataFrame con la columna 'alumnos_elegibles' calculada.
    """
    logger.info("Calculando alumnos_elegibles...")
    
    df = df.copy()
    
    if 'alumnos_elegibles' not in df.columns:
        df['alumnos_elegibles'] = np.nan
    
    # Calcular solo donde falte
    mask = df['alumnos_elegibles'].isna()
    if mask.sum() > 0:
        logger.info(f"Calculando {mask.sum()} valores faltantes de alumnos_elegibles")
        df.loc[mask, 'alumnos_elegibles'] = df.loc[mask].apply(
            lambda row: max(row['alumnos_previos'] * 1.2, row['cupo_maximo']),
            axis=1
        )
    
    logger.info("Cálculo de alumnos_elegibles completado.")
    return df


def alinear_columnas_con_modelo(X_pred: pd.DataFrame, X_train_cols: List[str]) -> pd.DataFrame:
    """
    Alinea las columnas de predicción con las del entrenamiento.
    Agrega columnas faltantes con 0 y elimina columnas extras.
    
    Parameters
    ----------
    X_pred : pd.DataFrame
        DataFrame de predicción con posibles columnas diferentes.
    X_train_cols : list
        Lista de nombres de columnas que el modelo espera.
    
    Returns
    -------
    pd.DataFrame
        DataFrame con columnas alineadas.
    """
    # Agregar columnas faltantes con 0
    for col in X_train_cols:
        if col not in X_pred.columns:
            X_pred[col] = 0
    
    # Ordenar columnas en el mismo orden que el entrenamiento
    X_pred = X_pred[X_train_cols]
    
    return X_pred


def preparar_features(
    df: pd.DataFrame,
    features: List[str],
    target: str = 'alumnos_matriculados',
    drop_target: bool = True,
    expected_columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
    """
    Prepara las features para el modelo:
    - Selecciona columnas especificadas
    - Imputa valores faltantes (mediana para numéricos, moda para categóricos)
    - Aplica one-hot encoding a variables categóricas
    - Separa X e y (si drop_target=True)
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame con todos los datos.
    features : list of str
        Lista de nombres de columnas a usar como features.
    target : str, default='alumnos_matriculados'
        Nombre de la columna objetivo.
    drop_target : bool, default=True
        Si True, devuelve X, y. Si False, devuelve X, None.
    
    Returns
    -------
    X : pd.DataFrame
        Features preparadas.
    y : pd.Series or None
        Variable objetivo (si drop_target=True).
    """
    logger.info(f"Preparando features: {features}")
    
    df = df.copy()
    
    # Validar que las features existan
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"Features no encontradas en el DataFrame: {missing}")
    
    # Separar target
    if drop_target:
        if target not in df.columns:
            raise ValueError(f"Columna objetivo '{target}' no encontrada")
        y = df[target].copy()
    else:
        y = None
    
    # Seleccionar features
    X = df[features].copy()
    
    # Identificar columnas numéricas y categóricas
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
    
    logger.info(f"Columnas numéricas: {numeric_cols}")
    logger.info(f"Columnas categóricas: {categorical_cols}")
    
    # Imputar valores faltantes
    for col in numeric_cols:
        if X[col].isna().sum() > 0:
            median_val = X[col].median()
            logger.info(f"Imputando {X[col].isna().sum()} valores faltantes en '{col}' con mediana: {median_val}")
            X[col].fillna(median_val, inplace=True)
    
    for col in categorical_cols:
        if X[col].isna().sum() > 0:
            mode_val = X[col].mode()[0] if len(X[col].mode()) > 0 else 'UNKNOWN'
            logger.info(f"Imputando {X[col].isna().sum()} valores faltantes en '{col}' con moda: {mode_val}")
            X[col].fillna(mode_val, inplace=True)
    
    # One-hot encoding para categóricas
    if categorical_cols:
        logger.info(f"Aplicando one-hot encoding a: {categorical_cols}")
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    # Alinear columnas si se especificó expected_columns
    if expected_columns is not None:
        logger.info(f"Alineando columnas con las esperadas por el modelo...")
        X = alinear_columnas_con_modelo(X, expected_columns)
    
    logger.info(f"Features finales: {X.shape[1]} columnas, {X.shape[0]} filas")
    logger.info(f"Nombres de columnas finales: {list(X.columns)}")
    
    return X, y


def entrenar_rf_regressor(
    X: pd.DataFrame,
    y: pd.Series,
    params: Dict[str, Any]
) -> RandomForestRegressor:
    """
    Entrena un modelo RandomForestRegressor con los parámetros especificados.
    
    Parameters
    ----------
    X : pd.DataFrame
        Features de entrenamiento.
    y : pd.Series
        Variable objetivo.
    params : dict
        Diccionario con hiperparámetros para RandomForestRegressor.
        Ejemplo: {'n_estimators': 300, 'max_depth': 12, 'random_state': 42}
    
    Returns
    -------
    RandomForestRegressor
        Modelo entrenado.
    """
    logger.info(f"Entrenando RandomForestRegressor con parámetros: {params}")
    
    model = RandomForestRegressor(**params)
    model.fit(X, y)
    
    logger.info("Entrenamiento completado.")
    return model


def evaluar_regresor(
    model: RandomForestRegressor,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict[str, float]:
    """
    Evalúa un modelo de regresión y devuelve métricas.
    
    Parameters
    ----------
    model : RandomForestRegressor
        Modelo entrenado.
    X_test : pd.DataFrame
        Features de prueba.
    y_test : pd.Series
        Valores reales.
    
    Returns
    -------
    dict
        Diccionario con métricas: MAE, RMSE, R2.
    """
    logger.info("Evaluando modelo...")
    
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    metrics = {
        'MAE': float(mae),
        'RMSE': float(rmse),
        'R2': float(r2)
    }
    
    logger.info(f"Métricas - MAE: {mae:.2f}, RMSE: {rmse:.2f}, R2: {r2:.4f}")
    
    return metrics


def guardar_modelo_y_metadata(
    model: RandomForestRegressor,
    features: List[str],
    metrics: Dict[str, float],
    output_path: str,
    name_prefix: str,
    curso: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    n_train: Optional[int] = None,
    n_test: Optional[int] = None
):
    """
    Guarda el modelo entrenado y su metadata en archivos separados.
    
    Parameters
    ----------
    model : RandomForestRegressor
        Modelo entrenado.
    features : list of str
        Lista de features utilizadas.
    metrics : dict
        Métricas de evaluación (MAE, RMSE, R2).
    output_path : str
        Directorio donde guardar el modelo.
    name_prefix : str
        Prefijo para el nombre del archivo (ej: 'modelo_demanda_general').
    curso : str, optional
        Código del curso (si es modelo específico).
    config : dict, optional
        Configuración del modelo.
    n_train : int, optional
        Número de muestras de entrenamiento.
    n_test : int, optional
        Número de muestras de prueba.
    """
    Path(output_path).mkdir(parents=True, exist_ok=True)
    
    # Generar nombre con fecha
    fecha = datetime.now().strftime("%Y%m%d")
    base_name = f"{name_prefix}_v{fecha}"
    
    # Rutas de archivos
    model_path = Path(output_path) / f"{base_name}.pkl"
    metadata_path = Path(output_path) / f"{base_name}.json"
    
    # Guardar modelo
    logger.info(f"Guardando modelo en: {model_path}")
    joblib.dump(model, model_path)
    
    # Preparar metadata
    metadata = {
        'model_name': base_name,
        'curso': curso,
        'date': datetime.now().isoformat(),
        'features': features,
        'metrics': metrics,
        'n_train': n_train,
        'n_test': n_test,
        'hyperparams': {
            'n_estimators': int(model.n_estimators),
            'max_depth': int(model.max_depth) if model.max_depth else None,
            'random_state': int(model.random_state) if model.random_state else None
        }
    }
    
    # Añadir hash del config si existe
    if config:
        config_str = json.dumps(config, sort_keys=True)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()
        metadata['config_hash'] = config_hash
    
    # Guardar metadata
    logger.info(f"Guardando metadata en: {metadata_path}")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    logger.info("Modelo y metadata guardados exitosamente.")
    
    return str(model_path)


def cargar_modelo(path: str) -> RandomForestRegressor:
    """
    Carga un modelo guardado desde un archivo .pkl.
    
    Parameters
    ----------
    path : str
        Ruta al archivo .pkl del modelo.
    
    Returns
    -------
    RandomForestRegressor
        Modelo cargado.
    
    Raises
    ------
    FileNotFoundError
        Si el archivo no existe.
    """
    logger.info(f"Cargando modelo desde: {path}")
    
    if not Path(path).exists():
        raise FileNotFoundError(f"El modelo no existe: {path}")
    
    model = joblib.load(path)
    logger.info("Modelo cargado exitosamente.")
    
    return model


# ============================================================================
# PRUEBAS UNITARIAS BÁSICAS
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("PRUEBAS UNITARIAS - utilidades_modelo.py")
    print("=" * 70)
    
    # Test 1: Crear DataFrame de ejemplo
    print("\n[Test 1] Creando DataFrame de ejemplo...")
    data = {
        'curso_ofertado_id': [1, 2, 3],
        'nombre_seccion': ['CIB02-2025-1-A', 'CIB02-2025-2-A', 'MAT101-2025-1-B'],
        'codigo_curso': ['CIB02', 'CIB02', 'MAT101'],
        'semestre': ['2025-1', '2025-2', '2025-1'],
        'creditos': [4, 4, 5],
        'tipo_curso': ['O', 'O', 'E'],
        'profesor_id': [1, 1, 2],
        'profesor_popularidad': [0.85, 0.85, 0.70],
        'alumnos_previos': [45, 50, 30],
        'variacion_matricula': [0.1, 0.05, -0.1],
        'num_prerrequisitos': [2, 2, 1],
        'tasa_aprobacion': [0.80, 0.82, 0.75],
        'franja_horaria': [1, 2, 1],
        'alumnos_elegibles': [60, 65, 35],
        'cupo_maximo': [50, 50, 40],
        'alumnos_matriculados': [48, 49, 32]
    }
    df_test = pd.DataFrame(data)
    print(f"✓ DataFrame creado: {df_test.shape}")
    
    # Test 2: Calcular alumnos_elegibles
    print("\n[Test 2] Calculando alumnos_elegibles (con valores ya presentes)...")
    df_test_elegibles = calcular_alumnos_elegibles(df_test.copy())
    print(f"✓ Alumnos elegibles: {df_test_elegibles['alumnos_elegibles'].tolist()}")
    
    # Test 3: Preparar features
    print("\n[Test 3] Preparando features...")
    features_test = ['creditos', 'alumnos_previos', 'variacion_matricula', 
                     'tasa_aprobacion', 'tipo_curso']
    X_test, y_test = preparar_features(df_test, features_test, drop_target=True)
    print(f"✓ X shape: {X_test.shape}, y shape: {y_test.shape}")
    print(f"✓ Columnas después de one-hot: {list(X_test.columns)}")
    
    # Test 4: Entrenar modelo pequeño
    print("\n[Test 4] Entrenando modelo de prueba...")
    params_test = {'n_estimators': 10, 'max_depth': 3, 'random_state': 42}
    model_test = entrenar_rf_regressor(X_test, y_test, params_test)
    print(f"✓ Modelo entrenado: {type(model_test).__name__}")
    
    # Test 5: Evaluar modelo
    print("\n[Test 5] Evaluando modelo...")
    metrics_test = evaluar_regresor(model_test, X_test, y_test)
    print(f"✓ Métricas: {metrics_test}")
    
    print("\n" + "=" * 70)
    print("TODAS LAS PRUEBAS COMPLETADAS ✓")
    print("=" * 70)
