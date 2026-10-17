"""Shared HTTP + source interface."""
from __future__ import annotations
import re
import html as _html
import httpx
from ..config import USER_AGENT

client = httpx.Client(timeout=30, headers={"User-Agent": USER_AGENT}, follow_redirects=True)


def strip_html(s: str | None) -> str:
    if not s:
        return ""
    s = _html.unescape(s)
    s = re.sub(r"<br\s*/?>|</p>|</li>|</div>|</h\d>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def looks_remote(*texts: str | None) -> bool:
    blob = " ".join(t or "" for t in texts).lower()
    return "remote" in blob or "anywhere" in blob or "distributed" in blob


class Source:
    """A source yields job dicts with at least: source, external_id, company, title, url, description."""
    name = "base"

    def fetch(self) -> list[dict]:  # pragma: no cover
        raise NotImplementedError
