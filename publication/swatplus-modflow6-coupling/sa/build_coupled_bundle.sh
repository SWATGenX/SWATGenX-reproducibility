#!/usr/bin/env bash
# Build the coupled SWAT+ <-> MODFLOW 6 Morris-SA bundle for an EC2 box.
# Ships: slim SWAT+ PFAS surface model + swatplus_pfas, the ifx/netCDF runtime libs,
# the calibrated MODFLOW 6 flow model inputs, the mf6 binary, the precomputed static
# GW georeferencing, and the Morris driver.
#   Layout after `tar -xzf bundle -C /home/ubuntu`:
#     coupled_sa/sw_model/   (TxtInOut + swatplus_pfas)
#     coupled_sa/libs/       (ifx/netCDF runtime .so)
#     coupled_sa/gw_model/   (MODFLOW_sfr_cal inputs)
#     coupled_sa/bin/mf6
#     coupled_sa/static_gw.npz
#     coupled_sa/coupled_morris.py
set -uo pipefail
CODES="${CODES:-/data/SWATGenXApp/codes}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SW_RUN="${SW_RUN:-$CODES/_temp/pfas-swatplus-port/run_rogue}"
LIBDIR="${LIBDIR:-$CODES/lib/netcdf-ifx}"
GW_CAL="${GW_CAL:-${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500/MODFLOW_sfr_cal}"
MF6="${MF6:-$CODES/bin/mf6}"
OUT="${1:-/tmp/coupled-sa-bundle.tar.gz}"

[ -x "$SW_RUN/swatplus_pfas" ] || { echo "[build] ERROR: $SW_RUN/swatplus_pfas missing" >&2; exit 1; }
[ -x "$MF6" ] || { echo "[build] ERROR: $MF6 missing" >&2; exit 1; }
[ -f "$HERE/static_gw.npz" ] || { echo "[build] ERROR: static_gw.npz missing (run precompute_static.py)" >&2; exit 1; }

STAGE="$(mktemp -d /tmp/coupled-sa-stage.XXXXXX)"; trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/coupled_sa/sw_model" "$STAGE/coupled_sa/libs" "$STAGE/coupled_sa/gw_model" "$STAGE/coupled_sa/bin"

echo "[build] staging SWAT+ PFAS surface model (inputs only) ..."
rsync -a \
  --exclude='fort.*' --exclude='*.nc' --exclude='*.out' \
  --exclude='channel_pfas_day.txt' --exclude='*_aa.txt' --exclude='*_aa_*.txt' \
  --exclude='success.fin' --exclude='*.fin' \
  --exclude='swatplus_pfas_xval' --exclude='swatplus_pfas_xval.*' \
  "$SW_RUN"/ "$STAGE/coupled_sa/sw_model"/
cp -p "$SW_RUN/swatplus_pfas" "$STAGE/coupled_sa/sw_model/swatplus_pfas"; chmod +x "$STAGE/coupled_sa/sw_model/swatplus_pfas"

echo "[build] staging ifx/netCDF runtime libs ..."
for L in libimf.so libifcoremt.so.5 libifport.so.5 libintlc.so.5 libsvml.so \
         libnetcdff.so libnetcdff.so.7 libnetcdff.so.7.1.0 libiomp5.so; do
  [ -e "$LIBDIR/$L" ] && cp -P "$LIBDIR/$L" "$STAGE/coupled_sa/libs/" || true
done

echo "[build] staging calibrated MODFLOW 6 flow model (inputs only) ..."
rsync -a \
  --exclude='*.cbc' --exclude='*.hds' --exclude='*.ucn' --exclude='*.lst' \
  --exclude='*.stage' --exclude='*.sft.*' \
  "$GW_CAL"/ "$STAGE/coupled_sa/gw_model"/

echo "[build] staging mf6 + static + driver ..."
cp -p "$MF6" "$STAGE/coupled_sa/bin/mf6"; chmod +x "$STAGE/coupled_sa/bin/mf6"
cp -p "$HERE/static_gw.npz" "$STAGE/coupled_sa/static_gw.npz"
cp -p "$HERE/coupled_morris.py" "$STAGE/coupled_sa/coupled_morris.py"

echo "[build] taring -> $OUT ..."
tar -czf "$OUT" -C "$STAGE" coupled_sa
echo "[build] done: $(du -h "$OUT" | cut -f1)  $OUT"
