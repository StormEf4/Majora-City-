#!/usr/bin/env bash
# Apply Majora City to the decomp checkout: reset it to the pinned commit, apply patches/, then copy mod/ over it.
#
#   tools/apply.sh           apply (idempotent; safe to run before every build)
#   tools/apply.sh --clean   restore the pristine decompilation
#
# The checkout is a managed workspace: edit mod/ and patches/ in this repo, never the files in build/mm.
# Extracted assets, the baserom and build output are untracked there and are left alone.

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

[ -d "$DECOMP_DIR/.git" ] || die "no decomp checkout at $DECOMP_DIR; run tools/setup.sh (or tools/check.sh) first"

reset_decomp

if [ "${1:-}" = "--clean" ]; then
    log "Decomp restored to pristine ${DECOMP_COMMIT:0:12}"
    exit 0
fi

shopt -s nullglob
patches=("$REPO_ROOT"/patches/*.patch)
for p in "${patches[@]}"; do
    git -C "$DECOMP_DIR" apply --whitespace=nowarn "$p" || die "patch $(basename "$p") does not apply to ${DECOMP_COMMIT:0:12}"
done

manifest="$DECOMP_DIR/$SYNC_MANIFEST"
: > "$manifest"
count=0
while IFS= read -r -d '' src; do
    rel="${src#"$REPO_ROOT/mod/"}"
    if git -C "$DECOMP_DIR" ls-files --error-unmatch -- "$rel" > /dev/null 2>&1; then
        die "mod/$rel would overwrite a decomp file; change it with a patch in patches/ instead"
    fi
    mkdir -p "$DECOMP_DIR/$(dirname "$rel")"
    cp "$src" "$DECOMP_DIR/$rel"
    echo "$rel" >> "$manifest"
    count=$((count + 1))
done < <(find "$REPO_ROOT/mod" -type f -print0 | sort -z)

log "Applied ${#patches[@]} patches and $count mod files to $DECOMP_DIR"
