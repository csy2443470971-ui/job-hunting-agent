# User guide

Five minutes. Then the agent does the tedious part and you keep the parts that matter.

![Pipeline](docs/architecture.svg)

## Four things to know first

**0. Answer the standing questions first. It's required.**
Every application form asks the same things: your legal name, whether you're authorized to work, whether you need
sponsorship, whether you'd relocate (and where), how you want to work, your degree and GPA, and the voluntary
self-identification questions (gender, race, Hispanic/Latino, veteran, disability). Open the dashboard → Storybook →
*Standing answers*, answer them once, and the agent fills them everywhere. Every self-identification question has
*Prefer not to say*; pick it and the agent chooses the form's decline option. Until the starred ones are done, the
agent won't prepare or submit anything. Your answers stay in `profile/standing.yaml` on your computer.

**Connect your application mailbox (once).** The agent sends approved emails from the address you apply with and
reads replies there, so it can mark each application *Received*, *Next step*, *Interview*, *Offer* or *Rejected*.
For Gmail: turn on 2-Step Verification, then Google Account → Security → App passwords → create one and paste it into
`.env` as `JHA_MAIL_APP_PASSWORD=`. Check it with `python -m agent.run mail-test`. Reading is read-only (nothing is
marked read, moved or deleted); you can revoke the app password any time.

**1. Feed it everything. It reads, you decide.**
Drop whatever you have into `inbox/`: old résumés, a LinkedIn PDF, portfolio text, cover letters you were proud of,
even voice memos. (Yes, you can just talk. Ramble about your last job on a walk, save the recording, drop it in.
It gets transcribed locally.) Then run `python -m agent.run intake`. You get a storybook draft back, and you edit it
like a document. Nothing goes into your storybook until you put it there.

**2. A storybook is a story, not your autobiography.**
Leave out what doesn't serve the story. If you're applying as a design engineer and as a strategist, those are two
stories, so keep two storybooks:

```bash
cp -r profile.example profiles/design-engineer
cp -r profile.example profiles/strategy
JHA_PROFILE=profiles/strategy python -m agent.run daily
```

Same you, different emphasis. The agent only ever says what the active storybook says, so if a line isn't there,
it won't show up on a résumé. That's the point.

**3. Nothing leaves without your yes.**
The agent can find, rank, write and fill. It cannot submit or send until you click Approve. It also won't touch
CAPTCHAs, LinkedIn Easy Apply, salary questions, demographic questions you haven't given standing answers for, or any answer an employer says must be
written by you. Those come to you, marked.

## A normal day

1. **Morning.** The daily run (`python -m agent.run daily`, or the scheduled task) finds new postings, ranks them,
   builds a one-page résumé for the good ones and fills the forms right up to the Submit button.
2. **Coffee.** Open the dashboard: `python -m dashboard.app`, then http://127.0.0.1:8765. Go to **Review**.
3. **Check the list.** Each application has a checklist: one page, writing checks, invented content under 15%,
   every question answered, posting still open. Approve stays grey until all of it is green. Grey is not a bug;
   it's the agent being honest about what's missing.
4. **Approve, reject or fix.**
   - Approve when you'd sign it.
   - Reject when the role or the angle is wrong. It goes back to Compose.
   - Fix the text first if a sentence isn't you. Emails are editable in place.
5. **Send.** Approved forms: `python -m agent.run submit` opens a visible browser and submits. If a CAPTCHA appears,
   that one's yours. Approved emails go out through your Gmail on the next run.

## Teach it

Every application has a **Note to the agent** box, and Reject asks why. Write the note you'd give a new assistant:
"Don't say *named*, say *defined the brand identity*." Overnight it turns notes into proposed fixes on the **Learn** page:
a better example for its writing brief, a reworded line in your storybook, or a phrase to block. Click Apply on the ones
you agree with. Changed your mind? Revert. It gets better, and it never edits itself behind your back.

## When you have to step in

| You'll see | What to do |
|---|---|
| "Only you can answer these" | Answer them. Usually salary, start date, or a "Why us?" the employer wants in your own words. |
| Approve is grey | Read the unticked line. It tells you what's missing. |
| A placeholder like `[YOUR ANSWER]` in an email | The agent didn't have that fact. Write it, or add it to your storybook so it never asks again. |
| A role you'd never take | Reject it, and add the keyword to `avoid_keywords` in `preferences.yaml`. |

## Where things live

- `profile/` (or `profiles/<story>/`): your storybook and settings. Private, never committed.
- `inbox/`: drop zone for raw material.
- `out/resumes/`: every PDF that was generated.
- Dashboard → **Activity**: a log of everything the agent did and everything you decided.

That's it. Go outsource the boring part.
