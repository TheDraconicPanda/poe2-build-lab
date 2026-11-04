# Reconciled baseline: supplied Abyssal Lich

The user confirmed this build's 1,892 Life and 6,091 maximum Energy Shield in
PoE2 **0.5.5**. The pinned PoB2 snapshot independently reproduces both integers
with **all saved PlayerStat and MinionStat outputs removed**.

Engine: `bb52d6b368307457eb9c54bb13f1829993d390b1` from
[PathOfBuildingCommunity/PathOfBuilding-PoE2](https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2/tree/bb52d6b368307457eb9c54bb13f1829993d390b1),
passive tree `0_5`. Game version is user supplied; the export does not identify
its original engine release. This is a validated build/snapshot pairing, not
certification of every 0.5.5 rule or build.

## Life

| Contribution | Base Life |
|---|---:|
| Level/base character contribution: 12 × 93 + 16 | 1,132 |
| Ogham Manor quest | 20 |
| Strength: 137 × 2 | 274 |
| Equipment: 31 + 97 + 127 + 46 + 67 | 368 |
| Total base | 1,794 |

Enhanced Barrier (`Tree:44299`) converts 5% of Life to ES. Increased Life is
11%: 5% from the Khari Crossing quest and 3% each from nodes 33141 and 36696.

`round(1794 × 0.95 × 1.11) = round(1891.773) = 1892`

The intermediate display line `1704` is formatted for the PoB breakdown. Do not
round that intermediate before applying increased Life.

## Energy Shield

The engine's global increased-ES pool is **533%**, including tree, jewels, quest
and Umbral Well contributions. Illuminated Crown (`Tree:1823`) adds **70%** for
the helmet. The factors are therefore 6.33 globally and 7.03 for the helmet.

Life-derived ES uses base Life in this engine's conversion/gain-as pipeline:
`round(1794 × (5% + 14%)) = 341`. The 14% comes from Atziri's Disdain. Using
14% of the final 1,892 Life instead would give the wrong result for this build.

| Source | Base ES after item parsing | Factor | ES contribution |
|---|---:|---:|---:|
| Helmet | 74 | 7.03 | 520.22 |
| Gloves | 65 | 6.33 | 411.45 |
| Boots | 173 | 6.33 | 1,095.09 |
| Body Armour | 215 | 6.33 | 1,360.95 |
| Global flat ES (amulet) | 86 | 6.33 | 544.38 |
| Life conversion and gain-as | 341 | 6.33 | 2,158.53 |

`round(520.22 + 411.45 + 1095.09 + 1360.95 + 544.38 + 2158.53)`
`= round(6090.62) = 6091`

These item ES values come from `GetArmourDataValue` after PoB parses the items.
Local increased ES and quality must not be applied to them a second time.

The app exposes the engine's evaluated modifier ledger, including source IDs,
passive names, modifier types, and global versus slot scopes. Slot scopes repeat
global modifiers; never sum rows across scopes.

## Checks establishing independence

`tests/test_engine.py` runs the actual engine, not a mocked calculator:

- Original fixture calculates 1,892 / 6,091.
- Replacing saved Life with 999,999 and ES with 1 still calculates 1,892 / 6,091;
  the comparison correctly reports a mismatch.
- Removing saved outputs entirely still calculates the same totals, with no
  reference match claimed.
- Changing the ring's +67 Life to +77 calculates **1,902 Life / 6,103 ES**.
  This exercises the dependency from item Life through conversion/gain-as to ES.

## Known limits

The engine reports an unparsed staff modifier:
`47% chance to gain Nature's Archon when your Plants Overgrow`.
This is displayed even when defence totals match; matching totals do not prove
combat buffs or every item mechanic are implemented.

The tree loader logs missing connector endpoints when preparing its UI assets.
These warnings originate in `Classes/PassiveTree.lua` while drawing connections,
not a failed lookup of this build's allocated nodes. The adapter separately checks
all selected allocated node IDs against the loaded tree; **none are missing**.

Only tree `0_5` is accepted for recalculation. Other tree versions are rejected
rather than silently migrated. Upgrade scenarios still need dedicated fixtures;
this milestone does not certify chest, rune, ring-effectiveness or general upgrade
predictions.
