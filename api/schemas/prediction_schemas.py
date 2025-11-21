"""
Schemas (DTOs) para la API de predicción de demanda.

Define los modelos Pydantic para validación de requests/responses.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime


# ==================== PREDICCIÓN ====================

class PredictionRequest(BaseModel):
    """Request para realizar predicción de demanda."""
    
    scope: Literal["single", "multiple", "all"] = Field(
        ...,
        description="Alcance de la predicción: single (un curso), multiple (varios), all (todos)"
    )
    
    model_type: Literal["auto", "general", "specific"] = Field(
        default="auto",
        description="Tipo de modelo: auto (estrategia inteligente), general (solo modelo general), specific (solo específicos)"
    )
    
    course_code: Optional[str] = Field(
        None,
        description="Código del curso (requerido si scope='single'). Ejemplo: 'CIB02'"
    )
    
    course_codes: Optional[List[str]] = Field(
        None,
        description="Lista de códigos de cursos (requerido si scope='multiple'). Ejemplo: ['CIB02', 'MAT101']"
    )
    
    @validator('course_code')
    def validate_single_course(cls, v, values):
        if values.get('scope') == 'single' and not v:
            raise ValueError("course_code es requerido cuando scope='single'")
        return v
    
    @validator('course_codes')
    def validate_multiple_courses(cls, v, values):
        if values.get('scope') == 'multiple':
            if not v or len(v) == 0:
                raise ValueError("course_codes debe contener al menos un curso cuando scope='multiple'")
        return v
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "scope": "single",
                    "model_type": "auto",
                    "course_code": "CIB02"
                },
                {
                    "scope": "multiple",
                    "model_type": "general",
                    "course_codes": ["CIB02", "MAT101", "FIS201"]
                },
                {
                    "scope": "all",
                    "model_type": "specific"
                }
            ]
        }


class CoursePrediction(BaseModel):
    """Predicción para un curso específico."""
    
    codigo_curso: str
    n_registros_historia: int
    cupo_maximo_promedio: float
    alumnos_previos_promedio: float
    prediccion_demanda: float
    mae_si_disponible: Optional[float]
    modelo_usado: str


class PredictionResponse(BaseModel):
    """Response de predicción exitosa."""
    
    success: bool = True
    message: str
    file_path: str
    timestamp: str
    scope: str
    model_type: str
    courses_processed: int
    predictions: List[CoursePrediction]
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Predicción completada exitosamente",
                "file_path": "results/predicciones_20251113_190805.csv",
                "timestamp": "2025-11-13 19:08:05",
                "scope": "single",
                "model_type": "auto",
                "courses_processed": 1,
                "predictions": [
                    {
                        "codigo_curso": "CIB02",
                        "n_registros_historia": 6,
                        "cupo_maximo_promedio": 50.0,
                        "alumnos_previos_promedio": 46.5,
                        "prediccion_demanda": 49.18,
                        "mae_si_disponible": 1.83,
                        "modelo_usado": "especifico_cached (modelo_demanda_CIB02_v20251113.pkl)"
                    }
                ]
            }
        }


# ==================== RESULTADOS ====================

class ResultFileInfo(BaseModel):
    """Información de un archivo de resultados."""
    
    filename: str
    filepath: str
    size_bytes: int
    created_at: str
    courses_count: int


class ResultsListResponse(BaseModel):
    """Response con lista de archivos de resultados."""
    
    success: bool = True
    count: int
    results: List[ResultFileInfo]


class DeleteResultRequest(BaseModel):
    """Request para eliminar un archivo de resultados."""
    
    filename: str = Field(
        ...,
        description="Nombre del archivo a eliminar. Ejemplo: 'predicciones_20251113_190805.csv'"
    )


class DeleteResponse(BaseModel):
    """Response genérica de eliminación."""
    
    success: bool
    message: str
    deleted_item: Optional[str] = None


# ==================== MODELOS ====================

class ModelFileInfo(BaseModel):
    """Información de un archivo de modelo entrenado."""
    
    filename: str
    filepath: str
    size_bytes: int
    created_at: str
    model_type: str  # "general" o "especifico"
    course_code: Optional[str] = None  # Solo para modelos específicos
    has_metadata: bool


class ModelsListResponse(BaseModel):
    """Response con lista de modelos entrenados."""
    
    success: bool = True
    count: int
    models: List[ModelFileInfo]


class DeleteModelRequest(BaseModel):
    """Request para eliminar un modelo."""
    
    filename: str = Field(
        ...,
        description="Nombre del archivo del modelo a eliminar. Ejemplo: 'modelo_demanda_CIB02_v20251113.pkl'"
    )
    
    delete_metadata: bool = Field(
        default=True,
        description="Si True, también elimina el archivo .json de metadata asociado"
    )


# ==================== ERRORES ====================

class ErrorResponse(BaseModel):
    """Response de error."""
    
    success: bool = False
    error: str
    detail: Optional[str] = None
    timestamp: str


# ==================== HEALTH CHECK ====================

class HealthResponse(BaseModel):
    """Response de health check."""
    
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: str
    services: dict
