"""Rebuild the Rogue GWF+GWT (flow + PFAS transport) MF6 model with DAILY flow
stress periods for the daily coupler (M4a).  GWF and GWT share TDIS, so this
gives daily flow + daily transport; the flow-daily/transport-monthly split is a
later optimization (FMI-based).  Recharge & PFAS source are placeholders here --
the SWAT+ coupler overwrites recharge (and, in M4b, the PFAS source) via BMI.

Usage: python build_daily_gwt.py <src_ws> <nper_days> <out_ws>
"""
import sys
import flopy

src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/rogue_pfas_PFOS"
nper = int(sys.argv[2]) if len(sys.argv) > 2 else 365
out_ws = sys.argv[3] if len(sys.argv) > 3 else "/tmp/mf6_daily_gwt"

print(f"loading GWF+GWT sim from {src}")
sim = flopy.mf6.MFSimulation.load(sim_ws=src, verbosity_level=0)

# --- TDIS: daily ---
sim.tdis.nper = nper
sim.tdis.perioddata = [(1.0, 1, 1.0)] * nper
print(f"TDIS -> {nper} daily stress periods")

# --- GWF storage transient (SP0 steady) ---
gwf = sim.get_model([m for m in sim.model_names if "sfr" in m.lower() or "gwf" in
                     str(sim.get_model(m).model_type).lower()][0]) \
    if False else None
for mname in sim.model_names:
    m = sim.get_model(mname)
    sto = m.get_package("sto")
    if sto is not None:
        sto.steady_state = {0: True}
        sto.transient = {1: True}
        print(f"  {mname}: STO -> SP0 steady, SP1+ transient")
    # leave OC unchanged: GWT OC has no BUDGET FILEOUT, so adding SAVE BUDGET
    # would error.  Original output control is fine.

sim.set_sim_path(out_ws)
sim.write_simulation()
print(f"wrote daily GWF+GWT model -> {out_ws}")
print("models:", list(sim.model_names))
