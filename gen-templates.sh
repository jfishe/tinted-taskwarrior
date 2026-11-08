#!/bin/sh
# Generate templates/*.mustache from src/taskwarrior.theme.in.
# Placeholders @ROLE@ expand to hex mustache variables per scheme system;
# quantize.py later turns each "hex:RRGGBB" into an xterm-256 color name.
set -eu
cd "$(dirname "$0")"

b16() { printf '{{%s-hex}}' "$1"; }
t8() { printf '{{%s.hex}}' "$1"; }

{
  printf '# tinted-taskwarrior\n# Scheme name: {{scheme-name}}\n# Scheme author: {{scheme-author}}\n# Scheme: {{scheme-system}}-{{scheme-slug}} ({{scheme-variant}})\n'
  sed \
    -e "s/@BG@/$(b16 base00)/g" \
    -e "s/@BG_ALT@/$(b16 base01)/g" \
    -e "s/@COMMENT@/$(b16 base03)/g" \
    -e "s/@RED@/$(b16 base08)/g" \
    -e "s/@ORANGE@/$(b16 base09)/g" \
    -e "s/@YELLOW@/$(b16 base0A)/g" \
    -e "s/@GREEN@/$(b16 base0B)/g" \
    -e "s/@CYAN@/$(b16 base0C)/g" \
    -e "s/@BLUE@/$(b16 base0D)/g" \
    -e "s/@MAGENTA@/$(b16 base0E)/g" \
    src/taskwarrior.theme.in
} > templates/base16.mustache

{
  printf '# tinted-taskwarrior\n# Scheme name: {{scheme.name}}\n# Scheme author: {{scheme.author}}\n# Scheme: {{scheme.system}}-{{scheme.slug}} ({{variant}})\n'
  sed \
    -e "s/@BG@/$(t8 ui.global.background.normal)/g" \
    -e "s/@BG_ALT@/$(t8 ui.highlight.line.background)/g" \
    -e "s/@COMMENT@/$(t8 palette.gray.normal)/g" \
    -e "s/@RED@/$(t8 palette.red.normal)/g" \
    -e "s/@ORANGE@/$(t8 palette.orange.normal)/g" \
    -e "s/@YELLOW@/$(t8 palette.yellow.normal)/g" \
    -e "s/@GREEN@/$(t8 palette.green.normal)/g" \
    -e "s/@CYAN@/$(t8 palette.cyan.normal)/g" \
    -e "s/@BLUE@/$(t8 palette.blue.normal)/g" \
    -e "s/@MAGENTA@/$(t8 palette.magenta.normal)/g" \
    src/taskwarrior.theme.in
} > templates/tinted8.mustache

if grep -n '@[A-Z_]*@' templates/*.mustache; then
  echo "unexpanded placeholder(s) above" >&2
  exit 1
fi
