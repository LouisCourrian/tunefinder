<div align="center">

# 🎵 tunefinder

**Find the streaming link of any track across every major platform — in one line of Python.**

[![CI](https://github.com/LouisCourrian/tunefinder/actions/workflows/ci.yml/badge.svg)](https://github.com/LouisCourrian/tunefinder/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/LouisCourrian/tunefinder)](https://github.com/LouisCourrian/tunefinder/releases)
[![Python versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-36%20passed-brightgreen.svg)](tests/)

*Spotify, Apple Music, Deezer, YouTube Music, Qobuz, SoundCloud — one call, every link.*

</div>

---

```python
from tunefinder import find_links

find_links("9Lana", "Balalaika")
# {
#   "spotify":      "https://open.spotify.com/track/...",
#   "appleMusic":   "https://music.apple.com/...",
#   "deezer":       "https://www.deezer.com/track/...",
#   "youtubeMusic": "https://music.youtube.com/watch?v=...",
#   "qobuz":        "https://www.qobuz.com/fr-fr/album/...?track_id=...",
#   "soundcloud":   "https://soundcloud.com/9lana/aovo7ub0aqee",
# }
```

That's it. No API keys, no OAuth, no manual setup — `tunefinder` searches
DuckDuckGo with platform-specific filters and a scoring system that picks
the *original* version of a track over remixes, covers and acoustic edits.

## ✨ Features

- 🎯 **Smart version scoring** — penalises acoustic / remix / live results when you didn't ask for them
- 🌍 **Multi-region fallback** — iterates DuckDuckGo regions until a perfect-score match is found
- 🪶 **One dependency** — just [`ddgs`](https://pypi.org/project/ddgs/), no auth, no API keys
- 🔌 **Six platforms** — Spotify, Apple Music, Deezer, YouTube Music, Qobuz, SoundCloud
- 🧠 **Deduplicated results** — same URL with multiple snippets keeps only the best-scoring one
- 🐛 **Inspectable** — `find_data()` returns every candidate with scores, `print_search_debug()` traces the search
- 🧪 **Typed** — `mypy --strict` clean and ships PEP 561 `py.typed`

## 📦 Installation

```bash
pip install git+https://github.com/LouisCourrian/tunefinder.git
```

## 🚀 Quick start

### Find a link

```python
from tunefinder import find_links

links = find_links("Stromae", "Alors on danse")
print(links["spotify"])
# → https://open.spotify.com/track/...
```

Limit to specific platforms:

```python
find_links("Stromae", "Alors on danse", platforms=["spotify", "deezer"])
```

### Get all candidates with scores

For audit, JSON export or UI integration, use `find_data` — it returns
every candidate ranked by score:

```python
import json
from tunefinder import find_data

data = find_data("9Lana", "Balalaika")
print(json.dumps(data, indent=2, ensure_ascii=False))
```

```json
{
  "artist": "9Lana",
  "title": "Balalaika",
  "requested_markers": [],
  "platforms": {
    "spotify": [
      {
        "url": "https://open.spotify.com/track/abc",
        "score": 100,
        "region": "wt-wt",
        "result_title": "Balalaika - Single by 9Lana | Spotify",
        "result_description": "Listen to Balalaika on Spotify...",
        "markers_detected": []
      }
    ],
    "deezer": []
  }
}
```

The first candidate of each platform list is the one `find_links` would
return. An empty list means nothing was found for that platform.

### Debug a tricky result

```python
from tunefinder import print_search_debug

print_search_debug("9Lana", "Balalaika")
```

Prints the selected candidate plus all alternatives, with their score,
region, description, and detected markers (acoustic, live, remix…).

### Tune the search

```python
from tunefinder import Config, find_links

config = Config(
    regions=("fr-fr", "us-en"),     # only these two regions
    delay_between_queries=0.5,      # be more polite to DuckDuckGo
    score_marker_unwanted=-80,      # stronger penalty for unwanted versions
)

find_links("Stromae", "Alors on danse", config=config)
```

All `Config` fields are documented in `Config.__doc__`.

## 🛠️ CLI

`tunefinder` also exposes a small command-line interface — handy for
shell scripts, smoke tests, or one-off lookups without writing Python:

```bash
# JSON dict on stdout (compact for piping, indented when stdout is a TTY)
tunefinder "9Lana" "Balalaika"

# Restrict to specific platforms
tunefinder "9Lana" "Balalaika" --platforms spotify deezer

# Full audit: every candidate with scores, as JSON
tunefinder "9Lana" "Balalaika" --data

# Human-readable trace: which candidate won and why
tunefinder "9Lana" "Balalaika" --debug

# Tune the search
tunefinder "Stromae" "Alors on danse" --regions fr-fr us-en --delay 0.5
```

It also runs as `python -m tunefinder ...` if the entry point is not on
your `PATH` (useful in unactivated virtual environments).

Run `tunefinder --help` for the full reference.

## 🎯 Why not just search?

DuckDuckGo (and any search engine) returns multiple versions of the same
track: studio, acoustic, live, remixes, covers, slowed/sped-up edits…
A naive `site:` search picks the first match, which often isn't the one
you want.

`tunefinder` solves this with a small scoring system:

- Detects whether **you** asked for a specific version (`"Title - Acoustic"`).
- Penalises results containing version markers you didn't ask for.
- Bonifies results that match the version markers you did ask for.
- Deduplicates URLs by keeping the most informative snippet per URL.
- Tries multiple DuckDuckGo regions until a perfect match is found.

## 🎚️ Supported platforms

| Platform      | Key in dict    | Notes                                                       |
| ------------- | -------------- | ----------------------------------------------------------- |
| Spotify       | `spotify`      | —                                                           |
| Apple Music   | `appleMusic`   | —                                                           |
| Deezer        | `deezer`       | —                                                           |
| YouTube Music | `youtubeMusic` | Indexation uneven on DuckDuckGo, some tracks won't surface. |
| Qobuz         | `qobuz`        | Track URL = album page + `?track_id=N` query string.        |
| SoundCloud    | `soundcloud`   | URLs are `/<artist>/<track-slug>` — playlists are excluded. |

## 🚫 Unsupported platforms

These services were considered but cannot be supported reliably with
DuckDuckGo as a search backend:

| Platform     | Why it isn't supported                                                                                                                                  |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tidal        | Tidal track pages (`tidal.com/browse/track/...`) are not indexed by DuckDuckGo — no results to score.                                                   |
| Amazon Music | Track pages are largely JS-rendered or behind a login wall; DuckDuckGo indexation is poor even when querying every regional TLD via `site:A OR site:B`. |
| Napster      | Since the rebrand, `app.napster.com` track pages are largely behind a login wall and have very weak SEO indexation.                                     |

If indexation improves for any of these, adding them is a one-entry
change in [`src/tunefinder/_platforms.py`](src/tunefinder/_platforms.py)
plus URL patterns in [`tests/test_platforms.py`](tests/test_platforms.py).

## 🔍 How does it actually work?

For each requested platform, `tunefinder`:

1. Builds a `site:<domain> "<artist>" "<title>"` query.
2. Sends it to DuckDuckGo via the [`ddgs`](https://pypi.org/project/ddgs/) package, iterating through a list of regions.
3. Filters returned URLs against a per-platform regex (`spotify.com/track/...`, etc.).
4. Scores each candidate against the requested artist + title and any version markers you asked for.
5. Returns the top-scoring URL — and short-circuits as soon as a perfect match is found in any region.

## 📜 Error contract

The public API has a small, stable contract — locked at 1.0 and protected
by Semantic Versioning afterwards:

- **Empty / whitespace / non-string `artist` or `title`** → `ValueError`
  raised immediately, before any DDGS call.
- **Unknown platform name** in `platforms=[...]` → `ValueError`.
- **DDGS errors** (rate-limit, timeout, network failure, "no results")
  → logged at `WARNING` level on the `tunefinder._search` logger; the
  affected platform simply does not appear in the returned dict
  (`find_links`) or has an empty candidate list (`find_data`). The call
  **never propagates a `DDGSException`** to the caller — partial results
  are preferred over hard failures.

If you need to react to DDGS warnings, configure logging:

```python
import logging
logging.getLogger("tunefinder._search").setLevel(logging.WARNING)
logging.basicConfig()
```

## ⚠️ Limitations

- DuckDuckGo may rate-limit or change its HTML at any time, which can
  break the library until updated.
- Searching many tracks back-to-back (dozens or more) will eventually
  trigger rate limits. Increase `delay_between_queries` or cache results
  in your own application.
- YouTube Music indexing on DuckDuckGo is uneven. Some official tracks
  may not surface in the results even though they exist.
- This is not affiliated with Spotify, Apple, Deezer, YouTube, Qobuz,
  SoundCloud, or DuckDuckGo. All trademarks belong to their respective
  owners.

## 🧪 Try it

```bash
git clone https://github.com/LouisCourrian/tunefinder
cd tunefinder
pip install -e ".[dev]"
pytest
```

## ✅ Status

`tunefinder` is **stable** as of `1.0.0`. The public API — `find_links`,
`find_data`, `print_search_debug`, `Config`, `PLATFORMS` — follows
[Semantic Versioning](https://semver.org/). Pin to a major version
(`tunefinder>=1.0,<2.0`) and you're good.

See [CHANGELOG.md](CHANGELOG.md) for the full release history and the
versioning policy.

## 🗺️ Release history

### Done in 0.3

- [x] **Real package metadata** in `pyproject.toml` (no more placeholders).
- [x] **PEP 561 `py.typed` marker** — type annotations exposed to consumer
      type checkers (mypy, pyright, …).
- [x] **GitHub Actions CI** — `ruff` + `mypy --strict` + `pytest` on
      Python 3.10–3.13 for every push and PR on `main`.

### Done in 0.4

- [x] **Automated GitHub releases** — pushing a `v*.*.*` tag publishes a
      release whose body is extracted from `CHANGELOG.md`.
- [x] **CLI** — `tunefinder ARTIST TITLE` (or `python -m tunefinder ...`)
      with `--data` / `--debug` / `--platforms` / `--regions` /
      `--delay` / `--pretty` flags. Output is JSON by default
      (compact for piping, indented on a TTY).

### Done in 1.0

- [x] **Input validation** — empty / whitespace / non-string `artist`
      or `title` raises `ValueError` before any DDGS call. CLI surfaces
      it as a clean one-line error.
- [x] **Retry / backoff on rate-limit** — `RatelimitException` and
      `TimeoutException` are retried with exponential backoff. Non-
      transient errors (e.g. "no results found") are not retried.
- [x] **Concurrent platform search** — `ThreadPoolExecutor` runs the
      6 platforms in parallel. A full lookup drops from ~20 s to
      roughly the slowest single platform.
- [x] **Error contract documented** — explicit section in the README
      and `find_links`' docstring. Locked under SemVer.
- [x] **`Development Status :: 5 - Production/Stable`** + tag `v1.0.0`.

### Considered for later

- [ ] Optional in-process TTL cache via `Config(cache_ttl_seconds=...)`.
- [ ] `async` variant for FastAPI / Starlette consumers.
- [ ] Native API fallback for Apple Music (iTunes Search) and Deezer
      (api.deezer.com) — free, no key, more reliable than DDGS for
      those two.

## 📄 License

MIT — see [LICENSE](LICENSE).

`tunefinder` is an independent project, not affiliated with Spotify,
Apple Music, Deezer, YouTube Music, Qobuz, SoundCloud, or DuckDuckGo.
All trademarks belong to their respective owners.
