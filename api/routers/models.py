"""
Router de API para gestión de modelos entrenados.

Endpoints CRUD para archivos .pkl de modelos y sus metadatos.
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, Any, Optional
import logging

from api.schemas.prediction_schemas import (
    ModelsListResponse,
    DeleteModelRequest,
    DeleteResponse
)
from api.services.models_service import ModelsService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/models",
    tags=["Modelos"]
)

# Instancia del servicio
models_service = ModelsService()


@router.get(
    "/",
    response_model=ModelsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar modelos entrenados",
    description="Obtiene lista de todos los modelos entrenados (general y específicos)"
)
async def list_models() -> ModelsListResponse:
    """
    Lista todos los modelos entrenados disponibles.
    
    Returns:
        ModelsListResponse con información de cada modelo
    """
    try:
        logger.info("GET /models - Listando modelos")
        response = models_service.list_models()
        logger.info(f"Encontrados {response.count} modelos")
        return response
        
    except Exception as e:
        logger.error(f"Error listando modelos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listando modelos: {str(e)}"
        )


@router.get(
    "/{filename}/metadata",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Obtener metadata de un modelo",
    description="Obtiene el archivo JSON de metadata asociado a un modelo específico"
)
async def get_model_metadata(filename: str) -> Dict[str, Any]:
    """
    Obtiene la metadata de un modelo específico.
    
    Args:
        filename: Nombre del archivo .pkl del modelo
        
    Returns:
        Diccionario con metadata del modelo
    """
    try:
        logger.info(f"GET /models/{filename}/metadata")
        metadata = models_service.get_model_metadata(filename)
        
        if metadata is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Metadata no encontrada para el modelo: {filename}"
            )
        
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo metadata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo metadata: {str(e)}"
        )


@router.delete(
    "/{filename}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Eliminar un modelo",
    description="Elimina un archivo .pkl de modelo y opcionalmente su metadata .json"
)
async def delete_model(
    filename: str,
    delete_metadata: bool = Query(
        True,
        description="Si True, también elimina el archivo .json de metadata"
    )
) -> DeleteResponse:
    """
    Elimina un modelo específico.
    
    Args:
        filename: Nombre del archivo .pkl a eliminar
        delete_metadata: Si True, también elimina el .json
        
    Returns:
        DeleteResponse con resultado de la operación
    """
    try:
        logger.info(f"DELETE /models/{filename}?delete_metadata={delete_metadata}")
        response = models_service.delete_model(filename, delete_metadata)
        
        if response.success:
            logger.info(f"Modelo eliminado: {filename}")
        else:
            logger.warning(f"Fallo al eliminar: {response.message}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error eliminando modelo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando modelo: {str(e)}"
        )


@router.delete(
    "/",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Eliminar modelos específicos",
    description="Elimina todos los modelos específicos (preserva el general por defecto)"
)
async def delete_all_models(
    confirm: bool = Query(
        False,
        description="Debe ser True para confirmar la eliminación masiva"
    ),
    include_general: bool = Query(
        False,
        description="Si True, también elimina el modelo general"
    )
) -> DeleteResponse:
    """
    Elimina todos los modelos específicos (y opcionalmente el general).
    
    PRECAUCIÓN: Esta acción es irreversible.
    
    Args:
        confirm: Debe ser True para ejecutar
        include_general: Si True, también elimina modelo general
        
    Returns:
        DeleteResponse con resultado
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe confirmar la eliminación con confirm=true"
        )
    
    try:
        logger.warning(f"DELETE /models?confirm=true&include_general={include_general}")
        response = models_service.delete_all_models(include_general)
        logger.info(f"Resultado: {response.message}")
        return response
        
    except Exception as e:
        logger.error(f"Error eliminando modelos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando modelos: {str(e)}"
        )
