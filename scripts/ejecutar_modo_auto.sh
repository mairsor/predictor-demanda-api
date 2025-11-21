#!/bin/bash
# Script para ejecutar modelo_todos.py en MODO AUTOMÁTICO
# Usa estrategia inteligente: específico cached > específico nuevo > general

echo "=================================================="
echo "MODO AUTOMÁTICO - Estrategia Inteligente"
echo "=================================================="
echo ""

# Ir al directorio raíz del proyecto (un nivel arriba de scripts/)
SCRIPT_DIR="$( cd "$( echo "${BASH_SOURCE[0]%/*}" )" && pwd )"
cd "$SCRIPT_DIR/.."

env/Scripts/python.exe -m src.modelo_todos \
    --data data/matriculas_por_curso.csv \
    --config configs/general_model.yml \
    --model_type auto

echo ""
echo "✓ Ejecución completada. Revisa results/ para ver las predicciones."
