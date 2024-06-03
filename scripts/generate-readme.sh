#!/bin/bash
# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -e -x -v -u -o pipefail

SCRIPT_DIR=$(realpath "$(dirname "${BASH_SOURCE[0]}")")
source "${SCRIPT_DIR}/utilities/common.sh"

# NOTE: Use dev requirements to generate the README because the README uses
# shell() with some tools that we only want to install into dev environment.
VENV_PATH="${PWD}/.cache/scripts/.venv" source "${PROJ_PATH}/scripts/utilities/ensure-venv.sh"
TOML=${PROJ_PATH}/pyproject.toml EXTRA=dev \
  DEV_VENV_PATH="${PWD}/.cache/scripts/.venv" \
  TARGET_VENV_PATH="${PWD}/.cache/scripts/.venv" \
  bash "${PROJ_PATH}/scripts/utilities/ensure-reqs.sh"


# TODO: Change this in the next version of snipinator to use `--rm --force`.
chmod +w "${PROJ_PATH}/README.md" || true
rm -f "${PROJ_PATH}/README.md" || true
touch "${PROJ_PATH}/README.md"
python -m snipinator.cli \
  -t "${PROJ_PATH}/README.md.jinja2" \
  -o "${PROJ_PATH}/README.md" \
  --rm \
  --chmod-ro

LAST_VERSION=$(tomlq -r -e '.["tool"]["changeguard-project-metadata"]["last_stable_release"]' pyproject.toml)
python -m mdremotifier.cli \
  -i "${PROJ_PATH}/README.md" \
  --url-prefix "https://github.com/realazthat/changeguard/blob/v${LAST_VERSION}/" \
  --img-url-prefix "https://raw.githubusercontent.com/realazthat/changeguard/v${LAST_VERSION}/" \
  -o "${PROJ_PATH}/.github/README.remotified.md"
