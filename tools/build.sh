#!/usr/bin/env bash
# Build the Majora City ROM and its distributable BPS patch.
#
#   tools/build.sh [extra make arguments]
#
# Output:
#   build/mm/build/n64-us/mm-n64-us-compressed.z64   the playable ROM (keep it to yourself)
#   dist/majora-city.bps                              the patch to share

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

jobs="${JOBS:-$(nproc 2> /dev/null || echo 4)}"
baserom="$(find_baserom)" || die "no ROM installed; run tools/setup.sh first"
[ -d "$DECOMP_DIR/extracted/$MC_VERSION" ] || die "assets not extracted; run tools/setup.sh first"

python3 "$REPO_ROOT/tools/gen_skyline.py" --check || die "regenerate the skyline: python3 tools/gen_skyline.py"
"$REPO_ROOT/tools/apply.sh"

log "Building ROM"
make -C "$DECOMP_DIR" -j"$jobs" VERSION="$MC_VERSION" COMPARE=0 rom compress "$@"

rom="$DECOMP_DIR/build/$MC_VERSION/mm-$MC_VERSION-compressed.z64"
[ -f "$rom" ] || die "build did not produce $rom"

mkdir -p "$REPO_ROOT/dist"
python3 "$REPO_ROOT/tools/bps.py" create "$baserom" "$rom" "$REPO_ROOT/dist/majora-city.bps"
log "ROM:   $rom"
log "Patch: dist/majora-city.bps"
