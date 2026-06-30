"""User-guide workflow diagram: how data flows through the coupled SWAT+/MODFLOW6
PFAS run, labeled with the actual files. No embedded title (it is a labeled
schematic). Writes guide_workflow.png next to the guide's figures.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(10.5, 6.2)); ax.set_xlim(0, 10.5); ax.set_ylim(0, 6.2); ax.axis("off")

def box(x, y, w, h, title, lines, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                                fc=fc, ec="#333", lw=1.2))
    ax.text(x + w/2, y + h - 0.22, title, ha="center", va="top", fontsize=9.5, fontweight="bold")
    ax.text(x + w/2, y + h - 0.55, "\n".join(lines), ha="center", va="top", fontsize=7.6, color="#222")

def arrow(x1, y1, x2, y2, c, lab="", dy=0.12):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=16, color=c, lw=2))
    if lab:
        ax.text((x1+x2)/2, (y1+y2)/2 + dy, lab, ha="center", fontsize=7.5, color=c, fontweight="bold")

# inputs
box(0.2, 4.6, 2.7, 1.4, "TxtInOut (your model)",
    ["pfas.dat  (compounds)", "pfas_hru.ini  (soil PFAS)", "mf6.con  (turns on MF6)",
     "*.map  (HRU<->cell links)"], "#e8eef7")
# SWAT+ land
box(0.2, 2.4, 2.7, 1.5, "SWAT+ land phase",
    ["daily runoff, ET,", "percolation (sepbtm)", "soil 3-phase PFAS:", "solid + air-water + water"], "#dceed6")
# MODFLOW 6
box(4.0, 2.4, 3.0, 1.7, "MODFLOW 6  (TxtInOut/mf6/)",
    ["GWF flow  (daily)", "GWT transport (monthly)", "SFR streams + SFT PFAS", "Freundlich sorption"], "#f6e3cf")
# outputs
box(8.0, 4.4, 2.3, 1.6, "Surface outputs",
    ["pfas_hru_aa.txt", "channel_pfas_day.txt", "pfas_cha_balance.out"], "#f1e7f6")
box(8.0, 2.2, 2.3, 1.6, "Groundwater outputs",
    ["mf6/pfas.ucn  (conc)", "mf6/pfas.lst  (mass bal)", "MODFLOW_sfr.lst  (flow)"], "#f1e7f6")
# engine summary
box(3.6, 0.3, 3.8, 1.1, "Coupler summary (screen)",
    ["recharge | stream<->aquifer exchange", "PFAS loaded | PFAS discharged"], "#fbe9e9")

arrow(1.55, 4.6, 1.55, 3.9, "#555", "read")
arrow(2.9, 3.15, 4.0, 3.15, "#2a7", "recharge +\nPFAS leached", dy=0.28)
arrow(4.0, 2.75, 2.9, 2.75, "#b33", "baseflow +\nPFAS discharge", dy=-0.42)
arrow(2.9, 3.4, 8.0, 5.1, "#76b", "")
arrow(7.0, 3.0, 8.0, 3.0, "#76b", "")
arrow(5.5, 2.4, 5.5, 1.4, "#a44", "")

ax.text(3.45, 2.98, "DOWN", fontsize=7, color="#2a7", rotation=0, ha="center")
ax.text(3.45, 2.55, "UP", fontsize=7, color="#b33", ha="center")
fig.tight_layout()
fig.savefig("guide_workflow.png", dpi=200, bbox_inches="tight")
print("wrote guide_workflow.png")
