# shellcheck shell=sh
# Sourced by the demo scripts. Points Taskwarrior at an isolated rc and
# database, ignoring any TASKRC/TASKDATA inherited from the caller (e.g. a
# per-project .env), and refuses to run anywhere near the real ones.
#
# TINTED_TASKWARRIOR_SANDBOX=DIR (used by the tests) puts the rc, theme and
# data under DIR instead of demo/.

REPO=$(CDPATH="" cd -- "$(dirname -- "$0")/.." && pwd)
DEMO="$REPO/demo"

if [ -n "${TINTED_TASKWARRIOR_SANDBOX:-}" ]; then
  SANDBOX=$(CDPATH="" cd -- "$TINTED_TASKWARRIOR_SANDBOX" && pwd)
else
  SANDBOX=$DEMO
fi
TASKRC="$SANDBOX/taskrc"
TASKDATA="$SANDBOX/data"
THEME="$SANDBOX/current.theme"
export TASKRC TASKDATA

# Checked before anything is written. seed.sh deletes $TASKDATA.
home=$(CDPATH="" cd -- "$HOME" 2>/dev/null && pwd || printf '%s' "$HOME")
case "$SANDBOX" in
  / | "$home" | "$home/.task" | "$home/.config" | "$home/.config/task")
    echo "refusing: unsafe sandbox $SANDBOX" >&2
    exit 1
    ;;
esac
if [ -e "$TASKDATA" ] && [ ! -d "$TASKDATA" ]; then
  echo "refusing: $TASKDATA is not a directory" >&2
  exit 1
fi

[ "$SANDBOX" = "$DEMO" ] || cp -f "$DEMO/taskrc" "$TASKRC"
mkdir -p "$TASKDATA"
# taskrc includes current.theme and holidays.rc; a missing include is fatal.
[ -e "$THEME" ] || : > "$THEME"
"$DEMO/holidays.sh" "$SANDBOX/holidays.rc"
