"""
Servicio para gestión de modelos entrenados.

Maneja operaciones CRUD sobre archivos de modelos (.pkl) y sus metadatos (.json).
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from api.schemas.prediction_schemas import (
    ModelFileInfo,
    ModelsListResponse,
    DeleteResponse
)

logger = logging.getLogger(__name__)


class ModelsService:
    """Servicio para gestionar modelos entrenados."""
    
    def __init__(self, project_root: str = None):
        """
        Inicializa el servicio de modelos.
        
        Args:
            project_root: Ruta raíz del proyecto
        """
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.models_dir = self.project_root / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
    
    def list_models(self) -> ModelsListResponse:
        """
        Lista todos los modelos entrenados disponibles.
        
        Returns:
            ModelsListResponse con información de modelos
        """
        model_files = []
        
        # Buscar todos los archivos .pkl de modelos
        for pkl_file in sorted(self.models_dir.glob("modelo_demanda_*.pkl"), reverse=True):
            try:
                # Determinar tipo y curso
                filename = pkl_file.stem  # Sin extensión
                
                if "general" in filename:
                    model_type = "general"
                    course_code = None
                else:
                    model_type = "especifico"
                    # Extraer código del curso del nombre
                    # Formato: modelo_demanda_CIB02_v20251113
                    parts = filename.split("_")
                    if len(parts) >= 3:
                        course_code = parts[2]
                    else:
                        course_code = "Unknown"
                
                # Verificar si tiene metadata
                json_file = pkl_file.with_suffix(".json")
                has_metadata = json_file.exists()
                
                # Obtener info del archivo
                stat = pkl_file.stat()
                created_at = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                
                model_files.append(ModelFileInfo(
                    filename=pkl_file.name,
                    filepath=str(pkl_file.relative_to(self.project_root)),
                    size_bytes=stat.st_size,
                    created_at=created_at,
                    model_type=model_type,
                    course_code=course_code,
                    has_metadata=has_metadata
                ))
            except Exception as e:
                logger.warning(f"Error procesando {pkl_file.name}: {str(e)}")
                continue
        
        return ModelsListResponse(
            success=True,
            count=len(model_files),
            models=model_files
        )
    
    def delete_model(self, filename: str, delete_metadata: bool = True) -> DeleteResponse:
        """
        Elimina un modelo específico y opcionalmente su metadata.
        
        Args:
            filename: Nombre del archivo .pkl del modelo
            delete_metadata: Si True, también elimina el .json
            
        Returns:
            DeleteResponse con resultado de la operación
        """
        pkl_file = self.models_dir / filename
        
        # Validar que el archivo existe
        if not pkl_file.exists():
            return DeleteResponse(
                success=False,
                message=f"Modelo no encontrado: {filename}"
            )
        
        # Validar que es un archivo de modelo
        if not filename.startswith("modelo_demanda_") or not filename.endswith(".pkl"):
            return DeleteResponse(
                success=False,
                message=f"Archivo no válido. Solo se pueden eliminar archivos de modelos (.pkl)"
            )
        
        deleted_files = []
        errors = []
        
        try:
            # Eliminar archivo .pkl
            pkl_file.unlink()
            deleted_files.append(filename)
            logger.info(f"Modelo eliminado: {filename}")
            
            # Eliminar metadata si existe y se solicita
            if delete_metadata:
                json_file = pkl_file.with_suffix(".json")
                if json_file.exists():
                    try:
                        json_file.unlink()
                        deleted_files.append(json_file.name)
                        logger.info(f"Metadata eliminada: {json_file.name}")
                    except Exception as e:
                        errors.append(f"Error eliminando metadata: {str(e)}")
            
            message = f"Eliminados: {', '.join(deleted_files)}"
            if errors:
                message += f". Advertencias: {'; '.join(errors)}"
            
            return DeleteResponse(
                success=True,
                message=message,
                deleted_item=", ".join(deleted_files)
            )
            
        except Exception as e:
            logger.error(f"Error eliminando {filename}: {str(e)}")
            return DeleteResponse(
                success=False,
                message=f"Error al eliminar modelo: {str(e)}"
            )
    
    def delete_all_models(self, include_general: bool = False) -> DeleteResponse:
        """
        Elimina todos los modelos específicos (y opcionalmente el general).
        
        Args:
            include_general: Si True, también elimina el modelo general
            
        Returns:
            DeleteResponse con resultado de la operación
        """
        deleted_count = 0
        errors = []
        
        for pkl_file in self.models_dir.glob("modelo_demanda_*.pkl"):
            # Si no incluir general, saltar modelo general
            if not include_general and "general" in pkl_file.name:
                continue
            
            try:
                pkl_file.unlink()
                deleted_count += 1
                
                # También eliminar metadata si existe
                json_file = pkl_file.with_suffix(".json")
                if json_file.exists():
                    json_file.unlink()
                    
            except Exception as e:
                errors.append(f"{pkl_file.name}: {str(e)}")
        
        if errors:
            return DeleteResponse(
                success=False,
                message=f"Eliminados {deleted_count} modelos. Errores: {'; '.join(errors)}"
            )
        
        model_type_msg = "todos los modelos" if include_general else "modelos específicos"
        return DeleteResponse(
            success=True,
            message=f"Eliminados {deleted_count} {model_type_msg} correctamente",
            deleted_item=f"{deleted_count} modelos"
        )
    
    def get_model_metadata(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la metadata de un modelo específico.
        
        Args:
            filename: Nombre del archivo .pkl del modelo
            
        Returns:
            Diccionario con metadata o None si no existe
        """
        pkl_file = self.models_dir / filename
        json_file = pkl_file.with_suffix(".json")
        
        if not json_file.exists():
            return None
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error leyendo metadata: {str(e)}")
            return None
