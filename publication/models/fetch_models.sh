#!/usr/bin/env bash
# Download the paper-1 evaluation SWAT+ model bundles (input-only) from the GitHub
# Release — server-independent, frozen to the versions reported in the manuscript.
# Usage: bash fetch_models.sh [DEST_DIR]   (default: ./models_download)
set -euo pipefail
DEST="${1:-$(dirname "$0")/models_download}"; mkdir -p "$DEST"
BASE="https://github.com/SWATGenX/SWATGenX-reproducibility/releases/download/models-v1.0"
FILES=(
  Oklawaha_S_030801020804.zip
  UpperSanPedro_M_09471300.zip
  Peace_L_94k_03100101.zip
  LittleKanawaha_X20_03152000.zip
  Verdigris_X40_07174000.zip
  UpperGila_X60_15060105.zip
  FloridaCal_02297600.zip
  IllinoisCal_05536265.zip
)
for f in "${FILES[@]}"; do
  echo "[fetch] $f"
  curl -fL --retry 3 -o "$DEST/$f" "$BASE/$f"
done
echo "[fetch] done -> $DEST  (unzip each to get SWAT_MODEL_Web_Application/)"
