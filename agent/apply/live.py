"""Is a posting still open? Checked right before tailoring/applying."""
from __future__ import annotations
from ..sources.base import client

def still_open(job: dict) -> bool:
    raw_src = job.get("source")
    try:
        if raw_src == "ashby":
            org = (job.get("url") or "").split("/")[3]
            r = client.get(f"https://api.ashbyhq.com/posting-api/job-board/{org}")
            return r.status_code == 200 and any(j["id"] == job["external_id"] for j in r.json().get("jobs", []))
        if raw_src == "greenhouse":
            import json
            raw = json.loads(job["raw"]) if isinstance(job.get("raw"), str) else job.get("raw") or {}
            r = client.get(f"https://boards-api.greenhouse.io/v1/boards/{raw.get('board_token')}/jobs/{job['external_id']}")
            return r.status_code == 200
        if raw_src == "lever":
            r = client.get(f"https://api.lever.co/v0/postings/{(job.get('raw') or {}).get('slug') if isinstance(job.get('raw'), dict) else ''}/{job['external_id']}")
            return r.status_code == 200
    except Exception:
        return True  # network trouble: don't drop the job, let the form step find out
    return True
