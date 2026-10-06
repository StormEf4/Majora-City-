#!/usr/bin/env bash
# Apply Majora City to the decomp checkout: reset it to the pinned commit, apply patches/, then copy mod/ over it.
# Only files whose content changes are written, so incremental builds stay fast.
#
#   tools/apply.sh           apply (idempotent; safe to run before every build)
#   tools/apply.sh --clean   restore the pristine decompilation
#
# The checkout is a managed workspace: edit mod/ and patches/ in this repo, never the files in the decomp checkout.
# Extracted assets, the ROM and build output are untracked there and are left alone.

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

[ -d "$DECOMP_DIR/.git" ] || die "no decomp checkout at $DECOMP_DIR; run ./majora-city build (or tools/check.sh) first"
python3 "$REPO_ROOT/tools/apply.py" --decomp "$DECOMP_DIR" --commit "$DECOMP_COMMIT" "$@"
