"""Shared LaTeX escaping for publication table emit scripts."""
from __future__ import annotations


def latex_escape(text: str) -> str:
    out = text
    out = out.replace("\\", r"\textbackslash{}")
    out = out.replace("&", r"\&")
    out = out.replace("%", r"\%")
    out = out.replace("#", r"\#")
    out = out.replace("_", r"\_")
    out = out.replace("≤", r"$\leq$")
    out = out.replace("≥", r"$\geq$")
    return out
