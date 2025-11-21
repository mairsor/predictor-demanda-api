"""
Router de API para predicción de demanda.

Endpoints principales para realizar predicciones.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging

from api.schemas.prediction_schemas import (
    PredictionRequest,
    PredictionResponse,
    ErrorResponse
)
from api.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/predictions",
    tags=["Predicciones"]
)

# Instancia del servicio
prediction_service = PredictionService()


@router.post(
    "/",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Realizar predicción de demanda",
    description="""
    Realiza predicción de demanda de matrícula para cursos.
    
    **Opciones de scope:**
    - `single`: Predicción para un solo curso (requiere course_code)
    - `multiple`: Predicción para varios cursos (requiere course_codes)
    - `all`: Predicción para todos los cursos del dataset
    
    **Opciones de model_type:**
    - `auto`: Estrategia inteligente (específico cached > específico nuevo > general)
    - `general`: Solo modelo general para todos los cursos
    - `specific`: Solo modelos específicos (entrena si es necesario)
    
    **Retorna:**
    - Ruta del archivo CSV generado
    - Lista completa de predicciones por curso
    - Metadata del proceso
    """
)
async def predict_demand(request: PredictionRequest) -> PredictionResponse:
    """
    Endpoint principal para realizar predicciones.
    
    Examples:
        ```json
        {
            "scope": "single",
            "model_type": "auto",
            "course_code": "CIB02"
        }
        ```
        
        ```json
        {
            "scope": "multiple",
            "model_type": "general",
            "course_codes": ["CIB02", "MAT101", "FIS201"]
        }
        ```
        
        ```json
        {
            "scope": "all",
            "model_type": "specific"
        }
        ```
    """
    try:
        logger.info(f"POST /predictions - scope={request.scope}, model_type={request.model_type}")
        
        # Ejecutar predicción
        response = prediction_service.predict(request)
        
        logger.info(f"Predicción exitosa: {response.courses_processed} cursos procesados")
        return response
        
    except ValueError as e:
        logger.warning(f"Validación fallida: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Error en predicción: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ejecutando predicción: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )


@router.post(
    "/quick/{course_code}",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predicción rápida para un curso",
    description="Atajo para predicción de un solo curso con modo auto"
)
async def quick_predict(course_code: str) -> PredictionResponse:
    """
    Predicción rápida para un curso específico (modo auto).
    
    Args:
        course_code: Código del curso (ej: CIB02, MAT101)
    
    Returns:
        PredictionResponse con resultados
    """
    request = PredictionRequest(
        scope="single",
        model_type="auto",
        course_code=course_code
    )
    
    return await predict_demand(request)
