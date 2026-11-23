#!/bin/sh
# Sample session of the interactive tool (requires the maude binary)
cd "$(dirname "$0")/.."
maude -no-banner -no-advise -allow-files examples/symbolic.maude qsharp-io.maude < tests/tool-session.txt
