#!/usr/bin/env bash
set -euo pipefail

main() {
  if [[ $# -gt 0 ]]; then
    if [[ $# -eq 1 && ( "$1" == "--help" || "$1" == "-h" ) ]]; then
      echo 'Usage: bash get.sh'
      echo 'Installs JustCast from GitHub using Codex CLI. Requires codex and git on PATH.'
      return 0
    fi
    echo 'Usage: bash get.sh [--help]' >&2
    return 1
  fi

  if ! command -v codex >/dev/null 2>&1; then
    echo 'Codex CLI is required. Install it, then run this command again:' >&2
    echo 'https://learn.chatgpt.com/docs/cli' >&2
    return 1
  fi
  if ! command -v git >/dev/null 2>&1; then
    echo 'Git is required. Install Git, then run this command again.' >&2
    return 1
  fi
  if ! codex plugin marketplace add --help >/dev/null 2>&1 ||
     ! codex plugin add --help >/dev/null 2>&1; then
    echo 'This Codex CLI does not support plugin installation. Update Codex CLI, then try again.' >&2
    return 1
  fi

  # Avoid a marketplace in the caller's project shadowing the GitHub source.
  justcast_install_dir="$(mktemp -d "${TMPDIR:-/tmp}/justcast-install.XXXXXXXX")"
  trap 'rmdir "$justcast_install_dir"' EXIT
  cd "$justcast_install_dir"

  echo 'Adding the JustCast marketplace from GitHub...'
  codex plugin marketplace add https://github.com/montekaka/justcast-skills.git --ref main
  echo 'Installing JustCast...'
  codex plugin add justcast@justcast

  echo 'JustCast is installed. Restart your desktop app and start a new chat.'
  echo 'Send this message to set up Volume Control:'
  echo '$justcast:volume-control init'
}

# Keep execution at the end so a truncated download cannot run a partial function.
main "$@"
