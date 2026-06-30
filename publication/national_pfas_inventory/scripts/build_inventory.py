import csv, sqlite3, difflib, os, datetime
BASE="/data/SWATGenXApp/GenXAppData/pfas_discovery"
EXT=f"{BASE}/extracted"
STAGE=f"{BASE}/pfas_inventory_staging.db"
if os.path.exists(STAGE): os.remove(STAGE)
NOW=datetime.date(2026,6,29).isoformat()

# ---- 18 known NC ALMP stations (Appendix 1: code -> name,lat,lon) ----
NC={'CPF038NSUR':('Lake Mackintosh',36.03892,-79.50370),'CPF002A1SUR':('Reidsville Lake',36.28892,-79.68022),
'CPF089E4SUR':('High Point Lake',35.99615,-79.94499),'CPF089D5SUR':('High Point Reservoir',36.01236,-79.98828),
'CPF007BSUR':('Lake Brandt',36.17123,-79.83965),'CPFLT8SUR':('Lake Townsend',36.18969,-79.73329),
'CPFSCR4SUR':('Lake Burlington',36.12893,-79.40698),'CPFGMR4SUR':('Graham-Mebane Reservoir',36.09976,-79.32872),
'CPFCCR6SUR':('Cane Creek Reservoir',35.94955,-79.24155),'CPFUL6SUR':('University Lake',35.89647,-79.09322),
'CPFBDL1SUR':('Buckhorn Dam Lake',35.54187,-78.99547),'CPFRD4SUR':('Randleman Reservoir',35.86300,-79.82800),
'CPFSC1SUR':('Sandy Creek Reservoir',35.74443,-79.67630),'CPFTR01SUR':('Turner Reservoir',35.76300,-79.45625),
'CPF138BSUR':('Glenville Lake',35.06932,-78.89730),'NEW006ESUR':('ASU Lake',36.23912,-81.67036),
'NEWBTP1SUR':('Blowing Rock Lake',36.142932,-81.672783),'WATBL1SUR':('Buckeye Lake',36.219191,-81.907021)}
known=list(NC)

def reconcile(sid):
    if sid in NC: return sid, "exact"
    m=difflib.get_close_matches(sid, known, n=1, cutoff=0.8)
    return (m[0],"fuzzy") if m else (None,"unresolved")

con=sqlite3.connect(STAGE); c=con.cursor()
# ---- NEW soil-profile table (canonical) ----
c.execute("""CREATE TABLE pfas_soil_profile(
 source_id TEXT, site_id TEXT, boring_id TEXT, lat REAL, lon REAL, state TEXT, sample_date TEXT,
 depth_top_cm REAL, depth_bottom_cm REAL, horizon TEXT, ph REAL, toc REAL, moisture_pct REAL,
 method TEXT, analyte TEXT, value REAL, units TEXT, qa_flag TEXT, mdl REAL, rl REAL, retrieved_at TEXT)""")
# ---- staged copies of prod tables for NC water ----
c.execute("""CREATE TABLE pfas_station_staged(site_id TEXT, name TEXT, lat REAL, lon REAL, state TEXT,
 site_type TEXT, source_id TEXT, source_detail TEXT)""")
c.execute("""CREATE TABLE pfas_observation_staged(site_id TEXT, media TEXT, analyte TEXT, n_samples INT,
 n_detect INT, max_value REAL, latest_value REAL, latest_date TEXT, band TEXT, source_id TEXT, retrieved_at TEXT)""")

# === load USGS NH soil ===
nh=0
for r in csv.DictReader(open(f"{EXT}/usgs_nh_2021_soil_profile_long.csv")):
    c.execute("INSERT INTO pfas_soil_profile VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
      (r['source_id'],r['site_id'],r['boring_id'],r['lat'],r['lon'],r['state'],r['sample_date'],
       r['depth_top_cm'],r['depth_bottom_cm'],r['horizon'],r['ph'],r['toc'],r['moisture_pct'],
       r['method'],r['analyte'],r['value'],r['units'],r['qa_flag'],r['mdl'],r['rl'],NOW)); nh+=1

# === load Kirtland soil (ft->cm; µg/kg == ng/g) ===
kf=0
for r in csv.DictReader(open(f"{EXT}/dod_kirtland_soil_profile.csv")):
    dt=float(r['depth_top_ft'])*30.48 if r['depth_top_ft'] else None
    db=float(r['depth_bottom_ft'])*30.48 if r['depth_bottom_ft'] else None
    c.execute("INSERT INTO pfas_soil_profile VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
      (r['source_id'],r['site'],f"{r.get('afff_area','')}:{r.get('exceeding_sample','') or r.get('medium','')}",
       None,None,'NM',None,dt,db,None,None,None,None,'direct',r['analyte'],
       r['max_value'],'ng/g',r['qa_flag'],None,r.get('rsl'),NOW)); kf+=1

# === NC water: reconcile IDs, aggregate to station x analyte ===
rows=list(csv.DictReader(open(f"{EXT}/nc_deq_almp_2023_long.csv")))
recon={}; agg={}
for r in rows:
    sid,how=reconcile(r['station_id']); recon[r['station_id']]=(sid,how)
    if not sid: continue
    val=float(r['result_ng_L']); d=r['sample_date']
    k=(sid,r['analyte'])
    a=agg.setdefault(k,{"n":0,"maxv":0,"lv":None,"ld":None})
    a["n"]+=1; a["maxv"]=max(a["maxv"],val)
    if a["ld"] is None or (d or "")>a["ld"]: a["ld"]=d; a["lv"]=val
stns=set()
for (sid,an),a in agg.items():
    c.execute("INSERT INTO pfas_observation_staged VALUES(?,?,?,?,?,?,?,?,?,?,?)",
      (sid,'water',an,a["n"],a["n"],a["maxv"],a["lv"],a["ld"],None,'nc_deq_almp',NOW)); stns.add(sid)
for sid in stns:
    nm,lat,lon=NC[sid]
    c.execute("INSERT INTO pfas_station_staged VALUES(?,?,?,?,?,?,?,?)",
      (f"NC_DEQ_ALMP:{sid}",nm,lat,lon,'NC','Reservoir','nc_deq_almp','NC DEQ ALMP-EC 2023 untreated surface water'))
con.commit()

# ---- report ----
print("=== STAGING DB:", STAGE, "===")
print(f"pfas_soil_profile rows: {c.execute('select count(*) from pfas_soil_profile').fetchone()[0]}  (USGS NH {nh} + Kirtland {kf})")
for sid_src in c.execute("select source_id, count(*), count(distinct site_id) from pfas_soil_profile group by source_id"):
    print(f"   {sid_src[0]}: {sid_src[1]} rows, {sid_src[2]} sites")
print(f"soil sites w/ multi-depth profiles: {c.execute('select count(*) from (select site_id from pfas_soil_profile group by site_id having count(distinct depth_top_cm)>1)').fetchone()[0]}")
print(f"\npfas_observation_staged (NC water): {c.execute('select count(*) from pfas_observation_staged').fetchone()[0]} obs across {c.execute('select count(*) from pfas_station_staged').fetchone()[0]} stations")
print("\n=== NC station-ID reconciliation (28 extracted -> 18 known) ===")
from collections import Counter
howc=Counter(v[1] for v in recon.values())
print("  ", dict(howc))
for raw,(sid,how) in sorted(recon.items()):
    if how!="exact": print(f"   {raw:14} -> {sid}  [{how}]")
