# Majora City: notes for contributors and AI sessions

Majora City is a ROM hack built on the zeldaret/mm decompilation (pinned in `decomp.lock`). Start with
`README.md`, `ROADMAP.md` and `docs/tech/architecture.md`.

## The build must stay one command

Users build the patch with `./majora-city build` and get updates with `./majora-city update` (see
`BUILDING.md`). Every change must keep that working:

- New C files go in `mod/`; changes to decomp files go in `patches/` (see architecture.md). Never require a
  manual step from users. If a change needs new setup work, put it in `./majora-city` so it happens automatically.
- If a new build dependency is needed, add it to `check_prereqs` in `./majora-city` (and its apt package).
- Bumping `DECOMP_COMMIT` in `decomp.lock` is safe for users: the CLI detects it and re-runs the one-time setup.

## Every update that changes the game (release checklist)

1. Bump `VERSION` (semantic versioning: new milestone → minor, e.g. `0.2.0`; fixes → patch, e.g. `0.1.1`).
   The patch file is named after it: `dist/MajoraCity-v<VERSION>.bps`.
2. Add a section at the top of `CHANGELOG.md` in player-facing language. It ships inside the share zip.
3. Update the status markers in `ROADMAP.md`.
4. Run the checks (no ROM needed):
   ```bash
   tools/check.sh --ido     # generated data, BPS, patches apply, C checks, IDO 7.1 compile
   tools/test_cli.sh        # end-to-end test of ./majora-city (fake ROM + fake make)
   ```
5. If `tools/gen_skyline.py` inputs changed, re-run it (and `tools/preview_skyline.py` for the doc images).

## Never

- Commit a ROM, extracted assets, or a `.bps` (they're gitignored; `rom/` only tracks its README).
- Edit files inside `build/mm`: it's a managed workspace rebuilt from `mod/` + `patches/`.
