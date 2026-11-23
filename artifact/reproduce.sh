#!/bin/sh
# Full reproduction of the results in the paper.
#   validation (RQ1): under 1 minute
#   performance (Section 5, RQ4): about 1 hour with the default limit of 120 s per run
# Usage: artifact/reproduce.sh [shots] [time_limit_in_seconds] [max_n]
set -e
SHOTS=${1:-4000}
LIMIT=${2:-120}
NMAX=${3:-16}
cd "$(cd "$(dirname "$0")" && pwd)/../maqsharp"

echo "== RQ1: validation against the Q# simulator ($SHOTS shots per operation)"
python3 validation/validate.py "$SHOTS" | tee /tmp/maq-validation.txt

echo
echo "== RQ4: performance on GHZ(n) and Grover(n) (limit $LIMIT s, n <= $NMAX)"
python3 perf/run_perf.py "$LIMIT" "$NMAX"
echo
cat perf/results.md
