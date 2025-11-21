# Modelo de Predicción de Demanda de Cursos - UNI

Sistema modular para predecir la demanda de matrícula de cursos usando Random Forest Regressor. Incluye modelo general (todos los cursos), modelos específicos por curso, sistema iterador para procesamiento masivo, y **API REST completa** para integración con backend.

Este proyecto corresponde al curso CIB02 – Ingeniería de Software (FIEE UNI) y se desarrolla como un prototipo funcional (MVP), con datos simulados y validación de algoritmos.

## 📋 Características

- **Modelo General**: Entrena con datos de todos los cursos para tener una base robusta
- **Modelos Específicos**: Ajuste fino por curso cuando hay suficiente historia
- **Sistema Iterador**: Procesa todos los cursos automáticamente usando la mejor estrategia disponible
- **API REST con FastAPI**: Backend completo con 11 endpoints para predicciones, gestión de resultados y modelos
- **Documentación Automática**: Swagger UI y ReDoc incluidos
- **Configuración YAML**: Hiperparámetros y features configurables por archivo
- **Metadata Completa**: Cada modelo incluye métricas, features y timestamp
- **Scripts Bash**: Automatización de tareas comunes organizados en `scripts/`
- **Modular y Extensible**: Diseñado para reemplazar cálculos Python por vistas SQL en el futuro

## 🏗️ Estructura del Proyecto

```
modelo_predictor_demanda/
├── api/                        # 🆕 API REST con FastAPI
│   ├── __init__.py
│   ├── routers/               # Endpoints REST
│   │   ├── __init__.py
│   │   ├── predictions.py    # POST /api/v1/predictions
│   │   ├── results.py        # GET/DELETE /api/v1/results
│   │   └── models.py         # GET/DELETE /api/v1/models
│   ├── services/              # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── prediction_service.py
│   │   ├── results_service.py
│   │   └── models_service.py
│   └── schemas/               # Modelos Pydantic (DTOs)
│       ├── __init__.py
│       └── prediction_schemas.py
├── src/                       # Core ML
│   ├── __init__.py
│   ├── utilidades_modelo.py  # Funciones compartidas (carga, preprocessing, métricas)
│   ├── modelo_general.py     # Entrena modelo global
│   ├── modelo_especifico.py  # Entrena modelo por curso
│   └── modelo_todos.py       # Itera y predice para todos los cursos
├── scripts/                   # 🆕 Scripts bash organizados
│   ├── ejecutar_modo_general.sh
│   ├── ejecutar_modo_especifico.sh
│   ├── ejecutar_modo_auto.sh
│   ├── ejecutar_curso_individual.sh
│   ├── ejecutar_cursos_seleccionados.sh
│   └── ejecutar_comparacion.sh
├── configs/
│   ├── general_model.yml     # Configuración del modelo general
│   └── ejemplo_CIB02.yml     # Configuración para curso específico
├── data/
│   └── matriculas_por_curso.csv # Dataset de ejemplo (16 columnas)
├── models/                    # Modelos .pkl y metadata .json (generado)
├── results/                   # Predicciones CSV (generado)
├── pruebas_automatizadas/     # Tests existentes
├── main.py                    # 🆕 Aplicación FastAPI
├── requirements.txt           # Dependencias Python (actualizado)
└── README.md                  # Este archivo
```

## 📊 Formato del Dataset

El archivo CSV debe contener las siguientes columnas:

### Columnas Obligatorias

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| `curso_ofertado_id` | int | ID único de la sección (PK) | `1` |
| `nombre_seccion` | string | Nombre descriptivo de la sección | `"CIB02-2023-1-A"` |
| `codigo_curso` | string | Código del curso | `"CIB02"` |
| `semestre` | string | Periodo académico | `"2025-2"` |
| `creditos` | int | Créditos del curso | `4` |
| `tipo_curso` | string | Obligatorio (O) o Electivo (E) | `"O"` |
| `profesor_id` | int | ID del profesor (FK) | `1` |
| `alumnos_previos` | int | Matriculados en ciclo anterior | `45` |
| `variacion_matricula` | float | Cambio % respecto ciclo anterior | `0.1` (10%) |
| `num_prerrequisitos` | int | Cantidad de prerrequisitos | `2` |
| `tasa_aprobacion` | float | Tasa de aprobación histórica (0-1) | `0.80` (80%) |
| `franja_horaria` | int | 1=mañana, 2=tarde, 3=noche | `1` |
| `cupo_maximo` | int | Capacidad máxima de la sección | `50` |
| `alumnos_matriculados` | int | **TARGET** - Alumnos realmente matriculados | `48` |

### Columnas Opcionales

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| `profesor_popularidad` | float | Popularidad del profesor (0-1) | `0.85` |
| `alumnos_elegibles` | int | Alumnos que pueden matricularse | `60` |

**Nota**: Si `alumnos_elegibles` no está presente, se calculará automáticamente usando la fórmula:
```
alumnos_elegibles = max(alumnos_previos * 1.2, cupo_maximo)
```

En el futuro, esto se reemplazará por una vista SQL que cuente estudiantes que aprobaron prerrequisitos.

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
cd modelo_predictor_demanda
```

### 2. Crear entorno virtual
```bash
python -m venv env
```

### 3. Activar entorno virtual

**Windows:**
```bash
env\Scripts\activate
```

**Linux/Mac:**
```bash
source env/bin/activate
```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

## 💻 Uso

### 🚀 Opción 1: API REST (Recomendado)

#### Iniciar el servidor FastAPI

```bash
# Método 1: Usando el script principal
python main.py

# Método 2: Usando uvicorn directamente
uvicorn main:app --reload

# Método 3: Especificar host y puerto
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

El servidor estará disponible en:
- **API**: http://localhost:8000
- **Documentación Swagger UI**: http://localhost:8000/docs
- **Documentación ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

#### Usar la API con Postman o curl

**1. Predecir UN SOLO CURSO:**
```bash
curl -X POST "http://localhost:8000/api/v1/predictions" \
  -H "Content-Type: application/json" \
  -d '{
    "scope": "single",
    "model_type": "auto",
    "course_code": "MAT101"
  }'
```

**2. Predecir VARIOS CURSOS:**
```bash
curl -X POST "http://localhost:8000/api/v1/predictions" \
  -H "Content-Type: application/json" \
  -d '{
    "scope": "multiple",
    "model_type": "auto",
    "course_codes": ["MAT101", "FIS201", "CIB02"]
  }'
```

**3. Predecir TODOS LOS CURSOS:**
```bash
curl -X POST "http://localhost:8000/api/v1/predictions" \
  -H "Content-Type: application/json" \
  -d '{
    "scope": "all",
    "model_type": "general"
  }'
```

**4. Predicción rápida (atajo):**
```bash
curl -X POST "http://localhost:8000/api/v1/predictions/quick/MAT101"
```

**5. Listar resultados:**
```bash
curl -X GET "http://localhost:8000/api/v1/results"
```

**6. Listar modelos entrenados:**
```bash
curl -X GET "http://localhost:8000/api/v1/models"
```

Ver sección [📡 API REST Reference](#-api-rest-reference) para más detalles.

---

### 🖥️ Opción 2: CLI (Línea de comandos)

#### 1. Entrenar Modelo General

Entrena un modelo con datos de todos los cursos:

```bash
python -m src.modelo_general --config configs/general_model.yml --data data/matriculas_por_curso.csv
```

**Salida:**
- `models/modelo_demanda_general_vYYYYMMDD.pkl` - Modelo serializado
- `models/modelo_demanda_general_vYYYYMMDD.json` - Metadata (features, métricas, hiperparámetros)
- `models/general_metrics.json` - Métricas consolidadas

#### 2. Entrenar Modelo Específico

Entrena un modelo para un curso específico:

```bash
python -m src.modelo_especifico --course CIB02 --config configs/ejemplo_CIB02.yml --data data/matriculas_por_curso.csv
```

**Con flag `--force`** (entrenar aunque no haya historia suficiente):
```bash
python -m src.modelo_especifico --course CIB02 --data data/matriculas_por_curso.csv --force
```

**Salida:**
- `models/modelo_demanda_CIB02_vYYYYMMDD.pkl`
- `models/modelo_demanda_CIB02_vYYYYMMDD.json`

#### 3. Procesar Todos los Cursos

Itera por todos los cursos y genera predicciones:

```bash
python -m src.modelo_todos --data data/matriculas_por_curso.csv --general_model models/modelo_demanda_general_v20251113.pkl
```

**Entrenar modelo general automáticamente si no existe:**
```bash
python -m src.modelo_todos --data data/matriculas_por_curso.csv --train_general
```

**No entrenar nuevos modelos específicos (solo usar existentes):**
```bash
python -m src.modelo_todos --data data/matriculas_por_curso.csv --no_train_specific --general_model models/modelo_demanda_general_latest.pkl
```

**Predecir cursos específicos con `--courses`:**
```bash
# Un solo curso
python -m src.modelo_todos --data data/matriculas_por_curso.csv --courses MAT101

# Varios cursos separados por comas
python -m src.modelo_todos --data data/matriculas_por_curso.csv --courses MAT101,FIS201,CIB02
```

**Salida:**
- `results/predicciones_YYYYMMDD_HHMMSS.csv` - Predicciones para todos los cursos

Formato del CSV de resultados:
```csv
codigo_curso,n_registros_historia,cupo_maximo_promedio,alumnos_previos_promedio,prediccion_demanda,mae_si_disponible,modelo_usado
CIB02,6,50.0,46.5,49.2,1.8,especifico_nuevo (modelo_demanda_CIB02_v20251113.pkl)
MAT101,6,70.0,67.5,70.1,2.3,especifico_cached (modelo_demanda_MAT101_v20251110.pkl)
QUI301,4,30.0,25.0,26.5,,general
```

---

### 🔧 Opción 3: Scripts Bash (Atajos)

Ejecuta tareas comunes desde el directorio `scripts/`:

```bash
# Modo general (todos los cursos con modelo general)
bash scripts/ejecutar_modo_general.sh

# Modo específico (entrena modelo específico por curso)
bash scripts/ejecutar_modo_especifico.sh

# Modo automático (mezcla general + específicos disponibles)
bash scripts/ejecutar_modo_auto.sh

# Predecir un solo curso
bash scripts/ejecutar_curso_individual.sh MAT101

# Predecir varios cursos seleccionados
bash scripts/ejecutar_cursos_seleccionados.sh "MAT101,FIS201,CIB02"

# Comparar modelos general vs específico
bash scripts/ejecutar_comparacion.sh
```

## ⚙️ Configuración

Los archivos `.yml` en `configs/` controlan el comportamiento de los modelos:

```yaml
# Features a usar
features:
  - creditos
  - alumnos_previos
  - variacion_matricula
  - num_prerrequisitos
  - tasa_aprobacion
  - franja_horaria
  - alumnos_elegibles
  - cupo_maximo
  - tipo_curso

# Hiperparámetros de RandomForest
hyperparams:
  n_estimators: 300
  max_depth: 12
  min_samples_split: 5
  min_samples_leaf: 2
  random_state: 42
  n_jobs: -1

# Variable objetivo
target: alumnos_matriculados

# Train/test split
test_size: 0.2

# Mínimo de semestres de historia (solo para modelos específicos)
min_history_semesters: 6

# Directorio de salida
output_dir: models/
```

## 📈 Métricas

Los modelos se evalúan con:

- **MAE** (Mean Absolute Error): Error promedio en número de alumnos
- **RMSE** (Root Mean Squared Error): Error cuadrático medio
- **R²** (Coefficient of Determination): Varianza explicada por el modelo

Ejemplo de salida:
```
MÉTRICAS DEL MODELO GENERAL
======================================================================
MAE:  2.15 alumnos
RMSE: 3.42 alumnos
R²:   0.9248
======================================================================
```

## 🔧 Funciones Principales (utilidades_modelo.py)

### Carga de Datos
- `cargar_datos_csv(path)` - Lee y valida CSV
- `get_data_from_db(conn_params)` - Stub para futuro uso con SQL (NotImplementedError)

### Preprocesamiento
- `calcular_alumnos_elegibles(df)` - Calcula columna si falta (aproximación pandas)
- `preparar_features(df, features)` - Imputación, one-hot encoding, split X/y

### Modelado
- `entrenar_rf_regressor(X, y, params)` - Entrena RandomForest
- `evaluar_regresor(model, X_test, y_test)` - Calcula métricas

### Persistencia
- `guardar_modelo_y_metadata(model, features, metrics, ...)` - Guarda .pkl y .json
- `cargar_modelo(path)` - Carga modelo desde .pkl

## 📡 API REST Reference

### Endpoints Disponibles

#### 🎯 Predicciones

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/predictions` | Predicción completa con configuración |
| POST | `/api/v1/predictions/quick/{course_code}` | Atajo para predecir un curso (auto mode) |

**Body de ejemplo para `/api/v1/predictions`:**

```json
{
  "scope": "single",           // "single" | "multiple" | "all"
  "model_type": "auto",        // "auto" | "specific" | "general"
  "course_code": "MAT101",     // requerido si scope = "single"
  "course_codes": ["MAT101"]   // requerido si scope = "multiple"
}
```

**Opciones de `model_type`:**
- `"auto"`: Usa modelo específico si existe, si no usa general
- `"specific"`: Solo usa modelo específico (falla si no existe)
- `"general"`: Usa el modelo general para todos los cursos

**Respuesta exitosa:**
```json
{
  "success": true,
  "message": "Predicción completada exitosamente",
  "file_path": "results/predicciones_20251119_143045.csv",
  "timestamp": "2025-11-19T14:30:45",
  "predictions": [
    {
      "codigo_curso": "MAT101",
      "nombre_curso": "Cálculo I",
      "demanda_predicha": 250,
      "modelo_utilizado": "específico",
      "fecha_prediccion": "2025-11-19"
    }
  ]
}
```

#### 📁 Gestión de Resultados

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/results` | Listar todos los archivos CSV de resultados |
| GET | `/api/v1/results/{filename}` | Obtener contenido de un CSV específico |
| DELETE | `/api/v1/results/{filename}` | Eliminar un archivo de resultados |
| DELETE | `/api/v1/results?confirm=true` | Eliminar todos los resultados (requiere confirmación) |

#### 🤖 Gestión de Modelos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/models` | Listar todos los modelos entrenados (.pkl) |
| GET | `/api/v1/models/{filename}/metadata` | Obtener metadata JSON de un modelo |
| DELETE | `/api/v1/models/{filename}?delete_metadata=true` | Eliminar modelo (y opcionalmente su metadata) |
| DELETE | `/api/v1/models?confirm=true&include_general=false` | Eliminar modelos específicos (general opcional) |

#### 🏥 Sistema

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información general de la API |
| GET | `/health` | Health check (valida directorios data/, models/, results/) |

### Ejemplos con Postman

**1. Configurar Postman:**
- **URL**: `http://localhost:8000/api/v1/predictions`
- **Método**: `POST`
- **Headers**: `Content-Type: application/json`
- **Body** (raw JSON): Selecciona `JSON` en el dropdown

**2. Ejemplos de Body:**

```json
// Predicción de un solo curso
{
  "scope": "single",
  "model_type": "auto",
  "course_code": "MAT101"
}

// Predicción de varios cursos
{
  "scope": "multiple",
  "model_type": "auto",
  "course_codes": ["MAT101", "FIS201", "CIB02"]
}

// Predicción de todos los cursos
{
  "scope": "all",
  "model_type": "general"
}
```

**3. Ver documentación interactiva:**
- Abre http://localhost:8000/docs
- Prueba endpoints directamente desde el navegador
- La documentación incluye schemas, ejemplos y validaciones

### Códigos de Estado HTTP

| Código | Significado |
|--------|-------------|
| 200 | OK - Operación exitosa |
| 201 | Created - Recurso creado exitosamente |
| 400 | Bad Request - Error en validación de datos |
| 404 | Not Found - Recurso no encontrado |
| 500 | Internal Server Error - Error en el servidor |

---

## 🧪 Tests

### Pruebas unitarias en utilidades_modelo.py
```bash
python src/utilidades_modelo.py
```

### Pruebas automatizadas existentes
```bash
cd pruebas_automatizadas
pytest test_demanda.py -v
```

### Probar API con curl
```bash
# Health check
curl http://localhost:8000/health

# Predicción rápida
curl -X POST http://localhost:8000/api/v1/predictions/quick/MAT101

# Listar resultados
curl http://localhost:8000/api/v1/results

# Listar modelos
curl http://localhost:8000/api/v1/models
```

## 🔮 Roadmap y TODOs

### Implementaciones Futuras

1. **Autenticación y Autorización en API**
   - Implementar JWT tokens para endpoints sensibles
   - Rate limiting para prevenir abuso
   - Roles de usuario (admin, viewer)

2. **Vista SQL para `alumnos_elegibles`**
   - Reemplazar `calcular_alumnos_elegibles()` 
   - Usar `get_data_from_db()` que retorne vista SQL con:
   ```sql
   SELECT COUNT(DISTINCT estudiante_id) as alumnos_elegibles
   FROM estudiantes_aprobados_prerrequisitos
   WHERE curso_id = X AND estudiante_id NOT IN (
       SELECT estudiante_id FROM aprobados WHERE curso_id = X
   )
   ```

3. **Mejoras en la API**
   - Paginación para listado de resultados y modelos
   - Filtros avanzados (por fecha, curso, tipo de modelo)
   - Websockets para notificaciones en tiempo real
   - Background tasks para predicciones largas

4. **CLI mejorado con Typer**
   - Descomenta `typer>=0.9` en requirements.txt
   - Interfaces interactivas para configuración

5. **Validación cruzada**
   - Implementar K-Fold CV para modelos específicos
   - Validación temporal (train en semestres anteriores, test en recientes)

6. **Features adicionales**
   - Promedio de calificaciones históricas
   - Tasa de deserción por curso
   - Correlación con cursos simultáneos
   - Tendencias estacionales

7. **Optimización de hiperparámetros**
   - Grid Search o Random Search automático
   - Guardar mejores parámetros en metadata
   - AutoML con optuna o hyperopt

8. **Despliegue y DevOps**
   - Dockerización de la aplicación
   - CI/CD con GitHub Actions
   - Despliegue en AWS/Azure/GCP
   - Monitoreo con Prometheus + Grafana

## 📝 Notas Técnicas

### Compatibilidad de Features

**IMPORTANTE**: Al usar `modelo_todos.py`, las features deben ser consistentes entre el modelo general y los específicos. El sistema aplica one-hot encoding a columnas categóricas, por lo que:

- Si entrenas con `tipo_curso`, todas las predicciones necesitan esa columna
- El orden de las columnas después de one-hot debe coincidir
- Usa los mismos archivos de configuración para consistencia

### Versionado de Modelos

Los archivos incluyen fecha en el nombre:
```
modelo_demanda_CIB02_v20251113.pkl
modelo_demanda_CIB02_v20251113.json
```

Esto permite:
- Comparar rendimiento entre versiones
- Rollback a modelos anteriores
- Auditoría de cambios

### Metadata JSON

Ejemplo de metadata guardada:
```json
{
  "model_name": "modelo_demanda_CIB02_v20251113",
  "curso": "CIB02",
  "date": "2025-11-13T14:30:45.123456",
  "features": ["creditos", "alumnos_previos", "tipo_curso_O", ...],
  "metrics": {
    "MAE": 2.15,
    "RMSE": 3.42,
    "R2": 0.9248
  },
  "n_train": 48,
  "n_test": 12,
  "hyperparams": {
    "n_estimators": 300,
    "max_depth": 12,
    "random_state": 42
  },
  "config_hash": "a3f5b2c8d9e1f4..."
}
```

## 🔧 Tecnologías Utilizadas

### Backend y API
- **FastAPI** (>=0.104.0): Framework web moderno para APIs REST
- **Uvicorn** (>=0.24.0): Servidor ASGI de alto rendimiento
- **Pydantic** (>=2.0.0): Validación de datos con type hints

### Machine Learning
- **scikit-learn** (>=1.2.0): RandomForestRegressor y métricas
- **pandas** (>=1.5.0): Manipulación de datos
- **numpy** (>=1.24.0): Operaciones numéricas
- **imbalanced-learn** (>=0.10.0): Técnicas para datos desbalanceados

### Persistencia y Configuración
- **joblib** (>=1.2.0): Serialización de modelos
- **PyYAML** (>=6.0.0): Configuración en YAML

### Base de Datos
- **SQLAlchemy** (>=1.4.0): ORM
- **psycopg2-binary** (>=2.9.0): Driver PostgreSQL

### Testing y Calidad
- **pytest** (>=7.0.0): Framework de testing
- **pytest-cov** (>=4.0.0): Cobertura de código

---

## 🤝 Contribuciones

Para agregar nuevas funcionalidades:

1. Mantén la modularidad (separa funciones en utilidades_modelo.py)
2. Documenta con docstrings (formato numpy)
3. Añade pruebas unitarias
4. Actualiza este README
5. Registra cambios en metadata JSON
6. Para cambios en API, actualiza schemas de Pydantic
7. Ejecuta tests antes de commit

### Workflow recomendado:
```bash
# 1. Crear rama
git checkout -b feature/nueva-funcionalidad

# 2. Hacer cambios y tests
pytest tests/ -v

# 3. Verificar API funciona
python main.py

# 4. Commit y push
git add .
git commit -m "feat: descripción del cambio"
git push origin feature/nueva-funcionalidad
```

---

## 📞 Soporte

### Documentación
- **Swagger UI**: http://localhost:8000/docs (cuando el servidor está corriendo)
- **ReDoc**: http://localhost:8000/redoc
- **Este README**: Para guía completa

### Issues y Preguntas
- Reporta bugs en GitHub Issues
- Para preguntas académicas, contacta al instructor del curso CIB02

---

## 📄 Licencia

Proyecto académico - Universidad Nacional de Ingeniería (UNI)  
Curso: Ingeniería de Software (CIB02) - FIEE

**Autores**: Equipo del proyecto  
**Institución**: Universidad Nacional de Ingeniería (UNI)  
**Semestre**: 2025-2

---

## 📝 Changelog

### [2.0.0] - 2025-11-19
#### Added
- ✨ API REST completa con FastAPI (11 endpoints)
- 📡 Documentación automática con Swagger UI y ReDoc
- 🔄 Endpoints para predicciones (single/multiple/all)
- 📁 CRUD completo para gestión de resultados CSV
- 🤖 CRUD completo para gestión de modelos entrenados
- 🏥 Health check endpoint
- 📦 Schemas Pydantic para validación de datos
- 🎯 Quick prediction endpoint (atajo)
- 🔧 Scripts bash organizados en `scripts/`
- ⚙️ Parámetro `--courses` en modelo_todos.py

#### Changed
- 📚 README ampliado con documentación de API
- 📦 requirements.txt actualizado y organizado
- 🏗️ Estructura del proyecto reorganizada

#### Removed
- ❌ Variable `experiencia_anios` eliminada del dataset (16 columnas ahora)

### [1.0.0] - 2025-11-13
- 🎉 Versión inicial con modelos general, específico y sistema iterador
- 📊 Dataset con 17 columnas originales
- ⚙️ Configuración YAML
- 📈 Métricas MAE, RMSE, R²

---

**Última actualización**: 2025-11-19  
**Versión actual**: 2.0.0  
**Python**: 3.11+  
**FastAPI**: 0.104.0+
