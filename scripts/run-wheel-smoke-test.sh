#!/bin/bash
# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -e -x -v -u -o pipefail

SCRIPT_DIR=$(realpath "$(dirname "${BASH_SOURCE[0]}")")
source "${SCRIPT_DIR}/utilities/common.sh"


TMP_PROJ_PATH=$(mktemp -d)
TMP_DIR=$(mktemp -d)
function cleanup {
  rm -Rf "${TMP_DIR}" || true
  rm -Rf "${TMP_PROJ_PATH}" || true
}
trap cleanup EXIT

################################################################################
VENV_PATH="${PWD}/.cache/scripts/.venv" \
  source "${PROJ_PATH}/scripts/utilities/ensure-venv.sh"
################################################################################
# Build wheel
cd "${TMP_PROJ_PATH}"


# Copy everything including hidden files, but ignore errors.
cp -a "${PROJ_PATH}/." "${TMP_PROJ_PATH}" || true

# Make everything writable, because `python -m build` copies everything and then
# deletes it, which is a problem if something is read only.
#
# Skips the dot files.
find "${TMP_PROJ_PATH}" -type f -not -path '*/.*' -exec chmod 777 {} +


DIST="${TMP_PROJ_PATH}/dist"
# TODO: Pin/minimum rust version, because some versions of rust fail to build
# the wheel. Pydantic has some rust parts.
python -m build --outdir "${DIST}" "${TMP_PROJ_PATH}"
################################################################################
# Install changeguard and run smoke test
cd "${TMP_DIR}"
pip install virtualenv
python -m virtualenv .venv
cp "${PROJ_PATH}/.python-version" .
VENV_PATH="${TMP_DIR}/.venv" source "${PROJ_PATH}/scripts/utilities/ensure-venv.sh"

EXIT_CODE=0
python -m changeguard.cli --help || EXIT_CODE=$?
if [[ "${EXIT_CODE}" -eq 0 ]]; then
  echo -e "${RED}Expected changeguard to to fail in a clean environment${NC}"
  exit 1
fi
echo -e "${GREEN}Success: changeguard failed in a clean environment${NC}"

pip install "${DIST}"/*.whl
echo -e "${GREEN}Success: changeguard installed successfully${NC}"

python -m changeguard.cli --help
python -m changeguard.cli --version
echo -e "${GREEN}Success: changeguard smoke test ran successfully${NC}"

echo -e "${GREEN}${BASH_SOURCE[0]}: Tests ran successfully${NC}"
################################################################################
