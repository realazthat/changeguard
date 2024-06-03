#!/bin/bash
# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -e -x -v -u -o pipefail

set +x +v

GRN='\033[0;32m'
NC='\033[0m'

mkdir -p ".deleteme"
EXIT_CODE=0
(unbuffer python -m changeguard.cli \
  test_list_paths \
  --directory . \
  --ignorefile .gitignore --ignoreline .git --ignoreline .trunk \
  2>&1 | tee ".deleteme/test-list-paths.log") || EXIT_CODE=$?



if [[ ${EXIT_CODE} -ne 0 ]]; then
  if grep -q "initial_iterdir_paths and git_paths do not match." ".deleteme/test-list-paths.log"; then
    echo -e "$(cat <<EOF
${GRN}
test_list_paths ran successfully but returned a non-zero status, probably
because there are some files that are not staged, but that's OK.
${NC}
EOF
)"
  else
    exit "${EXIT_CODE}"
  fi
fi

echo -e "${GRN}Example test_list_paths ran successfully${NC}"
