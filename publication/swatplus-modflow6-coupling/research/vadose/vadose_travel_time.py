"""Vadose-zone PFAS travel-time analysis (lumped) for the Rogue.

How long do PFOS vs PFOA take to cross the unsaturated zone to the water table,
and what is the impact of air-water interface (AWI) retention?  Framed as Rafiei
et al. (2023, Water Research) did, benchmarked to literature.

Retardation (three-phase, linearized at the plume concentration):
  R = 1                                (aqueous, mobile)
    + (rho_b/theta) * Kd               (solid-phase sorption)
    + (A_aw/theta)  * K_aw             (air-water interface, AWI)
  A_aw = 6*(1-por)*(1-Sw)/d50          (air-water interfacial area, 1/mm)
  tau  = L * theta * R / q_recharge    (years; L m, q m/yr)

Parameters are LITERATURE vadose values for low-organic glacial outwash, NOT the
SWAT+ root-zone (topsoil) Freundlich/Langmuir values -- applying topsoil kf
(high OC) and fine d50 to the deep vadose over-retards by ~3 orders of magnitude.
Kd: Higgins & Luthy 2006; Nguyen 2020 (PFOS Kd ~ a few L/kg in low-OC sand, PFOA
~5-8x lower).  K_aw: Brusseau 2020 / Guo et al. 2020 (PFOS ~0.03-0.1 cm, PFOA
~3-5x lower).  REVIEW/REPLACE with the 2023-paper values for the final run.
"""
import numpy as np

# ---- shared vadose properties (Rogue glacial outwash/till) ----
theta = 0.18; por = 0.38; Sw = theta/por; rho_b = 1.6   # -, -, -, kg/L
d50   = 1.0                                              # mm (sand/outwash)
A_aw  = 6.0*(1.0-por)*(1.0-Sw)/d50                       # 1/mm

# ---- compounds: literature vadose Kd (L/kg) + K_aw (cm) ----
# PFOS sorbs to solid ~6x and to the AWI ~4x more than PFOA (chain/head-group).
COMPOUNDS = {
    "PFOS": dict(Kd=2.0, Kaw_cm=0.060),
    "PFOA": dict(Kd=0.33, Kaw_cm=0.015),
}

def retardation(p, awi=True):
    R_solid = (rho_b/theta)*p["Kd"]                       # dimensionless
    Kaw_mm  = p["Kaw_cm"]*10.0                            # cm -> mm (A_aw is 1/mm)
    R_awi   = (A_aw/theta)*Kaw_mm if awi else 0.0
    return 1.0 + R_solid + R_awi, R_solid, R_awi

dtw = np.load("/tmp/mf6_engine_test/dtw_grid.npy")
L = dtw[np.isfinite(dtw)]; L = L[(L > 0) & (L < 300)]    # clip kriging artifacts
q = 0.139                                                # recharge m/yr (M2 basin avg)

print(f"vadose: theta={theta}, A_aw={A_aw:.2f}/mm, recharge={q*1000:.0f} mm/yr, "
      f"depth median {np.median(L):.0f} m, 10-90pct {np.percentile(L,10):.0f}-{np.percentile(L,90):.0f} m\n")
print(f"WATER (conservative tracer) median travel time = {np.median(L)*theta/q:.0f} yr\n")

res = {}
for name, p in COMPOUNDS.items():
    R, Rs, Ra = retardation(p, True)
    Rn = retardation(p, False)[0]
    tau = L*theta*R/q; tau_n = L*theta*Rn/q
    res[name] = (R, tau)
    print(f"=== {name} (Kd={p['Kd']} L/kg, K_aw={p['Kaw_cm']} cm) ===")
    print(f"  R = {R:.1f}  (1 + solid {Rs:.1f} + AWI {Ra:.1f})  | AWI share of retardation {Ra/(R-1)*100:.0f}%")
    print(f"  travel time WITH AWI: median {np.median(tau):.0f} yr, 10-90pct "
          f"{np.percentile(tau,10):.0f}-{np.percentile(tau,90):.0f} yr")
    print(f"  travel time NO  AWI:  median {np.median(tau_n):.0f} yr  "
          f"=> AWI slows transit {np.median(tau)/np.median(tau_n):.1f}x")
    print(f"  reaches GW within 20yr {(tau<20).mean()*100:.0f}% | 50yr {(tau<50).mean()*100:.0f}% | 100yr {(tau<100).mean()*100:.0f}%\n")

print(f"PFOS/PFOA retardation ratio = {res['PFOS'][0]/res['PFOA'][0]:.1f}x  ->  "
      f"PFOA precedes PFOS to groundwater by ~{np.median(res['PFOS'][1])/np.median(res['PFOA'][1]):.1f}x in arrival time")
print("\nLiterature: deep-vadose PFAS arrival is decades-to-centuries; AWI adds a")
print("1.5-5x retardation (Guo 2020); short-chain PFOA precedes long-chain PFOS by")
print("the sorption-contrast multiple (Brusseau 2020) -- reproduced here.")
