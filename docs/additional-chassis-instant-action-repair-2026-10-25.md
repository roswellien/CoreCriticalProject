# Additional chassis selection in Instant Action

The reported failure was reproduced: selecting Marauder as Commander accepted
runtime chassis ID 32, but the original roster validator subsequently changed
that entry to Strider (14). The previous adapter extended only the Commander
list and registered the chassis in the Mech Lab stockpile after validation.

The adapter now extends the original Commander, three lancemate and six enemy
selectors from the installed chassis catalog. Enemy lists are extended when
their original initializer runs, including independent mode refreshes. Existing
rows and their item data remain intact; inserted rows are checked for identity.

Registration also runs when the original active stockpile preparation returns,
before roster validation. It applies only to inventories with the original
unlimited flag. Newly created chassis items receive the original item's
unlimited flag too, matching stock initialization. Without that second flag,
assigning the same addition to Commander and lancemate consumed the only unit
and caused the lancemate to fall back to a stock chassis. Campaign inventories
receive no free chassis.

This advances installed catalog -> original Instant Action selection -> original
inventory validation -> original configuration construction -> live actors.
No Marauder-specific name, ID, loadout or visual replacement is hardcoded.
Original gameplay, translated module and other host components are retained.

## Validation and DEV activation

Local evidence is under `D:/MW3InstantActionRoles-20261025-r1/`:

- `mech-added-accept` and `mech-reset-caller` reproduce ID 32 becoming 14.
- `mech-fixed-commander` renders Marauder in the Mech Lab with its own 75-ton
  definition and loadout; `marauder-mechlab.png` records the preview.
- `mech-fixed-all-roles-r3` traces Commander, lancemate and enemy accepting ID 32
  and exposed the remaining finite-item defect.
- `mech-unlimited-final` uses the clean final host, selects Marauder for all
  three roles through recorded ordinary guest input, launches Instant Action,
  and records three distinct ID-32 actor roots. Its world render loads Marauder
  and no Strider replacement; `marauder-mission.png` records gameplay.
- `stock-training-sanity` reaches live Training without an additional-chassis
  catalog. This is a chassis-regression check with existing visual packs, not
  an original-graphics baseline comparison.
- Catalog, skin, preview-camera and exhaustive body-dispatch membership checks
  pass (`unit-final.log`; 2,097,672 dispatch checks).

The scripted runs intentionally stop at their presentation-frame budgets; the
budget-stop diagnostic is not a spontaneous game crash. These bounded tests do
not establish sustained combat, campaign/save compatibility or whole-game
acceptance. Strict acceptance remains 131/144.

Signed runtime 1.0.38 is installed in the existing DEV launcher's bundled Runtime
directory. All 669 manifest file hashes were checked. The previous host, profile,
manifest and source snapshot are retained in the local evidence directory.
The normal Windows DEV shortcut was reopened with its existing 14 enabled
packs and 1920x1080 settings. Its launcher-started game used the exact signed
host and closed normally (session `07ab6672aa234fa5aebbe9ec520f2bbe`, exit 0).
The public website/feed and installers have not been republished by this fix.
