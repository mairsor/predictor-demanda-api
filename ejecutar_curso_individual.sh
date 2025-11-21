#!/bin/bash

# Script para predecir demanda de UN SOLO CURSO específico
# Permite seleccionar el tipo de modelo: auto, general o specific
#
# Uso:
#   ./ejecutar_curso_individual.sh <CODIGO_CURSO> [TIPO_MODELO]
#
# Ejemplos:
#   ./ejecutar_curso_individual.sh CIB02          # Modo automático (default)
#   ./ejecutar_curso_individual.sh MAT101 auto    # Modo automático explícito
#   ./ejecutar_curso_individual.sh FIS201 general # Solo modelo general
#   ./ejecutar_curso_individual.sh ELE501 specific # Solo modelo específico

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar argumentos
if [ $# -lt 1 ]; then
    echo -e "${RED}Error: Falta el código del curso${NC}"
    echo "Uso: $0 <CODIGO_CURSO> [TIPO_MODELO]"
    echo ""
    echo "Ejemplos:"
    echo "  $0 CIB02          # Modo automático (default)"
    echo "  $0 MAT101 auto    # Modo automático explícito"
    echo "  $0 FIS201 general # Solo modelo general"
    echo "  $0 ELE501 specific # Solo modelo específico"
    exit 1
fi

CURSO=$1
TIPO_MODELO=${2:-auto}  # Default: auto

# Validar tipo de modelo
if [[ ! "$TIPO_MODELO" =~ ^(auto|general|specific)$ ]]; then
    echo -e "${RED}Error: Tipo de modelo inválido: $TIPO_MODELO${NC}"
    echo "Los tipos válidos son: auto, general, specific"
    exit 1
fi

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
echo -e "${GREEN}PREDICCIÓN DE DEMANDA - CURSO INDIVIDUAL${NC}"
echo -e "${GREEN}==================================================${NC}"
echo -e "${YELLOW}Curso:${NC} $CURSO"
echo -e "${YELLOW}Tipo de modelo:${NC} $TIPO_MODELO"
echo ""

# Ejecutar predicción
"D:/Estudios/Universidad Nacional de Ingeniería/8. Octavo Ciclo/Ingeniería de Software (CIB02)/Proyecto/modelo_predictor_demanda/env/Scripts/python.exe" -m src.modelo_todos \
    --data "$DATA_FILE" \
    --general_model "$GENERAL_MODEL" \
    --config "$CONFIG_FILE" \
    --model_type "$TIPO_MODELO" \
    --courses "$CURSO"

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Ejecución completada. Revisa results/ para ver las predicciones.${NC}"
else
    echo ""
    echo -e "${RED}✗ Error durante la ejecución.${NC}"
    exit 1
fi
