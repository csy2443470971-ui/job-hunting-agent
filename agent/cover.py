"""Node 5 · Cover letter and "Why this company".

Status: first version. The prompt is not tuned yet; expect to edit drafts in the dashboard.
Respects employer AI policies: when the posting requires the candidate's own first draft, it returns
needs_human instead of writing the answer.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from . import config
from .providers import structured


class CoverDraft(BaseModel):
    cover_letter: str = Field(description="150-250 words; one specific reason for this company, two pieces of evidence, a clear close")
    why_company: str = Field(description="90-150 words answering 'Why <company>?' with facts from the posting or public sources")
    evidence_used: list[str] = Field(description="storybook lines the drafts rely on")
    needs_human: list[str] = Field(description="parts that must be written by the person, with the reason")


def draft(job: dict, research: str = "") -> CoverDraft:
    from .llm import _system
    task = (f"Draft a cover letter and a 'Why {job.get('company')}' answer for {config.first_name()}. Use only storybook facts "
            "and what the posting or research says about the company. If the employer requires the candidate's own first draft, "
            "leave both fields empty and explain in needs_human.")
    body = (f"Company: {job.get('company')}\nTitle: {job.get('title')}\n\n## Posting\n{(job.get('description') or '')[:10000]}"
            + (f"\n\n## Research notes\n{research[:6000]}" if research else ""))
    return structured(_system(task), body, CoverDraft, effort="high", max_tokens=6000)
