# Building the Majora City patch

You get a `.bps` patch file that turns a Majora's Mask (USA) ROM into Majora City, plus a share-ready zip and
a playable ROM for yourself. It's **one command**, and the same command works for every future update.

**You need:** your own dump of *The Legend of Zelda: Majora's Mask* (USA, N64), as `.z64`, `.n64`, `.v64`, or a
`.zip` containing one. It must be the clean cartridge dump; the builder checks this and tells you exactly what's
wrong if not.

---

## Windows

The build runs in WSL (Linux inside Windows), which Microsoft provides for free.

1. **Install WSL (once).** Open *PowerShell as Administrator* and run `wsl --install`, then restart the PC.
   On first start, Ubuntu asks you to pick a username and password.
2. **Get Majora City.** In the Ubuntu window:
   ```bash
   git clone https://github.com/StormEf4/Majora-City-.git
   cd Majora-City-
   ```
   (Or download the zip from GitHub and unzip it anywhere. Updates are easier with `git clone`.)
3. **Put your ROM in the `rom` folder** inside Majora-City-. From Windows Explorer, open
   `\\wsl$\Ubuntu\home\<your-username>\Majora-City-\rom`.
4. **Build:** double-click **`majora-city.cmd`**, or run `./majora-city build` in Ubuntu.

The first time, it offers to install the build tools (type your Ubuntu password when asked).

## Linux (Ubuntu, Debian, and others)

```bash
git clone https://github.com/StormEf4/Majora-City-.git
cd Majora-City-
cp "/path/to/Majora's Mask (USA).z64" rom/
./majora-city build
```

On Debian/Ubuntu it offers to install anything missing. On other distributions, `./majora-city doctor` lists the
packages you need.

## macOS

```bash
brew install coreutils make python3 libpng bash libxml2 libiconv
```
MIPS binutils must be built once from source; follow
[the decompilation's macOS guide](https://github.com/zeldaret/mm/blob/main/docs/BUILDING_MACOS.md). Then:
```bash
git clone https://github.com/StormEf4/Majora-City-.git && cd Majora-City-
cp "/path/to/Majora's Mask (USA).z64" rom/
./majora-city build
```

---

## What happens

```
[1/6] Checking your computer      build tools present? (offers to install them)
[2/6] Checking your ROM           right game, right region, clean dump?
[3/6] Getting the decompilation   downloads zeldaret/mm once
[4/6] One-time setup              extracts the game's files and test-builds the original (10-30 min, once)
[5/6] Building Majora City        compiles the hack (seconds to a few minutes)
[6/6] Creating the patch          makes the .bps and checks it reproduces the build exactly

✓ Done
  Patch   dist/MajoraCity-v0.1.0.bps
  Share   dist/MajoraCity-v0.1.0.zip   (patch + how-to-play + changelog)
  Play    dist/MajoraCity-v0.1.0.z64   (your own patched ROM; don't share it)
```

After the first build your ROM is remembered, so you can delete it from `rom/`.

## Every update after this

```bash
./majora-city update
```

That downloads the latest Majora City changes and builds the new patch, named after the new version
(`MajoraCity-v0.2.0.bps`, ...). Nothing else is needed. If an update moves to a newer decompilation, the
one-time setup re-runs by itself. On Windows, `majora-city.cmd update` does the same.

## Sharing the patch

Share **`dist/MajoraCity-vX.Y.Z.zip`** (or just the `.bps`), for example on the GitHub Releases page. Players
patch their own ROM with [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/) in a browser; the zip's
`HOW-TO-PLAY.txt` walks them through it. **Never share the `.z64` ROM.**

## Other commands

| Command | What it does |
|---|---|
| `./majora-city build "/path/to/rom.z64"` | Build with a ROM that isn't in `rom/` (you can also drag the file onto the terminal window when asked) |
| `./majora-city doctor` | Check the build tools; `--install` installs them on Debian/Ubuntu/WSL |
| `./majora-city patch ROM.z64 MajoraCity-vX.Y.Z.bps` | Apply a patch yourself |
| `./majora-city info MajoraCity-vX.Y.Z.bps` | Show which version and commit a patch was built from |
| `./majora-city clean` | Delete compiled output (next build recompiles); `--all` also removes the setup (your ROM is kept in `rom/`) |
| `./majora-city build --verbose` | Show the full compiler output instead of a timer |

## When something goes wrong

The builder stops with a short explanation and, for long steps, the last lines of the log. Full logs are in
`build/logs/` (on WSL with the repo on a Windows drive: `~/.cache/majora-city/logs/`).

| Message | Fix |
|---|---|
| "This is the Japanese/European version" | Majora City needs the USA ROM. |
| "isn't identical to the original cartridge" | The ROM is modified (a randomizer, another hack, already patched), a bad dump, or a GameCube/Virtual Console extraction. Use a clean N64 dump. |
| "Some things the build needs aren't installed" | Run `./majora-city doctor --install` (Debian/Ubuntu/WSL) or follow the hint it prints. |
| "The one-time setup failed" | Run `./majora-city doctor`. If the log mentions a checksum, the ROM isn't the clean USA version. |
| "You have local changes" (during update) | `git stash`, then `./majora-city update`, then `git stash pop`. |
| A patch name ends in `-modified` | It was built with uncommitted changes. That's fine for testing; release from a clean checkout. |
