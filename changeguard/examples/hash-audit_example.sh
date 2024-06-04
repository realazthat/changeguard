#!/bin/bash
# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -e -x -v -u -o pipefail

mkdir -p ".deleteme"

# SNIPPET_START
python -m changeguard.cli \
  hash \
  --ignorefile ".gitignore" \
  --ignoreline .trunk --ignoreline .git \
  --method auto \
  --tmp-backup-dir ".deleteme/audit-original" \
  --audit-file ".deleteme/check-changes-audit.yaml" \
  --directory "."

python -m changeguard.cli \
  audit \
  --audit-file ".deleteme/check-changes-audit.yaml" \
  --show-delta \
  --directory .
# SNIPPET_END
