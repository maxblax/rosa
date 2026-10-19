#!/usr/bin/env bash
# Lance toute la suite Playwright de non-régression.
# Cible par défaut : serveur local sur 5678. Pour une autre instance :
#   ROSA_BASE_URL=https://... ROSA_USER=... ROSA_PASSWORD=... tests_playwright/run_all.sh
cd "$(dirname "$0")/.." || exit 1
PY=${PYTHON:-./.venv/bin/python}
fail=0
for t in tests_playwright/test_*.py; do
  if "$PY" "$t" > /dev/null 2>&1; then echo "PASS $t"; else echo "FAIL $t"; fail=1; fi
done
exit $fail
