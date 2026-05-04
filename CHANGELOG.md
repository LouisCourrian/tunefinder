# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
