#!/usr/bin/env bash
# Assemble a self-contained Overleaf bundle (flat layout) from the monorepo manuscript,
# then zip it. Overleaf needs a flat project, so two path rewrites are applied:
#   main.tex / supplement.tex : \bibliography{../bib/references} -> \bibliography{references}
#   sections/*.tex            : \input{../tables/generated/...}  -> \input{tables/...}
# Figures stay as final/... (resolved from the main doc's dir, identical in the bundle).
# Run from repo root or publication/manuscript/. Produces overleaf/ and overleaf.zip.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
MS="${ROOT}/publication/manuscript"
OUT="${MS}/overleaf"
cd "$MS"

rm -rf "$OUT"
mkdir -p "$OUT/sections" "$OUT/final" "$OUT/tables"

# preamble verbatim
cp preamble-common.tex "$OUT/preamble-common.tex"

# main + supplement: flatten the bib path only
for f in main.tex supplement.tex; do
  sed -E 's#\\bibliography\{\.\./bib/references\}#\\bibliography{references}#' "$f" > "$OUT/$f"
done

# sections: flatten the generated-tables input path
for f in sections/*.tex; do
  sed -E 's#\\input\{\.\./tables/generated/#\\input{tables/#g' "$f" > "$OUT/sections/$(basename "$f")"
done

# bib (full), figures, generated tables
cp "${ROOT}/publication/bib/references.bib" "$OUT/references.bib"
cp final/*.png final/*.pdf "$OUT/final/" 2>/dev/null || true
cp "${ROOT}/publication/tables/generated/"*.tex "$OUT/tables/" 2>/dev/null || true

# fresh aux files so the supplement's cross-refs to the main text resolve on first compile
cp main.aux supplement.aux "$OUT/" 2>/dev/null || true

cat > "$OUT/README-overleaf.md" <<'EOF'
# Overleaf upload

1. Overleaf -> New Project -> **Upload Project** -> drop this ZIP.
2. Menu -> **Main document = main.tex**; **Compiler = pdfLaTeX**.
3. Compile. The supplement is a separate document: open `supplement.tex` and compile it
   once if you change it (its cross-references to the main text use the shipped
   `supplement.aux` until then).

Self-contained: figures in `final/`, generated tables in `tables/`, bib `references.bib`.
Regenerate this bundle from the monorepo with `publication/manuscript/build_overleaf_bundle.sh`.
EOF

# zip (deterministic-ish, exclude OS cruft)
rm -f "${MS}/overleaf.zip"
( cd "$OUT" && zip -qr "${MS}/overleaf.zip" . -x '*.DS_Store' )
echo "Wrote ${OUT}/ and ${MS}/overleaf.zip ($(du -h "${MS}/overleaf.zip" | cut -f1))"
echo "  sections: $(ls "$OUT/sections" | wc -l) | figures: $(ls "$OUT/final" | wc -l) | tables: $(ls "$OUT/tables" | wc -l)"
