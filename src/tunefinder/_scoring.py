"""Détection des marqueurs de version et calcul du score d'un résultat."""

from __future__ import annotations

import re
from typing import Any

from ._config import Config


def has_marker(text: str, marker: str) -> bool:
    """Vérifie qu'un marqueur apparaît comme un mot complet.

    Le ``\\b`` (frontière de mot) évite que ``live`` matche ``alive``,
    ``cover`` matche ``discover``, etc.
    """
    return re.search(r"\b" + re.escape(marker) + r"\b", text) is not None


def markers_in(text: str, markers: tuple[str, ...]) -> set[str]:
    """Renvoie l'ensemble des marqueurs présents dans un texte donné."""
    return {m for m in markers if has_marker(text, m)}


def score_result(
    result: dict[str, Any],
    artist_lower: str,
    title_lower: str,
    requested_markers: set[str],
    config: Config,
) -> int:
    """Calcule le score d'un résultat de recherche.

    Plus le score est élevé, mieux le résultat correspond à la recherche.

    Stocke aussi les détails du calcul sur ``result`` (clés ``markers_found``,
    ``markers_unwanted``, ``markers_matched``, ``markers_missing``) pour que
    le code appelant puisse les inspecter.
    """
    text = (result["title"] + " " + result["body"]).lower()
    score = 0

    has_artist = artist_lower in text
    has_title = title_lower in text
    if has_artist and has_title:
        score += config.score_both_match
    elif has_artist or has_title:
        score += config.score_one_match

    found = markers_in(text, config.version_markers)
    unwanted = found - requested_markers
    matched = found & requested_markers
    missing = requested_markers - found

    score += config.score_marker_unwanted * len(unwanted)
    score += config.score_marker_matched * len(matched)
    score += config.score_marker_missing * len(missing)

    result["markers_found"] = found
    result["markers_unwanted"] = unwanted
    result["markers_matched"] = matched
    result["markers_missing"] = missing
    return score
