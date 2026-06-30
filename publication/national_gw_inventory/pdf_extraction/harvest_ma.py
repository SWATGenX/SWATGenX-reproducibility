#!/usr/bin/env python
"""
harvest_ma.py — Massachusetts well-lithology + hydraulics harvester.

SOURCE: MassDEP EEA Online "DataLake" API (no auth).
  base = https://eeaonline.eea.state.ma.us/EEA/DataLake/V1.0/DataLakeAPI/
  - Enumerate well-drilling records:
        GET .../welldrilling?_start={offset}&_end={offset+page}
        -> {"Items":[{WellID, Latitude, Longitude, TotalDepth, DepthtoBedrock,
                      WaterLevel, WellType, DateComplete, ...}], "TotalCount": N}
        (_end is exclusive; the server returns <page rows where IDs are sparse.)
  - Per-well lithology report (born-digital TEXT PDF, %PDF-1.3, NO VLM needed):
        GET .../WellDrilling/generatereport/{WellID} -> application/octet-stream PDF
        Contains OVER BURDEN + BEDROCK lithology tables:
            From(ft) | To(ft) | Lithology | Color | Comment | ...   (overburden)
            From(ft) | To(ft) | Lithology | Comment | ...           (bedrock)
        Parsed from `pdftotext -bbox` word coordinates (robust to multi-line
        lithology wraps and header/data column mis-alignment).

OUTPUTS (parquet, zstd):
  MA/MA_lithology.parquet  columns EXACTLY: state, well_id, seq, top_ft,
                           bottom_ft, description
  MA/MA_hydraulics.parquet columns: state, well_id, swl_ft, depth_ft,
                           yield_gpm, screen_top_ft, screen_bottom_ft
                           (yield/screen null — not present in search Items)

Checkpointed + resumable: per-well lithology rows streamed to a JSONL checkpoint;
re-runs skip already-processed wells. Run with --limit N for a test slice.

Uses ONLY /data/SWATGenXApp/codes/.venv/bin/python + requests + pdftotext.
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "Chrome/124.0 Safari/537.36")
BASE = "https://eeaonline.eea.state.ma.us/EEA/DataLake/V1.0/DataLakeAPI/"
OUT_DIR = "/data/SWATGenXApp/GenXAppData/state_well_records/MA"
ITEMS_JSONL = os.path.join(OUT_DIR, "_items.jsonl")          # raw search Items
LITHO_CKPT = os.path.join(OUT_DIR, "_litho_checkpoint.jsonl")  # per-well litho rows
DONE_SET = os.path.join(OUT_DIR, "_litho_done.txt")          # processed WellIDs
LITHO_PARQUET = os.path.join(OUT_DIR, "MA_lithology.parquet")
HYDRA_PARQUET = os.path.join(OUT_DIR, "MA_hydraulics.parquet")
STATE = "MA"

# ---------------------------------------------------------------------------
# HTTP with retries
# ---------------------------------------------------------------------------
def make_session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "*/*"})
    return s


def get_retry(sess, url, params=None, stream=False, tries=5, timeout=120):
    last = None
    for k in range(tries):
        try:
            r = sess.get(url, params=params, stream=stream, timeout=timeout)
            if r.status_code == 200:
                return r
            last = "HTTP %d" % r.status_code
        except Exception as e:  # noqa: BLE001
            last = repr(e)
        time.sleep(min(2 ** k, 30) + 0.3 * k)
    raise RuntimeError("GET failed %s : %s" % (url, last))


# ---------------------------------------------------------------------------
# Enumerate search Items
# ---------------------------------------------------------------------------
def enumerate_items(sess, page=1000, max_records=None, log=print):
    """Page through welldrilling; append unique Items to ITEMS_JSONL. Returns list."""
    # resume from existing file
    seen = set()
    items = []
    if os.path.exists(ITEMS_JSONL):
        with open(ITEMS_JSONL) as f:
            for line in f:
                try:
                    it = json.loads(line)
                except Exception:
                    continue
                wid = it.get("WellID")
                if wid is not None and wid not in seen:
                    seen.add(wid)
                    items.append(it)
        log("[items] resumed %d items from checkpoint" % len(items))

    # total count
    r = get_retry(sess, BASE + "welldrilling", params={"_start": 0, "_end": 1})
    total = r.json().get("TotalCount", 0)
    log("[items] TotalCount=%d" % total)
    if max_records:
        total = min(total, max_records)

    fout = open(ITEMS_JSONL, "a")
    start = 0
    # If resuming a partial enumeration, continue from the highest covered offset.
    # We page by offset regardless; dedup by WellID handles overlap.
    while start < total:
        end = start + page
        r = get_retry(sess, BASE + "welldrilling",
                      params={"_start": start, "_end": end})
        batch = r.json().get("Items", [])
        added = 0
        for it in batch:
            wid = it.get("WellID")
            if wid is None or wid in seen:
                continue
            seen.add(wid)
            items.append(it)
            fout.write(json.dumps(it) + "\n")
            added += 1
        fout.flush()
        log("[items] offset %d-%d: %d rows, +%d new (total %d)"
            % (start, end, len(batch), added, len(items)))
        start = end
        if max_records and len(items) >= max_records:
            break
    fout.close()
    if max_records:
        items = items[:max_records]
    return items


# ---------------------------------------------------------------------------
# PDF lithology parsing (bbox word coordinates)
# ---------------------------------------------------------------------------
_WORD_RE = re.compile(
    r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>')
_PAGE_RE = re.compile(r'<page width="[\d.]+" height="[\d.]+">')
_NUM_RE = re.compile(r'^\d+(?:\.\d+)?$')
_FLAGWORDS = {"No", "Yes", "Slow", "Fast", "NR", "Large", "Drop"}


def _pdf_words(pdf_bytes):
    p = subprocess.run(["pdftotext", "-bbox", "-", "-"], input=pdf_bytes,
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    txt = p.stdout.decode("utf-8", "replace")
    words = []
    page = 0
    for line in txt.split("\n"):
        if _PAGE_RE.search(line):
            page += 1
            continue
        m = _WORD_RE.search(line)
        if m:
            x0, y0, x1, y1 = (float(m.group(1)), float(m.group(2)),
                              float(m.group(3)), float(m.group(4)))
            t = html.unescape(m.group(5)).strip()
            if t:
                words.append({"p": page, "x": x0, "x1": x1,
                              "y": (y0 + y1) / 2.0, "t": t})
    return words


def _label_pos(words, label):
    for w in words:
        if w["t"] == label:
            return w["y"], w["p"]
    return None, None


def _header_after(words, label, want):
    """First From(ft) header row below the section `label`, containing all `want`."""
    ly, lp = _label_pos(words, label)
    if ly is None:
        return None
    cands = sorted([w for w in words
                    if w["t"] == "From(ft)" and w["p"] == lp and w["y"] > ly],
                   key=lambda z: z["y"])
    for c in cands:
        band = [ww for ww in words
                if abs(ww["y"] - c["y"]) < 6 and ww["p"] == c["p"]]
        toks = {ww["t"]: ww["x"] for ww in band}
        if all(k in toks for k in want):
            return toks, c["y"], c["p"]
    return None


def _colmap(header_x, order):
    present = sorted([(nm, header_x[nm]) for nm in order if nm in header_x],
                     key=lambda z: z[1])
    b = {}
    for k, (nm, x) in enumerate(present):
        xhi = present[k + 1][1] if k + 1 < len(present) else 1e9
        b[nm] = (x, xhi)
    return b


def _assign_cells(band, centers, min_x, max_x):
    """Assign each non-flag word in [min_x, max_x) to the nearest header column
    center. centers: list of (name, x). Returns dict name -> joined text."""
    buckets = {nm: [] for nm, _ in centers}
    for w in band:
        if w["x"] < min_x or w["x"] >= max_x or w["t"] in _FLAGWORDS:
            continue
        nm = min(centers, key=lambda c: abs(w["x"] - c[1]))[0]
        buckets[nm].append(w)
    out = {}
    for nm, ws in buckets.items():
        ws = sorted(ws, key=lambda z: (round(z["y"] / 6), z["x"]))
        out[nm] = re.sub(r"\s+", " ", " ".join(w["t"] for w in ws)).strip()
    return out


def _parse_table(words, hy, hp, bounds, has_color, y_stop):
    fxlo, fxhi = bounds["From(ft)"]
    txlo, txhi = bounds["To(ft)"]
    # Column centers used for nearest-column word assignment. This is robust to the
    # frequent MA pattern where lithology/color/comment text is mis-aligned vs. the
    # header and straddles nominal column boundaries.
    centers = [("Lithology", bounds["Lithology"][0])]
    if has_color and "Color" in bounds:
        centers.append(("Color", bounds["Color"][0]))
    if "Comment" in bounds:
        centers.append(("Comment", bounds["Comment"][0]))
    # Words at/after the Water-Zone column are flag/operational fields, not lithology.
    max_x = bounds.get("Water", (1e9, 1e9))[0]

    body = [w for w in words
            if w["p"] == hp and w["y"] > hy + 4
            and (y_stop is None or w["y"] < y_stop - 2)]
    anchors = sorted([w for w in body
                      if fxlo - 2 <= w["x"] < fxhi and _NUM_RE.match(w["t"])],
                     key=lambda z: z["y"])
    rows = []
    for k, a in enumerate(anchors):
        ytop = a["y"]
        ylo = (anchors[k - 1]["y"] + ytop) / 2 if k > 0 else ytop - 10
        yhi = (ytop + anchors[k + 1]["y"]) / 2 if k + 1 < len(anchors) else ytop + 30
        band = [w for w in body if ylo < w["y"] <= yhi]
        tos = [w for w in band
               if txlo - 2 <= w["x"] < txhi and _NUM_RE.match(w["t"])]
        if not tos:
            continue
        try:
            top = float(a["t"])
            bot = float(tos[0]["t"])
        except ValueError:
            continue
        min_x = max(tos[0]["x1"] + 1, txlo)
        cells = _assign_cells(band, centers, min_x, max_x)
        lith = cells.get("Lithology", "")
        color = cells.get("Color", "")
        comment = cells.get("Comment", "")
        # Material text: prefer Lithology; if blank (common in MA reports where the
        # driller wrote the material in the Comment column), fall back to Comment.
        material = lith if lith else comment
        if not material:
            continue
        desc = (material + (" " + color if color else "")).strip()
        rows.append((top, bot, desc))
    return rows


def extract_lithology(pdf_bytes):
    """Return list of (top_ft, bottom_ft, description) for overburden + bedrock."""
    words = _pdf_words(pdf_bytes)
    if not words:
        return []
    res = []
    br_y, _ = _label_pos(words, "BEDROCK")
    ob = _header_after(words, "OVER", ["From(ft)", "To(ft)", "Lithology", "Color"])
    if ob:
        hx, hy, hp = ob
        b = _colmap(hx, ["From(ft)", "To(ft)", "Lithology", "Color", "Comment", "Water"])
        res += _parse_table(words, hy, hp, b, True, br_y)
    bre = _header_after(words, "BEDROCK",
                        ["From(ft)", "To(ft)", "Lithology", "Comment"])
    if bre:
        hx, hy, hp = bre
        b = _colmap(hx, ["From(ft)", "To(ft)", "Lithology", "Comment", "Water"])
        res += _parse_table(words, hy, hp, b, False, None)
    return res


# ---------------------------------------------------------------------------
# Per-well lithology fetch (stream-and-discard PDF)
# ---------------------------------------------------------------------------
def fetch_well_litho(sess, well_id):
    url = BASE + "WellDrilling/generatereport/%s" % well_id
    r = get_retry(sess, url, stream=True, timeout=120)
    buf = bytearray()
    for chunk in r.iter_content(65536):
        if chunk:
            buf += chunk
    r.close()
    if not buf[:4] == b"%PDF":
        return []  # not a PDF (no report)
    return extract_lithology(bytes(buf))


# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------
def load_done():
    done = set()
    if os.path.exists(DONE_SET):
        with open(DONE_SET) as f:
            for line in f:
                line = line.strip()
                if line:
                    done.add(line)
    return done


# ---------------------------------------------------------------------------
# Hydraulics parquet (from Items, no extra fetch)
# ---------------------------------------------------------------------------
def _to_float(v):
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def write_hydraulics(items, log=print):
    rows = []
    for it in items:
        rows.append({
            "state": STATE,
            "well_id": str(it.get("WellID")),
            "swl_ft": _to_float(it.get("WaterLevel")),
            "depth_ft": _to_float(it.get("TotalDepth")),
            "yield_gpm": None,         # not present in search Items
            "screen_top_ft": None,     # not present in search Items
            "screen_bottom_ft": None,  # not present in search Items
        })
    df = pd.DataFrame(rows, columns=["state", "well_id", "swl_ft", "depth_ft",
                                     "yield_gpm", "screen_top_ft", "screen_bottom_ft"])
    df.to_parquet(HYDRA_PARQUET, compression="zstd", index=False)
    log("[hydraulics] wrote %d rows -> %s" % (len(df), HYDRA_PARQUET))
    return len(df)


# ---------------------------------------------------------------------------
# Lithology parquet from checkpoint
# ---------------------------------------------------------------------------
def write_lithology_parquet(log=print):
    rows = []
    if os.path.exists(LITHO_CKPT):
        with open(LITHO_CKPT) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                rows.append(rec)
    df = pd.DataFrame(rows, columns=["state", "well_id", "seq",
                                     "top_ft", "bottom_ft", "description"])
    if len(df):
        df["seq"] = df["seq"].astype("int64")
        df["top_ft"] = df["top_ft"].astype("float64")
        df["bottom_ft"] = df["bottom_ft"].astype("float64")
    df.to_parquet(LITHO_PARQUET, compression="zstd", index=False)
    log("[lithology] wrote %d rows (%d wells) -> %s"
        % (len(df), df["well_id"].nunique() if len(df) else 0, LITHO_PARQUET))
    return len(df)


# ---------------------------------------------------------------------------
# Main harvest
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None,
                    help="process only first N wells (test mode)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--page", type=int, default=1000)
    ap.add_argument("--flush-every", type=int, default=500,
                    help="rewrite parquet every N completed wells")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    def log(*a):
        print(*a, flush=True)

    t0 = time.time()
    sess = make_session()

    # 1. enumerate items
    items = enumerate_items(sess, page=args.page, max_records=args.limit, log=log)
    log("[items] total unique wells: %d" % len(items))

    # 2. hydraulics parquet (always rewrite from current items)
    write_hydraulics(items, log=log)

    # 3. lithology: per-well, checkpointed
    done = load_done()
    todo = [it for it in items if str(it.get("WellID")) not in done]
    log("[lithology] %d done, %d to process" % (len(done), len(todo)))

    ckpt_f = open(LITHO_CKPT, "a")
    done_f = open(DONE_SET, "a")
    lock = threading.Lock()
    counters = {"n": 0, "rows": 0, "err": 0}

    # thread-local sessions
    tl = threading.local()

    def worker(it):
        wid = it.get("WellID")
        if not hasattr(tl, "s"):
            tl.s = make_session()
        try:
            litho = fetch_well_litho(tl.s, wid)
        except Exception as e:  # noqa: BLE001
            return wid, None, repr(e)
        return wid, litho, None

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(worker, it) for it in todo]
        for fut in as_completed(futs):
            wid, litho, err = fut.result()
            with lock:
                if err is not None:
                    counters["err"] += 1
                    # do NOT mark done -> retried on resume
                else:
                    for seq, (top, bot, desc) in enumerate(litho, start=1):
                        rec = {"state": STATE, "well_id": str(wid), "seq": seq,
                               "top_ft": top, "bottom_ft": bot, "description": desc}
                        ckpt_f.write(json.dumps(rec) + "\n")
                        counters["rows"] += 1
                    done_f.write("%s\n" % wid)
                    counters["n"] += 1
                    if counters["n"] % 200 == 0:
                        ckpt_f.flush()
                        done_f.flush()
                    if counters["n"] % args.flush_every == 0:
                        rate = counters["n"] / max(1e-6, time.time() - t0)
                        log("[lithology] %d wells, %d rows, %d err, %.1f w/s"
                            % (counters["n"], counters["rows"],
                               counters["err"], rate))

    ckpt_f.flush()
    ckpt_f.close()
    done_f.flush()
    done_f.close()

    # 4. final parquet rewrite
    write_lithology_parquet(log=log)
    dt = time.time() - t0
    log("[done] processed %d wells this run, %d errors, %d litho rows added, %.0fs"
        % (counters["n"], counters["err"], counters["rows"], dt))


if __name__ == "__main__":
    main()
