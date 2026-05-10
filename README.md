# tunefinder

Find streaming links for any track across **Spotify**, **Apple Music**,
**Deezer**, **YouTube Music**, **Qobuz** and **SoundCloud** — using
DuckDuckGo as a search backend, with smart scoring that avoids returning
acoustic/remix versions when you asked for the original (and vice versa).

## Installation

```bash
pip install git+https://github.com/LouisCourrian/tunefinder.git
```

## Quickstart

```python
from tunefinder import find_links

links = find_links("9Lana", "Balalaika")
# {
#   "spotify":      "https://open.spotify.com/track/...",
#   "appleMusic":   "https://music.apple.com/...",
#   "deezer":       "https://www.deezer.com/track/...",
#   "youtubeMusic": "https://music.youtube.com/watch?v=...",
#   "qobuz":        "https://www.qobuz.com/fr-fr/album/...?track_id=...",
#   "soundcloud":   "https://soundcloud.com/artist/track-slug",
# }
```

Limit to specific platforms:

```python
find_links("9Lana", "Balalaika", platforms=["spotify", "deezer"])
```

## Why not just search?

DuckDuckGo (and any search engine) returns multiple versions of the same
track: studio, acoustic, live, remixes, covers, slowed/sped-up edits…
A naive `site:` search picks the first match, which often isn't the one
you want.

`tunefinder` solves this with a small scoring system:

- Detects whether **you** asked for a specific version (`"Title - Acoustic"`).
- Penalizes results containing version markers you didn't ask for.
- Bonifies results that match the version markers you did ask for.
- Deduplicates URLs by keeping the most informative snippet per URL.
- Tries multiple DuckDuckGo regions until a perfect match is found.

## Detailed output

For audit, JSON export, or UI integration, use `find_data` — it returns
all candidates ranked by score:

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

The first candidate of each platform list is the one selected. An empty
list means nothing was found for that platform.

## Debugging a result

If you suspect a wrong selection, print the full search trace:

```python
from tunefinder import print_search_debug

print_search_debug("9Lana", "Balalaika")
```

You'll see the selected candidate plus all alternatives, with their score,
region, description, and the markers detected (acoustic, live, remix…).

## Customization

For non-default behavior, pass a `Config` object:

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

## Supported platforms

| Platform      | Key in dict    | Notes                                                       |
| ------------- | -------------- | ----------------------------------------------------------- |
| Spotify       | `spotify`      | —                                                           |
| Apple Music   | `appleMusic`   | —                                                           |
| Deezer        | `deezer`       | —                                                           |
| YouTube Music | `youtubeMusic` | Indexation uneven on DuckDuckGo, some tracks won't surface. |
| Qobuz         | `qobuz`        | Track URL = album page + `?track_id=N` query string.        |
| SoundCloud    | `soundcloud`   | URLs are `/<artist>/<track-slug>` — playlists are excluded. |

## Unsupported platforms

These services were considered but cannot be supported reliably with
DuckDuckGo as a search backend:

| Platform     | Why it isn't supported                                                                                                                                |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tidal        | Tidal track pages (`tidal.com/browse/track/...`) are not indexed by DuckDuckGo — no results to score.                                                 |
| Amazon Music | Track pages are largely JS-rendered or behind a login wall; DuckDuckGo indexation is poor even when querying every regional TLD via `site:A OR site:B`. |
| Napster      | Since the rebrand, `app.napster.com` track pages are largely behind a login wall and have very weak SEO indexation.                                   |

If indexation improves for any of these, adding them is a one-entry change
in [`src/tunefinder/_platforms.py`](src/tunefinder/_platforms.py) plus URL
patterns in [`tests/test_platforms.py`](tests/test_platforms.py).

The URL regex accepts every Amazon Music TLD, so any regional URL returned
by DuckDuckGo is still validated. To add or remove regions, edit
``extra_sites`` on the ``amazonMusic`` entry in
[`src/tunefinder/_platforms.py`](src/tunefinder/_platforms.py).

## Limitations

- This library scrapes DuckDuckGo via the `ddgs` package. DuckDuckGo may
  rate-limit or change its HTML at any time, which can break the library
  until updated.
- Searching many tracks back-to-back (dozens or more) will eventually
  trigger rate limits. Consider increasing `delay_between_queries` or
  caching results in your own application.
- YouTube Music indexing on DuckDuckGo is uneven. Some official tracks
  may not surface in the results even though they exist.
- This is not affiliated with Spotify, Apple, Deezer, YouTube, or
  DuckDuckGo. All trademarks belong to their respective owners.

## Roadmap

`tunefinder` is currently at **v0.2.0**. The library is functional and
useful as-is, but a few items remain before tagging a stable **v1.0**.

### Toward v0.3 — housekeeping

- Replace the placeholder author metadata in `pyproject.toml`.
- Ship a `py.typed` marker so consumer projects pick up the type hints.
- Add a GitHub Actions workflow running `pytest + ruff + mypy` on every
  pull request, so `main` cannot regress silently.

### Toward v1.0 — stable API

- Decide and document the error contract: should a DDGS failure (network,
  rate-limit, parser break) raise an exception, or stay silent and return
  a partial dict? Whatever the choice, it gets locked at 1.0.
- Validate inputs explicitly: empty or whitespace-only artist/title
  should raise `ValueError` instead of silently returning no results.
- Add a retry/backoff loop on DDGS rate-limit exceptions instead of
  giving up after the first failure.
- Search platforms concurrently with a `ThreadPoolExecutor`. Today
  `find_links` runs the 6 platforms serially, which can take ~20 s for
  a full lookup — concurrent search would drop this to roughly the time
  of the slowest single platform.
- Bump the `Development Status` classifier to `5 - Production/Stable`
  once the API is considered frozen.

### Considered for later

- Optional in-process TTL cache via `Config(cache_ttl_seconds=...)`.
- CLI entry point: `python -m tunefinder "9Lana" "Balalaika"` printing
  the JSON output for shell scripting.
- An `async` variant for FastAPI / Starlette consumers.
- Integration tests hitting real DuckDuckGo, gated behind a `slow`
  marker and only run nightly.

## License

MIT — see [LICENSE](LICENSE).
