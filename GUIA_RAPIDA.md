# Guía Rápida de Uso - Modelo de Predicción de Demanda

## ✅ Proyecto Completado

Se ha creado exitosamente la estructura completa del sistema de predicción de demanda de cursos.

## 📂 Archivos Creados

### Módulos principales (src/)
- ✅ `src/__init__.py` - Inicializador del paquete
- ✅ `src/utilidades_modelo.py` - Funciones compartidas (596 líneas)
- ✅ `src/modelo_general.py` - Entrenamiento modelo global
- ✅ `src/modelo_especifico.py` - Entrenamiento por curso
- ✅ `src/modelo_todos.py` - Iterador automático

### Configuración
- ✅ `configs/general_model.yml` - Config modelo general
- ✅ `configs/ejemplo_CIB02.yml` - Config modelo específico

### Datos
- ✅ `data/matriculas_por_curso.csv` - Dataset con 35 registros de ejemplo (8 cursos)

### Documentación
- ✅ `README.md` - Documentación completa (400+ líneas)
- ✅ `requirements.txt` - Dependencias actualizadas

## 🚀 Ejemplos de Uso Rápido

### 1. Entrenar Modelo General
```bash
python -m src.modelo_general --config configs/general_model.yml --data data/matriculas_por_curso.csv
```

**Resultado esperado:**
```
MÉTRICAS DEL MODELO GENERAL
======================================================================
MAE:  1.74 alumnos
RMSE: 1.97 alumnos
R²:   0.9778
======================================================================
✓ Modelo guardado en: models/modelo_demanda_general_v20251113.pkl
```

### 2. Entrenar Modelo Específico (CIB02)
```bash
python -m src.modelo_especifico --course CIB02 --config configs/ejemplo_CIB02.yml --data data/matriculas_por_curso.csv
```

### 3. Procesar Todos los Cursos
```bash
python -m src.modelo_todos --data data/matriculas_por_curso.csv --general_model models/modelo_demanda_general_v20251113.pkl
```

**Resultado:** Archivo CSV en `results/` con predicciones para todos los cursos.

### 4. Ejecutar Pruebas Unitarias
```bash
python src/utilidades_modelo.py
```

## 📊 Estructura de Datos

El CSV debe tener estas columnas:

**Obligatorias (14):**
- curso_ofertado_id (int, PK), nombre_seccion (string), codigo_curso (string)
- semestre (string), creditos (int), tipo_curso (string)
- profesor_id (int, FK), alumnos_previos (int), variacion_matricula (float)
- num_prerrequisitos (int), tasa_aprobacion (float), franja_horaria (int)
- cupo_maximo (int), alumnos_matriculados (int, target)

**Opcionales (2):**
- profesor_popularidad (float), alumnos_elegibles (int)

## 🔧 Personalización

### Cambiar Features
Edita `configs/general_model.yml`:
```yaml
features:
  - creditos
  - alumnos_previos
  - tasa_aprobacion
  # ... añade o quita features aquí
```

### Ajustar Hiperparámetros
```yaml
hyperparams:
  n_estimators: 300  # número de árboles
  max_depth: 12      # profundidad máxima
  random_state: 42   # semilla aleatoria
```

### Cambiar Historia Mínima
En `ejemplo_CIB02.yml`:
```yaml
min_history_semesters: 6  # ajustar según necesidad
```

## 📈 Métricas de Calidad

El sistema evalúa cada modelo con:
- **MAE** (Mean Absolute Error): Error promedio en # de alumnos
- **RMSE** (Root Mean Squared Error): Error cuadrático medio
- **R²**: Proporción de varianza explicada (0-1, mayor es mejor)

## 🎯 Próximos Pasos

1. **Integrar con Base de Datos**
   - Implementar `get_data_from_db()` en `utilidades_modelo.py`
   - Reemplazar CSV por consulta SQL

2. **Crear Vista SQL para alumnos_elegibles**
   ```sql
   CREATE VIEW vista_alumnos_elegibles AS
   SELECT curso_id, COUNT(DISTINCT estudiante_id) as alumnos_elegibles
   FROM estudiantes_aprobados_prerrequisitos
   WHERE estudiante_id NOT IN (
       SELECT estudiante_id FROM aprobados WHERE curso_id = X
   )
   GROUP BY curso_id;
   ```

3. **Optimización de Hiperparámetros**
   - Implementar Grid Search o Random Search
   - Validación cruzada temporal

4. **Features Adicionales**
   - Promedio de calificaciones históricas
   - Tasa de deserción
   - Correlación con cursos simultáneos

## ⚠️ Notas Importantes

- Los modelos se guardan con timestamp en el nombre
- La metadata JSON incluye features, métricas y configuración
- El sistema usa one-hot encoding para variables categóricas
- Los archivos legacy en `modelo_predictor/` se mantienen por compatibilidad

## 📞 Soporte

Para dudas o problemas:
1. Revisar el README.md completo
2. Ejecutar pruebas unitarias: `python src/utilidades_modelo.py`
3. Verificar logs en consola (nivel INFO)

---

**Proyecto:** Predicción de Demanda de Cursos - UNI  
**Curso:** CIB02 - Ingeniería de Software  
**Fecha:** 2025-11-13  
**Estado:** ✅ FUNCIONAL
