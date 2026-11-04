# Darkness Enthroned and Ingenuity comparisons

Engine implementation is complete for the supported cases below. **Representative
in-game before/after verification remains pending.** This is the remaining V1
acceptance gate, not an additional completed game measurement. Do not buy an item
solely to validate a test; an existing supported swap can provide the evidence.

The pinned engine revision remains `bb52d6b368307457eb9c54bb13f1829993d390b1`.
Original Life/ES are user-confirmed in PoE2 0.5.5; engine/snapshot compatibility is
build-specific. See [BASELINE.md](BASELINE.md) and [PROJECT.md](PROJECT.md).

## Darkness Enthroned: body-armour context, 94% effect

Select an existing socket and its new augment. The application edits the Rune
binding and optional effect roll in the item input; unmodified PoB2 `ParseRaw` /
`UpdateRunes` rebuilds the regular and Bonded modifiers. Exported rune effects are
not kept as additional independent bonuses. Only the Body Armour variant and the
validated existing augments (Fox Idol, Rune of the Blossom, Iron Rune tiers, None)
are supported. Other contexts or unknown augments fail explicitly.

| Replaces Fox Idol in socket 1 | Armour-context base modifier | Additional effect after truncation | Total increased defences | Life | ES |
|---|---:|---:|---:|---:|---:|
| Normal Iron Rune | 16% | 15% | 31% | 1,892 | 6,386 |
| Greater Iron Rune | 18% | 16% | 34% | 1,892 | 6,415 |
| Perfect Iron Rune | 20% | 18% | 38% | 1,892 | 6,453 |

At 94%, 16 × 1.94 = 31.04 is nominal arithmetic, not the effective fractional
modifier used in this engine. The original integer modifier is retained and the
additional 94% component is truncated per combined mod, giving 16 + 15 = 31.
On this belt, the armour-context defence bonus is global: a belt has no local
armour defence to scale. Normal armour items use a different local-defence path.

PoB combines equal rune stat lines before additional scaling. With two Greater
Iron Runes this is 36 + truncate(36 × .94) = **69%**, not 34 + 34 = 68%.
The integration test checks the actual evaluated ledger, not only final ES.

Replacing Fox Idol removes its Idol/Bonded benefits. Iron Rune's displayed Bonded
Life/Mana modifiers are not automatically active; this fixture's Life remains
1,892. Replacing Rune of the Blossom in socket 2 instead removes its Spirit effects:
normal Iron Rune still predicts 6,386 ES but gives **−13 unreserved Spirit** under
the retained skill configuration. That is not a usable defence upgrade without
resolving the skills/reservations first.

An empty socket is represented by `Rune: None`, not by silently adding socket
capacity. Empty-to-Iron, occupied-to-Iron, no-op swaps, effect rolls and combined
same-stat rounding are tested. Other jewel and chest controls can be combined.

## Ingenuity: replace the equipped belt

The supported current-version template has separate **20–30% left** and
**20–30% right** ring effect, 1–3 charm slots and neutral (0%) charm-charge rolls.
Left means Ring 1, right means Ring 2. Legacy shared 40–80% ring-effect versions
are intentionally rejected. This is a labelled hypothetical belt, not a claim
about an unspecified real item.

Ingenuity replaces the entire equipped belt record. Darkness Enthroned's augment
effect, socket bindings and rune modifiers are removed, rather than stacked with
Ingenuity. Ring items are retained. PoB applies the corresponding ring-side effect
and per-mod truncation, then reruns Life and downstream Life-derived ES.

| Left / right effect | Life | ES | Calculated unreserved Spirit |
|---|---:|---:|---:|
| 30% / 20% | 1,919 | 6,122 | −9 |
| 20% / 30% | 1,922 | 6,122 | −9 |
| 30% / 30% | 1,927 | 6,129 | −7 |

These retain the selected skills, so all three have an insufficient-Spirit warning.
Their Life/ES totals are **conditional calculations**, not recommendations to equip
the belt with the unchanged skill setup.

For 30% / 20%, the original +46 Life on Ring 1 gains truncate(46 × .30) = 13;
+67 Life on Ring 2 gains truncate(67 × .20) = 13. Changing the side assignment
changes the result. Ring Spirit bonuses are evaluated separately, not inferred
from Life or from the character's final total.

The UI exposes resulting belt/socket identities, evaluated ring/belt modifier
sources and calculated Spirit alongside Life/ES differences.

## Spirit coverage limit

The snapshot calculates **229 total / 38 unreserved Spirit** for the original
build, while the export saved **229 / 36**. Life and ES match exactly, but Spirit
is not reconciled and is presented only as a diagnostic. This known mismatch is
shown in comparison warnings. Negative Spirit still reveals a problem with the
retained skill setup; no automatic skill removal or speculative minion reduction
is applied to disguise it.

The unparsed Nature's Archon staff modifier also remains visible. The application
is a bounded Life/ES comparison tool, not a complete combat or reservation engine.

## Evidence and remaining acceptance check

`tests/test_interactions.py` exercises the real engine. Rune results are compared
with separately edited raw exports and expected evaluated modifiers. Ingenuity
results are additionally compared with **a neutral belt and manually pre-scaled
ring Life/Spirit**, without using ring-effect mods or the scenario constructor.
This independent path checks side assignment, truncation and downstream ES.

Browser smoke covers rune replacement, whole-belt replacement, lost-coverage
warnings, conditional Spirit, input changes hiding stale results, and mobile layout.

To close the V1 game-verification gate, record one supported rune or belt change:
original PoB/export and game maximum Life/ES, exact socket replacement or ring-side
rolls, same active weapons/skills/conditions, and game maximum Life/ES afterward.
Resolve mismatches before declaring V1 accepted. The existing original baseline
confirmation does not supply this additional evidence.

## Pinned source references

- [Rune definitions](https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2/blob/bb52d6b368307457eb9c54bb13f1829993d390b1/src/Data/ModRunes.lua): armour-context Iron Rune 16/18/20%, regular/Bonded data.
- [Item parsing and scaling](https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2/blob/bb52d6b368307457eb9c54bb13f1829993d390b1/src/Classes/Item.lua): UpdateRunes combines stat lines; BuildModList applies additional socketed augment effect.
- [Modifier scaling](https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2/blob/bb52d6b368307457eb9c54bb13f1829993d390b1/src/Classes/ModStore.lua): ScaleAddMod truncation and precision rules.
- [Ring effect application](https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2/blob/bb52d6b368307457eb9c54bb13f1829993d390b1/src/Modules/CalcPerform.lua): per-slot bonus-effect scaling.
- [Belts](https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2/blob/bb52d6b368307457eb9c54bb13f1829993d390b1/src/Data/Uniques/belt.lua): current and legacy Ingenuity variants, Darkness Enthroned contexts.
