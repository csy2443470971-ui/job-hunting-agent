"""The agent, step by step: who does each step, with which model and prompt, what it reads and what it hands on.

This is documentation that lives next to the code it describes. `python scripts/export_pipeline.py` renders it as
docs/pipeline.md and as the data behind the deck's appendix. `runs` is one of:
  you     you do it in the dashboard
  model   a call to the model (JHA_MODEL)
  draft   a call to the draft model (JHA_DRAFT_MODEL), or the model when there is none
  code    plain code, no model
`prompt` names a constant in agent/prompts.py; every model call also reads the system prefix (prompts.SYSTEM).
"""

NODES = [
    # ------------------------------------------------------------------ 01 · tell it everything
    dict(id="tell", step="01", name="Tell it everything", lane="you", runs="you", code="dashboard → Storybook",
         reads=[("", "files you drop (old résumés, reference letters, papers, voice memos) and what you type or say")],
         gives=[("storybook_add", "the files' text and your note"), ("storybook_style", "one résumé you like, and how to use it")]),
    dict(id="storybook_add", step="01", name="Add to the storybook", lane="agent", runs="model", prompt="STORYBOOK_ADD", schema="Additions",
         code="agent/storybook.py · add_from",
         reads=[("tell", "the text of each file (PDF, DOCX, audio transcribed locally) and your note"), ("storybook", "what it already says")],
         gives=[("storybook", "new résumé lines, each with the file it came from; Back undoes the batch")],
         note="A résumé that is about someone else adds nothing about you; on its own it goes to Learn a style instead."),
    dict(id="storybook_style", step="01", name="Learn a style", lane="agent", runs="model", prompt="STORYBOOK_STYLE", schema="Edits",
         code="agent/storybook.py · learn_from",
         reads=[("tell", "a résumé you admire and your instruction (\"lead with the result\")"), ("storybook", "your résumé lines")],
         gives=[("storybook", "the same facts reworded in that style, line by line; Back undoes it")]),
    dict(id="intake", step="01", name="Intake draft (command line)", lane="agent", runs="draft", prompt="INTAKE", schema="Storybook",
         code="agent/intake.py · python -m agent.run intake",
         reads=[("", "every file in inbox/")],
         gives=[("", "a draft storybook (_intake-draft-<date>.md) you edit and move in by hand")]),
    dict(id="standing", step="01", name="Standing answers", lane="you", runs="you", code="dashboard → Setup / Storybook · agent/setup_answers.py",
         reads=[("", "your answers, once: legal name, work authorization, sponsorship, relocation, self-identification…")],
         gives=[("answers", "answers that override the model's"), ("fill", "filled on every form as written")]),
    dict(id="storybook", step="01", name="The storybook", lane="agent", runs="code", code="<profile>/master/*.md",
         reads=[("storybook_add", "added lines"), ("storybook_style", "reworded lines"), ("learn", "fixes you applied")],
         gives=[("", "every model call, as part of the system prefix: the only facts the agent may use about you")]),
    # ------------------------------------------------------------------ 02 · find and rank
    dict(id="find", step="02", name="Find postings", lane="agent", runs="code", code="agent/sources/ · agent/run.py · discover, prefilter",
         reads=[("", "public job boards: Greenhouse, Lever and Ashby boards of the companies you follow, Hacker News; no login")],
         gives=[("rank", "new postings (company, title, location, description), after a keyword filter drops obvious misses")]),
    dict(id="rank", step="02", name="Rank the fit", lane="agent", runs="draft", prompt="RANK", schema="JobScore",
         code="agent/jev.py (Jev, TypeSafe) · agent/llm.py · score_job",
         reads=[("find", "each posting"), ("storybook", "your record and role lenses (06-roles.md)")],
         gives=[("tailor", "postings scoring at least min_score_to_queue, with the lens, reasons and gaps")],
         note="Jev rates every posting first when TYPESAFE_API_KEY is set; the model then reads the likely fits. Under 50 is never applied to."),
    # ------------------------------------------------------------------ 03 · the résumé and the form
    dict(id="tailor", step="03", name="Write the résumé", lane="agent", runs="model", prompt="TAILOR", schema="ResumeContent",
         code="agent/llm.py · tailor_resume → agent/resume/render.py",
         reads=[("rank", "the posting and its score notes (lens, reasons, gaps)"), ("storybook", "the facts")],
         gives=[("check", "résumé lines to check"), ("review", "a one-page PDF (links, headline and awards are set by code)")]),
    dict(id="check", step="03", name="Writing check", lane="agent", runs="model", prompt="REPAIR", schema="Repaired",
         code="agent/voicecheck.py (rules) · agent/llm.py · repair_text",
         reads=[("tailor", "every line"), ("answers", "every answer"), ("email", "every email")],
         gives=[("review", "the same text with banned phrases rewritten, same facts; anything left is flagged for you")],
         note="The rules are code (agent/voicecheck.py and the phrases you taught it); the model only rewrites what they flag."),
    dict(id="answers", step="03", name="Answer the form", lane="agent", runs="model", prompt="ANSWERS", extra="WHY_US", schema="FormAnswers",
         code="agent/llm.py · answer_form · agent/mission.py",
         reads=[("", "the form's questions, read live from the page"), ("rank", "the posting"),
                ("", "the company's mission in its own words (code: found in its postings)"), ("standing", "standing answers")],
         gives=[("fill", "an answer for every field"), ("review", "questions only you can answer, with the form's own options")],
         note="Why-us questions add the WHY_US rule: open with the company's mission, then why it matters to you."),
    dict(id="fill", step="03", name="Fill the form", lane="agent", runs="code", code="agent/apply/fill.py · the agent's browser",
         reads=[("answers", "answers"), ("standing", "standing answers"), ("tailor", "the résumé PDF"),
                ("", "the agent's browser profile, with any sign-ins you made yourself")],
         gives=[("review", "a full-page screenshot of the filled form; Submit is never pressed here")]),
    dict(id="cover", step="03", name="Cover letter (first version)", lane="agent", runs="model", prompt="COVER", schema="CoverDraft",
         code="agent/cover.py · python -m agent.run cover <job_id>",
         reads=[("rank", "the posting and any research notes"), ("storybook", "the facts")],
         gives=[("review", "a cover letter and a why-us answer, or what you must write yourself")]),
    # ------------------------------------------------------------------ 04 · you decide
    dict(id="review", step="04", name="You review", lane="you", runs="you", code="dashboard → Waiting for review",
         reads=[("tailor", "the résumé"), ("fill", "the form screenshot"), ("answers", "questions for you"), ("", "a checklist that must pass")],
         gives=[("submit", "Approve"), ("revise", "Change this résumé: what to change, typed or spoken"), ("learn", "Reject, with a note")]),
    dict(id="revise", step="04", name="Revise the résumé", lane="agent", runs="model", prompt="REVISE", schema="ResumeContent",
         code="agent/run.py · revise · /api/applications/<id>/revise",
         reads=[("review", "your note"), ("tailor", "the current résumé"), ("rank", "the posting"), ("storybook", "the facts")],
         gives=[("review", "the résumé re-rendered in place (writing check, one page); a green dot when done")],
         note="A branch: it changes this one application's résumé only. Asks the storybook can't support are left out and noted."),
    dict(id="learn", step="04", name="Learn from notes", lane="agent", runs="draft", prompt="LEARN", schema="Patches",
         code="agent/learn.py",
         reads=[("review", "your notes and the reasons you rejected drafts"), ("", "the writing brief and preferences.yaml")],
         gives=[("storybook", "proposed fixes you apply or dismiss one by one: a brief example, a storybook line, a banned phrase, a preference")]),
    # ------------------------------------------------------------------ 05 · out the door, and back
    dict(id="submit", step="05", name="Submit", lane="agent", runs="code", code="agent/run.py · submit_approved · agent/apply/fill.py",
         reads=[("review", "approved applications only")],
         gives=[("track", "the application, sent on the employer's site, in a visible browser")],
         note="A CAPTCHA or an emailed security code stops it: you finish it in that window. LinkedIn and Indeed are never automated."),
    dict(id="email", step="05", name="Email applications", lane="agent", runs="model", prompt="EMAIL", extra="EMAIL_PROBLEM", schema="EmailDraft",
         code="agent/llm.py · draft_email · agent/mailbox.py · send",
         reads=[("rank", "the posting, post or article"), ("storybook", "the facts")],
         gives=[("review", "a draft to approve or edit"), ("track", "after Approve: sent from your mailbox (SMTP)")]),
    dict(id="track", step="05", name="Track replies", lane="agent", runs="code", code="agent/mailbox.py · fetch (IMAP) · agent/replies.py",
         reads=[("", "your application mailbox, read-only: nothing is marked read, moved or deleted")],
         gives=[("", "each reply sorted by rules (received, next step, interview, offer, rejected) and its application moved on in Applied")]),
]

RUNS = {"you": "You", "model": "The model", "draft": "The draft model (or the model)", "code": "Code, no model"}
STEPS = {"01": "Tell it everything", "02": "Find and rank", "03": "The résumé and the form", "04": "You decide", "05": "Out the door, and back"}
