"""Recall-recovery for low/zero-yield worklist reports.
locate_soil_pages under-detects on scanned/no-text PDFs and on reports whose tables don't trip the
text heuristic. Strategy: render EVERY page (capped) and Gemini-extract each — no reliance on a text
layer. Flat (sid,page) thread pool. Loads a source only if recovery yields MORE rows than what's
already in the DB for that source (never clobber a good load).
Usage: python recover_lowyield.py            # uses the built-in low-yield list
       python recover_lowyield.py sid1 sid2  # specific source_ids
"""
import sys, os, json, sqlite3, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(__file__))
from extract_soil_ri import gem, to_cm, SpendCapExceeded, norm_props
BASE="/data/SWATGenXApp/GenXAppData/pfas_discovery"
RAW=f"{BASE}/raw_pdfs/worklist"
INV=f"{BASE}/pfas_soil_inventory.db"
WL=f"{BASE}/soil_report_worklist.json"
SPENDF=f"{BASE}/gemini_spend.txt"
PAGECAP=160          # max pages to render per report
WORKERS=12
UNIT_TO_NGG={"ng/g":1.0,"ug/kg":1.0,"µg/kg":1.0,"ng/kg":0.001,"mg/kg":1000.0}

# reports that yielded 0 or far-below-expectation in the worklist run
DEFAULT=["ak_dot_homer_soil","ak_dot_fairbanks_intl_sc","ak_dot_nome_sc","ak_dot_deadhorse_pfas",
 "nm_env_holloman_phase1_2022","mt_deq_helena_aasf_si","mt_deq_ftwhh_si","az_deq_luke_si_add1",
 "az_deq_luke_si_add2","mi_egle_biosolids_e_ionia","mi_egle_5312_11mile_kent",
 "epa_sems_100022125_dallas_county","mi_egle_biosolids_a_delhi","wa_ecology_spokane_ipi"]

def npages(pdf):
    try:
        out=subprocess.run(["pdfinfo",pdf],capture_output=True,text=True,timeout=120).stdout
        for ln in out.splitlines():
            if ln.startswith("Pages:"): return int(ln.split()[1])
    except: pass
    return 0

def render_and_extract(args):
    pdf,pg=args
    with tempfile.TemporaryDirectory() as td:
        try:
            subprocess.run(["pdftoppm","-png","-r","170","-f",str(pg),"-l",str(pg),pdf,f"{td}/p"],
                           check=True, timeout=120, stderr=subprocess.DEVNULL)
        except Exception: return pg,[],{}
        png=[f for f in os.listdir(td) if f.endswith(".png")]
        if not png: return pg,[],{}
        recs,u=gem(f"{td}/{png[0]}")
        return pg,(recs or []),(u or {})

def main():
    sids=sys.argv[1:] or DEFAULT
    wl={}
    for p in (WL, WL.replace("worklist.json","worklist2.json")):
        try:
            for w in json.load(open(p)).get("worklist",[]): wl[w["source_id"]]=w
        except FileNotFoundError: pass
    con=sqlite3.connect(INV); con.execute("PRAGMA busy_timeout=60000"); c=con.cursor()
    try: spent=float(open(SPENDF).read().strip())
    except: spent=0.0
    run=0.0
    for sid in sids:
        w=wl.get(sid)
        pdf=f"{RAW}/{sid}.pdf"
        if not w or not os.path.exists(pdf):
            print(f"-- {sid}: no pdf/worklist entry"); continue
        cur=c.execute("select count(*) from pfas_soil_profile where source_id=?",(sid,)).fetchone()[0]
        np=npages(pdf)
        if np==0: print(f"-- {sid}: pdfinfo failed (encrypted/corrupt?)"); continue
        pages=list(range(1,min(np,PAGECAP)+1))
        tasks=[(pdf,pg) for pg in pages]
        rows=[]; tin=tout=0
        try:
            with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                for pg,recs,u in ex.map(render_and_extract, tasks):
                    tin+=u.get("promptTokenCount",0); tout+=u.get("candidatesTokenCount",0)
                    for r in recs:
                        if r.get("analyte") and r.get("value") is not None: rows.append(r)
        except SpendCapExceeded:
            print("ABORT: Gemini spend cap hit — raise cap at https://ai.studio/spend and re-run (idempotent).")
            break
        cost=tin/1e6*0.30+tout/1e6*2.5; run+=cost
        if len(rows)<=cur:
            print(f"NO-GAIN {sid}: recovered {len(rows)} <= existing {cur} (np={np}) ${cost:.3f}")
            continue
        st=w.get("state",""); site=w.get("site",sid); host=w.get("host","worklist")
        c.execute("DELETE FROM pfas_soil_profile WHERE source_id=?",(sid,))
        c.execute("DELETE FROM soil_source WHERE source_id=?",(sid,))
        loaded=0
        for r in rows:
            v=r.get("value"); u=(r.get("units") or "ng/g").lower(); f=UNIT_TO_NGG.get(u)
            if v is None or f is None: continue
            try: val=round(float(v)*f,4)
            except: continue
            ph,toc,moist,tex,bd=norm_props(r)
            c.execute("INSERT INTO pfas_soil_profile (source_id,site_id,boring_id,lat,lon,state,sample_date,depth_top_cm,depth_bottom_cm,horizon,ph,toc,moisture_pct,method,analyte,value,units,qa_flag,mdl,rl,retrieved_at,texture,bulk_density) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (sid,site,str(r.get("sample_id") or "")[:80],r.get("lat"),r.get("lon"),st,
               r.get("sample_date") or None,to_cm(r.get("depth_top"),r.get("depth_unit")),
               to_cm(r.get("depth_bottom"),r.get("depth_unit")),None,ph,toc,moist,
               "direct",r.get("analyte"),val,"ng/g",r.get("qa_flag") or "",None,None,"2026-06-30",tex,bd))
            loaded+=1
        c.execute("INSERT INTO soil_source VALUES(?,?,?,?,?,?,?,?,?,?,?)",
          (sid,site,host,st,"vlm_pdf","gemini_vision_recovered",w["url"],"US public record",loaded,
           f"recovery render-all (np={np} cap={PAGECAP}); ${cost:.4f}","2026-06-29"))
        con.commit()
        print(f"RECOVERED {sid}: {cur} -> {loaded} rows (np={np}) ${cost:.3f}")
    open(SPENDF,"w").write(f"{spent+run:.4f}")
    tot=c.execute("select count(*) from pfas_soil_profile").fetchone()[0]
    print(f"\nrecovery spend ${run:.4f} | cumulative ${spent+run:.4f}")
    print(f"inventory now: {tot} rows")
    con.close()

if __name__=="__main__":
    main()
