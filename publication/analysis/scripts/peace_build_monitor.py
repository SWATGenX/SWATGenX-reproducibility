#!/usr/bin/env python3
"""Self-contained hourly status emailer for the parallel Peace TauDEM builds.

Runs as www-data (so it can read the SMTP password and signal the www-data build
processes). Launched detached by run_peace_parallel_builds.sh with the run START
epoch as argv[1]. Every hour it inspects each build's log + build_timing.json +
PID liveness, classifies the current stage / stall / completion, and emails a
plain-text status report (link/text only — never attaches model files).

At the 12-hour cap it terminates any still-running build (and orphaned heavy
tools) and sends a final summary, then exits.
"""
from __future__ import annotations

import json
import os
import re
import smtplib
import ssl
import subprocess
import sys
import time
from collections import deque
from datetime import datetime, timedelta
from email.mime.text import MIMEText

LOGDIR = "/tmp"
SITE = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0310/huc8/03100101"
PW_FILE = "/data/SWATGenXApp/codes/ssl_certificate/godaddy_email_password.json"
RECEIVER = "vahidr32@gmail.com"
SENDER = "info@swatgenx.com"
MAX_HOURS = 12.0
TAIL_LINES = 6000
STALL_MIN = 25  # no new log output for this long => flag as possibly stuck

BUILDS = [
    {"key": "s1250c250", "thr": "1250/250 (fine)",
     "name": "SWAT_MODEL_TauDEM_split_s1250c250_clip"},
    {"key": "s2500c500", "thr": "2500/500 (medium)",
     "name": "SWAT_MODEL_TauDEM_split_s2500c500_clip"},
    {"key": "s5000c1000", "thr": "5000/1000 (coarse)",
     "name": "SWAT_MODEL_TauDEM_split_s5000c1000_clip"},
]
for b in BUILDS:
    b["log"] = f"{LOGDIR}/peace_par_taudem_{b['key']}.log"
    b["pidf"] = f"{LOGDIR}/peace_par_{b['key']}.pid"
    b["dir"] = f"{SITE}/{b['name']}"

# (rank, regex, human label) -- monotonic QSWAT+/Editor pipeline; highest matched rank wins.
STAGE_SIGS = [
    (1, r"reading|loading DEM|Clipping DEM|clip.*dem|pitremove|pit ?remove", "DEM preprocessing"),
    (2, r"runTauDEM|TauDEM tools|d8flowdir|aread8|threshold|streamnet|gridnet", "TauDEM flow routing / stream net"),
    (3, r"delineation.*finished|finishDelineation|delineation \(existing\) finished", "delineation finished"),
    (4, r"splitChannelsByLakes|addHUCLakes|lake topology|wiring.*lake|reservoir", "lake integration (split/wire)"),
    (5, r"starting HRU generation|calcHRUs|HRU generation|HRUsAreCreated", "HRU generation"),
    (6, r"HRU phase finished|HRU.*completed|processes are completed", "HRU finished"),
    (7, r"SWAT\+ Editor for", "SWAT+ Editor (writing TxtInOut)"),
    (8, r"Writing .*\.\.\.|Writing .*report", "SWAT+ Editor (writing files)"),
    (9, r"streamflow_data|streamflow data for|Creating weather station|streamflow_record", "streamflow / weather extraction"),
]
DONE_SIG = re.compile(r"\[run_taudem_variant\] DONE|chandeg\.con exists=True")
HEARTBEAT = re.compile(r"elapsed (\d+)m\s*(\d+)s")


def stamp(ts: float | None = None) -> str:
    return datetime.fromtimestamp(ts if ts else time.time()).strftime("%Y-%m-%d %H:%M:%S")


def tail(path: str, n: int = TAIL_LINES) -> list[str]:
    try:
        with open(path, "r", errors="replace") as fh:
            return list(deque(fh, maxlen=n))
    except FileNotFoundError:
        return []


def pid_alive(pidf: str) -> int | None:
    try:
        with open(pidf) as fh:
            pid = int(fh.read().strip())
    except (FileNotFoundError, ValueError):
        return None
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return None
    except PermissionError:
        # EPERM => the process exists but is owned by another user (the timeout
        # wrapper runs as the launching user, not www-data); treat as alive.
        return pid
    except OSError:
        return None
    return pid


def classify(b: dict) -> dict:
    try:
        return _classify(b)
    except Exception as e:  # never let a status read kill the 12h monitor
        print(f"{stamp()} classify({b['key']}) error: {e}", flush=True)
        return {"thr": b["thr"], "name": b["name"], "status": "UNKNOWN (monitor read error)",
                "stage": "—", "last_out": "—", "stall_min": None, "alive_pid": None}


def _classify(b: dict) -> dict:
    """Return status dict for one build."""
    res = {"thr": b["thr"], "name": b["name"]}
    timing = os.path.join(b["dir"], "build_timing.json")
    chandeg = os.path.join(b["dir"], "Scenarios", "Default", "TxtInOut", "chandeg.con")
    lines = tail(b["log"])
    alive = pid_alive(b["pidf"])

    # log mtime / stall
    last_out = None
    try:
        last_out = os.path.getmtime(b["log"])
    except OSError:
        pass
    res["last_out"] = stamp(last_out) if last_out else "—"
    stall_min = ((time.time() - last_out) / 60.0) if last_out else None
    res["stall_min"] = stall_min

    # most-recent stage
    best_rank, best_label = 0, "starting / DEM setup"
    for rank, rx, label in STAGE_SIGS:
        crx = re.compile(rx, re.IGNORECASE)
        if any(crx.search(ln) for ln in lines):
            if rank >= best_rank:
                best_rank, best_label = rank, label
    res["stage"] = best_label

    # heartbeat (current long-running QSWAT+ stage elapsed)
    hb = None
    for ln in reversed(lines):
        m = HEARTBEAT.search(ln)
        if m:
            hb = int(m.group(1)) + int(m.group(2)) / 60.0
            break
    res["heartbeat_min"] = hb

    # completion?
    completed = False
    if os.path.exists(timing):
        try:
            with open(timing) as fh:
                t = json.load(fh)
            if t.get("built"):
                completed = True
                res["build_min"] = t.get("total_build_minutes")
        except Exception:
            pass
    if not completed and os.path.exists(chandeg) and any(DONE_SIG.search(ln) for ln in lines):
        completed = True

    if completed:
        res["status"] = "COMPLETED"
    elif alive:
        if stall_min is not None and stall_min >= STALL_MIN:
            res["status"] = "RUNNING (possibly stalled)"
        else:
            res["status"] = "RUNNING"
    else:
        # process gone, no completion => interrupted/failed/timed-out
        killed = any("KILLED-AT-CAP" in ln or "timed out" in ln.lower() for ln in lines)
        res["status"] = "TIMED-OUT/KILLED" if killed else "STOPPED (no completion)"
    res["alive_pid"] = alive
    return res


def render(report: list[dict], hour: int, start: float, capped: bool) -> tuple[str, str]:
    now = time.time()
    elapsed_h = (now - start) / 3600.0
    n_done = sum(1 for r in report if r["status"] == "COMPLETED")
    n_run = sum(1 for r in report if r["status"].startswith("RUNNING"))
    n_dead = len(report) - n_done - n_run
    tag = "FINAL (12h cap)" if capped else f"hour {hour}/12"
    subj = (f"[Peace TauDEM builds] {tag} — {n_run} running, {n_done} done, {n_dead} stopped")

    L = []
    L.append(f"Peace HUC8 03100101 — parallel TauDEM+lakes builds (splitChannelsByLakes, clipped DEM, 30 m).")
    L.append(f"Run started: {stamp(start)}   |   Now: {stamp(now)}   |   Elapsed: {elapsed_h:.2f} h / {MAX_HOURS:.0f} h cap")
    L.append("NHD baseline already built earlier: 101.3 min (ran alone).")
    L.append("NOTE: these three run concurrently, so wall-clocks are NOT directly comparable to each other")
    L.append("      or to the NHD baseline (CPU/IO contention). Goal here is a successful TauDEM+lakes build per threshold.")
    L.append("")
    for r in report:
        L.append(f"=== {r['thr']}  [{r['name']}] ===")
        L.append(f"  status : {r['status']}")
        L.append(f"  stage  : {r['stage']}")
        if r.get("heartbeat_min") is not None:
            L.append(f"  current QSWAT+ stage elapsed: {r['heartbeat_min']:.0f} min (delineation/lake-merge/HRU heartbeat)")
        if r.get("build_min") is not None:
            L.append(f"  build time: {r['build_min']:.1f} min")
        if r.get("stall_min") is not None:
            L.append(f"  last log output: {r['last_out']} ({r['stall_min']:.0f} min ago)")
        else:
            L.append(f"  last log output: {r['last_out']}")
        L.append("")

    remaining = [r["thr"] for r in report if r["status"].startswith("RUNNING")]
    not_done = [r["thr"] for r in report if r["status"] != "COMPLETED"]
    L.append(f"Still running : {', '.join(remaining) if remaining else 'none'}")
    L.append(f"Not yet complete: {', '.join(not_done) if not_done else 'none — all done'}")
    if capped:
        L.append("")
        L.append("12-hour cap reached: any still-running build was terminated. See per-build status above.")
    L.append("")
    L.append("(Automated hourly report from peace_build_monitor.py on the SWATGenX server.)")
    return subj, "\n".join(L)


def send_email(subject: str, body: str) -> None:
    try:
        with open(PW_FILE) as fh:
            pw = json.load(fh)["email_password"]
    except Exception as e:
        print(f"{stamp()} cannot read pw: {e}", flush=True)
        return
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = RECEIVER
    try:
        s = smtplib.SMTP("smtp.office365.com", 587, timeout=45)
        s.ehlo(); s.starttls(context=ssl.create_default_context()); s.ehlo()
        s.login(SENDER, pw)
        s.send_message(msg)
        s.quit()
        print(f"{stamp()} sent: {subject}", flush=True)
    except Exception as e:
        print(f"{stamp()} EMAIL FAILED: {e}", flush=True)


def kill_running(report: list[dict]) -> None:
    # We run as www-data; target the www-data runner of each still-running build by
    # its unique --model-name (the timeout wrapper is owned by another user and is
    # left to fire on its own). timeout 12h is the primary cap; this is the backstop.
    for r, b in zip(report, BUILDS):
        if not r.get("alive_pid"):
            continue
        for sig in ("-TERM", "-KILL"):
            subprocess.run(["pkill", sig, "-u", "www-data", "-f",
                            f"model-name {b['name']}"], check=False)
            time.sleep(3)
    # mop up orphaned heavy tools (we are at the cap; everything is being torn down)
    for name in ("mpiexec", "pitremove", "aread8", "streamnet", "d8flowdir", "threshold"):
        subprocess.run(["pkill", "-u", "www-data", "-x", name], check=False)
    # write a marker into each log so a late classify() reads TIMED-OUT/KILLED
    for r, b in zip(report, BUILDS):
        if r.get("alive_pid"):
            try:
                with open(b["log"], "a") as fh:
                    fh.write(f"\n[monitor] KILLED-AT-CAP {stamp()}\n")
            except Exception:
                pass


def main() -> int:
    start = float(sys.argv[1]) if len(sys.argv) > 1 else time.time()
    print(f"{stamp()} monitor up; start={stamp(start)} cap={MAX_HOURS}h", flush=True)

    # hour-0 baseline email shortly after launch (let builds spin up first)
    time.sleep(10)
    report = [classify(b) for b in BUILDS]
    subj, body = render(report, hour=0, start=start, capped=False)
    send_email(subj, body)

    hour = 0
    while True:
        # sleep to the next hour boundary relative to start
        hour += 1
        target = start + hour * 3600.0
        sleep_s = target - time.time()
        capped_now = (hour * 1.0) >= MAX_HOURS or (time.time() - start) >= MAX_HOURS * 3600.0
        if sleep_s > 0 and not capped_now:
            time.sleep(sleep_s)

        report = [classify(b) for b in BUILDS]
        all_done = all(r["status"] == "COMPLETED" for r in report)
        none_running = not any(r["status"].startswith("RUNNING") for r in report)
        capped = (time.time() - start) >= MAX_HOURS * 3600.0 or hour >= int(MAX_HOURS)

        if capped:
            kill_running(report)
            report = [classify(b) for b in BUILDS]
            subj, body = render(report, hour=hour, start=start, capped=True)
            send_email(subj, body)
            print(f"{stamp()} cap reached; final sent; exit", flush=True)
            return 0

        subj, body = render(report, hour=hour, start=start, capped=False)
        send_email(subj, body)

        if all_done or none_running:
            # one wrap-up note then exit early
            send_email("[Peace TauDEM builds] all builds settled — monitor exiting",
                       body + "\n\nAll builds have completed or stopped before the 12h cap. Monitor exiting.")
            print(f"{stamp()} all settled; exit", flush=True)
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
