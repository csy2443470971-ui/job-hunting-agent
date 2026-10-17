# 03 — Job Sources, APIs and Sourcing Plan

*Researched 2026-10-13. Target: designer/technologist → climate tech, AI companies, design agencies (IDEO, Frog, Pentagram, Work & Co, Instrument, Huge, R/GA…), creative studios, tech companies. Agent runs daily in Python.*

> **Key finding up front:** every ATS "submit application" API (Greenhouse, Lever, Ashby, SmartRecruiters, Workable) authenticates with the **employer's** API key. A job seeker cannot call them. Programmatic *discovery* via ATS is free and excellent; programmatic *submission* must go through the hosted apply page (browser automation) or email. Plan accordingly (see §6).

---

## 1. Job aggregator APIs

| Source | Endpoint / docs | Auth | Free tier / pricing | Limits & notes |
|---|---|---|---|---|
| **Adzuna** | `https://api.adzuna.com/v1/api/jobs/{country}/search/{page}?app_id=&app_key=&what=&where=` — [developer.adzuna.com](https://developer.adzuna.com/) | app_id + app_key (free signup) | Free; commercial use after 14-day trial needs agreement ([ToS](https://developer.adzuna.com/docs/terms_of_service)) | Default caps: 25/min, 250/day, 1,000/week, 2,500/month. 20+ countries. Good for US/UK/DE/AU design & climate keywords. |
| **JSearch** (OpenWeb Ninja via RapidAPI) | `https://jsearch.p.rapidapi.com/search?query=` — [openwebninja.com](https://www.openwebninja.com/) | RapidAPI key | Free "Basic" plan with hard monthly cap (confirm on RapidAPI pricing tab; vendor pages suggest ~100–200 req/mo); paid from ~$10–25/mo | Aggregates Google for Jobs (LinkedIn, Indeed, Glassdoor…). Best single "everything" query; spend quota on precise queries. |
| **Jooble** | `POST https://jooble.org/api/{KEY}` JSON `{keywords, location, page}` — [jooble.org/api/about](https://jooble.org/api/about) | Free key on request | Free, per-key limits unpublished | Aggregator; lots of duplicates; decent for Europe. |
| **Reed** (UK) | `https://www.reed.co.uk/api/1.0/search?keywords=&locationName=` — [reed.co.uk/developers](https://www.reed.co.uk/developers/jobseeker) | Basic auth, key as username, empty password; self-serve | Free | UK only; good for London agency roles. |
| **The Muse** | `https://www.themuse.com/api/public/jobs?category=Design%20and%20UX&page=1` — [themuse.com/developers](https://www.themuse.com/developers/api/v2) | Optional `api_key` | Free | 500 req/h without key, 3,600/h with key. Mostly larger US employers; has category filters (Design, Creative, Software). |
| **Remotive** | `https://remotive.com/api/remote-jobs?category=design&search=` — [GitHub](https://github.com/remotive-com/remote-jobs-api) | None | Free, attribution required | Max 4 calls/day advised, >2/min blocked; 24h delayed. |
| **Arbeitnow** | `https://www.arbeitnow.com/api/job-board-api?page=` — [docs](https://arbeitnow.com/blog/job-board-api/) | None | Free | Mostly ATS-sourced, EU/DE heavy; `remote`, `visa_sponsorship` flags; `next` pagination. |
| **Himalayas** | `https://himalayas.app/jobs/api` (browse, cursor, limit≤20) and `/jobs/api/search?q=&seniority=&sort=recent` — [himalayas.app/api](https://himalayas.app/api) | None | Free, attribution required, no re-syndication | Rate-limited (429, numbers unpublished); data refreshed every 24h → poll once/day. Remote-only. |
| **RemoteOK** | `https://remoteok.com/api` (JSON, skip index 0) and `/remote-jobs.rss` — [help](https://remoteok.featurebase.app/help/articles/3140840-is-there-an-api-or-rssjson-feed-of-remote-jobs) | None | Free, dofollow backlink required | Newest ~100 posts only; tag filter unreliable. Low value for design. |
| **USAJobs** | — | — | — | **Skip**: US federal only, not target sectors. |
| **Careerjet** | v4 API, Basic auth with publisher key; must pass `user_ip` + `user_agent` — [careerjet.com/partners](https://www.careerjet.com/partners/) ; [python client](https://github.com/careerjet/careerjet-api-client-python) | Publisher key (free signup) | Free | Old `affid` clients are stale; 70 markets; aggregator noise. Low priority. |
| **SerpApi Google Jobs** | `https://serpapi.com/search?engine=google_jobs&q=` — [docs](https://serpapi.com/google-jobs-api) | API key | 250 searches/mo free (50/h); $25/1k, $75/5k | Clean Google-for-Jobs results incl. `apply_options` (deep links to ATS). Good complement to JSearch. |
| **Apify** LinkedIn/Indeed actors | e.g. [LinkedIn Jobs Scraper](https://apify.com/curious_coder/linkedin-jobs-scraper), [Indeed Scraper](https://apify.com/misceres/indeed-scraper) | Apify token | $5/mo free platform credit; actors add ~$1–5 per 1k results | Scrapes public listing pages (no login). Acceptable for *discovery*; see §6 for ToS risk. |

**Free with no auth:** Remotive, Arbeitnow, Himalayas, RemoteOK, The Muse (keyless), HN Algolia. **Free with key:** Adzuna, Jooble, Reed, Careerjet, JSearch (small), SerpApi (250/mo), Apify ($5).

---

## 2. ATS public endpoints (no auth, JSON) — the backbone

These are the highest-signal sources because they come straight from company career pages and are updated instantly. Build a `companies.yaml` of target companies with `{ats, token}` and poll all of them daily.

| ATS | List jobs (no auth) | Job detail / form fields | Submit via API? | Token discovery |
|---|---|---|---|---|
| **Greenhouse** | `GET https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true` — [docs](https://docs.greenhouse.io/job-board.html) | `GET …/jobs/{id}?questions=true&pay_transparency=true` → `questions[]` with `label`, `required`, `fields[{name,type,values}]` (types: input_text, input_file, textarea, multi_value_single_select…). **Full form schema, no auth.** | `POST …/jobs/{id}` exists but needs **the employer's Job Board API key** (Basic auth). Not usable by candidates. Hosted form at `https://job-boards.greenhouse.io/{token}/jobs/{id}` is a plain HTML form → automate with Playwright. | URL path of `boards.greenhouse.io/{token}` or `job-boards.greenhouse.io/{token}`; on custom domains view-source for `greenhouse.io` iframe `for=` param. Invalid token → `{"error":"Invalid Board Token"}`. |
| **Lever** | `GET https://api.lever.co/v0/postings/{company}?mode=json&limit=100&skip=0` (also `jobs.eu.lever.co` → `api.eu.lever.co`) — [docs](https://github.com/lever/postings-api) | Single posting: `/v0/postings/{company}/{id}`. Custom questions are **not** exposed by the public API. | `POST /v0/postings/{company}/{id}?key=` requires employer key; 2 POST/s cap. Candidate path: hosted `jobs.lever.co/{company}/{id}/apply` (some have hCaptcha). | `jobs.lever.co/{slug}`; view-source for `lever.co`. Slug ≠ always company name — verify content. |
| **Ashby** | `GET https://api.ashbyhq.com/posting-api/job-board/{org}?includeCompensation=true` — [docs](https://developers.ashbyhq.com/docs/public-job-posting-api) | Each job has `applyUrl`, `jobUrl`, `descriptionHtml`, compensation. Form spec via `jobPosting.info` requires API key. | `applicationForm.submit` requires employer key with `candidatesWrite` ([ref](https://developers.ashbyhq.com/reference/applicationformsubmit)). Candidate path: `jobs.ashbyhq.com/{org}/{id}/application` (React SPA; Playwright works). | `jobs.ashbyhq.com/{org}`. |
| **Workable** | `GET https://www.workable.com/api/accounts/{slug}?details=true` (redirects to `apply.workable.com/api/v1/widget/accounts/{slug}`) — [ref](https://dev.to/zsevic/integration-with-workable-public-jobs-api-3nk4); also `https://apply.workable.com/api/v3/accounts/{slug}/jobs` (POST, paged) | Job detail `…/api/v2/accounts/{slug}/jobs/{shortcode}` incl. description; form via `…/jobs/{shortcode}/form` (undocumented, works unauthenticated). | Candidate POST requires employer SPI token. Hosted apply page is straightforward HTML. | `apply.workable.com/{slug}/`. |
| **SmartRecruiters** | `GET https://api.smartrecruiters.com/v1/companies/{company}/postings?limit=100&offset=0` — [docs](https://developers.smartrecruiters.com/docs/posting-api) | `…/postings/{id}` full detail. Screening questions via `GET /postings/{uuid}/configuration` — **requires OAuth scope** `candidate_applications_manage` (employer). | `POST /postings/{uuid}/candidates` — employer OAuth only. Hosted `jobs.smartrecruiters.com/{company}/{id}`. | `careers.smartrecruiters.com/{company}`. Lower-tier customers may return empty feed. |
| **BambooHR** | `GET https://{company}.bamboohr.com/careers/list` (JSON); detail `/careers/{id}/detail` (undocumented but stable) | Detail incl. description; form not exposed. | No. Hosted form (often with reCAPTCHA). | `{company}.bamboohr.com/careers`. |
| **Rippling** | `GET https://ats.rippling.com/api/jobs/{company}` style endpoints are **unofficial/inconsistent**; safest is to scrape `https://ats.rippling.com/{company}/jobs` (server-rendered JSON in `__NEXT_DATA__`). | Descriptions often missing from the board API. | No. | `ats.rippling.com/{company}/jobs`. |
| **Teamtailor** | `GET https://{slug}.teamtailor.com/jobs.json` and `/jobs.rss?offset=&per_page=` (or custom career domain) | Title, location, dept, remote_type, apply_url. | No (Teamtailor API is employer-token). | `{slug}.teamtailor.com` or careers domain. Nordic/EU heavy. |
| **Recruitee** | `GET https://{company}.recruitee.com/api/offers/` — [docs](https://docs.recruitee.com/reference/offers) | Full description + `careers_url`. | `POST …/api/offers/{slug}/candidates` is a documented **public careers-site endpoint (no token)** — the one ATS where candidate-side API submission is officially supported. | `{company}.recruitee.com`. EU/NL heavy. |
| **Personio** | `GET https://{company}.jobs.personio.de/xml?language=en` (XML) — [docs](https://support.personio.de/hc/en-us/articles/207576365) | Description in XML; form not exposed. | No. | `{company}.jobs.personio.de`. DACH. |

**Discovery tip:** many target companies (Frog, Huge, R/GA, IDEO) use Greenhouse/Lever/Workday. Seed `companies.yaml` from [ClimateTechList](https://www.climatetechlist.com/) company list, YC climate/AI companies, and the agency list; detect ATS by fetching `/careers` and grepping for `greenhouse.io|lever.co|ashbyhq.com|workable.com|smartrecruiters.com|bamboohr.com|rippling.com|teamtailor.com|recruitee.com|personio`. Apify's [ats-company-discovery](https://apify.com/wickfeed/ats-company-discovery) can bootstrap the list. **Workday** (IDEO uses it) has a per-tenant JSON endpoint `https://{tenant}.wd{n}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs` (POST, no auth) worth adding.

---

## 3. Niche boards for the target sectors

| Board | URL | Feed / API | Scrape-friendliness | Notes |
|---|---|---|---|---|
| **Climatebase** | https://climatebase.org/jobs | No official API. Search page loads structured JSON (Algolia-backed) — inspect XHR. Apify actor exists. | Moderate; respect robots | Largest climate board; has "Design" function filter. |
| **Terra.do** | https://www.terra.do/climate-jobs/job-board/?q=designer | No API; job board behind $49/mo membership for full access | Paywalled | Public search page shows listings; details require login. |
| **Work on Climate** | https://workonclimate.org (Slack) | Slack #jobs channels; no public feed. Read via a user token on your own account (`conversations.history`) only if community rules allow. | Not scrapeable | Substack newsletter has job digests. |
| **ClimateTechList** | https://www.climatetechlist.com/jobs | Aggregates company ATS boards daily; asks to be contacted for data use | Ask first | Use it as a *company list* source, then hit the ATS APIs directly. |
| **Climate Draft** | https://climatedraft.org | No feed; small board | Light HTML | Startup-heavy. |
| **Green Jobs Network** | https://greenjobslist.org, newsletter at https://greenjobs.beehiiv.com | Beehiiv newsletter has RSS (`/feed`) | RSS | US green/sustainability roles. |
| **ai-jobs.net** (aijobs.net) | https://aijobs.net | RSS feed advertised; paid listings only | RSS | AI/ML heavy, some product/design. |
| **Wellfound** | https://wellfound.com/jobs | Old `api.angel.co` is dead (404); site behind Cloudflare | Hard; use Apify actor ($0.5–8/1k) | Still the best startup design-role source. |
| **Welcome to the Jungle (ex-Otta)** | https://app.welcometothejungle.com | No public API; Apify scraper | Hard (SPA) | UK/EU startups; matches design+AI well. |
| **HN Who is hiring** | https://news.ycombinator.com/submitted?id=whoishiring | **HN Algolia API**: `https://hn.algolia.com/api/v1/search_by_date?tags=story,author_whoishiring&query=%22Who%20is%20hiring%22` → `items/{id}` for comments; free, no key | Excellent | Monthly thread on 1st; also "Freelancer? Seeking freelancer?" thread. Grep comments for `designer|design engineer|climate`. |
| **Work at a Startup (YC)** | https://www.workatastartup.com/jobs | No official API; internal JSON (`/companies/{id}/jobs`), Apify actors $0.02–0.5/1k | Moderate | ~1,500 YC companies hiring; filter by "Design". |
| **Working Not Working** | https://workingnotworking.com | No feed; "UnJobBoard" behind login | Poor | Agency/creative freelance; manual check weekly. |
| **Dribbble Jobs** | https://dribbble.com/jobs | RSS historically; HTML paginated, scrape-friendly | Good | Product/visual design. |
| **Behance Jobs** | https://www.behance.net/joblist | Adobe internal JSON API (`/v3/jobs`) via XHR; no official docs | Moderate | Many agency/brand roles. |
| **Design Jobs Board** (UK) | https://www.designjobsboard.com | HTML | Good | Agency roles; London. |
| **Authentic Jobs** | https://authenticjobs.com | RSS feed (`/rss`) | Good | Legacy but still active. |
| **If You Could Jobs** (It's Nice That) | https://www.ifyoucouldjobs.com | HTML + email alerts; It's Nice That has no separate board | Good | **Best UK creative-studio source.** |
| **Krop** | https://www.krop.com/creative-jobs/ | RSS available | Good | US creative. |
| **Coroflot** | https://www.coroflot.com/design-jobs | RSS available | Good | Industrial/product design. |
| **AIGA Design Jobs** | https://designjobs.aiga.org | HTML (membership for some features) | Good | US. |
| **Dsgn Jobs** | https://dsgnjobs.com | HTML | Good | Small curated board. |
| **Creative Lives in Progress** | https://www.creativelivesinprogress.com/opportunities | HTML | Good | Entry/mid UK creative. |
| **The Dots** | https://the-dots.com/jobs | SPA, login-gated details | Poor | UK creative network. |
| **Design Week Jobs** | https://jobs.designweek.co.uk | HTML + email alerts | Good | UK. |
| **Dezeen Jobs** | https://www.dezeenjobs.com | HTML, daily newsletter | Good | Architecture/design. |
| **Layer** (layer.design studio) | https://layerdesign.com | Studio site; posts on ats.rippling.com/layer | Via Rippling | Monitor directly. |
| **Protocol** | — | Could not identify an active board by this name (2026) | — | Treat as dead/ambiguous. |

---

## 4. Social-media and "random mention" hiring posts

| Platform | Realistic approach (2026) | Cost |
|---|---|---|
| **X/Twitter** | Official API is pay-per-use by default for new devs: ~$0.005/post read, capped 2M/mo; legacy Basic ($200/mo, 15k reads) being retired. [Nitter and XCancel are dead](https://techcrunch.com/2026/09/15/nitter-and-xcancel-are-dead-again-after-xs-latest-legal-actions) after Sept 2026 C&Ds. Practical: a saved search `("we're hiring" OR "hiring a") (designer OR "design engineer") (climate OR studio)` run ~5×/day via pay-per-use search (~$1–3/mo), or skip X. | $0–5/mo |
| **Bluesky** | `GET https://api.bsky.app/xrpc/app.bsky.feed.searchPosts?q=hiring%20designer&sort=latest&limit=100` — no auth; page by `until=` timestamp (cursor on unauth returns 403). Also free Jetstream firehose (`wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post`) for keyword filtering in real time. | Free |
| **Mastodon** | Per-instance `GET https://{instance}/api/v1/timelines/tag/hiring?limit=40` and `/api/v2/search?q=&type=statuses` (public on most instances). Target mastodon.social, hachyderm.io, mastodon.design, climatejustice.social. | Free |
| **Threads** | Official `keyword_search` needs app review (`threads_keyword_search`, ~500 queries/7 days). Scrapers return ~10 results. Low ROI — skip. | — |
| **LinkedIn posts** | No API for post search; scraping logged-in feed violates ToS and triggers restrictions (see §6). Realistic: **manual** saved search `"we're hiring" designer climate` in the LinkedIn UI, or Google: `site:linkedin.com/posts "hiring" "designer" climate` via SerpApi/JSearch. Do not automate against your account. | Free (manual) |
| **Reddit** | Public RSS needs no key: `https://www.reddit.com/r/forhire/new.rss`, `/r/designjobs/new.rss`, `/r/DesignJobs`, `/r/UXDesign` (hiring threads), `/r/climatetech`, `/r/remotejs`. OAuth API: 100 QPM free for non-commercial; new app approval can take weeks. Use RSS. | Free |
| **Newsletters** | Subscribe with a dedicated Gmail label and parse: CTVC ([job board](https://ctvc.co/launching-our-ctvc-job-board), weekly Monday roles), Keep Cool, Work on Climate Substack, Climate Tech Canada, Green Jobs Network, Dezeen Jobs Daily, Design Week alerts, If You Could alerts, [Ugh creative roles](https://ugh-newsletter.beehiiv.com), UX Jobs Substack. Substack/Beehiiv publications expose RSS at `{pub}.substack.com/feed` and `{pub}.beehiiv.com/feed`. | Free |
| **Discord/Slack** | Designer Hangout (Slack, invite-only, #jobs), Friends of Figma Discord (33k members), Work on Climate Slack, Mixed Methods Slack, ADPList. Reading programmatically requires a user token and community permission; realistic path is a weekly manual skim or Slack's built-in keyword notifications forwarded to email. | Free |

---

## 5. Finding companies with publicly stated problems (unsolicited proposals)

Goal: surface "we're struggling with X" / "we need help with Y" signals from target companies, then draft a proposal.

| Signal type | Feed / API | Query pattern |
|---|---|---|
| **Press & blogs** | **Google News RSS** (free, no key): `https://news.google.com/rss/search?q="climate"+("redesign"+OR+"rebrand"+OR+"new+app")+when:7d&hl=en-US&gl=US&ceid=US:en` | `"is looking to" (redesign OR "user experience")`, `"raised" ("seed" OR "Series A") climate design` |
| **Global news index** | **GDELT DOC 2.0** `https://api.gdeltproject.org/api/v2/doc/doc?query=&mode=ArtList&format=json&timespan=7d` — free, no key, 1 req/5 s, 3-month window ([docs](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)) | `("climate tech" OR cleantech) ("user experience" OR "design")` |
| **Semantic web search** | **Exa** ([pricing](https://exa.ai/docs/changelog/pricing-update): $7/1k search+contents; ~$10 free credits/mo), **Tavily** (1,000 credits/mo free, [docs](https://docs.tavily.com/documentation/api-credits)), Perplexity Sonar/Search API ($5/1k, no free tier) | Exa `type=neural`, `category=company` / `news`: "climate startup says its onboarding is confusing", "founder admits website needs redesign" |
| **Founder podcasts/interviews** | My Climate Journey, Catalyst (Canary), The Interchange, Climate Tech VC pods, Design Better, Lenny's. Pull RSS → transcribe with Whisper (local) or use podcast-transcript APIs (Podscribe, Listen Notes API — free 300 req/mo). | Regex on transcripts: `(struggl|hard part|we need|haven't figured out).{0,80}(design|brand|website|onboarding|product)` |
| **GitHub** | Search API `https://api.github.com/search/issues?q=org:{org}+label:"help wanted"+is:open` (30 req/min with token). Also `topic:climate` repos. | Design-system / docs / UI issues at climate orgs (e.g. OpenClimateFix, WattTime, Climate TRACE) |
| **Product Hunt** | GraphQL v2 `https://api.producthunt.com/v2/api/graphql` — free dev token, 6,250 complexity/15 min, non-commercial ([docs](https://www.producthunt.com/v2/docs)) | Daily launches with topics `Climate Tech`, `Artificial Intelligence`; look for rough UX + traction → proposal. |
| **RFPs / grants** | ClimateWorks, Elemental Impact, SAM.gov (API, free), UK Contracts Finder (API), Devex, Bonfire. Design-specific: AIGA RFP list, Idealist. | `"request for proposals" (brand OR website OR "UX") climate` |
| **Public roadmaps / changelogs** | Canny/Productboard public boards, GitHub Projects, `/changelog` pages → RSS via Feedly-style polling (or [RSS-Bridge](https://github.com/RSS-Bridge/rss-bridge) self-hosted). Feedly's API is enterprise-only — skip. | "Planned" items mentioning design, accessibility, mobile. |
| **Hiring signals as proxy** | ATS feeds (§2): a company that just posted "Head of Design" but no designers yet = design debt → fractional/design-partner pitch. | — |

Recommended stack: Google News RSS + GDELT (free, broad) → Tavily/Exa for targeted semantic queries (cheap) → an LLM pass to classify "stated problem" vs noise → store in `leads.sqlite`.

---

## 6. Automation legality and practicality

| Platform | ToS position | Risk | Recommendation |
|---|---|---|---|
| **LinkedIn** | User Agreement bars bots/scrapers and automating any activity on the platform; enforcement is behavioural (FUSE/Quicksand/Sentinel) with tiered restrictions → suspension. | High for your real account | **Never automate your logged-in session.** Discover via JSearch/SerpApi/Apify (public pages, not your account). Queue **Easy Apply** as a human task with pre-filled answers. |
| **Indeed** | ToS explicitly prohibits automation of Indeed Apply outside official vendors; scraping prohibited; Persona bot-check on apply. | High + CAPTCHA | Discover via JSearch/SerpApi; **queue Indeed Apply for a human click.** |
| **Greenhouse / Lever / Ashby / Workable hosted forms** | No candidate ToS against assisted form-filling; Greenhouse form is plain HTML (occasional reCAPTCHA v2/v3); Lever sometimes hCaptcha; Ashby SPA, no CAPTCHA usually. | Low–medium | **Automate with Playwright in "assist" mode:** agent fills everything from the Greenhouse `questions` schema, screenshots, then pauses for human review/submit (or auto-submits for boards with no CAPTCHA and `AUTO_SUBMIT=true`). |
| **Recruitee** | Public candidates endpoint documented for careers sites. | Low | Fully automatable via API. |
| **Email applications / cold outreach** | Legal; CAN-SPAM/GDPR require honesty + opt-out for marketing-style mail; 1:1 job applications are fine. | Low | Automate drafts; human approves send (or auto-send with daily cap). |
| **Wellfound / WTTJ / Climatebase / Dribbble** | ToS discourage scraping; Cloudflare on Wellfound. | Medium | Low-rate polling (1–2×/day) with realistic headers, or paid Apify actor. Apply via their UI manually. |

**Decision rule:** *Automate directly* = ATS JSON discovery, Recruitee API, Playwright-assisted ATS hosted forms, Gmail sending. *Queue for human click* = LinkedIn Easy Apply, Indeed Apply, any CAPTCHA, any form with video/portfolio-upload requirements, Workday (multi-step accounts).

---

## 7. Email sending and contact finding

**Sending from your Gmail**

| Option | Setup | Pros / cons |
|---|---|---|
| **Gmail API + OAuth** (recommended) | Google Cloud project → OAuth client (Desktop) → scopes `gmail.send`, `gmail.readonly` (for parsing newsletter labels + replies), store refresh token locally. Python: `google-api-python-client`. | Free for standard use; threads/labels/drafts via same client; no password stored; supports creating **drafts** for human review. Needs one-time consent screen; "unverified app" warning is fine for personal use. |
| **SMTP app password** | 2-Step Verification → App Password → `smtplib` to `smtp.gmail.com:587`. | 10-minute setup; send-only; cannot read replies or create drafts. |

Both: personal Gmail cap is **500 recipients / rolling 24h**; stay far below (≤20–30 outreach/day) to avoid reputation blocks. Keep plain-text, one recipient per message, no tracking pixels. Use the Gmail API to also **read** the `Job Alerts` label (newsletters from §4) and detect replies to applications.

**Finding and verifying hiring contacts**

| Tool | Free tier (2026) | Use |
|---|---|---|
| **Hunter.io** | 50 credits/mo (finder 1 cr, verifier 0.5 cr, domain search); API key on free plan — [pricing](https://hunter.io/pricing) | Domain Search for `design` / `people` dept; Email Finder from name + domain; Verifier before sending. Best single pick. |
| **Apollo.io** | Free plan; enrichment API 50/min, 200/h, 600/day — [rate limits](https://docs.apollo.io/docs/rate-limits) | People search by title ("Head of Design", "Design Director") at company; credits for reveals limited. |
| **RocketReach** | 5 lookups/mo | Spot checks only. |
| **Clearbit** | **Free tier discontinued (Apr 2025); now HubSpot-only** — skip. | — |
| **Verification** | Hunter verifier (above); MillionVerifier 200 one-time credits; NeverBounce 10 free. Also do your own MX + SMTP-RCPT check with `py3-validate-email` as first pass. | Only email `valid`/`accept-all` with a confidence note. |

Pattern inference fallback: derive `first.last@` from one known address on the domain (Hunter returns the pattern), then verify.

---

## 8. Prioritised wiring order and cadence

| # | Source | Why first | Poll cadence |
|---|---|---|---|
| 1 | **ATS feeds** (Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Recruitee, Teamtailor, Workday) over a curated `companies.yaml` of ~150 climate/AI/agency targets | Highest signal, instant, free, gives form schema | Every 6h (cheap; ~150 requests) |
| 2 | **HN Who is hiring** via Algolia | Free, AI/startup-rich, often design-engineer roles | Daily; heavy on the 1st–3rd of month |
| 3 | **Himalayas + Remotive + Arbeitnow** | Free, no key, remote design roles | 1×/day (Himalayas caches daily) |
| 4 | **Adzuna** | Free, multi-country, salary data | 2×/day, ≤100 calls/day |
| 5 | **The Muse** | Free, keyless, design category | 1×/day |
| 6 | **JSearch or SerpApi Google Jobs** | Catches LinkedIn/Indeed/Glassdoor without touching them | 1×/day, 5–8 precise queries |
| 7 | **If You Could Jobs + Dribbble + Design Jobs Board + Dezeen/Design Week** (HTML/RSS) | Core creative-studio & agency coverage | 1×/day |
| 8 | **Climatebase + ClimateTechList company list + CTVC/Green Jobs newsletters (Gmail parse)** | Climate-sector depth | 1×/day |
| 9 | **Bluesky search + Reddit RSS + Mastodon tags** | Free "we're hiring" mentions | Every 4h (light) |
| 10 | **Google News RSS + GDELT + Tavily** problem-signal scan | Feeds the unsolicited-proposal pipeline | 1×/day |

Later / optional: Wellfound & WTTJ via Apify ($), X pay-per-use search ($), YC Work at a Startup scrape, Work on Climate Slack (manual weekly).

**Daily run shape:** 06:00 fetch all → dedupe by `(company, normalised title, location)` with a 30-day seen-set in SQLite → LLM score vs profile (design × climate/AI/agency, seniority, location/remote) → for ATS hits fetch Greenhouse `questions=true` → generate tailored answers/cover note → Playwright assist-fill → human review queue (Easy Apply / Indeed / CAPTCHA) → Gmail drafts for direct/unsolicited outreach (Hunter-verified contacts) → 08:00 digest email.

**Dead or paywalled (as of Oct 2026):** Nitter/XCancel (dead), AngelList/Wellfound API (dead), Clearbit free tier (gone), Terra.do board (membership), Feedly API (enterprise), Indeed/LinkedIn official job APIs (partner-only), Working Not Working & The Dots (login-gated), "Protocol" design board (could not locate).
