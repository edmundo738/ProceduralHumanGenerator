#!/bin/sh
# Serve o site de preview commitado em site/ (sem venv, sem Blender).
cd "$(dirname "$0")/../.." || exit 1
exec python3 -m http.server "${1:-8080}" --bind 0.0.0.0 --directory site
