"""Render agent/pipeline.py (with the prompts from agent/prompts.py) as docs/pipeline.md, and as data for the deck.

    python scripts/export_pipeline.py [deck/pipeline.js]

The deck's file is a script (window.PIPELINE = …) so the deck works when opened straight from disk.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agent import prompts, pipeline  # noqa: E402

names = {n["id"]: n["name"] for n in pipeline.NODES}


def where(i: str) -> str:
    return names.get(i, "")


nodes = []
for n in pipeline.NODES:
    nodes.append({**n, "runs_label": pipeline.RUNS[n["runs"]],
                  "prompt_text": getattr(prompts, n["prompt"]) if n.get("prompt") else "",
                  "extra_text": getattr(prompts, n["extra"]) if n.get("extra") else "",
                  "reads": [{"from": f, "from_name": where(f), "what": w} for f, w in n["reads"]],
                  "gives": [{"to": t, "to_name": where(t), "what": w} for t, w in n["gives"]]})

md = ["# How the agent works, step by step", "",
      "Generated from `agent/pipeline.py` and `agent/prompts.py` by `python scripts/export_pipeline.py`. Do not edit by hand.", "",
      "Every model call sends the same system prefix, then one task line, then the step's input:", "",
      "```text", prompts.SYSTEM, "```", "",
      "**Who runs a step:** *you* in the dashboard; *the model* (`JHA_MODEL`); *the draft model* (`JHA_DRAFT_MODEL`, or the model when "
      "there is none); or plain *code*. Models are set in `.env` or on the dashboard's Setup page (see `agent/providers.py`).", ""]
for step, title in pipeline.STEPS.items():
    md += [f"## {step} · {title}", ""]
    for n in [x for x in nodes if x["step"] == step]:
        md += [f"### {n['name']}", "", f"**Runs:** {n['runs_label']} · `{n['code']}`" + (f" · output: `{n['schema']}`" if n.get("schema") else ""), ""]
        md += ["**Reads**", ""] + [f"- {('from **' + r['from_name'] + '**: ') if r['from_name'] else ''}{r['what']}" for r in n["reads"]] + [""]
        md += ["**Hands on**", ""] + [f"- {('to **' + g['to_name'] + '**: ') if g['to_name'] else ''}{g['what']}" for g in n["gives"]] + [""]
        if n["prompt_text"]:
            md += [f"**Prompt** (`prompts.{n['prompt']}`)", "", "```text", n["prompt_text"], "```", ""]
        if n["extra_text"]:
            md += [f"**Added when it applies** (`prompts.{n['extra']}`)", "", "```text", n["extra_text"], "```", ""]
        if n.get("note"):
            md += [f"> {n['note']}", ""]
(ROOT / "docs" / "pipeline.md").write_text("\n".join(md), encoding="utf-8")
out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "deck" / "pipeline.js"
if out.parent.exists():
    data = json.dumps({"system": prompts.SYSTEM, "steps": pipeline.STEPS, "nodes": nodes}, ensure_ascii=False, indent=1)
    out.write_text(f"window.PIPELINE = {data};\n" if out.suffix == ".js" else data, encoding="utf-8")
print(f"docs/pipeline.md · {out if out.parent.exists() else '(no deck folder)'} · {len(nodes)} steps")
