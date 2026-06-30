"""Generate figures for the national groundwater inventory data paper from the real measured data.
Outputs PDF + PNG into paper/figures/. Re-run after calibration/triage updates."""
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
CAL = os.path.join(HERE, "..", "pdf_extraction_demo", "calibration")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.size": 9, "font.family": "serif", "axes.linewidth": 0.7})


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"), bbox_inches="tight", dpi=200)
    plt.close(fig)


# ---- Figure 1: calibration — per-state LLM/VLM split (the headline result) ----
cards = [json.load(open(f))["card"] for f in glob.glob(os.path.join(CAL, "*_card.json"))]
cards.sort(key=lambda c: c["raster_pct_VLM"])
st = [c["state"] for c in cards]
llm = [c["text_layer_pct_LLM"] for c in cards]
vlm = [c["raster_pct_VLM"] for c in cards]
# tokens/log per state, blended from the text/raster mix at the paper's rates
# (text-layer LLM ~1,800 tok/log; VLM raster ~1,000 tok/log). Provider-independent, unlike $.
TOK_TEXT, TOK_VLM = 1800.0, 1000.0
tok = [c["text_layer_pct_LLM"] / 100 * TOK_TEXT + c["raster_pct_VLM"] / 100 * TOK_VLM for c in cards]
haspdf = [c["has_pdf_pct"] for c in cards]

fig, ax = plt.subplots(figsize=(6.5, 3.4))
y = range(len(st))
ax.barh(y, llm, color="#2c7fb8", label="text-layer (cheap LLM route)")
ax.barh(y, vlm, left=llm, color="#e6843c", label="raster scan (vision model)")
ax.set_yticks(list(y)); ax.set_yticklabels(st)
ax.set_xlabel("share of well logs (\\%)")
ax.set_xlim(0, 119)
for i, t in enumerate(tok):
    ax.text(102, i, f"{t:,.0f} tok", va="center", fontsize=7.5, color="#333")
ax.text(102, len(st) - 0.3, "tokens/log", fontsize=7.5, color="#333", style="italic")
# every bar is stacked to 100%, so there is no empty space inside the axes -> put the legend
# ABOVE the plot (title removed; it lives in the LaTeX caption per the figures-no-titles rule).
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=2, fontsize=8, frameon=False)
fig.tight_layout()
save(fig, "Fig4_calibration")

# ---- Figure 2: availability census — initial surface audit vs. after systematic probing ----
# Both states (48) and wells (13.4M) are conserved across the reclassification, so we show the
# before/after directly: the headline finding is that probing moves ~3.7M wells from B (vision) to A (free).
cats = ["A: machine-readable\nlithology (free)", "B: PDF-only\nlithology (vision)", "C: no digital\nlithology"]
init_states, fin_states = [8, 26, 14], [17, 13, 18]
init_wells, fin_wells = [3.2, 7.7, 2.5], [7.0, 4.0, 2.4]
INIT, FIN = "#c2c2c2", "#2c7fb8"
xs = [0, 1, 2]; wd = 0.38
fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.6, 3.0))
for ax, init, fin, fmt, ylab, pad in [
        (a1, init_states, fin_states, lambda v: f"{v}", "CONUS states", 0.5),
        (a2, init_wells, fin_wells, lambda v: f"{v}M", "wells (millions)", 0.12)]:
    b1 = ax.bar([x - wd / 2 for x in xs], init, wd, color=INIT, label="initial surface audit")
    b2 = ax.bar([x + wd / 2 for x in xs], fin, wd, color=FIN, label="after systematic probing")
    for bars, vals in ((b1, init), (b2, fin)):
        for rect, v in zip(bars, vals):
            ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height() + pad, fmt(v),
                    ha="center", va="bottom", fontsize=7)
    ax.set_ylabel(ylab); ax.set_xticks(xs); ax.set_xticklabels(cats, fontsize=6.6)
    ax.set_ylim(0, max(init + fin) * 1.18)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
a1.text(0.02, 1.04, "(a)", transform=a1.transAxes, fontsize=9, weight="bold")
a2.text(0.02, 1.04, "(b)", transform=a2.transAxes, fontsize=9, weight="bold")
handles, labels = a1.get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=2, fontsize=7.5, frameon=False,
           bbox_to_anchor=(0.5, 1.02))
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "Fig2_census")

# ---- Figure 3: the subsurface-data tradeoff (schematic from §1.1) ----
# Two axes the 1-D spectrum couldn't carry: spatial availability vs. depth detail. The existing
# sources sit on a tradeoff frontier (coarse-everywhere <-> exquisite-nowhere); depth-resolved
# driller's logs break it by occupying the otherwise-empty abundant+detailed quadrant.
from matplotlib.patches import Rectangle  # noqa: E402
fig, ax = plt.subplots(figsize=(6.5, 4.6))
ax.set_xlim(0, 10); ax.set_ylim(0, 10)

# colour scheme follows the rest of the paper: orange = driller's logs / THIS WORK (the hero),
# blue = the map-based alternative, grey = research boreholes (sparse). highlight the target quadrant.
ORANGE, BLUE, GREY = "#e6843c", "#2c7fb8", "#969696"
ax.add_patch(Rectangle((5.0, 5.0), 5.0, 5.0, facecolor="#fdf0e3", edgecolor="none", zorder=0))

# each entry: marker (x,y), size~abundance, colour; label block anchored in its own clear region
pts = [
    dict(x=1.6, y=8.6, s=60, col=GREY, title="Exquisite, nowhere",
         sub="research boreholes\n(USGS DS1058 $n$=2; East River $n$=4)",
         lx=0.4, ly=7.9, ha="left"),
    dict(x=7.7, y=7.3, s=1300, col=ORANGE, title="Abundant, depth-resolved",
         sub="state driller's logs (millions)\nharmonized by THIS WORK",
         lx=7.7, ly=6.0, ha="center"),
    dict(x=8.2, y=1.7, s=380, col=BLUE, title="Coarse, everywhere",
         sub="surface lithology / permeability maps\n(GLiM, GLHYMPS; Moosdorf 2010)",
         lx=9.8, ly=3.3, ha="right"),
]
for p in pts:
    ax.scatter([p["x"]], [p["y"]], s=p["s"], color=p["col"], edgecolor="#333",
               linewidth=0.9, zorder=3, alpha=0.95)
    ax.text(p["lx"], p["ly"], p["title"], ha=p["ha"], va="top",
            fontsize=8.4, weight="bold", color="#222", zorder=4)
    ax.text(p["lx"], p["ly"] - 0.46, p["sub"], ha=p["ha"], va="top",
            fontsize=6.8, color="#555", zorder=4)

# axes as labelled arrows; no box, no embedded title (title lives in the LaTeX caption)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.annotate("", xy=(10, 0), xytext=(0, 0),
            arrowprops=dict(arrowstyle="-|>", color="#444", lw=1.1))
ax.annotate("", xy=(0, 10), xytext=(0, 0),
            arrowprops=dict(arrowstyle="-|>", color="#444", lw=1.1))
ax.set_xlabel("Spatial availability  (nowhere $\\rightarrow$ everywhere)", fontsize=8.5)
ax.set_ylabel("Subsurface detail  (coarse $\\rightarrow$ depth-resolved)", fontsize=8.5)
ax.set_xticks([]); ax.set_yticks([])
save(fig, "Fig1_spectrum")

print("figures written to", FIG)
print("states in fig1:", st)

# ---- Figures 4-5: large-n (1000/state) VLM yield + hydraulic-field coverage ----
EV = os.path.join(HERE, "eval_results", "vlm_eval_6state.json")
if os.path.exists(EV):
    ev = json.load(open(EV))
    sts = sorted(ev, key=lambda s: -ev[s]["success_rate_of_attempted"])
    # Fig 4: lithology success rate per state
    fig, ax = plt.subplots(figsize=(5.2, 2.8))
    ax.bar(sts, [ev[s]["success_rate_of_attempted"] for s in sts], color="#31a354")
    for i, s in enumerate(sts):
        ax.text(i, ev[s]["success_rate_of_attempted"] + 1, f"{ev[s]['success_rate_of_attempted']:.0f}", ha="center", fontsize=8)
    ax.set_ylabel("lithology recovery (\\%)"); ax.set_ylim(0, 105)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    save(fig, "Fig5_yield")
    # Fig 5: hydraulic-field coverage heatmap
    flds = ["static_water_level_ft", "yield_gpm", "screen_top_ft", "drawdown_ft", "pump_rate_gpm", "specific_capacity_gpm_per_ft"]
    lbl = ["SWL", "yield", "screen", "drawdown", "pump rate", "spec. cap."]
    import numpy as np
    M = np.array([[ev[s]["hydraulic_field_fill_pct"].get(f, 0) for f in flds] for s in sts])
    fig, ax = plt.subplots(figsize=(5.6, 2.8))
    im = ax.imshow(M, cmap="YlOrRd", aspect="auto", vmin=0, vmax=70)
    ax.set_xticks(range(len(flds))); ax.set_xticklabels(lbl, fontsize=7.5, rotation=20, ha="right")
    ax.set_yticks(range(len(sts))); ax.set_yticklabels(sts, fontsize=8)
    for i in range(len(sts)):
        for j in range(len(flds)):
            ax.text(j, i, f"{M[i,j]:.0f}", ha="center", va="center", fontsize=7,
                    color="black" if M[i, j] < 45 else "white")
    ax.set_title("Hydraulic-field coverage (\\% of documents), n=1000/state", fontsize=8.5)
    fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02, label="\\% filled")
    save(fig, "Fig6_hydraulic")
    print("eval figures written")
