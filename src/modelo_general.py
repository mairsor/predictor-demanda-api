"""
modelo_general.py

Script para entrenar un modelo RandomForestRegressor global usando datos de todos
los cursos consolidados. El modelo se guarda en la carpeta 'models/' junto con
su metadata.

Uso:
    python -m src.modelo_general --config configs/general_model.yml --data data/matriculas_por_curso.csv

Autor: Sistema de Predicción de Demanda UNI
Fecha: 2025-11-13
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any

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
        'output_dir': 'models/'
    }


def entrenar_y_guardar_general(
    df: pd.DataFrame,
    config: Dict[str, Any]
) -> str:
    """
    Entrena el modelo general y lo guarda con su metadata.
    
    Esta función puede ser importada y usada por otros scripts.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame con todos los datos de cursos.
    config : dict
        Configuración del modelo.
    
    Returns
    -------
    str
        Ruta del archivo del modelo guardado.
    """
    logger.info("=" * 70)
    logger.info("ENTRENAMIENTO DE MODELO GENERAL")
    logger.info("=" * 70)
    
    # Calcular alumnos_elegibles si falta
    if 'alumnos_elegibles' not in df.columns or df['alumnos_elegibles'].isna().any():
        logger.info("Calculando alumnos_elegibles...")
        df = calcular_alumnos_elegibles(df)
    
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
    
    logger.info(f"Total de muestras: {len(df)}")
    logger.info(f"Features seleccionadas: {features}")
    logger.info(f"Hyperparámetros: {hyperparams}")
    
    # Preparar features
    X, y = preparar_features(df, features, target=target, drop_target=True)
    
    # Split train/test
    random_state = hyperparams.get('random_state', 42)
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
    logger.info("MÉTRICAS DEL MODELO GENERAL")
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
        name_prefix='modelo_demanda_general',
        config=config,
        n_train=len(X_train),
        n_test=len(X_test)
    )
    
    # Guardar métricas adicionales
    import json
    metrics_file = Path(output_dir) / 'general_metrics.json'
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metrics': metrics,
            'n_train': len(X_train),
            'n_test': len(X_test),
            'model_path': model_path
        }, f, indent=2)
    
    logger.info(f"Métricas adicionales guardadas en: {metrics_file}")
    logger.info(f"Modelo guardado en: {model_path}")
    
    return model_path


def main():
    """
    Función principal para ejecutar el script desde CLI.
    """
    parser = argparse.ArgumentParser(
        description='Entrena un modelo general de predicción de demanda'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='configs/general_model.yml',
        help='Ruta al archivo de configuración YAML'
    )
    parser.add_argument(
        '--data',
        type=str,
        required=True,
        help='Ruta al archivo CSV con datos de matrícula'
    )
    
    args = parser.parse_args()
    
    try:
        # Cargar configuración
        config = cargar_config(args.config)
        
        # Cargar datos
        df = cargar_datos_csv(args.data)
        
        # Entrenar y guardar
        model_path = entrenar_y_guardar_general(df, config)
        
        logger.info("\n✓ ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
        logger.info(f"✓ Modelo guardado en: {model_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"ERROR: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
