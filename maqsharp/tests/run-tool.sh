#!/bin/sh
# Sesión de ejemplo de la herramienta interactiva (requiere el binario maude)
cd "$(dirname "$0")/.."
maude -no-banner -no-advise -allow-files examples/symbolic.maude qsharp-io.maude < tests/tool-session.txt
