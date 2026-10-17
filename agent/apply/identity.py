"""Name and contact fields on application forms, decided in code (node 07 · Apply, and 05 · Write for answers).

Rule (from the person, 2026-10-17): legal name first. "First name", "Last name", "Full name", "Name" and
"Legal name" fields get the legal name. Only a field that asks for a preferred name / nickname / "name you go by"
gets the preferred name. Résumés and email sign-offs keep the display name from profile.yaml.
"""
from __future__ import annotations
import re
from .. import config

PREFERRED = re.compile(r"prefer|nickname|go by|known as|called", re.I)


def identity_answer(label: str) -> str | None:
    p = config.profile()
    legal = p.get("legal_name") or {}
    first, last = legal.get("first", ""), legal.get("last", "")
    preferred = p.get("preferred_name") or first
    l = (label or "").lower()
    if not re.search(r"name|e-?mail|phone|mobile", l) or re.search(r"company|school|employer|reference|manager|\breferr", l):
        return None
    if "name" in l:
        if PREFERRED.search(l):
            return preferred
        if re.search(r"first|given", l):
            return first
        if re.search(r"last|family|surname", l):
            return last
        if re.search(r"middle", l):
            return ""
        return f"{first} {last}".strip()
    if re.search(r"e-?mail", l):
        return p.get("email")
    if re.search(r"phone|mobile", l):
        return p.get("phone")
    return None
