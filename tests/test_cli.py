"""Tests for the ``tunefinder`` command-line interface.

The CLI is a thin wrapper over the public API, so we test the wrapper
shape: argument parsing, output mode selection, JSON shape, and the
exit-code contract. The underlying search engine is mocked the same
way ``test_search.py`` mocks it.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from tunefinder import __main__ as cli


@pytest.fixture
def fake_ddgs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make DDGS return one canonical spotify hit for any matching query."""

    class FakeDDGS:
        def text(
            self, query: str, region: str = "", max_results: int = 10
        ) -> list[dict[str, str]]:
            if "site:open.spotify.com/track" in query:
                return [
                    {
                        "href": "https://open.spotify.com/track/X",
                        "title": "Balalaika - 9Lana",
                        "body": "9Lana single",
                    }
                ]
            return []

    monkeypatch.setattr("tunefinder._search.DDGS", FakeDDGS)


def test_default_prints_compact_json_dict(
    fake_ddgs: None, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = cli.main(
        ["9Lana", "Balalaika", "--platforms", "spotify", "--delay", "0"]
    )
    assert rc == 0
    out = capsys.readouterr().out
    data: dict[str, str] = json.loads(out)
    assert data == {"spotify": "https://open.spotify.com/track/X"}
    # Compact JSON: no newlines inside the object.
    assert "\n  " not in out


def test_data_flag_returns_full_structure(
    fake_ddgs: None, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = cli.main(
        ["9Lana", "Balalaika", "--platforms", "spotify", "--delay", "0", "--data"]
    )
    assert rc == 0
    data: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert data["artist"] == "9Lana"
    assert data["title"] == "Balalaika"
    assert "spotify" in data["platforms"]
    assert data["platforms"]["spotify"][0]["url"] == "https://open.spotify.com/track/X"


def test_pretty_flag_indents_json(
    fake_ddgs: None, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = cli.main(
        [
            "9Lana",
            "Balalaika",
            "--platforms",
            "spotify",
            "--delay",
            "0",
            "--pretty",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "\n  " in out  # indented lines


def test_debug_flag_emits_human_readable_trace(
    fake_ddgs: None, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = cli.main(
        [
            "9Lana",
            "Balalaika",
            "--platforms",
            "spotify",
            "--delay",
            "0",
            "--debug",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    # The trace contains the platform name in upper-case and the resolved URL.
    assert "SPOTIFY" in out
    assert "https://open.spotify.com/track/X" in out


def test_version_flag_prints_version_and_exits_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    # Output looks like "tunefinder X.Y.Z\n" — non-empty and contains a digit.
    assert "tunefinder" in out
    assert any(c.isdigit() for c in out)


def test_unknown_platform_is_rejected_by_argparse(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["9Lana", "Balalaika", "--platforms", "nonexistent"])
    # argparse uses exit code 2 for usage errors.
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "invalid choice" in err


def test_missing_positional_args_fails(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["9Lana"])  # missing TITLE
    assert exc.value.code == 2


def test_data_and_debug_are_mutually_exclusive(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["9Lana", "Balalaika", "--data", "--debug"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "not allowed with" in err or "mutually exclusive" in err


def test_empty_artist_prints_clean_error_no_traceback(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = cli.main(["", "Balalaika", "--platforms", "spotify", "--delay", "0"])
    assert rc == 2
    err = capsys.readouterr().err
    # No traceback should leak — just a single-line error message.
    assert "Traceback" not in err
    assert "must be a non-empty string" in err
    # Stdout stays clean too.
    assert capsys.readouterr().out == ""


def test_whitespace_title_prints_clean_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = cli.main(["Artist", "   ", "--platforms", "spotify", "--delay", "0"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert "must be a non-empty string" in err
