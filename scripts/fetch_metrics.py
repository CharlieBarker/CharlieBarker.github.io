#!/usr/bin/env python3
"""Fetch publication metrics from OpenAlex (and optionally Altmetric) and write
assets/data/metrics.json for the /metrics/ page.

Environment variables (all optional):
  OPENALEX_API_KEY   raises the OpenAlex rate budget
  ALTMETRIC_API_KEY  enables Altmetric scores (the API now requires a key)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ORCID = "0000-0002-5223-6838"
OUT = Path(__file__).resolve().parent.parent / "assets" / "data" / "metrics.json"

# Only count real papers; OpenAlex also lists peer-review replies and supplements.
INCLUDE_TYPES = {"article", "preprint"}
EXCLUDE_DOIS = set()  # lowercase DOIs to drop entirely
# Preprint/journal versions of one paper are merged when their titles match, or
# when listed here as {preprint_doi: journal_doi}.
MERGE = {"10.1101/2024.12.05.626952": "10.1038/s44320-025-00183-5"}

EMAIL = "charbarker96@gmail.com"


def get(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": f"metrics-script ({EMAIL})"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if i == retries - 1:
                raise
        except urllib.error.URLError:
            if i == retries - 1:
                raise
        time.sleep(2 * (i + 1))


def openalex(path, **params):
    params["mailto"] = EMAIL
    if os.environ.get("OPENALEX_API_KEY"):
        params["api_key"] = os.environ["OPENALEX_API_KEY"]
    return get(f"https://api.openalex.org/{path}?{urllib.parse.urlencode(params)}")


def norm_doi(doi):
    return (doi or "").lower().replace("https://doi.org/", "")


def norm_title(t):
    return "".join(c for c in t.lower() if c.isalnum())


def h_index(counts):
    counts = sorted(counts, reverse=True)
    return sum(1 for i, c in enumerate(counts, 1) if c >= i)


def fetch_works(author_id):
    works, cursor = [], "*"
    while cursor:
        page = openalex(
            "works",
            filter=f"author.orcid:{ORCID}",
            select="id,doi,title,publication_year,publication_date,cited_by_count,"
                   "counts_by_year,authorships,type,primary_location",
            **{"per-page": 100, "cursor": cursor},
        )
        works += page["results"]
        cursor = page["meta"].get("next_cursor")
        if not page["results"]:
            break
    return works


def build_papers(raw, author_id):
    papers = {}
    for w in raw:
        doi = norm_doi(w.get("doi"))
        if w["type"] not in INCLUDE_TYPES or doi in EXCLUDE_DOIS:
            continue
        pos = next((a["author_position"] for a in w["authorships"]
                    if (a["author"].get("id") or "").endswith(author_id)), None)
        by_year = {c["year"]: c["cited_by_count"] for c in w["counts_by_year"]}
        residual = w["cited_by_count"] - sum(by_year.values())
        source = ((w.get("primary_location") or {}).get("source") or {}).get("display_name")
        key = MERGE.get(doi, doi) or w["id"]
        # Same paper listed twice (preprint + journal): merge by title.
        key = next((k for k, p in papers.items() if p["_tkey"] == norm_title(w["title"])), key)
        if key in papers:
            p = papers[key]
            for y, c in by_year.items():
                p["_by_year"][y] = p["_by_year"].get(y, 0) + c
            p["_residual"] += residual
            p["first_author"] = p["first_author"] or pos == "first"
            p["dois"].append(doi)
            # prefer the journal version's title/venue/date (non-preprint)
            if w["type"] == "article":
                p.update(title=w["title"], venue=source, doi=doi, type="article")
            p["year"] = min(p["year"], w["publication_year"])
            p["date"] = min(p["date"], w["publication_date"])
            continue
        papers[key] = dict(
            title=w["title"], doi=doi, dois=[doi], year=w["publication_year"],
            date=w["publication_date"], venue=source, type=w["type"],
            first_author=pos == "first", _by_year=by_year, _residual=residual,
            _tkey=norm_title(w["title"]),
        )
    return list(papers.values())


def altmetric(papers):
    key = os.environ.get("ALTMETRIC_API_KEY")
    if not key:
        print("ALTMETRIC_API_KEY not set; skipping Altmetric", file=sys.stderr)
        return False
    for p in papers:
        best = None
        for doi in p["dois"]:
            d = get(f"https://api.altmetric.com/v1/doi/{doi}?key={key}")
            if d and (best is None or d.get("score", 0) > best.get("score", 0)):
                best = d
        if best:
            p["altmetric"] = dict(score=round(best.get("score", 0), 1),
                                  posts=best.get("cited_by_posts_count", 0),
                                  url=best.get("details_url"))
        time.sleep(1)
    return True


def yearly(papers, first_only):
    ps = [p for p in papers if p["first_author"] or not first_only]
    if not ps:
        return []
    start, end = min(p["year"] for p in ps), date.today().year
    rows = []
    for y in range(start, end + 1):
        cum = []
        for p in ps:
            if p["year"] > y:
                continue
            cum.append(p["_residual"] + sum(c for yy, c in p["_by_year"].items() if yy <= y))
        rows.append(dict(
            year=y, papers=len(cum), citations=sum(cum), h_index=h_index(cum),
            new_citations=sum(p["_by_year"].get(y, 0) for p in ps),
        ))
    return rows


def main():
    author = openalex("authors/orcid:" + ORCID, select="id,display_name")
    author_id = author["id"].rsplit("/", 1)[-1]
    papers = build_papers(fetch_works(author_id), author_id)
    have_alt = altmetric(papers)

    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    snapshots = prev.get("snapshots", [])
    totals = dict(
        date=date.today().isoformat(), papers=len(papers),
        first_author_papers=sum(p["first_author"] for p in papers),
        citations=sum(p["_residual"] + sum(p["_by_year"].values()) for p in papers),
        h_index=h_index([p["_residual"] + sum(p["_by_year"].values()) for p in papers]),
        altmetric=round(sum(p.get("altmetric", {}).get("score", 0) for p in papers), 1) if have_alt else None,
    )
    if not snapshots or {k: v for k, v in snapshots[-1].items() if k != "date"} != \
            {k: v for k, v in totals.items() if k != "date"}:
        snapshots.append(totals)

    series = dict(all=yearly(papers, False), first_author=yearly(papers, True))
    for p in papers:
        total = p["_residual"] + sum(p["_by_year"].values())
        p["citations"] = total
        p["by_year"] = {str(y): c for y, c in sorted(p["_by_year"].items())}
        for k in ("_by_year", "_residual", "_tkey"):
            p.pop(k)
    papers.sort(key=lambda p: p["date"], reverse=True)

    out = dict(
        generated=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        author=author["display_name"], source="OpenAlex", altmetric_enabled=have_alt,
        totals=totals,
        yearly=series,
        papers=papers, snapshots=snapshots,
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {OUT}: {len(papers)} papers, {totals['citations']} citations, h={totals['h_index']}")


if __name__ == "__main__":
    main()
