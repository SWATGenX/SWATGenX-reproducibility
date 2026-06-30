"""Rebuild the calibrated Rogue MF6 flow model with DAILY stress periods for
SWAT+ <-> MODFLOW 6 daily coupling (M2).  Each day = one stress period =
one timestep; transient storage so the water table responds to daily recharge.
Recharge is a placeholder here -- the SWAT+ coupler overwrites RECHARGE via BMI
each day.  Usage: python build_daily_mf6.py <nper_days> <out_ws>
"""
import sys
import flopy

CAL = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500/MODFLOW_sfr_cal"
nper = int(sys.argv[1]) if len(sys.argv) > 1 else 365
out_ws = sys.argv[2] if len(sys.argv) > 2 else "/tmp/mf6_daily_build"

print(f"loading calibrated flow model from {CAL}")
sim = flopy.mf6.MFSimulation.load(sim_ws=CAL, verbosity_level=0)
gwf = sim.get_model()

# --- TDIS: nper daily periods, perlen=1 d, 1 step each ---
sim.tdis.nper = nper
sim.tdis.perioddata = [(1.0, 1, 1.0)] * nper
print(f"TDIS -> {nper} daily stress periods (perlen=1, nstp=1)")

# --- STO: period 0 steady (settle from calibrated heads), then transient ---
sto = gwf.get_package("sto")
sto.steady_state = {0: True}
sto.transient = {1: True}
print("STO -> SP0 steady-state, SP1+ transient")

# --- OC: keep output light (save head+budget last step of each period) ---
oc = gwf.get_package("oc")
try:
    oc.saverecord = {0: [("HEAD", "LAST"), ("BUDGET", "LAST")]}
except Exception as e:
    print("OC saverecord note:", e)

# --- IMS: ensure it converges fast for daily flow (keep complex but cap) ---
# (leave as calibrated; flow-only daily converges in few iterations)

sim.set_sim_path(out_ws)
sim.write_simulation()
print(f"wrote daily MF6 model -> {out_ws}")
print("packages:", [p for p in gwf.package_names])
