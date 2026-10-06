#!/usr/bin/env bash
# Fast checks that need no ROM. Run before every commit (CI runs the same thing).
#
#   tools/check.sh          generated data, BPS self-test, patches apply, C syntax/type check against the decomp
#   tools/check.sh --ido    also compile every Majora City C file with the game's real compiler (IDO 7.1)
#
# The C check uses the same host-gcc "CC_CHECK" flags as the decomp's Makefile, plus
# -Wdeclaration-after-statement, because IDO only accepts C89 declarations.

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

with_ido=0
[ "${1:-}" = "--ido" ] && with_ido=1

log "1/5 Generated skyline data is up to date"
python3 "$REPO_ROOT/tools/gen_skyline.py" --check

log "2/5 BPS round-trip self-test"
python3 "$REPO_ROOT/tools/bps.py" selftest

log "3/5 Patches apply to the pinned decomp"
ensure_decomp
"$REPO_ROOT/tools/apply.sh"

cd "$DECOMP_DIR"
VERSION_MACRO="$(echo "$MC_VERSION" | tr 'a-z.-' 'A-Z__')"
IINC=(-Iinclude -Iinclude/libc -Isrc -I"build/$MC_VERSION" -I. -I"extracted/$MC_VERSION")
# Without a ROM, a few ROM-extracted headers don't exist yet. These minimal stand-ins come last on the include
# path, so the real headers always win once ./majora-city build has extracted them.
IINC+=(-I"$REPO_ROOT/tools/check_stubs")
[ -d "extracted/$MC_VERSION" ] || echo "  (no extracted assets: using tools/check_stubs for ROM-only headers)"
C_DEFINES=(-D_MIPS_SZLONG=32 -DF3DEX_GBI_2 -DF3DEX_GBI_PL -DGBI_DOWHILE -DMM_VERSION="$VERSION_MACRO" -D_LANGUAGE_C)
MIPS_BUILTIN_DEFS=(-DMIPSEB -D_MIPS_FPSET=16 -D_MIPS_ISA=2 -D_ABIO32=1 -D_MIPS_SIM=_ABIO32 -D_MIPS_SZINT=32 -D_MIPS_SZPTR=32)
CC_CHECK_FLAGS=(-fno-builtin -fsyntax-only -funsigned-char -std=gnu89 -m32 -DNON_MATCHING -DAVOID_UB -DCC_CHECK=1)
CC_CHECK_WARNINGS=(-Wall -Wextra -Wno-unknown-pragmas -Wno-unused-parameter -Wno-unused-variable -Wno-missing-braces
    -Wno-unused-but-set-variable -Wno-unused-label -Wno-sign-compare -Wno-tautological-compare
    -Werror=implicit-int -Werror=implicit-function-declaration -Werror=int-conversion -Werror=incompatible-pointer-types)
MC_STRICT=(-Werror -Wdeclaration-after-statement)

mapfile -t mod_c < <(cd "$REPO_ROOT/mod" && find . -name '*.c' ! -name '*.inc.c' | sed 's|^\./||' | sort)
# Decomp C files our patches touch.
mapfile -t patched_c < <(grep -h '^+++ b/' "$REPO_ROOT"/patches/*.patch | sed 's|^+++ b/||' | grep '\.c$' | sort -u)

log "4/5 C syntax and type check (host gcc, decomp CC_CHECK flags)"
for f in "${mod_c[@]}"; do
    gcc "${CC_CHECK_FLAGS[@]}" "${IINC[@]}" "${CC_CHECK_WARNINGS[@]}" "${MC_STRICT[@]}" "${C_DEFINES[@]}" \
        "${MIPS_BUILTIN_DEFS[@]}" "$f"
    echo "  ok  $f"
done
for f in "${patched_c[@]}"; do
    gcc "${CC_CHECK_FLAGS[@]}" "${IINC[@]}" "${CC_CHECK_WARNINGS[@]}" "${C_DEFINES[@]}" "${MIPS_BUILTIN_DEFS[@]}" "$f"
    echo "  ok  $f (patched)"
done

# The text bank goes through the decomp's own encoder, then the same modern-cpp pass the Makefile uses.
textgen="$(mktemp -d)"
mkdir -p "$textgen/assets/text"
gcc -E -P -xc -fno-dollars-in-identifiers -DMM_VERSION="$VERSION_MACRO" "${IINC[@]}" assets/text/message_data.h |
    python3 tools/text/msgenc.py --encoding nes --charmap assets/text/charmap.txt - "$textgen/assets/text/message_data.enc.h"
gcc -fsyntax-only -std=gnu89 -m32 -funsigned-char -Wno-unknown-pragmas -Werror -I"$textgen" "${IINC[@]}" \
    "${C_DEFINES[@]}" assets/text/message_data_static.c
grep -q 'DEFINE_MESSAGE(0x4D00' "$textgen/assets/text/message_data.enc.h" || die "Majora City text bank missing from encoded text"
echo "  ok  assets/text/message_data.h (Majora City text bank encodes and compiles)"

if [ "$with_ido" = 1 ]; then
    log "5/5 Compile with IDO 7.1 (the original N64 compiler, static recompilation)"
    IDO="tools/ido_recomp/linux/7.1/cc"
    if [ ! -x "$IDO" ]; then
        # Same archive and location the decomp's own tools/Makefile uses.
        mkdir -p tools/ido_recomp/linux/7.1
        curl -sSL https://github.com/decompals/ido-static-recomp/releases/download/v1.2/ido-7.1-recomp-linux.tar.gz |
            tar xz -C tools/ido_recomp/linux/7.1
    fi
    out="$(mktemp -d)"
    for f in "${mod_c[@]}" "${patched_c[@]}"; do
        # Same flags as the decomp Makefile's IDO rule (CFLAGS, WARNINGS, C_DEFINES, MIPS_VERSION, ENDIAN, OPTFLAGS).
        "$IDO" -c -G 0 -non_shared -Xcpluscomm -nostdinc -Wab,-r4300_mul "${IINC[@]}" \
            -fullwarn -verbose -woff 624,649,838,712,516,513,596,564,594,807,609 \
            "${C_DEFINES[@]}" -mips2 -EB -O2 -g3 -o "$out/$(basename "$f" .c).o" "$f"
        echo "  ok  $f -> $(stat -c %s "$out/$(basename "$f" .c).o") bytes"
    done
    gcc -E -undef -D_LANGUAGE_C -D__sgi -P -xc -fno-dollars-in-identifiers -DMM_VERSION="$VERSION_MACRO" \
        -I"$textgen" "${IINC[@]}" assets/text/message_data_static.c -o "$out/message_data_static.c"
    "$IDO" -c -G 0 -non_shared -Xcpluscomm -nostdinc -Wab,-r4300_mul "${IINC[@]}" -woff 624,649,838,712,516,513,596,564,594,807,609 \
        "${C_DEFINES[@]}" -mips2 -EB -O2 -o "$out/message_data_static.o" "$out/message_data_static.c"
    echo "  ok  assets/text/message_data_static.c (with the Majora City text bank)"
    rm -rf "$out"
else
    log "5/5 IDO compile skipped (pass --ido to enable)"
fi

rm -rf "$textgen"

text="extracted/$MC_VERSION/text/message_data.h"
if [ -f "$text" ] && grep -q 'DEFINE_MESSAGE(0x4D[0-9A-Fa-f][0-9A-Fa-f],' "$text"; then
    die "vanilla text uses IDs in 0x4D00-0x4DFF; move the Majora City text bank"
fi

log "All checks passed"
