#!/usr/bin/env bash
# End-to-end test of the user-facing build flow (./majora-city), without a real ROM.
#
# A fake ROM (accepted via MC_TEST_ACCEPT_MD5) and a stand-in for `make` (which "builds" a ROM derived from the
# Majora City files present in the decomp checkout) exercise everything around the real compiler: ROM checks,
# first-time setup, incremental rebuilds, versioned output, the share zip, `update`, `patch` and `info`.
#
#   tools/test_cli.sh
#
# Set MC_DECOMP_REPO to a local zeldaret/mm clone to avoid the network.

set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

pass() { printf '  \033[1;32mPASS\033[0m %s\n' "$*"; }
die() { printf '  \033[1;31mFAIL\033[0m %s\n' "$*" >&2; exit 1; }
expect_fail() { # expect_fail "needle" cmd...
    local needle="$1" out status=0
    shift
    out="$("$@" 2>&1)" || status=$?
    [ "$status" -ne 0 ] || die "expected failure: $*"
    grep -qF "$needle" <<< "$out" || { echo "$out"; die "expected message '$needle'"; }
}

# --- a git "origin" holding a copy of this repo (including uncommitted work), and a user clone of it ------------------
mkdir -p "$WORK/seed"
(cd "$SRC" && git ls-files -co --exclude-standard -z | xargs -0 -I{} cp --parents {} "$WORK/seed/")
git -C "$WORK/seed" init -q -b main
git -C "$WORK/seed" -c user.name=t -c user.email=t@t add -A
git -C "$WORK/seed" -c user.name=t -c user.email=t@t commit -qm seed
git clone -q --bare "$WORK/seed" "$WORK/origin.git"
git clone -q "$WORK/origin.git" "$WORK/user"
U="$WORK/user"

# --- fake make ---------------------------------------------------------------------------------------------------------
cat > "$WORK/fake-make" << 'EOF'
#!/usr/bin/env bash
# Stand-in for the decomp's make: records goals; "init" extracts, "rom" builds a ROM from the synced mod files.
dir=.
goals=()
while [ $# -gt 0 ]; do
    case "$1" in
        -C) dir="$2"; shift ;;
        -j*|*=*) ;;
        *) goals+=("$1") ;;
    esac
    shift
done
cd "$dir"
echo "${goals[*]}" >> "$FAKE_MAKE_LOG"
case " ${goals[*]} " in
    *" init "*)
        [ -f baseroms/n64-us/baserom.z64 ] || { echo "no baserom" >&2; exit 1; }
        mkdir -p extracted/n64-us build/n64-us ;;
    *" rom "*)
        [ -d extracted/n64-us ] || { echo "not set up" >&2; exit 1; }
        grep -q McSaveData include/z64save.h || { echo "patches not applied" >&2; exit 1; }
        mkdir -p build/n64-us
        { head -c 4096 baseroms/n64-us/baserom.z64; cat src/overlays/actors/ovl_Mc_Intro/z_mc_intro.c;
          tail -c +4097 baseroms/n64-us/baserom.z64; } > build/n64-us/mm-n64-us-compressed.z64 ;;
esac
EOF
chmod +x "$WORK/fake-make"

# --- fake ROMs ---------------------------------------------------------------------------------------------------------
python3 - "$WORK" << 'EOF'
import hashlib, os, sys, zipfile
work = sys.argv[1]
def rom(code, seed):
    h = bytearray(os.urandom(0)) + bytearray(64 * 1024)
    h[0:4] = b"\x80\x37\x12\x40"
    h[0x20:0x33] = b"ZELDA MAJORA'S MASK"
    h[0x3B:0x3F] = code
    for i in range(0x1000, len(h)):
        h[i] = (i * seed) & 0xFF
    return bytes(h)
good = rom(b"NZSE", 7)
v64 = bytearray(good); v64[0::2], v64[1::2] = good[1::2], good[0::2]
with zipfile.ZipFile(os.path.join(work, "good.zip"), "w") as z:
    z.writestr("Majora's Mask (USA).v64", bytes(v64))
open(os.path.join(work, "good.z64"), "wb").write(good)
open(os.path.join(work, "jp.z64"), "wb").write(rom(b"NZSJ", 7))
open(os.path.join(work, "good.md5"), "w").write(hashlib.md5(good).hexdigest())
EOF

export MC_MAKE="$WORK/fake-make" FAKE_MAKE_LOG="$WORK/make.log" MC_SKIP_DOCTOR=1 NO_COLOR=1
export MC_TEST_ACCEPT_MD5="$(cat "$WORK/good.md5")" MC_DECOMP_DIR="$WORK/mm"
: > "$FAKE_MAKE_LOG"
cd "$U"

echo "majora-city end-to-end test"

./majora-city version | grep -q "Majora City v0.1.0" || die "version"
pass "version"

expect_fail "No ROM found" ./majora-city build < /dev/null
pass "no ROM: clear instructions"

cp "$WORK/jp.z64" rom/
expect_fail "Japanese version" ./majora-city build < /dev/null
rm rom/jp.z64
pass "wrong region is explained"

cp "$WORK/good.zip" rom/
./majora-city build < /dev/null > "$WORK/out1.txt" 2>&1 || { cat "$WORK/out1.txt"; die "first build"; }
grep -q "Setup complete" "$WORK/out1.txt" || die "first build should run setup"
[ "$(cat "$FAKE_MAKE_LOG")" = $'init\nrom compress' ] || die "unexpected make calls: $(cat "$FAKE_MAKE_LOG")"
for f in MajoraCity-v0.1.0.bps MajoraCity-v0.1.0.zip MajoraCity-v0.1.0.z64; do
    [ -f "dist/$f" ] || die "missing dist/$f"
done
pass "first build (from a .v64 inside a .zip in rom/): setup + build + bps + zip + playable ROM"

python3 tools/bps.py apply "$WORK/good.z64" dist/MajoraCity-v0.1.0.bps "$WORK/patched.z64" > /dev/null
cmp -s "$WORK/patched.z64" dist/MajoraCity-v0.1.0.z64 || die "patch doesn't reproduce the built ROM"
pass "the .bps turns the original ROM into exactly the built ROM"

./majora-city info dist/MajoraCity-v0.1.0.bps | grep -q "Majora City v0.1.0" || die "info metadata"
python3 -c "import zipfile,sys; n=sorted(zipfile.ZipFile(sys.argv[1]).namelist()); sys.exit(n!=['CHANGELOG.txt','HOW-TO-PLAY.txt','MajoraCity-v0.1.0.bps'])" dist/MajoraCity-v0.1.0.zip ||
    die "share zip contents"
pass "patch metadata and share zip"

stamp_before="$(stat -c %Y "$MC_DECOMP_DIR/include/z64save.h")"
rm rom/good.zip # later builds must not need the ROM again
./majora-city build < /dev/null > "$WORK/out2.txt" 2>&1 || { cat "$WORK/out2.txt"; die "second build"; }
grep -q "Already done" "$WORK/out2.txt" || die "second build should skip setup"
[ "$(cat "$FAKE_MAKE_LOG")" = $'init\nrom compress\nrom compress' ] || die "rebuild ran setup again: $(cat "$FAKE_MAKE_LOG")"
[ "$(stat -c %Y "$MC_DECOMP_DIR/include/z64save.h")" = "$stamp_before" ] || die "rebuild touched unchanged files"
pass "rebuild: no ROM needed, setup skipped, unchanged files untouched (fast incremental)"

echo "// local tweak" >> mod/src/overlays/actors/ovl_Mc_Intro/z_mc_intro.c
./majora-city build < /dev/null > /dev/null 2>&1 || die "build with local changes"
[ -f dist/MajoraCity-v0.1.0-modified.bps ] || die "uncommitted changes should be labelled -modified"
git checkout -q mod/src/overlays/actors/ovl_Mc_Intro/z_mc_intro.c
pass "builds with uncommitted changes are labelled -modified"

# A new release lands upstream: VERSION bump + a code change.
git clone -q "$WORK/origin.git" "$WORK/dev"
echo "0.1.1" > "$WORK/dev/VERSION"
echo "// v0.1.1" >> "$WORK/dev/mod/src/overlays/actors/ovl_Mc_Intro/z_mc_intro.c"
git -C "$WORK/dev" -c user.name=t -c user.email=t@t commit -qam "v0.1.1"
git -C "$WORK/dev" push -q origin HEAD
./majora-city update < /dev/null > "$WORK/out3.txt" 2>&1 || { cat "$WORK/out3.txt"; die "update"; }
grep -q "Updated from v0.1.0 to v0.1.1" "$WORK/out3.txt" || die "update message"
[ -f dist/MajoraCity-v0.1.1.bps ] || die "update should produce v0.1.1"
python3 tools/bps.py apply "$WORK/good.z64" dist/MajoraCity-v0.1.1.bps "$WORK/p2.z64" > /dev/null
grep -q "v0.1.1" "$WORK/p2.z64" || die "updated patch doesn't contain the new code"
pass "update: pulls, rebuilds, names the patch after the new version"

sed -i 's/^DECOMP_COMMIT=.*/DECOMP_COMMIT=0000000/' "$MC_DECOMP_DIR/.mc_setup_stamp"
cp "$WORK/good.z64" rom/
./majora-city build < /dev/null > "$WORK/out4.txt" 2>&1 || { cat "$WORK/out4.txt"; die "build after pin change"; }
grep -q "newer decompilation" "$WORK/out4.txt" || die "pin change should re-run setup"
pass "a decomp pin change re-runs the one-time setup automatically"

./majora-city patch "$WORK/good.zip" dist/MajoraCity-v0.1.1.bps "$WORK/p3.z64" > /dev/null
cmp -s "$WORK/p3.z64" "$WORK/p2.z64" || die "patch command output differs"
expect_fail "Japanese version" ./majora-city patch "$WORK/jp.z64" dist/MajoraCity-v0.1.1.bps "$WORK/p4.z64"
pass "patch command (players): works from a zip, rejects the wrong ROM clearly"

echo "all CLI tests passed"
