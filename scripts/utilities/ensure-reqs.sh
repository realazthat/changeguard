#!/bin/bash
# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -e -x -v -u -o pipefail

SCRIPT_DIR=$(realpath "$(dirname "${BASH_SOURCE[0]}")")
source "${SCRIPT_DIR}/common.sh"
[[ $0 == "${BASH_SOURCE[0]}" ]] && EXIT="exit" || EXIT="return"

TOML=${TOML:-""}
EXTRA=${EXTRA:-""}

if [[ -z "${TOML}" ]]; then
  echo -e "${RED}TOML is not set${NC}"
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
  ${EXIT} 1
fi

function is_dirty() {
  SYNC_TOUCH_TIME=$(stat -c '%y' "${SYNC_TOUCH_FILE}")
  TOML_TIME=$(stat -c '%y' "${TOML}")
  echo "SYNC_TOUCH_TIME: ${SYNC_TOUCH_TIME}"
  echo "TOML_TIME:       ${TOML_TIME}"
  if [[ ! -f "${SYNC_TOUCH_FILE}" ]]; then
    return 0
  fi
  if [[ "${SYNC_TOUCH_FILE}" -nt "${TOML}" ]]; then
    return 1
  else
    return 0
  fi
}

# trunk-ignore(shellcheck/SC2310)
if ! is_dirty; then
  echo -e "${GREEN}Syncing is not needed${NC}"
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
touch "${SYNC_TOUCH_FILE}"

# trunk-ignore(shellcheck/SC2310)
if is_dirty; then
  echo -e "${RED}Syncing failed${NC}"
  ${EXIT} 1
fi

echo -e "${GREEN}Synced requirements${NC}"
