# tinted-taskwarrior

Remote tinty template that themes [Taskwarrior](https://taskwarrior.org)
from the current tinty scheme (base16, base24, tinted8).

Each built file is a Taskwarrior color theme: an `include`-able rc fragment of
`color.*` settings covering the same rules as Taskwarrior's bundled
`solarized-dark-256.theme`. These are task states (active, blocked, blocking,
recurring, scheduled, completed, deleted), due/due today/overdue, priorities,
`+next`, alternate rows, headers and labels, and the calendar, burndown,
history, summary, sync and undo views.

Taskwarrior supports at most 256 colors, never truecolor. Each scheme color
is mapped to the nearest xterm-256 color (an `rgbRGB` cube entry or a
`grayN` ramp entry, by CIEDE2000), and the original hex is kept in a trailing
comment. Cube entries 16–21 are never used, because
[tinted-shell](https://github.com/tinted-theming/tinted-shell) redefines them.
The theme therefore doesn't depend on the terminal's palette. Subtle
background tints (alternate rows, weekends) are only as close as the
256-color palette allows.

## Tinted Configuration

Append to `~/.config/tinted-theming/tinty/config.toml`:

```toml
[[items]]
name = "tinted-taskwarrior"
path = "https://github.com/jfishe/tinted-taskwarrior"
themes-dir = "taskwarrior"
supported-systems = ["base16", "base24", "tinted8"]
hook = "python3 -I ~/.local/share/tinted-theming/tinty/repos/tinted-taskwarrior/quantize.py %f"
```

The hook is needed for schemes that aren't in the upstream tinted-theming
schemes repo, such as those from `[[schemes.extras]]` or `tinty generate-scheme`.
tinty has no prebuilt theme for those, so `tinty apply` renders the template
itself. That output still has raw `hex:RRGGBB` colors, which Taskwarrior rejects
("The color 'hex:002b36' is not recognized"). The hook converts them to
xterm-256 names. For upstream schemes the applied file is already converted, and
the hook leaves it unchanged.

tinty keeps the current theme at
`~/.local/share/tinted-theming/tinty/tinted-taskwarrior-taskwarrior-file.theme`.
Run `tinty install && tinty apply <scheme>` once, then include it from each
taskrc that should follow the scheme:

```ini
include ~/.local/share/tinted-theming/tinty/tinted-taskwarrior-taskwarrior-file.theme
```

Taskwarrior expands `~` and `$HOME` in `include` paths. A missing include file
is fatal ("Could not read include file"), so apply a scheme before adding the
line.

### Per-project task environments

Taskwarrior reads a single rc: `$TASKRC` when set, otherwise `~/.taskrc`.
A project that sets its own `TASKRC`/`TASKDATA`, for example through an `.env`
file, gets the theme only if its own rc has the `include` line. Its data is
never affected.

## Layout

- `src/taskwarrior.theme.in`: the theme, with `hex:@ROLE@` placeholders.
- `gen-templates.sh`: expands the roles into `templates/base16.mustache`
  (base16 and base24) and `templates/tinted8.mustache`.

  | role | base16 | tinted8 |
  | --- | --- | --- |
  | `BG` | base00 | ui.global.background.normal |
  | `BG_ALT` | base01 | ui.highlight.line.background |
  | `COMMENT` | base03 | palette.gray.normal |
  | `RED` `ORANGE` `YELLOW` `GREEN` | base08 09 0A 0B | palette.red/orange/yellow/green.normal |
  | `CYAN` `BLUE` `MAGENTA` | base0C 0D 0E | palette.cyan/blue/magenta.normal |

- `quantize.py`: rewrites each `hex:RRGGBB` in the built themes to the nearest
  xterm-256 color name. It uses only the standard library and is idempotent.
  `build.sh` runs it on `taskwarrior/`, and the tinty hook runs it on the
  applied theme.
- `taskwarrior/`: built output, one file per scheme. It's committed, and tinty
  reads it directly.
- `demo/`: an isolated Taskwarrior rc and database for previewing themes.
- `tests/`: pytest.

## Development

Requirements: tinty, Taskwarrior, [uv](https://docs.astral.sh/uv/).

```sh
./build.sh          # tinty sync + gen-templates.sh + tinty build + quantize.py
uv run pytest       # every theme loads in Taskwarrior; quantizer; demo data
uv run ruff check . && uv run ruff format --check . && uv run pyrefly check
```

`build.sh` builds against the upstream tinted-theming schemes plus the
`[[schemes.extras]]` in [`tinty.toml`](tinty.toml), such as
[tinted-colortemplate](https://github.com/jfishe/tinted-colortemplate)'s
solarized8. It uses that config and its own data dir (`.cache/tinty`), not
your personal tinty setup. It rebuilds `taskwarrior/` from scratch, so removed
schemes disappear. (`tinty build .` alone reads only the upstream schemes.)

The [update workflow](.github/workflows/update.yml) runs the same `build.sh`
with the same tinty release (pinned there; keep it in step with your local
tinty). It runs weekly and on template or build changes, so local and CI
builds produce the same files.

### Previewing themes

Nothing here reads or writes `~/.taskrc`, `~/.task`, or another project's
task database:

- `demo/lib.sh` points `TASKRC` at `demo/taskrc` and `TASKDATA` at
  `demo/data/`, overriding anything inherited, and refuses unsafe locations.
- The tests point `HOME`, `TASKRC` and `TASKDATA` into a temporary directory,
  and fail if the real rc or data files change.
- With [direnv](https://direnv.net), `direnv allow` once makes plain `task`
  inside the repo use the demo environment too (`.envrc`).

```sh
demo/seed.sh                                    # (re)build the demo database
demo/show.sh                                    # current tinty scheme, every colored view
demo/show.sh base16-solarized-dark              # a specific scheme
demo/show.sh tinted8-solarized8-light next calendar
demo/show.sh --compare base16-nord base16-gruvbox-light-medium next
demo/show.sh --all next                         # step through every scheme
```

The demo database is built with relative dates, so it always looks current.
It contains projects (Home, Garden, Work.Website, Work.Release), H/M/L
priorities, overdue, due-today and due-soon tasks, and scheduled, waiting and
`until` tasks. It also has an active task, blocked and blocking tasks, weekly
recurrences, annotations, `+next`/`+bug` tags, and five weeks of completed and
deleted tasks for the burndown, history and summary reports.

`demo/holidays.sh` writes `demo/holidays.rc` with US holidays for this year and
next. Taskwarrior 2.6's bundled `holidays.en-US.rc` stops at 2022.
`demo/taskrc` sets `calendar.details=sparse`, because Taskwarrior colors
due, overdue and scheduled days in `task calendar` only when details are on.

## License

MIT. See [LICENSE.txt](LICENSE.txt) and
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
