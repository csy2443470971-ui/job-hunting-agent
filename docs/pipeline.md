# How the agent works, step by step

Generated from `agent/pipeline.py` and `agent/prompts.py` by `python scripts/export_pipeline.py`. Do not edit by hand.

Every model call sends the same system prefix, then one task line, then the step's input:

```text
## House rules (docs/00-house-rules.md)
…the one-page writing brief…

## Preferences (preferences.yaml)
…what to apply for, where, how often…

## Master documents (the storybook)
…every file in profile/master…

## Task
<one task line below>
```

**Who runs a step:** *you* in the dashboard; *the model* (`JHA_MODEL`); *the draft model* (`JHA_DRAFT_MODEL`, or the model when there is none); or plain *code*. Models are set in `.env` or on the dashboard's Setup page (see `agent/providers.py`).

## 01 · Tell it everything

### Tell it everything

**Runs:** You · `dashboard → Storybook`

**Reads**

- files you drop (old résumés, reference letters, papers, voice memos) and what you type or say

**Hands on**

- to **Add to the storybook**: the files' text and your note
- to **Learn a style**: one résumé you like, and how to use it

### Add to the storybook

**Runs:** The model · `agent/storybook.py · add_from` · output: `Additions`

**Reads**

- from **Tell it everything**: the text of each file (PDF, DOCX, audio transcribed locally) and your note
- from **The storybook**: what it already says

**Hands on**

- to **The storybook**: new résumé lines, each with the file it came from; Back undoes the batch

**Prompt** (`prompts.STORYBOOK_ADD`)

```text
Add what this material says about the person to their storybook. Use only facts the material states: never guess numbers, titles, dates, degrees or tools. Skip anything the storybook already says. One fact per line, résumé-ready, result first when the material gives one. In reference letters keep what the writer says the person did, not the praise. A file about someone else adds nothing: list it in about_someone_else.
```

> A résumé that is about someone else adds nothing about you; on its own it goes to Learn a style instead.

### Learn a style

**Runs:** The model · `agent/storybook.py · learn_from` · output: `Edits`

**Reads**

- from **Tell it everything**: a résumé you admire and your instruction ("lead with the result")
- from **The storybook**: your résumé lines

**Hands on**

- to **The storybook**: the same facts reworded in that style, line by line; Back undoes it

**Prompt** (`prompts.STORYBOOK_STYLE`)

```text
Rewrite the person's résumé lines in the style of the reference résumé, following their instruction. Borrow structure, rhythm, verbs and how impact is framed. Keep every fact, number and name the same; add nothing. Return only lines that actually change.
```

### Intake draft (command line)

**Runs:** The draft model (or the model) · `agent/intake.py · python -m agent.run intake` · output: `Storybook`

**Reads**

- every file in inbox/

**Hands on**

- a draft storybook (_intake-draft-<date>.md) you edit and move in by hand

**Prompt** (`prompts.INTAKE`)

```text
Turn the raw material into storybook entries. Every line must be traceable to a file; list contradictions as conflicts; copy the person's own sentences verbatim into voice_samples.
```

### Standing answers

**Runs:** You · `dashboard → Setup / Storybook · agent/setup_answers.py`

**Reads**

- your answers, once: legal name, work authorization, sponsorship, relocation, self-identification…

**Hands on**

- to **Answer the form**: answers that override the model's
- to **Fill the form**: filled on every form as written

### The storybook

**Runs:** Code, no model · `<profile>/master/*.md`

**Reads**

- from **Add to the storybook**: added lines
- from **Learn a style**: reworded lines
- from **Learn from notes**: fixes you applied

**Hands on**

- every model call, as part of the system prefix: the only facts the agent may use about you

## 02 · Find and rank

### Find postings

**Runs:** Code, no model · `agent/sources/ · agent/run.py · discover, prefilter`

**Reads**

- public job boards: Greenhouse, Lever and Ashby boards of the companies you follow, Hacker News; no login

**Hands on**

- to **Rank the fit**: new postings (company, title, location, description), after a keyword filter drops obvious misses

### Rank the fit

**Runs:** The draft model (or the model) · `agent/jev.py (Jev, TypeSafe) · agent/llm.py · score_job` · output: `JobScore`

**Reads**

- from **Find postings**: each posting
- from **The storybook**: your record and role lenses (06-roles.md)

**Hands on**

- to **Write the résumé**: postings scoring at least min_score_to_queue, with the lens, reasons and gaps

**Prompt** (`prompts.RANK`)

```text
Judge whether {first_name} is a credible candidate for this posting, as a strict recruiter in that field would. Map it to one role family below; respect that family's seniority guard (cap at 50, action 'maybe'). Work authorisation is settled, so it is never a blocker. Role families: {roles}
```

> Jev rates every posting first when TYPESAFE_API_KEY is set; the model then reads the likely fits. Under 50 is never applied to.

## 03 · The résumé and the form

### Write the résumé

**Runs:** The model · `agent/llm.py · tailor_resume → agent/resume/render.py` · output: `ResumeContent`

**Reads**

- from **Rank the fit**: the posting and its score notes (lens, reasons, gaps)
- from **The storybook**: the facts

**Hands on**

- to **Writing check**: résumé lines to check
- to **You review**: a one-page PDF (links, headline and awards are set by code)

**Prompt** (`prompts.TAILOR`)

```text
Build the one-page résumé content for this posting through the matching lens in 06-roles.md. Mark each item's provenance honestly; 'new' items must stay under {diy_max}. Where a piece of work has a URL in the master documents, set link_text and link.
```

### Writing check

**Runs:** The model · `agent/voicecheck.py (rules) · agent/llm.py · repair_text` · output: `Repaired`

**Reads**

- from **Write the résumé**: every line
- from **Answer the form**: every answer
- from **Email applications**: every email

**Hands on**

- to **You review**: the same text with banned phrases rewritten, same facts; anything left is flagged for you

**Prompt** (`prompts.REPAIR`)

```text
Rewrite the text to fix the listed problems. Same facts, same or shorter length.
```

> The rules are code (agent/voicecheck.py and the phrases you taught it); the model only rewrites what they flag.

### Answer the form

**Runs:** The model · `agent/llm.py · answer_form · agent/mission.py` · output: `FormAnswers`

**Reads**

- the form's questions, read live from the page
- from **Rank the fit**: the posting
- the company's mission in its own words (code: found in its postings)
- from **Standing answers**: standing answers

**Hands on**

- to **Fill the form**: an answer for every field
- to **You review**: questions only you can answer, with the form's own options

**Prompt** (`prompts.ANSWERS`)

```text
Answer this application form. Anything only {first_name} can answer goes in needs_human with a short reason.
```

**Added when it applies** (`prompts.WHY_US`)

```text
For a why-us question (why this company, what excites you about us): open with the company's mission in a sentence, in their words or close to them; then why it matters to the candidate as a person: character, habits, what they love doing (07-voice.md); experience last, one light touch at most. Never open with the candidate. A little American warmth and energy is welcome; hype words are not.
```

> Why-us questions add the WHY_US rule: open with the company's mission, then why it matters to you.

### Fill the form

**Runs:** Code, no model · `agent/apply/fill.py · the agent's browser`

**Reads**

- from **Answer the form**: answers
- from **Standing answers**: standing answers
- from **Write the résumé**: the résumé PDF
- the agent's browser profile, with any sign-ins you made yourself

**Hands on**

- to **You review**: a full-page screenshot of the filled form; Submit is never pressed here

### Cover letter (first version)

**Runs:** The model · `agent/cover.py · python -m agent.run cover <job_id>` · output: `CoverDraft`

**Reads**

- from **Rank the fit**: the posting and any research notes
- from **The storybook**: the facts

**Hands on**

- to **You review**: a cover letter and a why-us answer, or what you must write yourself

**Prompt** (`prompts.COVER`)

```text
Draft a cover letter and a 'Why {company}' answer for {first_name}. Use only storybook facts and what the posting or research says about the company. If the employer requires the candidate's own first draft, leave both fields empty and explain in needs_human.
```

## 04 · You decide

### You review

**Runs:** You · `dashboard → Waiting for review`

**Reads**

- from **Write the résumé**: the résumé
- from **Fill the form**: the form screenshot
- from **Answer the form**: questions for you
- a checklist that must pass

**Hands on**

- to **Submit**: Approve
- to **Revise the résumé**: Change this résumé: what to change, typed or spoken
- to **Learn from notes**: Reject, with a note

### Revise the résumé

**Runs:** The model · `agent/run.py · revise · /api/applications/<id>/revise` · output: `ResumeContent`

**Reads**

- from **You review**: your note
- from **Write the résumé**: the current résumé
- from **Rank the fit**: the posting
- from **The storybook**: the facts

**Hands on**

- to **You review**: the résumé re-rendered in place (writing check, one page); a green dot when done

**Prompt** (`prompts.REVISE`)

```text
Revise this one-page résumé as the person asks. Change only what the note asks for; keep everything else as it is. Facts, numbers, titles and dates come from the master documents only: if the note asks for something they don't support, leave it out and say so in tailoring_notes. Keep provenance honest.
```

> A branch: it changes this one application's résumé only. Asks the storybook can't support are left out and noted.

### Learn from notes

**Runs:** The draft model (or the model) · `agent/learn.py` · output: `Patches`

**Reads**

- from **You review**: your notes and the reasons you rejected drafts
- the writing brief and preferences.yaml

**Hands on**

- to **The storybook**: proposed fixes you apply or dismiss one by one: a brief example, a storybook line, a banned phrase, a preference

**Prompt** (`prompts.LEARN`)

```text
Propose the smallest patches that would have prevented each problem. Prefer one example row in the brief over a new rule; keep the brief to one page. Use storybook_line only to reword an existing line with the same facts, quoting it exactly in 'before'. Use ban_phrase for a phrase that should never appear. Use preference for changes to what to apply for, where, or how often: replace one exact line of preferences.yaml in 'before' with the edited line in 'after'. Skip notes that need no change.
```

## 05 · Out the door, and back

### Submit

**Runs:** Code, no model · `agent/run.py · submit_approved · agent/apply/fill.py`

**Reads**

- from **You review**: approved applications only

**Hands on**

- to **Track replies**: the application, sent on the employer's site, in a visible browser

> A CAPTCHA or an emailed security code stops it: you finish it in that window. LinkedIn and Indeed are never automated.

### Email applications

**Runs:** The model · `agent/llm.py · draft_email · agent/mailbox.py · send` · output: `EmailDraft`

**Reads**

- from **Rank the fit**: the posting, post or article
- from **The storybook**: the facts

**Hands on**

- to **You review**: a draft to approve or edit
- to **Track replies**: after Approve: sent from your mailbox (SMTP)

**Prompt** (`prompts.EMAIL`)

```text
Write a {kind} email from {first_name} to this company. Hinge it on one concrete thing in the context; if the context is thin, write less rather than pad.
```

**Added when it applies** (`prompts.EMAIL_PROBLEM`)

```text
Propose, in 2-3 sentences, what the person would do about it, grounded in what they have actually done.
```

### Track replies

**Runs:** Code, no model · `agent/mailbox.py · fetch (IMAP) · agent/replies.py`

**Reads**

- your application mailbox, read-only: nothing is marked read, moved or deleted

**Hands on**

- each reply sorted by rules (received, next step, interview, offer, rejected) and its application moved on in Applied
