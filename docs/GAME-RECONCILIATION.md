# Current game measurements: reconciliation open

These user-reported readings supersede the earlier confirmation of 1,892 Life /
6,091 ES. The original export remains a useful **PoB engine parity fixture**, but
is not a verified baseline for the current game state.

| State | Reported game Life | Reported game ES | Original export recalculation |
|---|---:|---:|---:|
| Full gear | 1,891 | 6,949 | 1,892 Life / 6,091 ES |
| Helmet removed | Not supplied | 4,548 | 1,892 Life / 3,982 ES |
| Luminous Shard removed (20% increased ES) | Not supplied | 6,758 | 1,892 Life / 5,900 ES |

The user identified Luminous Shard and reports no gear change since syncing the
PoB on Ninja. The exact current Ninja export and skill/conditional-buff state
remain needed. The removal readings are interpreted as separate changes from
full gear; do not invent unreported Life readings or declare those conditions proven.

Measured deltas are **2,401 ES for the helmet** and **191 ES for the jewel**.
The old model already predicts a 191-point loss for that jewel. Its full baseline
and helmet-removal totals differ from the new game values.

## Strong diagnostic constraint, not a formula correction

Adding a *diagnostic-only* 90 percentage points to the original model's global
increased-ES pool reproduces all three reported ES integers through the actual
pinned engine:

| State | Original engine | Engine with diagnostic +90 percentage points | Game |
|---|---:|---:|---:|
| Full gear | 6,091 | 6,949 | 6,949 |
| Helmet removed | 3,982 | 4,548 | 4,548 |
| Luminous Shard removed | 5,900 | 6,758 | 6,758 |

The old global increased-ES pool is 533%; the candidate pool is 623%. This is not
90% more final ES. The old total scaling base is 954, including Life-derived ES.
The helmet has a further 70% slot-specific increase:

- Full: `954 × 7.23 + 74 × 0.70 = 6949.22` → 6,949 by the engine's final rounding.
- No helmet: `(954 − 74 − 251) × 7.23 = 4547.67` → 4,548. The 251 is the lost
  Life-derived ES contribution, not additional local helmet ES.
- No jewel: `954 × 7.03 + 74 × 0.70 = 6758.42` → 6,758.

This fit constrains the investigation; it does not uniquely prove where the extra
increase comes from. It may be missing state/input or an engine-rule mismatch.
**No +90 custom modifier or calibration is applied to the app, its saved builds,
its bundled data or the original regression fixture.** The experiment used
separate temporary XML inputs only.

## Life discrepancy remains separate

The old raw Life calculation is `1794 × .95 × 1.11 = 1891.773`. The engine rounds
that to 1,892; truncation would give the reported 1,891. This is consistent with a
rounding-order hypothesis but is not enough evidence to change every Life formula.
A changed input or intermediate rounding could also explain one point.

## Next evidence needed

Obtain the current PoB code or Ninja character URL and compare its exact inputs
with the original fixture: tree allocations, attributes, quests, global modifiers,
active weapon/skill/config sets, and conditional buffs. Identify an actual source
for the 90-point candidate gap, or demonstrate the specific engine rule that is
wrong. Then add the current build and removals as new game-validated regression
cases. Until then, the stored observations in `tests/fixtures/game-observations.json`
are an **unresolved acceptance target**, not a passing correctness test.
