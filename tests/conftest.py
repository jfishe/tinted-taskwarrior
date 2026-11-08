"""Keep every test away from the user's real Taskwarrior configuration."""

import os
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
REAL_HOME = Path.home()


def _real_task_files() -> dict[Path, float]:
    """mtimes of the real task rc/data that tests must never touch."""
    candidates = [
        REAL_HOME / ".taskrc",
        REAL_HOME / ".config" / "task" / "taskrc",
        *(REAL_HOME / ".task").glob("*.data"),
    ]
    for var in ("TASKRC", "TASKDATA"):
        if value := os.environ.get(var):
            p = Path(value)
            candidates += [p] if p.is_file() else list(p.glob("*.data"))
    return {p: p.stat().st_mtime for p in candidates if p.exists()}


@pytest.fixture(autouse=True)
def isolated_task_env(tmp_path, monkeypatch):
    """Point HOME, TASKRC and TASKDATA into tmp_path for the test."""
    before = _real_task_files()
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("TASKRC", str(tmp_path / "taskrc"))
    monkeypatch.setenv("TASKDATA", str(tmp_path / "data"))
    monkeypatch.setenv("TINTED_TASKWARRIOR_SANDBOX", str(tmp_path))
    (tmp_path / "taskrc").write_text("news.version=2.6.0\n")
    yield tmp_path
    after = {p: p.stat().st_mtime for p in before if p.exists()}
    assert after == before, "a test modified the real task configuration"
