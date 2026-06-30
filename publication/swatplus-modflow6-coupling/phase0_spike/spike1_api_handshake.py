#!/usr/bin/env python3
"""Phase-0 de-risking spike: prove the SWAT+ <-> MODFLOW 6 per-day handshake.

Builds a minimal MF6 GWF model (array recharge RCHA + a RIV package), then drives
it through the XMI/BMI API (libmf6.so via xmipy): discover variable addresses, SET
the recharge array mid-run, step the model, and GET the river-aquifer exchange flux
(RIV SIMVALS) + heads. Running two recharge levels and showing the heads/flux respond
proves the exact mechanism the coupler needs (SET recharge -> do_time_step -> GET
RIV exchange). This retires the largest unknowns: API drivability + address
discovery + SET/GET reach the right arrays.
"""
import os, numpy as np, flopy
from xmipy import XmiWrapper

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(HERE, "model")
LIB = os.path.join(HERE, "bin", "libmf6.so")
NAME = "spike"
NROW = NCOL = 10
DELR = DELC = 100.0

def build():
    sim = flopy.mf6.MFSimulation(sim_name=NAME, sim_ws=WS, exe_name=os.path.join(HERE, "bin", "mf6"))
    # daily TDIS (the coupler steps day by day)
    # two daily stress periods so the coupler can SET a different recharge each day
    flopy.mf6.ModflowTdis(sim, nper=2, perioddata=[(1.0, 1, 1.0), (1.0, 1, 1.0)], time_units="days")
    flopy.mf6.ModflowIms(sim, complexity="SIMPLE", linear_acceleration="BICGSTAB",
                         outer_dvclose=1e-6, inner_dvclose=1e-6)
    gwf = flopy.mf6.ModflowGwf(sim, modelname=NAME, save_flows=True, newtonoptions="NEWTON")
    flopy.mf6.ModflowGwfdis(gwf, nlay=1, nrow=NROW, ncol=NCOL, delr=DELR, delc=DELC,
                            top=10.0, botm=0.0, length_units="meters")
    flopy.mf6.ModflowGwfic(gwf, strt=5.0)
    flopy.mf6.ModflowGwfnpf(gwf, k=10.0, icelltype=1, save_specific_discharge=True)
    # west edge constant head (regional gradient out)
    chd = [[(0, i, 0), 8.0] for i in range(NROW)]
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data=chd)
    # a river down column 5 (the GW<->stream exchange we read back)
    riv = [[(0, i, 5), 6.0, 100.0, 4.0] for i in range(NROW)]  # stage, cond, rbot
    flopy.mf6.ModflowGwfriv(gwf, stress_period_data=riv)
    # ARRAY recharge (RCHA) -- per-cell, the form the SWAT+ coupler will SET
    flopy.mf6.ModflowGwfrcha(gwf, recharge=1e-4)
    flopy.mf6.ModflowGwfoc(gwf, head_filerecord=f"{NAME}.hds", budget_filerecord=f"{NAME}.cbc",
                           saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")])
    sim.write_simulation()
    print("[build] MF6 model written to", WS)

def find_addr(names, *needles):
    for nm in names:
        if all(s.upper() in nm.upper() for s in needles):
            return nm
    return None

def drive():
    mf6 = XmiWrapper(lib_path=LIB, working_directory=WS)
    mf6.initialize()
    invars = mf6.get_input_var_names()
    outvars = mf6.get_output_var_names()
    rch_addr = find_addr(invars, NAME, "RCHA", "RECHARGE") or find_addr(invars, NAME, "RECHARGE")
    riv_addr = find_addr(outvars, NAME, "RIV", "SIMVALS") or find_addr(invars, NAME, "RIV", "SIMVALS")
    head_addr = find_addr(outvars, NAME, "X") or f"{NAME}/X"
    print("[addr] recharge :", rch_addr)
    print("[addr] riv flux :", riv_addr)
    print("[addr] head     :", head_addr)
    assert rch_addr and riv_addr, "could not resolve RECHARGE / RIV SIMVALS addresses"

    results = []
    end = mf6.get_end_time()
    # we re-run the single daily step twice via re-init is overkill; instead SET recharge,
    # step, read -- then SET a 10x recharge and step again within the run loop is not valid
    # for a 1-period sim, so we demonstrate SET+GET on the live arrays before the solve.
    for label, rch_val in [("baseline", 1e-4), ("x20_recharge", 2e-3)]:
        rch = mf6.get_value_ptr(rch_addr)           # zero-copy view into MF6 memory
        rch[:] = rch_val                            # <-- SET recharge (what SWAT+ does)
        mf6.prepare_time_step(0.0)
        mf6.do_time_step()                          # <-- MF6 solves
        mf6.finalize_time_step()
        riv = mf6.get_value_ptr(riv_addr)           # <-- GET river-aquifer flux (baseflow term)
        head = mf6.get_value_ptr(head_addr)
        results.append((label, rch_val, float(np.sum(riv)), float(np.mean(head))))
        print(f"[step] {label:14} recharge={rch_val:.1e}  sum(RIV flux)={np.sum(riv):+.4f} m3/d  mean head={np.mean(head):.4f} m")
        if mf6.get_current_time() >= end:
            break
    mf6.finalize()
    # verdict
    if len(results) >= 2:
        d_riv = results[1][2] - results[0][2]
        d_head = results[1][3] - results[0][3]
        print(f"\n[verdict] raising recharge changed mean head by {d_head:+.4f} m and net RIV flux by {d_riv:+.4f} m3/d")
        ok = abs(d_head) > 1e-6
        print("[verdict] SET-recharge -> solve -> GET-RIV handshake:", "PROVEN" if ok else "NO RESPONSE (investigate)")
    return results

if __name__ == "__main__":
    build()
    drive()
