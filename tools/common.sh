# Shared helpers for the Majora City tools. Source this file; don't run it.
#
#   MC_DECOMP_DIR   where the decompilation checkout lives (default: build/mm inside this repo)
#   MC_VERSION      decomp version to build (default: n64-us; it is the only one Majora City supports)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../decomp.lock
source "$REPO_ROOT/decomp.lock"

DECOMP_DIR="${MC_DECOMP_DIR:-$REPO_ROOT/build/mm}"
MC_VERSION="${MC_VERSION:-n64-us}"
SYNC_MANIFEST=".mc_synced_files"

log() { printf '\033[1;35m[majora-city]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[majora-city] error:\033[0m %s\n' "$*" >&2; exit 1; }

# Clone (or fetch) the decompilation at the pinned commit. Never touches extracted/ or build/ contents.
ensure_decomp() {
    if [ ! -d "$DECOMP_DIR/.git" ]; then
        log "Creating decomp checkout in $DECOMP_DIR"
        mkdir -p "$DECOMP_DIR"
        git -C "$DECOMP_DIR" init -q
        git -C "$DECOMP_DIR" remote add origin "$DECOMP_REPO"
    fi
    if ! git -C "$DECOMP_DIR" cat-file -e "${DECOMP_COMMIT}^{commit}" 2>/dev/null; then
        log "Fetching zeldaret/mm @ ${DECOMP_COMMIT:0:12}"
        git -C "$DECOMP_DIR" fetch -q --depth 1 origin "$DECOMP_COMMIT"
    fi
}

# Restore the decomp's tracked files to the pinned commit and remove files synced from mod/ last time.
reset_decomp() {
    if [ -f "$DECOMP_DIR/$SYNC_MANIFEST" ]; then
        while IFS= read -r f; do
            rm -f "$DECOMP_DIR/$f"
        done < "$DECOMP_DIR/$SYNC_MANIFEST"
        rm -f "$DECOMP_DIR/$SYNC_MANIFEST"
    fi
    git -C "$DECOMP_DIR" checkout -q --force --detach "$DECOMP_COMMIT"
}

find_baserom() {
    local dir="$DECOMP_DIR/baseroms/$MC_VERSION" ext
    for ext in z64 n64 v64; do
        if [ -f "$dir/baserom.$ext" ]; then
            echo "$dir/baserom.$ext"
            return 0
        fi
    done
    return 1
}
