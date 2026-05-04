"""Tests du module de scoring."""

from __future__ import annotations

from tunefinder._config import Config
from tunefinder._scoring import has_marker, markers_in, score_result


def test_has_marker_word_boundary() -> None:
    """``\\b`` doit matcher des mots complets uniquement."""
    assert has_marker("acoustic version of the song", "acoustic")
    assert not has_marker("alive in the city", "live")  # 'live' dans 'alive'
    assert not has_marker("discover this", "cover")  # 'cover' dans 'discover'


def test_markers_in_returns_set() -> None:
    cfg = Config()
    found = markers_in("balalaika acoustic version", cfg.version_markers)
    assert "acoustic" in found
    # "version" seul n'est pas dans la liste
    assert "version" not in found


def test_score_both_match() -> None:
    cfg = Config()
    result = {
        "title": "Balalaika - 9Lana",
        "body": "Listen to balalaika by 9lana on Spotify",
    }
    score = score_result(result, "9lana", "balalaika", set(), cfg)
    assert score == cfg.score_both_match


def test_score_only_artist() -> None:
    cfg = Config()
    result = {"title": "Some Other Track", "body": "by 9lana"}
    score = score_result(result, "9lana", "balalaika", set(), cfg)
    assert score == cfg.score_one_match


def test_score_unwanted_marker_penalized() -> None:
    """Sur une recherche normale, un résultat acoustic doit être pénalisé."""
    cfg = Config()
    result = {
        "title": "Balalaika Acoustic Version",
        "body": "9Lana acoustic ver.",
    }
    requested: set[str] = set()  # pas de version demandée
    score = score_result(result, "9lana", "balalaika", requested, cfg)
    # both match (+100) puis pénalité acoustic + ver
    assert score < cfg.score_both_match


def test_score_requested_marker_bonus() -> None:
    """Si on demande la version acoustique, elle doit être bonifiée."""
    cfg = Config()
    result = {
        "title": "Balalaika Acoustic Version",
        "body": "9Lana acoustic",
    }
    requested = {"acoustic"}
    score = score_result(result, "9lana", "balalaika", requested, cfg)
    # both match (+100) + acoustic matched (+30)
    expected = cfg.score_both_match + cfg.score_marker_matched
    assert score == expected


def test_score_stores_marker_details() -> None:
    """Le scoring doit annoter le résultat avec les marqueurs détectés."""
    cfg = Config()
    result: dict = {
        "title": "Balalaika Acoustic",
        "body": "9Lana version acoustique",
    }
    score_result(result, "9lana", "balalaika", set(), cfg)
    assert "acoustic" in result["markers_found"]
    assert "acoustic" in result["markers_unwanted"]
    assert result["markers_matched"] == set()
