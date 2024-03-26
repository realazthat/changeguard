#!/bin/bash
# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -e -x -v -u -o pipefail

SCRIPT_DIR=$(realpath "$(dirname "${BASH_SOURCE[0]}")")
source "${SCRIPT_DIR}/common.sh"

TOML=${TOML:-""}
EXTRA=${EXTRA:-""}

if [[ -z "${TOML}" ]]; then
  echo -e "${RED}TOML is not set${NC}"
  [[ $(realpath "$0"||true) == $(realpath "${BASH_SOURCE[0]}"||true) ]] && EXIT="exit" || EXIT="return"
  ${EXIT} 1
fi


if [[ "${EXTRA}" == "dev" ]]; then
  OUTPUT_REQUIREMENTS_FILE="${PWD}/.cache/scripts/dev-requirements.txt"
  SYNC_TOUCH_FILE="${PWD}/.cache/scripts/dev-pip-sync-touched"
elif [[ "${EXTRA}" == "prod" ]]; then
  OUTPUT_REQUIREMENTS_FILE="${PWD}/.cache/scripts/prod-requirements.txt"
  SYNC_TOUCH_FILE="${PWD}/.cache/scripts/prod-pip-sync-touched"
else
  echo -e "${RED}EXTRA should be either dev or prod${NC}"
  [[ $(realpath "$0"||true) == $(realpath "${BASH_SOURCE[0]}"||true) ]] && EXIT="exit" || EXIT="return"
  ${EXIT} 1
fi

export FILE="${PROJ_PATH}/pyproject.toml"
export TOUCH_FILE=".cache/scripts/${EXTRA}-requirements.touch"
if bash "${PROJ_PATH}/scripts/utilities/is_not_dirty.sh"; then
  echo -e "${GREEN}Syncing is not needed${NC}"
  [[ $(realpath "$0"||true) == $(realpath "${BASH_SOURCE[0]}"||true) ]] && EXIT="exit" || EXIT="return"
  ${EXIT} 0
fi
echo -e "${BLUE}Syncing requirements${NC}"

python -m pip install pip-tools

mkdir -p "$(dirname "${OUTPUT_REQUIREMENTS_FILE}")"
python -m piptools compile \
    --extra "${EXTRA}" \
    -o "${OUTPUT_REQUIREMENTS_FILE}" \
    "${TOML}"

pip-sync "${OUTPUT_REQUIREMENTS_FILE}"
export FILE="${PROJ_PATH}/pyproject.toml"
export TOUCH_FILE=".cache/scripts/${EXTRA}-requirements.touch"
bash "${PROJ_PATH}/scripts/utilities/mark_dirty.sh"

export FILE="${PROJ_PATH}/pyproject.toml"
export TOUCH_FILE=".cache/scripts/${EXTRA}-requirements.touch"
if bash "${PROJ_PATH}/scripts/utilities/is_not_dirty.sh"; then
  :
else
  echo -e "${RED}Syncing failed${NC}"
  [[ $(realpath "$0"||true) == $(realpath "${BASH_SOURCE[0]}"||true) ]] && EXIT="exit" || EXIT="return"
  ${EXIT} 1
fi

echo -e "${GREEN}Synced requirements${NC}"
