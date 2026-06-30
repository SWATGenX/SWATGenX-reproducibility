"""Assemble the MODELED in-stream GW fingerprint (from multianalyte SFT runs) and compare to the
OBSERVED plume end-member and the observed per-reach GW gradient.

Consumes multianalyte_reach_conc.csv (per-reach, per-analyte SFT in-stream conc from GW discharge).
Two tests:
  (1) Does the modeled GW-discharged in-stream composition match the observed GW plume fingerprint?
      (SFT should transport the plume signature to the channel.)
  (2) Do the reaches the model lights up with GW PFOS coincide with the reaches where the observed
      fingerprint unmixing found high f_gw (instream_snapped.csv)?
"""
import pandas as pd, numpy as np, geopandas as gpd
from shapely.geometry import Point
OUT = "/data/SWATGenXApp/codes/publication/swatplus-modflow6-coupling/research/multianalyte_spike"
SHP = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500/SWAT_MODEL_Web_Application/Watershed/Shapes/rivs1.shp"
LEAN5 = ["PFOS", "PFOA", "PFHxS", "PFBS", "PFHxA"]

rc = pd.read_csv(f"{OUT}/multianalyte_reach_conc.csv")   # reach, PFOS, PFOA, ...
present = [a for a in LEAN5 if a in rc.columns]
rc["tot"] = rc[present].sum(axis=1)
for a in present:
    rc[a + "_f"] = rc[a] / rc.tot.replace(0, np.nan)

# observed plume end-member (from earlier spike)
fp = pd.read_csv(f"{OUT}/rogue_fingerprints.csv")
plume = fp[fp["class"] == "GW_plume"]
gw_em = {a: plume[a].sum() for a in present}
s = sum(gw_em.values()); gw_em = {a: gw_em[a] / s for a in present}

# modeled GW-discharged in-stream fingerprint, averaged over reaches that actually carry GW load
carry = rc[rc.tot > rc.tot.quantile(0.75)]
mod_fp = {a: carry[a].sum() for a in present}; s2 = sum(mod_fp.values()); mod_fp = {a: mod_fp[a] / s2 for a in present}
print("=== TEST 1: modeled GW-discharged in-stream fingerprint vs observed plume end-member ===")
print(f"{'analyte':8s} {'observed_plume':>15s} {'modeled_SFT':>13s}")
for a in present:
    print(f"{a:8s} {gw_em[a]:15.3f} {mod_fp[a]:13.3f}")
l1 = sum(abs(gw_em[a] - mod_fp[a]) for a in present)
print(f"L1 distance (plume vs modeled-discharge) = {l1:.3f}  (small => SFT preserves the plume signature)")

# map SFT reach index -> Channel. SFT reaches are 0-based in topological/SFR order; the model's
# rivs1 channel mapping requires the reach->channel table. Use spatial: snap observed high-f_gw
# stations to channels (already in instream_snapped.csv) and compare modeled GW load on those channels.
print("\n=== TEST 2: spatial coincidence of modeled GW in-stream load with observed high-f_gw reaches ===")
try:
    snap = pd.read_csv(f"{OUT}/instream_snapped.csv")
    onch = snap[snap.snap_m < 50].groupby("Channel").f_gw.median()
    # modeled per-reach total; need reach->channel. Approx: rank reaches by modeled GW load and report
    rc_sorted = rc.sort_values("tot", ascending=False)
    print(f"reaches with modeled GW in-stream PFOS >1 ng/L: {(rc.tot>1).sum()} of {len(rc)}")
    print(f"top-5 modeled GW-load reaches (SFT idx): {rc_sorted.reach.head(5).tolist()}")
    print(f"observed on-channel high-f_gw channels (>0.4): {onch[onch>0.4].index.tolist()}")
    print("(full reach->channel join needs the SFR packagedata order; done in next step)")
except Exception as e:
    print("test2 skipped:", e)

rc.to_csv(f"{OUT}/multianalyte_reach_fingerprint.csv", index=False)
print("\nsaved multianalyte_reach_fingerprint.csv")
