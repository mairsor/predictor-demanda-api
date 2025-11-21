"""
Router de API para gestión de archivos de resultados.

Endpoints CRUD para archivos CSV de predicciones.
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, Any
import logging

from api.schemas.prediction_schemas import (
    ResultsListResponse,
    DeleteResultRequest,
    DeleteResponse
)
from api.services.results_service import ResultsService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/results",
    tags=["Resultados"]
)

# Instancia del servicio
results_service = ResultsService()


@router.get(
    "/",
    response_model=ResultsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar archivos de resultados",
    description="Obtiene lista de todos los archivos CSV de predicciones generados"
)
async def list_results() -> ResultsListResponse:
    """
    Lista todos los archivos de resultados disponibles.
    
    Returns:
        ResultsListResponse con información de cada archivo
    """
    try:
        logger.info("GET /results - Listando archivos de resultados")
        response = results_service.list_results()
        logger.info(f"Encontrados {response.count} archivos de resultados")
        return response
        
    except Exception as e:
        logger.error(f"Error listando resultados: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listando resultados: {str(e)}"
        )


@router.get(
    "/{filename}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Obtener contenido de un resultado",
    description="Obtiene el contenido completo de un archivo CSV de resultados específico"
)
async def get_result_content(filename: str) -> Dict[str, Any]:
    """
    Obtiene el contenido de un archivo de resultados.
    
    Args:
        filename: Nombre del archivo (ej: predicciones_20251113_190805.csv)
        
    Returns:
        Diccionario con el contenido del CSV
    """
    try:
        logger.info(f"GET /results/{filename} - Obteniendo contenido")
        content = results_service.get_result_content(filename)
        return content
        
    except FileNotFoundError as e:
        logger.warning(f"Archivo no encontrado: {filename}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error obteniendo contenido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo contenido: {str(e)}"
        )


@router.delete(
    "/{filename}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Eliminar un archivo de resultados",
    description="Elimina un archivo CSV de resultados específico"
)
async def delete_result(filename: str) -> DeleteResponse:
    """
    Elimina un archivo de resultados específico.
    
    Args:
        filename: Nombre del archivo a eliminar
        
    Returns:
        DeleteResponse con resultado de la operación
    """
    try:
        logger.info(f"DELETE /results/{filename}")
        response = results_service.delete_result(filename)
        
        if response.success:
            logger.info(f"Archivo eliminado: {filename}")
        else:
            logger.warning(f"Fallo al eliminar: {response.message}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error eliminando resultado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando resultado: {str(e)}"
        )


@router.delete(
    "/",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Eliminar todos los resultados",
    description="Elimina todos los archivos CSV de resultados"
)
async def delete_all_results(
    confirm: bool = Query(
        False,
        description="Debe ser True para confirmar la eliminación masiva"
    )
) -> DeleteResponse:
    """
    Elimina todos los archivos de resultados.
    
    PRECAUCIÓN: Esta acción es irreversible.
    
    Args:
        confirm: Debe ser True para ejecutar
        
    Returns:
        DeleteResponse con resultado
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe confirmar la eliminación con confirm=true"
        )
    
    try:
        logger.warning("DELETE /results?confirm=true - Eliminando todos los resultados")
        response = results_service.delete_all_results()
        logger.info(f"Resultado: {response.message}")
        return response
        
    except Exception as e:
        logger.error(f"Error eliminando resultados: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando resultados: {str(e)}"
        )
