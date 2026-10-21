"""Gemma reads each search result against the profile and returns a verdict."""

import json
import re
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date

from lazy_scholar.config import Config
from lazy_scholar.llm import generate
from lazy_scholar.profile import profile_text
from lazy_scholar.search import SearchResult

# Gemma takes ~17 s per call, so 3 at a time is ~10 requests/minute:
# about 3x faster, and should stay well under the free-tier per-minute limit.
WORKERS = 3

PROMPT = """You screen opportunities for a student. Today is {today}.

Student profile:
{profile}

Search result:
- title: {title}
- url: {url}
- snippet: {snippet}

Decide if this is a real, currently open scholarship, grant, paid internship, or
hackathon/competition with a prize that this student can apply to. Follow the
profile's location rule strictly. If the deadline has passed, it is not eligible.
If the page is a list of many opportunities, a news article, or unclear, it is
not eligible.

Use the whole score range so matches can be ranked:
- 90-100: fits the profile's interests exactly, clear prize/pay, clear open deadline
- 70-89: good fit, but one of interest, prize/pay or deadline is vague
- 40-69: eligible but only loosely related to the profile's interests
- 0-39: not eligible or a poor fit

Answer with only a JSON object, no other text:
{{"eligible": true or false,
  "category": "scholarship" | "grant" | "internship" | "hackathon" | "other",
  "score": 0-100 match with the profile,
  "deadline": "YYYY-MM-DD" or null,
  "amount": short text like "$5,000" or "paid" or null,
  "summary": one sentence describing the opportunity,
  "reasons": [up to 3 short reasons for the decision]}}"""


@dataclass(frozen=True)
class Verdict:
    url: str
    title: str
    eligible: bool
    category: str
    score: int
    deadline: str | None
    amount: str | None
    summary: str
    reasons: list[str]


def parse_json(text: str) -> dict:
    """Pull the first {...} block out of the reply (models sometimes wrap it in ```json)."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in model reply: {text[:200]!r}")
    return json.loads(match.group(0))


def generate_with_retry(config: Config, prompt: str, attempts: int = 3) -> str:
    """The free tier sometimes returns 503 for a moment; wait and try again."""
    for attempt in range(attempts):
        try:
            return generate(config, prompt)
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(10 * (attempt + 1))
    raise AssertionError("unreachable")


def judge(config: Config, profile: dict, result: SearchResult) -> Verdict:
    prompt = PROMPT.format(
        today=date.today().isoformat(),
        profile=profile_text(profile),
        title=result.title,
        url=result.url,
        snippet=result.snippet,
    )
    data = parse_json(generate_with_retry(config, prompt))
    return Verdict(
        url=result.url,
        title=result.title,
        eligible=bool(data.get("eligible", False)),
        category=str(data.get("category") or "other"),
        score=int(data.get("score") or 0),
        deadline=data.get("deadline"),
        amount=data.get("amount"),
        summary=str(data.get("summary", "")),
        reasons=[str(r) for r in data.get("reasons", [])][:3],
    )


def judge_all(
    config: Config,
    profile: dict,
    results: list[SearchResult],
    on_verdict: Callable[[Verdict], None] | None = None,
) -> list[Verdict]:
    """Judge results a few at a time; on_verdict runs as each one finishes, so a crash loses nothing."""
    verdicts = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(judge, config, profile, r): r for r in results}
        for future in as_completed(futures):
            try:
                verdict = future.result()
            except Exception as e:  # one bad reply should not sink the whole night
                print(f"Could not judge {futures[future].url}: {e}")
                continue
            verdicts.append(verdict)
            if on_verdict:  # called on this thread, so the SQLite connection stays single-threaded
                on_verdict(verdict)
    return verdicts
