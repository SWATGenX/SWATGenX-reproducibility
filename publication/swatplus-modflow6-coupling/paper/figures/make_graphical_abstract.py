"""Graphical abstract for the SWAT+<->MODFLOW 6 PFAS paper: a conceptual cross-section of the coupled
surface-water + groundwater PFAS pathway. No title (it is a labeled schematic, per WR). WR spec:
531 x 1328 px (h x w). Run: .venv/bin/python make_graphical_abstract.py"""
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, Polygon
from matplotlib.lines import Line2D

W, H = 1328, 531
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
ax.set_xlim(0, 13.28); ax.set_ylim(0, 5.31); ax.axis("off")

# --- land surface (gentle slope, high-left source upland -> low-right stream) ---
xs = np.linspace(0, 13.28, 200)
surf = 4.55 - 0.10*xs - 0.25*np.sin(xs*0.5)
ax.fill_between(xs, surf, 5.31, color="#cfe8c5", zorder=1)           # sky/surface band
ax.plot(xs, surf, color="#5a8f4a", lw=1.6, zorder=3)

# --- vadose zone + aquifer ---
wt = surf - 1.15 - 0.05*xs                                           # water table
ax.fill_between(xs, wt, surf, color="#e9dcc3", zorder=1)             # vadose zone (soil)
ax.fill_between(xs, 0.2, wt, color="#bfe0ef", zorder=1)              # saturated aquifer
ax.plot(xs, wt, color="#2f7fb0", lw=1.2, ls="--", zorder=3)

# --- groundwater PFAS plume (left source spreading right toward stream) ---
gx = np.linspace(1.2, 11.0, 60)
for i, x0 in enumerate(np.linspace(1.4, 2.2, 5)):
    yy = (wt[np.searchsorted(xs, gx)] + 0.2)/2
    a = 0.5*np.exp(-((gx-x0)/3.5)**2)
    ax.scatter(gx, yy - 0.1, s=120*a, c="#d62728", alpha=0.18, zorder=2, edgecolors="none")
ax.plot(1.7, 2.0, "*", color="#d62728", ms=22, mec="k", zorder=5)
ax.text(1.7, 1.55, "Wolverine\nPFAS source", ha="center", va="top", fontsize=8.5, color="#7a1414")

# --- stream channel (right) ---
sx = 11.9
ax.add_patch(Rectangle((sx-0.35, 0.2), 0.7, surf[np.searchsorted(xs, sx)]-0.2,
                       color="#1f6fb2", zorder=4))
ax.text(sx, 5.05, "stream", ha="center", fontsize=9, color="#10456f", fontweight="bold")

# --- arrows: the coupled pathways ---
def arrow(x1, y1, x2, y2, color, lw=2.2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=16,
                                 color=color, lw=lw, zorder=6))
# SWAT+ recharge (down)
for x0 in (4.0, 6.5, 9.0):
    yi = surf[np.searchsorted(xs, x0)]; yw = wt[np.searchsorted(xs, x0)]
    arrow(x0, yi-0.15, x0, yw+0.05, "#3a6b2e", 1.8)
ax.text(6.5, 3.95, "SWAT$^+$ recharge (percolation)", ha="center", fontsize=8.5, color="#3a6b2e")
# surface PFAS runoff to stream (along surface)
arrow(2.2, surf[np.searchsorted(xs,2.2)]+0.05, sx-0.4, surf[np.searchsorted(xs,sx)]+0.05, "#5a8f4a", 1.6)
ax.text(6.8, 4.55, "SWAT$^+$ surface PFAS", ha="center", fontsize=8.5, color="#3a6b2e")
# groundwater plume transport (right, in aquifer)
arrow(3.0, 1.55, 10.6, 1.15, "#d62728", 2.2)
ax.text(6.8, 0.95, "MODFLOW 6 groundwater transport (Freundlich)", ha="center", fontsize=8.5, color="#a11")
# discharge to stream via SFT (up at stream)
arrow(11.1, 1.2, sx-0.4, 2.2, "#7b3fb5", 2.4)
ax.text(10.6, 2.65, "SFT:\ngroundwater\ndischarge\n+ PFAS", ha="center", va="bottom", fontsize=8, color="#5a1f8f")

# --- compartment labels ---
ax.text(0.15, 4.95, "SWAT$^+$ land surface", fontsize=10, fontweight="bold", color="#2f5f22")
ax.text(0.15, 2.55, "MODFLOW 6 aquifer (GWF + GWT)", fontsize=10, fontweight="bold", color="#10456f")
ax.text(0.15, 0.35, "two-way BMI/XMI coupling — one continuous surface-water + groundwater PFAS balance",
        fontsize=8.5, style="italic", color="#444")

plt.tight_layout(pad=0.2)
fig.savefig("graphical_abstract.png", dpi=300, bbox_inches=None)  # >=300 dpi raster for WR
fig.savefig("graphical_abstract.pdf", bbox_inches=None)
print("wrote graphical_abstract.png/.pdf (%dx%d px target)" % (W, H))
