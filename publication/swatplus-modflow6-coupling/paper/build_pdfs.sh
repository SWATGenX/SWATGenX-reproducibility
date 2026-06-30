#!/usr/bin/env bash
# Build the PFAS manuscript + supplementary PDFs (pdflatex x3 + bibtex).
set -uo pipefail
cd "$(dirname "$0")"

# main (with bibliography)
pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1 || true
bibtex main >/dev/null 2>&1 || true
pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1 || true
pdflatex -interaction=nonstopmode main.tex > /tmp/pfas_tex.log 2>&1 || true

# supplementary (no bibliography; toc needs two passes)
pdflatex -interaction=nonstopmode supplementary.tex >/dev/null 2>&1 || true
pdflatex -interaction=nonstopmode supplementary.tex > /tmp/pfas_si.log 2>&1 || true

# user guide (how-to-run; toc needs two passes)
pdflatex -interaction=nonstopmode user_guide.tex >/dev/null 2>&1 || true
pdflatex -interaction=nonstopmode user_guide.tex > /tmp/pfas_guide.log 2>&1 || true

for f in main supplementary user_guide; do
  log=/tmp/pfas_tex.log
  [ "$f" = supplementary ] && log=/tmp/pfas_si.log
  [ "$f" = user_guide ] && log=/tmp/pfas_guide.log
  if [ -f "$f.pdf" ]; then echo "OK: $(pwd)/$f.pdf ($(du -h $f.pdf | cut -f1))";
  else echo "FAILED $f — tail of log:"; tail -25 "$log"; fi
done
