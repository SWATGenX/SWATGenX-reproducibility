"""Two maps: structured 250 m MODFLOW grid vs the quadtree (DISV) refined grid.
Shows the active domain + the quadtree refinement in the source->discharge corridor.
"""
import numpy as np, flopy, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from flopy.discretization import VertexGrid
from matplotlib_scalebar.scalebar import ScaleBar

ROGUE = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500"
CAL = f"{ROGUE}/MODFLOW_sfr_cal"
OUT = "/data/SWATGenXApp/codes/publication/swatplus-modflow6-coupling/research/multianalyte_spike"
plt.rcParams.update({"font.size": 9, "pdf.fonttype": 42, "savefig.bbox": "tight"})

# structured grid + active domain
sim = flopy.mf6.MFSimulation.load(sim_ws=CAL, verbosity_level=0)
gwf = sim.get_model(); sg = gwf.modelgrid
idom0 = gwf.dis.idomain.array[0]

# DISV grid
gp = np.load(f"{OUT}/disv_gridprops.npy", allow_pickle=True).item()
vg = VertexGrid(vertices=gp["vertices"], cell2d=gp["cell2d"],
                ncpl=gp["ncpl"], nlay=gp["nlay"],
                top=np.asarray(gp["top"], float), botm=np.asarray(gp["botm"], float))
try:
    idom_d = np.load(f"{OUT}/disv_map.npz")["idom_d"][0]
except Exception:
    idom_d = np.ones(gp["ncpl"], dtype=int)

fig, axes = plt.subplots(1, 2, figsize=(9.2, 5.2))

# (a) structured
ax = axes[0]
pmv = flopy.plot.PlotMapView(modelgrid=sg, ax=ax)
am = np.ma.masked_where(idom0 <= 0, idom0.astype(float))
pmv.plot_array(am, cmap="Blues", alpha=0.35, vmin=0, vmax=2)
pmv.plot_grid(lw=0.15, color="0.45")
ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
ax.text(0.0, 1.02, "(a)", transform=ax.transAxes, fontweight="bold", fontsize=11, va="bottom")
ncell = int((idom0 > 0).sum())
ax.text(0.02, 0.02, f"structured 250 m\n{ncell:,} active cells/layer",
        transform=ax.transAxes, fontsize=8, va="bottom",
        bbox=dict(boxstyle="round", fc="white", ec="0.7", alpha=0.9))
ax.add_artist(ScaleBar(1, location="lower right", frameon=False, font_properties={"size": 7}))

# (b) DISV quadtree
ax = axes[1]
pmvd = flopy.plot.PlotMapView(modelgrid=vg, ax=ax)
amd = np.ma.masked_where(idom_d <= 0, idom_d.astype(float))
pmvd.plot_array(amd, cmap="Blues", alpha=0.35, vmin=0, vmax=2)
pmvd.plot_grid(lw=0.12, color="0.45")
ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
ax.text(0.0, 1.02, "(b)", transform=ax.transAxes, fontweight="bold", fontsize=11, va="bottom")
nactive = int((idom_d > 0).sum())
ax.text(0.02, 0.02, f"quadtree (DISV)\n{gp['ncpl']:,} cells/layer\n250 m → 62.5 m (corridor + source)",
        transform=ax.transAxes, fontsize=8, va="bottom",
        bbox=dict(boxstyle="round", fc="white", ec="0.7", alpha=0.9))
ax.add_artist(ScaleBar(1, location="lower right", frameon=False, font_properties={"size": 7}))

# zoom inset on the finest-refined cluster to show the 250->62.5 m quadtree nesting
xc = np.array([row[1] for row in gp["cell2d"]]); yc = np.array([row[2] for row in gp["cell2d"]])
# polygon area per cell (shoelace) to find the smallest (most-refined) cells
vx = {int(v[0]): (float(v[1]), float(v[2])) for v in gp["vertices"]}
areas = np.zeros(gp["ncpl"])
for row in gp["cell2d"]:
    ic = int(row[0]); ivs = [int(v) for v in row[4:]]
    pts = [vx[i] for i in ivs if i in vx]
    if len(pts) >= 3:
        x = np.array([p[0] for p in pts]); y = np.array([p[1] for p in pts])
        areas[ic] = 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
fine = np.argsort(areas)[:200]                       # 200 finest cells
cx, cy = float(np.median(xc[fine])), float(np.median(yc[fine]))
half = 1400.0
axin = ax.inset_axes([0.60, 0.60, 0.38, 0.38])
pmz = flopy.plot.PlotMapView(modelgrid=vg, ax=axin)
pmz.plot_grid(lw=0.3, color="0.3")
axin.set_xlim(cx - half, cx + half); axin.set_ylim(cy - half, cy + half)
axin.set_xticks([]); axin.set_yticks([])
for s in axin.spines.values():
    s.set_edgecolor("#b91c1c"); s.set_linewidth(1.2)
ax.indicate_inset_zoom(axin, edgecolor="#b91c1c", lw=1.0)

fig.patch.set_facecolor("white")
for _ax in axes:
    _ax.set_facecolor("white")
fig.savefig(f"{OUT}/grid_comparison.png", dpi=300, facecolor="white")
fig.savefig(f"{OUT}/grid_comparison.pdf", facecolor="white")
print(f"wrote grid_comparison.png/.pdf | structured {ncell} active, DISV {gp['ncpl']} cells")
