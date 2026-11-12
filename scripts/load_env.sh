# Source this file to export Qualtrics API credentials for one account from
# ~/.claude/secrets/qualtrics_tokens.env (Qualtrics REST API).
#
#   source ${CLAUDE_PLUGIN_ROOT}/scripts/load_env.sh <account>
#
# <account> names a block in the secrets file: `mit` reads QUALTRICS_MIT_TOKEN,
# QUALTRICS_MIT_DC and QUALTRICS_MIT_BRAND. A leading `qualtrics-` is ignored
# (`qualtrics-mit` = `mit`), and plain `qualtrics` means `stanford`, so older
# instance names keep working.
#
# Exports QUALTRICS_API_TOKEN, QUALTRICS_DATA_CENTER, QUALTRICS_BRAND,
# QUALTRICS_INSTANCE. Fails fast if the account, the secrets file or a field is
# missing. See the README "Setup" section for the secrets file.

_QUALTRICS_INSTANCE="${1:-}"
_QSECRETS="$HOME/.claude/secrets/qualtrics_tokens.env"

if [ -z "$_QUALTRICS_INSTANCE" ]; then
  echo "load_env.sh: name the account, e.g. 'source load_env.sh mit' (see the README \"Setup\" section)" >&2
  return 1 2>/dev/null || exit 1
fi
_QNAME="${_QUALTRICS_INSTANCE#qualtrics-}"
[ "$_QNAME" = "qualtrics" ] && _QNAME=stanford
_QPREFIX="QUALTRICS_$(printf '%s' "$_QNAME" | tr '[:lower:]-' '[:upper:]_')"

if [ ! -f "$_QSECRETS" ]; then
  echo "load_env.sh: secrets file not found: $_QSECRETS (see the README \"Setup\" section)" >&2
  return 1 2>/dev/null || exit 1
fi

set -a; . "$_QSECRETS"; set +a

eval "export QUALTRICS_API_TOKEN=\"\${${_QPREFIX}_TOKEN:-}\""
eval "export QUALTRICS_DATA_CENTER=\"\${${_QPREFIX}_DC:-}\""
eval "export QUALTRICS_BRAND=\"\${${_QPREFIX}_BRAND:-}\""
export QUALTRICS_INSTANCE="$_QUALTRICS_INSTANCE"

if [ -z "$QUALTRICS_API_TOKEN" ] || [ -z "$QUALTRICS_DATA_CENTER" ] || [ -z "$QUALTRICS_BRAND" ]; then
  echo "load_env.sh: ${_QPREFIX}_TOKEN / ${_QPREFIX}_DC / ${_QPREFIX}_BRAND missing in $_QSECRETS" >&2
  return 1 2>/dev/null || exit 1
fi

unset _QUALTRICS_INSTANCE _QNAME _QPREFIX _QSECRETS
