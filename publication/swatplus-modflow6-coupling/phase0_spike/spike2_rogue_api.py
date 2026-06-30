#!/usr/bin/env python3
"""Phase-0 closeout: drive the REAL ported Rogue MF6 model through the XMI API at scale.

Confirms the SWAT+<->MF6 handshake works on the full 60k-cell, 5060-well, 8k-RIV Rogue
grid (not just the toy spike): resolve addresses, SET a perturbed recharge array, step,
GET the RIV river-aquifer flux + heads, and show the response. Requires the model built
by phase0_port_rogue.py (run that first).
"""
import os, numpy as np
from xmipy import XmiWrapper

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(HERE, "rogue_mf6")
LIB = "/data/SWATGenXApp/codes/_temp/swatplus-mf6-spike/bin/libmf6.so"
NAME = "ROGUE"

def addr(names, pkg, var):
    """Resolve by EXACT variable name (last path segment) with a package substring."""
    cands = [n for n in names if n.split("/")[-1].upper() == var.upper() and pkg.upper() in n.upper()]
    return cands[0] if cands else None

def run_one(mult):
    """One full init->SET-recharge->solve->GET-RIV cycle (nper=1 steady model)."""
    mf6 = XmiWrapper(lib_path=LIB, working_directory=WS)
    mf6.initialize()
    inv, outv = mf6.get_input_var_names(), mf6.get_output_var_names()
    rch_a = addr(inv, "RCHA", "RECHARGE")
    riv_a = addr(outv, "RIV", "SIMVALS") or addr(inv, "RIV", "SIMVALS")
    head_a = addr(outv, NAME, "X") or f"{NAME}/X"
    info = (rch_a, riv_a, head_a, mf6.get_value_ptr(rch_a).size, mf6.get_value_ptr(riv_a).size)
    # SET *after* prepare_time_step: the RCH package reads its file value during prepare,
    # so the coupler overrides the populated array between prepare and the solve.
    mf6.prepare_time_step(0.0)
    rch = mf6.get_value_ptr(rch_a)
    rch[:] = rch[:] * mult                          # SET (what SWAT+ does each day)
    mf6.do_time_step(); mf6.finalize_time_step()
    riv = mf6.get_value_ptr(riv_a); head = mf6.get_value_ptr(head_a)
    hv = head[np.abs(head) < 1e6]
    out = (float(np.sum(riv)), float(hv.mean()))
    mf6.finalize()
    return info, out

def main():
    (rch_a, riv_a, head_a, nrch, nriv), base = run_one(1.0)
    print("[addr] recharge:", rch_a, "| riv:", riv_a, "| head:", head_a)
    print(f"[scale] recharge array size={nrch}  river boundaries={nriv}")
    print(f"[step] baseline        net RIV flux={base[0]:+.1f} m3/d  mean head={base[1]:.2f} m")
    _, hi = run_one(1.5)
    print(f"[step] recharge_x1.5   net RIV flux={hi[0]:+.1f} m3/d  mean head={hi[1]:.2f} m")
    dh = hi[1] - base[1]
    print(f"\n[verdict] +50% recharge -> mean head {base[1]:.2f} -> {hi[1]:.2f} m ({dh:+.2f} m); "
          f"net RIV flux {base[0]:+.0f} -> {hi[0]:+.0f} m3/d (most extra recharge exits via drains)")
    # head response is the unambiguous proof the SET propagated through the solve
    print("[verdict] full-Rogue SET-recharge -> solve -> GET handshake:",
          "PROVEN AT SCALE" if abs(dh) > 0.1 else "NO RESPONSE")

if __name__ == "__main__":
    main()
