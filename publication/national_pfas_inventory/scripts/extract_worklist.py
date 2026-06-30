"""Consume soil_report_worklist.json (discovery output): download each verified report PDF,
extract depth-resolved soil PFAS via Gemini vision, normalize, idempotent-load to the inventory DB.
- Skips source_ids already present (no re-cost).
- Skips structured/non-PDF entries (CA EDF .zip etc.) — those have a separate parser.
- Cost-tracked vs $100 budget (cumulative spend persisted to gemini_spend.txt).
Run AFTER any other Gemini batch finishes (avoid SQLite write contention).
"""
import sys, os, json, sqlite3, urllib.request, time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(__file__))
from extract_soil_ri import extract_report, to_cm, SpendCapExceeded, norm_props
BASE="/data/SWATGenXApp/GenXAppData/pfas_discovery"
RAW=f"{BASE}/raw_pdfs/worklist"; os.makedirs(RAW, exist_ok=True)
INV=f"{BASE}/pfas_soil_inventory.db"
WL=(sys.argv[1] if len(sys.argv)>1 and sys.argv[1].endswith(".json")
    else f"{BASE}/soil_report_worklist.json")
SPENDF=f"{BASE}/gemini_spend.txt"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
BUDGET=100.0
UNIT_TO_NGG={"ng/g":1.0,"ug/kg":1.0,"µg/kg":1.0,"ng/kg":0.001,"mg/kg":1000.0}

def prior_spend():
    try: return float(open(SPENDF).read().strip())
    except: return 0.0

def download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest)>1024: return os.path.getsize(dest)
    req=urllib.request.Request(url, headers={"User-Agent":UA,"Accept":"application/pdf,*/*"})
    data=urllib.request.urlopen(req, timeout=600).read()
    open(dest,"wb").write(data); return len(data)

WORKERS=int(os.environ.get("WORKERS","10"))
FORCE=os.environ.get("FORCE","0")=="1"   # re-extract even if source_id already loaded (e.g. property re-pass)

def extract_one(w):
    """Network-bound worker: download + VLM-extract one report. No DB. Returns dict."""
    sid=w["source_id"]; url=w["url"]; site=w.get("site",sid); st=w.get("state","")
    pdf=f"{RAW}/{sid}.pdf"
    sz=download(url, pdf)//1024
    if sz<5:
        return {"sid":sid,"status":"blocked","sz":sz}
    rows,pages,cost=extract_report(pdf, sid, site, st)
    return {"sid":sid,"site":site,"st":st,"url":url,"host":w.get("host","worklist"),
            "rows":rows,"pages":pages,"cost":cost,"sz":sz,"status":"ok"}

def main():
    d=json.load(open(WL)); wl=d.get("worklist",[])
    con=sqlite3.connect(INV); con.execute("PRAGMA busy_timeout=60000"); c=con.cursor()
    existing={r[0] for r in c.execute("select source_id from soil_source")}
    spent=prior_spend(); run_spent=0.0
    done=skipped=failed=0
    # build the to-do list (dedup by URL; skip already-loaded + structured)
    seen_url=set(); todo=[]
    for w in wl:
        sid=w["source_id"]; url=w["url"]
        if sid in existing and not FORCE: skipped+=1; continue
        if url.lower().split("?")[0].endswith((".zip",".csv",".xlsx",".xls",".txt")) or "edf" in sid.lower():
            skipped+=1; continue
        if url in seen_url: skipped+=1; continue
        seen_url.add(url); todo.append(w)
    print(f"to-do {len(todo)} reports ({skipped} skipped) | {WORKERS} workers", flush=True)
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs={ex.submit(extract_one, w): w for w in todo}
        for fut in as_completed(futs):
            w=futs[fut]; sid=w["source_id"]
            try:
                res=fut.result()
            except SpendCapExceeded:
                print(f"ABORT: Gemini spend cap hit at {done} loaded — raise cap at https://ai.studio/spend and re-run (idempotent).", flush=True)
                break
            except Exception as e:
                failed+=1; print(f"ERR {sid}: {str(e)[:140]}", flush=True); continue
            if res["status"]=="blocked":
                failed+=1; print(f"SKIP {sid}: tiny/blocked ({res['sz']}KB)", flush=True); continue
            run_spent+=res["cost"]
            c.execute("DELETE FROM pfas_soil_profile WHERE source_id=?", (sid,))
            c.execute("DELETE FROM soil_source WHERE source_id=?", (sid,))
            loaded=0
            for r in res["rows"]:
                v=r.get("value"); u=(r.get("units") or "ng/g").lower()
                f=UNIT_TO_NGG.get(u)
                if v is None or f is None: continue
                try: val=round(float(v)*f,4)
                except: continue
                ph,toc,moist,tex,bd=norm_props(r)
                c.execute("INSERT INTO pfas_soil_profile (source_id,site_id,boring_id,lat,lon,state,sample_date,depth_top_cm,depth_bottom_cm,horizon,ph,toc,moisture_pct,method,analyte,value,units,qa_flag,mdl,rl,retrieved_at,texture,bulk_density) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (sid, res["site"], str(r.get("sample_id") or "")[:80], r.get("lat"), r.get("lon"), res["st"],
                   r.get("sample_date") or None, to_cm(r.get("depth_top"),r.get("depth_unit")),
                   to_cm(r.get("depth_bottom"),r.get("depth_unit")), None,ph,toc,moist,
                   "direct", r.get("analyte"), val, "ng/g", r.get("qa_flag") or "", None,None,"2026-06-30",tex,bd))
                loaded+=1
            c.execute("INSERT INTO soil_source VALUES(?,?,?,?,?,?,?,?,?,?,?)",
              (sid, res["site"], res["host"], res["st"], "vlm_pdf","gemini_vision", res["url"],
               "US public record", loaded, f"worklist auto; soil pages {res['pages']}; ${res['cost']:.4f}", "2026-06-29"))
            con.commit()
            done+=1
            print(f"OK  {sid}: {res['sz']}KB pages={res['pages']} rows={loaded} ${res['cost']:.4f}", flush=True)
    open(SPENDF,"w").write(f"{spent+run_spent:.4f}")
    tot=c.execute("select count(*) from pfas_soil_profile").fetchone()[0]
    prof=c.execute("select count(*) from (select source_id,site_id from pfas_soil_profile where depth_top_cm is not null group by source_id,site_id having count(distinct depth_top_cm)>1)").fetchone()[0]
    print(f"\n=== worklist run: loaded {done} reports, skipped {skipped}, failed {failed} ===")
    print(f"run spend ${run_spent:.4f} | cumulative ${spent+run_spent:.4f} / ${BUDGET}")
    print(f"inventory now: {tot} soil rows, {prof} multi-depth profiles")
    con.close()

if __name__=="__main__":
    main()
