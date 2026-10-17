---
name: job-hunting-rules
description: The person's house rules for the job-hunting agent — résumés, form answers, emails, proposals, titles, links, register, approvals. Load before writing, editing or reviewing ANY application material in this project, before running or changing the pipeline (agent/), and in every scheduled daily run.
---

# Job-hunting house rules

1. Read `docs/00-house-rules.md` (one page). It is the authority: three tests (true, professional, personal) and worked examples.
2. For content read `profile/master/` (facts, lenses in `06-roles.md`, voice in `07-voice.md`). `docs/02-writing-style-guide.md` is background reading, not a rulebook.
3. Before you hand anything over, check it against the rules. The fast checks are in code:
   ```bash
   python3 -c "from agent.voicecheck import lint, report; import sys; print(report(lint(sys.stdin.read(), 'resume')) or 'clean')" < draft.txt
   ```
   (`kind` = resume | answer | email). Hard issues must be fixed; soft ones need a look.
4. Mechanical rules (headline, links, per-entry titles, one page, approvals, standing answers) live in code; don't restate them in prompts.
5. When the person gives new feedback, don't append a rule. Ask what principle it is an instance of: if the brief already covers it, add or sharpen one example row; if it is mechanical, enforce it in code (agent/voicecheck.py, headline.py, links.py). Keep the brief to one page.
