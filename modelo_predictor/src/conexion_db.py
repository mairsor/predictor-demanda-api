"""
Módulo de conexión a la base de datos PostgreSQL.

Usa variables de entorno para mantener las credenciales seguras.
Archivo .env debe estar en la raíz del proyecto.
"""

import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
# Busca el archivo .env en la raíz del proyecto
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'

if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Variables de entorno cargadas desde: {env_path}")
else:
    print(f"⚠ Advertencia: No se encontró el archivo .env en: {env_path}")
    print("  Usando variables de entorno del sistema o valores por defecto.")

# Obtener credenciales de las variables de entorno
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'matricula_inteligente')
DB_PORT = os.getenv('DB_PORT', '5432')

try:
    # Conectar a la base de datos usando variables de entorno
    connection = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )

    print("✓ Conexión exitosa a la base de datos.")
    print(f"  Host: {DB_HOST}")
    print(f"  Database: {DB_NAME}")
    print(f"  User: {DB_USER}")

    cursor = connection.cursor()
    
    # Obtener versión de PostgreSQL
    cursor.execute("SELECT version();")
    row = cursor.fetchone()
    print(f"\n✓ Versión de la base de datos:")
    print(f"  {row[0]}")

    # Consultar tabla profesor
    print(f"\n✓ Datos de la tabla 'profesor':")
    cursor.execute("SELECT * FROM profesor")
    rows = cursor.fetchall()
    
    if rows:
        for row in rows:
            print(f"  {row}")
    else:
        print("  (No hay registros)")

except psycopg2.Error as e:
    print(f"✗ Error de base de datos: {e}")
except Exception as e:
    print(f"✗ Error al conectar a la base de datos: {e}")

finally:
    if 'connection' in locals() and connection:
        connection.close()
        print("\n✓ Conexión cerrada.")
