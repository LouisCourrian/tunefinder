"""tunefinder — find streaming links across multiple platforms.

Public API:

- :func:`find_links` — quick lookup, returns ``{platform: url}``.
- :func:`find_data` — full data with all candidates, JSON-serializable.
- :func:`print_search_debug` — human-readable debug output.
- :class:`Config` — tunable parameters (regions, markers, scoring weights).
"""

from __future__ import annotations

from ._config import Config, get_default_config
from ._debug import print_search_debug
from ._platforms import PLATFORMS
from ._search import find_data, find_links

__version__ = "0.3.0"

__all__ = [
    "Config",
    "PLATFORMS",
    "__version__",
    "find_data",
    "find_links",
    "get_default_config",
    "print_search_debug",
]
