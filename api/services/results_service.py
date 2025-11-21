"""
Servicio para gestión de archivos de resultados.

Maneja operaciones CRUD sobre archivos CSV de resultados de predicciones.
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import logging

from api.schemas.prediction_schemas import (
    ResultFileInfo,
    ResultsListResponse,
    DeleteResponse
)

logger = logging.getLogger(__name__)


class ResultsService:
    """Servicio para gestionar archivos de resultados."""
    
    def __init__(self, project_root: str = None):
        """
        Inicializa el servicio de resultados.
        
        Args:
            project_root: Ruta raíz del proyecto
        """
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.results_dir = self.project_root / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def list_results(self) -> ResultsListResponse:
        """
        Lista todos los archivos de resultados disponibles.
        
        Returns:
            ResultsListResponse con información de archivos
        """
        result_files = []
        
        # Buscar todos los CSV de predicciones
        for csv_file in sorted(self.results_dir.glob("predicciones_*.csv"), reverse=True):
            try:
                # Leer metadata del CSV
                df = pd.read_csv(csv_file)
                courses_count = len(df)
                
                # Obtener info del archivo
                stat = csv_file.stat()
                created_at = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                
                result_files.append(ResultFileInfo(
                    filename=csv_file.name,
                    filepath=str(csv_file.relative_to(self.project_root)),
                    size_bytes=stat.st_size,
                    created_at=created_at,
                    courses_count=courses_count
                ))
            except Exception as e:
                logger.warning(f"Error leyendo {csv_file.name}: {str(e)}")
                continue
        
        return ResultsListResponse(
            success=True,
            count=len(result_files),
            results=result_files
        )
    
    def delete_result(self, filename: str) -> DeleteResponse:
        """
        Elimina un archivo de resultados específico.
        
        Args:
            filename: Nombre del archivo a eliminar
            
        Returns:
            DeleteResponse con resultado de la operación
        """
        file_path = self.results_dir / filename
        
        # Validar que el archivo existe
        if not file_path.exists():
            return DeleteResponse(
                success=False,
                message=f"Archivo no encontrado: {filename}"
            )
        
        # Validar que es un archivo de predicciones
        if not filename.startswith("predicciones_") or not filename.endswith(".csv"):
            return DeleteResponse(
                success=False,
                message=f"Archivo no válido. Solo se pueden eliminar archivos de predicciones (.csv)"
            )
        
        try:
            file_path.unlink()
            logger.info(f"Archivo eliminado: {filename}")
            
            return DeleteResponse(
                success=True,
                message="Archivo eliminado correctamente",
                deleted_item=filename
            )
        except Exception as e:
            logger.error(f"Error eliminando {filename}: {str(e)}")
            return DeleteResponse(
                success=False,
                message=f"Error al eliminar archivo: {str(e)}"
            )
    
    def delete_all_results(self) -> DeleteResponse:
        """
        Elimina todos los archivos de resultados.
        
        Returns:
            DeleteResponse con resultado de la operación
        """
        deleted_count = 0
        errors = []
        
        for csv_file in self.results_dir.glob("predicciones_*.csv"):
            try:
                csv_file.unlink()
                deleted_count += 1
            except Exception as e:
                errors.append(f"{csv_file.name}: {str(e)}")
        
        if errors:
            return DeleteResponse(
                success=False,
                message=f"Eliminados {deleted_count} archivos. Errores: {'; '.join(errors)}"
            )
        
        return DeleteResponse(
            success=True,
            message=f"Eliminados {deleted_count} archivos de resultados correctamente",
            deleted_item=f"{deleted_count} archivos"
        )
    
    def get_result_content(self, filename: str) -> Dict[str, Any]:
        """
        Obtiene el contenido de un archivo de resultados específico.
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Diccionario con el contenido del CSV
        """
        file_path = self.results_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {filename}")
        
        try:
            df = pd.read_csv(file_path)
            return {
                "filename": filename,
                "courses_count": len(df),
                "data": df.to_dict(orient="records")
            }
        except Exception as e:
            raise RuntimeError(f"Error leyendo archivo: {str(e)}")
