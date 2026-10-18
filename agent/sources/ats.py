"""Public, no-auth ATS job-board endpoints. These are the most reliable sources:
the company itself publishes them, and several accept applications by API."""
from __future__ import annotations
from .base import client, strip_html, looks_remote

# ---- Greenhouse ---------------------------------------------------------
def _gh_form(token: str, j: dict) -> str:
    """Companies that embed Greenhouse on their own careers page get the hosted form instead,
    so the form filler sees the application, not the company site (cookie banners, nav)."""
    u = j.get("absolute_url") or ""
    return u if "greenhouse.io" in u else f"https://job-boards.greenhouse.io/embed/job_app?for={token}&token={j['id']}"


def greenhouse_jobs(token: str, company: str | None = None) -> list[dict]:
    r = client.get(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs", params={"content": "true"})
    if r.status_code != 200:
        return []
    out = []
    for j in r.json().get("jobs", []):
        desc = strip_html(j.get("content"))
        loc = (j.get("location") or {}).get("name")
        out.append({
            "source": "greenhouse", "external_id": str(j["id"]), "company": company or token,
            "title": j.get("title"), "location": loc, "remote": looks_remote(loc, j.get("title")),
            "url": j.get("absolute_url"), "apply_url": _gh_form(token, j),
            "description": desc, "posted_at": j.get("updated_at"),
            "raw": {"board_token": token, "id": j["id"], "departments": j.get("departments"), "offices": j.get("offices")},
        })
    return out


def greenhouse_questions(token: str, job_id: str | int) -> dict:
    """Application form questions for a posting (used to fill the form by API)."""
    r = client.get(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs/{job_id}", params={"questions": "true"})
    return r.json() if r.status_code == 200 else {}


# ---- Lever --------------------------------------------------------------
def lever_jobs(company_slug: str, company: str | None = None) -> list[dict]:
    r = client.get(f"https://api.lever.co/v0/postings/{company_slug}", params={"mode": "json"})
    if r.status_code != 200:
        return []
    out = []
    for j in r.json():
        cats = j.get("categories") or {}
        loc = cats.get("location")
        desc = strip_html(j.get("descriptionPlain") or j.get("description"))
        for section in j.get("lists") or []:
            desc += f"\n\n{section.get('text','')}\n" + strip_html(section.get("content"))
        out.append({
            "source": "lever", "external_id": j["id"], "company": company or company_slug,
            "title": j.get("text"), "location": loc,
            "remote": looks_remote(loc, cats.get("commitment"), j.get("workplaceType")),
            "url": j.get("hostedUrl"), "apply_url": j.get("applyUrl"),
            "description": desc, "posted_at": None,
            "raw": {"slug": company_slug, "id": j["id"], "team": cats.get("team"), "commitment": cats.get("commitment")},
        })
    return out


# ---- Ashby --------------------------------------------------------------
def ashby_jobs(org: str, company: str | None = None) -> list[dict]:
    r = client.get(f"https://api.ashbyhq.com/posting-api/job-board/{org}", params={"includeCompensation": "true"})
    if r.status_code != 200:
        return []
    out = []
    for j in r.json().get("jobs", []):
        loc = j.get("location")
        out.append({
            "source": "ashby", "external_id": j["id"], "company": company or org,
            "title": j.get("title"), "location": loc,
            "remote": bool(j.get("isRemote")) or looks_remote(loc),
            "url": j.get("jobUrl"), "apply_url": j.get("applyUrl"),
            "description": strip_html(j.get("descriptionHtml")) or j.get("descriptionPlain", ""),
            "posted_at": j.get("publishedAt"),
            "raw": {"org": org, "id": j["id"], "department": j.get("department"), "team": j.get("team"),
                    "employmentType": j.get("employmentType"), "compensation": j.get("compensation")},
        })
    return out


# ---- discovery ----------------------------------------------------------
def probe_company(slug: str) -> list[tuple[str, str]]:
    """Try a slug against the three ATSs. Returns [(ats, token)] that respond."""
    found = []
    if client.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs").status_code == 200:
        found.append(("greenhouse", slug))
    if client.get(f"https://api.lever.co/v0/postings/{slug}", params={"mode": "json"}).status_code == 200:
        found.append(("lever", slug))
    if client.get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}").status_code == 200:
        found.append(("ashby", slug))
    return found


FETCHERS = {"greenhouse": greenhouse_jobs, "lever": lever_jobs, "ashby": ashby_jobs}


def fetch_company(entry: dict) -> list[dict]:
    """entry from profile/companies.yaml: {name, ats, board_token, sector}"""
    fn = FETCHERS.get(entry.get("ats"))
    if not fn or not entry.get("board_token"):
        return []
    jobs = fn(entry["board_token"], entry.get("name"))
    for j in jobs:
        j["sector"] = entry.get("sector")
    return jobs
