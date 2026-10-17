"""Hacker News monthly 'Who is hiring?' thread via the Algolia API (no auth)."""
from __future__ import annotations
import re
from .base import client, strip_html, looks_remote

ALGOLIA = "https://hn.algolia.com/api/v1"


def latest_thread_id() -> int | None:
    r = client.get(f"{ALGOLIA}/search_by_date", params={"query": "Ask HN: Who is hiring?", "tags": "story,author_whoishiring", "hitsPerPage": 1})
    hits = r.json().get("hits", []) if r.status_code == 200 else []
    return int(hits[0]["objectID"]) if hits else None


def fetch(keywords: list[str] | None = None) -> list[dict]:
    tid = latest_thread_id()
    if not tid:
        return []
    out, page = [], 0
    while True:
        r = client.get(f"{ALGOLIA}/search_by_date", params={"tags": f"comment,story_{tid}", "hitsPerPage": 1000, "page": page})
        data = r.json()
        for h in data.get("hits", []):
            text = strip_html(h.get("comment_text") or "")
            if not text or h.get("parent_id") != tid:
                continue
            first = text.split("\n", 1)[0]
            company = re.split(r"\s*\|\s*", first)[0][:80]
            if keywords and not any(k.lower() in text.lower() for k in keywords):
                continue
            out.append({
                "source": "hn", "external_id": str(h["objectID"]), "company": company,
                "title": first[:160], "location": None, "remote": looks_remote(text),
                "url": f"https://news.ycombinator.com/item?id={h['objectID']}", "apply_url": None,
                "description": text, "posted_at": h.get("created_at"),
                "raw": {"thread": tid, "author": h.get("author")},
            })
        page += 1
        if page >= data.get("nbPages", 1):
            break
    return out
