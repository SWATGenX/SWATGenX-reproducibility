"""One-at-a-time HYDRAULIC sensitivity of the coupled SWAT+/MODFLOW 6 PFHxA model.

For each hydraulic parameter, run the live coupling at x0.5 and x2.0 of base and
record the surface<->groundwater MASS EXCHANGE (recharge in, SFR gaining baseflow,
SFR losing seepage, PFHxA discharged to streams) and the MODFLOW transport mass-
balance discrepancy.  PFHxA (R~1.6) exchanges on the short (90-day) window, so the
signal reflects model interactions, not plume accuracy.

Params: aquifer Kh, Kv; recharge (coupler multiplier); streambed K (SFR rhk);
specific yield (STO sy); longitudinal dispersivity (DSP alh).
"""
import os, re, shutil, subprocess
import numpy as np
import flopy

BASE = "/tmp/oat_base"
ENVP = ("set +u; source /opt/intel/oneapi/setvars.sh >/dev/null 2>&1; "
        "export LD_LIBRARY_PATH=/data/SWATGenXApp/codes/bin:$LD_LIBRARY_PATH; ")
PARAMS = ["Kh", "Kv", "recharge", "sfrk", "SY", "disp"]
FACTORS = [0.5, 2.0]   # committed oat_results.csv used these; 4 extreme (high-velocity) cases hit MF6 non-convergence (a robustness finding)
                       # daily transport stays Courant-stable (x0.5/x2 broke MF6
                       # convergence at high flow velocity)


def apply_param(d, param, f):
    if param == "recharge":
        L = open(f"{d}/mf6.con").read().splitlines()
        while len(L) < 4:
            L.append("")
        L[3] = f"{f}"
        open(f"{d}/mf6.con", "w").write("\n".join(L) + "\n")
        return
    sim = flopy.mf6.MFSimulation.load(sim_ws=f"{d}/mf6", verbosity_level=0)
    gwf = sim.get_model("modflow_sfr"); gwt = sim.get_model("pfas")
    if param == "Kh":
        npf = gwf.get_package("npf"); npf.k.set_data(np.array(npf.k.array) * f)
    elif param == "Kv":
        npf = gwf.get_package("npf")
        if npf.k33.array is not None:
            npf.k33.set_data(np.array(npf.k33.array) * f)
    elif param == "sfrk":
        sfr = gwf.get_package("sfr_0"); pd = sfr.packagedata.get_data()
        pd["rhk"] = pd["rhk"] * f; sfr.packagedata.set_data(pd)
    elif param == "SY":
        sto = gwf.get_package("sto"); sto.sy.set_data(np.array(sto.sy.array) * f)
    elif param == "disp":
        dsp = gwt.get_package("dsp")
        dsp.alh.set_data(np.array(dsp.alh.array) * f)
        if dsp.ath1.array is not None:
            dsp.ath1.set_data(np.array(dsp.ath1.array) * f)
    sim.write_simulation()


def parse(log):
    def g(pat):
        m = re.search(pat, log)
        return float(m.group(1)) if m else np.nan
    return dict(
        recharge=g(r"recharge \(sum[^=]*=\s*([0-9.eE+-]+)"),
        gain=g(r"SFR exchange: gaining\s*([0-9.eE+-]+)"),
        loss=g(r"losing\s*(-?[0-9.eE+-]+)"),
        disch=g(r"PFAS discharged to stream\s*=\s*([0-9.eE+-]+)"),
    )


def massbal(d):
    try:
        t = open(f"{d}/mf6/pfas.lst").read()
        pc = re.findall(r"PERCENT DISCREPANCY =\s*(-?[0-9.eE+-]+)", t)
        return float(pc[-1]) if pc else np.nan
    except Exception:
        return np.nan


def run(d):
    subprocess.run(f"cd {d} && {ENVP} timeout 900 ./swatplus-mf6 > run.log 2>&1",
                   shell=True, executable="/bin/bash")
    r = parse(open(f"{d}/run.log").read()); r["mb"] = massbal(d)
    return r


rows = []
base = parse(open("/tmp/oat_base.log").read()); base["mb"] = massbal(BASE)
rows.append(("base", 1.0, base))
print(f"base: recharge={base['recharge']:.3g} gain={base['gain']:.3g} disch={base['disch']:.3g}")
for p in PARAMS:
    for f in FACTORS:
        d = f"/tmp/oat_{p}_{f}"
        if os.path.exists(d):
            shutil.rmtree(d)
        shutil.copytree(BASE, d)
        apply_param(d, p, f)
        r = run(d); rows.append((p, f, r))
        print(f"{p} x{f}: recharge={r['recharge']:.3g} gain={r['gain']:.3g} "
              f"loss={r['loss']:.3g} disch={r['disch']:.3g} mb%={r['mb']:.2g}", flush=True)

with open("/tmp/oat_results.csv", "w") as fo:
    fo.write("param,factor,recharge_m,sfr_gain_m3,sfr_loss_m3,pfhxa_disch_kg,massbal_pct\n")
    for p, f, r in rows:
        fo.write(f"{p},{f},{r['recharge']},{r['gain']},{r['loss']},{r['disch']},{r['mb']}\n")
print("wrote /tmp/oat_results.csv")
