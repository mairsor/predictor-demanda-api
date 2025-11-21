#!/bin/bash
# Script para ejecutar modelo_todos.py en MODO AUTOMÁTICO
# Usa estrategia inteligente: específico cached > específico nuevo > general

echo "=================================================="
echo "MODO AUTOMÁTICO - Estrategia Inteligente"
echo "=================================================="
echo ""

cd "d:/Estudios/Universidad Nacional de Ingeniería/8. Octavo Ciclo/Ingeniería de Software (CIB02)/Proyecto/modelo_predictor_demanda"

env/Scripts/python.exe -m src.modelo_todos \
    --data data/matriculas_por_curso.csv \
    --config configs/general_model.yml \
    --model_type auto

echo ""
echo "✓ Ejecución completada. Revisa results/ para ver las predicciones."
