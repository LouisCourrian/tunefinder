# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
