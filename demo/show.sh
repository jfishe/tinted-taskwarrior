#!/bin/sh
# Preview a tinted-taskwarrior theme against the demo database.
#
# Usage:
#   demo/show.sh [SCHEME|FILE] [REPORT ...]
#   demo/show.sh --all [REPORT ...]
#   demo/show.sh --compare SCHEME SCHEME [REPORT ...]
#
# SCHEME is a built theme name such as base16-solarized-dark (default: the
# current tinty scheme); FILE is a path to any .theme file. REPORTs default to
# a tour of every colored view. Never touches ~/.taskrc or ~/.task; see
# demo/lib.sh.
set -eu
# shellcheck source=demo/lib.sh
. "$(dirname -- "$0")/lib.sh"

DEFAULT_REPORTS="next list projects summary calendar burndown.daily history ghistory.monthly color legend"

resolve() {
  if [ -f "$1" ]; then
    printf '%s\n' "$1"
  elif [ -f "$REPO/taskwarrior/$1.theme" ]; then
    printf '%s\n' "$REPO/taskwarrior/$1.theme"
  else
    echo "no such theme: $1" >&2
    exit 1
  fi
}

show() {
  theme=$(resolve "$1")
  shift
  cp -f "$theme" "$THEME" # THEME is set by lib.sh
  [ -s "$TASKDATA/pending.data" ] || "$REPO/demo/seed.sh" >/dev/null
  # shellcheck disable=SC2086 # split the default report list into words
  [ $# -gt 0 ] || set -- $DEFAULT_REPORTS
  printf '\n\033[1m=== %s ===\033[0m\n' "$(basename "$theme" .theme)"
  # "color legend" is one command; everything else is one report per word.
  while [ $# -gt 0 ]; do
    if [ "$1" = color ] && [ "${2:-}" = legend ]; then
      printf '\n--- task color legend ---\n'
      task rc._forcecolor=on color legend || true
      shift 2
      continue
    fi
    printf '\n--- task %s ---\n' "$1"
    task rc._forcecolor=on rc.defaultwidth="${COLUMNS:-120}" "$1" || true
    shift
  done
}

case "${1:-}" in
  --all)
    shift
    [ $# -gt 0 ] || set -- next
    for f in "$REPO"/taskwarrior/*.theme; do
      show "$f" "$@"
      printf '\n[Enter: next scheme, q: quit] '
      read -r answer </dev/tty || break
      [ "$answer" = q ] && break
    done
    ;;
  --compare)
    shift
    a=$1 b=$2
    shift 2
    show "$a" "$@"
    show "$b" "$@"
    ;;
  "")
    current=$(tinty current 2>/dev/null || true)
    [ -n "$current" ] || { echo "no scheme given and tinty current failed" >&2; exit 1; }
    show "$current"
    ;;
  -h | --help | -*)
    sed -n '2,12s/^# \{0,1\}//p' "$0"
    [ "$1" = -h ] || [ "$1" = --help ]
    ;;
  *)
    show "$@"
    ;;
esac
