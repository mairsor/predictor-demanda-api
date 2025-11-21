#!/bin/bash
# Script para ejecutar modelo_todos.py en MODO ESPECÍFICO
# Usa SOLO modelos específicos (entrena si es necesario)

echo "=================================================="
echo "MODO ESPECÍFICO - Solo Modelos Específicos"
echo "=================================================="
echo ""

cd "d:/Estudios/Universidad Nacional de Ingeniería/8. Octavo Ciclo/Ingeniería de Software (CIB02)/Proyecto/modelo_predictor_demanda"

env/Scripts/python.exe -m src.modelo_todos \
    --data data/matriculas_por_curso.csv \
    --config configs/general_model.yml \
    --model_type specific

echo ""
echo "✓ Ejecución completada. Revisa results/ para ver las predicciones."
