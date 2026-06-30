"""Batch: download verified RI/SI PDFs, extract depth-resolved soil PFAS, load to inventory DB.
Uses extract_soil_ri.extract_report. Idempotent per source_id. Tracks cumulative Gemini spend vs budget."""
import sys, os, json, sqlite3, subprocess, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from extract_soil_ri import extract_report, to_cm
BASE="/data/SWATGenXApp/GenXAppData/pfas_discovery"; RAW=f"{BASE}/raw_pdfs/dod"; os.makedirs(RAW,exist_ok=True)
INV=f"{BASE}/pfas_soil_inventory.db"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
BUDGET=100.0

BATCH=[
 ("nmed_cannon_si_tables","Cannon AFB (AFFF SI soil tables)","NM",
  "https://hwbdocs.env.nm.gov/Cannon%20AFB/2018-08-22%20Final%20Site%20Inspection%20Rpt%20-%20Site%20Inspection%20of%20Aqueous%20Film%20Forming%20Foam%20PFAS/Tables.pdf"),
 ("nmed_cannon_ft008_rfi_2026","Cannon AFB FT008 RFI (2026)","NM",
  "https://hwbdocs.env.nm.gov/Cannon%20AFB/2026-04-29%20RCRA%20facility%20IR,%20FT008/Cannon%20AFB_2025_FT008%20RFI_Rev0_January%202026.pdf"),
 ("nmed_holloman_phase1_2022","Holloman AFB Phase 1 PFAS","NM",
  "https://hwbdocs.env.nm.gov/Holloman%20AFB/2022-06-30%20Phase%201%20PFAS%20Investigation%20Rpt%20(no%20cover%20Ltr).pdf"),
 ("epa_sems_fort_wainwright","Fort Wainwright (AFFF, SEMS)","AK",
  "https://semspub.epa.gov/work/10/100270856.pdf"),
 # name-driven accessible reports (Vahid's idea; via Wayback / state DEQ / home.army.mil mirrors)
 ("dod_army_cavazos_pasi","Fort Cavazos (Hood) PFAS PA/SI","TX",
  "http://web.archive.org/web/20250725155502id_/https://aec.army.mil/Portals/115/PFAS/Hood_PFAS_PA-SI.pdf"),
 ("dod_af_malmstrom_si","Malmstrom AFB PFAS SI","MT",
  "https://deq.mt.gov/files/DEQAdmin/PFAS/FNLMalmstromAFBSIReport.pdf"),
 ("dod_arng_ft_harrison_si","Fort Wm Henry Harrison ARNG PFAS SI","MT",
  "https://deq.mt.gov/Files/DEQAdmin/PFAS/ARNG%20PFAS_Final%20SI%20Report_FTWHH%20(1).pdf"),
 ("dod_army_moore_pasi","Fort Moore (Benning) PFAS PA/SI","GA",
  "https://web.archive.org/web/20250604141742id_/https://aec.army.mil/Portals/115/PFAS/Benning_PASI_RED.pdf"),
 ("dod_army_chaffee_si","Fort Chaffee PFAS SI (pt1)","AR",
  "https://web.archive.org/web/20251207050730id_/https://aec.army.mil/Portals/115/PFAS/FTCH_SI-pt1.pdf"),
 ("dod_army_meade_pasi","Fort Meade PFAS PA/SI","MD",
  "https://home.army.mil/meade/application/files/1016/6558/7315/Fort_Meade_PFAS_Preliminary_Assessment_PASI_Report_Sept2022.pdf"),
]
UNIT_TO_NGG={"ng/g":1.0,"ug/kg":1.0,"µg/kg":1.0,"mg/kg":1000.0}

con=sqlite3.connect(INV); c=con.cursor()
# Cannon tables full Gemini extraction supersedes the partial PFOS+PFOA vision load (nmed_cannon_si)
c.execute("DELETE FROM pfas_soil_profile WHERE source_id='nmed_cannon_si'")
c.execute("DELETE FROM soil_source WHERE source_id='nmed_cannon_si'")
spent=0.0; summary=[]
for sid,site,state,url in BATCH:
    pdf=f"{RAW}/{sid}.pdf"
    try:
        if not os.path.exists(pdf):
            req=urllib.request.Request(url,headers={"User-Agent":UA})
            data=urllib.request.urlopen(req,timeout=300).read()
            open(pdf,"wb").write(data)
        sz=os.path.getsize(pdf)//1024
        rows,pages,cost=extract_report(pdf,sid,site,state)
        spent+=cost
        # idempotent load
        c.execute("DELETE FROM pfas_soil_profile WHERE source_id=?",(sid,))
        c.execute("DELETE FROM soil_source WHERE source_id=?",(sid,))
        loaded=0
        for r in rows:
            v=r.get("value"); u=(r.get("units") or "ng/g").lower()
            f=UNIT_TO_NGG.get(u)
            if v is None or f is None: continue
            c.execute("INSERT INTO pfas_soil_profile VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (sid,site,str(r.get("sample_id") or "")[:80],r.get("lat"),r.get("lon"),state,r.get("sample_date") or None,
               to_cm(r.get("depth_top"),r.get("depth_unit")),to_cm(r.get("depth_bottom"),r.get("depth_unit")),
               None,None,None,None,"direct",r.get("analyte"),round(float(v)*f,4),"ng/g",r.get("qa_flag") or "",None,None,"2026-06-29"))
            loaded+=1
        c.execute("INSERT INTO soil_source VALUES(?,?,?,?,?,?,?,?,?,?,?)",
          (sid,site,"DoD (state mirror)" if "nmed" in sid else "EPA SEMS",state,"vlm_pdf","gemini_vision",url,"US public record",loaded,
           f"Auto-batch; soil-depth pages {pages}; ${cost:.4f}",os.environ.get("D","2026-06-29")))
        con.commit()
        summary.append((sid,sz,len(pages) if isinstance(pages,list) else pages,loaded,round(cost,4)))
        print(f"OK  {sid}: {sz}KB, pages={pages}, rows={loaded}, ${cost:.4f}")
    except Exception as e:
        print(f"ERR {sid}: {str(e)[:160]}")
print(f"\n=== batch done | Gemini spend this run ${spent:.4f} (budget ${BUDGET}) ===")
tot=c.execute("select count(*) from pfas_soil_profile").fetchone()[0]
prof=c.execute("select count(*) from (select site_id from pfas_soil_profile group by site_id having count(distinct depth_top_cm)>1)").fetchone()[0]
print(f"inventory now: {tot} soil rows, {prof} multi-depth profiles, sources:")
for r in c.execute("select source_id, rows, state from soil_source order by source_id"): print("  ",r)
con.close()
