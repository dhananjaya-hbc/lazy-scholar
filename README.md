# Lazy Scholar

**An agent that hunts for money for my studies while I sleep.**

Every night, Lazy Scholar searches the web for scholarships, grants, paid internships and
hackathons with prizes. An open-weight **Gemma** model reads each result against my profile and
decides whether I can actually apply. Each morning it publishes a short digest with a drafted
application email for the best match.

**Live digest:** https://lazyscholar.tech

Built for the [DEV Hacktoberfest Open-Source AI Challenge, Week 3 "Slow and Steady"](https://dev.to/challenges/hacktoberfest-week3-2026-10-19).

## How it works

```
 GitHub Actions, every night (02:00 Sri Lanka time)
 │
 ├─ 1. Search    SerpApi runs 6 Google queries          search.py
 ├─ 2. Remember  SQLite skips links already judged      db.py
 ├─ 3. Judge     Gemma scores each new link → JSON      judge.py, llm.py
 ├─ 4. Digest    HTML page + email draft for top match  digest.py
 └─ 5. Publish   GitHub Pages at lazyscholar.tech       .github/workflows/nightly.yml
```

1. **Search.** [SerpApi](https://serpapi.com) runs a few Google queries tuned to the profile,
   such as remote AI internships and online hackathons with cash prizes. Big job boards are
   excluded, because a page listing 50 jobs can't be judged as one opportunity.
2. **Remember.** Every link is stored in SQLite with its verdict and deadline. A link is never
   judged twice, so later nights only spend model calls on new links. In CI the database lives
   on a separate `data` branch between runs.
3. **Judge.** Gemma gets the profile, today's date and the search result, and returns JSON:

   ```json
   {"eligible": true, "category": "hackathon", "score": 85, "deadline": "2026-11-30",
    "amount": "$5,000", "summary": "...", "reasons": ["Online, fits location rule", "..."]}
   ```

   It rejects expired deadlines, in-person events the profile can't travel to, and list or
   news pages. It judges 3 links at a time, with retries and a timeout per call.
4. **Digest.** Open matches are sorted by deadline, then score, with "new" and "closing soon"
   tags. Gemma drafts an email for the best match using placeholders such as `[your CGPA]`.
5. **Publish.** A GitHub Actions cron job runs everything and deploys the page to GitHub Pages
   on a `.tech` domain.

## Why Gemma: open weights, no lock-in

Gemma's weights are open, so the same model can run on a hosted API today and on my own
hardware later. Switching is a single setting in [`llm.py`](src/lazy_scholar/llm.py):

| `MODEL_PROVIDER` | Where Gemma runs |
|---|---|
| `google` (default) | Google AI Studio / Gemini API |
| `openrouter` | OpenRouter |
| `ollama` | Self-hosted with Ollama |

The default model is `gemma-4-26b-a4b-it`, a Mixture-of-Experts model that activates only
4B parameters per call, which keeps nightly judging fast and cheap. For higher-quality judging,
set `MODEL_NAME=gemma-4-31b-it`.

## Privacy

The profile, which includes details like GPA, is **never committed and never shown on the
page**. It lives in a gitignored `profile.toml` locally and in the `PROFILE` GitHub Secret in
CI. Only opportunity details are published. The email draft uses placeholders that you fill in
yourself.

## Run it yourself

Requirements: [uv](https://docs.astral.sh/uv/), a free [Google AI Studio](https://aistudio.google.com)
API key, and a free [SerpApi](https://serpapi.com) key.

```bash
git clone https://github.com/dhananjaya-hbc/lazy-scholar.git
cd lazy-scholar
cp .env.example .env                    # add GEMINI_API_KEY and SERPAPI_API_KEY
cp profile.example.toml profile.toml    # describe yourself; stays private
uv run lazy-scholar                     # search, judge, write site/index.html
```

- `uv run lazy-scholar --no-search` rebuilds the digest from the database without using
  any SerpApi searches, which is handy for testing.
- To tune what it looks for, edit `QUERIES` in [`search.py`](src/lazy_scholar/search.py).

**To run it nightly on your own fork:**
1. Add `GEMINI_API_KEY`, `SERPAPI_API_KEY` and `PROFILE` (the whole `profile.toml`) under
   Settings → Secrets and variables → Actions.
2. Set Settings → Pages → Source to **GitHub Actions**.

### Staying inside free tiers

- **SerpApi:** the free plan has 250 searches a month. A night uses at most 6, about 186 a
  month, and the run skips searching when fewer than 10 remain.
- **Gemma:** the Gemini API free tier has daily and per-minute limits. A typical night needs
  only a handful of calls, because links already judged are skipped.

## Project layout

```
src/lazy_scholar/
  __init__.py   nightly pipeline (uv run lazy-scholar)
  config.py     settings from .env / environment
  profile.py    private profile from profile.toml or the PROFILE secret
  search.py     SerpApi queries and search budget guard
  llm.py        one generate() over Google AI Studio, OpenRouter, Ollama
  judge.py      Gemma prompt, JSON parsing, retries, 3 calls at a time
  db.py         SQLite memory
  digest.py     public HTML digest and email draft
.github/workflows/nightly.yml   cron, data branch, Pages deploy
```

## Credits

- **[Gemma](https://ai.google.dev/gemma)** by Google DeepMind: the open-weight model that does the judging
- **[Google AI Studio / Gemini API](https://aistudio.google.com)** and the
  **[google-genai](https://github.com/googleapis/python-genai)** Python SDK: hosting and client
- **[SerpApi](https://serpapi.com)** and its **[Python library](https://github.com/serpapi/serpapi-python)**: web search
- **[python-dotenv](https://github.com/theskumar/python-dotenv)**: loading `.env`
- **[HTTPX](https://www.python-httpx.org)**: HTTP client for the OpenRouter and Ollama providers
- **[SQLite](https://sqlite.org)**, through Python's standard library: memory
- **[uv](https://github.com/astral-sh/uv)** by Astral: Python and dependency management
- **[GitHub Actions](https://github.com/features/actions)** and **[GitHub Pages](https://pages.github.com)**,
  using `actions/checkout`, `astral-sh/setup-uv`, `actions/upload-pages-artifact` and `actions/deploy-pages`
- **[.tech domains](https://get.tech)**: the `lazyscholar.tech` domain

## Built with AI assistance

I built this with help from **Claude Code** (Anthropic), which I used to scaffold the project,
write and debug code, and plan the work. That is allowed by the challenge rules. I made the
decisions, tested each step against real searches, and reviewed every commit before it was made.

## License

[MIT](LICENSE) © 2026 Chamod Dhananjaya
