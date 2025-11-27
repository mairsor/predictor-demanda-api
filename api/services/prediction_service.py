"""
Servicio de predicción de demanda.

Maneja la lógica de negocio para ejecutar predicciones usando los scripts bash.
"""

import subprocess
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import logging

from api.schemas.prediction_schemas import (
    PredictionRequest,
    PredictionResponse,
    CoursePrediction
)

logger = logging.getLogger(__name__)


class PredictionService:
    """Servicio para manejar predicciones de demanda."""
    
    def __init__(self, project_root: str = None):
        """
        Inicializa el servicio de predicción.
        
        Args:
            project_root: Ruta raíz del proyecto. Si es None, se detecta automáticamente.
        """
        if project_root is None:
            # Detectar raíz del proyecto (api/ está en la raíz)
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.scripts_dir = self.project_root / "scripts"
        self.results_dir = self.project_root / "results"
        
        # En Docker usa python directamente, en desarrollo usa el venv
        import sys
        self.python_exe = sys.executable
        
        # Crear directorio de resultados si no existe
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def predict(self, request: PredictionRequest) -> PredictionResponse:
        """
        Ejecuta predicción según la configuración del request.
        
        Args:
            request: Configuración de la predicción
            
        Returns:
            PredictionResponse con resultados
            
        Raises:
            RuntimeError: Si hay error en la ejecución
        """
        logger.info(f"Iniciando predicción: scope={request.scope}, model_type={request.model_type}")
        
        start_time = datetime.now()
        
        # Ejecutar predicción según scope
        if request.scope == "single":
            result_file = self._predict_single(request.course_code, request.model_type)
        elif request.scope == "multiple":
            result_file = self._predict_multiple(request.course_codes, request.model_type)
        else:  # all
            result_file = self._predict_all(request.model_type)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Leer resultados del CSV generado
        predictions = self._read_predictions(result_file)
        
        # Importar PredictionMetadata
        from api.schemas.prediction_schemas import PredictionMetadata
        
        # Construir response
        return PredictionResponse(
            success=True,
            message="Predicción completada exitosamente",
            output_file=result_file.name,  # Solo nombre del archivo
            courses_processed=len(predictions),
            predictions=predictions,
            metadata=PredictionMetadata(
                timestamp=datetime.now().isoformat(),
                execution_time_seconds=execution_time,
                model_type=request.model_type,
                scope=request.scope
            )
        )
    
    def _predict_single(self, course_code: str, model_type: str) -> Path:
        """Ejecuta predicción para un solo curso."""
        logger.info(f"Predicción individual: {course_code} con modelo {model_type}")
        
        # Usar Python directamente en lugar del script bash
        cmd = [
            str(self.python_exe),
            "-m", "src.modelo_todos",
            "--data", "data/matriculas_por_curso.csv",
            "--general_model", "models/modelo_demanda_general_v20251113.pkl",
            "--config", "configs/general_model.yml",
            "--model_type", model_type,
            "--courses", course_code
        ]
        
        return self._execute_prediction(cmd)
    
    def _predict_multiple(self, course_codes: List[str], model_type: str) -> Path:
        """Ejecuta predicción para varios cursos."""
        courses_str = ",".join(course_codes)
        logger.info(f"Predicción múltiple: {courses_str} con modelo {model_type}")
        
        cmd = [
            str(self.python_exe),
            "-m", "src.modelo_todos",
            "--data", "data/matriculas_por_curso.csv",
            "--general_model", "models/modelo_demanda_general_v20251113.pkl",
            "--config", "configs/general_model.yml",
            "--model_type", model_type,
            "--courses", courses_str
        ]
        
        return self._execute_prediction(cmd)
    
    def _predict_all(self, model_type: str) -> Path:
        """Ejecuta predicción para todos los cursos."""
        logger.info(f"Predicción de todos los cursos con modelo {model_type}")
        
        cmd = [
            str(self.python_exe),
            "-m", "src.modelo_todos",
            "--data", "data/matriculas_por_curso.csv",
            "--general_model", "models/modelo_demanda_general_v20251113.pkl",
            "--config", "configs/general_model.yml",
            "--model_type", model_type
        ]
        
        return self._execute_prediction(cmd)
    
    def _execute_prediction(self, cmd: List[str]) -> Path:
        """
        Ejecuta el comando de predicción y retorna el archivo de resultados generado.
        
        Args:
            cmd: Comando a ejecutar
            
        Returns:
            Path al archivo CSV generado
            
        Raises:
            RuntimeError: Si hay error en la ejecución
        """
        # Guardar archivos existentes para detectar el nuevo
        existing_files = set(self.results_dir.glob("predicciones_*.csv"))
        
        try:
            # Log del comando que se va a ejecutar
            logger.info(f"Ejecutando comando: {' '.join(cmd)}")
            logger.info(f"Directorio de trabajo: {self.project_root}")
            
            # Ejecutar comando
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )
            
            # Log de stdout y stderr
            if result.stdout:
                logger.info(f"STDOUT: {result.stdout}")
            if result.stderr:
                logger.warning(f"STDERR: {result.stderr}")
            
            if result.returncode != 0:
                logger.error(f"Error en predicción (código {result.returncode})")
                error_msg = result.stderr if result.stderr else result.stdout
                raise RuntimeError(f"Error ejecutando predicción: {error_msg}")
            
            logger.info("Predicción ejecutada exitosamente")
            
            # Encontrar el archivo nuevo generado
            new_files = set(self.results_dir.glob("predicciones_*.csv")) - existing_files
            
            if not new_files:
                raise RuntimeError("No se generó archivo de resultados")
            
            # Retornar el más reciente (debería ser solo uno)
            result_file = max(new_files, key=lambda p: p.stat().st_mtime)
            logger.info(f"Archivo de resultados: {result_file.name}")
            
            return result_file
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Timeout en ejecución de predicción")
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            raise RuntimeError(f"Error inesperado: {str(e)}")
    
    def _read_predictions(self, csv_file: Path) -> List[CoursePrediction]:
        """
        Lee el archivo CSV de predicciones y convierte a objetos CoursePrediction.
        
        Args:
            csv_file: Path al archivo CSV
            
        Returns:
            Lista de CoursePrediction
        """
        try:
            df = pd.read_csv(csv_file)
            
            # Verificar que el DataFrame no esté vacío
            if df.empty:
                logger.warning(f"El archivo CSV {csv_file.name} está vacío")
                return []
            
            logger.info(f"Leyendo {len(df)} predicciones del archivo {csv_file.name}")
            logger.info(f"Columnas encontradas: {df.columns.tolist()}")
            
            predictions = []
            for _, row in df.iterrows():
                # Redondear demanda predicha a entero
                demanda = int(round(float(row['prediccion_demanda'])))
                
                predictions.append(CoursePrediction(
                    codigo_curso=row['codigo_curso'],
                    nombre_curso=f"Curso {row['codigo_curso']}",  # Por defecto, se puede mejorar con DB
                    n_registros_historia=int(row['n_registros_historia']) if pd.notna(row.get('n_registros_historia')) else None,
                    cupo_maximo_promedio=float(row['cupo_maximo_promedio']) if pd.notna(row.get('cupo_maximo_promedio')) else None,
                    alumnos_previos_promedio=float(row['alumnos_previos_promedio']) if pd.notna(row.get('alumnos_previos_promedio')) else None,
                    prediccion_demanda=demanda,
                    demanda_predicha=demanda,  # Alias para frontend
                    mae_si_disponible=float(row['mae_si_disponible']) if pd.notna(row.get('mae_si_disponible')) else None,
                    modelo_usado=row['modelo_usado']
                ))
            
            logger.info(f"Se procesaron {len(predictions)} predicciones correctamente")
            return predictions
            
        except Exception as e:
            logger.error(f"Error leyendo predicciones del archivo {csv_file.name}: {str(e)}")
            logger.error(f"Contenido del archivo (primeras líneas):")
            try:
                with open(csv_file, 'r') as f:
                    logger.error(f.read(500))
            except:
                pass
            raise RuntimeError(f"Error leyendo archivo de resultados: {str(e)}")
