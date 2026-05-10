"""Tests du moteur de recherche, avec DDGS mocké pour ne pas faire de vrais appels réseau."""

from __future__ import annotations

import pytest

from tunefinder import PLATFORMS, Config, find_data, find_links


@pytest.fixture
def fast_config() -> Config:
    """Config sans pause entre requêtes ni pause de retry, pour accélérer les tests."""
    return Config(
        delay_between_queries=0.0,
        regions=("wt-wt",),
        initial_backoff_seconds=0.0,
        parallel=False,
    )


def _make_ddgs_mock(results_by_query: dict[str, list[dict[str, str]]]):
    """Construit une fausse classe DDGS qui renvoie des résultats prédéfinis.

    ``results_by_query`` : un dict ``{substring_de_la_requete: [resultats]}``.
    Le premier substring matché gagne.
    """

    class FakeDDGS:
        def text(self, query: str, region: str = "", max_results: int = 10):
            for substring, results in results_by_query.items():
                if substring in query:
                    return results
            return []

    return FakeDDGS


def test_find_links_picks_original_over_acoustic(
    fast_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Si l'utilisateur ne demande pas la version acoustique, l'originale gagne."""
    fake_ddgs = _make_ddgs_mock(
        {
            "site:open.spotify.com/track": [
                {
                    "href": "https://open.spotify.com/track/ACOUSTIC1",
                    "title": "Balalaika Acoustic - 9Lana",
                    "body": "9Lana acoustic version",
                },
                {
                    "href": "https://open.spotify.com/track/ORIGINAL1",
                    "title": "Balalaika - 9Lana",
                    "body": "9Lana single 2024",
                },
            ]
        }
    )
    monkeypatch.setattr("tunefinder._search.DDGS", fake_ddgs)

    links = find_links(
        "9Lana", "Balalaika", platforms=["spotify"], config=fast_config
    )
    assert links["spotify"] == "https://open.spotify.com/track/ORIGINAL1"


def test_find_links_picks_acoustic_when_requested(
    fast_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Si l'utilisateur demande explicitement 'Acoustic', cette version gagne."""
    fake_ddgs = _make_ddgs_mock(
        {
            "site:open.spotify.com/track": [
                {
                    "href": "https://open.spotify.com/track/ACOUSTIC1",
                    "title": "Balalaika Acoustic - 9Lana",
                    "body": "9Lana acoustic version",
                },
                {
                    "href": "https://open.spotify.com/track/ORIGINAL1",
                    "title": "Balalaika - 9Lana",
                    "body": "9Lana single 2024",
                },
            ]
        }
    )
    monkeypatch.setattr("tunefinder._search.DDGS", fake_ddgs)

    links = find_links(
        "9Lana", "Balalaika Acoustic", platforms=["spotify"], config=fast_config
    )
    assert links["spotify"] == "https://open.spotify.com/track/ACOUSTIC1"


def test_find_data_returns_all_candidates_sorted(
    fast_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_ddgs = _make_ddgs_mock(
        {
            "site:open.spotify.com/track": [
                {
                    "href": "https://open.spotify.com/track/ACOUSTIC1",
                    "title": "Balalaika Acoustic - 9Lana",
                    "body": "9Lana acoustic version",
                },
                {
                    "href": "https://open.spotify.com/track/ORIGINAL1",
                    "title": "Balalaika - 9Lana",
                    "body": "9Lana single 2024",
                },
            ]
        }
    )
    monkeypatch.setattr("tunefinder._search.DDGS", fake_ddgs)

    data = find_data(
        "9Lana", "Balalaika", platforms=["spotify"], config=fast_config
    )
    candidates = data["platforms"]["spotify"]
    assert len(candidates) == 2
    assert candidates[0]["score"] >= candidates[1]["score"]
    assert candidates[0]["url"] == "https://open.spotify.com/track/ORIGINAL1"


def test_find_data_empty_platform_when_no_results(
    fast_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("tunefinder._search.DDGS", _make_ddgs_mock({}))
    data = find_data(
        "Nobody", "Nothing", platforms=["spotify"], config=fast_config
    )
    assert data["platforms"]["spotify"] == []


def test_find_data_dedupes_keeping_best_snippet(
    fast_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Une même URL avec deux snippets différents → on garde celui avec le meilleur score."""
    fake_ddgs = _make_ddgs_mock(
        {
            "site:open.spotify.com/track": [
                {
                    "href": "https://open.spotify.com/track/SAME",
                    "title": "Random playlist mention",
                    "body": "this is a song",  # ni artiste ni titre
                },
                {
                    "href": "https://open.spotify.com/track/SAME",
                    "title": "Balalaika - 9Lana",
                    "body": "9Lana official single",  # both match
                },
            ]
        }
    )
    monkeypatch.setattr("tunefinder._search.DDGS", fake_ddgs)

    data = find_data(
        "9Lana", "Balalaika", platforms=["spotify"], config=fast_config
    )
    # Une seule URL après dédup
    assert len(data["platforms"]["spotify"]) == 1
    # Et c'est le bon snippet qui a été gardé (score = both match = 100)
    assert data["platforms"]["spotify"][0]["score"] == fast_config.score_both_match


def test_unknown_platform_raises(fast_config: Config) -> None:
    with pytest.raises(ValueError, match="Plateforme inconnue"):
        find_links("a", "b", platforms=["nonexistent"], config=fast_config)


@pytest.mark.parametrize(
    "artist,title",
    [
        ("", "Track"),
        ("Artist", ""),
        ("   ", "Track"),
        ("Artist", "\t\n  "),
        ("", ""),
    ],
)
def test_find_links_rejects_empty_or_whitespace_inputs(
    fast_config: Config, artist: str, title: str
) -> None:
    """Empty or whitespace-only inputs would just waste DDGS calls."""
    with pytest.raises(ValueError, match="must be a non-empty string"):
        find_links(artist, title, config=fast_config)


def test_find_links_rejects_non_string_inputs(fast_config: Config) -> None:
    with pytest.raises(ValueError, match="must be a non-empty string"):
        find_links(None, "Track", config=fast_config)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must be a non-empty string"):
        find_links("Artist", 42, config=fast_config)  # type: ignore[arg-type]


def test_find_data_rejects_empty_inputs(fast_config: Config) -> None:
    with pytest.raises(ValueError, match="must be a non-empty string"):
        find_data("", "Track", config=fast_config)


def test_print_search_debug_rejects_empty_inputs(fast_config: Config) -> None:
    from tunefinder import print_search_debug

    with pytest.raises(ValueError, match="must be a non-empty string"):
        print_search_debug("", "Track", config=fast_config)


# ---------------------------------------------------------------------------
# Retry / backoff on transient DDGS failures
# ---------------------------------------------------------------------------


def _spotify_hit() -> dict[str, str]:
    return {
        "href": "https://open.spotify.com/track/X",
        "title": "Balalaika - 9Lana",
        "body": "9Lana single",
    }


def test_ratelimit_is_retried_and_eventually_succeeds(
    fast_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A RatelimitException on the first call is retried; second call wins."""
    from ddgs.exceptions import RatelimitException

    calls = {"n": 0}

    class FlakyDDGS:
        def text(
            self, query: str, region: str = "", max_results: int = 10
        ) -> list[dict[str, str]]:
            calls["n"] += 1
            if calls["n"] == 1:
                raise RatelimitException("simulated rate limit")
            return [_spotify_hit()]

    monkeypatch.setattr("tunefinder._search.DDGS", FlakyDDGS)
    links = find_links(
        "9Lana", "Balalaika", platforms=["spotify"], config=fast_config
    )
    assert links == {"spotify": "https://open.spotify.com/track/X"}
    assert calls["n"] == 2  # one failure + one retry success


def test_retries_exhausted_then_gives_up_silently(
    fast_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If every attempt raises a transient error, we log and return empty."""
    from ddgs.exceptions import RatelimitException

    calls = {"n": 0}

    class AlwaysFlakyDDGS:
        def text(
            self, query: str, region: str = "", max_results: int = 10
        ) -> list[dict[str, str]]:
            calls["n"] += 1
            raise RatelimitException("rate-limited forever")

    monkeypatch.setattr("tunefinder._search.DDGS", AlwaysFlakyDDGS)
    links = find_links(
        "9Lana", "Balalaika", platforms=["spotify"], config=fast_config
    )
    assert links == {}
    # 2 queries (with / without quotes) × (1 initial + max_retries=2 retries)
    # = at most 6 attempts. With early_exit and 1 region, the first query
    # exhausts its 3 attempts, then the second query exhausts its 3.
    assert calls["n"] == (fast_config.max_retries + 1) * 2


# ---------------------------------------------------------------------------
# Concurrent platform search
# ---------------------------------------------------------------------------


def _all_platforms_mock() -> type:
    """Build a DDGS mock returning one canonical hit per platform site."""
    hits = {
        "site:open.spotify.com/track": [
            {
                "href": "https://open.spotify.com/track/SP",
                "title": "Balalaika - 9Lana",
                "body": "9Lana single",
            }
        ],
        "site:music.apple.com": [
            {
                "href": "https://music.apple.com/us/album/x/1?i=2",
                "title": "Balalaika - 9Lana",
                "body": "9Lana single",
            }
        ],
        "site:deezer.com": [
            {
                "href": "https://www.deezer.com/track/123",
                "title": "Balalaika - 9Lana",
                "body": "9Lana single",
            }
        ],
        "site:music.youtube.com": [
            {
                "href": "https://music.youtube.com/watch?v=abc",
                "title": "Balalaika - 9Lana",
                "body": "9Lana single",
            }
        ],
        "site:qobuz.com": [
            {
                "href": "https://www.qobuz.com/fr-fr/album/x/1?track_id=9",
                "title": "Balalaika - 9Lana",
                "body": "9Lana single",
            }
        ],
        "site:soundcloud.com": [
            {
                "href": "https://soundcloud.com/9lana/balalaika",
                "title": "Balalaika - 9Lana",
                "body": "9Lana single",
            }
        ],
    }

    class FakeDDGS:
        def text(
            self, query: str, region: str = "", max_results: int = 10
        ) -> list[dict[str, str]]:
            for substring, results in hits.items():
                if substring in query:
                    return results
            return []

    return FakeDDGS


def test_parallel_and_serial_produce_identical_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Threading must not change what comes out — only how fast."""
    monkeypatch.setattr("tunefinder._search.DDGS", _all_platforms_mock())

    base = Config(
        delay_between_queries=0.0,
        regions=("wt-wt",),
        initial_backoff_seconds=0.0,
    )
    serial = find_links("9Lana", "Balalaika", config=Config(**{
        **base.__dict__, "parallel": False,
    }))
    parallel = find_links("9Lana", "Balalaika", config=Config(**{
        **base.__dict__, "parallel": True,
    }))
    assert serial == parallel
    # Sanity: we got hits for all six platforms.
    assert set(serial) == set(PLATFORMS.keys())


def test_parallel_is_faster_than_serial_under_a_sleep_mock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With a slow DDGS, 6 parallel platforms should clearly beat serial."""
    import time as _time

    class SlowDDGS:
        def text(
            self, query: str, region: str = "", max_results: int = 10
        ) -> list[dict[str, str]]:
            _time.sleep(0.2)
            # Return nothing — we only care about timing here, not content.
            return []

    monkeypatch.setattr("tunefinder._search.DDGS", SlowDDGS)

    base = Config(
        delay_between_queries=0.0,
        regions=("wt-wt",),
        initial_backoff_seconds=0.0,
    )

    t0 = _time.perf_counter()
    find_links("9Lana", "Balalaika", config=Config(**{
        **base.__dict__, "parallel": False,
    }))
    serial_elapsed = _time.perf_counter() - t0

    t0 = _time.perf_counter()
    find_links("9Lana", "Balalaika", config=Config(**{
        **base.__dict__, "parallel": True, "max_workers": 6,
    }))
    parallel_elapsed = _time.perf_counter() - t0

    # 6 platforms × 2 queries × 0.2s ≈ 2.4s serial.
    # In parallel they all run concurrently → ≈ 0.4s (2 queries × 0.2s).
    # Generous threshold to absorb scheduler jitter on CI.
    assert parallel_elapsed < serial_elapsed * 0.6, (
        f"Parallel ({parallel_elapsed:.2f}s) should clearly beat "
        f"serial ({serial_elapsed:.2f}s)"
    )


def test_non_transient_error_is_not_retried(
    fast_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`DDGSException("No results")` is not transient — no retry."""
    from ddgs.exceptions import DDGSException

    calls = {"n": 0}

    class NoResultsDDGS:
        def text(
            self, query: str, region: str = "", max_results: int = 10
        ) -> list[dict[str, str]]:
            calls["n"] += 1
            raise DDGSException("No results found")

    monkeypatch.setattr("tunefinder._search.DDGS", NoResultsDDGS)
    links = find_links(
        "9Lana", "Balalaika", platforms=["spotify"], config=fast_config
    )
    assert links == {}
    # Exactly one attempt per query, no retries on a non-transient error.
    # 2 queries (with / without quotes) × 1 attempt = 2 calls.
    assert calls["n"] == 2


def test_find_data_structure_is_json_serializable(
    fast_config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json

    fake_ddgs = _make_ddgs_mock(
        {
            "site:open.spotify.com/track": [
                {
                    "href": "https://open.spotify.com/track/X",
                    "title": "Balalaika - 9Lana",
                    "body": "9Lana single",
                }
            ]
        }
    )
    monkeypatch.setattr("tunefinder._search.DDGS", fake_ddgs)

    data = find_data(
        "9Lana", "Balalaika", platforms=["spotify"], config=fast_config
    )
    # Ne doit pas lever
    json.dumps(data, ensure_ascii=False)
