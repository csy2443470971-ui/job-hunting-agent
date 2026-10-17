"""Assemble a résumé from the playbook's tagged résumé lines, with no model call.

Lines in profile/master/02-experience.md and 03-projects.md end with [lens, lens]. For a lens we take the entries with
the most matching lines, keep the best 3-4 lines each, and order entries reverse-chronologically. Wording is the
playbook's own, so it already follows the brief.
"""
from __future__ import annotations
import re
from . import config

def _p():
    return config.profile()


LINE_RE = re.compile(r"^- (.+?) \[([a-z_, ]+)\]\s*$")


def _sections(path, keep: set | None = None) -> dict[str, list[tuple[str, set[str]]]]:
    out, cur = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            name = line[3:].split(" · ")[0].strip()
            cur = name if "[fill" not in line or (keep and name in keep) else None
            out.setdefault(cur, []) if cur else None
            continue
        m = LINE_RE.match(line)
        if cur and m:
            out[cur].append((m.group(1).strip(), {t.strip() for t in m.group(2).split(",")}))
    return {k: v for k, v in out.items() if v}


def _linkify(text: str) -> tuple[str, str]:
    for name, url in (_p().get("project_links") or {}).items():
        if name in text:
            return name, url
    return "", ""


def assemble(lens: str, sector: str | None = None, n_entries: int = 4, n_projects: int = 3, posting_text: str = "") -> dict:
    prof = _p(); ENTRIES = prof.get("entries", {}); PROJECT_LINKS = prof.get("project_links", {})
    PINNED = [n for n, m in ENTRIES.items() if m.get("pinned")]
    exp = _sections(config.MASTER_DIR / "02-experience.md", set(ENTRIES))
    proj = _sections(config.MASTER_DIR / "03-projects.md")
    want = {lens} | ({"climate"} if sector == "climate" else set())

    def rank(lines):
        return sum(2 if t & want else 0 for _, t in lines) + 0.1 * len(lines)

    names = [n for n in exp if n in ENTRIES]
    pinned = [n for n in PINNED if n in names]   # the most recent role always appears
    chosen = pinned + sorted([n for n in names if n not in pinned], key=lambda n: -rank(exp[n]))[:n_entries - len(pinned)]
    chosen.sort(key=lambda n: ENTRIES[n]["start"], reverse=True)
    from collections import Counter
    verbs: Counter = Counter()

    def pick(cands, k):
        """Lens-matching lines first; skip a line whose opening verb is already used twice on the page."""
        out = []
        for text, tags in sorted(cands, key=lambda x: (0 if x[1] & want else 1, verbs[x[0].split()[0]])):
            v = text.split()[0]
            if verbs[v] >= 2 and len(cands) - len(out) > k - len(out):
                continue
            out.append((text, tags)); verbs[v] += 1
            if len(out) == k:
                break
        return out

    experience = []
    for n in chosen:
        lines = pick(exp[n], 4)
        bullets = []
        for text, _ in lines:
            lt, url = _linkify(text)
            bullets.append({"text": text, "provenance": "master", "link_text": lt, "link": url})
        m = ENTRIES[n]
        experience.append({"org": n, "org_link": m["link"], "role": m["role"], "dates": m["dates"], "location": m["location"], "bullets": bullets})
    used = " ".join(b["text"] for e in experience for b in e["bullets"])
    projects = []
    for name, lines in sorted(proj.items(), key=lambda kv: -rank(kv[1])):
        if name.startswith("Talks") or name in used or not any(t & want for _, t in lines):
            continue
        matching = [(t, tags) for t, tags in lines if tags & want]
        text = sorted(matching, key=lambda x: verbs[x[0].split()[0]])[0][0]
        verbs[text.split()[0]] += 1
        projects.append({"name": name, "blurb": text, "link": PROJECT_LINKS.get(name, ""), "provenance": "master"})
        if len(projects) >= n_projects:
            break
    return {"name": prof.get("name", ""), "headline": "", "email": prof.get("email", ""), "phone": prof.get("phone", ""),
            "location": prof.get("location", ""), "links": [], "summary": "",
            "experience": experience, "projects": projects, "education": prof.get("education", []),
            "skills": skills_for(lens, posting_text), "diy_ratio": 0.0, "diy_notes": [], "tailoring_notes": [f"assembled from playbook lines for lens {lens}"]}


GENERATIVE_RE = r"generative|creative coding|digital art|shader|particle|webgl artist|installation"


def skills_for(lens: str, posting_text: str = "") -> list[dict]:
    """Techniques (particle systems, SDF) appear only when the posting asks for generative / digital-art work."""
    import copy
    prof = _p(); groups_def = prof.get("skill_groups", {})
    keys = prof.get("skills_by_lens", {}).get(lens) or prof.get("skills_by_lens", {}).get("product_design", [])
    groups = [copy.deepcopy(groups_def[k]) for k in keys if k in groups_def]
    if re.search(GENERATIVE_RE, posting_text or "", re.I):
        for g in groups:
            if g["label"] == "Creative coding":
                g["items"] += prof.get("generative_extra", [])
    return groups
