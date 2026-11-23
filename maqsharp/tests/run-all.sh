#!/bin/sh
# Ejecuta todas las pruebas con las bindings de Python de Maude (pip install maude)
# o con el binario maude si está en el PATH.
cd "$(dirname "$0")"
for f in parse bell teleport calls ghz loops; do
  echo "######## $f"
  if command -v maude >/dev/null; then maude -no-banner -no-advise $f.maude < /dev/null
  else python3 ../run.py $f.maude; fi
done
