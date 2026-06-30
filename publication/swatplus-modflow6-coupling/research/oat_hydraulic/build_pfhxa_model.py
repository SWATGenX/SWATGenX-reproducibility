"""Build a daily GWF+GWT model for PFHxA -- the most mobile PFAS in the watershed
data (retardation R~1.6; carboxylate, weak soil + air-water sorption).  Used for
the one-at-a-time HYDRAULIC sensitivity of the coupled SWAT+/MODFLOW 6 model:
a mobile tracer that exchanges between groundwater and stream on a short timescale.

- MST sorption: distcoef set so R = 1 + rho_b*Kd/theta ~= 1.6 (PFHxA).
- Initial condition: uniform aquifer PFHxA (50 ng/L), so the groundwater->stream
  discharge is active from day one (the point Tannery plume is PFOS, not PFHxA).
Usage: python build_pfhxa_model.py <src_daily_gwt> <out_ws>
"""
import sys
import numpy as np
import flopy

src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/mf6_gwt90_src"
out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/mf6_pfhxa"

sim = flopy.mf6.MFSimulation.load(sim_ws=src, verbosity_level=0)
gwt = sim.get_model("pfas")

# --- PFHxA sorption (R ~ 1.6) ---
mst = gwt.get_package("mst")
por = float(np.nanmean(mst.porosity.array)); bd = float(np.nanmean(mst.bulk_density.array))
R = 1.6
Kd = (R - 1) * por / bd
mst.distcoef.set_data(Kd)
try:
    mst.sp2.set_data(0.90)          # Freundlich exponent for PFHxA
except Exception:
    pass
print(f"MST: PFHxA distcoef={Kd:.2e} (R~{R}), Freundlich n=0.90")

# --- uniform aquifer PFHxA initial condition ---
gwt.get_package("ic").strt.set_data(50.0)      # ng/L background everywhere
print("IC: uniform 50 ng/L PFHxA")

# --- drop the PFOS point plume (CNC); PFHxA is diffuse, not the Tannery source ---
try:
    gwt.remove_package("cnc")
    print("removed CNC (PFOS point plume)")
except Exception as e:
    print("CNC note:", e)

sim.set_sim_path(out)
sim.write_simulation()
print(f"wrote PFHxA daily GWF+GWT model -> {out}")
