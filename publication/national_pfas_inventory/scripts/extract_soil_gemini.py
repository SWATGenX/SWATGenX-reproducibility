import json, base64, subprocess, os, urllib.request, time, csv
ROOT="/data/SWATGenXApp/codes"
KEY=json.load(open(f"{ROOT}/ssl_certificate/google-services/gemini_api_key.json"))["gemini_api_key"]
MODEL="models/gemini-2.5-flash"
URL=f"https://generativelanguage.googleapis.com/v1beta/{MODEL}:generateContent?key={KEY}"
PDF="kirtland_ri.pdf"
W="kirtland_soil"; os.makedirs(W,exist_ok=True)

PROMPT=("This image is a page of 'Table 10-2: Summary of Screening Level Exceedances' from a US Air Force "
 "AFFF Remedial Investigation. It reports DEPTH-RESOLVED SOIL PFAS. Extract every analyte row. "
 "The table groups rows under depth-zone sub-headers like 'Surface Soil (0.0 to 1.0 ft bgs)', "
 "'Subsurface Soil (15.0 to 25.0 ft bgs)', and 'Groundwater'. For SOIL rows only (skip Groundwater), return ONLY a JSON array; "
 "one object per analyte per depth-zone per AFFF Release Area:\n"
 '{"afff_area":"e.g. FT013","medium":"surface_soil|subsurface_soil","depth_top_ft":<num>,"depth_bottom_ft":<num>,'
 '"analyte":"PFOS","max_value":<number>,"units":"ug/kg","qa_flag":"J|U|empty","rsl":<number or null>,'
 '"n_exceed":<int or null>,"n_samples":<int or null>,"exceeding_sample":"id or empty"}\n'
 "Parse the depth interval numbers from the sub-header. max_value is the numeric Maximum Detected Concentration "
 "(strip the J/U qualifier into qa_flag; '--' means no value -> skip). Carry afff_area down its rows. SOIL only.")

def gem(png):
    b64=base64.b64encode(open(png,'rb').read()).decode()
    body=json.dumps({"contents":[{"parts":[{"inline_data":{"mime_type":"image/png","data":b64}},{"text":PROMPT}]}],
        "generationConfig":{"temperature":0,"response_mime_type":"application/json"}}).encode()
    req=urllib.request.Request(URL,data=body,headers={"Content-Type":"application/json"})
    r=json.load(urllib.request.urlopen(req,timeout=90))
    return json.loads(r["candidates"][0]["content"]["parts"][0]["text"]), r.get("usageMetadata",{})

subprocess.run(["pdftoppm","-png","-r","200","-f","28","-l","29",PDF,f"{W}/pg"],check=True)
rows=[]; tin=tout=0
for p in sorted(os.listdir(W)):
    if not p.endswith(".png"): continue
    recs,u=gem(f"{W}/{p}"); tin+=u.get("promptTokenCount",0); tout+=u.get("candidatesTokenCount",0)
    for r in recs:
        if r.get("analyte") and r.get("max_value") is not None:
            r["source_id"]="dod_af_kirtland_ri"; r["site"]="Kirtland AFB, NM"
            rows.append(r)
    print(f"  {p}: {len(recs)} soil rows")
cost=tin/1e6*0.30+tout/1e6*2.5
print(f"\nKIRTLAND soil rows: {len(rows)} | est cost ${cost:.4f}")
out="/data/SWATGenXApp/GenXAppData/pfas_discovery/extracted/dod_kirtland_soil_profile.csv"
cols=["source_id","site","afff_area","medium","depth_top_ft","depth_bottom_ft","analyte","max_value","units","qa_flag","rsl","n_exceed","n_samples","exceeding_sample"]
with open(out,"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
print("wrote",out)
print(f"\n{'area':8} {'medium':16} {'depth_ft':9} {'analyte':8} {'ug/kg':>7} flag")
for r in rows[:18]:
    print(f"{r.get('afff_area',''):8} {r.get('medium',''):16} {str(r.get('depth_top_ft'))+'-'+str(r.get('depth_bottom_ft')):9} {r.get('analyte',''):8} {str(r.get('max_value')):>7} {r.get('qa_flag','')}")
