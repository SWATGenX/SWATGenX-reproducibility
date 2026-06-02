#!/usr/bin/env bash
# Regenerate all committed LaTeX table fragments from source CSV/JSON, then build PDFs.
# Layer B + A (see REPRODUCIBILITY.md). Emitters that need the model workspaces
# (layer C) are the export_*/render_* scripts, not run here.
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SCRIPTS="${ROOT}/publication/analysis/scripts"

echo "== Regenerating LaTeX table fragments =="
fail=0
for f in "${SCRIPTS}"/emit_tab_*.py; do
  name="$(basename "$f")"
  if python3 "$f" >/dev/null 2>&1; then
    echo "  ok    ${name}"
  else
    echo "  FAIL  ${name}"
    fail=$((fail + 1))
  fi
done

echo "== Building PDFs =="
bash "${ROOT}/publication/manuscript/build_pdfs.sh"

if [ "${fail}" -gt 0 ]; then
  echo "WARNING: ${fail} emitter(s) failed — likely need layer-C model workspaces (set SWATGENX_USER_PATH)."
fi
echo "Done."
