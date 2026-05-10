"""Tests du moteur de recherche, avec DDGS mocké pour ne pas faire de vrais appels réseau."""

from __future__ import annotations

import pytest

from tunefinder import Config, find_data, find_links


@pytest.fixture
def fast_config() -> Config:
    """Config sans pause entre requêtes pour accélérer les tests."""
    return Config(delay_between_queries=0.0, regions=("wt-wt",))


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
