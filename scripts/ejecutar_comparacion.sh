#!/bin/bash
# Script para comparar los 3 modos de predicción

echo "=========================================================================="
echo "COMPARACIÓN DE MODOS - General vs Específico vs Automático"
echo "=========================================================================="
echo ""

# Ir al directorio raíz del proyecto (un nivel arriba de scripts/)
SCRIPT_DIR="$( cd "$( echo "${BASH_SOURCE[0]%/*}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Modo General
echo "1/3 Ejecutando MODO GENERAL..."
echo "----------------------------------------------------------------------"
env/Scripts/python.exe -m src.modelo_todos \
    --data data/matriculas_por_curso.csv \
    --config configs/general_model.yml \
    --model_type general
echo ""
sleep 2

# Modo Específico
echo "2/3 Ejecutando MODO ESPECÍFICO..."
echo "----------------------------------------------------------------------"
env/Scripts/python.exe -m src.modelo_todos \
    --data data/matriculas_por_curso.csv \
    --config configs/general_model.yml \
    --model_type specific
echo ""
sleep 2

# Modo Automático
echo "3/3 Ejecutando MODO AUTOMÁTICO..."
echo "----------------------------------------------------------------------"
env/Scripts/python.exe -m src.modelo_todos \
    --data data/matriculas_por_curso.csv \
    --config configs/general_model.yml \
    --model_type auto
echo ""

echo "=========================================================================="
echo "✓ Comparación completada"
echo "=========================================================================="
echo ""
echo "Revisa la carpeta results/ para comparar los 3 CSV generados."
echo "Archivos generados (últimos 3):"
ls -lt results/*.csv | head -3
