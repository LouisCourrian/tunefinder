"""Affichage humain-lisible du détail d'une recherche.

Utile pour investiguer manuellement un cas où le résultat paraît bizarre.
"""

from __future__ import annotations

from ._config import Config, get_default_config
from ._platforms import PLATFORMS
from ._search import _search_one_platform


def print_search_debug(
    artist: str,
    title: str,
    platforms: list[str] | None = None,
    config: Config | None = None,
) -> None:
    """Affiche dans la console le détail des résultats de recherche.

    Pour chaque plateforme : le candidat sélectionné, son score, sa région,
    et la liste des autres candidats avec leurs flags (marqueurs non demandés,
    marqueurs manquants).
    """
    cfg = config or get_default_config()
    plats = platforms or list(PLATFORMS.keys())

    print(f"\n{'=' * 72}")
    print(f"  Recherche : {artist} — {title}")
    print(f"{'=' * 72}")

    for plat in plats:
        print(f"\n▶ {plat.upper()}")
        print("─" * 72)
        result = _search_one_platform(artist, title, plat, cfg, early_exit=False)

        requested = result["requested_markers"]
        if requested:
            print(f"  ⚙  Versions demandées : {', '.join(sorted(requested))}")
        else:
            print(
                "  ⚙  Aucune version particulière demandée → on évite les alternatives"
            )

        if not result["selected"]:
            print("\n  ✗ Aucun lien trouvé")
            continue

        sel = result["selected"]
        print(f"\n  ✓ SÉLECTIONNÉ  (score : {sel['score']}, région : {sel['region']})")
        print(f"     URL    : {sel['url']}")
        print(f"     titre  : {sel['title']}")
        print(f"     desc.  : {sel['body']}")
        if sel["markers_found"]:
            print(
                f"     versions détectées : {', '.join(sorted(sel['markers_found']))}"
            )

        if result["candidates"]:
            print(f"\n  ⋯ Autres candidats ({len(result['candidates'])}) :")
            for i, c in enumerate(result["candidates"], 1):
                flags = []
                if c["markers_unwanted"]:
                    flags.append(
                        f"non demandés : {', '.join(sorted(c['markers_unwanted']))}"
                    )
                if c["markers_missing"]:
                    flags.append(
                        f"manquants : {', '.join(sorted(c['markers_missing']))}"
                    )
                flag_str = "  |  ".join(flags) if flags else "—"
                print(f"     [{i}] score {c['score']}, région {c['region']}")
                print(f"         URL    : {c['url']}")
                print(f"         titre  : {c['title']}")
                print(f"         desc.  : {c['body']}")
                print(f"         flags  : {flag_str}")
        else:
            print("\n  ⋯ Aucun autre candidat")
