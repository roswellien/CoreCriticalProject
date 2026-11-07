# Modular MW3-RE content tools

The native MW3-RE `mw3content` executable owns package validation, dependency and
conflict resolution, compilation, installation and inspection. The launcher and
Mod Studio call its JSON interface; neither maintains a second gameplay resolver.
These tools require a matching modular-content runtime and content executable.

## Launcher profiles

Open **Mods & Packs → MW3-RE profiles**. Select your `mw3content` executable,
MW3-RE runtime and a writable package library. Install a `.mw3pack`, refresh the
available versions, select exact package versions and give the collection a name.
**Choose HUD & appearances** queries the resolved native catalogue and offers
available HUD layouts and chassis appearances; these selections remain separate
from package enablement and retain the native stock HUD by default.
**Save profile** validates and preserves it. **Use for Play** selects it for the
launcher's Play button. Resolution runs again before the native process starts.

Profiles are separate files under the launcher's user-data `content-profiles`
directory. Changing a profile name creates another collection. Replacing an
existing profile retains its previous version. Failed resolution leaves the saved
profile unchanged. Package versions and optional integrity pins come from the
native tool's installed inventory; the UI never guesses a compatible replacement.
Saving records the complete resolved dependency closure with exact versions and
integrity hashes. Installing newer dependencies cannot change an existing profile.
Unavailable saved pins remain selected until the user explicitly removes them.

The selected runtime uses its own graphics and controls configuration. Launch
arguments identify the verified original installation, selected profile, package
store and a separate native write directory. **Use existing launcher mode** clears
the profile selection. Selecting Original/D7VK also clears that selection.
The older prepared-pack library and original-engine path remain separate.

## Studio authoring

Open **Native content packages** in Map Studio. Configure the two executables and
a workspace outside the original installation. Choose a starter definition, edit
the source manifest and **Save and compile**. Compilation calls the native tool;
unknown behaviors, references or fields are reported by that tool rather than
silently accepted by the editor.

Sources live in `sources/<project>/`, immutable compiled builds in
`compiled/<project>/build-<unique-id>/`, exports in `exports/`, and installed
versions in `store/`. Each successful compilation atomically updates
`compiled/<project>/latest.json`; failed compilation preserves that receipt and
all earlier builds. Repeated exports use distinct filenames containing the
project and package version. **Install compiled
version** makes it available to the exact pins in the profile editor. Validate and
save the profile before **Native playtest**, optionally choosing a stable mission
ID. Playtests run MW3-RE with an isolated write directory and log under
`playtest/<role>/`. A second Studio playtest for the same role is refused while
its process is active. No operation copies files into the original installation.

For an arena mission, choose **Host arena** or **Join arena**, enter its stable
mission ID and use matching gameplay profiles on both peers. Host and join have
separate native write directories, so a local pair can run from the same Studio
workspace. Configure host port, join address and two to eight expected players.
The runtime performs the bounded content handshake before arena construction;
the Studio does not bypass identity checks. To select an additional chassis,
put `selections.multiplayer` in the pinned profile with `chassis` and `skin`
stable content IDs and the exact chassis-scoped native `loadout` name.

Starter definitions are authored examples, not included game assets. Chassis and
weapon variants explicitly name a stock native base. Skin texture-slot bindings
and prepared visual payloads require compatible locally authored resources;
the editor does not fabricate asset-free substitutes for those resources.
The JSON editor exposes the current native schemas. Arbitrary scripts, new HUD
widget types and unimplemented native mechanics are not admitted by these tools.

A HUD can optionally add `data.artwork` using the `hud_artwork_binding` example
returned by the template API. It declares `format: "mw3h-v1"` and a `sprites`
object mapping native 16-digit sprite identities to explicit package resource
paths. Put the authored files under `sources/<project>/` before compilation and
require capability `hud-artwork-mw3h-v1` version 1. This is the existing MW3H-v1
prepared UI format; the native renderer reads the selected HUD's pinned resources
without a manual artwork directory or native image archive rebuild. The Studio
shows the optional JSON example beside the source editor. Files are integrity
checked by the shared native tool and decoded lazily by the native compositor.

## Checks

The following checks use authored temporary fixtures and a built native content
tool. They exercise actual compilation, installation and resolution, including
rejected pins preserving the previous profile:

```powershell
dotnet run --project tools/mw3-remaster-launcher-tests -- --modular-content-only C:\path\to\mw3content.exe
$env:MW3CONTENT = 'C:\path\to\mw3content.exe'
python -m unittest discover -s games/mw3/mod-tools/tests -p test_content_authoring.py -v
```

Without `MW3CONTENT`, the Python workspace-containment check runs and the native
integration case is explicitly skipped. These fixtures do not establish live
mission completion, campaign fidelity or runtime release readiness.
