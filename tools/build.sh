#!/usr/bin/env bash
# Superseded by ./majora-city build, which runs the one-time setup automatically.
exec "$(dirname "${BASH_SOURCE[0]}")/../majora-city" build "$@"
