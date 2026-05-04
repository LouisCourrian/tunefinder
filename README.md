# tunefinder

Find streaming links for any track across **Spotify**, **Apple Music**,
**Deezer** and **YouTube Music** — using DuckDuckGo as a search backend, with
smart scoring that avoids returning acoustic/remix versions when you asked
for the original (and vice versa).

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
#   "youtubeMusic": "https://music.youtube.com/watch?v=..."
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

| Platform      | Key in dict    |
| ------------- | -------------- |
| Spotify       | `spotify`      |
| Apple Music   | `appleMusic`   |
| Deezer        | `deezer`       |
| YouTube Music | `youtubeMusic` |

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

## License

MIT — see [LICENSE](LICENSE).
