"""Plateformes de streaming supportées et leurs patterns d'URL.

Chaque entrée définit :
- ``site`` : le domaine utilisé dans la requête ``site:`` envoyée à DuckDuckGo
- ``pattern`` : une expression régulière compilée pour valider/extraire l'URL
  d'un morceau depuis les résultats de recherche.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Platform:
    """Description d'une plateforme de streaming."""

    name: str
    site: str
    pattern: re.Pattern[str]


PLATFORMS: dict[str, Platform] = {
    "spotify": Platform(
        name="spotify",
        site="open.spotify.com/track",
        pattern=re.compile(r"https://open\.spotify\.com/track/[a-zA-Z0-9]+"),
    ),
    "appleMusic": Platform(
        name="appleMusic",
        site="music.apple.com",
        pattern=re.compile(
            r"https://music\.apple\.com/[a-z]{2,3}/"
            r"(?:album/[^?\s\"'<>]+\?i=\d+|song/[^?\s\"'<>]+/\d+|song/\d+)"
        ),
    ),
    "deezer": Platform(
        name="deezer",
        site="deezer.com",
        pattern=re.compile(r"https://www\.deezer\.com/(?:[a-z]{2}/)?track/\d+"),
    ),
    "youtubeMusic": Platform(
        name="youtubeMusic",
        site="music.youtube.com",
        pattern=re.compile(r"https://music\.youtube\.com/watch\?v=[a-zA-Z0-9_-]+"),
    ),
}
