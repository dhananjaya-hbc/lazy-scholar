# Lazy Scholar

Entry for the **DEV Hacktoberfest Open-Source AI Challenge, Week 3 "Slow and Steady"**
(https://dev.to/challenges/hacktoberfest-week3-2026-10-19).

## Deadline
- Submissions due **Oct 25, 2026, 11:59 PM PDT** = **Mon Oct 26, 12:29 PM Sri Lanka time**.
- Aim to publish the DEV post on **Sun Oct 25** (Sri Lanka time) to leave a buffer.

## Why this project
The builder is a university student in Sri Lanka who needs money for their studies.
Story for the post: "I need money for my studies, so I built an agent that hunts for money
while I sleep." Writing quality is the most heavily weighted judging criterion, so the
personal story matters.

## What it does
An agent that searches every night for scholarships, grants, paid internships and hackathons
with prizes, and posts a short morning digest.

1. **Search**: SerpApi runs a few queries per night (free plan, limited searches/month).
2. **Judge**: Gemma (open-weight, hosted via Google AI Studio / Gemini API) reads each result
   plus the user's profile and returns JSON: eligible?, match score, deadline, amount, reasons.
3. **Remember**: SQLite deduplicates seen URLs and tracks deadlines.
4. **Digest**: morning page ("3 new matches, 1 closes Friday") plus a drafted application
   email for the best match.
5. **Run and host**: nightly GitHub Actions cron, static site on GitHub Pages at
   **lazyscholar.tech** (free `.tech` domain).

## Decisions already made
- **No local models.** The user's Mac is an M2 with 8 GB RAM, so use hosted Gemma only.
  Include a `MODEL_PROVIDER` setting (Google AI Studio by default, with Ollama and OpenRouter
  options) so the code shows there is no lock-in.
- "Why open innovation matters" angle: open weights mean no lock-in. The same model can be
  self-hosted later with one config change, unlike a closed model.
- Python 3.12 with `uv`. The system Python 3.14 is too new for some packages.
- The public page must **not** show personal details (GPA etc.), only the matches.
- Keys live only in `.env` (gitignored) locally and in GitHub Secrets in CI. Never commit them
  or paste them in chat.

## Prize categories to enter (a project can win only once per challenge)
- Gemma ($200, featured)
- SerpApi ($100)
- .tech domain ($100)
- GitHub Copilot ($100): covers "automate your project with GitHub Actions"

## Challenge rules to respect
- New project built during Oct 19–25. AI assistance is allowed; be open about it in the post.
- Credit all libraries and prior work in the README and the post.
- English post, tags `devchallenge` and `hf26challenge`, using the submission template:
  What I Built / Demo / Code / How I Built It / Why Does Open Innovation Matter? /
  My Agent Session (optional, DevRelay) / The Lazy Payoff (optional) / Prize Categories.
- Any commits after the deadline must be noted in the README.
- The user writes the post in their own voice; Claude helps polish.

## Git workflow (user preference)
- Commit **every file individually**, with its own commit, and push often (the user wants an
  active GitHub contribution graph).
- Use conventional commit messages (`feat:`, `fix:`, `chore:`, `docs:`).
- **Ask the user before every commit.**
- Commit as the user only (`Dhananjaya Chamod <dhananjayachamod0754@gmail.com>`): no
  `Co-Authored-By: Claude` line or other Claude attribution.
- GitHub account: `dhananjaya-hbc`. Planned public repo: `lazy-scholar` (site: lazyscholar.tech)
  (ask the user to confirm before creating it).

## Status (Oct 21, 2026)
- [x] Project folder created with `.gitignore` and `.env` (placeholder keys)
- [ ] User: DEV account + Hacktoberfest registration
- [x] User: Google AI Studio API key → `.env` as `GEMINI_API_KEY` (verified: Gemma 4 answers)
- [x] Gemma models in AI Studio: `gemma-4-26b-a4b-it` (MoE, 4B active, **default**) and
      `gemma-4-31b-it` (dense flagship, 256K context, fallback for better judging)
- [x] User: SerpApi free account → `.env` as `SERPAPI_API_KEY`. Limit: **250 searches/month**,
      so the nightly run uses at most 6 queries (~186/month) and stops when fewer than 10 are left
- [x] User: claimed `.tech` domain: **lazyscholar.tech** (check auto-renew is off)
- [ ] User: optional DevRelay setup to save agent sessions
- [ ] User: share profile (degree, university, year, interests, what they want: scholarships /
      internships / hackathons, local or international)
- [ ] User: confirm creating the public GitHub repo
- [x] Claude: scaffold the project (uv, Python 3.12, `src/lazy_scholar/`, `config.py` with `MODEL_PROVIDER`)
- [ ] Claude: search module
- Note: the project has its own git repo. `/Users/dhananjaya` also has a stray `.git`, so always run git from inside the project.

## Day plan
- **Wed Oct 21**: accounts and keys, scaffold
- **Thu Oct 22**: search + Gemma judging + SQLite
- **Fri Oct 23**: digest, email drafts, static site, GitHub Actions nightly run
- **Sat Oct 24**: polish, README, deploy to the .tech domain, record a 2-minute demo video
- **Sun Oct 25**: write and publish the DEV post
