"""QA gate 5: analyte-name normalization for pfas_soil_profile.
Adds/refreshes column `analyte_canon` (canonical abbreviation) WITHOUT destroying the raw `analyte`
string (provenance). Folds full chemical names, case variants, and family notations to one canonical
token per compound. Preserves isomer prefixes (L-/Br-/n-) as distinct canonical analytes to avoid
double-counting linear+branched against a reported total. Reports any strings it could not map.
"""
import sqlite3, re, sys, os
INV="/data/SWATGenXApp/GenXAppData/pfas_discovery/pfas_soil_inventory.db"

# canonical case for each known abbreviation (key = uppercased, hyphen/space-stripped)
ABBR={
 "PFOS":"PFOS","PFOA":"PFOA","PFBS":"PFBS","PFHXS":"PFHxS","PFNA":"PFNA","PFHPA":"PFHpA",
 "PFHXA":"PFHxA","PFDA":"PFDA","PFBA":"PFBA","PFPEA":"PFPeA","PFTRDA":"PFTrDA","PFTRA":"PFTrDA",
 "PFTRIDA":"PFTrDA","PFTRIA":"PFTrDA","PFDOA":"PFDoA","PFDODA":"PFDoA","PFUNA":"PFUnA",
 "PFUDA":"PFUnA","PFUNDA":"PFUnA","PFUNDCA":"PFUnA","PFTEDA":"PFTeDA","PFTA":"PFTeDA","PFTEA":"PFTeDA",
 "PFOSA":"PFOSA","FOSA":"PFOSA","PFPES":"PFPeS","PFHPS":"PFHpS","PFDS":"PFDS","PFDCS":"PFDS",
 "PFNS":"PFNS","PFDOS":"PFDoS","PFHXDA":"PFHxDA","PFODA":"PFODA","PFMPA":"PFMPA","PFMBA":"PFMBA",
 "PFEESA":"PFEESA","PFPRA":"PFPrA","PFPA":"PFPeA","PFBTA":"PFBA","PFNDCA":"PFDA","PFDOA2":"PFDA",
 "NFDHA":"NFDHA","ADONA":"ADONA","DONA":"ADONA","HFPODA":"HFPO-DA","GENX":"HFPO-DA",
 "NETFOSAA":"NEtFOSAA","NMEFOSAA":"NMeFOSAA","ETFOSAA":"NEtFOSAA","MEFOSAA":"NMeFOSAA",
 "NETFOSA":"NEtFOSA","NMEFOSA":"NMeFOSA","ETFOSA":"NEtFOSA","MEFOSA":"NMeFOSA",
 "NETFOSE":"NEtFOSE","NMEFOSE":"NMeFOSE","ETFOSE":"NEtFOSE","MEFOSE":"NMeFOSE",
 "NETFOSAE":"NEtFOSE","NMEFOSAE":"NMeFOSE","NETFOSF":"NEtFOSE",
 "9CLPF3ONS":"9Cl-PF3ONS","11CLPF3OUDS":"11Cl-PF3OUdS","TFSI":"TFSI","PFEESA2":"PFEESA",
}
# full chemical names (lowercased, parenthetical removed, 'acid'/punct-insensitive) -> canonical
FULL={
 "perfluorooctanesulfonic":"PFOS","perfluorooctanesulfonate":"PFOS","perfluorooctanoic":"PFOA",
 "perfluorobutanesulfonic":"PFBS","perfluorobutanesulfonate":"PFBS","perfluorobutanoic":"PFBA",
 "perfluorobutyric":"PFBA","perfluorohexanesulfonic":"PFHxS","perfluorohexanesulfonate":"PFHxS",
 "perfluorohexanoic":"PFHxA","perfluorononanoic":"PFNA","perfluorononanesulfonic":"PFNS",
 "perfluoroheptanoic":"PFHpA","perfluoroheptanesulfonic":"PFHpS","perfluoropentanoic":"PFPeA",
 "perfluoropentanesulfonic":"PFPeS","perfluorodecanoic":"PFDA","perfluorodecanesulfonic":"PFDS",
 "perfluorodecanesulfonate":"PFDS","perfluoroundecanoic":"PFUnA","perfluorododecanoic":"PFDoA",
 "perfluorododecanesulfonic":"PFDoS","perfluorotridecanoic":"PFTrDA","perfluorotetradecanoic":"PFTeDA",
 "perfluorohexadecanoic":"PFHxDA","perfluorooctadecanoic":"PFODA","perfluorooctanesulfonamide":"PFOSA",
 "perfluorooctanesulphonamide":"PFOSA","perfluorohexanesulfonate":"PFHxS",
 "nonafluoro36dioxaheptanoic":"NFDHA","perfluoro3methoxypropanoic":"PFMPA","perfluoro4methoxybutanoic":"PFMBA",
 "perfluoro2ethoxyethanesulfonic":"PFEESA","perfluoro2ethoxyethanesulfonicacid":"PFEESA",
 "48dioxa3hperfluorononanoic":"ADONA","hexafluoropropyleneoxidedimer":"HFPO-DA",
 "hexafluoropropyleneoxidedimeracid":"HFPO-DA",
 "netfose":"NEtFOSE","nmefose":"NMeFOSE",
 "nethylperfluorooctanesulfonamidoacetic":"NEtFOSAA","nmethylperfluorooctanesulfonamidoacetic":"NMeFOSAA",
 "nethylperfluoro1octanesulfonamido":"NEtFOSA","nmethylperfluoro1octanesulfonamido":"NMeFOSA",
 "nethylperfluoro1octanesulfonamide":"NEtFOSA","nmethylperfluoro1octanesulfonamide":"NMeFOSA",
 "nethylperfluorooctanesulfonamidothanol":"NEtFOSE","nmethylperfluorooctanesulfonamidothanol":"NMeFOSE",
 "2nmethylperfluoro1octanesulfonamidoethanol":"NMeFOSE","2nethylperfluoro1octanesulfonamidoethanol":"NEtFOSE",
 "perfluoro2ethoxyethanesulfonic":"PFEESA","perfluoroethoxyethanesulfonic":"PFEESA",
 "tetrafluoroheptafluoropropoxypropanoic":"HFPO-DA","heptafluoropropoxy":"HFPO-DA",
}
# extra abbrevs incl. F-53B and FOSE variants
ABBR.update({"9CLPF3ONS":"9Cl-PF3ONS","11CLPF3OUDS":"11Cl-PF3OUdS","NETFOSAE":"NEtFOSE",
 "NETFOSF":"NEtFOSA","NMEFOSF":"NMeFOSA"})
# isomer prefix only — NOT the N- of N-Ethyl/N-Methyl substituents; n-isomer must precede PF
PREFIX=re.compile(r"^(L|Br|lin|linear|branched)[-\s]|^n-(?=PF)", re.I)
XY=re.compile(r"(\d+:\d+)")  # fluorotelomer chain notation
ABBR_PAT=re.compile(r"^(PF[A-Z0-9]{2,7}|N?[EM]e?FOSA{1,2}E?|FOSA|HFPO-?DA|ADONA|DONA|GENX|NFDHA|PFEESA|TFSI|\d+:\d+\s?FT[SC]A?)$", re.I)

def normfull(s):
    return re.sub(r"[^a-z0-9]","", s.lower())

def canon(raw):
    s=raw.strip().replace("Ñ","n").replace("ñ","n")  # OCR unicode fix (PFUÑA)
    if not s or s.upper() in ("PFAS","TOTAL PFAS","PFAS, TOTAL (6)","PFOS/PFOA (COMBINED)"):
        return None  # aggregate/non-specific
    pre=""
    m=PREFIX.match(s)
    if m:
        p=(m.group(1) or "n").lower(); pre={"l":"L-","br":"Br-","n":"n-","lin":"L-","linear":"L-","branched":"Br-"}.get(p,"n-")
        s=s[m.end():].strip()
    s=re.sub(r"^(total|sum of)\s+","",s,flags=re.I).strip()
    s=re.sub(r"\s*-\s*SPLP$","",s,flags=re.I)
    s=re.sub(r"^\d{2,7}-\d{1,2}-\d\s*-\s*","",s)  # strip CAS prefix
    # fluorotelomer family
    low=s.lower()
    if "fts" in low or "fluorotelomer sulfon" in low:
        m=XY.search(s);
        if m: return pre+f"{m.group(1)} FTS"
    if "ftca" in low or "fluorotelomer carbox" in low:
        m=XY.search(s)
        if m: return pre+f"{m.group(1)} FTCA"
    # pre-parenthetical core as a bare abbreviation (e.g. "9Cl-PF3ONS (F-53B Major)")
    core0=re.split(r"\(",s)[0].strip()
    keycore=re.sub(r"[-\s]","",core0).upper()
    if keycore in ABBR: return pre+ABBR[keycore]
    # parenthetical abbreviation
    for tok in re.findall(r"\(([^)]+)\)", s):
        t=tok.strip()
        key=re.sub(r"[-\s]","",t).upper()
        if key in ABBR: return pre+ABBR[key]
        if "GENX" in key: return pre+"HFPO-DA"
        if ABBR_PAT.match(t):
            k2=re.sub(r"[-\s]","",t).upper()
            if k2 in ABBR: return pre+ABBR[k2]
    # bare abbreviation
    key=re.sub(r"[-\s]","",s).upper()
    if key in ABBR: return pre+ABBR[key]
    # full chemical name (try pre-paren core AND whole string — some names have parens mid-name)
    core=re.split(r"\(",s)[0]
    cands=set()
    for base in (core, s):
        nf0=normfull(base)
        cands.update({nf0, nf0.replace("acid",""), nf0.replace("acid","").replace("propanoic","")})
    for cand in cands:
        if cand in FULL: return pre+FULL[cand]
    # contains a known full-name stem
    whole=normfull(s)
    for stem,ab in FULL.items():
        if stem in whole: return pre+ab
    return None

def main():
    con=sqlite3.connect(INV); c=con.cursor()
    cols=[r[1] for r in c.execute("PRAGMA table_info(pfas_soil_profile)")]
    if "analyte_canon" not in cols:
        c.execute("ALTER TABLE pfas_soil_profile ADD COLUMN analyte_canon TEXT")
    raws=[r[0] for r in c.execute("select distinct analyte from pfas_soil_profile where analyte is not null")]
    mapped={}; unmapped=[]
    for r in raws:
        ca=canon(r)
        if ca: mapped[r]=ca
        else: unmapped.append(r)
    for raw,ca in mapped.items():
        c.execute("update pfas_soil_profile set analyte_canon=? where analyte=?",(ca,raw))
    con.commit()
    import collections
    dist=collections.Counter()
    for (ca,n) in c.execute("select analyte_canon,count(*) from pfas_soil_profile where analyte_canon is not null group by analyte_canon"):
        dist[ca]=n
    nrows_canon=c.execute("select count(*) from pfas_soil_profile where analyte_canon is not null").fetchone()[0]
    nrows_null=c.execute("select count(*) from pfas_soil_profile where analyte_canon is null").fetchone()[0]
    print(f"raw analyte strings: {len(raws)} -> canonical analytes: {len(dist)}")
    print(f"rows with canon: {nrows_canon} | rows unmapped(null): {nrows_null}")
    print("\ncanonical analytes (top 30):")
    for a,n in dist.most_common(30): print(f"  {n:6}  {a}")
    if unmapped:
        rowcounts={r[0]:r[1] for r in c.execute("select analyte,count(*) from pfas_soil_profile group by analyte")}
        print(f"\nUNMAPPED strings ({len(unmapped)}) — left as analyte_canon=NULL:")
        for u in sorted(unmapped,key=lambda x:-rowcounts.get(x,0))[:40]:
            print(f"  {rowcounts.get(u,0):4}  {repr(u)}")
    con.close()

if __name__=="__main__":
    main()
