"""Tests des patterns d'URL des plateformes."""

from __future__ import annotations

import pytest

from tunefinder._platforms import PLATFORMS


@pytest.mark.parametrize(
    "platform,url",
    [
        ("spotify", "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp"),
        ("appleMusic", "https://music.apple.com/us/album/test/123?i=456"),
        ("appleMusic", "https://music.apple.com/fr/song/test/789"),
        ("deezer", "https://www.deezer.com/track/123456"),
        ("deezer", "https://www.deezer.com/fr/track/123456"),
        ("youtubeMusic", "https://music.youtube.com/watch?v=dQw4w9WgXcQ"),
        ("youtubeMusic", "https://music.youtube.com/watch?v=abc-DEF_123"),
    ],
)
def test_pattern_matches_valid_url(platform: str, url: str) -> None:
    pattern = PLATFORMS[platform].pattern
    assert pattern.search(url) is not None, f"{url} should match {platform}"


@pytest.mark.parametrize(
    "platform,url",
    [
        # mauvaises plateformes
        ("spotify", "https://open.spotify.com/album/123"),
        ("spotify", "https://open.spotify.com/playlist/123"),
        ("deezer", "https://www.deezer.com/album/123"),
        # mauvais protocole / domaine
        ("spotify", "http://open.spotify.com/track/abc"),
        ("youtubeMusic", "https://www.youtube.com/watch?v=abc"),
    ],
)
def test_pattern_rejects_invalid_url(platform: str, url: str) -> None:
    pattern = PLATFORMS[platform].pattern
    assert pattern.search(url) is None, f"{url} should NOT match {platform}"


def test_all_platforms_have_required_attributes() -> None:
    for name, plat in PLATFORMS.items():
        assert plat.name == name
        assert plat.site, f"{name} missing site"
        assert plat.pattern is not None, f"{name} missing pattern"
