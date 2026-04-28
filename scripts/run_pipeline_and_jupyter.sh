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
  PIPELINE_OK=1

  echo "[entrypoint] Discovering repositories..."
  if ! python /app/scripts/discover_repos.py "${ORG_NAME}" --limit "${REPO_LIMIT}"; then
    echo "[entrypoint] Warning: discover_repos.py failed. Jupyter will still start."
    PIPELINE_OK=0
  fi

  echo "[entrypoint] Adding/updating submodules..."
  if ! python /app/scripts/add_submodules.py; then
    echo "[entrypoint] Warning: add_submodules.py failed. Jupyter will still start."
    PIPELINE_OK=0
  fi

  echo "[entrypoint] Running security analysis (SBOM/SCA/SAST)..."
  if ! python /app/scripts/generate_all.py; then
    echo "[entrypoint] Warning: generate_all.py failed. Jupyter will still start."
    PIPELINE_OK=0
  fi

  if [[ "${PIPELINE_OK}" == "1" ]]; then
    mkdir -p "${RESULTS_DIR}"
    date -u +"%Y-%m-%dT%H:%M:%SZ" > "${MARKER_FILE}"
    echo "[entrypoint] Pipeline finished successfully. Marker written to ${MARKER_FILE}."
  else
    echo "[entrypoint] Pipeline finished with warnings. Marker not written so the next run can retry."
  fi
fi

echo "[entrypoint] Launching Jupyter Notebook on port 8888..."
exec jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root /app/nbs/analysis.ipynb
