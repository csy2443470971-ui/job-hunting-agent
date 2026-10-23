# User guide

Five minutes. Then the agent does the tedious part and you keep the parts that matter.

## Start

Install it ([README → Install](README.md#install)), open **Job Hunter Agent**, and follow the **Setup** page. It opens
there until the three required steps are done:

1. **Connect a model.** Claude through the API, your Claude Code login, or an open-source model on your own computer
   (Ollama) or server (vLLM, LM Studio, OpenRouter). Add a smaller *draft model* for ranking if you like. Press *Test*.
2. **Answer the standing questions.** Legal name, work authorization, sponsorship, relocation (and where), how you want to
   work, education, and the voluntary self-identification questions. Every one of those has *Prefer not to say*; pick it and
   the agent chooses the form's decline option. Until the required ones are answered, it prepares and submits nothing.
3. **Tell it everything.** On the **Storybook** page, drop whatever you have on *Drop anything*: old résumés, reference
   letters, papers, portfolio text, voice memos. Or tap the mic and just talk. It adds what the material says about you as
   résumé lines, each with the file it came from, and invents nothing. *Back to previous version* undoes it. Drop a résumé
   that isn't yours and it learns that résumé's style instead.

Then, when you want them: connect your **mailbox** (an app password; it reads replies and never changes your inbox), open
the **agent's browser** to sign in to sites where you keep an account, and add a **Jev** key for faster ranking.

## Three things to know

**A storybook is a story, not your autobiography.** Leave out what doesn't serve the story. Applying as a designer and as a
strategist? Keep two storybooks under `profiles/` and pick one with `JHA_PROFILE=profiles/<story>`. The agent only ever says
what the active storybook says.

**Nothing leaves without your yes.** The agent finds, ranks, writes and fills. It cannot submit or send until you click
Approve. CAPTCHAs, emailed security codes, LinkedIn and Indeed, salary questions, and any answer an employer wants in your own
words come to you, marked.

**It never holds your passwords.** Your mailbox uses an app password you can revoke. Where a site needs an account, you sign
in yourself in the agent's browser; the session stays there, the password never reaches the agent.

## A normal day

1. **Open the app and press Refresh** (bottom left). It updates the app, finds new postings and reads new replies.
2. **Job applications → Waiting for review.** Each has a one-page résumé, a screenshot of the filled form, and a checklist.
   Approve stays grey until the checklist passes; the unticked line says what's missing.
3. **Decide.**
   - *Approve* when you'd sign it. The form is submitted in a visible browser; if a CAPTCHA appears, that one's yours.
   - *Change this résumé*: type or say what to change ("lead with the climate work"). A *Revising* badge shows while it works,
     a green dot when the new version is in.
   - *Reject* with a note when the role or the angle is wrong.
4. **Applied.** Grouped as *Heard back*, *Rejected* and *No reply yet*, each with its latest email's subject.

## Teach it

Notes and rejection reasons become proposed fixes: a better example for the writing brief, a reworded storybook line, a phrase
to block, a preference. Apply the ones you agree with; revert any time. It never edits itself behind your back.

## When you have to step in

| You'll see | What to do |
|---|---|
| "Only you can answer these" | Answer them. Usually salary, start date, or a "Why us?" the employer wants in your own words. |
| Approve is grey | Read the unticked line. It tells you what's missing. |
| A placeholder like `[YOUR ANSWER]` in an email | The agent didn't have that fact. Write it, or add it to your storybook so it never asks again. |
| A role you'd never take | Reject it, and say why: "no agencies" becomes a proposed preference. |
| A model error | Setup → Connect a model → *Test* shows what's wrong. |

## Where things live

- `profile/`: your storybook, standing answers and preferences. Private, never committed.
- `data/`: the database, the app's log, and the agent's browser profile.
- `out/resumes/`: every PDF that was generated.
- **Activity** in the app: everything the agent did and everything you decided.
- Every step and prompt: [docs/pipeline.md](docs/pipeline.md).

That's it. Go outsource the boring part.
