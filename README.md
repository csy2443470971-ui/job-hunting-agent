<p align="center"><img src="docs/brand/icon.png" width="96" alt=""></p>

# Job Hunter Agent

A personal agent that turns your own material into job applications: it finds postings, ranks them, writes a
one-page résumé from facts you approved, fills the form or drafts the email, and waits for you to say yes.

<a href="https://siennachen.com/project-job-hunting-agent.html"><img src="docs/media/job-hunter-agent-film-cover.jpg" alt="Job Hunter Agent, the 52-second product film: click to watch with sound" width="100%"></a>

▶ **[Watch the 52-second film](https://siennachen.com/project-job-hunting-agent.html)** (sound on) · or the [mp4 in this repo](docs/media/job-hunter-agent-film.mp4). It shows demo data: a fictional applicant and fictional companies, and the application form is filled by the agent's own code.

## Install

One command installs everything and opens the app. Its **Setup** page then walks you through the rest.

| | |
|---|---|
| **Mac** | `git clone https://github.com/csy2443470971-ui/job-hunting-agent && cd job-hunting-agent && ./install.sh` <br>Job Hunter Agent goes into Applications, with its icon in the Dock. |
| **Windows 10 / 11** | Download the repo ([ZIP](https://github.com/csy2443470971-ui/job-hunting-agent/archive/refs/heads/main.zip)), unzip it, right-click **install.ps1** → *Run with PowerShell*. <br>Job Hunter Agent goes into the Start menu and onto the desktop. |
| **Linux** | `./install.sh` adds Job Hunter Agent to your applications menu. |

You need Python 3.10 or newer (the installer tells you how if it's missing). The app runs on your computer: the
dashboard, your storybook, your answers and your mail settings never leave it. Opening the app again brings back the
same window; there is only ever one.

<details><summary>Without the installer</summary>

```bash
pip install -r requirements.txt
python -m playwright install chromium
python -m agent.run init        # your private profile/ and .env
python -m dashboard.app         # then open http://127.0.0.1:8765 and follow Setup
```
</details>

## First run: the Setup page

| Step | | What you do |
|---|---|---|
| 1 · Connect a model | required | Pick the model, and optionally a draft model (below). *Test* makes one small call to prove it answers. |
| 2 · Standing answers | required | The questions every form asks, answered once: legal name, work authorization, sponsorship, relocation, education, voluntary self-identification (each has *Prefer not to say*). |
| 3 · Tell it everything | required | Drop old résumés, reference letters, papers, notes, voice memos, or just talk. It turns them into résumé lines, each with its source, and invents nothing. |
| 4 · Your mailbox | optional | An app password, so it can tell you who wrote back and send the emails you approve. |
| 5 · The agent's browser | optional | Sign in, yourself, to sites where you keep a job account (a company's Workday). |
| 6 · Jev | optional | Ranks every posting before a model reads it: faster and cheaper. |

`python -m agent.run setup` prints the same checklist in a terminal.

## Models

Two settings, on the Setup page or in `.env`:

- **`JHA_MODEL`**, *the model*: everything that goes out under your name or decides what is true about you: the résumé,
  form answers, emails, revisions, and what gets added to your storybook.
- **`JHA_DRAFT_MODEL`**, *the draft model*, optional: first passes over the many: ranking every posting, proposing fixes
  from your notes, the intake draft you edit by hand. Leave it empty and the model does everything.

| Write it as | Runs on | Needs |
|---|---|---|
| `anthropic:claude-opus-5-5` | Claude through the API | `ANTHROPIC_API_KEY` |
| `claude-code` | your Claude Code login | `claude` installed and signed in; no key |
| `ollama:qwen3:32b` | an open-source model on your computer | [Ollama](https://ollama.com), then `ollama pull qwen3:32b` |
| `openai:Qwen/Qwen3-32B` | any OpenAI-compatible server: vLLM, LM Studio, llama.cpp, OpenRouter, Together | `JHA_OPENAI_BASE_URL` (and `JHA_OPENAI_API_KEY` if it needs one) |

For example: `JHA_MODEL=anthropic:claude-opus-5-5` with `JHA_DRAFT_MODEL=anthropic:claude-haiku-5-5`; or everything on your
own machine with `ollama:qwen3:32b` and `ollama:qwen3:4b`; or a hosted model for writing and a local one for ranking.
`python -m agent.run models --test` checks both. Every call goes through one function, `structured()` in
`agent/providers.py`, so adding a provider means adding one function there. Running vLLM with speculative decoding
(its own draft model) is a server setting and needs nothing here.

## How it works

Every step, with who runs it, its prompt, what it reads and what it hands on, is in **[docs/pipeline.md](docs/pipeline.md)**,
generated from `agent/pipeline.py` and `agent/prompts.py` (every prompt the agent sends lives in that one file).

| # | Step | Who | What happens |
|---|---|---|---|
| 01 | Tell it everything | you → model | Files you drop and what you say become storybook lines with their sources; Back undoes them. A résumé you like teaches it a style. |
| 02 | Find and rank | code → draft model | Public boards (Greenhouse, Lever, Ashby, Hacker News); Jev and the draft model rank every posting. Under 50 is never applied to. |
| 03 | The résumé and the form | model → code | A one-page résumé per posting from the storybook, a writing check, answers for the form, then the form filled in the agent's browser, with a screenshot. Nothing is submitted. |
| 04 | You decide | you | Approve; *Change this résumé* (typed or spoken: the model revises it, a green dot when done); or Reject with a note, which becomes a proposed fix. |
| 05 | Out the door, and back | code | Approved forms are submitted in a visible browser; approved emails go from your mailbox; replies are read and each application moves to *Heard back*, *Rejected* or *No reply yet*. |

## Access: what the agent can reach, and how you give it

| | How | What it never does |
|---|---|---|
| **Job boards** | Public pages; no login | — |
| **Your mailbox** | An app password you create and can revoke (Setup → Mailbox) | Mark read, move, label, delete or reply; send anything you didn't approve |
| **Sites that need an account** | The agent's own browser profile (Chrome when installed), separate from yours: you sign in there yourself, once | See, type or store a password |
| **LinkedIn, Indeed** | Not used | Automate them. Their terms forbid it and accounts get restricted; put your LinkedIn URL in your standing answers and the agent fills it into forms |
| **CAPTCHAs, emailed security codes** | You, in the agent's window; it stops and tells you | Solve or type them |
| **Submitting** | Only after you click Approve | Submit or send on its own |

## Every day

Open the app and press **Refresh** (bottom left): it updates the app itself, finds new postings and reads new replies.
Or run `python -m agent.run daily` on a schedule (cron, launchd, Task Scheduler) to also write résumés and fill forms
overnight; it never submits. Then review in **Job applications**.

## Not autopilot

The agent runs on your judgement. Your storybook decides what can be said, your taste decides what goes out, and every
application stops in the dashboard, where you approve it, edit it, or send it back with a note. Notes and rejection reasons
become proposed fixes (`agent/learn.py`): an example in the writing brief, a reworded storybook line, a phrase to block,
a preference. Nothing changes until you apply one, and every applied fix can be reverted.

`docs/00-house-rules.md` is the one-page writing brief every model call reads. Mechanical rules live in code: plain
job-title headlines (`agent/headline.py`), links as words (`agent/links.py`), writing checks (`agent/voicecheck.py`),
one page (`agent/resume/render.py`).

## Your data

`profile/` (storybook, standing answers, preferences), `data/` (the database and the agent's browser profile), `out/`,
`inbox/` and `.env` are git-ignored and stay on your computer. `profile.example/` holds a fictional person so you can see
the format. Several stories at once: keep one storybook per story under `profiles/` and pick one with `JHA_PROFILE`.

Try it without your own data: `JHA_PROFILE=profile.example JHA_DB=data/demo.sqlite python scripts/demo.py`, then start
the dashboard with the same two variables.

More: [User guide](USER_GUIDE.md) · [Every step and prompt](docs/pipeline.md) · other commands: `intake`, `discover`,
`score`, `tailor <job_id>`, `cover <job_id>`, `prepare`, `submit --app <id>`, `outbox`, `status`, `browser`, `models`.

## License

MIT
