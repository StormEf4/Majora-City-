#!/usr/bin/env bash
# One-time setup: fetch the pinned decompilation, install your ROM, extract assets and verify a vanilla build.
#
#   tools/setup.sh "/path/to/Majora's Mask (USA).z64"
#
# Needs the decomp's build dependencies (see README.md). Your ROM never leaves your machine and is never committed.

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

rom="${1:-}"
jobs="${JOBS:-$(nproc 2> /dev/null || echo 4)}"

ensure_decomp
reset_decomp

if [ -n "$rom" ]; then
    [ -f "$rom" ] || die "ROM not found: $rom"
    ext="${rom##*.}"
    ext="$(echo "$ext" | tr '[:upper:]' '[:lower:]')"
    case "$ext" in
        z64 | n64 | v64) ;;
        *) die "expected a .z64, .n64 or .v64 file, got .$ext" ;;
    esac
    mkdir -p "$DECOMP_DIR/baseroms/$MC_VERSION"
    cp "$rom" "$DECOMP_DIR/baseroms/$MC_VERSION/baserom.$ext"
    log "Installed ROM as baseroms/$MC_VERSION/baserom.$ext"
fi

find_baserom > /dev/null || die "no ROM installed; run: tools/setup.sh /path/to/your/MajorasMask-US.z64"

# Build vanilla first: this extracts assets and proves the ROM and toolchain are good before any mod code is involved.
log "Extracting and building vanilla (make init); this takes a while the first time"
make -C "$DECOMP_DIR" init -j"$jobs" VERSION="$MC_VERSION"

"$REPO_ROOT/tools/apply.sh"
log "Setup complete. Build Majora City with: tools/build.sh"
