"""
modelo_especifico.py

Script para entrenar un modelo RandomForestRegressor específico para un curso dado.
Valida que haya suficiente historia antes de entrenar.

Uso:
    python -m src.modelo_especifico --course CIB02 --data data/matriculas_por_curso.csv --config configs/ejemplo_CIB02.yml
    python -m src.modelo_especifico --course CIB02 --data data/matriculas_por_curso.csv --force

Autor: Sistema de Predicción de Demanda UNI
Fecha: 2025-11-13
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
import pandas as pd
from sklearn.model_selection import train_test_split

from src.utilidades_modelo import (
    cargar_datos_csv,
    calcular_alumnos_elegibles,
    preparar_features,
    entrenar_rf_regressor,
    evaluar_regresor,
    guardar_modelo_y_metadata,
    DEFAULT_FEATURES
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cargar_config(config_path: str) -> Dict[str, Any]:
    """
    Carga la configuración desde un archivo YAML.
    
    Parameters
    ----------
    config_path : str
        Ruta al archivo de configuración.
    
    Returns
    -------
    dict
        Configuración cargada.
    """
    logger.info(f"Cargando configuración desde: {config_path}")
    
    if not Path(config_path).exists():
        logger.warning(f"Archivo de configuración no encontrado: {config_path}")
        logger.warning("Usando configuración por defecto.")
        return get_default_config()
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Configuración cargada: {config}")
    return config


def get_default_config() -> Dict[str, Any]:
    """
    Devuelve la configuración por defecto si no existe archivo YAML.
    
    Returns
    -------
    dict
        Configuración por defecto.
    """
    return {
        'features': DEFAULT_FEATURES,
        'hyperparams': {
            'n_estimators': 300,
            'max_depth': 12,
            'random_state': 42
        },
        'target': 'alumnos_matriculados',
        'test_size': 0.2,
        'min_history_semesters': 6,
        'output_dir': 'models/'
    }


def entrenar_y_guardar_especifico(
    df: pd.DataFrame,
    course_code: str,
    config: Dict[str, Any],
    force: bool = False
) -> Optional[str]:
    """
    Entrena un modelo específico para un curso y lo guarda con su metadata.
    
    Esta función puede ser importada y usada por otros scripts.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame con todos los datos de cursos.
    course_code : str
        Código del curso (ej: 'CIB02').
    config : dict
        Configuración del modelo.
    force : bool, default=False
        Si True, entrena aunque no haya historia suficiente.
    
    Returns
    -------
    str or None
        Ruta del archivo del modelo guardado, o None si no se pudo entrenar.
    """
    logger.info("=" * 70)
    logger.info(f"ENTRENAMIENTO DE MODELO ESPECÍFICO: {course_code}")
    logger.info("=" * 70)
    
    # Filtrar datos del curso
    df_curso = df[df['codigo_curso'] == course_code].copy()
    
    if len(df_curso) == 0:
        logger.error(f"No se encontraron datos para el curso: {course_code}")
        return None
    
    logger.info(f"Registros encontrados para {course_code}: {len(df_curso)}")
    
    # Validar historia mínima
    min_history = config.get('min_history_semesters', 6)
    
    if len(df_curso) < min_history:
        if not force:
            logger.warning("=" * 70)
            logger.warning(f"ADVERTENCIA: Historial insuficiente para {course_code}")
            logger.warning(f"  - Registros disponibles: {len(df_curso)}")
            logger.warning(f"  - Mínimo requerido: {min_history}")
            logger.warning("  - Recomendación: Usar el modelo general")
            logger.warning("  - Para entrenar de todos modos, usar: --force")
            logger.warning("=" * 70)
            return None
        else:
            logger.warning(f"Historial insuficiente ({len(df_curso)} < {min_history}), pero entrenando por --force")
    
    # Calcular alumnos_elegibles si falta
    if 'alumnos_elegibles' not in df_curso.columns or df_curso['alumnos_elegibles'].isna().any():
        logger.info("Calculando alumnos_elegibles...")
        df_curso = calcular_alumnos_elegibles(df_curso)
    
    # Obtener configuración
    features = config.get('features', DEFAULT_FEATURES)
    target = config.get('target', 'alumnos_matriculados')
    hyperparams = config.get('hyperparams', {
        'n_estimators': 300,
        'max_depth': 12,
        'random_state': 42
    })
    test_size = config.get('test_size', 0.2)
    output_dir = config.get('output_dir', 'models/')
    
    logger.info(f"Total de muestras: {len(df_curso)}")
    logger.info(f"Features seleccionadas: {features}")
    logger.info(f"Hyperparámetros: {hyperparams}")
    
    # Preparar features
    X, y = preparar_features(df_curso, features, target=target, drop_target=True)
    
    # Split train/test
    random_state = hyperparams.get('random_state', 42)
    
    # Si hay muy pocas muestras, usar un test_size menor
    if len(X) < 10:
        test_size = 0.1
        logger.warning(f"Pocas muestras disponibles, ajustando test_size a {test_size}")
    
    if len(X) < 3:
        logger.error("Muy pocas muestras para entrenar y validar (mínimo 3)")
        return None
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    logger.info(f"Train set: {X_train.shape[0]} muestras")
    logger.info(f"Test set: {X_test.shape[0]} muestras")
    
    # Entrenar modelo
    model = entrenar_rf_regressor(X_train, y_train, hyperparams)
    
    # Evaluar modelo
    metrics = evaluar_regresor(model, X_test, y_test)
    
    logger.info("=" * 70)
    logger.info(f"MÉTRICAS DEL MODELO: {course_code}")
    logger.info("=" * 70)
    logger.info(f"MAE:  {metrics['MAE']:.2f} alumnos")
    logger.info(f"RMSE: {metrics['RMSE']:.2f} alumnos")
    logger.info(f"R²:   {metrics['R2']:.4f}")
    logger.info("=" * 70)
    
    # Guardar modelo y metadata
    model_path = guardar_modelo_y_metadata(
        model=model,
        features=list(X.columns),
        metrics=metrics,
        output_path=output_dir,
        name_prefix=f'modelo_demanda_{course_code}',
        curso=course_code,
        config=config,
        n_train=len(X_train),
        n_test=len(X_test)
    )
    
    logger.info(f"Modelo guardado en: {model_path}")
    
    return model_path


def main():
    """
    Función principal para ejecutar el script desde CLI.
    """
    parser = argparse.ArgumentParser(
        description='Entrena un modelo específico de predicción de demanda para un curso'
    )
    parser.add_argument(
        '--course',
        type=str,
        required=True,
        help='Código del curso (ej: CIB02)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Ruta al archivo de configuración YAML (opcional)'
    )
    parser.add_argument(
        '--data',
        type=str,
        required=True,
        help='Ruta al archivo CSV con datos de matrícula'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Forzar entrenamiento aunque no haya historia suficiente'
    )
    
    args = parser.parse_args()
    
    try:
        # Cargar configuración
        if args.config:
            config = cargar_config(args.config)
        else:
            config = get_default_config()
        
        # Cargar datos
        df = cargar_datos_csv(args.data)
        
        # Entrenar y guardar
        model_path = entrenar_y_guardar_especifico(
            df, args.course, config, force=args.force
        )
        
        if model_path:
            logger.info("\n✓ ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
            logger.info(f"✓ Modelo guardado en: {model_path}")
            return 0
        else:
            logger.warning("\n⚠ No se pudo entrenar el modelo")
            logger.warning("⚠ Considera usar el modelo general como alternativa")
            return 1
        
    except Exception as e:
        logger.error(f"ERROR: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
