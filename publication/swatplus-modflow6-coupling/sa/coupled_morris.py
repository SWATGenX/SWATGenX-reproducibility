#!/usr/bin/env python3
"""Coupled SWAT+ <-> MODFLOW 6 Morris (elementary-effects) sensitivity analysis
for the Rogue PFAS model. Full 18-parameter screening over the surface-water PFAS
engine (5), the groundwater flow model (7), and the groundwater transport model (6),
on the integrated in-stream and aquifer quantities of interest.

Structure exploits separability: the coupled in-stream PFOS at mainstem reach i is
    C_i = C_SW_i(theta_SW)  +  G * B_i(theta_GW)
(additive in the two legs; G = calibrated coupling effectiveness 0.061). So we DEDUP:
run each distinct surface sub-vector through SWAT+ once and each distinct groundwater
sub-vector through MODFLOW once, then assemble every Morris sample from the lookups.
This gives both the OAT caching win and clean parallelism.

QoIs:
  instream_lower : coupled in-stream PFOS at the lower mainstem (ch 2, RR-0020)
  instream_mid   : coupled in-stream PFOS at mid mainstem    (ch 10, RR-0050)
  gw_plume       : mean modeled groundwater PFOS at the predicted obs cells
  baseflow       : net gaining groundwater discharge to the stream (m3/s)

Env knobs: SA_R (trajectories, default 20), SA_LEVELS (default 4), SA_SEED,
SA_NPROC, SA_OUT, plus the leg paths (SW_MODEL, SW_BIN, SW_LD, GW_CAL, GW_MF6,
STATIC_NPZ). Writes morris_samples.csv, morris_Y.csv, morris_indices_<qoi>.csv.
"""
import os, sys, shutil, subprocess, time, glob, json
import numpy as np
from multiprocessing import Pool
from SALib.sample.morris import sample as morris_sample
from SALib.analyze import morris as morris_analyze

# ----------------------------------------------------------------------------- config
HERE = os.path.dirname(os.path.abspath(__file__))
SW_MODEL = os.environ.get("SW_MODEL", "/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/run_rogue")
SW_BIN   = os.environ.get("SW_BIN", os.path.join(SW_MODEL, "swatplus_pfas"))
SW_LD    = os.environ.get("SW_LD", "/data/SWATGenXApp/codes/lib/netcdf-ifx")
GW_CAL   = os.environ.get("GW_CAL", "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500/MODFLOW_sfr_cal")
GW_MF6   = os.environ.get("GW_MF6", "/data/SWATGenXApp/codes/bin/mf6")
STATIC   = os.environ.get("STATIC_NPZ", os.path.join(HERE, "static_gw.npz"))
WORK     = os.environ.get("SA_WORK", "/tmp/sa_work")
OUT      = os.environ.get("SA_OUT", HERE)
R        = int(os.environ.get("SA_R", "20"))
LEVELS   = int(os.environ.get("SA_LEVELS", "4"))
SEED     = int(os.environ.get("SA_SEED", "20260623"))
NPROC    = int(os.environ.get("SA_NPROC", str(max(1, (os.cpu_count() or 2) - 1))))
NYEARS   = int(os.environ.get("SA_GW_NYEARS", "40"))
G_COUPLE = 0.061          # calibrated GW-source effectiveness (joint fit)

# ----------------------------------------------------------------------------- params
# name, lo, hi, leg, transform  (transform: 'lin' or 'log10' -> value = 10**x)
PARAMS = [
    ("soil_scale", 0.05,  0.22,  "sw", "lin"),
    ("koc_scale",  0.50,  2.00,  "sw", "lin"),
    ("kl",         0.07,  0.27,  "sw", "lin"),
    ("lm",         1500., 3500., "sw", "lin"),
    ("percop",     0.10,  0.40,  "sw", "lin"),
    ("kh",        -0.80,  0.80,  "gwf","lin"),
    ("kv",        -0.80,  0.80,  "gwf","lin"),
    ("rch",       -0.30,  0.48,  "gwf","lin"),
    ("ghb",       -2.00,  0.50,  "gwf","lin"),
    ("drn",       -2.00,  0.50,  "gwf","lin"),
    ("pump",      -1.70,  0.00,  "gwf","lin"),
    ("sfrk",      -1.50,  1.00,  "gwf","lin"),
    ("t_kf",      -3.00, -1.30,  "gwt","log10"),  # Freundlich Kf 1e-3..5e-2
    ("t_n",        0.60,  1.00,  "gwt","lin"),     # Freundlich exponent
    ("t_alh",      1.00,  50.0,  "gwt","lin"),     # longitudinal dispersivity (m)
    ("t_ath",      0.10,  5.00,  "gwt","lin"),     # transverse dispersivity (m)
    ("t_cap",      4.00,  6.00,  "gwt","log10"),   # source cap 1e4..1e6 ng/L
    ("t_bg",       5.00,  20.0,  "gwt","lin"),     # ambient background ng/L
]
NAMES = [p[0] for p in PARAMS]
PROBLEM = {"num_vars": len(PARAMS), "names": NAMES,
           "bounds": [[p[1], p[2]] for p in PARAMS]}
SW_IDX  = [i for i, p in enumerate(PARAMS) if p[3] == "sw"]
GW_IDX  = [i for i, p in enumerate(PARAMS) if p[3] in ("gwf", "gwt")]

def phys(i, x):
    """physical value of parameter i given the sampled (bounds-space) value x."""
    return 10.0 ** x if PARAMS[i][4] == "log10" else x

# ----------------------------------------------------------------------------- SW leg
def sw_write_inputs(rundir, sw):
    soil_scale, koc_scale, kl, lm, percop = sw
    with open(os.path.join(rundir, "pfas_calib.dat"), "w") as f:
        f.write(f"{soil_scale:.6f} {koc_scale:.6f}\n")
    path = os.path.join(rundir, "pfas.dat")
    lines = open(path).readlines()
    for i, ln in enumerate(lines):
        t = ln.split()
        if len(t) >= 7 and t[0] == "1" and t[1].upper().startswith("PFOS"):
            lines[i] = (f"  {t[0]:<3s}{t[1]:<8s}{float(t[2]):<10.5f} {float(t[3]):<10.2f} "
                        f"{kl:<9.4f} {lm:<9.1f} {percop:.3f}\n")
            break
    open(path, "w").writelines(lines)

def sw_parse_mainstem(path, mainstem):
    from collections import defaultdict
    mass = defaultdict(float); vol = defaultdict(float)
    with open(path) as f:
        f.readline()
        for line in f:
            p = line.split()
            if len(p) < 18: continue
            try:
                unit = int(p[4]); sol = float(p[9]); sor = float(p[10]); conc = float(p[-1])
            except ValueError: continue
            m = sol + sor; mass[unit] += m
            if conc > 0: vol[unit] += m / conc * 1e9
    return {int(c): (mass[c] / vol[c] * 1e9 if vol[c] > 0 else 0.0) for c in mainstem}

DRYRUN = os.environ.get("SA_DRYRUN", "0") == "1"

def run_sw(arg):
    key, sw, mainstem = arg
    if DRYRUN:   # surrogate: in-stream SW PFOS ~ soil_scale*koc, rising downstream
        ss, kc = sw[0], sw[1]
        return key, {int(c): 40*ss*kc*(1+0.05*(7-i)) for i, c in enumerate(mainstem)}
    rundir = os.path.join(WORK, f"sw_{key}")
    t0 = time.time()
    try:
        shutil.rmtree(rundir, ignore_errors=True)
        shutil.copytree(SW_MODEL, rundir, symlinks=True)
        sw_write_inputs(rundir, sw)
        env = dict(os.environ)
        env["LD_LIBRARY_PATH"] = SW_LD + ":" + env.get("LD_LIBRARY_PATH", "")
        env["OMP_NUM_THREADS"] = "1"
        binp = os.path.join(rundir, os.path.basename(SW_BIN))
        with open(os.path.join(rundir, "run.log"), "w") as lg:
            subprocess.run([binp], cwd=rundir, env=env, stdout=lg,
                           stderr=subprocess.STDOUT, timeout=2400, check=False)
        cp = os.path.join(rundir, "channel_pfas_day.txt")
        conc = sw_parse_mainstem(cp, mainstem) if os.path.exists(cp) else {}
        print(f"[sw {key}] {time.time()-t0:5.0f}s ss={sw[0]:.3f} nchan={len(conc)}", flush=True)
        return key, conc
    except Exception as e:
        print(f"[sw {key}] FAIL {e}", flush=True); return key, {}
    finally:
        shutil.rmtree(rundir, ignore_errors=True)

# ----------------------------------------------------------------------------- GW leg
_S = np.load(STATIC)
REACH_RC = _S["reach_rc"]; REACH_CH = _S["reach_channel"]; CH = _S["ch"]; CHR = _S["chr"]
AREA = _S["area"]; MAINSTEM = _S["mainstem"]; MEAN_Q = float(_S["mean_q"])
SRC_RC = set(map(tuple, _S["src_rc"])); OBS_RC = _S["obs_rc"]; OBS_VAL = _S["obs_val"]
PERLEN = 365.25; POROSITY = 0.30; BULK = 1800.0; DIFFC = 1e-10

def gw_build(ws, gw):
    import flopy
    kh, kv, rch, ghb, drn, pump, sfrk, tkf, tn, talh, tath, tcap, tbg = gw
    sim = flopy.mf6.MFSimulation.load(sim_ws=GW_CAL, exe_name=GW_MF6, verbosity_level=0)
    sim.set_sim_path(ws); g = sim.get_model(); gwfname = g.name
    # ---- perturb flow ----
    npf = g.get_package("npf")
    npf.k.set_data(np.array(npf.k.array) * 10**kh)
    if npf.k33.array is not None: npf.k33.set_data(np.array(npf.k33.array) * 10**kv)
    rp = g.get_package("rcha"); rp.recharge.set_data({k: np.array(v)*10**rch for k, v in rp.recharge.get_data().items()})
    for name, col, mult in [("ghb", "cond", ghb), ("drn", "cond", drn), ("wel", "q", pump)]:
        pk = g.get_package(name); d = pk.stress_period_data.get_data()
        out = {}
        for k, v in d.items():
            v2 = v.copy(); v2[col] = v[col] * 10**mult; out[k] = v2
        pk.stress_period_data.set_data(out)
    sfr = g.get_package("sfr_0"); pd_ = sfr.packagedata.get_data()
    if "rhk" in pd_.dtype.names:
        pd_ = pd_.copy(); pd_["rhk"] = pd_["rhk"] * 10**sfrk; sfr.packagedata.set_data(pd_)
    dis = g.dis; nlay, nrow, ncol = dis.nlay.array, dis.nrow.array, dis.ncol.array
    idom = dis.idomain.array; nre = sfr.nreaches.array
    # ---- transport ----
    ats = [(i, PERLEN/8.0, 0.01, PERLEN, 2.0, 5.0) for i in range(NYEARS)]
    tdis = flopy.mf6.ModflowTdis(sim, nper=NYEARS, time_units="days", perioddata=[(PERLEN, 8, 1.2)]*NYEARS)
    flopy.mf6.ModflowUtlats(tdis, maxats=len(ats), perioddata=ats, filename="pfas.ats")
    g.sto.steady_state.set_data({0: True})
    gwt = flopy.mf6.ModflowGwt(sim, modelname="pfas", save_flows=True)
    flopy.mf6.ModflowGwtdis(gwt, nlay=nlay, nrow=nrow, ncol=ncol, delr=dis.delr.array,
                            delc=dis.delc.array, top=dis.top.array, botm=dis.botm.array,
                            idomain=idom, length_units="meters")
    flopy.mf6.ModflowGwtic(gwt, strt=tbg); flopy.mf6.ModflowGwtadv(gwt, scheme="tvd")
    flopy.mf6.ModflowGwtdsp(gwt, alh=talh, ath1=tath, diffc=DIFFC)
    flopy.mf6.ModflowGwtmst(gwt, porosity=POROSITY, sorption="freundlich",
                            bulk_density=BULK, distcoef=tkf, sp2=tn)
    cnc = [[(0, int(r), int(c)), tcap] for r, c in SRC_RC if idom[0, int(r), int(c)] != 0]
    flopy.mf6.ModflowGwtcnc(gwt, stress_period_data={0: cnc}, pname="cnc")
    flopy.mf6.ModflowGwtssm(gwt, sources=[[]])
    flopy.mf6.ModflowGwtsft(gwt, flow_package_name="sfr_0", save_flows=True,
                            packagedata=[[r, 0.0] for r in range(nre)], pname="sft_0")
    flopy.mf6.ModflowGwtoc(gwt, concentration_filerecord="pfas.ucn", saverecord=[("CONCENTRATION", "LAST")])
    flopy.mf6.ModflowGwfgwt(sim, exgtype="GWF6-GWT6", exgmnamea=gwfname, exgmnameb="pfas", filename="pfas.gwfgwt")
    ims = flopy.mf6.ModflowIms(sim, complexity="COMPLEX", linear_acceleration="BICGSTAB",
                               outer_dvclose=1e-3, inner_dvclose=1e-4, outer_maximum=500,
                               inner_maximum=500, filename="pfas.ims")
    sim.register_ims_package(ims, ["pfas"]); sim.write_simulation(silent=True)
    return gwfname

def gw_extract(ws):
    import flopy
    cbc = flopy.utils.CellBudgetFile(glob.glob(f"{ws}/*.sfr.cbc")[0])
    rec = cbc.get_data(text="GWF")[-1]
    qgw = rec["q"] if rec.dtype.names else np.array([r[2] for r in rec])
    ucn = flopy.utils.HeadFile(f"{ws}/pfas.ucn", text="CONCENTRATION")
    c = ucn.get_data()                      # (nlay,nrow,ncol)
    cmax = np.nanmax(np.where(c > 1e29, np.nan, c), axis=0)
    caq = np.array([cmax[r, c_] for r, c_ in REACH_RC])
    is_src = np.array([(int(r), int(c_)) in SRC_RC for r, c_ in REACH_RC])
    load = np.where((qgw > 0) & ~is_src, qgw * caq * 1000.0, 0.0)
    per_ch = {}
    for c_, l in zip(REACH_CH, load): per_ch[int(c_)] = per_ch.get(int(c_), 0.0) + l
    nd = {int(a): int(b) for a, b in zip(CH, CHR)}; valid = set(CH.tolist())
    cum = {int(x): 0.0 for x in CH}
    for s, l in per_ch.items():
        if l <= 0: continue
        cur, seen = int(s), set()
        while cur in valid and cur not in seen:
            cum[cur] += l; seen.add(cur); cur = nd.get(cur, -1)
    amax = AREA.max(); adict = dict(zip(CH.tolist(), AREA.tolist()))
    B = {}
    for ci in MAINSTEM:
        q_i = MEAN_Q * adict.get(int(ci), amax) / amax
        B[int(ci)] = cum.get(int(ci), 0.0) / (q_i * 86400.0 * 1000.0)
    baseflow = float(np.sum(qgw)) / 86400.0                       # net gaining (m3/s)
    plume = float(np.nanmean([cmax[r, c_] for r, c_ in OBS_RC]))  # mean modeled at obs cells
    return B, baseflow, plume

def run_gw(arg):
    key, gw = arg
    if DRYRUN:   # surrogate: B downstream-heavy ~ source/transport; baseflow ~ recharge/K
        kh, kv, rch, ghb, drn, pump, sfrk, tkf, tn, talh, tath, tcap, tbg = gw
        B = {int(c): (tcap/1e5)*(tkf/0.005)*(0.5+2.0*(i >= 5)) for i, c in enumerate(MAINSTEM)}
        bf = 5.0 * 10**rch * 10**(0.3*kh)
        plume = tbg + 0.1*tcap*(tkf/0.005)
        return key, (B, bf, plume)
    ws = os.path.join(WORK, f"gw_{key}")
    t0 = time.time()
    try:
        shutil.rmtree(ws, ignore_errors=True)
        gw_build(ws, gw)
        p = subprocess.run([GW_MF6], cwd=ws, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=3600)
        lst = os.path.join(ws, "mfsim.lst"); txt = open(lst, errors="ignore").read() if os.path.exists(lst) else ""
        ok = (p.returncode == 0) and ("Normal termination" in txt) and ("CONVERGENCE FAILURE" not in txt)
        if not ok:
            print(f"[gw {key}] FAIL converge", flush=True); return key, None
        B, bf, plume = gw_extract(ws)
        print(f"[gw {key}] {time.time()-t0:5.0f}s bf={bf:.1f} plume={plume:.0f}", flush=True)
        return key, (B, bf, plume)
    except Exception as e:
        print(f"[gw {key}] FAIL {e}", flush=True); return key, None
    finally:
        shutil.rmtree(ws, ignore_errors=True)

# ----------------------------------------------------------------------------- main
def main():
    os.makedirs(WORK, exist_ok=True); os.makedirs(OUT, exist_ok=True)
    X = morris_sample(PROBLEM, N=R, num_levels=LEVELS, seed=SEED)   # (R*(D+1), D)
    n = X.shape[0]
    print(f"[morris] D={len(PARAMS)} R={R} levels={LEVELS} -> {n} samples; nproc={NPROC}", flush=True)
    # physical values
    Xp = np.array([[phys(i, X[s, i]) for i in range(len(PARAMS))] for s in range(n)])
    mains = [int(c) for c in MAINSTEM]

    # ---- dedup sub-vectors ----
    def key_of(vec): return "_".join(f"{v:.6g}" for v in vec)
    sw_jobs, sw_key_for = {}, []
    for s in range(n):
        sw = Xp[s, SW_IDX]; k = key_of(sw); sw_key_for.append(k)
        if k not in sw_jobs: sw_jobs[k] = (k, [float(v) for v in sw], mains)
    gw_jobs, gw_key_for = {}, []
    for s in range(n):
        gw = Xp[s, GW_IDX]; k = key_of(gw); gw_key_for.append(k)
        if k not in gw_jobs: gw_jobs[k] = (k, [float(v) for v in gw])
    print(f"[morris] unique SW runs={len(sw_jobs)}  unique GW runs={len(gw_jobs)}", flush=True)

    t0 = time.time()
    with Pool(NPROC) as pool:
        sw_res = dict(pool.map(run_sw, list(sw_jobs.values()), chunksize=1))
    print(f"[morris] SW done {time.time()-t0:.0f}s", flush=True)
    t1 = time.time()
    with Pool(NPROC) as pool:
        gw_res = dict(pool.map(run_gw, list(gw_jobs.values()), chunksize=1))
    print(f"[morris] GW done {time.time()-t1:.0f}s", flush=True)

    # ---- assemble QoIs ----
    ch_low, ch_mid = 2, 10
    Y = {k: np.full(n, np.nan) for k in ["instream_lower", "instream_mid", "gw_plume", "baseflow"]}
    for s in range(n):
        cs = sw_res.get(sw_key_for[s], {}); gw = gw_res.get(gw_key_for[s])
        if not cs or gw is None: continue
        B, bf, plume = gw
        Y["instream_lower"][s] = cs.get(ch_low, np.nan) + G_COUPLE * B.get(ch_low, 0.0)
        Y["instream_mid"][s]   = cs.get(ch_mid, np.nan) + G_COUPLE * B.get(ch_mid, 0.0)
        Y["gw_plume"][s]       = plume
        Y["baseflow"][s]       = bf

    # ---- save raw + analyze ----
    np.savetxt(os.path.join(OUT, "morris_samples.csv"), X, delimiter=",",
               header=",".join(NAMES), comments="")
    with open(os.path.join(OUT, "morris_Y.csv"), "w") as f:
        f.write(",".join(Y.keys()) + "\n")
        for s in range(n):
            f.write(",".join(f"{Y[k][s]:.6g}" for k in Y) + "\n")
    summary = {}
    for qoi, y in Y.items():
        ok = ~np.isnan(y)
        if ok.sum() < len(PARAMS) + 1:
            print(f"[morris] {qoi}: too few valid ({ok.sum()})", flush=True); continue
        Si = morris_analyze.analyze(PROBLEM, X[ok], y[ok], num_levels=LEVELS, seed=SEED)
        rows = sorted(zip(NAMES, Si["mu_star"], Si["mu_star_conf"], Si["sigma"]),
                      key=lambda r: -r[1])
        with open(os.path.join(OUT, f"morris_indices_{qoi}.csv"), "w") as f:
            f.write("param,mu_star,mu_star_conf,sigma\n")
            for nm, ms, mc, sg in rows: f.write(f"{nm},{ms:.6g},{mc:.6g},{sg:.6g}\n")
        summary[qoi] = {"n_valid": int(ok.sum()), "top": [r[0] for r in rows[:5]]}
        print(f"[morris] {qoi}: n={ok.sum()} top5={[r[0] for r in rows[:5]]}", flush=True)
    json.dump(summary, open(os.path.join(OUT, "morris_summary.json"), "w"), indent=2)
    print(f"[morris] DONE total wall {time.time()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    main()
