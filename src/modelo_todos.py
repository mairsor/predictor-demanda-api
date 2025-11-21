"""
modelo_todos.py

Itera por todos los cursos en el dataset. Para cada curso:
- Si hay historia suficiente (>=min_history): entrena modelo específico
- Si no: usa el modelo general para predecir

Genera un archivo CSV con predicciones para todos los cursos.

Uso:
    python -m src.modelo_todos --data data/matriculas_por_curso.csv --general_model models/modelo_demanda_general_latest.pkl
    python -m src.modelo_todos --data data/matriculas_por_curso.csv --train_general

Autor: Sistema de Predicción de Demanda UNI
Fecha: 2025-11-13
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

import pandas as pd
import numpy as np
import yaml

from src.utilidades_modelo import (
    cargar_datos_csv,
    calcular_alumnos_elegibles,
    preparar_features,
    cargar_modelo,
    DEFAULT_FEATURES
)

# Importar funciones de entrenamiento
from src.modelo_general import entrenar_y_guardar_general
from src.modelo_especifico import entrenar_y_guardar_especifico, get_default_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def buscar_modelo_especifico(course_code: str, models_dir: str = 'models/') -> Optional[str]:
    """
    Busca si existe un modelo específico para el curso dado.
    
    Parameters
    ----------
    course_code : str
        Código del curso.
    models_dir : str
        Directorio donde buscar modelos.
    
    Returns
    -------
    str or None
        Ruta al modelo más reciente encontrado, o None.
    """
    models_path = Path(models_dir)
    if not models_path.exists():
        return None
    
    # Buscar archivos que coincidan con el patrón
    pattern = f"modelo_demanda_{course_code}_v*.pkl"
    matching_files = list(models_path.glob(pattern))
    
    if not matching_files:
        return None
    
    # Ordenar por fecha de modificación y tomar el más reciente
    matching_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return str(matching_files[0])


def predecir_con_modelo(
    model,
    df_curso: pd.DataFrame,
    features: list,
    target: str = 'alumnos_matriculados'
) -> Dict[str, Any]:
    """
    Realiza predicciones para un curso usando un modelo dado.
    
    Parameters
    ----------
    model : RandomForestRegressor or tuple
        Modelo entrenado o tupla (modelo, metadata).
    df_curso : pd.DataFrame
        Datos del curso.
    features : list
        Lista de features.
    target : str
        Nombre de la columna objetivo.
    
    Returns
    -------
    dict
        Diccionario con predicciones y estadísticas.
    """
    # Si model es una tupla (modelo, metadata), extraer
    if isinstance(model, tuple):
        modelo, metadata = model
        expected_cols = metadata.get('feature_names', None)
    else:
        modelo = model
        # Intentar obtener feature_names del modelo sklearn
        expected_cols = getattr(modelo, 'feature_names_in_', None)
        if expected_cols is not None:
            expected_cols = list(expected_cols)
    
    # Preparar features
    if target in df_curso.columns:
        X, y = preparar_features(df_curso, features, target=target, drop_target=True, expected_columns=expected_cols)
        tiene_target = True
    else:
        X, _ = preparar_features(df_curso, features, target=target, drop_target=False, expected_columns=expected_cols)
        y = None
        tiene_target = False
    
    # Predecir
    y_pred = modelo.predict(X)
    
    resultado = {
        'prediccion_media': float(np.mean(y_pred)),
        'prediccion_std': float(np.std(y_pred)),
        'n_registros': len(y_pred)
    }
    
    if tiene_target and y is not None:
        from sklearn.metrics import mean_absolute_error
        mae = mean_absolute_error(y, y_pred)
        resultado['mae'] = float(mae)
    else:
        resultado['mae'] = None
    
    return resultado


def procesar_todos_cursos(
    df: pd.DataFrame,
    config: Dict[str, Any],
    general_model_path: Optional[str] = None,
    use_cached: bool = True,
    train_specific: bool = True,
    force_model_type: Optional[str] = None,
    cursos_filtrados: Optional[list] = None
) -> pd.DataFrame:
    """
    Procesa todos los cursos únicos en el dataset.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame con todos los datos.
    config : dict
        Configuración.
    general_model_path : str, optional
        Ruta al modelo general.
    use_cached : bool
        Si True, usa modelos específicos existentes si los encuentra.
    train_specific : bool
        Si True, entrena modelos específicos cuando hay historia suficiente.
    force_model_type : str, optional
        Fuerza el uso de un tipo específico de modelo:
        - 'general': Solo usar modelo general para todos los cursos
        - 'specific': Solo usar modelos específicos (entrena si es necesario)
        - None: Usa estrategia automática (default)
    cursos_filtrados : list, optional
        Lista de códigos de curso a procesar. Si None, procesa todos.
    
    Returns
    -------
    pd.DataFrame
        DataFrame con predicciones para cada curso.
    """
    logger.info("=" * 70)
    logger.info("PROCESAMIENTO DE TODOS LOS CURSOS")
    logger.info("=" * 70)
    
    # Cargar modelo general
    modelo_general = None
    if general_model_path and Path(general_model_path).exists():
        logger.info(f"Cargando modelo general desde: {general_model_path}")
        modelo_general = cargar_modelo(general_model_path)
    else:
        logger.warning("No se proporcionó modelo general o no existe.")
        logger.warning("Se entrenará si es necesario.")
    
    # Calcular alumnos_elegibles si falta
    if 'alumnos_elegibles' not in df.columns or df['alumnos_elegibles'].isna().any():
        df = calcular_alumnos_elegibles(df)
    
    # Obtener lista de cursos únicos
    cursos = df['codigo_curso'].unique()
    
    # Filtrar cursos si se especificaron
    if cursos_filtrados:
        cursos_disponibles = set(cursos)
        cursos_solicitados = set(cursos_filtrados)
        cursos_no_encontrados = cursos_solicitados - cursos_disponibles
        
        if cursos_no_encontrados:
            logger.warning(f"Cursos no encontrados en el dataset: {cursos_no_encontrados}")
        
        cursos = [c for c in cursos if c in cursos_solicitados]
        
        if not cursos:
            logger.error("Ninguno de los cursos solicitados existe en el dataset")
            return pd.DataFrame()
        
        logger.info(f"Cursos filtrados: {cursos}")
    
    logger.info(f"Total de cursos únicos: {len(cursos)}")
    
    # Configuración
    features = config.get('features', DEFAULT_FEATURES)
    target = config.get('target', 'alumnos_matriculados')
    min_history = config.get('min_history_semesters', 6)
    output_dir = config.get('output_dir', 'models/')
    
    resultados = []
    
    for i, curso in enumerate(cursos, 1):
        logger.info("\n" + "=" * 70)
        logger.info(f"[{i}/{len(cursos)}] Procesando curso: {curso}")
        logger.info("=" * 70)
        
        df_curso = df[df['codigo_curso'] == curso].copy()
        n_registros = len(df_curso)
        
        logger.info(f"Registros históricos: {n_registros}")
        
        modelo_usado = None
        mae = None
        prediccion = None
        model_path = None
        
        # MODO FORZADO: Solo modelo general
        if force_model_type == 'general':
            logger.info(f"Modo forzado: usando SOLO modelo general")
            
            if modelo_general is None:
                logger.warning("Modelo general no disponible. Entrenando...")
                model_path = entrenar_y_guardar_general(df, config)
                modelo_general = cargar_modelo(model_path)
            
            try:
                resultado = predecir_con_modelo(modelo_general, df_curso, features, target)
                prediccion = resultado['prediccion_media']
                mae = resultado['mae']
                modelo_usado = 'general (forzado)'
            except Exception as e:
                logger.error(f"Error al usar modelo general: {e}")
                prediccion = None
                mae = None
                modelo_usado = 'error'
        
        # MODO FORZADO: Solo modelos específicos
        elif force_model_type == 'specific':
            logger.info(f"Modo forzado: usando SOLO modelo específico")
            
            # Intentar cargar modelo específico cached
            if use_cached:
                model_path = buscar_modelo_especifico(curso, output_dir)
                if model_path:
                    logger.info(f"Modelo específico encontrado: {model_path}")
                    try:
                        modelo_especifico = cargar_modelo(model_path)
                        resultado = predecir_con_modelo(modelo_especifico, df_curso, features, target)
                        prediccion = resultado['prediccion_media']
                        mae = resultado['mae']
                        modelo_usado = f'especifico_cached ({Path(model_path).name})'
                    except Exception as e:
                        logger.warning(f"Error al usar modelo específico cached: {e}")
            
            # Si no hay cached o falló, entrenar nuevo
            if modelo_usado is None:
                if n_registros >= min_history:
                    logger.info(f"Entrenando modelo específico...")
                    try:
                        model_path = entrenar_y_guardar_especifico(df, curso, config, force=False)
                        if model_path:
                            modelo_especifico = cargar_modelo(model_path)
                            resultado = predecir_con_modelo(modelo_especifico, df_curso, features, target)
                            prediccion = resultado['prediccion_media']
                            mae = resultado['mae']
                            modelo_usado = f'especifico_nuevo ({Path(model_path).name})'
                    except Exception as e:
                        logger.error(f"Error al entrenar modelo específico: {e}")
                        modelo_usado = 'error'
                else:
                    logger.error(f"Historia insuficiente para modelo específico ({n_registros} < {min_history})")
                    modelo_usado = 'error (historia insuficiente)'
        
        # MODO AUTOMÁTICO: Estrategia inteligente (default)
        else:
            # Estrategia: 1) Buscar modelo específico existente
            if use_cached:
                model_path = buscar_modelo_especifico(curso, output_dir)
                if model_path:
                    logger.info(f"Modelo específico encontrado: {model_path}")
                    try:
                        modelo_especifico = cargar_modelo(model_path)
                        resultado = predecir_con_modelo(modelo_especifico, df_curso, features, target)
                        prediccion = resultado['prediccion_media']
                        mae = resultado['mae']
                        modelo_usado = f'especifico_cached ({Path(model_path).name})'
                    except Exception as e:
                        logger.warning(f"Error al usar modelo específico cached: {e}")
            
            # Estrategia 2) Entrenar modelo específico si hay historia suficiente
            if modelo_usado is None and train_specific and n_registros >= min_history:
                logger.info(f"Entrenando modelo específico (historia: {n_registros} >= {min_history})...")
                try:
                    model_path = entrenar_y_guardar_especifico(df, curso, config, force=False)
                    if model_path:
                        modelo_especifico = cargar_modelo(model_path)
                        resultado = predecir_con_modelo(modelo_especifico, df_curso, features, target)
                        prediccion = resultado['prediccion_media']
                        mae = resultado['mae']
                        modelo_usado = f'especifico_nuevo ({Path(model_path).name})'
                except Exception as e:
                    logger.warning(f"Error al entrenar modelo específico: {e}")
            
            # Estrategia 3) Usar modelo general como fallback
            if modelo_usado is None:
                logger.info(f"Usando modelo general como fallback (historia: {n_registros} < {min_history})")
                
                if modelo_general is None:
                    logger.warning("Modelo general no disponible. Entrenando...")
                    model_path = entrenar_y_guardar_general(df, config)
                    modelo_general = cargar_modelo(model_path)
                
                try:
                    resultado = predecir_con_modelo(modelo_general, df_curso, features, target)
                    prediccion = resultado['prediccion_media']
                    mae = resultado['mae']
                    modelo_usado = 'general'
                except Exception as e:
                    logger.error(f"Error al usar modelo general: {e}")
                    prediccion = None
                    mae = None
                    modelo_usado = 'error'
        
        # Obtener datos adicionales del curso
        cupo_maximo = df_curso['cupo_maximo'].mean()
        alumnos_previos = df_curso['alumnos_previos'].mean()
        
        resultados.append({
            'codigo_curso': curso,
            'n_registros_historia': n_registros,
            'cupo_maximo_promedio': cupo_maximo,
            'alumnos_previos_promedio': alumnos_previos,
            'prediccion_demanda': prediccion,
            'mae_si_disponible': mae,
            'modelo_usado': modelo_usado
        })
        
        logger.info(f"✓ Curso {curso} procesado.")
        pred_str = f"{prediccion:.1f}" if prediccion is not None else "N/A"
        logger.info(f"  - Predicción: {pred_str}")
        logger.info(f"  - Modelo: {modelo_usado}")
    
    # Crear DataFrame de resultados
    df_resultados = pd.DataFrame(resultados)
    
    logger.info("\n" + "=" * 70)
    logger.info("RESUMEN DE PREDICCIONES")
    logger.info("=" * 70)
    logger.info(f"\n{df_resultados.to_string()}")
    
    return df_resultados


def main():
    """
    Función principal para ejecutar el script desde CLI.
    """
    parser = argparse.ArgumentParser(
        description='Procesa todos los cursos y genera predicciones'
    )
    parser.add_argument(
        '--data',
        type=str,
        required=True,
        help='Ruta al archivo CSV con datos de matrícula'
    )
    parser.add_argument(
        '--general_model',
        type=str,
        default=None,
        help='Ruta al modelo general .pkl (opcional)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='configs/general_model.yml',
        help='Ruta al archivo de configuración YAML'
    )
    parser.add_argument(
        '--use_cached',
        action='store_true',
        default=True,
        help='Usar modelos específicos existentes si los encuentra'
    )
    parser.add_argument(
        '--no_train_specific',
        action='store_true',
        help='No entrenar nuevos modelos específicos'
    )
    parser.add_argument(
        '--train_general',
        action='store_true',
        help='Entrenar modelo general automáticamente si no se proporciona'
    )
    parser.add_argument(
        '--model_type',
        type=str,
        choices=['general', 'specific', 'auto'],
        default='auto',
        help='Tipo de modelo a usar: general (solo general), specific (solo específicos), auto (estrategia automática)'
    )
    parser.add_argument(
        '--courses',
        type=str,
        default=None,
        help='Curso(s) específico(s) a procesar. Para un solo curso: "CIB02". Para varios: "CIB02,MAT101,FIS201". Si no se especifica, procesa todos los cursos.'
    )
    
    args = parser.parse_args()
    
    try:
        # Cargar configuración
        if Path(args.config).exists():
            with open(args.config, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            logger.warning("Config no encontrado, usando default")
            config = get_default_config()
        
        # Cargar datos
        df = cargar_datos_csv(args.data)
        
        # Determinar force_model_type
        force_type = None if args.model_type == 'auto' else args.model_type
        
        # Parsear cursos si se especificaron
        cursos_filtrados = None
        if args.courses:
            cursos_filtrados = [c.strip() for c in args.courses.split(',')]
            logger.info(f"Cursos solicitados: {cursos_filtrados}")
        
        # Procesar todos los cursos (o los filtrados)
        df_resultados = procesar_todos_cursos(
            df=df,
            config=config,
            general_model_path=args.general_model,
            use_cached=args.use_cached,
            train_specific=not args.no_train_specific,
            force_model_type=force_type,
            cursos_filtrados=cursos_filtrados
        )
        
        # Guardar resultados
        output_dir = Path(config.get('output_dir', 'models/')).parent / 'results'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"predicciones_{fecha}.csv"
        
        df_resultados.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"\n✓ Predicciones guardadas en: {output_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"ERROR: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
