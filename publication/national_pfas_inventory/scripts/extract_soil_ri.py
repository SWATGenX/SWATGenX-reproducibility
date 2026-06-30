"""Generalized depth-resolved SOIL PFAS extractor for RI-report PDFs.
locate soil-by-depth pages (pdftotext) -> render -> Gemini vision -> normalized rows -> inventory DB.
Reusable across NYSDEC/EPA SEMS/DoD reports. Soil-only; excludes water + private wells."""
import json, base64, subprocess, os, urllib.request, urllib.error, re, sqlite3, datetime, sys, tempfile
ROOT="/data/SWATGenXApp/codes"
KEY=json.load(open(f"{ROOT}/ssl_certificate/google-services/gemini_api_key.json"))["gemini_api_key"]
URL=f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={KEY}"
INV="/data/SWATGenXApp/GenXAppData/pfas_discovery/pfas_soil_inventory.db"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
MAXPAGES=30  # per-report cost cap
ANALYTE_RE=re.compile(r"PFOS|PFOA|PFHxS|PFHxA|PFBS|PFBA|PFNA|PFHpA|PFPeA|HFPO|Perfluoro|FTS|FOSAA")
DEPTH_RE=re.compile(r"ft bgs|feet bgs|\bbgs\b|Sample Depth|Depth \(ft|Depth Interval|in bgs|\bft\b.*soil", re.I)
UNIT_RE=re.compile(r"ug/kg|µg/kg|ng/g|mg/kg")

PROMPT=("Page from an environmental Remedial Investigation report. Extract DEPTH-RESOLVED SOIL PFAS only. "
 "Return ONLY a JSON array; one object per analyte per soil sample:\n"
 '{"sample_id":"boring/sample id","depth_top":<num>,"depth_bottom":<num>,"depth_unit":"ft|in|cm",'
 '"analyte":"PFOS","value":<number>,"units":"ug/kg|ng/g|mg/kg","qa_flag":"J|U|empty",'
 '"sample_date":"YYYY-MM-DD or empty","lat":<num or null>,"lon":<num or null>,'
 '"ph":<num or null>,"toc":<num or null>,"toc_unit":"%|mg/kg|g/kg or null",'
 '"moisture_pct":<num or null>,"texture":"<USDA class or grain-size/soil description or null>",'
 '"bulk_density":<num g/cm3 or null>}\n'
 "RULES: SOIL only — SKIP groundwater, surface water, sediment, and ANY private/residential drinking-water-well rows. "
 "Capture depth interval from the row or its sub-header. value numeric only (J/U qualifier -> qa_flag; keep the number even if U). "
 "Skip '--'/blank. If no depth-resolved soil PFAS on the page, return []. "
 "SOIL PROPERTIES: if this page also reports per-sample pH, total organic carbon (TOC/foc — give value + its unit), "
 "moisture/water content (%), soil texture/USDA class/grain-size description, or bulk/dry density for a sample, "
 "attach them to that sample's analyte objects; otherwise leave those fields null. Do NOT invent properties not on the page. "
 "BE EXHAUSTIVE: extract EVERY analyte column for EVERY soil sample/depth on the page (all PFAS incl. ADONA, PMPA, "
 "9Cl-PF3ONS, FOSAAs, fluorotelomers, etc.), including non-detect rows (keep the reported value + qa_flag 'U'). "
 "Do not summarize, deduplicate, or skip rows.")

def norm_props(r):
    """Return (ph, toc_pct, moisture_pct, texture, bulk_density) normalized; TOC -> percent (=foc*100)."""
    def num(x):
        try: return float(x)
        except: return None
    ph=num(r.get("ph")); moist=num(r.get("moisture_pct")); bd=num(r.get("bulk_density"))
    tex=(r.get("texture") or None)
    if isinstance(tex,str): tex=tex.strip()[:60] or None
    toc=num(r.get("toc")); tu=(r.get("toc_unit") or "%").lower()
    if toc is not None:
        if "mg/kg" in tu: toc=toc/10000.0      # mg/kg -> %
        elif "g/kg" in tu: toc=toc/10.0         # g/kg  -> %
        # else already percent
        toc=round(toc,4)
    if ph is not None and not (0<ph<14): ph=None        # sanity
    if moist is not None and not (0<=moist<=100): moist=None
    return ph, toc, moist, tex, bd

class SpendCapExceeded(RuntimeError):
    """Gemini project monthly spend cap hit — retrying is futile, abort the run."""

def gem(png):
    b64=base64.b64encode(open(png,'rb').read()).decode()
    body=json.dumps({"contents":[{"parts":[{"inline_data":{"mime_type":"image/png","data":b64}},{"text":PROMPT}]}],
      "generationConfig":{"temperature":0,"response_mime_type":"application/json"}}).encode()
    import time
    for a in range(4):
        try:
            r=json.load(urllib.request.urlopen(urllib.request.Request(URL,data=body,headers={"Content-Type":"application/json"}),timeout=90))
            return json.loads(r["candidates"][0]["content"]["parts"][0]["text"]), r.get("usageMetadata",{})
        except urllib.error.HTTPError as e:
            try: msg=e.read().decode()[:300]
            except: msg=str(e)
            if e.code==429 and "spending cap" in msg.lower():
                raise SpendCapExceeded(msg)          # fail fast — no point retrying thousands of pages
            if e.code==429:                          # transient rate limit -> exponential backoff
                if a==3: return [],{"_err":msg[:120]}
                time.sleep(5*(a+1)); continue
            if a==3: return [],{"_err":msg[:120]}
            time.sleep(3)
        except Exception as e:
            if a==3: return [],{"_err":str(e)[:120]}
            time.sleep(3)

def locate_soil_pages(pdf):
    txt=subprocess.run(["pdftotext","-layout",pdf,"-"],capture_output=True,text=True,timeout=300).stdout
    pages=txt.split("\f"); hits=[]
    for i,pg in enumerate(pages,1):
        if ANALYTE_RE.search(pg) and UNIT_RE.search(pg) and (DEPTH_RE.search(pg) or "Soil" in pg or "SOIL" in pg):
            # require it look like SOIL not just groundwater
            if UNIT_RE.search(pg):  # soil units present (ug/kg etc; groundwater would be ng/L)
                hits.append(i)
    return hits

def to_cm(v,unit):
    if v is None: return None
    try: v=float(v)
    except: return None
    return round(v*{"ft":30.48,"in":2.54,"cm":1.0}.get((unit or "ft").lower(),30.48),1)

def extract_report(pdf, source_id, site_name, jurisdiction):
    pages=locate_soil_pages(pdf)[:MAXPAGES]
    rows=[]; tin=tout=0
    with tempfile.TemporaryDirectory() as td:
        for pg in pages:
            subprocess.run(["pdftoppm","-png","-r","200","-f",str(pg),"-l",str(pg),pdf,f"{td}/p"],check=True)
            png=[f for f in os.listdir(td) if f.endswith(".png")]
            if not png: continue
            recs,u=gem(f"{td}/{png[0]}"); 
            for f in png: os.remove(f"{td}/{f}")
            tin+=u.get("promptTokenCount",0); tout+=u.get("candidatesTokenCount",0)
            for r in recs:
                if r.get("analyte") and r.get("value") is not None:
                    rows.append(r)
    cost=tin/1e6*0.30+tout/1e6*2.5
    return rows, pages, cost

if __name__=="__main__":
    # validation run on Kirtland (already downloaded)
    pdf=sys.argv[1] if len(sys.argv)>1 else "/tmp/claude-1000/-data-SWATGenXApp-codes/e43d5802-dfac-470a-9b2b-ef83b0cac684/scratchpad/kirtland_ri.pdf"
    rows,pages,cost=extract_report(pdf,"dod_af_kirtland_ri_full","Kirtland AFB","NM")
    print(f"soil-depth pages located: {len(locate_soil_pages(pdf))} (used {len(pages)}: {pages})")
    print(f"extracted soil rows: {len(rows)} | est cost ${cost:.4f}")
    from collections import Counter
    print("analytes:", dict(Counter(r['analyte'] for r in rows)))
    print("sample rows:")
    for r in rows[:10]:
        print(f"  {r.get('sample_id','')[:22]:22} {r.get('depth_top')}-{r.get('depth_bottom')}{r.get('depth_unit','')} {r['analyte']:8} {r['value']} {r.get('units','')} {r.get('qa_flag','')}")
