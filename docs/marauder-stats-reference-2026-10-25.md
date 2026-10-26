# Marauder statistics reference and MW3 mapping

Owner supplied these references on October 25, 2026. Use named variants and
source-backed content data for additions; animation/controller compatibility
must not determine their gameplay identity. No original stock definitions or
installed packs were changed by this reference review.

## Reference comparisons

| Reference | Mass | Engine | Heat sinks | Role in this work |
| --- | --- | --- | --- | --- |
| [Marauder MAD-3R](https://www.sarna.net/wiki/Marauder) | 75 t | Standard 300 | 16 single | Baseline target; 64.8 km/h, 11.5 t armor, two PPCs, two medium lasers, AC/5 and 20 rounds. |
| [Orion ON1-K](https://www.sarna.net/wiki/Orion) | 75 t | Standard 300 | 10 single | Same weight/technology category; stronger armor and a mixed missile/ballistic loadout. Its values are not a substitute for Marauder's. |
| [Timber Wolf Prime](https://www.sarna.net/wiki/Timber_Wolf_(Mad_Cat)) | 75 t | XL 375 | 17 double | Compatible visual starting point; faster Clan OmniMech with different construction and weapons. |
| [Summoner Prime](https://www.sarna.net/wiki/Summoner_(Thor)) | 70 t | XL 350 | 14 double | Faster Clan comparison with jump capability; not a same-tonnage template. |

Marauder variant candidates from the same reference:

- MAD-5CS: ER PPCs, medium pulse lasers, LB 10-X, XL engine and 18 double sinks.
- MAD-5M: large/medium pulse lasers, LB 10-X, XL engine, 16 double sinks and four jump jets.
- MAD-5S: ER PPC/medium-pulse armament with a Gauss rifle.

These are distinct loadouts, not interchangeable names for the current refit.
Full variant armor allocation, critical slots, ammunition placement, construction
and equipment must be verified before a pack is labeled as that variant.

## Original MW3 equipment check

Read-only inspection of the user's local original media found both `PPC` and
`AC5` definitions in `weapons.zrd`. The native weapon lookup at `004848a0`
searches 37 records, stride 24, starting at `005e64ec`:

| Required item | Data definition | Registered native weapon ID |
| --- | --- | --- |
| Standard PPC | Present | Absent from this table |
| Standard AC/5 | Present | 1 |
| ER PPC | Present | 7 |
| LB 10-X | Present | 15 |
| Medium pulse laser | Present | 24 |

This corrects the earlier overly broad statement that standard PPC and AC/5
were absent from MW3. The AC/5 already has a registered identity. The standard
PPC has data but needs a verified game-facing registration and all its consumers
checked; merely replacing an authored string would not prove a working weapon.
Do not alias it to ER PPC or change a stock weapon's behavior.

The current experimental refit still has ER PPCs, Ultra AC/5 and fifteen single
sinks. It remains a compatibility prototype, not a verified MAD-3R. To reach the
baseline target, correct the weapon selections and sink count in authored pack
data, then check the original parser's mass/slot rules, Mech Lab presentation,
firing/heat/ammunition behavior and saved configurations. A data change cannot
stand in for unsupported engine behavior.

Local source identities and the complete registered weapon-name/ID list are in
`local/work-ahead/marauder-prototype-20261024-r1/stat-reference-20261025/equipment-availability.json`.
Only derived findings are recorded here; original media remains local.

## Pack architecture

Store chassis statistics, loadout names and equipment choices in the pack's
authored definition/registry. Additional compatible variants should be discovered
through that data contract, as additional skins are. Extend shared engine
capabilities only for a missing behavior or equipment contract, rather than
adding a special case for each mech. Preserve the original game's damage/range/
heat rules; tabletop numbers establish construction references, not an implicit
rebalance of stock MW3 weapons.

This review adds no gameplay acceptance credit and does not activate a new DEV
runtime. Acceptance remains 131/144.
