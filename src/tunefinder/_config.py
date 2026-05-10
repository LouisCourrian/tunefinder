"""Configuration de la recherche.

L'objet :class:`Config` regroupe tous les paramètres ajustables. Une instance
par défaut est utilisée si l'utilisateur n'en fournit pas explicitement.
"""

from __future__ import annotations

from dataclasses import dataclass

# Régions DuckDuckGo essayées dans l'ordre. ``wt-wt`` = worldwide (sans
# localisation), c'est le réflexe pour avoir une recherche neutre.
DEFAULT_REGIONS: tuple[str, ...] = ("wt-wt", "us-en", "uk-en", "fr-fr", "de-de")


# Marqueurs de "version alternative" (en anglais — couvre la grande majorité
# des cas, même pour des artistes francophones, parce que ces termes sont
# devenus quasi internationaux).
DEFAULT_VERSION_MARKERS: tuple[str, ...] = (
    "acoustic",
    "live",
    "remix",
    "remixed",
    "instrumental",
    "karaoke",
    "radio edit",
    "radio version",
    "radio mix",
    "extended mix",
    "extended version",
    "demo",
    "demo version",
    "remastered",
    "remaster",
    "cover",
    "unplugged",
    "stripped",
    "stripped down",
    "orchestral",
    "piano version",
    "slowed",
    "slowed down",
    "sped up",
    "reverb",
    "8d audio",
    "alternate version",
    "alternate take",
    "single version",
    "album version",
    "rework",
    "reworked",
    "mashup",
    "bootleg",
    "vip mix",
    # "ver" : abréviation typique des sorties asiatiques ("ver. Artist X",
    # "Acoustic Ver."). Le mot "version" complet n'est PAS inclus pour
    # éviter les doubles pénalités sur les requêtes du type "Title Acoustic".
    "ver",
)


@dataclass
class Config:
    """Paramètres de recherche.

    Args:
        regions: Liste des régions DuckDuckGo à interroger, dans l'ordre.
            La première à remonter un score parfait court-circuite les autres.
        delay_between_queries: Pause en secondes entre deux requêtes DDGS.
            Trop bas → risque de blocage. Trop haut → script lent.
        max_results_per_query: Nombre maximum de résultats demandés à DDGS
            par requête.
        version_markers: Mots qui signalent une version alternative.
        score_both_match: Bonus quand artiste ET titre sont dans la description.
        score_one_match: Bonus quand seulement l'un des deux l'est.
        score_marker_unwanted: Pénalité pour un marqueur trouvé mais non demandé.
        score_marker_matched: Bonus pour un marqueur trouvé ET demandé.
        score_marker_missing: Pénalité pour un marqueur demandé mais absent.
        max_retries: Nombre de tentatives supplémentaires sur une erreur DDGS
            transitoire (rate-limit, timeout). 0 = aucun retry.
        initial_backoff_seconds: Pause avant le premier retry. Doublée à
            chaque tentative suivante (cf. ``backoff_multiplier``).
        backoff_multiplier: Facteur d'augmentation du délai entre retries.
        parallel: Si True, ``find_links`` et ``find_data`` interrogent les
            plateformes en parallèle (``ThreadPoolExecutor``).
        max_workers: Nombre maximum de threads pour la recherche parallèle.
    """

    regions: tuple[str, ...] = DEFAULT_REGIONS
    delay_between_queries: float = 0.3
    max_results_per_query: int = 10

    version_markers: tuple[str, ...] = DEFAULT_VERSION_MARKERS

    score_both_match: int = 100
    score_one_match: int = 40
    score_marker_unwanted: int = -50
    score_marker_matched: int = 30
    score_marker_missing: int = -30

    max_retries: int = 2
    initial_backoff_seconds: float = 1.0
    backoff_multiplier: float = 2.0

    parallel: bool = True
    max_workers: int = 6


# Instance partagée utilisée quand l'utilisateur ne passe pas de Config.
_DEFAULT_CONFIG = Config()


def get_default_config() -> Config:
    """Renvoie l'instance Config utilisée par défaut.

    Modifier l'objet renvoyé affecte les appels qui n'ont pas de Config explicite.
    Pour une configuration isolée, créer une nouvelle instance ``Config(...)``.
    """
    return _DEFAULT_CONFIG
