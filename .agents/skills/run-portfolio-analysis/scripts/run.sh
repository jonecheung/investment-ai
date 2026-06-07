#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
GUARDRAILS_SCRIPTS="$(cd "${SCRIPT_DIR}/../../evaluate-portfolio-guardrails/scripts" && pwd)"
VENV="${SKILL_DIR}/.venv"

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 is required but not found in PATH" >&2
  exit 1
fi

if [[ ! -x "${VENV}/bin/python" ]]; then
  echo "Creating skill-local venv at ${VENV}..." >&2
  python3 -m venv "${VENV}"
  "${VENV}/bin/pip" install -q -r "${SCRIPT_DIR}/requirements.txt"
fi

export PYTHONPATH="${GUARDRAILS_SCRIPTS}:${SCRIPT_DIR}:${PYTHONPATH:-}"
exec "${VENV}/bin/python" "${SCRIPT_DIR}/analyze.py" "$@"
