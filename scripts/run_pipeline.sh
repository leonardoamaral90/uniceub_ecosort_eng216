#!/usr/bin/env bash
set -euo pipefail

echo "[EcoSort] Aguardando Prefect em ${PREFECT_API_URL:-http://prefect-server:4200/api}..."
python /app/scripts/wait_for_tcp.py prefect-server 4200 120

echo "[EcoSort] Executando fluxo orquestrado..."
python -m ecosort.orchestration.flows

echo "[EcoSort] Pipeline finalizado."
