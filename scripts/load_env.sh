# Source this file to export Qualtrics API credentials from
# ~/.claude/secrets/qualtrics_tokens.env (Qualtrics REST API).
#
#   source ${CLAUDE_PLUGIN_ROOT}/scripts/load_env.sh  # default: 'qualtrics' (Stanford)
#   source ${CLAUDE_PLUGIN_ROOT}/scripts/load_env.sh  qualtrics-mit   # MIT
#
# Instance -> secrets prefix:
#   qualtrics      -> QUALTRICS_STANFORD_TOKEN / _DC / _BRAND
#   qualtrics-mit  -> QUALTRICS_MIT_TOKEN     / _DC / _BRAND
#
# Exports QUALTRICS_API_TOKEN, QUALTRICS_DATA_CENTER, QUALTRICS_BRAND,
# QUALTRICS_INSTANCE. Fails fast if the secrets file or required fields are
# missing. See the README "Setup" section for the secrets file.

_QUALTRICS_INSTANCE="${1:-qualtrics}"
_QSECRETS="$HOME/.claude/secrets/qualtrics_tokens.env"

case "$_QUALTRICS_INSTANCE" in
  qualtrics|stanford|qualtrics-stanford) _QPREFIX=QUALTRICS_STANFORD ;;
  qualtrics-mit|mit)                     _QPREFIX=QUALTRICS_MIT ;;
  *) echo "load_env.sh: unknown instance '$_QUALTRICS_INSTANCE' (expected 'qualtrics' or 'qualtrics-mit')" >&2
     return 1 2>/dev/null || exit 1 ;;
esac

if [ ! -f "$_QSECRETS" ]; then
  echo "load_env.sh: secrets file not found: $_QSECRETS (see the README "Setup" section)" >&2
  return 1 2>/dev/null || exit 1
fi

set -a; . "$_QSECRETS"; set +a

eval "export QUALTRICS_API_TOKEN=\"\${${_QPREFIX}_TOKEN:-}\""
eval "export QUALTRICS_DATA_CENTER=\"\${${_QPREFIX}_DC:-}\""
eval "export QUALTRICS_BRAND=\"\${${_QPREFIX}_BRAND:-}\""
export QUALTRICS_INSTANCE="$_QUALTRICS_INSTANCE"

if [ -z "$QUALTRICS_API_TOKEN" ] || [ -z "$QUALTRICS_DATA_CENTER" ]; then
  echo "load_env.sh: ${_QPREFIX}_TOKEN / ${_QPREFIX}_DC missing in $_QSECRETS" >&2
  return 1 2>/dev/null || exit 1
fi

unset _QUALTRICS_INSTANCE _QPREFIX _QSECRETS
