#!/bin/sh
# Smoke test of the MaQ# artifact (about 1 minute).
# Runs the object-level tests and a session of the interactive tool, and compares
# the relevant lines of the output with artifact/smoke-expected.txt.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/../maqsharp"

echo "== object-level tests"
./tests/run-all.sh > /tmp/maq-tests.txt 2>&1
if grep -qiE "warning|error" /tmp/maq-tests.txt; then
  echo "FAILED: warnings or errors in tests/run-all.sh (see /tmp/maq-tests.txt)"; exit 1
fi
echo "   ok"

echo "== interactive tool session (tests/tool-session.txt)"
./tests/run-tool.sh 2>&1 \
  | grep -E "^ *(result:|holds|does NOT hold|path:|cycle:|reachable|unexplored|in stuck)|^Error|Operations:" \
  > /tmp/maq-session.txt
if diff -u "$HERE/smoke-expected.txt" /tmp/maq-session.txt; then
  echo "   ok"
  echo "SMOKE TEST PASSED"
else
  echo "FAILED: the output differs from artifact/smoke-expected.txt (diff above)"; exit 1
fi
