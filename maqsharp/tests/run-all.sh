#!/bin/sh
# Runs all the tests with the Maude Python bindings (pip install maude)
# or with the maude binary if it is in the PATH.
cd "$(dirname "$0")"
for f in parse bell teleport calls ghz loops; do
  echo "######## $f"
  if command -v maude >/dev/null; then maude -no-banner -no-advise $f.maude < /dev/null
  else python3 ../run.py $f.maude; fi
done
