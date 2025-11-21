# 🔒 Guía de Seguridad - Variables de Entorno

## ✅ Cambios Implementados

Se ha configurado el proyecto para **NO exponer credenciales** en el código fuente.

### 📁 Archivos Creados

1. **`.env`** - Credenciales reales (NO se sube a GitHub)
2. **`.env.example`** - Plantilla pública para otros desarrolladores
3. **`.gitignore`** actualizado - Excluye archivos sensibles

### 🔧 Cómo Funciona

#### Antes ❌ (Inseguro):
```python
connection = psycopg2.connect(
    host="172.232.188.183",
    user="admin",
    password="admin123",  # ¡EXPUESTO EN GITHUB!
    database="matricula_inteligente",
    port="5435"
)
```

#### Ahora ✅ (Seguro):
```python
import os
from dotenv import load_dotenv

load_dotenv()  # Carga variables desde .env

connection = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),  # Lee desde .env
    database=os.getenv('DB_NAME'),
    port=os.getenv('DB_PORT')
)
```

## 📋 Pasos para Configurar (Para Otros Desarrolladores)

### 1. Clonar el Repositorio
```bash
git clone <tu-repo>
cd modelo_predictor_demanda
```

### 2. Crear el Archivo `.env`
```bash
# Copiar la plantilla
cp .env.example .env

# Editar con tus credenciales reales
nano .env  # o usar cualquier editor
```

### 3. Configurar Variables
Edita `.env` con tus valores:
```env
DB_HOST=tu_servidor
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña_secreta
DB_NAME=tu_base_datos
DB_PORT=5432
```

### 4. Instalar Dependencias
```bash
pip install python-dotenv
```

### 5. Probar Conexión
```bash
python modelo_predictor/src/conexion_db.py
```

## 🛡️ Archivos Protegidos por `.gitignore`

El archivo `.gitignore` ahora excluye:

```gitignore
# Variables de entorno - NUNCA subir
.env

# Entorno virtual
env/
venv/

# Modelos entrenados (archivos grandes)
models/*.pkl

# Resultados
results/*.csv

# Cache de Python
__pycache__/
*.pyc

# Configuración de IDE
.vscode/
.idea/
```

## 📝 Archivo `.env.example`

**Este archivo SÍ se sube a GitHub** como plantilla:

```env
# Plantilla de variables de entorno
# Copia este archivo como .env y reemplaza con tus valores reales

DB_HOST=tu_host_aqui
DB_USER=tu_usuario_aqui
DB_PASSWORD=tu_contraseña_aqui
DB_NAME=tu_base_de_datos_aqui
DB_PORT=5432
```

## ✅ Validación

Para verificar que `.env` está siendo ignorado por git:

```bash
# Ver archivos rastreados
git status

# El archivo .env NO debe aparecer en la lista

# Ver archivos ignorados
git check-ignore -v .env
# Debe mostrar: .gitignore:4:.env    .env
```

## ⚠️ Importante: Si Ya Subiste Credenciales

Si accidentalmente subiste credenciales a GitHub:

### 1. Cambiar Todas las Contraseñas
```sql
-- En PostgreSQL
ALTER USER admin WITH PASSWORD 'nueva_contraseña_segura';
```

### 2. Eliminar del Historial de Git
```bash
# Usar BFG Repo-Cleaner o git filter-branch
# ¡PELIGROSO! Reescribe el historial

# Alternativa: Hacer el repositorio privado temporalmente
```

### 3. Notificar al Equipo
- Informar sobre el cambio de credenciales
- Actualizar servicios que usen la BD

## 🎯 Buenas Prácticas Adicionales

### 1. Variables de Entorno en Producción

Para servidores (Heroku, AWS, etc.):
```bash
# Heroku
heroku config:set DB_HOST=xxx DB_USER=xxx DB_PASSWORD=xxx

# AWS EC2
export DB_HOST=xxx
export DB_USER=xxx
export DB_PASSWORD=xxx
```

### 2. Usar `.env` Local para Desarrollo

```python
# Prioridad de variables:
# 1. Variables del sistema
# 2. Variables de .env (desarrollo)
# 3. Valores por defecto (fallback)

DB_HOST = os.getenv('DB_HOST', 'localhost')  # Default: localhost
```

### 3. Validar Conexión al Iniciar

```python
def validate_db_connection():
    """Valida que todas las variables de BD estén configuradas."""
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'DB_PORT']
    
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        raise ValueError(f"Faltan variables de entorno: {missing}")
    
    print("✓ Todas las variables de BD configuradas")
```

## 📚 Recursos Adicionales

- [python-dotenv Documentation](https://pypi.org/project/python-dotenv/)
- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [12 Factor App - Config](https://12factor.net/config)

## 🔍 Checklist de Seguridad

Antes de hacer `git push`:

- [ ] `.env` está en `.gitignore`
- [ ] No hay contraseñas en el código
- [ ] `.env.example` tiene valores de ejemplo (no reales)
- [ ] `git status` no muestra `.env`
- [ ] Credenciales reales solo en `.env` local

---

**✅ Proyecto ahora seguro para GitHub**  
**Fecha:** 2025-11-13  
**Estado:** Implementado y Validado
