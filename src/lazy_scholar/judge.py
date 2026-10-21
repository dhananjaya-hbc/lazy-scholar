"""Gemma reads each search result against the profile and returns a verdict."""

import json
import re
import time
from dataclasses import dataclass
from datetime import date

from lazy_scholar.config import Config
from lazy_scholar.llm import generate
from lazy_scholar.profile import profile_text
from lazy_scholar.search import SearchResult

# Stay well under the free-tier requests-per-minute limit.
SECONDS_BETWEEN_CALLS = 2

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


def judge_all(config: Config, profile: dict, results: list[SearchResult]) -> list[Verdict]:
    verdicts = []
    for i, result in enumerate(results):
        if i:
            time.sleep(SECONDS_BETWEEN_CALLS)
        try:
            verdicts.append(judge(config, profile, result))
        except Exception as e:  # one bad reply should not sink the whole night
            print(f"Could not judge {result.url}: {e}")
    return verdicts
