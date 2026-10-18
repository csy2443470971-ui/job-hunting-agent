"""Résumé headline = a plain job title. Hard rule, not left to the model.

No clauses ("who builds...", "that..."), no taglines after "·", no adjectives. Either the posting's own base title
(when it is a title we target) or the lens default below.
"""
from __future__ import annotations
import re

DEFAULTS = {
    "ai_product": "AI Product Designer",
    "product_design": "Digital Product Designer",
    "ux_research": "UX Researcher",
    "design_engineer": "Design Engineer",
    "art_director": "Digital Art Director",
    "motion": "Motion Designer",
    "strategy": "Design Strategist",
    "brand_strategy": "Brand Strategist",
    "founders_office": "Strategy & Business Development",
}
FALLBACK = "Digital Product Designer"
SENIORITY = r"\b(senior|sr\.?|(?<!of )staff|principal|lead|junior|jr\.?|associate|intern|ii|iii|iv|freelance|contract|temporary)\b"
TARGET_WORDS = r"(designer|design engineer|researcher|art director|strategist|creative technologist|technologist|prototyper|chief of staff)"


def base_title(posting_title: str) -> str | None:
    pt = posting_title or ""
    if "|" in pt:  # HN style "Company | Title | Location | ..."
        segs = [x.strip() for x in pt.split("|")]
        pt = next((x for x in segs[1:] if re.search(TARGET_WORDS, x, re.I)), segs[1] if len(segs) > 1 else "")
    pt = re.sub(r"\[[^\]]*\]|\([^)]*\b20\d\d\b[^)]*\)", " ", pt)   # "[2027] …", "(2027 Start)" are tags, not the title
    t = re.split(r"[,(\-–/]", pt)[0]
    t = re.sub(SENIORITY, "", t, flags=re.I)
    t = re.sub(r"^[\s.,&-]+|[\s.,&-]+$", "", re.sub(r"\s+", " ", t)).strip()
    if not re.search(TARGET_WORDS, t, re.I) or len(t.split()) > 4:
        return None
    small = {"of", "and", "&", "for"}
    return " ".join(w if w.isupper() else (w.lower() if i and w.lower() in small else w[:1].upper() + w[1:]) for i, w in enumerate(t.split()))


GENERIC = {"product designer", "designer", "strategist", "ux designer", "researcher"}


def headline(role_family: str | None, posting_title: str | None) -> str:
    """Specific posting titles (Web Designer, Design Engineer, Motion Designer) are used as-is;
    generic ones (Product Designer) give way to the sharper lens default (AI Product Designer, Digital Product Designer)."""
    b = base_title(posting_title or "")
    if b and b.lower() not in GENERIC:
        return b
    return DEFAULTS.get(role_family or "", FALLBACK)


ROLE_FRAGMENT = re.compile(r"^\s*(?:[A-Z][\w-]*\s){0,3}(designer|engineer|strategist|researcher|director|technologist)\.\s*", re.I)


def strip_role_fragment(summary: str) -> str:
    """'Product designer. I build ...' -> 'I build ...' (the headline already says the role)."""
    return ROLE_FRAGMENT.sub("", summary or "", count=1)


def fix_entry_titles(content: dict, role_family: str | None) -> None:
    """Entries listed under entry_titles in profile.yaml get a lens-specific title; dates come from entries."""
    from . import config
    prof = config.profile(); titles = prof.get("entry_titles", {}); entries = prof.get("entries", {})
    for e in content.get("experience", []):
        for name, by_lens in titles.items():
            if name.split()[0].lower() in (e.get("org") or "").lower():
                e["org"] = name
                e["role"] = by_lens.get(role_family or "", by_lens.get("default", e.get("role", "")))
                if name in entries:
                    e["dates"] = entries[name].get("dates", e.get("dates", ""))
