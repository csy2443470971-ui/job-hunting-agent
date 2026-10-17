# 02 · Writing style guide (résumés + outreach)

> docs/00-house-rules.md overrides this guide. In particular rule 16 (professional register): plain is good, but use the field's nouns and precise verbs; roles stated as roles ("Guest Speaker, <Club name>").

Rules the generator follows so every one-page PDF and email reads like the user wrote it, not like a model. Targets: climate tech, AI companies, design agencies (IDEO / Frog / Pentagram-style), creative studios, tech companies of any size.

The one test: **would a tired hiring manager believe a specific person typed this?** Specific nouns, real numbers, uneven sentence lengths, one opinion somewhere. Nothing that could be pasted into someone else's résumé.

---

## 1. One-page résumé structure (design/tech hybrid)

Single column. No photo, no skill bars, no "objective". Margins ≥ 0.5 in, body 10–11 pt, line spacing ≥ 1.07, left-aligned (never justified). Bold/italic only for entry titles and dates. PDF only.

**Section order**

1. **Header** (1–2 lines): name · city/timezone · email · portfolio URL · GitHub or LinkedIn (two links max). Portfolio written as a readable domain, not a hyperlinked word.
2. **Summary** (optional, ≤ 2 lines, only if the sections below can't say it): "Designer who ships code. 4 yrs on climate data products; built X, used by Z." Cut it if it contains an adjective about yourself.
3. **Experience** (reverse-chronological; 2–4 bullets per role, most on the latest).
4. **Selected projects** (2–3 lines: name · stack · what it does · a number or link). For agencies/studios this can move above Experience when the projects are stronger than the jobs.
5. **Skills** (one or two lines grouped by kind: *Design* — Figma, prototyping, research; *Code* — TypeScript, React, Three.js, Python. No ratings).
6. **Education** (one line per degree; above Experience only for new grads).
7. **Extras** (talks, awards, languages). One line, often cut.

**When it spills past one page, cut in this order**

1. Extras / awards / certificates.
2. Summary.
3. Roles older than ~6 years → title + dates, no bullets.
4. The fourth bullet on every role, then the third on roles older than the last two.
5. Projects outside the target company's domain.
6. Skills you don't want to be interviewed on.
7. Only then tighten margins/font, never below 0.5 in / 10 pt.

Never cut: numbers, links, the most recent role, anything that overlaps the job post.

---

## 2. Bullet-writing rules

Formula (Google's XYZ, r/EngineeringResumes' CAR): **did X · measured by Y · by doing Z**. Order can flex ("Cut onboarding drop-off 31% by …" or "Rebuilt the pipeline in Rust; nightly job went from 40 min to 6"). Don't force every bullet into the same shape; uniform rhythm is itself an AI tell.

- Start with a plain past-tense verb: built, cut, shipped, redesigned, rewrote, ran, wired, moved, found, fixed. Not posture verbs (spearheaded, championed, drove, leveraged, orchestrated).
- One idea per bullet, max two lines. A third line means two bullets or padding.
- A number in at least half the bullets, with a baseline where possible ("from 40 min to 6", not "by 85%" alone). No number? Name the concrete thing instead (product, team size, client).
- Nouns the reader can picture: "Figma → React component library", not "design systems expertise".
- Say what *you* did in team work. "Owned the map layer" beats "collaborated cross-functionally on".
- No adjectives about yourself, no adverbs ("successfully", "significantly").
- No parallel triplets ("faster, cheaper, and more reliable"). Two items, or one.
- Delete the first three words and see if the bullet still works. It usually does.

**Before → after (AI-sounding → human)**

1. *Spearheaded the end-to-end redesign of the onboarding experience, leveraging user research to drive significant improvements in engagement.*
   → Redesigned onboarding after 14 user interviews; sign-up completion went from 52% to 71% in the quarter after launch.
2. *Leveraged cutting-edge AI technologies to build innovative solutions for climate data visualization.*
   → Built a browser tool that renders 10 years of ERA5 wind data as an interactive globe (Three.js + Zarr); used by two research groups at ETH.
3. *Collaborated cross-functionally with engineering and product stakeholders to deliver a seamless, user-centric design system.*
   → Wrote the Figma library and the matching React components (38 of them) so engineers stopped rebuilding buttons; design-to-ship time dropped from ~2 weeks to 3 days.
4. *Passionate about creating impactful, delightful experiences that empower users.*
   → (delete; this is not a bullet)
5. *Demonstrated strong leadership skills by mentoring junior designers and fostering a culture of excellence.*
   → Ran weekly crits for 3 junior designers; two were promoted within a year.
6. *Utilized data-driven insights to optimize the conversion funnel, resulting in enhanced business outcomes.*
   → Found in Mixpanel that 60% of drop-off was on the pricing page; rewrote it, conversion up 18%.
7. *Orchestrated the successful migration of legacy systems to a modern, scalable architecture.*
   → Moved the billing service from a PHP monolith to Node; cut deploy time from 45 min to 4 and killed the Friday outage.
8. *Played a pivotal role in the development of a robust, cutting-edge mobile application.*
   → Built the iOS app's map and offline mode (Swift, MapKit); 40k downloads, 4.7★ on 1,200 reviews.
9. *Conducted comprehensive research to gain valuable insights into user needs and pain points.*
   → Interviewed 22 farmers in Jiangsu about irrigation schedules; the findings changed the product from an app to an SMS service.
10. *Championed accessibility best practices across the organization, ensuring inclusive experiences for all users.*
    → Audited 60 screens against WCAG 2.1 AA and fixed the 140 issues; the product passed the client's accessibility review on the first try.
11. *Delivered high-quality creative assets for a diverse array of clients across multiple industries.*
    → Designed brand identity and a 30-page site for a solar installer and two bike shops; the solar client's inbound leads doubled in 3 months.
12. *Not only improved performance but also enhanced maintainability of the codebase.*
    → Dropped page load from 6.2 s to 1.9 s by lazy-loading the 3D scene and trimming 400 KB of unused CSS.

---

## 3. Banned words and patterns

Hard bans (the generator must never emit these in a résumé or email; a human may override on purpose):

**Verbs/posture:** leverage, leveraged, utilize, spearhead, spearheaded, champion, championed, orchestrate, drive/drove (as in "drove results"), facilitate, foster, empower, elevate, streamline, optimize (without a number), harness, unlock, navigate (metaphorical), delve, embark, bolster, garner, underscore, showcase.

**Adjectives:** cutting-edge, innovative, robust, seamless, scalable (as adjective of self), dynamic, passionate, results-driven, detail-oriented, self-motivated, proactive, strategic, holistic, impactful, delightful, world-class, best-in-class, state-of-the-art, groundbreaking, transformative, meticulous, comprehensive, vibrant, pivotal, crucial, key (as "key role"), synergistic.

**Nouns:** synergy, synergies, tapestry, landscape, realm, journey, ecosystem (unless literal), paradigm, stakeholders (say who), value-add, thought leadership, best practices, solutions (say what), deliverables, go-getter, team player, rockstar, ninja, wizard.

**Phrases:** "I am writing to express my interest", "I hope this email finds you well", "I came across your posting", "I believe I would be a great fit", "proven track record", "think outside the box", "hit the ground running", "wear many hats", "at the intersection of", "in today's fast-paced world", "it's important to note", "in conclusion", "I look forward to hearing from you", "please don't hesitate", "a testament to", "serves as / stands as", "plays a vital role", "a wide range of", "a diverse array of", "with a focus on", "in order to", "not just X but Y", "not only X but also Y", "it's not about X, it's about Y", "from X to Y" as a flourish, "whether it's A, B, or C", "I'm excited to", "thrilled", "humbled", "deeply", "truly", "genuinely", "incredibly".

**Self-descriptions (user rule, 2026-10-17):** never "designer who builds…", "engineer that…", "someone who…". Headlines are plain job titles (Digital Product Designer, AI Product Designer). Summaries are plain statements, or nothing.

**Structural tells:**
- Three parallel items in a row (tricolon). Use two or four, or break it.
- Every sentence the same length. Mix a 4-word sentence with a 25-word one.
- Em dashes more than once per email or twice per résumé. Comma, period, or parentheses instead.
- A summary sentence restating what was just said; a motivational closing line.
- Rhetorical question, then the answer.
- Bolded phrases inside prose; Title Case headings; curly quotes; emoji.
- Opening with a compliment ("I've long admired…") or "As a [role], I …".
- Stacked hedges ("I think I could potentially maybe help").
- A list where every item starts with the same word.

**"Sounds like a person" checklist** (run before output):

- [ ] At least one proper noun only this person could write (a client, a city, a dataset, a product).
- [ ] At least one number with a baseline or unit.
- [ ] Longest sentence ≥ 2× the shortest.
- [ ] Zero hard-ban words.
- [ ] No sentence could move to someone else's résumé unchanged.
- [ ] One small opinion or admission ("the first version was wrong").
- [ ] Emails: the ask is one yes/no sentence; reads aloud in under 40 seconds; at least one contraction. Résumé bullets: no contractions.
- [ ] The subject line could only belong to this email.

---

## 4. Cold email / self-pitch

Evidence: reply rates peak for bodies of 50–125 words; job-seeker guides land on 75–100. Statement subject lines beat questions (15.8% vs 9.8% replies in a 2026 recruiter-outreach survey). Emails that ask the reader to *review* something get ignored; emails that make yes/no easy get answered. Personalization must be true; invented fandom is worse than none.

**Structure (≤ 120 words, ≤ 4 short paragraphs)**

1. **Why you, why now** (1 sentence): the true trigger. A post, a listing, a product detail, a problem they said out loud.
2. **Who you are** (1–2 sentences): one role noun, one or two results with numbers, a link.
3. **What you'd do for them** (1–2 sentences): a concrete first thing tied to their stated problem. Not "I'd love to contribute".
4. **The ask** (1 sentence): small, yes/no, time-boxed.
5. Sign-off: name, one link. "Thanks, Alex", not "Best regards".

**Subject lines** (3–8 words, statement, specific; include their product or the role):
- `Designer + Three.js for the grid map`
- `Re: your post about onboarding drop-off`
- `Product designer who codes, re: Senior PD role`
- `A fix for the slow dashboard`
- `Saw the hiring post, one idea`

Bad: "Opportunity", "Introduction", "Quick question", "Hello!", "Application for Senior Product Designer Position".

**Opening lines that aren't "I hope this finds you well"**
- "Your changelog last week mentioned the map takes 8 s to load on mobile."
- "Saw [name] post that you're hiring a designer who can ship React."
- "I used [product] to plan a trip to Yunnan and the offline mode broke on day two. I think I know why."
- "Short one, three sentences."
- "[Mutual] said I should write."

**Referencing a stated problem**: quote it in their words (job post, blog, podcast, tweet), then one sentence on how you've handled the same thing, with a number. Don't lecture them on their own problem; never "I noticed you're struggling with".

**Closing asks that work**: "Worth 15 minutes next week?" / "Want me to send the prototype?" / "Should I apply through the site or is this the better channel?" / "If now's wrong, who should I write to instead?"

**Follow-up**: one bump after 5–7 days, two lines, no guilt ("Bumping this once. Still happy to send the prototype."). Then stop.

### Example 1 — posted job, no application window yet

Subject: `Product designer who ships React, re: Senior PD role`

> Hi Maya,
>
> Your careers page lists a Senior Product Designer but the apply button isn't live, so I'm writing directly.
>
> I'm a designer who also writes the front end. Last year at Fieldwork I redesigned the irrigation scheduler and built it in React; farmer retention at 90 days went from 41% to 63%. Portfolio: alexrivera.design.
>
> The role mentions the dashboard is "hard to extend". I rebuilt a similar one on a component library last spring and can show how I'd approach yours.
>
> Worth 15 minutes next week, or should I wait for the form?
>
> Thanks,
> Alex

### Example 2 — unsolicited proposal to a company that stated a problem

Subject: `A fix for the 8-second map load`

> Hi Tomas,
>
> In your Q3 update you wrote that the grid map "takes eight seconds on a phone and we don't know why."
>
> I've hit this twice on climate data products. Both times it was the GeoJSON being parsed on the main thread. Moving it to tiles plus a worker took a similar map from 7 s to 1.4 s.
>
> I built a quick prototype on your public dataset over the weekend: [link]. It's rough, but it loads in under two seconds on my old Pixel.
>
> Would it help if I walked your team through it? 20 minutes, no slides.
>
> Alex
> alexrivera.design

### Example 3 — social-media "we're hiring" mention

Subject: `Saw your hiring post, one idea`

> Hi Priya,
>
> You posted yesterday that you need "a designer who isn't scared of the terminal."
>
> That's roughly my whole résumé. I spent three years at a studio doing brand and web, then two building Three.js data tools; the latest one visualizes 10 years of wind data and is used by two research groups.
>
> Your onboarding has a step where users pick a region from a dropdown of 190 countries. I'd replace it with a map and a search box; I've done it before and it cut time-to-first-chart in half.
>
> Should I apply through the link, or is a short call easier?
>
> Alex
> alexrivera.design

---

## 5. Notes for design agencies and climate tech

**Design agencies / studios (IDEO, Frog, Pentagram-style)**

- Frog's talent lead: the portfolio is reviewed first, PDF or URL. The résumé exists to pass the recruiter filter and be the hand-out in the studio interview. Keep it quiet and correct; put the cleverness in the work.
- Portfolio link in the header, and again as a short label under the most relevant project ("case study: alexrivera.design/grid"). Two or three featured projects beat ten.
- Case-study framing (résumé and email): context → your role in one phrase → the constraint → what shipped → what happened. Studios hire for point of view and comfort with ambiguity, so name the decision you made under the constraint. "Client wanted a chatbot; research said users wanted a phone number; shipped the phone number" beats any metric.
- Say what you personally made. Agency reviewers assume everything was collaborative; they want to know your hands.
- Craft words are fine: typography, system, prototype, crit, brief, pitch. Corporate words are not: stakeholder alignment, KPI, synergy.
- NDA work: describe the problem class and your role without the client name; "under NDA, can walk through live".

**Climate tech**

- Employers screen for mission fit but are tired of generated cover letters (Canary Media quotes recruiter fatigue). Show the mission through what you've done, not what you believe. One sentence of "why climate" maximum, and it must be concrete: a project, a dataset, a place.
- Good: "I've spent two years on grid and irrigation data because that's where I think design actually moves a number." Bad: "I'm deeply passionate about combating the climate crisis and building a sustainable future for generations to come."
- Never lecture a climate company about climate. Don't use: crisis, urgent, planet, future generations, make a difference, sustainable (of yourself), green, eco-friendly, impactful.
- Lead with proof you can do the work (shipped tools, numbers, domains: energy, agriculture, buildings, carbon accounting). Name the sub-sector; "climate" alone is too broad.
- Numbers climate teams care about: tCO2e, kWh, hectares, households, sensors, data volume, model accuracy, time to insight. Use the ones you actually have.

---

## 6. Voice calibration (mirror the user, not the model)

The generator writes in the user's voice, taken from the master document:

1. **Extract a voice profile first:** median and max sentence length, favorite verbs, how they name tools ("Three.js" vs "three"), contractions or not, "I" sentences vs verb-first fragments, recurring phrases, jokes, how they refer to their own work ("the globe thing"). Store as `voice.json`; pass it into every generation.
2. **Reuse their phrasing verbatim** where it exists. If the master doc says "the first version was ugly and slow", that line goes in as-is, never upgraded to "the initial iteration had performance shortcomings".
3. **Match rhythm.** Median sentence 11 words → output median 9–13. If they write fragments, keep fragments.
4. **Keep quirks:** lowercase product names, date style, "ok" not "okay", spelling variant, punctuation habits. Don't normalize. Chinese-English habits (an occasional dropped article, "very" as intensifier) are theirs; fix only what a reader would stumble on.
5. **Borrow their opinions.** The master doc has views ("dashboards are mostly for the people who commission them"). Pull one into each email. Never invent one.
6. **Default register when in doubt:** plain, slightly dry, first person, no exclamation marks, one contraction per paragraph, no adjectives about self.
7. **Post-check:** flag any sentence > 1.8× the user's longest, any ban-list word, any paragraph with zero proper nouns. Regenerate only those sentences.
8. **Résumé bullets are the one place to be terser than the user:** fragments, no "I", past tense, verb first. Everything else mirrors them.

---

## Sources

- Google XYZ formula (Laszlo Bock, via Inc.): https://law.utexas.edu/wp-content/uploads/sites/44/2020/09/Google-Recruiters-Say-Using-the-X-Y-Z-Formula-on-Your-Resume-Will-Improve-Your-Odds-of-Getting-Hired-at-Google-_-Inc.com_.pdf
- Random Recruiter on XYZ in practice: https://randomrecruiter.substack.com/p/transform-your-resume-with-the-google-xyz-method
- r/EngineeringResumes wiki (bullet formats, one page, margins/fonts): https://www.reddit.com/r/EngineeringResumes/wiki/index/
- Jake's résumé template (Jake Gutierrez, Overleaf/GitHub): https://github.com/jakegut/resume
- Harvard OCS résumé & cover letter guide (action verbs, one page): https://cdn-careerservices.fas.harvard.edu/wp-content/uploads/sites/161/2022/04/undergrad_resumes_and_cover_letters-1.pdf
- The Muse, 45 things to remove from your résumé: https://themuse.com/advice/45-things-you-might-have-on-your-resume-that-need-to-be-removed
- CareerBuilder/LinkedIn buzzword data via HCAMag and Korn Ferry: https://www.hcamag.com/ca/news/general/ditch-the-cliches-hiring-managers-reveal-cv-turn-offs/154490 · https://kornferry.com/insights/this-week-in-leadership/5-cliches-to-keep-off-your-resume
- Wikipedia, "Signs of AI writing" (word list, negative parallelism, rule of three, em dashes, markup tells): https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
- Jake Orlowitz on AI's overused words: https://medium.com/@jakeorlowitz/delving-into-the-load-bearing-tapestry-of-ais-overused-words-a2a0024cee9a
- Ruben on "delve" and Paul Graham: https://ruben.substack.com/p/delve
- Next Play, "The guide to getting a job with cold email" (structure, examples, who to email, follow-up): https://nextplayso.substack.com/p/the-guide-to-getting-a-job-with-cold
- Next Play, "How to get hired at a startup" (lead with a specific contribution): https://nextplayso.substack.com/p/how-to-get-hired-at-a-startup
- Quarter Mile, "How to get hired" (clear ask, scarce founder time): https://quarter--mile.com/How-To-Get-Hired
- YC Work at a Startup FAQ: https://www.workatastartup.com/faq
- VC Backed, cold emails to founders: https://www.vcbacked.co/blog/how-to-write-cold-emails-to-founders
- Sam Parr cold-email formula (Horizons Pod summary): https://horizonspod.substack.com/p/the-cold-email-formula-that-made
- Patrick McKenzie, "Don't call yourself a programmer" (describe value in business terms; most hiring is private): https://www.kalzumeus.com/2011/10/28/dont-call-yourself-a-programmer/
- 2026 recruiter cold-email subject-line survey (statement vs question, first name): https://www.noon.ai/blog/articles/337-recruiting-email-subject-line-statistics
- Hunter / FullEnrich on cold-email body length: https://www.fullenrich.com/content/how-long-should-a-cold-email-be
- Careery, when cold emailing hiring managers works: https://careery.pro/blog/cold-email-hiring-manager-when-to-use
- Core77 "Getting Hired" series: Frog (portfolio first, PDF or URL): https://core77.com/posts/26280/Getting-Hired-To-Land-a-Job-at-frog-Know-Your-Strengths-Have-a-Point-of-View-and-Be-Comfortable-with-Ambiguity · IDEO and wrap-up: https://www.core77.com/posts/26319/How-to-Land-Your-Dream-Design-Job-Eight-Tips-for-Getting-Hired-at-a-Top-ID-Firm
- Dribbble, how to design a UX résumé: https://content-hub.dribbble.com/?p=22
- UX Planet, what not to include on a designer résumé (2025): https://uxplanet.org/what-not-to-include-on-your-designer-resume-in-2025-eb5852c460b1
- uxfolio, UX résumés hiring managers like (90% of time on case studies): https://blog.uxfol.io/ux-designer-resume/
- Canary Media, career experts answer climate jobseekers (one page, recruiter fatigue with AI letters): https://canarymedia.com/articles/clean-energy-jobs/career-experts-answer-6-top-questions-from-climate-jobseekers
- The Commons, how to land your first climate job (evidence over passion): https://www.thecommons.earth/blog/how-to-land-your-first-climate-job
- Silas Mahner, how to get a job in climate tech: https://silasmahner.substack.com/p/how-to-get-a-job-in-climatetech
- Work on Climate: https://workonclimate.org · Terra.do: https://www.terra.do · Climatebase: https://climatebase.org
