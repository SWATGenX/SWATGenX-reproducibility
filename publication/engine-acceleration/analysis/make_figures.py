#!/usr/bin/env python3
"""Generate the two scaling figures for the engine-acceleration paper.

Data are the exact published table values (results.tex Tables 2-3). Outputs land in
manuscript/figures/ as PNG at 300 dpi (matching the companion paper's artwork format;
titles are omitted and supplied via the LaTeX \\caption, per the C&G artwork guidelines).
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "..", "figures")
os.makedirs(FIGDIR, exist_ok=True)

plt.rcParams.update({
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})

# ---- Figure: cross-hardware scaling (final engine, dedicated AWS instances) ----
# Self-relative speedup (each machine's own t1 -> N). Consistent final-engine re-run,
# one simulated year, daily channel_sd, best of two. (Workstation removed; AWS-only.)
n   = [2, 4, 6, 8, 10, 12, 16, 20, 24]
c8a = [1.70, 2.79, 3.48, 3.95, 4.30, 4.54, 4.90, 5.18, 5.33]   # AMD EPYC "Turin", 32 vCPU
c8i = [1.59, 2.41, 2.93, 3.29, 3.55, 3.75, 4.01, 3.73, 3.74]   # Intel Xeon "Granite Rapids", 32 vCPU
c5a = [1.62, 2.47, 2.89, 3.21, 3.42, 3.60, 3.81, 3.51, 3.58]   # AMD EPYC "Rome", 32 vCPU

fig, ax = plt.subplots(figsize=(5.4, 3.6))
ax.plot(n, c8a, marker="o", ms=4, lw=1.6, color="#c0392b", label="c8a (Turin)")
ax.plot(n, c8i, marker="s", ms=4, lw=1.6, color="#2c6fbb", label="c8i (Granite Rapids)")
ax.plot(n, c5a, marker="^", ms=4, lw=1.6, color="#27ae60", label="c5a (Rome)")
ax.annotate("Turin still climbing\nat 24 threads (5.33×)", xy=(24, 5.33), xytext=(13, 5.2),
            fontsize=8, color="#c0392b",
            arrowprops=dict(arrowstyle="->", color="#c0392b", lw=0.8))
ax.annotate("others peak ~16,\nregress on SMT", xy=(16, 4.01), xytext=(8.5, 2.1),
            fontsize=8, color="#555",
            arrowprops=dict(arrowstyle="->", color="#555", lw=0.8))
ax.set_xlabel("Worker threads")
ax.set_ylabel("Speedup (each machine's own $1\\rightarrow N$)")
ax.set_xticks(n)
ax.set_ylim(1.2, 5.8)
ax.legend(frameon=False, loc="lower right", fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "Figure_3.png"), dpi=300, bbox_inches="tight")
plt.close(fig)

print("WROTE", os.path.join(FIGDIR, "Figure_3.png"))

# ---- Figure: speedup configurator (total vs stock single-core, end-to-end) ----
# Directly measured R0(stock,1 thread) / R6FULL(N) on each dedicated AWS instance.
nn  = [2, 4, 6, 8, 10, 12, 16, 20, 24]
c8a_tot = [2.28, 3.74, 4.66, 5.29, 5.76, 6.09, 6.57, 6.95, 7.14]   # Turin
c8i_tot = [3.32, 5.05, 6.13, 6.88, 7.42, 7.85, 8.40, 7.80, 7.83]   # Granite Rapids
c5a_tot = [2.81, 4.28, 5.00, 5.56, 5.92, 6.23, 6.59, 6.08, 6.20]   # Rome
# c8a byte-identical (routing-serial) mode: directly measured vs-stock on the same box.
byte_n   = [2, 4, 8, 16]
c8a_byte = [1.98, 2.75, 3.37, 3.80]

fig, ax = plt.subplots(figsize=(6.2, 4.0))
ax.plot(nn, c8a_tot, marker="o", ms=4, lw=1.8, color="#c0392b", label="c8a Turin — full wavefront")
ax.plot(nn, c8i_tot, marker="s", ms=4, lw=1.6, color="#2c6fbb", label="c8i Granite Rapids — full")
ax.plot(nn, c5a_tot, marker="^", ms=4, lw=1.6, color="#27ae60", label="c5a Rome — full")
ax.plot(byte_n, c8a_byte, marker="o", ms=3, lw=1.4, color="#c0392b", ls="--",
        label="c8a Turin — byte-identical (routing-serial)")
ax.set_xlabel("Cores")
ax.set_ylabel("Total speedup vs. stock single core")
ax.set_xticks(nn)
ax.set_xlim(1.0, 25)
ax.set_ylim(1.0, 9.0)
ax.legend(frameon=False, loc="upper left", fontsize=7.5)
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "Figure_5.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("WROTE", os.path.join(FIGDIR, "Figure_5.png"))

# =====================================================================
# Figure 1 — command-order level histogram (Peace, 265 levels)
# Object count per topological level from the engine's openmp_waves.out.
# =====================================================================
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

lev_counts = [67616,2055,1228,811,597,468,373,301,243,210,182,154,134,106,97,84,74,65,59,56,53,45,41,40,37,37,35,30,29,29,29,27,24,23,23,22,19,17,16,16,14,13,12,11,11,11,8,7,7,7,7,6,6,6,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,3,3,3,3,3,3,3,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
levels = list(range(1, len(lev_counts) + 1))
n_width1 = sum(1 for c in lev_counts if c == 1)

fig, ax = plt.subplots(figsize=(6.0, 3.6))
ax.bar(levels, lev_counts, width=1.0, color="#2c6fbb", edgecolor="none")
ax.set_yscale("log")
ax.set_xlabel("Topological level (command order)")
ax.set_ylabel("Objects at level (log scale)")
ax.set_xlim(0, len(levels) + 1)
ax.annotate(f"level 1: {lev_counts[0]:,} leaf objects\n(57,998 HRUs + other source nodes)",
            xy=(1, lev_counts[0]), xytext=(33, 18000), fontsize=8.5, color="#c0392b",
            arrowprops=dict(arrowstyle="->", color="#c0392b", lw=0.9))
ax.annotate(f"width-1 main-stem tail\n({n_width1} serial levels)",
            xy=(220, 1), xytext=(120, 12), fontsize=8.5, color="#555",
            arrowprops=dict(arrowstyle="->", color="#555", lw=0.9))
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "Figure_1.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("WROTE", os.path.join(FIGDIR, "Figure_1.png"))

# =====================================================================
# Figure 2 — routing-DAG level wavefront schematic (conceptual)
# =====================================================================
fig, ax = plt.subplots(figsize=(6.6, 3.4))
ax.axis("off")
ax.set_xlim(0, 10); ax.set_ylim(0, 6)

def node(x, y, c="#2c6fbb", r=0.16):
    ax.add_patch(plt.Circle((x, y), r, color=c, zorder=3))
def edge(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=8,
                                 color="#888", lw=1.0, shrinkA=6, shrinkB=6, zorder=2))

# level bands (shaded), narrowing left->right
band_x = [0.5, 2.2, 3.9, 5.6, 7.3]
band_w = [1.4, 1.0, 0.8, 0.7, 0.7]
band_n = ["level 1\n(land phase,\n~58k HRUs)", "level 2", "level 3", "$\\cdots$", "deep main\nstem (width 1)"]
for i, (bx, bw) in enumerate(zip(band_x, band_w)):
    ax.add_patch(FancyBboxPatch((bx - bw/2, 0.6), bw, 4.2, boxstyle="round,pad=0.02",
                 fc="#eef3fb" if i % 2 == 0 else "#f6f8fc", ec="#cfd8e6", lw=0.8, zorder=1))
    ax.text(bx, 0.25, band_n[i], ha="center", va="top", fontsize=7.2, color="#444")

# HRUs at level 1 (many), narrowing to 1 at the tail
ys = [1.4, 2.2, 3.0, 3.8, 4.6]
for y in ys: node(band_x[0], y, "#27ae60")
ax.text(band_x[0], 5.05, "independent\nHRUs (parallel)", ha="center", fontsize=7, color="#27ae60")
for y in [2.0, 3.0, 4.0]: node(band_x[1], y, "#2c6fbb")
for y in [2.4, 3.6]: node(band_x[2], y, "#2c6fbb")
node(band_x[3], 3.0, "#2c6fbb")
node(band_x[4], 3.0, "#c0392b")
# a few edges showing convergence
for y in ys: edge(band_x[0], y, band_x[1], min(max(y, 2.0), 4.0))
for y in [2.0, 3.0, 4.0]: edge(band_x[1], y, band_x[2], 2.4 if y < 3 else 3.6)
for y in [2.4, 3.6]: edge(band_x[2], y, band_x[3], 3.0)
edge(band_x[3], 3.0, band_x[4], 3.0)

ax.text(5.0, 5.7, "one OpenMP parallel region per simulated day; "
        "implicit barrier between levels", ha="center", fontsize=8, style="italic", color="#333")
ax.annotate("", xy=(8.3, 3.0), xytext=(7.9, 3.0),
            arrowprops=dict(arrowstyle="-|>", color="#c0392b", lw=1.4))
ax.text(8.5, 3.0, "outlet", ha="left", va="center", fontsize=7.5, color="#c0392b")
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "Figure_2.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("WROTE", os.path.join(FIGDIR, "Figure_2.png"))

# =====================================================================
# Figure 4 — VTune profile of the final engine at 8 threads
# (180-day window). Left: CPU-time composition. Right: effective work by routine.
# =====================================================================
fig, (axL, axR) = plt.subplots(1, 2, figsize=(7.2, 3.2), gridspec_kw={"width_ratios": [1, 1.25]})

# left: stacked composition, each segment labelled to the right (no legend -> no overlap)
comp = [("Effective (real work)", 929, "#27ae60"),
        ("Spin (barrier idle)", 312, "#f59e0b"),
        ("Overhead", 25, "#94a3b8")]
total = sum(s for _, s, _ in comp)
bottom = 0
centers = {}
for label, sec, col in comp:
    axL.bar(0, sec, bottom=bottom, width=0.5, color=col)
    centers[label] = bottom + sec / 2
    bottom += sec
secmap = {l: s for l, s, _ in comp}
# bold value inside the two large segments
for label in ("Effective (real work)", "Spin (barrier idle)"):
    axL.text(0, centers[label], f"{secmap[label]} s\n({round(100*secmap[label]/total)}%)",
             ha="center", va="center", fontsize=8, color="#0b1220", fontweight="bold")
# name labels to the right; tiny overhead slice gets a leader line + inline value
label_y = {"Effective (real work)": centers["Effective (real work)"],
           "Spin (barrier idle)": centers["Spin (barrier idle)"],
           "Overhead": total + 70}
for label, sec, col in comp:
    arrow = dict(arrowstyle="-", color="#9aa3af", lw=0.8) if label == "Overhead" else None
    txt = label if label != "Overhead" else f"Overhead  {sec} s ({round(100*sec/total)}%)"
    axL.annotate(txt, xy=(0.27, centers[label]), xytext=(0.42, label_y[label]),
                 va="center", ha="left", fontsize=8, color="#333", arrowprops=arrow)
axL.set_xlim(-0.45, 2.1); axL.set_xticks([])
axL.set_ylim(0, total * 1.13)
axL.set_ylabel("CPU-seconds (8 threads)")
axL.text(-0.4, total * 1.11, "(a)", fontsize=10, fontweight="bold", va="top")

# right: effective work by routine
rt = [("sd_channel_control3\n(serial main stem)", 698, "#c0392b"),
      ("hru_control\n(parallel land phase)", 90, "#27ae60"),
      ("command_object /\nru_control (mixed)", 41, "#2c6fbb")]
names = [r[0] for r in rt]; secs = [r[1] for r in rt]; cols = [r[2] for r in rt]
axR.barh(range(len(rt))[::-1], secs, color=cols, height=0.6)
for i, s in enumerate(secs):
    axR.text(s + 12, (len(rt)-1-i), f"{s} s", va="center", fontsize=8)
axR.set_yticks(range(len(rt))[::-1]); axR.set_yticklabels(names, fontsize=7.2)
axR.set_xlabel("Effective CPU-seconds"); axR.set_xlim(0, 800)
axR.text(10, 2.35, "(b)", fontsize=10, fontweight="bold", va="top")
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "Figure_4.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("WROTE", os.path.join(FIGDIR, "Figure_4.png"))
