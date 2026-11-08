"""demo/seed.sh produces a task for every color rule, in the sandbox only."""

import os
import re
import subprocess

import pytest
from conftest import REPO

import quantize


@pytest.fixture
def seeded(isolated_task_env):
    subprocess.run([REPO / "demo" / "seed.sh"], check=True, capture_output=True)
    return isolated_task_env


def count(sandbox, *filters: str) -> int:
    out = subprocess.run(
        ["task", "rc.verbose=nothing", *filters, "count"],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "TASKRC": str(sandbox / "taskrc")},
    )
    return int(out.stdout.strip())


def test_seed_stays_in_sandbox(seeded):
    assert (seeded / "data" / "pending.data").exists()
    assert (seeded / "taskrc").exists()


@pytest.mark.parametrize(
    "virtual_tag",
    [
        "+OVERDUE",
        "+DUETODAY",
        "+DUE",
        "+ACTIVE",
        "+BLOCKED",
        "+BLOCKING",
        "+SCHEDULED",
        "+WAITING",
        "+UNTIL",
        "+ANNOTATED",
        "+COMPLETED",
        "+DELETED",
        "+TAGGED",
    ],
)
def test_seed_covers_rule(seeded, virtual_tag):
    assert count(seeded, virtual_tag) >= 1


def test_seed_covers_priorities_and_recurrence(seeded):
    for p in "HML":
        assert count(seeded, f"priority:{p}") >= 1
    assert count(seeded, "+PENDING", "recur.any:") >= 1


@pytest.mark.parametrize("where", ["/", "HOME"])
def test_seed_refuses_unsafe_sandbox(isolated_task_env, monkeypatch, where):
    home = isolated_task_env / "home"
    (home / ".task").mkdir()
    sentinel = home / ".task" / "pending.data"
    sentinel.write_text("keep me\n")
    monkeypatch.setenv("TINTED_TASKWARRIOR_SANDBOX", "/" if where == "/" else str(home))
    r = subprocess.run(
        [REPO / "demo" / "seed.sh"], check=False, capture_output=True, text=True
    )
    assert r.returncode != 0
    assert "refusing" in r.stderr
    assert sentinel.read_text() == "keep me\n"
    assert not (home / "taskrc").exists()


def test_calendar_highlights_every_rule(seeded):
    """Due/overdue/due-today/scheduled/holiday days are colored in the grid.

    Taskwarrior marks task days only when calendar.details is not "none", and
    renders months only on a terminal, so run it under script(1) with a width.
    """
    theme = REPO / "taskwarrior" / "base16-solarized-dark.theme"
    (seeded / "current.theme").write_text(theme.read_text())
    # "color.calendar.due=gray3 on rgb320  # #002b36 on #b58900" -> 256 index
    bg_index = {}
    for line in theme.read_text().splitlines():
        key, _, value = line.partition("=")
        if key.startswith("color.calendar.") and " on #" in value:
            bg_hex = value.rsplit(" on #", 1)[1]
            bg_index[key.removeprefix("color.calendar.")] = quantize.nearest(bg_hex)[1]
    out = subprocess.run(
        ["script", "-qc", "stty cols 120 rows 50; task calendar", "/dev/null"],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "TASKRC": str(seeded / "taskrc")},
    ).stdout
    grid = "\n".join(line for line in out.splitlines() if "Legend" not in line)
    for rule in ("due", "overdue", "due.today", "scheduled", "holiday"):
        assert f"48;5;{bg_index[rule]}m" in grid, rule

    # Weekends are a foreground color, so a weekend day on a striped
    # (color.alternate) week row still differs from the weekdays around it.
    lines = theme.read_text().splitlines()

    def source_hex(key: str) -> str:
        line = next(x for x in lines if x.startswith(key + "="))
        return line.rsplit("#", 1)[1]

    fg = quantize.nearest(source_hex("color.calendar.weekend"))[1]
    alt = quantize.nearest(source_hex("color.alternate"))[1]
    # A 2-character day cell, not the 4-character week-number cell.
    cell = re.compile(rf"\x1b\[38;5;{fg}m\x1b\[48;5;{alt}m[ \d]\d\x1b")
    assert cell.search(grid), "no weekend day on a striped week row"
