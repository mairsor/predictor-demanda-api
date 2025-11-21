"""
Aplicación principal FastAPI para el sistema de predicción de demanda.

API REST para gestión de predicciones, resultados y modelos.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
from pathlib import Path

from api.routers import predictions, results, models
from api.schemas.prediction_schemas import HealthResponse, ErrorResponse

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="API de Predicción de Demanda de Matrícula",
    description="""
    API REST para predecir la demanda de matrícula en cursos universitarios.
    
    ## Funcionalidades principales:
    
    ### 📊 Predicciones
    * Predicción individual, múltiple o masiva
    * Selección de tipo de modelo (auto, general, específico)
    * Retorna archivo CSV y datos JSON
    
    ### 📁 Gestión de Resultados
    * Listar archivos de predicciones generados
    * Ver contenido de resultados
    * Eliminar resultados individuales o masivos
    
    ### 🤖 Gestión de Modelos
    * Listar modelos entrenados
    * Ver metadata de modelos
    * Eliminar modelos específicos o todos
    
    ## Tecnologías
    * FastAPI + Pydantic para validación
    * RandomForest para predicciones ML
    * PostgreSQL para datos históricos
    """,
    version="1.0.0",
    contact={
        "name": "Sistema de Predicción UNI",
        "url": "https://github.com/mairsor/sistema_recomendacion_generacion_horarios"
    },
    license_info={
        "name": "MIT"
    }
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(predictions.router)
app.include_router(results.router)
app.include_router(models.router)


# ==================== ENDPOINTS RAÍZ ====================

@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz con información de la API."""
    return {
        "message": "API de Predicción de Demanda de Matrícula - UNI",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "endpoints": {
            "predictions": "/api/v1/predictions",
            "results": "/api/v1/results",
            "models": "/api/v1/models"
        }
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"]
)
async def health_check():
    """
    Health check endpoint para verificar estado del servicio.
    
    Returns:
        HealthResponse con estado de servicios
    """
    # Verificar directorios esenciales
    project_root = Path(__file__).parent
    
    services_status = {
        "api": "ok",
        "data_dir": "ok" if (project_root / "data").exists() else "missing",
        "models_dir": "ok" if (project_root / "models").exists() else "missing",
        "results_dir": "ok" if (project_root / "results").exists() else "missing",
        "scripts_dir": "ok" if (project_root / "scripts").exists() else "missing"
    }
    
    # Determinar status general
    all_ok = all(status == "ok" for status in services_status.values())
    overall_status = "healthy" if all_ok else "degraded"
    
    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        services=services_status
    )


# ==================== MANEJADORES DE ERRORES ====================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Manejador personalizado para errores 404."""
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            success=False,
            error="Recurso no encontrado",
            detail=f"La ruta {request.url.path} no existe",
            timestamp=datetime.now().isoformat()
        ).dict()
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Manejador personalizado para errores 500."""
    logger.error(f"Error interno: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error="Error interno del servidor",
            detail="Ha ocurrido un error inesperado. Por favor, contacte al administrador.",
            timestamp=datetime.now().isoformat()
        ).dict()
    )


# ==================== EVENTOS ====================

@app.on_event("startup")
async def startup_event():
    """Evento al iniciar la aplicación."""
    logger.info("=" * 70)
    logger.info("API de Predicción de Demanda - INICIANDO")
    logger.info("=" * 70)
    logger.info(f"Versión: 1.0.0")
    logger.info(f"Docs: http://localhost:8000/docs")
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Evento al cerrar la aplicación."""
    logger.info("API de Predicción de Demanda - CERRANDO")


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload en desarrollo
        log_level="info"
    )
