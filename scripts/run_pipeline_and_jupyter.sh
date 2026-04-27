#!/usr/bin/env bash
set -euo pipefail

ORG_NAME="${ORG_NAME:-FlowiseAI}"
REPO_LIMIT="${REPO_LIMIT:-5}"
SKIP_IF_RESULTS_EXIST="${SKIP_IF_RESULTS_EXIST:-1}"

RESULTS_DIR="/app/data/results"
MARKER_FILE="${RESULTS_DIR}/.pipeline_completed"

echo "[entrypoint] Starting pipeline for org='${ORG_NAME}', limit='${REPO_LIMIT}'"

mkdir -p /app/data

if [[ "${SKIP_IF_RESULTS_EXIST}" == "1" && -f "${MARKER_FILE}" ]]; then
  echo "[entrypoint] Existing pipeline marker found. Skipping pipeline execution."
else
  echo "[entrypoint] Discovering repositories..."
  python /app/scripts/discover_repos.py "${ORG_NAME}" --limit "${REPO_LIMIT}"

  echo "[entrypoint] Adding/updating submodules..."
  python /app/scripts/add_submodules.py

  echo "[entrypoint] Running security analysis (SBOM/SCA/SAST)..."
  python /app/scripts/generate_all.py

  mkdir -p "${RESULTS_DIR}"
  date -u +"%Y-%m-%dT%H:%M:%SZ" > "${MARKER_FILE}"
  echo "[entrypoint] Pipeline finished successfully. Marker written to ${MARKER_FILE}."
fi

echo "[entrypoint] Launching Jupyter Notebook on port 8888..."
exec jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root /app/nbs/analysis.ipynb
