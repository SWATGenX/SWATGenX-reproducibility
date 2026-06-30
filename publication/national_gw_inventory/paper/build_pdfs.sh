#!/usr/bin/env bash
# Build main.pdf and supplement.pdf for the national groundwater inventory data descriptor.
set -euo pipefail
cd "$(dirname "$0")"

VENV=../../../.venv/bin/python
[ -x "$VENV" ] && "$VENV" make_figures.py >/dev/null 2>&1 || python3 make_figures.py >/dev/null 2>&1 || true

pass() { pdflatex -interaction=nonstopmode -halt-on-error "$1.tex" >/dev/null 2>&1 || \
         pdflatex -interaction=nonstopmode "$1.tex" >/tmp/${1}_latex.log 2>&1; }

echo "Building main.pdf ..."
pass main; bibtex main >/dev/null 2>&1 || true; pass main; pass main
echo "Building supplement.pdf ..."
pass supplement; bibtex supplement >/dev/null 2>&1 || true; pass supplement; pass supplement
echo "Cross-ref refresh ..."
pass main; pass supplement
echo "Done: $(pwd)/main.pdf and supplement.pdf"
