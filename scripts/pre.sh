#!/bin/bash
# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -e -x -v -u -o pipefail

SCRIPT_DIR=$(realpath "$(dirname "${BASH_SOURCE[0]}")")
source "${SCRIPT_DIR}/utilities/common.sh"


# Check that no changes occurred to files through the workflow.
STEP=pre bash scripts/changeguard.sh

EXTRA=dev bash scripts/pin-extra-reqs.sh
EXTRA=prod bash scripts/pin-extra-reqs.sh
bash scripts/run-all-examples.sh
bash scripts/run-all-tests.sh
bash scripts/format.sh
bash scripts/type-check.sh
bash scripts/generate-readme.sh
bash scripts/run-wheel-smoke-test.sh
bash scripts/run-edit-mode-smoke-test.sh
if [[ -z "${GITHUB_ACTIONS:-}" ]]; then
  bash scripts/act.sh
  bash scripts/precommit.sh
fi

# If running in GitHub Actions, check that no changes occurred to files through
# the workflow. If changes occurred, they should be staged and pre.sh should be
# run again.
STEP=post bash scripts/changeguard.sh

echo -e "${GREEN}Success: pre.sh${NC}"
