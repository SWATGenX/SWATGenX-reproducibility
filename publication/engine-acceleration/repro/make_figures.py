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
FIGDIR = os.path.join(HERE, "figures")
os.makedirs(FIGDIR, exist_ok=True)

plt.rcParams.update({
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})

# ---- Figure: cross-hardware scaling (Table 3) ----
# (The fixed-clock workstation figure was removed: all timings are now AWS-only.)
n = [2, 4, 6, 8, 10, 12, 16, 20]
c8a = [1.66, 2.62, 3.18, 3.56, 3.79, 4.03, 4.40, 4.62]   # AMD Turin 32c
c8i = [1.51, 2.18, 2.62, 2.88, 3.01, 3.15, 3.34, 3.20]   # Intel Granite Rapids 16c x2
c5a = [1.59, 2.34, 2.76, 3.03, 3.20, 3.38, 3.55, 3.38]   # AMD Rome 16c x2

fig, ax = plt.subplots(figsize=(5.4, 3.6))
ax.plot(n, c8a, marker="o", ms=4, lw=1.6, color="#c0392b",
        label="c8a (Turin, 32c)")
ax.plot(n, c8i, marker="s", ms=4, lw=1.6, color="#2c6fbb",
        label="c8i (Granite Rapids, 16c×2)")
ax.plot(n, c5a, marker="^", ms=4, lw=1.6, color="#27ae60",
        label="c5a (Rome, 16c×2)")
# peak markers
ax.annotate("peak 4.62×\n(20 of 32c, climbing)", xy=(20, 4.62), xytext=(13.5, 4.75),
            fontsize=8, color="#c0392b",
            arrowprops=dict(arrowstyle="->", color="#c0392b", lw=0.8))
ax.annotate("16c parts peak,\nregress on SMT", xy=(16, 3.55), xytext=(8.5, 2.0),
            fontsize=8, color="#555",
            arrowprops=dict(arrowstyle="->", color="#555", lw=0.8))
ax.set_xlabel("Worker threads")
ax.set_ylabel("Speedup (each machine's own $1\\rightarrow N$)")
ax.set_xticks(n)
ax.set_ylim(1.2, 5.0)
ax.legend(frameon=False, loc="lower right", fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "Figure_3.png"), dpi=300, bbox_inches="tight")
plt.close(fig)

print("WROTE", os.path.join(FIGDIR, "Figure_3.png"))

# ---- Figure 3: comprehensive speedup configurator (total vs stock single-core) ----
# Anchors: c8a measured stock baseline 217.7s; optimized serial 141.5s (1.54x).
# Non-c8a curves are self-relative parallel scaling, anchored to the optimized-serial
# reference by the ~1.20x parallel-binary N=1 overhead, then x1.54 serial.
SERIAL = 1.54
N1OVR = 1.20

def interp(xs, ys, x):
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + t * (ys[i + 1] - ys[i])
    return ys[-1]

# c8a measured wall times -> P anchored to optimized serial (141.5)
c8a_n = [1, 2, 4, 8, 16]
c8a_full_wall = [170.2, 105.9, 71.1, 56.2, 62.7]
c8a_byte_wall = [171.5, 119.6, 90.6, 79.1, 87.7]
c8a_full_tot = [SERIAL * 141.5 / w for w in c8a_full_wall]
c8a_byte_tot = [SERIAL * 141.5 / w for w in c8a_byte_wall]

# self-relative parallel curves -> total vs stock = SERIAL * (Pself / N1OVR)
# (Workstation curve removed: all timings are AWS-only.)
c8i_n = [1, 2, 4, 6, 8, 10, 12, 16, 20]; c8i_p = [1.00, 1.51, 2.18, 2.62, 2.88, 3.01, 3.15, 3.34, 3.20]
c5a_n = [1, 2, 4, 6, 8, 10, 12, 16, 20]; c5a_p = [1.00, 1.59, 2.34, 2.76, 3.03, 3.20, 3.38, 3.55, 3.38]
c8i_tot = [SERIAL * p / N1OVR for p in c8i_p]
c5a_tot = [SERIAL * p / N1OVR for p in c5a_p]

fig, ax = plt.subplots(figsize=(6.2, 4.0))
ax.axhline(SERIAL, color="#888", lw=1.0, ls=":", zorder=1)
ax.text(20.2, SERIAL, f"  serial only ({SERIAL:.2f}×)", va="center", ha="left", fontsize=7.5, color="#666")
ax.plot(c8a_n, c8a_full_tot, marker="o", ms=4, lw=1.8, color="#c0392b", label="c8a Turin 32c — full")
ax.plot(c8a_n, c8a_byte_tot, marker="o", ms=4, lw=1.6, color="#c0392b", ls="--", label="c8a Turin 32c — byte-identical")
ax.plot(c8i_n, c8i_tot, marker="s", ms=4, lw=1.6, color="#2c6fbb", label="c8i Granite Rapids 16c — full (est.)")
ax.plot(c5a_n, c5a_tot, marker="^", ms=4, lw=1.6, color="#27ae60", label="c5a Rome 16c — full (est.)")
ax.set_xlabel("Cores")
ax.set_ylabel("Total speedup vs. stock single core")
ax.set_xticks([1, 2, 4, 8, 12, 16, 20])
ax.set_xlim(0.5, 24)
ax.set_ylim(1.0, 6.2)
ax.legend(frameon=False, loc="upper left", fontsize=7.5)
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "Figure_5.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("WROTE", os.path.join(FIGDIR, "Figure_5.png"))
