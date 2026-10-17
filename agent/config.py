"""Central settings. Everything path-related lives here."""
from __future__ import annotations
import os
import re
from pathlib import Path
from dotenv import load_dotenv
import yaml

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "out"
RESUME_OUT = OUT_DIR / "resumes"
PROFILE_DIR = ROOT / "profile" if (ROOT / "profile").exists() else ROOT / "profile.example"
MASTER_DIR = PROFILE_DIR / "master"
DOCS_DIR = ROOT / "docs"
DB_PATH = Path(os.getenv("JHA_DB", str(DATA_DIR / "jobs.sqlite")))

for d in (DATA_DIR, RESUME_OUT, OUT_DIR / "emails"):
    d.mkdir(parents=True, exist_ok=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_TAILOR = os.getenv("MODEL_TAILOR", "claude-opus-5-5")
MODEL_SCORE = os.getenv("MODEL_SCORE", "claude-opus-5-5")
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")

USER_AGENT = "job-hunting-agent/0.1 (personal, low-volume)"


def _load_yaml(path: Path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or default


def preferences() -> dict:
    return _load_yaml(PROFILE_DIR / "preferences.yaml", {})


def roles() -> dict:
    return _load_yaml(PROFILE_DIR / "roles.yaml", {})


def companies() -> list[dict]:
    return _load_yaml(PROFILE_DIR / "companies.yaml", {}).get("companies", [])


def master_text() -> str:
    """Concatenate every markdown/text file in profile/master, in filename order.
    PDFs/DOCX should be converted to .md first (see docs/01)."""
    parts = []
    for p in sorted(MASTER_DIR.glob("*")):
        if p.suffix.lower() in {".md", ".txt"}:
            parts.append(f"\n\n<!-- file: {p.name} -->\n" + p.read_text(encoding="utf-8"))
    return "".join(parts).strip()


def profile() -> dict:
    """Person-specific data (profile/profile.yaml). Code never hard-codes a person."""
    return _load_yaml(PROFILE_DIR / "profile.yaml", {})


def first_name() -> str:
    return (profile().get("name") or "the candidate").split()[0]


def file_stem() -> str:
    return re.sub(r"\W+", "_", profile().get("name") or "Candidate").strip("_")
