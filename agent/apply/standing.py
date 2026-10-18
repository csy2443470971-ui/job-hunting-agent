"""Standing answers for recurring form questions, decided in code (node 05 · Write and 07 · Apply).

The person gave these once (2026-10-17) so similar questions are never asked again. Values live in
profile/preferences.yaml under eligibility.self_id; disability status is not given and still goes to "needs you".
Works on a question label, or on one option label when an ATS renders each checkbox as its own field ("Male", "White").
"""
from __future__ import annotations
import re
from .. import config

_DEFAULT = {"gender": None, "race": None, "race_detail": None, "hispanic_latino": None, "veteran": None, "relocate": None}


def _sid() -> dict:
    """Only what the person put in preferences.yaml; nothing is assumed."""
    return {**_DEFAULT, **((config.preferences().get("eligibility") or {}).get("self_id") or {})}


def _pick(options: list[str] | None, *wants: str) -> str | None:
    """First option whose text contains one of `wants` (in order), else None."""
    for w in wants:
        for o in options or []:
            if re.search(w, o, re.I):
                return o
    return None


def _is(value: str | None, text: str) -> bool:
    return bool(value) and re.sub(r"\W+", " ", value.lower()).strip() == re.sub(r"\W+", " ", text.lower()).strip()


SKIP_NEED = re.compile(r"\boptional\b|opt-?in|text messages?|sms|marketing|newsletter|pronounce|pronoun|cover letter|"
                       r"\(file upload|upload handled|handled outside|additional file|^attach\b|legal name|if the form adds", re.I)


def simple_answer(label: str) -> str | None:
    """Questions too simple to ask the person about (preferences.yaml eligibility.simple_answers)."""
    p = config.preferences(); table = ((p.get("eligibility") or {}).get("simple_answers") or {})
    site = (config.profile().get("links") or {}).get("website", "")
    for pat, val in table.items():
        if re.search(pat, label or "", re.I):
            return str(val).replace("{website}", site)
    return None


def standing_answer(label: str, options: list[str] | None = None, as_option: bool = False) -> str | None:
    """as_option=True: `label` is one choice of a checkbox/radio group, so only the per-option demographic rules apply;
    question rules (relocation, sponsorship, simple answers) must never tick an option because it shares a word."""
    s, l = _sid(), (label or "").strip().lower()
    if not l:
        return None
    v = None if as_option else simple_answer(label)
    if v is not None:
        return _pick(options, "^" + re.escape(v)) or v if options else v
    o = re.sub(r"\s*\(.*?\)", "", l).strip()   # "White (Not Hispanic or Latino)" -> "white"
    # one checkbox per option: Yes for the person's own value, No for the rest (only when a value is set)
    if re.match(r"(i )?(decline|prefer not|don.t wish)", o):
        return "No" if any(s.values()) else None   # you chose to answer, so never tick a decline option
    if s["gender"] and re.fullmatch(r"(fe)?male|wom[ae]n|man|non-?binary|.*gender.*(identity|non|fluid).*", o) and len(o) < 40:
        return "Yes" if _is(s["gender"], o) or (o in ("woman", "women") and _is(s["gender"], "female")) or (o == "man" and _is(s["gender"], "male")) else "No"
    if s["race"] and re.fullmatch(r"(east |south |southeast )?asian|white|black.*|native.*|american indian.*|hispanic or latino|two or more.*|middle eastern.*", o):
        if o == "hispanic or latino":
            return "Yes" if _is(s["hispanic_latino"], "yes") else "No"
        return "Yes" if _is(s["race"], o) or _is(s["race_detail"], o) else "No"
    if s["veteran"] and re.search(r"identify as one or more of the classifications of protected veteran|i am a (protected )?veteran", l):
        return "No" if re.search(r"not", s["veteran"], re.I) else "Yes"
    if s["veteran"] and re.search(r"i am not a (protected )?veteran", l):
        return "Yes" if re.search(r"not", s["veteran"], re.I) else "No"
    if as_option:
        return None
    # whole questions
    if s["relocate"] and re.search(r"address|where .*work from|city", l) and re.search(r"relocat", l):
        return "Relocating" if _is(s["relocate"], "yes") else None
    if s["relocate"] and re.search(r"relocat|willing to (move|be based)", l):
        return _pick(options, "^" + re.escape(s["relocate"])) or s["relocate"]
    if s["gender"] and re.search(r"\bgender\b|\bsex\b", l):
        return _pick(options, f"^{re.escape(s['gender'])}$", re.escape(s["gender"])) or s["gender"]
    if s["hispanic_latino"] and re.search(r"hispanic|latin[oax]", l):
        return _pick(options, r"^no\b", r"not hispanic") if _is(s["hispanic_latino"], "no") and _pick(options, r"^no\b", r"not hispanic") else s["hispanic_latino"]
    if s["race"] and re.search(r"\brace\b|ethnic", l):
        detail = f' ({s["race_detail"]})' if s.get("race_detail") else ""
        return _pick(options, *(re.escape(x) for x in (s.get("race_detail"), s["race"]) if x)) or s["race"] + detail
    if s["veteran"] and re.search(r"veteran", l):
        return _pick(options, re.escape(s["veteran"]), r"not a (protected )?veteran" if re.search("not", s["veteran"], re.I) else r"^yes") or s["veteran"]
    if re.search(r"self-?identification|eeo", l) and not re.search(r"disab", l) and all(s[k] for k in ("gender", "race", "veteran")):
        return f'Gender: {s["gender"]}; race: {s["race"]}' + (f' ({s["race_detail"]})' if s.get("race_detail") else "") + \
               (f'; Hispanic or Latino: {s["hispanic_latino"]}' if s.get("hispanic_latino") else "") + f'; veteran: {s["veteran"]}'
    return None
