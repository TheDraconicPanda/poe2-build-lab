# Verified defence comparison workflow

Milestone 3 adds engine-backed what-if comparisons to the supplied Abyssal Lich.
Both the original and changed build are recalculated with saved outputs stripped.
The engine revision is unchanged from [the reconciled baseline](BASELINE.md).

## Supported changes

- Set one allocated jewel's plain `N% increased maximum Energy Shield` modifier.
- Set every allocated jewel with that supported modifier to the same target.
- Remove one jewel from its active tree socket, including all of its modifiers.
- Set the equipped chest's **final local ES**, after quality and local modifiers.
- Combine jewel and chest changes; calculate together to include their interaction.

All other jewel modifiers and all other chest properties remain constant. The
chest control models one defence input, not a complete item replacement or a
craftable item. Its original name, special effects, sockets, Life and attributes
remain equipped. No chest is silently created if none is equipped. Level-dependent
local ES is rejected for this override. Inactive items/jewels cannot be selected.

Decorated, ranged or duplicate ES modifier lines are rejected rather than guessed.
All-jewel mode does not affect jewels without the supported maximum-ES modifier.
Zero targets and downgrades are allowed; the UI shows signed absolute/relative changes.

## Results for the supplied build

| Scenario | Life | ES | ES difference |
|---|---:|---:|---:|
| Original / no edits | 1,892 | 6,091 | 0 |
| Eagle Vessel: 16% → 20% | 1,892 | 6,129 | +38 |
| All five jewels → 20% | 1,892 | 6,234 | +143 |
| Chest final local ES: 215 → 200 | 1,892 | 5,996 | −95 |
| Chest final local ES: 215 → 400 | 1,892 | 7,262 | +1,171 |
| All five jewels → 20%, chest → 400 | 1,892 | 7,433 | +1,342 |
| Remove Eagle Vessel | 1,892 | 5,938 | −153 |

A literal chest **200 → 400** comparison increases ES from **5,996 → 7,262**, a
gain of **1,266**. The supplied chest has 215 local ES, so its gain to 400 differs.
Combined gains are recalculated together rather than adding separately rounded gains.

Only the original totals were confirmed in game. The scenario numbers are validated
against the pinned PoB2 implementation; they are not new in-game measurements.

## Why chest headers cannot implement this feature

Editing `Energy Shield: 215` to `Energy Shield: 400` in the export does **not** change
the engine's local defence. `Classes/Item.lua` reconstructs local ES from the base,
quality and local modifiers in `BuildModListForSlotNum`.

The adapter supplies the engine's existing `ArmourData` input with key `EnergyShield`
through the equipped item's `baseModList`, rebuilds its slot mod list, clears caches,
and reruns the normal calculation pipeline. `ArmourData` is applied after the local
calculation by unmodified upstream code. The adapter checks the resulting local
value with `GetArmourDataValue` before accepting the result. No final character
stat or post-calculation delta is patched.

The override lives in the scenario request/provenance, not a misleading edited
export header. Existing upstream source/data files and the original import remain
unchanged.

## Independent regression evidence

`tests/fixtures/defence-scenarios.json` records requests, independent raw-export
edits, expected totals and the engine revision. `tests/test_scenarios.py` compares
the public comparison function against those separately edited builds.

Jewel reference builds edit only their raw modifier text or socket assignment.
The independent chest references change the original 136% increased Evasion/ES
modifier to 119% (which produces 200 local ES) or 339% (400 local ES), then use
normal `calculate()` with **no local-ES override**. The reference also changes
Evasion; this fixture has no Evasion-to-Life/ES dependency, and the test compares
Life and ES only. It is independent validation of the local-ES override path,
not a claim that these hypothetical unique-item rolls can exist.

Tests cover no operations, explicit same-value overrides, individual/all jewels,
chest changes, combined changes, removal, edit isolation, invalid inputs and
inactive sockets. Browser smoke covers one/all/combined/no-op comparisons, input
changes hiding stale results, baseline coverage notes and mobile layout.

Results retain engine source coverage notes on both sides, including the existing
unparsed Nature's Archon staff modifier. A baseline/reference mismatch is shown
prominently instead of marking the upgrade as reconciled. Rune and ring-effectiveness
comparisons are now implemented; see [INTERACTIONS.md](INTERACTIONS.md). Their
representative in-game validation remains pending.

## API

`POST /api/compare` accepts an export and a scenario. Empty scenario `{}` is a
no-change comparison. Fields can be combined:

```json
{
  "export": "<PoB2 XML or compressed export>",
  "scenario": {
    "jewels": {"mode": "one", "itemId": "2", "targetPercent": 20},
    "chestEnergyShield": 400
  }
}
```

Jewel modes: `one` requires itemId and targetPercent; `all` requires targetPercent;
`remove` requires itemId. The response includes both complete engine results,
applied changes, absolute/relative differences, assumptions and provenance. No
requests or imports are stored as build history.

## Interaction request fields

Add `darknessRune: {"socket": 1, "rune": "Iron Rune", "effectPercent": 94}`
for a socket replacement, or `ingenuity: {"leftPercent": 30, "rightPercent": 20,
"charmSlots": 3}` for the whole-belt replacement. These fields are mutually
exclusive but can combine with jewel/chest changes. Augment effect is optional
and defaults to the equipped belt’s explicit roll. Supported new augments are
None and normal/greater/perfect Iron Rune.

Results now also include diagnostic Spirit values and resolved belt/ring identities.
Spirit has a known original-reference mismatch; negative unreserved Spirit yields
a prominent conditional-skill warning rather than an automatic skill adjustment.
