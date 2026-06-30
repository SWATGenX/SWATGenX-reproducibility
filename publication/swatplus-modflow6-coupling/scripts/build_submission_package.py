#!/usr/bin/env python3
"""Assemble the Water Research submission package from the current compiled artifacts.

Maps each main-manuscript figure to its real number (from main.aux) and the actual
graphics file it uses (from the figure environments), so figures_main/ always matches
the typeset manuscript. SI figures are numbered S1..SN in printed (includegraphics) order.
Re-run after any recompile; idempotent.
"""
import os, re, shutil, zipfile

PAPER = os.path.join(os.path.dirname(__file__), "..", "paper")
PAPER = os.path.abspath(PAPER)
ROOT = os.path.dirname(PAPER)
OUT = os.path.join(ROOT, "submission")
FIGDIRS = [os.path.join(PAPER, "figures"), os.path.join(ROOT, "figures")]

DATE = "2026-06-28"  # stamp (Date.now unavailable; keep in sync with build)

def resolve(fname):
    for d in FIGDIRS:
        p = os.path.join(d, fname)
        if os.path.exists(p):
            return p
        # try without/with extension variants
        for ext in (".pdf", ".png"):
            if os.path.exists(p + ext):
                return p + ext
    raise FileNotFoundError(fname)

def label_to_number(auxfile):
    m = {}
    if not os.path.exists(auxfile):
        return m
    for line in open(auxfile):
        g = re.match(r"\\newlabel\{(fig:[^}]+)\}\{\{([^}]+)\}", line)
        if g:
            m[g.group(1)] = g.group(2)
    return m

def figs_in_order(texfiles):
    """Walk the given tex files; yield (label, [graphics_filenames]) per figure env, in order.
    A figure environment may hold several panels (multiple \\includegraphics)."""
    out = []
    for tf in texfiles:
        if not os.path.exists(tf):
            continue
        txt = open(tf).read()
        # split into figure environments (figure, figure*, sidewaysfigure)
        for env in re.finditer(r"\\begin\{(sidewaysfigure|figure\*?)\}(.*?)\\end\{\1\}", txt, re.S):
            body = env.group(2)
            incs = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", body)
            lab = re.search(r"\\label\{(fig:[^}]+)\}", body)
            if incs:
                out.append((lab.group(1) if lab else None, incs))
    return out

def main_section_order():
    main = open(os.path.join(PAPER, "main.tex")).read()
    order = re.findall(r"\\input\{(sections/[^}]+)\}", main)
    return [os.path.join(PAPER, s + (".tex" if not s.endswith(".tex") else "")) for s in order]

def short(label):
    return label.split(":", 1)[1] if label and ":" in label else (label or "fig")

def clean(d):
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)

os.makedirs(OUT, exist_ok=True)
fmain = os.path.join(OUT, "figures_main"); clean(fmain)
fsi = os.path.join(OUT, "figures_SI"); clean(fsi)

def stem(fname):
    return os.path.splitext(os.path.basename(fname))[0]

def export(figs, outdir, prefix, numfor):
    """Copy each figure (and its panels) to outdir as <prefix><N>[_panel]_<name>.<ext>."""
    manifest = []
    for i, (label, panels) in enumerate(figs, 1):
        n = numfor(label, i)
        name = short(label) if label else stem(panels[0])
        multi = len(panels) > 1
        for j, fname in enumerate(panels):
            src = resolve(fname)
            ext = os.path.splitext(src)[1]
            tag = chr(ord('a') + j) if multi else ""
            pn = short(label) if label else stem(fname)
            dst = os.path.join(outdir, f"{prefix}{n}{('_'+tag) if tag else ''}_{pn}{ext}")
            shutil.copy2(src, dst)
            disp = f"{prefix}{n}{tag}"
            manifest.append((disp, n, label, os.path.basename(src), os.path.basename(dst)))
            print(f"  {disp:>7}  {pn:30s} <- {os.path.basename(src)}")
    return manifest

# ---- main figures: number from aux, file(s) from figure env ----
num = label_to_number(os.path.join(PAPER, "main.aux"))
print("MAIN FIGURES")
manifest_main = export(figs_in_order(main_section_order()), fmain, "Figure_",
                       lambda label, i: num.get(label, str(i)))

# ---- SI figures: number S1..SN in printed order ----
print("SI FIGURES")
manifest_si = export(figs_in_order([os.path.join(PAPER, "supplementary.tex")]), fsi, "Figure_S",
                     lambda label, i: str(i))

# ---- top-level deliverables ----
copies = [
    ("main.pdf", "manuscript.pdf"),
    ("supplementary.pdf", "supplementary_material.pdf"),
    ("cover_letter.pdf", "cover_letter.pdf"),
    ("figures/graphical_abstract.pdf", "graphical_abstract.pdf"),
    ("figures/graphical_abstract.png", "graphical_abstract_300dpi.png"),
    ("highlights.txt", "highlights.txt"),
]
for src, dst in copies:
    s = os.path.join(PAPER, src)
    if os.path.exists(s):
        shutil.copy2(s, os.path.join(OUT, dst))
        print(f"  copied {dst}")
    else:
        print(f"  WARN missing {src}")

# ---- LaTeX source (buildable tree: tex + bib + bbl + figures + build script) ----
latex_out = os.path.join(OUT, "latex_source"); clean(latex_out)
TEX_FILES = ["main.tex", "supplementary.tex", "preamble-common.tex", "cover_letter.tex",
             "si_param_table.tex", "si_perreach_table.tex", "references.bib",
             "main.bbl", "supplementary.bbl", "build_pdfs.sh"]
for f in TEX_FILES:
    s = os.path.join(PAPER, f)
    if os.path.exists(s):
        shutil.copy2(s, os.path.join(latex_out, f))
os.makedirs(os.path.join(latex_out, "sections"), exist_ok=True)
for f in sorted(os.listdir(os.path.join(PAPER, "sections"))):
    if f.endswith(".tex"):
        shutil.copy2(os.path.join(PAPER, "sections", f), os.path.join(latex_out, "sections", f))
# figures: copy paper/figures + EVERY referenced figure (some live in ../figures, e.g.
# conceptual_model.pdf), so the project compiles standalone (graphicspath includes figures/)
fig_dst = os.path.join(latex_out, "figures"); os.makedirs(fig_dst, exist_ok=True)
for f in os.listdir(os.path.join(PAPER, "figures")):
    fp = os.path.join(PAPER, "figures", f)
    if os.path.isfile(fp):
        shutil.copy2(fp, os.path.join(fig_dst, f))
refd = set()
for _lbl, panels in figs_in_order(main_section_order() + [os.path.join(PAPER, "supplementary.tex")]):
    refd.update(panels)
for fn in refd:
    try:
        src = resolve(fn)
    except FileNotFoundError:
        print(f"  WARN figure not found: {fn}"); continue
    dst = os.path.join(fig_dst, os.path.basename(src))
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
n_sec = len([x for x in os.listdir(os.path.join(latex_out, "sections")) if x.endswith(".tex")])
n_fig = len([x for x in os.listdir(os.path.join(latex_out, "figures"))])
print(f"  latex_source/ bundled ({n_sec} section files + tex/bib/bbl + {n_fig} figures)")

# ---- README ----
readme = [f"""WATER RESEARCH SUBMISSION PACKAGE
Watershed-scale PFAS fate and transport across surface water and groundwater:
a two-way coupled SWAT+/MODFLOW 6 model
Assembled {DATE}

CONTENTS
  manuscript.pdf                 main manuscript (line-numbered, double-spaced)
  supplementary_material.pdf     supplementary information
  cover_letter.pdf               cover letter to the Editor
  graphical_abstract.pdf         graphical abstract (vector)
  graphical_abstract_300dpi.png  graphical abstract (>=300 dpi)
  highlights.txt                 highlights (<=85 chars each)
  figures_main/                  main figures, each as its own file (printed order)
  figures_SI/                    supplementary figures (printed order)
  latex_source/                  full buildable LaTeX project (tex + bib + bbl + figures)

MAIN FIGURE ORDER (matches the manuscript)"""]
seen = set()
for disp, n, label, srcf, dstf in manifest_main:
    if n in seen:
        continue
    seen.add(n)
    readme.append(f"  Figure {n:>2}  {short(label) if label else srcf}")
readme.append("\nSUPPLEMENTARY FIGURE ORDER")
seen = set()
for disp, n, label, srcf, dstf in manifest_si:
    if n in seen:
        continue
    seen.add(n)
    readme.append(f"  Figure S{n:<3} {short(label) if label else srcf}")
readme.append("""
REMAINING -- AUTHOR DECISIONS BEFORE SUBMITTING
  1. Length: trim main text if desired (WR asks for conciseness, no hard cap).
  2. Verify the "~150 m DEM bias" figure in methods-modflow-generation.tex.
  3. (Optional) 3-5 suggested reviewers for Editorial Manager -- not required.
  4. Final read-through.
""")
open(os.path.join(OUT, "README.txt"), "w").write("\n".join(readme))
print("  wrote README.txt")

# ---- zip ----
zipname = os.path.join(ROOT, f"WaterResearch_submission_{DATE}.zip")
if os.path.exists(zipname):
    os.remove(zipname)
with zipfile.ZipFile(zipname, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(OUT):
        for f in files:
            full = os.path.join(root, f)
            z.write(full, os.path.relpath(full, OUT))
print(f"\nWROTE {zipname}")
print(f"  {len(manifest_main)} main figures, {len(manifest_si)} SI figures")
