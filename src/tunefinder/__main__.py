"""Command-line interface for tunefinder.

Run as ``python -m tunefinder ...`` or, after install, as ``tunefinder ...``.

The CLI is intentionally thin: it parses arguments, builds an optional
``Config`` from the tuning flags, then delegates to the same public API
the library exposes (``find_links``, ``find_data``, ``print_search_debug``).
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from ._config import Config, get_default_config
from ._debug import print_search_debug
from ._platforms import PLATFORMS
from ._search import find_data, find_links


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tunefinder",
        description=(
            "Find streaming links for a track across multiple platforms. "
            "Prints a JSON object on stdout by default."
        ),
    )
    parser.add_argument("artist", metavar="ARTIST", help="artist name")
    parser.add_argument("title", metavar="TITLE", help="track title")
    parser.add_argument(
        "--platforms",
        nargs="+",
        metavar="PLATFORM",
        choices=sorted(PLATFORMS.keys()),
        help="restrict search to the given platform keys (default: all supported)",
    )
    parser.add_argument(
        "--regions",
        nargs="+",
        metavar="REGION",
        help="override DuckDuckGo regions (e.g. fr-fr us-en wt-wt)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        metavar="SECONDS",
        help="pause between DDGS queries (default: 0.3)",
    )
    output_mode = parser.add_mutually_exclusive_group()
    output_mode.add_argument(
        "--data",
        action="store_true",
        help="print the full find_data output (all candidates with scores) as JSON",
    )
    output_mode.add_argument(
        "--debug",
        action="store_true",
        help="print the human-readable search trace instead of JSON",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="indent JSON output (auto-enabled when stdout is a TTY)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def _build_config(args: argparse.Namespace) -> Config | None:
    """Return a tuned ``Config`` if any tuning flag was set, else ``None``.

    Returning ``None`` lets the public API fall back to the package-level
    default config, which keeps the test suite's mocking points intact.
    """
    if args.regions is None and args.delay is None:
        return None
    base = get_default_config()
    return Config(
        regions=tuple(args.regions) if args.regions is not None else base.regions,
        delay_between_queries=(
            args.delay if args.delay is not None else base.delay_between_queries
        ),
        max_results_per_query=base.max_results_per_query,
        version_markers=base.version_markers,
        score_both_match=base.score_both_match,
        score_one_match=base.score_one_match,
        score_marker_unwanted=base.score_marker_unwanted,
        score_marker_matched=base.score_marker_matched,
        score_marker_missing=base.score_marker_missing,
    )


def main(argv: list[str] | None = None) -> int:
    # On Windows the default console codepage is cp1252, which cannot encode
    # characters outside Latin-1 (CJK, emoji, "→", …) that routinely appear
    # in DuckDuckGo result snippets. Reconfigure stdout to UTF-8 so JSON
    # output and the debug trace never crash on a Unicode track title.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = _build_parser()
    args = parser.parse_args(argv)
    config = _build_config(args)

    if args.debug:
        print_search_debug(
            args.artist, args.title, platforms=args.platforms, config=config
        )
        return 0

    if args.data:
        result: object = find_data(
            args.artist, args.title, platforms=args.platforms, config=config
        )
    else:
        result = find_links(
            args.artist, args.title, platforms=args.platforms, config=config
        )

    pretty = args.pretty or sys.stdout.isatty()
    indent = 2 if pretty else None
    print(json.dumps(result, indent=indent, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
