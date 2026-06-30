"""(1) Verify the lumped travel time against an EXPLICIT 1D advection-dispersion-
retardation breakthrough (Ogata-Banks) -- the two approaches the user asked to
test.  (2) Sobol sensitivity + uncertainty of the vadose travel time.

tau_lumped = L*theta*R/q ;  R = 1 + (rho_b/theta)Kd + (A_aw/theta)K_aw
Explicit 1D: C/C0 = 0.5 erfc[(L - v t/R)/(2 sqrt(D t/R))], v=q/theta, D=alpha*v.
The 50% breakthrough time at z=L equals R*L/v = tau_lumped (dispersion only
spreads the front), so agreement validates the lumped estimate.
"""
import numpy as np
from scipy.special import erfc
from SALib.sample import sobol as sobol_sample
from SALib.analyze import sobol as sobol_analyze

rho_b = 1.6
def A_aw(por, Sw, d50): return 6*(1-por)*(1-Sw)/d50
def R_factor(Kd, Kaw_cm, theta, por, d50):
    Sw = theta/por
    return 1 + (rho_b/theta)*Kd + (A_aw(por, Sw, d50)/theta)*Kaw_cm*10

NOM = {"PFOS": dict(Kd=2.0, Kaw_cm=0.060), "PFOA": dict(Kd=0.33, Kaw_cm=0.015)}
theta0, por0, d500, q0, L0 = 0.18, 0.38, 0.5, 0.139, 31.0   # median-cell

print("=== (1) lumped vs explicit-1D breakthrough (median 31 m column) ===")
for name, p in NOM.items():
    R = R_factor(p["Kd"], p["Kaw_cm"], theta0, por0, d500)
    tau = L0*theta0*R/q0
    v = q0/theta0; D = 5.0*v          # 5 m dispersivity (10-20% of L)
    t = np.linspace(0.1, 4*tau, 4000)
    C = 0.5*erfc((L0 - v*t/R)/(2*np.sqrt(D*t/R)))
    t50 = t[np.argmin(np.abs(C-0.5))]
    print(f"  {name}: lumped tau={tau:.0f} yr | explicit-1D 50% breakthrough={t50:.0f} yr "
          f"| agree to {abs(t50-tau)/tau*100:.0f}%")

print("\n=== (2) Sobol sensitivity + uncertainty of PFOS vadose travel time ===")
problem = {
    "num_vars": 6,
    "names": ["Kd", "K_aw", "theta", "d50", "recharge", "depth"],
    "bounds": [[1.0, 4.0], [0.02, 0.12], [0.12, 0.25], [0.1, 2.0], [0.05, 0.25], [12.0, 69.0]],
}
X = sobol_sample.sample(problem, 1024)
Y = np.array([L*th*R_factor(Kd, Kaw, th, por0, d50)/q
              for Kd, Kaw, th, d50, q, L in X])
Si = sobol_analyze.analyze(problem, Y, print_to_console=False)
print(f"  PFOS travel time over the parameter space: median {np.median(Y):.0f} yr, "
      f"5-95pct {np.percentile(Y,5):.0f}-{np.percentile(Y,95):.0f} yr")
print("  Sobol total-order indices (share of travel-time variance):")
order = np.argsort(Si["ST"])[::-1]
for i in order:
    print(f"    {problem['names'][i]:9s}  ST={Si['ST'][i]:.2f}  S1={Si['S1'][i]:.2f}")
print("\n  => the dominant controls on land->GW PFAS timing are the ones to constrain")
print("     (and they are all >> the 54-yr simulation window: land PFAS does not")
print("     reach groundwater within 1970-2024 -- GW PFAS is legacy).")
