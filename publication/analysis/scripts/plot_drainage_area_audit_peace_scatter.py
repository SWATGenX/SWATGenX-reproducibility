#!/usr/bin/env python3
"""Peace River drainage-area audit scatter for the manuscript (Objective 2).

Reads the up-to-date frontend catalog (source of truth for the published page)
and plots SWAT+ chandeg.con area vs original NHDPlus HR TotDASqKm at the 76
gage-assigned channels, colored by audit class, with a 1:1 line and the
0.5-2.0x agreement band.

Output: publication/manuscript/final/fig-drainage-area-audit-peace-scatter.png
"""
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = "/data/SWATGenXApp/codes"
CATALOG = os.path.join(ROOT, "web_application/frontend/src/data/drainageAreaAuditCatalog.json")
OUT = os.path.join(ROOT, "publication/figures/final/fig-drainage-area-audit-peace-scatter.png")

CLASS_STYLE = {
    "swat_nhd_ok":            ("#2e7d32", "o", "Within 0.5–2.0×"),
    "swat_nhd_moderate":      ("#1565c0", "s", "Moderate (band edge)"),
    "assignment_outlier_low": ("#e65100", "v", "Assignment outlier (low)"),
    "assignment_outlier_high":("#c62828", "^", "Assignment outlier (high)"),
}

def main():
    cat = json.load(open(CATALOG))
    peace = next(m for m in cat["models"] if m["catalogModelId"] == "03100101")
    stations = [s for s in peace["stations"]
                if s.get("swatplusDrainageAreaKm2") and s.get("nhdHrTotdasqkmKm2")]
    s = peace["summary"]

    fig, ax = plt.subplots(figsize=(6.6, 6.0))
    lo, hi = 0.05, 1e4
    # 1:1 line and 0.5-2.0x band
    line = np.array([lo, hi])
    ax.plot(line, line, color="0.35", lw=1.2, ls="-", zorder=1, label="1:1")
    ax.fill_between(line, 0.5 * line, 2.0 * line, color="0.85", alpha=0.5, zorder=0,
                    label="0.5–2.0× band")

    seen = set()
    for st in stations:
        cls = st.get("auditClass", "swat_nhd_ok")
        color, marker, label = CLASS_STYLE.get(cls, ("0.4", "o", cls))
        ax.scatter(st["nhdHrTotdasqkmKm2"], st["swatplusDrainageAreaKm2"],
                   c=color, marker=marker, s=38, edgecolors="white", linewidths=0.4,
                   zorder=3, label=label if label not in seen else None)
        seen.add(label)

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    ax.set_xlabel("Original NHDPlus HR cumulative drainage  TotDASqKm  (km$^2$)")
    ax.set_ylabel("SWAT+ executable channel area  chandeg.con  (km$^2$)")
    ax.set_title("Peace River HUC-8 (03100101): drainage-area fidelity audit")
    ax.annotate(
        f"n = {s['nMatchedSwatNhd']} matched\nmedian SWAT+/NHD = {s['medianSwatNhdRatio']:.2f}\n"
        f"{s['withinHalfToDouble']}/{s['nMatchedSwatNhd']} within 0.5–2.0×\n"
        f"mainstem offset ≈ +10–17%",
        xy=(0.04, 0.96), xycoords="axes fraction", va="top", ha="left",
        fontsize=9, bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="0.7", alpha=0.9))
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
    ax.grid(True, which="both", ls=":", lw=0.4, alpha=0.5)
    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=200)
    print(f"wrote {OUT}  ({len(stations)} points)")

if __name__ == "__main__":
    main()
