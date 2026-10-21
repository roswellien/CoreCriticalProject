MW3 Mod Tools — source preview

This package contains the desktop Map & Mission Editor and experimental browser
Map Studio source. It does not include the game, a native host, game archives,
extracted models, textures, music, or exported map packs.

Start with docs/setup-mod-tools.md. Install Windows x64 Python 3.11–3.14 with
Tkinter, obtain Mech3AX v0.7.0-rc3 separately, and supply your own original game.
Run Setup Mod Tools.cmd with the two folder paths described in that guide.
Then use Play MW3 - Mission Editor.cmd.

Studio is a prototype. Full preview/export/play needs additional local caches,
geometry and a prepared native game host. Do not assume export means a map is
playable or redistributable. Read docs/legal.md before sharing any output.

Project source: https://github.com/roswellien/MW3Recomp
Project-authored code: MIT (LICENSE). Three.js r128: MIT; its notice and exact
upstream file identities are in editor/web/static/js under the Mod Tools folder.
Pillow 12.3.0: MIT-CMU, installed separately from PyPI with pinned wheel hashes.
Mech3AX: EUPL-1.2, obtained separately, never bundled by this package.

PACKAGE-CONTENTS.json lists every included source file and its SHA-256.
SHA256SUMS.txt accompanies the archive. This is a local review candidate;
public release readiness and broader code review remain open.
