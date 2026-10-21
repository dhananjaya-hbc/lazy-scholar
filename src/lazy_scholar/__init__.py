import sys
from datetime import date


def main() -> None:
    """One nightly run: search, skip seen URLs, judge with Gemma, remember, build the digest."""
    from lazy_scholar import db, digest
    from lazy_scholar.config import load_config
    from lazy_scholar.judge import judge_all
    from lazy_scholar.profile import load_profile
    from lazy_scholar.search import run_searches

    config = load_config()
    profile = load_profile()
    conn = db.connect(config.db_path)

    # `lazy-scholar --no-search` rebuilds from the database without using SerpApi searches.
    results = [] if "--no-search" in sys.argv else run_searches(config)
    fresh = db.remember(conn, results)
    retry = [r for r in db.unjudged(conn) if r.url not in {f.url for f in fresh}]
    to_judge = fresh + retry
    print(f"{len(results)} results, {len(fresh)} new, {len(retry)} to retry")

    verdicts = judge_all(config, profile, to_judge, on_verdict=lambda v: db.save_verdicts(conn, [v]))

    matches = db.open_matches(conn)
    # "New" means first found today, so a --no-search rebuild keeps the same headline.
    today = date.today().isoformat()
    new_urls = {m["url"] for m in matches if m["first_seen"] == today}
    print(f"Judged {len(verdicts)}: {len(new_urls)} new matches, {len(matches)} open in total")
    for m in matches:
        print(f"  {m['score']:3} {m['category']:11} {m['deadline'] or 'no deadline':11} {m['title'][:60]}")

    print(f"Digest written to {digest.build(config, matches, new_urls)}")
