"""Every built theme must load cleanly in Taskwarrior."""

import os
import re
import subprocess

import pytest
from conftest import REPO

import quantize

THEMES = sorted((REPO / "taskwarrior").glob("*.theme"))


def test_themes_built():
    assert len(THEMES) > 100


def task(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["task", *args],
        capture_output=True,
        text=True,
        env=os.environ,
        check=False,
    )


@pytest.mark.parametrize("theme", THEMES, ids=lambda p: p.stem)
def test_theme_loads(theme, isolated_task_env):
    text = theme.read_text()
    assert "hex:" not in text and "{{" not in text

    rc = isolated_task_env / "taskrc"
    rc.write_text(f"include {theme}\nnews.version=2.6.0\n")

    legend = task("rc._forcecolor=on", "color", "legend")
    assert legend.returncode == 0, legend.stderr
    assert "not recognized" not in legend.stderr

    show = task("show")
    assert show.returncode == 0, show.stderr
    assert "unrecognized variables" not in show.stdout, show.stdout


def _settings(theme) -> dict[str, str]:
    out = {}
    for line in theme.read_text().splitlines():
        if line.startswith("color.") and "=" in line:
            key, _, value = line.partition("=")
            out[key] = value.split("#")[0].strip()
    return out


@pytest.mark.parametrize("theme", THEMES, ids=lambda p: p.stem)
def test_weekend_visible_on_alternate_rows(theme):
    """task calendar stripes alternate weeks with color.alternate; a weekend
    background equal to it would make weekends vanish on those rows."""
    s = _settings(theme)
    weekend_bg = s["color.calendar.weekend"].partition("on ")[2].strip()
    alternate_bg = s["color.alternate"].partition("on ")[2].strip()
    assert s["color.calendar.weekend"], "weekend has no color"
    assert weekend_bg != alternate_bg or not weekend_bg


def test_apply_time_render_loads_after_hook(isolated_task_env):
    """tinty renders the template itself for extras/generated schemes, so the
    applied file has raw hex: tokens until the quantize.py hook runs on it."""
    source = (REPO / "src" / "taskwarrior.theme.in").read_text()
    theme = isolated_task_env / "tinted-taskwarrior-taskwarrior-file.theme"
    theme.write_text(re.sub(r"@[A-Z_]+@", "586e75", source))

    assert quantize.main([str(theme)]) == 0
    text = theme.read_text()
    assert "hex:" not in text

    (isolated_task_env / "taskrc").write_text(f"include {theme}\nnews.version=2.6.0\n")
    legend = task("rc._forcecolor=on", "color", "legend")
    assert legend.returncode == 0, legend.stderr
    assert "not recognized" not in legend.stderr
