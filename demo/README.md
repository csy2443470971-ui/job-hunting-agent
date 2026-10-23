# Live demo

A demo account is a second account in the app, empty to start. It runs the whole flow for a fictional applicant,
Taylor Brooks, on real postings at real companies, and sends nothing.

## Before you present

- Connect a model on your own account (Setup → Connect a model). Demo accounts use the same one.
- Have Google Chrome installed if you can. The agent's browser uses it.

## The flow, about five minutes

1. **Create it.** Click the account name at the top of the sidebar → **New demo account**. The app restarts on an empty
   account. An orange line on every page says nothing is sent.
2. **Standing questions.** Setup → *Answer the standing questions* → **Use the sample answers**.
3. **Tell it everything.** Setup → *Tell it everything* → **Show the sample material** opens `demo/materials`. Drag all
   four files onto **Drop anything**: a résumé, a reference letter, a capstone paper and a voice memo. The storybook fills
   with résumé lines, each naming the file it came from.
4. **Find jobs.** Press **Refresh** (bottom left). It reads the public job boards of the companies on the watchlist
   (Greenhouse, Lever, Ashby) and ranks what it finds. About a minute.
5. **Prepare one.** Job applications → *Not started* → pick a design role → **Prepare**. You get a one-page résumé built
   from Taylor's storybook, then the company's real application form filled in the agent's browser, with a screenshot
   to check.
6. **Approve.** In a demo account it stops there: *Demo account: nothing was sent.*
7. **Back to yours.** Click the account name → your own account.

## What a demo account never does

- Submit an application. Forms are filled up to the Submit button, never past it.
- Upload a file to a company's site. Résumé and transcript fields are left empty.
- Send email or read a mailbox.

Taylor is fictional. Anything sent would reach a real recruiter.

## Files

- `standing.yaml`: Taylor's standing answers, copied in by *Use the sample answers*.
- `materials/`: the four sample files. Everyone and every organization in them is fictional (example.com addresses,
  a 555-01xx phone number).
- `make_materials.py`: makes them again.

Each demo account lives in `profiles/demo-N/`, with its own database (`data/demo-N.sqlite`) and browser profile
(`data/browser-demo-N/`). To remove one, switch to another account and delete those three.
