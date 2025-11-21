#!/bin/bash

# Script para predecir demanda de VARIOS CURSOS SELECCIONADOS
# Permite seleccionar el tipo de modelo: auto, general o specific
#
# Uso:
#   ./ejecutar_cursos_seleccionados.sh <CURSO1,CURSO2,CURSO3,...> [TIPO_MODELO]
#
# Ejemplos:
#   ./ejecutar_cursos_seleccionados.sh "CIB02,MAT101"                 # Modo automático (default)
#   ./ejecutar_cursos_seleccionados.sh "CIB02,MAT101,FIS201" auto     # Modo automático explícito
#   ./ejecutar_cursos_seleccionados.sh "ELE501,QUI301" general        # Solo modelo general
#   ./ejecutar_cursos_seleccionados.sh "CIB02,MAT101" specific        # Solo modelos específicos
#
# NOTA: Los códigos de curso deben estar separados por comas SIN ESPACIOS

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar argumentos
if [ $# -lt 1 ]; then
    echo -e "${RED}Error: Falta la lista de cursos${NC}"
    echo "Uso: $0 <CURSO1,CURSO2,CURSO3,...> [TIPO_MODELO]"
    echo ""
    echo "Ejemplos:"
    echo "  $0 \"CIB02,MAT101\"                 # Modo automático (default)"
    echo "  $0 \"CIB02,MAT101,FIS201\" auto     # Modo automático explícito"
    echo "  $0 \"ELE501,QUI301\" general        # Solo modelo general"
    echo "  $0 \"CIB02,MAT101\" specific        # Solo modelos específicos"
    echo ""
    echo -e "${YELLOW}NOTA: Los códigos de curso deben estar separados por comas SIN ESPACIOS${NC}"
    exit 1
fi

CURSOS=$1
TIPO_MODELO=${2:-auto}  # Default: auto

# Validar tipo de modelo
if [[ ! "$TIPO_MODELO" =~ ^(auto|general|specific)$ ]]; then
    echo -e "${RED}Error: Tipo de modelo inválido: $TIPO_MODELO${NC}"
    echo "Los tipos válidos son: auto, general, specific"
    exit 1
fi

# Validar formato de cursos (no debe tener espacios)
if [[ "$CURSOS" =~ [[:space:]] ]]; then
    echo -e "${RED}Error: La lista de cursos no debe contener espacios${NC}"
    echo "Formato correcto: \"CIB02,MAT101,FIS201\" (sin espacios)"
    exit 1
fi

# Contar cursos
IFS=',' read -ra CURSO_ARRAY <<< "$CURSOS"
NUM_CURSOS=${#CURSO_ARRAY[@]}

# Ir al directorio raíz del proyecto (un nivel arriba de scripts/)
SCRIPT_DIR="$( cd "$( echo "${BASH_SOURCE[0]%/*}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Configuración
DATA_FILE="data/matriculas_por_curso.csv"
GENERAL_MODEL="models/modelo_demanda_general_v20251113.pkl"
CONFIG_FILE="configs/general_model.yml"

# Verificar que existen los archivos necesarios
if [ ! -f "$DATA_FILE" ]; then
    echo -e "${RED}Error: No se encuentra el archivo de datos: $DATA_FILE${NC}"
    exit 1
fi

# Banner
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}PREDICCIÓN DE DEMANDA - CURSOS SELECCIONADOS${NC}"
echo -e "${GREEN}==================================================${NC}"
echo -e "${YELLOW}Cursos seleccionados:${NC} $CURSOS"
echo -e "${YELLOW}Número de cursos:${NC} $NUM_CURSOS"
echo -e "${YELLOW}Tipo de modelo:${NC} $TIPO_MODELO"
echo ""

# Mostrar lista de cursos
echo -e "${BLUE}Cursos a procesar:${NC}"
for curso in "${CURSO_ARRAY[@]}"; do
    echo "  - $curso"
done
echo ""

# Ejecutar predicción
env/Scripts/python.exe -m src.modelo_todos \
    --data "$DATA_FILE" \
    --general_model "$GENERAL_MODEL" \
    --config "$CONFIG_FILE" \
    --model_type "$TIPO_MODELO" \
    --courses "$CURSOS"

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Ejecución completada. Revisa results/ para ver las predicciones.${NC}"
else
    echo ""
    echo -e "${RED}✗ Error durante la ejecución.${NC}"
    exit 1
fi
