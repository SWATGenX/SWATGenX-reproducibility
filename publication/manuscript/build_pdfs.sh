#!/usr/bin/env bash
# Build main manuscript PDF and standalone supplementary PDF.
# Run from repository root or publication/manuscript/.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
MS="${ROOT}/publication/manuscript"
cd "$MS"

build_main() {
  pdflatex -interaction=nonstopmode main.tex >/dev/null
  bibtex main >/dev/null 2>&1 || true
  pdflatex -interaction=nonstopmode main.tex >/dev/null
  pdflatex -interaction=nonstopmode main.tex >/dev/null
}

build_supplement() {
  pdflatex -interaction=nonstopmode supplement.tex >/dev/null
  bibtex supplement >/dev/null 2>&1 || true
  pdflatex -interaction=nonstopmode supplement.tex >/dev/null
  pdflatex -interaction=nonstopmode supplement.tex >/dev/null
}

echo "Building main.pdf ..."
build_main
echo "Building supplement.pdf (requires main.aux for cross-refs) ..."
build_supplement
echo "Refreshing cross-document references ..."
pdflatex -interaction=nonstopmode main.tex >/dev/null
pdflatex -interaction=nonstopmode supplement.tex >/dev/null

echo "Done: ${MS}/main.pdf and ${MS}/supplement.pdf"
