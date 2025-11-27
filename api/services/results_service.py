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
                rows = len(df)
                
                # Obtener info del archivo
                stat = csv_file.stat()
                created_date = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
                modified_date = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                
                # Formatear tamaño
                size_bytes = stat.st_size
                if size_bytes < 1024:
                    size_human = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_human = f"{size_bytes / 1024:.2f} KB"
                else:
                    size_human = f"{size_bytes / 1024 / 1024:.2f} MB"
                
                result_files.append(ResultFileInfo(
                    filename=csv_file.name,
                    size_bytes=size_bytes,
                    size_human=size_human,
                    created_date=created_date,
                    modified_date=modified_date,
                    rows=rows
                ))
            except Exception as e:
                logger.warning(f"Error leyendo {csv_file.name}: {str(e)}")
                continue
        
        # Calcular totales
        total_bytes = sum(f.size_bytes for f in result_files)
        if total_bytes < 1024:
            total_size_human = f"{total_bytes} B"
        elif total_bytes < 1024 * 1024:
            total_size_human = f"{total_bytes / 1024:.2f} KB"
        else:
            total_size_human = f"{total_bytes / 1024 / 1024:.2f} MB"
        
        return ResultsListResponse(
            success=True,
            count=len(result_files),
            files=result_files,
            total_size_bytes=total_bytes,
            total_size_human=total_size_human
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
            
            # Transformar datos al formato esperado por el frontend
            data = []
            for _, row in df.iterrows():
                prediction = {
                    "codigo_curso": row.get("codigo_curso", ""),
                    "nombre_curso": f"Curso {row.get('codigo_curso', 'N/A')}",  # Nombre por defecto
                    "demanda_predicha": int(round(row.get("prediccion_demanda", 0))),
                    "prediccion_demanda": row.get("prediccion_demanda", 0),
                    "modelo_usado": row.get("modelo_usado", "N/A"),
                    "n_registros_historia": row.get("n_registros_historia"),
                    "cupo_maximo_promedio": row.get("cupo_maximo_promedio"),
                    "alumnos_previos_promedio": row.get("alumnos_previos_promedio"),
                    "mae_si_disponible": row.get("mae_si_disponible"),
                    "confianza": None
                }
                data.append(prediction)
            
            return {
                "success": True,
                "filename": filename,
                "rows": len(df),
                "columns": df.columns.tolist(),
                "data": data
            }
        except Exception as e:
            raise RuntimeError(f"Error leyendo archivo: {str(e)}")
