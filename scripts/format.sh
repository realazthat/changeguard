#!/bin/bash
# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -e -x -v -u -o pipefail

SCRIPT_DIR=$(realpath "$(dirname "${BASH_SOURCE[0]}")")
source "${SCRIPT_DIR}/utilities/common.sh"

VENV_PATH="${PWD}/.cache/scripts/.venv" source "${PROJ_PATH}/scripts/utilities/ensure-venv.sh"
TOML=${PROJ_PATH}/pyproject.toml EXTRA=dev \
  DEV_VENV_PATH="${PWD}/.cache/scripts/.venv" \
  TARGET_VENV_PATH="${PWD}/.cache/scripts/.venv" \
  bash "${PROJ_PATH}/scripts/utilities/ensure-reqs.sh"

# find all *.md.jinja2 paths in changeguard
find ./changeguard -type f -name "*.md.jinja2" -print0 | while IFS= read -r -d '' MARKDOWN_TEMPLATE; do
  MARKDOWN_TEMPLATE=$(realpath "${MARKDOWN_TEMPLATE}")
  python -m mdreftidy.cli "${MARKDOWN_TEMPLATE}" \
    --renumber --remove-unused --move-to-bottom --sort-ref-blocks --inplace
  bash scripts/utilities/prettier.sh --parser markdown "${MARKDOWN_TEMPLATE}" --write
done

python -m mdreftidy.cli "${PWD}/README.md.jinja2" \
  --renumber --remove-unused --move-to-bottom --sort-ref-blocks --inplace
bash scripts/utilities/prettier.sh --parser markdown "${PWD}/README.md.jinja2" --write
bash scripts/utilities/prettier.sh --parser markdown "${PWD}/LICENSE.md" --write

python -m yapf -r ./changeguard -i
python -m yapf -r ./scripts -i
if toml-sort "${PROJ_PATH}/pyproject.toml" --check; then
  :
else
  toml-sort --in-place "${PROJ_PATH}/pyproject.toml"
fi
autoflake --remove-all-unused-imports --in-place --recursive ./changeguard
python -m isort ./changeguard

# vulture ./changeguard
