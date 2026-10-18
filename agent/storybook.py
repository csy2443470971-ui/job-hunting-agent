"""Storybook versions and "learn from a résumé you like".

- snapshot(reason): saves the storybook before any change (manual save, applied fix, style learning).
- restore_previous(): puts back the most recent snapshot ("Back to previous version"). Press again to go further back.
- learn_from(file, prompt): reads a résumé you admire and rewrites your storybook's résumé lines in that style, using
  only your own facts. Runs line block by line block and reports progress, so the page can show it changing.
"""
from __future__ import annotations
import datetime, json, re, shutil, threading
from pathlib import Path
from pydantic import BaseModel, Field
from . import config

STATUS: dict = {"state": "idle"}


def _vdir() -> Path:
    d = config.PROFILE_DIR / ".versions"; d.mkdir(exist_ok=True); return d


def snapshot(reason: str) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    d = _vdir() / ts; d.mkdir()
    for f in config.MASTER_DIR.glob("*.md"):
        shutil.copy2(f, d / f.name)
    (d / "_meta.json").write_text(json.dumps({"reason": reason, "at": ts}), encoding="utf-8")
    return ts


def versions() -> list[dict]:
    out = []
    for d in sorted(_vdir().iterdir(), reverse=True):
        if d.is_dir():
            m = json.loads((d / "_meta.json").read_text()) if (d / "_meta.json").exists() else {}
            out.append({"id": d.name, "reason": m.get("reason", ""), "at": d.name[:15]})
    return out


def restore_previous() -> str | None:
    vs = [d for d in sorted(_vdir().iterdir(), reverse=True) if d.is_dir()]
    if not vs:
        return None
    d = vs[0]
    for f in d.glob("*.md"):
        shutil.copy2(f, config.MASTER_DIR / f.name)
    reason = json.loads((d / "_meta.json").read_text()).get("reason", "") if (d / "_meta.json").exists() else ""
    shutil.rmtree(d)
    return reason


class Edit(BaseModel):
    before: str = Field(description="an existing résumé line, copied exactly (without its [tags])")
    after: str = Field(description="the same facts rewritten in the admired style; no new facts, numbers, tools or claims")
    why: str = Field(description="what was borrowed from the reference, in a few words")


class Edits(BaseModel):
    edits: list[Edit]


LINE_RE = re.compile(r"^- (.+?) (\[[a-z_, ]+\])\s*$")


def _sections(text: str) -> list[tuple[str, list[str]]]:
    out, cur = [], None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = (line[3:].split(" · ")[0], []); out.append(cur)
        elif cur and LINE_RE.match(line):
            cur[1].append(LINE_RE.match(line).group(1))
    return [s for s in out if s[1]]


def learn_from(reference_text: str, reference_name: str, prompt: str) -> None:
    """Background job. Updates STATUS as it goes."""
    from .llm import _system
    from .providers import structured
    files = [config.MASTER_DIR / n for n in ("02-experience.md", "03-projects.md") if (config.MASTER_DIR / n).exists()]
    blocks = [(f, name, lines) for f in files for name, lines in _sections(f.read_text(encoding="utf-8"))]
    STATUS.clear(); STATUS.update(state="running", reference=reference_name, prompt=prompt, total=len(blocks), done=0, changes=[], current="")
    snapshot(f"before learning from {reference_name}")
    task = ("Rewrite the person's résumé lines in the style of the reference résumé, following their instruction. "
            "Borrow structure, rhythm, verbs and how impact is framed. Keep every fact, number and name the same; add nothing. "
            "Return only lines that actually change.")
    try:
        for f, name, lines in blocks:
            STATUS["current"] = name
            body = (f"## Instruction\n{prompt}\n\n## Reference résumé ({reference_name})\n{reference_text[:12000]}\n\n"
                    f"## Lines for '{name}'\n" + "\n".join(f"- {l}" for l in lines))
            res = structured(_system(task), body, Edits, effort="medium", max_tokens=4000)
            text = f.read_text(encoding="utf-8")
            for e in res.edits:
                if e.before in text and e.after and e.after != e.before:
                    text = text.replace(e.before, e.after, 1)
                    STATUS["changes"].append({"where": name, "before": e.before, "after": e.after, "why": e.why})
            f.write_text(text, encoding="utf-8")
            STATUS["done"] += 1
        STATUS["state"] = "done"
    except Exception as ex:  # keep what was done; the snapshot can undo it
        STATUS.update(state="error", error=str(ex)[:300])


def start_learn_from(reference_text: str, reference_name: str, prompt: str) -> bool:
    if STATUS.get("state") == "running":
        return False
    threading.Thread(target=learn_from, args=(reference_text, reference_name, prompt), daemon=True).start()
    return True
