#!/usr/bin/env python3
"""Validate MODGenX/mf6_builder against the real Rogue arrays: load the deployed NWT
model, feed its top/botm/K/ibound/recharge/RIV/DRN/WEL into build_mf6_model, confirm
convergence + clean mass balance. Proves the convergence-by-construction fix before
wiring it into MODGenXCore."""
import sys, warnings, flopy; warnings.filterwarnings("ignore")
sys.path.insert(0, "/data/SWATGenXApp/codes/MODGenX")
from mf6_builder import build_mf6_model

D = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500/MODFLOW_250m"
BIN = "/data/SWATGenXApp/codes/_temp/swatplus-mf6-spike/bin/mf6"
m = flopy.modflow.Modflow.load("MODFLOW_250m.nam", model_ws=D, version="mfnwt",
                               check=False, forgive=True, verbose=False)
d, bas, upw = m.dis, m.bas6, m.get_package("UPW")
ok, rep = build_mf6_model(
    model_ws="/data/SWATGenXApp/codes/_temp/swatplus-mf6-spike/rogue_builder_test",
    name="rogue", exe_path=BIN,
    top=d.top.array, botm=d.botm.array, k_horiz=upw.hk.array, k_vert=upw.vka.array,
    ibound=bas.ibound.array, recharge=m.rch.rech.array, delr=d.delr.array, delc=d.delc.array,
    riv_rec=m.riv.stress_period_data[0], drn_rec=m.drn.stress_period_data[0],
    wel_rec=m.wel.stress_period_data[0], run=True)
print("converged:", ok, "| mass-balance %:", rep.get("mass_balance_discrepancy_pct"),
      "| repairs:", rep.get("repairs"))
assert ok and abs(rep.get("mass_balance_discrepancy_pct") or 9) < 1.0, "FAILED"
print("PASS: convergence-by-construction validated on the Rogue")
