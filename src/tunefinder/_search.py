"""Moteur de recherche et API publique de tunefinder."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from ddgs import DDGS
from ddgs.exceptions import RatelimitException, TimeoutException

from ._config import Config, get_default_config
from ._platforms import PLATFORMS, Platform
from ._scoring import markers_in, score_result

# Erreurs DDGS qu'on retente : rate-limit et timeout réseau. Les autres
# (notamment ``DDGSException("No results found")`` quand la requête ne
# renvoie rien) sont par nature non transitoires — pas la peine d'attendre.
_RETRYABLE_DDGS_EXCEPTIONS: tuple[type[BaseException], ...] = (
    RatelimitException,
    TimeoutException,
)

logger = logging.getLogger(__name__)


def _validate_query(artist: str, title: str) -> None:
    """Reject empty / whitespace-only inputs at the API boundary.

    Doing this here means ``find_links``, ``find_data`` and
    ``print_search_debug`` all share the same rejection contract — a
    single source of truth for the public API.
    """
    if not isinstance(artist, str) or not artist.strip():
        raise ValueError(
            f"artist must be a non-empty string, got {artist!r}"
        )
    if not isinstance(title, str) or not title.strip():
        raise ValueError(
            f"title must be a non-empty string, got {title!r}"
        )


def _ddgs_text_with_retry(
    query: str, region: str, config: Config
) -> list[dict[str, Any]]:
    """Wrap ``DDGS().text(...)`` with exponential backoff on transient errors.

    Retries up to ``config.max_retries`` times on rate-limit / timeout, with
    an exponential delay between attempts. Non-transient errors (e.g.
    ``DDGSException("No results found")``) are re-raised immediately so the
    caller can decide how to handle them.
    """
    last_exc: BaseException | None = None
    for attempt in range(config.max_retries + 1):
        try:
            return list(
                DDGS().text(
                    query,
                    region=region,
                    max_results=config.max_results_per_query,
                )
            )
        except _RETRYABLE_DDGS_EXCEPTIONS as exc:
            last_exc = exc
            if attempt >= config.max_retries:
                break
            backoff = config.initial_backoff_seconds * (
                config.backoff_multiplier**attempt
            )
            logger.warning(
                "DDGS transient error (attempt %d/%d) for query=%r region=%s: "
                "%s — retrying in %.1fs",
                attempt + 1,
                config.max_retries + 1,
                query,
                region,
                exc,
                backoff,
            )
            time.sleep(backoff)
    # Exhausted retries on a transient error: re-raise so the outer
    # _collect_results handler logs it and we move on to the next region.
    assert last_exc is not None  # narrows type for mypy
    raise last_exc


def _collect_results(
    query: str,
    platform: Platform,
    region: str,
    config: Config,
) -> list[dict[str, Any]]:
    """Lance UNE recherche DDGS (avec retry) et filtre par pattern d'URL."""
    results: list[dict[str, Any]] = []
    try:
        for r in _ddgs_text_with_retry(query, region, config):
            m = platform.pattern.search(r.get("href", ""))
            if m:
                results.append(
                    {
                        "url": m.group(0),
                        "title": r.get("title", ""),
                        "body": r.get("body", ""),
                    }
                )
    except Exception as exc:  # noqa: BLE001 — on logge mais on continue
        logger.warning(
            "DDGS error for query=%r region=%s: %s", query, region, exc
        )
    return results


def _search_one_platform(
    artist: str,
    title: str,
    platform_name: str,
    config: Config,
    *,
    early_exit: bool,
) -> dict[str, Any]:
    """Recherche bas niveau sur une seule plateforme.

    Renvoie toujours un dict avec ``selected``, ``candidates``, ``requested_markers``.

    Si ``early_exit`` est True, on arrête dès qu'un résultat atteint le score
    parfait — c'est ce que veut l'utilisateur "rapide". Sinon on parcourt
    toutes les régions pour avoir une vue complète (mode debug / data).
    """
    if platform_name not in PLATFORMS:
        raise ValueError(
            f"Plateforme inconnue : {platform_name!r}. "
            f"Plateformes valides : {sorted(PLATFORMS.keys())}"
        )
    platform = PLATFORMS[platform_name]
    a, t = artist.lower(), title.lower()

    requested = markers_in(a + " " + t, config.version_markers)

    queries = [
        f'site:{platform.site} "{artist}" "{title}"',
        f'site:{platform.site} {artist} {title}',
    ]

    all_results: list[dict[str, Any]] = []
    perfect_score = config.score_both_match + config.score_marker_matched * len(
        requested
    )

    for region in config.regions:
        for query in queries:
            new_results = _collect_results(query, platform, region, config)
            for r in new_results:
                r["region"] = region
                r["score"] = score_result(r, a, t, requested, config)
                all_results.append(r)

            if early_exit and all_results:
                best = max(all_results, key=lambda x: x["score"])
                if best["score"] >= perfect_score:
                    # Déduplication minimale puis renvoi
                    deduped = _dedupe_keep_best(all_results)
                    deduped.sort(key=lambda r: r["score"], reverse=True)
                    return {
                        "selected": deduped[0] if deduped else None,
                        "candidates": deduped[1:],
                        "requested_markers": requested,
                    }

            time.sleep(config.delay_between_queries)

    if not all_results:
        return {
            "selected": None,
            "candidates": [],
            "requested_markers": requested,
        }

    deduped = _dedupe_keep_best(all_results)
    deduped.sort(key=lambda r: r["score"], reverse=True)
    return {
        "selected": deduped[0],
        "candidates": deduped[1:],
        "requested_markers": requested,
    }


def _dedupe_keep_best(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pour chaque URL, garde uniquement le résultat avec le meilleur score.

    DDGS renvoie souvent une même URL avec différents snippets selon le
    contexte (page directe, dans une playlist, dans un album). On garde le
    snippet le plus informatif (= celui qui produit le meilleur score).
    """
    best_per_url: dict[str, dict[str, Any]] = {}
    for r in results:
        url = r["url"]
        if url not in best_per_url or r["score"] > best_per_url[url]["score"]:
            best_per_url[url] = r
    return list(best_per_url.values())


def _candidate_to_dict(c: dict[str, Any]) -> dict[str, Any]:
    """Convertit un candidat interne en dict JSON-compatible."""
    return {
        "url": c["url"],
        "score": c["score"],
        "region": c["region"],
        "result_title": c["title"],
        "result_description": c["body"],
        "markers_detected": sorted(c["markers_found"]),
    }


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------


def _run_per_platform(
    artist: str,
    title: str,
    plats: list[str],
    config: Config,
    *,
    early_exit: bool,
) -> dict[str, dict[str, Any]]:
    """Run ``_search_one_platform`` for each platform, optionally in parallel.

    Returns a ``{platform_name: result_dict}`` mapping. When
    ``config.parallel`` is True the platforms are searched concurrently
    via a thread pool (capped at ``config.max_workers``); otherwise they
    run sequentially in the requested order. The result is the same
    either way — only the wall-clock time changes.
    """
    if not config.parallel or len(plats) <= 1:
        return {
            plat: _search_one_platform(
                artist, title, plat, config, early_exit=early_exit
            )
            for plat in plats
        }

    workers = min(config.max_workers, len(plats))
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_to_plat = {
            pool.submit(
                _search_one_platform,
                artist,
                title,
                plat,
                config,
                early_exit=early_exit,
            ): plat
            for plat in plats
        }
        for future in future_to_plat:
            plat = future_to_plat[future]
            results[plat] = future.result()
    return results


def find_links(
    artist: str,
    title: str,
    platforms: list[str] | None = None,
    config: Config | None = None,
) -> dict[str, str]:
    """Renvoie un dict ``{platform: url}`` avec le meilleur lien trouvé.

    Les plateformes sans résultat n'apparaissent pas dans le dict renvoyé.

    Raises:
        ValueError: si ``artist`` ou ``title`` est vide, fait uniquement
            d'espaces, ou n'est pas une ``str``.
    """
    _validate_query(artist, title)
    cfg = config or get_default_config()
    plats = platforms or list(PLATFORMS.keys())

    per_plat = _run_per_platform(artist, title, plats, cfg, early_exit=True)

    out: dict[str, str] = {}
    # Iterate in the original ``plats`` order so the returned dict is stable
    # regardless of which thread finished first.
    for plat in plats:
        result = per_plat[plat]
        if result["selected"] is not None:
            out[plat] = result["selected"]["url"]
    return out


def find_data(
    artist: str,
    title: str,
    platforms: list[str] | None = None,
    config: Config | None = None,
) -> dict[str, Any]:
    """Renvoie un dict structuré avec tous les candidats par plateforme.

    Les candidats sont triés par score décroissant. Une liste vide signifie
    qu'aucun candidat n'a été trouvé pour la plateforme.

    Le dict renvoyé est directement sérialisable en JSON via ``json.dumps``.

    Raises:
        ValueError: si ``artist`` ou ``title`` est vide, fait uniquement
            d'espaces, ou n'est pas une ``str``.
    """
    _validate_query(artist, title)
    cfg = config or get_default_config()
    plats = platforms or list(PLATFORMS.keys())

    requested = markers_in(
        (artist + " " + title).lower(), cfg.version_markers
    )

    out: dict[str, Any] = {
        "artist": artist,
        "title": title,
        "requested_markers": sorted(requested),
        "platforms": {},
    }

    per_plat = _run_per_platform(artist, title, plats, cfg, early_exit=False)

    # Iterate in original platform order for output stability.
    for plat in plats:
        result = per_plat[plat]

        all_candidates: list[dict[str, Any]] = []
        if result["selected"] is not None:
            all_candidates.append(result["selected"])
        all_candidates.extend(result["candidates"])
        all_candidates.sort(key=lambda r: r["score"], reverse=True)

        out["platforms"][plat] = [_candidate_to_dict(c) for c in all_candidates]

    return out
