#!/bin/bash
# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -e -x -v -u -o pipefail

SCRIPT_DIR=$(realpath "$(dirname "${BASH_SOURCE[0]}")")
source "${SCRIPT_DIR}/utilities/common.sh"

VENV_PATH=".cache/scripts/.venv" source "${PROJ_PATH}/scripts/utilities/ensure-venv.sh"
TOML=${PROJ_PATH}/pyproject.toml EXTRA=dev source "${PROJ_PATH}/scripts/utilities/ensure-reqs.sh"



EXTRA=${EXTRA:-}

if [[ "${EXTRA}" == "dev" ]]; then
  :
elif [[ "${EXTRA}" == "prod" ]]; then
  :
else
  echo -e "${RED}EXTRA must be set to 'dev' or 'prod'${NC}"
  [[ $(realpath "$0"||true) == $(realpath "${BASH_SOURCE[0]}"||true) ]] && EXIT="exit" || EXIT="return"
  ${EXIT} 1
fi

PINNED_REQ_FILE="${PWD}/.cache/scripts/${EXTRA}-requirements.txt"

function is_dirty {
  if [[ ! -f "${PINNED_REQ_FILE}" ]]; then
    return 0
  fi
  if [[ "${PINNED_REQ_FILE}" -nt "${PROJ_PATH}/pyproject.toml" ]]; then
    return 1
  else
    return 0
  fi
}

# trunk-ignore(shellcheck/SC2310)
if is_dirty; then
  echo -e "${BLUE}Generating ${PINNED_REQ_FILE}${NC}"

  mkdir -p ".cache/scripts/"
  python -m piptools compile --generate-hashes \
    --extra "${EXTRA}" \
    "${PROJ_PATH}/pyproject.toml" \
    -o "${PINNED_REQ_FILE}"
  echo -e "${GREEN}Generated ${PINNED_REQ_FILE}${NC}"
else
  echo -e "${GREEN}Requirements ${PINNED_REQ_FILE} are up to date${NC}"
fi

# trunk-ignore(shellcheck/SC2310)
if is_dirty; then
  echo -e "${RED}pyproject.toml is dirty, pinning failed${NC}"
  [[ $(realpath "$0"||true) == $(realpath "${BASH_SOURCE[0]}"||true) ]] && EXIT="exit" || EXIT="return"
  ${EXIT} 1
fi


python scripts/pin-extra-reqs.py \
  --reqs "${PINNED_REQ_FILE}" \
  --extra "${EXTRA}" \
  --toml "${PROJ_PATH}/pyproject.toml"

if toml-sort "${PROJ_PATH}/pyproject.toml" --check; then
  echo -e "${GREEN}pyproject.toml needs no formatting${NC}"
else
  echo -e "${BLUE}pyproject.toml needs formatting${NC}"
  toml-sort --in-place "${PROJ_PATH}/pyproject.toml"
  echo -e "${GREEN}pyproject.toml formatted${NC}"
fi
if toml-sort "${PROJ_PATH}/pyproject.toml" --check; then
  echo -e "${GREEN}pyproject.toml is formatted${NC}"
else
  echo -e "${RED}pyproject.toml is not formatted${NC}"
  ${EXIT} 1
fi

echo -e "${GREEN}Pinned ${EXTRA} requirements${NC}"