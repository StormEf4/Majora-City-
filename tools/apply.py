#!/usr/bin/env python3
"""
Apply Majora City (patches/ + mod/) to the decomp checkout, touching only files whose content actually changes.

Re-running it is cheap and keeps file timestamps stable, so `make` only rebuilds what really changed. That matters
because patched headers such as z64save.h are included by almost every source file.

    python3 tools/apply.py --decomp build/mm --commit <sha>           apply
    python3 tools/apply.py --decomp build/mm --commit <sha> --clean   restore the pristine decompilation

Usually run through tools/apply.sh, which fills in both arguments from decomp.lock.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = ".mc_synced_files"


def git(cwd, *args, check=True):
    result = subprocess.run(["git", "-C", cwd] + list(args), capture_output=True)
    if check and result.returncode != 0:
        raise RuntimeError("git %s failed:\n%s" % (" ".join(args), result.stderr.decode(errors="replace")))
    return result


def read_bytes(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        return None


def write_if_changed(path, data):
    if read_bytes(path) == data:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return True


def patched_paths(patch_files):
    """Files each patch touches: (paths that exist at the pinned commit, paths the patches create)."""
    existing, created = set(), set()
    for p in patch_files:
        with open(p, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        for i, line in enumerate(lines):
            m = re.match(r"^\+\+\+ b/(.+)$", line)
            if not m:
                continue
            path = m.group(1)
            (created if i > 0 and lines[i - 1] == "--- /dev/null" else existing).add(path)
    return existing, created


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--decomp", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    decomp = os.path.abspath(args.decomp)
    manifest_path = os.path.join(decomp, MANIFEST)
    old_synced = set((read_bytes(manifest_path) or b"").decode().split("\n")) - {""}

    # 1. Be on the pinned commit. Moving to a new commit (a pin bump) resets everything, which is expected.
    head = git(decomp, "rev-parse", "HEAD", check=False).stdout.decode().strip()
    if head != args.commit:
        git(decomp, "checkout", "-q", "--force", "--detach", args.commit)

    if args.clean:
        git(decomp, "checkout", "-q", "--force", "--detach", args.commit)
        for rel in old_synced:
            if os.path.isfile(os.path.join(decomp, rel)):
                os.remove(os.path.join(decomp, rel))
        if os.path.exists(manifest_path):
            os.remove(manifest_path)
        if not args.quiet:
            print("Decomp restored to pristine %s" % args.commit[:12])
        return 0

    patch_files = sorted(
        os.path.join(REPO, "patches", f) for f in os.listdir(os.path.join(REPO, "patches")) if f.endswith(".patch")
    )
    existing, created = patched_paths(patch_files)

    # 2. Work out the patched content in a scratch repository seeded with the pristine files.
    desired = {}
    with tempfile.TemporaryDirectory(prefix="mc-apply-") as tmp:
        git(tmp, "init", "-q")
        for rel in sorted(existing):
            data = git(decomp, "show", "%s:%s" % (args.commit, rel), check=False)
            if data.returncode != 0:
                print("error: a patch modifies %s, which doesn't exist at %s" % (rel, args.commit[:12]), file=sys.stderr)
                return 1
            os.makedirs(os.path.dirname(os.path.join(tmp, rel)) or tmp, exist_ok=True)
            with open(os.path.join(tmp, rel), "wb") as f:
                f.write(data.stdout)
        for p in patch_files:
            result = git(tmp, "apply", "--whitespace=nowarn", p, check=False)
            if result.returncode != 0:
                print(
                    "error: patch %s does not apply to %s\n%s"
                    % (os.path.basename(p), args.commit[:12], result.stderr.decode(errors="replace")),
                    file=sys.stderr,
                )
                return 1
        for rel in existing | created:
            desired[rel] = read_bytes(os.path.join(tmp, rel))

    # 3. Mod files, which must never shadow a decomp file.
    tracked = set(git(decomp, "ls-files", "-z").stdout.decode().split("\0")) - {""}
    mod_root = os.path.join(REPO, "mod")
    synced = set(created)
    for dirpath, _, files in os.walk(mod_root):
        for name in files:
            src = os.path.join(dirpath, name)
            rel = os.path.relpath(src, mod_root).replace(os.sep, "/")
            if rel in tracked:
                print("error: mod/%s would overwrite a decomp file; change it with a patch instead" % rel, file=sys.stderr)
                return 1
            if rel in desired:
                print("error: mod/%s is also created by a patch" % rel, file=sys.stderr)
                return 1
            desired[rel] = read_bytes(src)
            synced.add(rel)

    # 4. Write only what changed; undo leftovers from earlier versions of the mod.
    changed = []
    for rel, data in sorted(desired.items()):
        if write_if_changed(os.path.join(decomp, rel), data):
            changed.append(rel)

    stale_tracked = set(git(decomp, "diff", "--name-only", "-z", "HEAD").stdout.decode().split("\0")) - {""}
    stale_tracked -= set(desired)
    for rel in sorted(stale_tracked):
        git(decomp, "checkout", "-q", "HEAD", "--", rel)
        changed.append(rel)

    for rel in sorted(old_synced - synced):
        path = os.path.join(decomp, rel)
        if rel not in tracked and os.path.isfile(path):
            os.remove(path)
            changed.append(rel)

    with open(manifest_path, "w") as f:
        f.write("\n".join(sorted(synced)) + "\n")

    if not args.quiet:
        print(
            "Applied %d patches and %d mod files to %s (%s)"
            % (
                len(patch_files),
                len(synced - created),
                decomp,
                ("%d file%s updated" % (len(changed), "" if len(changed) == 1 else "s")) if changed else "up to date",
            )
        )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as e:
        print("error: %s" % e, file=sys.stderr)
        sys.exit(1)
