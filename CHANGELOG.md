# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Command-line interface** (`tunefinder ARTIST TITLE` after install,
  or `python -m tunefinder ...`). Output is JSON by default — compact
  when piping, indented automatically when stdout is a TTY. Supports
  `--platforms`, `--regions`, `--delay`, `--data` (full audit with
  scores), `--debug` (human-readable trace), `--pretty` and `--version`.
  Implementation lives in `src/tunefinder/__main__.py`; entry point
  registered via `[project.scripts]` in `pyproject.toml`.
- GitHub Actions release workflow (`.github/workflows/release.yml`):
  every pushed `v*.*.*` tag now publishes a GitHub Release with notes
  extracted automatically from `CHANGELOG.md`. Supports manual
  backfill via `workflow_dispatch` for tags pushed before this change.

### Changed

- README overhaul: centered header with badges (CI, latest release,
  Python versions, license, tests), emoji-headed sections, dedicated
  "Status" and "Roadmap to 1.0" sections with checkbox-tracked progress,
  and a `## Try it` quickstart for contributors.

## [0.3.0] - 2026-05-10

### Added

- PEP 561 `py.typed` marker — type annotations are now exposed to
  consumers' type checkers (mypy, pyright, …).
- GitHub Actions CI workflow running `ruff`, `mypy` and `pytest` on
  Python 3.10–3.13 for every push and PR on `main`.

### Changed

- Real author metadata and GitHub URLs in `pyproject.toml` (no more
  placeholders).
- `Development Status` classifier bumped from `3 - Alpha` to
  `4 - Beta` to reflect that the API is stabilising toward 1.0.

## [0.2.0] - 2026-05-10

### Added

- Support for **Qobuz** (`qobuz` key) — track URLs identified by
  `?track_id=N` on the album page.
- Support for **SoundCloud** (`soundcloud` key) — playlists (`/sets/`),
  user pages and system paths (`/likes`, `/reposts`, …) are excluded.

### Documented

- New "Unsupported platforms" section in the README explaining why
  **Tidal**, **Amazon Music** and **Napster** cannot be supported reliably
  with DuckDuckGo as a search backend (no/poor SEO indexation, login walls).
- New "Roadmap" section in the README outlining the work planned to
  reach v0.3 (housekeeping) and v1.0 (stable API).

## [0.1.0] - 2026-05-04

### Added

- Initial release.
- `find_links(artist, title)` — quick lookup returning `{platform: url}`.
- `find_data(artist, title)` — full structured output with all candidates ranked by score.
- `print_search_debug(artist, title)` — human-readable debug output.
- `Config` dataclass for tunable parameters (regions, version markers, scoring weights).
- Support for Spotify, Apple Music, Deezer, YouTube Music.
- Multi-region DDGS search with deduplication keeping the best snippet per URL.
- Version-marker-aware scoring (acoustic, live, remix, etc.) so the right
  version of a track is selected by default.
