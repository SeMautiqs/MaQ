#!/bin/sh
# Runs the whole evaluation of the paper natively (without Docker), including
# the comparisons with QRAT and AutoQ 2.0, and collects the results and the
# description of the machine in a folder. Used to obtain the numbers reported
# in the paper.
#
# Requirements: Maude 3.5.1 (maude in the PATH and MAUDE_LIB pointing to its
# folder), Python 3 with qdk 1.34.0, git, and the QRAT binary. AutoQ is
# downloaded and built by the script, which needs cmake, Boost, and the ANTLR4
# C++ runtime (on macOS: brew install cmake boost antlr4-cpp-runtime); set
# AUTOQ to the path of an AutoQ binary to skip the build.
# Usage: artifact/evaluate-native.sh QRAT_BINARY [output_dir]
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
QRAT="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT="$(mkdir -p "${2:-$ROOT/results}" && cd "${2:-$ROOT/results}" && pwd)"
WORK="$OUT/deps"
QSHARP_COMMIT=0e58afc2fbb3fb8db806412b045acc0c675f8ce3
AUTOQ_COMMIT=7eed39a

command -v maude >/dev/null || { echo "maude is not in the PATH"; exit 1; }
[ -n "$MAUDE_LIB" ] || { echo "MAUDE_LIB is not set"; exit 1; }
python3 -c "import qdk" 2>/dev/null || { echo "the Python package qdk is not installed"; exit 1; }
[ -n "$1" ] && [ -f "$QRAT" ] && [ -x "$QRAT" ] || { echo "QRAT binary not found: $1"; exit 1; }
export QSHARP_PYTHON_TELEMETRY=none

echo "== downloading the Q# samples and Katas and the QRAT examples"
mkdir -p "$WORK"
if [ ! -d "$WORK/qsharp" ]; then
  git init -q "$WORK/qsharp"
  (cd "$WORK/qsharp" && git remote add origin https://github.com/microsoft/qsharp.git \
     && git fetch -q --depth 1 origin $QSHARP_COMMIT && git checkout -q FETCH_HEAD)
fi
[ -d "$WORK/qrat" ] || git clone -q --depth 1 https://github.com/canhminhdo/qrat.git "$WORK/qrat"
if [ ! -d "$WORK/AutoQ" ]; then
  git clone -q https://github.com/fmlab-iis/AutoQ.git "$WORK/AutoQ"
  (cd "$WORK/AutoQ" && git checkout -q $AUTOQ_COMMIT)
fi
if [ -z "$AUTOQ" ]; then
  echo "== building AutoQ"
  (cd "$WORK/AutoQ" && make release > "$OUT/autoq-build.txt" 2>&1) \
    && AUTOQ="$WORK/AutoQ/build/cli/autoq" \
    || echo "AutoQ could not be built (see $OUT/autoq-build.txt); its comparison is skipped"
fi

echo "== machine"
{
  date
  uname -a
  if [ "$(uname)" = Darwin ]; then
    sw_vers; sysctl -n machdep.cpu.brand_string; sysctl -n hw.ncpu
    echo "RAM: $(( $(sysctl -n hw.memsize) / 1073741824 )) GB"
  else
    grep -m1 "model name" /proc/cpuinfo; nproc; grep MemTotal /proc/meminfo
  fi
  echo "Maude $(maude --version 2>&1 | head -1)"
  python3 -c "import sys, importlib.metadata as m; print('Python', sys.version.split()[0], 'qdk', m.version('qdk'))"
  (cd "$ROOT" && git rev-parse HEAD 2>/dev/null) || echo "MaQ# snapshot without git history"
} | tee "$OUT/machine.txt"

echo "== Evaluation"
QSHARP_REPO="$WORK/qsharp" "$ROOT/artifact/reproduce.sh" 2>&1 | tee "$OUT/reproduce.txt"
cp "$ROOT/maqsharp/perf/results.md" "$OUT/perf-results.md" || echo "no performance results"

echo "== comparison with QRAT"
(cd "$ROOT/maqsharp" && python3 perf/compare_qrat.py "$QRAT" "$WORK/qrat/artifact" 120 5 10 15 20) \
  2>&1 | tee "$OUT/qrat.txt"
cp "$ROOT/maqsharp/perf/qrat-results.md" "$OUT/qrat-results.md" || echo "no QRAT results"

if [ -n "$AUTOQ" ] && [ -x "$AUTOQ" ]; then
  echo "== comparison with AutoQ 2.0"
  (cd "$ROOT/maqsharp" && python3 perf/compare_autoq.py "$AUTOQ" "$WORK/AutoQ/benchmarks/TACAS25/RUS" 5) \
    2>&1 | tee "$OUT/autoq.txt"
  cp "$ROOT/maqsharp/perf/autoq-results.md" "$OUT/autoq-results.md" || echo "no AutoQ results"
fi

echo
echo "Done. Send the folder $OUT (without deps/)."
