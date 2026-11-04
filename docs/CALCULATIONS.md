# Calculation evidence and open questions

Researched 2026-11-04 using public
[PathOfBuildingCommunity/PathOfBuilding-PoE2](https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2),
revision `bb52d6b368307457eb9c54bb13f1829993d390b1`.
This snapshot now reproduces the supplied build’s confirmed defence totals. That
is build-specific evidence, **not certification of every 0.5.5 rule**. See
[the reconciled baseline](BASELINE.md).
No upstream implementation or game data is bundled with this application.

## Why saved totals are insufficient

The supplied export contains `PlayerStat Life=1892`, `EnergyShield=6091`,
`Spec:EnergyShieldInc=383`, and allocated node IDs for tree `0_5`. A saved result
is not the source ledger. `Spec:EnergyShieldInc` must not be assumed to contain
all equipment, conditional and global defence modifiers. The importer intentionally
does not prefill the sensitivity pool from this field.

## Authoritative implementation references

Links are pinned so future upstream changes do not silently alter this research.

- [CalcDefence.lua](https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2/blob/bb52d6b368307457eb9c54bb13f1829993d390b1/src/Modules/CalcDefence.lua#L1359): resource conversion/gain-as paths distinguish per-slot/global bases and total modifiers; per-slot increased/more scaling occurs before final ES rounding (around line 1460). This prevents a universal one-line formula.
- [Item.lua](https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2/blob/bb52d6b368307457eb9c54bb13f1829993d390b1/src/Classes/Item.lua#L1490): socketed augment context/effect handling. Inspect item parsing/local armour calculation before treating exported ES headers as final displayed local ES.
- [Unique belts](https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2/blob/bb52d6b368307457eb9c54bb13f1829993d390b1/src/Data/Uniques/belt.lua#L65): Darkness Enthroned supports different equipment contexts. This export specifically says body armour, not an arbitrary belt rune effect.
- [ModRunes.lua](https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2/blob/bb52d6b368307457eb9c54bb13f1829993d390b1/src/Data/ModRunes.lua#L1711): normal Iron Rune armour entry is 16% increased Armour, Evasion and Energy Shield; it is local in ordinary armour. Context and the belt's special rules must be evaluated before assuming the same modifier is global on the belt.
- [HeadlessWrapper.lua](https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2/blob/bb52d6b368307457eb9c54bb13f1829993d390b1/src/HeadlessWrapper.lua): exposes `loadBuildFromXML` and a headless build object; candidate adapter entry point. Now integrated and exercised by the baseline and regression tests.

At 94% increased augment effect, the nominal scale factor is **1.94**. For a 16%
modifier the unrounded arithmetic is **31.04%**. That is not a verified global ES
bonus or a final character ES increase: applicability, modifier rounding, socket
replacement, bonded effects and the engine revision remain to be validated.
The supplied belt already holds Fox Idol and Rune of the Blossom, so replacing
one also removes its effects. A hypothetical empty socket is a different scenario.

## Visible complications in this build

- Atziri's Disdain: gain 14% of maximum Life as extra maximum ES. Validate the
  exact gain-as basis and ordering, rather than inferring it from tooltip wording.
- Atziri's Splendour: hybrid defences, extra socket behaviour and local increased ES.
- A jewel grants ES from an equipped Focus, while the active weapon is a staff;
  modifier applicability matters.
- Quest configuration includes 30% increased Global Armour, Evasion and Energy Shield.
- Passive IDs include weapon-specific allocations; conditions and attribute overrides
  must be resolved with the matching tree and selected weapon set.

## Sensitivity worksheet

For fixed base ES and fixed more multipliers, when one additive increased-ES pool
is the only changed factor:

`hypothetical ES = reference ES × (100 + pool + delta) / (100 + pool)`

16% → 20% is **+4 percentage points**, not 4% more final ES. All five imported
jewels to 20% adds 15 percentage points. The former worksheet retained fractional results and advertised its assumptions.
It has now been replaced by engine-backed comparisons, including per-slot scaling
and final rounding; see [SCENARIOS.md](SCENARIOS.md).

## Baseline milestone completed

The adapter strips saved outputs and independently calculates 1,892 Life / 6,091 ES.
The evaluated global increased-ES pool is 533%, with an extra 70% for the helmet
from Illuminated Crown. The detailed source ledger, rounding and conversion order
are documented in [BASELINE.md](BASELINE.md). The speculative points above now
have build-specific evidence there; rune and ring-effectiveness scenarios now have engine regression tests;
[INTERACTIONS.md](INTERACTIONS.md) records their still-pending game check. Jewel/chest scenarios
now have independent regression inputs in [SCENARIOS.md](SCENARIOS.md).
