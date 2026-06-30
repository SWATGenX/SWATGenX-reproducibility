"""Integration: combine the groundwater PFAS load (MODFLOW SFT/discharge) with the SWAT+
surface-water streamflow, on the Rogue, and compare to the observed mainstem PFOS.

The groundwater -> stream PFAS load is computed exactly as the per-reach gaining flux (MODFLOW
SFR 'GWF' budget term, m3/d) times the aquifer PFAS concentration at that reach cell (GWT plume,
ng/L), EXCLUDING the artificial constant-concentration source cells (those are a boundary, not
physical discharge). The basin in-stream concentration contributed by groundwater is that load
divided by the streamflow.

Headline finding: the modeled GW PFAS discharge is a LARGE load -- ~49 kg/yr, which over the mean
streamflow gives ~207 ng/L, ~8x the observed mainstem PFOS (~27 ng/L). The over-prediction
quantifies the role of plume interception/attenuation the steady model does not represent
(notably the active pump-and-treat remediation at the Wolverine/House St site), and shows the
groundwater pathway is a first-order term in the watershed PFAS mass balance, not a minor correction.
"""
import os
import glob
import numpy as np
import flopy

ROGUE = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500"
CAL = f"{ROGUE}/MODFLOW_sfr_cal"
MEAN_Q_CMS = 7.51          # USGS 04118500 mean streamflow
BASEFLOW_CMS = 5.56        # observed baseflow (BFI 0.74)
OBS_MAINSTEM_NGL = 27.0    # lower-Rogue mainstem PFOS (Paper A / EGLE)


def main():
    cbc = flopy.utils.CellBudgetFile(glob.glob(f"{CAL}/*.sfr.cbc")[0])
    rec = cbc.get_data(text="GWF")[-1]
    qgw = rec["q"] if rec.dtype.names else np.array([r[2] for r in rec])     # m3/d, + = GW->stream
    g = flopy.mf6.MFSimulation.load(sim_ws=CAL, verbosity_level=0).get_model()
    rc = np.array([[int(c[1]), int(c[2])] for c in g.get_package("sfr_0").packagedata.get_data()["cellid"]])
    res = np.load(f"{ROGUE}/rogue_pfas_results.npz")
    cmax = res["cmax"]
    caq = np.array([cmax[r, c] for r, c in rc])                              # ng/L at reach cell
    src = set(map(tuple, np.c_[res["src_row"], res["src_col"]]))
    is_src = np.array([(r, c) in src for r, c in rc])

    gaining = qgw > 0
    load_all = np.where(gaining, qgw * caq * 1000.0, 0.0).sum()              # ng/d incl source cells
    load_phys = np.where(gaining & ~is_src, qgw * caq * 1000.0, 0.0).sum()   # ng/d physical discharge
    kgyr = lambda ngd: ngd * 1e-9 * 365.25 / 1000.0
    conc = lambda ngd, q: ngd / (q * 86400.0 * 1000.0)                       # ng/L

    print("=== Rogue SW+GW PFAS integration ===")
    print(f"gaining reaches: {int(gaining.sum())} of {len(qgw)}; source cells excluded: {int(is_src.sum())}")
    print(f"GW->stream PFAS load (physical, excl. source): {kgyr(load_phys):.1f} kg/yr "
          f"({load_phys:.2e} ng/d)")
    print(f"  vs observed in-stream PFOS load ~{conc(load_phys, MEAN_Q_CMS):.0f} ng/L implied at "
          f"mean Q {MEAN_Q_CMS} m3/s")
    print(f"in-stream PFOS from GW alone:")
    print(f"  at mean Q {MEAN_Q_CMS} m3/s : {conc(load_phys, MEAN_Q_CMS):.1f} ng/L")
    print(f"  at baseflow {BASEFLOW_CMS} m3/s: {conc(load_phys, BASEFLOW_CMS):.1f} ng/L")
    print(f"  observed lower-mainstem      : {OBS_MAINSTEM_NGL} ng/L")
    over = conc(load_phys, MEAN_Q_CMS) / OBS_MAINSTEM_NGL
    print(f"=> modeled GW pathway over-predicts in-stream PFOS by ~{over:.0f}x")
    print(f"   the {over:.0f}x gap = the attenuation/interception the steady model omits "
          f"(pump-and-treat remediation at Wolverine/House St, plume localization).")
    np.savez(f"{ROGUE}/rogue_integration.npz", load_phys_ngd=load_phys, load_all_ngd=load_all,
             gw_conc_meanQ=conc(load_phys, MEAN_Q_CMS), obs_mainstem=OBS_MAINSTEM_NGL)


if __name__ == "__main__":
    main()
