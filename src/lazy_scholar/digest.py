"""Build the public morning digest (site/index.html) from the database.

Only opportunity details go on the page, never the private profile.
"""

import html
import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

from lazy_scholar.config import Config
from lazy_scholar.llm import generate

SITE_DIR = Path("site")
CLOSING_SOON_DAYS = 7

DRAFT_PROMPT = """Write a short, polite application or enquiry email (under 150 words) from a
university student for this opportunity. Use these exact placeholders instead of personal
details: [your name], [your university], [your degree], [your year], [your CGPA],
[link to your GitHub]. Do not invent any other facts about the student.

Opportunity: {title}
URL: {url}
Details: {summary}

Reply with the email only, starting with "Subject:"."""


def days_left(deadline: str | None) -> int | None:
    if not deadline:
        return None
    try:
        return (date.fromisoformat(deadline) - date.today()).days
    except ValueError:
        return None


def headline(new: list[sqlite3.Row], closing: list[sqlite3.Row], matches: list[sqlite3.Row]) -> str:
    parts = [f"{len(new)} new match{'es' if len(new) != 1 else ''}"]
    for m in closing[:2]:
        when = datetime.fromisoformat(m["deadline"]).strftime("%A")
        parts.append(f"1 closes {when}")
    if not closing:
        # Nothing this week: still point at the next deadline so the page is useful.
        upcoming = [m for m in matches if days_left(m["deadline"]) is not None]
        if upcoming:
            nxt = datetime.fromisoformat(upcoming[0]["deadline"]).strftime("%a %d %b")
            parts.append(f"next deadline {nxt}")
    return ", ".join(parts)


def draft_email(config: Config, match: sqlite3.Row) -> str:
    prompt = DRAFT_PROMPT.format(title=match["title"], url=match["url"], summary=match["summary"])
    return generate(config, prompt).strip()


def card(m: sqlite3.Row, is_new: bool) -> str:
    left = days_left(m["deadline"])
    deadline = f"{m['deadline']} ({left} days left)" if left is not None else "No deadline listed"
    reasons = "".join(f"<li>{html.escape(r)}</li>" for r in json.loads(m["reasons"] or "[]"))
    badges = f'<span class="tag">{html.escape(m["category"])}</span>'
    if is_new:
        badges += '<span class="tag new">new</span>'
    if left is not None and left <= CLOSING_SOON_DAYS:
        badges += '<span class="tag soon">closing soon</span>'
    return f"""
    <article class="card">
      <div class="meta">{badges}<span class="score">{m['score']}/100</span></div>
      <h2><a href="{html.escape(m['url'])}" rel="noopener">{html.escape(m['title'])}</a></h2>
      <p>{html.escape(m['summary'] or '')}</p>
      <p class="facts"><strong>Deadline:</strong> {html.escape(deadline)}
        &nbsp;·&nbsp; <strong>Amount:</strong> {html.escape(m['amount'] or 'not stated')}</p>
      <ul class="reasons">{reasons}</ul>
    </article>"""


def build(config: Config, matches: list[sqlite3.Row], new_urls: set[str]) -> Path:
    new = [m for m in matches if m["url"] in new_urls]
    closing = [m for m in matches if (d := days_left(m["deadline"])) is not None and d <= CLOSING_SOON_DAYS]
    best = max(new or matches, key=lambda m: m["score"], default=None)
    draft = draft_email(config, best) if best else ""

    cards = "".join(card(m, m["url"] in new_urls) for m in matches) or "<p>No open matches yet.</p>"
    draft_html = (
        f'<section class="draft"><h2>Drafted email for the best match</h2>'
        f"<p>For <em>{html.escape(best['title'])}</em>. Fill in the [placeholders] before sending.</p>"
        f"<pre>{html.escape(draft)}</pre></section>"
        if best else ""
    )
    page = TEMPLATE.format(
        today=date.today().strftime("%A, %d %B %Y"),
        headline=html.escape(headline(new, closing, matches)),
        count=len(matches),
        cards=cards,
        draft=draft_html,
    )
    SITE_DIR.mkdir(exist_ok=True)
    out = SITE_DIR / "index.html"
    out.write_text(page)
    return out


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lazy Scholar</title>
<meta name="description" content="A nightly agent that hunts for scholarships, internships and hackathons. Judged by Gemma.">
<style>
  :root {{ --bg: #faf8f3; --fg: #1f1d1a; --muted: #6b665d; --card: #fff; --line: #e6e1d6;
          --accent: #2f6f4f; --new: #2f5f8f; --soon: #b3541e; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #161513; --fg: #ece8df; --muted: #a39d92; --card: #1f1e1b; --line: #33312c;
            --accent: #7fc39c; --new: #8db4dc; --soon: #e8955f; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--fg);
         font: 16px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }}
  main {{ max-width: 760px; margin: 0 auto; padding: 32px 16px 64px; }}
  header p {{ color: var(--muted); margin: 4px 0; }}
  h1 {{ font-size: 1.9rem; margin: 0; }}
  .headline {{ font-size: 1.25rem; font-weight: 600; color: var(--accent); margin: 16px 0 24px; }}
  .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 12px;
          padding: 16px 18px; margin-bottom: 14px; }}
  .card h2 {{ font-size: 1.08rem; margin: 6px 0; }}
  .card a {{ color: inherit; }}
  .meta {{ display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }}
  .tag {{ font-size: .75rem; padding: 2px 8px; border-radius: 99px; border: 1px solid var(--line);
         color: var(--muted); text-transform: capitalize; }}
  .tag.new {{ color: var(--new); border-color: currentColor; }}
  .tag.soon {{ color: var(--soon); border-color: currentColor; }}
  .score {{ margin-left: auto; font-weight: 600; color: var(--accent); font-variant-numeric: tabular-nums; }}
  .facts, .reasons {{ color: var(--muted); font-size: .92rem; }}
  .reasons {{ margin: 6px 0 0; padding-left: 20px; }}
  .draft pre {{ white-space: pre-wrap; background: var(--card); border: 1px solid var(--line);
               border-radius: 12px; padding: 16px; font: .92rem/1.5 ui-monospace, monospace; }}
  footer {{ color: var(--muted); font-size: .85rem; margin-top: 40px; }}
  footer a {{ color: inherit; }}
</style>
</head>
<body>
<main>
  <header>
    <h1>Lazy Scholar</h1>
    <p>Morning digest for {today}. {count} open matches.</p>
  </header>
  <p class="headline">{headline}</p>
  {cards}
  {draft}
  <footer>Found overnight by SerpApi, judged by open-weight Gemma.
    <a href="https://github.com/dhananjaya-hbc/lazy-scholar">Source on GitHub</a></footer>
</main>
</body>
</html>
"""
