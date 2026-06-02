"""
Lightweight phase timing for publication runtime profiling (stdlib only).

Enable with environment variable SWATGENX_RUNTIME_PROFILE=1 (or true/yes).
Set SWATGENX_RUNTIME_JSONL to an absolute or repo-relative path for JSONL output.

Optional envelope keys (merged into each JSON line if set):
  SWATGENX_RUNTIME_RUN_ID, SWATGENX_RUNTIME_MODEL_ID, SWATGENX_RUNTIME_TIER,
  SWATGENX_RUNTIME_STATE

Does not log file paths beyond the JSONL path you configure; do not set env
values to secrets or tokens.
"""
from __future__ import annotations

import contextlib
import json
import os
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def _profile_enabled() -> bool:
    v = (os.environ.get("SWATGENX_RUNTIME_PROFILE") or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _jsonl_path() -> str | None:
    p = (os.environ.get("SWATGENX_RUNTIME_JSONL") or "").strip()
    return p or None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _resolve_jsonl_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = _repo_root() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _envelope_from_env() -> dict[str, str]:
    out: dict[str, str] = {}
    mapping = (
        ("run_id", "SWATGENX_RUNTIME_RUN_ID"),
        ("model_id", "SWATGENX_RUNTIME_MODEL_ID"),
        ("tier", "SWATGENX_RUNTIME_TIER"),
        ("state", "SWATGENX_RUNTIME_STATE"),
    )
    for key, envk in mapping:
        val = (os.environ.get(envk) or "").strip()
        if val:
            out[key] = val
    return out


@contextlib.contextmanager
def runtime_phase(
    phase_name: str,
    phase_group: str,
    include_in_processing_total: bool,
    *,
    notes: str = "",
) -> Iterator[None]:
    """
    Context manager: records one phase to JSONL when profiling is enabled.
    include_in_processing_total: True => counts toward core_processing_time in summaries.
    """
    if not _profile_enabled():
        yield
        return

    raw_path = _jsonl_path()
    if not raw_path:
        yield
        return

    path = _resolve_jsonl_path(raw_path)
    t0 = time.perf_counter()
    start = datetime.now(timezone.utc)
    err: BaseException | None = None
    try:
        yield
    except BaseException as exc:
        err = exc
        raise
    finally:
        t1 = time.perf_counter()
        end = datetime.now(timezone.utc)
        rec: dict[str, Any] = {
            "phase_name": phase_name,
            "phase_group": phase_group,
            "include_in_processing_total": bool(include_in_processing_total),
            "elapsed_seconds": round(t1 - t0, 6),
            "start_utc": start.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "end_utc": end.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "status": "ok" if err is None else "error",
            "notes": notes or (repr(err) if err else ""),
        }
        if err is not None:
            rec["error_type"] = type(err).__name__
            tb = traceback.format_exc()
            if tb and tb.strip():
                rec["traceback_tail"] = tb[-4000:]
        rec.update(_envelope_from_env())
        line = json.dumps(rec, ensure_ascii=False) + "\n"
        with path.open("a", encoding="utf-8") as f:
            f.write(line)


def null_phase() -> contextlib.AbstractContextManager[None]:
    """Explicit no-op context (always skips recording)."""
    return contextlib.nullcontext()
