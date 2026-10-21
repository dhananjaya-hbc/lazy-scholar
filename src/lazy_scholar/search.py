"""Nightly web search via SerpApi.

Free plan: 250 searches/month. At 6 queries a night that is ~186 a month,
leaving room for manual test runs.
"""

from dataclasses import dataclass

import serpapi

from lazy_scholar.config import Config

MAX_QUERIES_PER_RUN = 6
# Stop early if the account is nearly out, so test runs never burn the last searches.
MIN_SEARCHES_LEFT = 10

# Job boards return lists of many jobs, which Gemma cannot judge one by one.
NO_JOB_BOARDS = (
    "-site:indeed.com -site:glassdoor.com -site:ziprecruiter.com"
    " -site:linkedin.com -site:simplyhired.com"
)

# Tuned to the profile: IT undergraduate in Sri Lanka, local or remote only.
QUERIES = [
    "scholarship for Sri Lankan undergraduate IT students apply 2026",
    f"remote paid internship software engineering students worldwide apply {NO_JOB_BOARDS}",
    f"remote AI LLM internship paid undergraduate apply {NO_JOB_BOARDS}",
    "online hackathon cash prize AI generative AI students 2026",
    "online blockchain hackathon prize students apply",
    "grant for undergraduate students Sri Lanka technology research",
]


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    query: str
    date: str | None = None


def searches_left(client: serpapi.Client) -> int:
    """Remaining searches this month. The account endpoint is free."""
    account = client.account()
    return int(account.get("total_searches_left", 0))


def run_searches(config: Config, queries: list[str] = QUERIES) -> list[SearchResult]:
    if not config.serpapi_api_key:
        raise RuntimeError("SERPAPI_API_KEY is not set")
    client = serpapi.Client(api_key=config.serpapi_api_key)

    left = searches_left(client)
    budget = min(MAX_QUERIES_PER_RUN, left - MIN_SEARCHES_LEFT)
    if budget <= 0:
        print(f"Skipping search: only {left} SerpApi searches left this month")
        return []

    results: list[SearchResult] = []
    seen: set[str] = set()
    for query in queries[:budget]:
        # tbs=qdr:m keeps results from the past month (past week returned too few);
        # SQLite drops URLs already seen, so repeats never reach the digest.
        response = client.search({"engine": "google", "q": query, "num": 10, "tbs": "qdr:m"})
        for item in response.get("organic_results", []):
            url = item.get("link")
            if not url or url in seen:
                continue
            seen.add(url)
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=url,
                    snippet=item.get("snippet", ""),
                    query=query,
                    date=item.get("date"),
                )
            )
    return results


if __name__ == "__main__":
    from lazy_scholar.config import load_config

    for r in run_searches(load_config(), QUERIES[:1]):
        print(f"- {r.title}\n  {r.url}\n  {r.snippet}\n")
