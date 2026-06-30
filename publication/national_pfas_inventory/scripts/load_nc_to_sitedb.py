"""Load NC DEQ ALMP-EC 2023 ambient surface-water PFAS into prod site.db (pfas_* map layer).
Idempotent: clears source_id='nc_deq_almp' first. Station IDs reconciled to the 18 Appendix-1 codes."""
import csv, sqlite3, difflib, datetime
DB="/data/SWATGenXApp/codes/web_application/instance/site.db"
CSV="/data/SWATGenXApp/GenXAppData/pfas_discovery/extracted/nc_deq_almp_2023_long.csv"
SID="nc_deq_almp"; NOW="2026-06-29"; TS=datetime.datetime(2026,6,29,12,0,0).isoformat()
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
def fix(sid): 
    if sid in NC: return sid
    m=difflib.get_close_matches(sid,known,n=1,cutoff=0.8); return m[0] if m else None

agg={}
for r in csv.DictReader(open(CSV)):
    sid=fix(r['station_id'])
    if not sid: continue
    v=float(r['result_ng_L']); d=r['sample_date']
    a=agg.setdefault((sid,r['analyte']),{"n":0,"maxv":0.0,"lv":None,"ld":""})
    a["n"]+=1; a["maxv"]=max(a["maxv"],v)
    if (d or "")>a["ld"]: a["ld"]=d; a["lv"]=v

con=sqlite3.connect(DB,timeout=30); c=con.cursor()
# idempotent clear
for t in ("pfas_observation","pfas_station","pfas_data_source"):
    c.execute(f"DELETE FROM {t} WHERE source_id=?",(SID,))
# register source
c.execute("""INSERT INTO pfas_data_source(source_id,name,authority,agency,state,media,access_method,url,license,
 wqx_submitted,status,retrieved_at,row_count,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
 (SID,'North Carolina DEQ — Ambient Lakes Monitoring (Emerging Compounds) 2023','state',
  'NC DEQ Division of Water Resources, Water Sciences Section','NC','water','vlm_pdf',
  'https://www.deq.nc.gov/water-resources/almp2023ecreportfinalcjsignpdf/open','state open data','no','active',
  NOW,len(agg),"Gemini-vision extraction of Table 2 (untreated reservoir surface water, 18 public-supply reservoirs). "
  "Station IDs reconciled to Appendix-1 codes. NOT in WQP (NC ~empty). HUC8/12 pending spatial join. Namespace 'NC_DEQ_ALMP:'.",
  TS,TS))
# stations
stns={sid for (sid,_) in agg}
for sid in stns:
    nm,lat,lon=NC[sid]
    c.execute("""INSERT INTO pfas_station(site_id,name,lat,lon,state,site_type,huc8,updated_at,huc12,source_id,source_detail)
     VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(f"NC_DEQ_ALMP:{sid}",nm,lat,lon,'NC','Reservoir',None,TS,None,SID,
     'NC DEQ ALMP-EC 2023 untreated surface water'))
# observations
for (sid,an),a in agg.items():
    c.execute("""INSERT INTO pfas_observation(site_id,media,analyte,n_samples,n_detect,max_value,latest_value,
     latest_date,band,source_id,retrieved_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
     (f"NC_DEQ_ALMP:{sid}",'water',an,a["n"],a["n"],a["maxv"],a["lv"],a["ld"],None,SID,NOW))
con.commit()
print("LOADED nc_deq_almp:",
      "stations=",c.execute("select count(*) from pfas_station where source_id=?",(SID,)).fetchone()[0],
      "obs=",c.execute("select count(*) from pfas_observation where source_id=?",(SID,)).fetchone()[0],
      "source_registered=",c.execute("select count(*) from pfas_data_source where source_id=?",(SID,)).fetchone()[0])
print("top NC PFOS by max_value:")
for r in c.execute("""select s.name, o.max_value from pfas_observation o join pfas_station s on o.site_id=s.site_id
  where o.source_id=? and o.analyte='PFOS' order by o.max_value desc limit 5""",(SID,)): print("  ",r)
con.close()
