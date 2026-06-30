"""Render the conceptual-model flowchart from its HTML source to a high-res PNG
and a vector PDF for the manuscript and the user guide. The editable source is
'PFAS Coupled Model.html'; this script just rasterizes/prints it via headless
Chromium so the figure is reproducible.  Run: python render_conceptual.py
"""
import pathlib, os
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
SRC = (HERE / "PFAS Coupled Model.html").as_uri()

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox"])
    # taller viewport so the centred card + its overflowing connector lines are not clipped
    pg = b.new_page(viewport={"width": 1760, "height": 1360}, device_scale_factor=3)
    pg.goto(SRC, wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(3500)                      # let the bundler render
    pg.add_style_tag(content="html,body{background:#ffffff !important;}")
    # Grow the diagram card so the dashed connector lines (overflow:visible SVG) stay on the
    # cream background instead of being clipped at the card edge. Fonts are left at their
    # native sizes (the boxes are tightly spaced -- ~16 px apart -- so a font bump overflows;
    # legibility comes from the full-page landscape placement in the LaTeX instead).
    pg.evaluate("""() => {
        let card=null,a=0;
        for(const el of document.querySelectorAll('div')){const r=el.getBoundingClientRect();
          if(r.width>1600&&r.width<1760&&r.height>1000&&r.width*r.height>a){a=r.width*r.height;card=el;}}
        if(card){ const r=card.getBoundingClientRect();
          card.style.height=(r.height+70)+'px'; card.style.width=(r.width+40)+'px';
        }
    }""")
    pg.wait_for_timeout(500)                        # let the reflow settle
    box = pg.evaluate("""() => {
        let best=null,a=0;
        for(const el of document.querySelectorAll('div')){const r=el.getBoundingClientRect();
          if(r.width>900&&r.height>500&&r.width<1820&&r.width*r.height>a){a=r.width*r.height;best=el;}}
        const r=best.getBoundingClientRect();
        // small symmetric pad to guarantee no edge clipping of connector lines
        return {x:Math.max(0,r.x-12),y:Math.max(0,r.y-12),width:r.width+24,height:r.height+24};
    }""")
    pg.screenshot(path=str(HERE / "conceptual_model.png"), clip=box)
    pg.pdf(path=str(HERE / "conceptual_model.pdf"),
           width=f"{box['width']/96}in", height=f"{box['height']/96}in",
           print_background=True, margin={"top":"0","bottom":"0","left":"0","right":"0"})
    b.close()
print("wrote conceptual_model.png + conceptual_model.pdf")
