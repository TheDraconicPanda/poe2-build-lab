# Finite scope: defence upgrades for one verified build

## Target and completion rule

Version 1 targets the supplied Abyssal Lich in **PoE2 0.5.5**. Engine snapshot
`bb52d6b368307457eb9c54bb13f1829993d390b1` now reproduces its two defence totals;
this validates the build/snapshot pair rather than every rule in that game patch. The user confirms maximum Life
1,892 and maximum Energy Shield 6,091 match the game. The export's `targetVersion`
is `0_1` while its passive tree is `0_5`; neither identifies a precise engine build.
Do not silently run a newer ruleset and call the result 0.5.5 accurate.

V1 is complete only when all four milestones pass. Matching reported numbers is
not independent verification. No calibrating unknown contributions to force totals.

| Milestone | Deliverable | Acceptance gate | State |
|---|---|---|---|
| 1. Import and audit | Local web app reads PoB2 XML/export codes, active gear, jewels, quests and reference totals | Actual supplied export imports; 14 equipped items, five allocated jewels; 1,892 Life / 6,091 ES displayed explicitly as exported | Implemented |
| 2. Reconciled baseline | Versioned engine adapter plus source ledger for level/attributes, gear, tree, quests, skills/conditions and interactions | Calculate both totals without reading saved PlayerStat outputs; match exact integers; every contribution traceable; unsupported modifiers surfaced | Implemented for supplied build; see BASELINE.md |
| 3. Defence comparisons | Change one jewel to 20%, all five to 20%, and body-armour final local ES independently and together | Baseline unchanged when no edits; each scenario matches an independently recalculated PoB build; show absolute/relative change and assumptions | Implemented for supported edits; see SCENARIOS.md |
| 4. Two named interactions | Darkness Enthroned at 94% with Iron Rune variants; ring-effectiveness belt | Differential PoB fixtures validate socket context, effect scaling, per-mod rounding and each ring; verify representative game changes | Engine features implemented; in-game before/after check pending (INTERACTIONS.md) |

Implementation now covers all four milestones. V1 acceptance remains pending the
representative interaction game check; no further feature scope is implied.

The sensitivity worksheet has been replaced with engine-backed comparisons.
Milestone 3 covers isolated final local chest ES, not wholesale item replacement.

## Design decision

The app now runs a pinned PoB2 headless adapter (`engine/calculator.py` and
`engine/runner.lua`). It reuses the upstream tree, parser and calculation pipeline
without changing their arithmetic. Results record the exact revision, tree and
selected item/config/skill/tree sets. The supplied weapon-set choice is preserved
in the XML. Upstream licences are retained with installed sources; no upstream
code or binaries are vendored. See engine/THIRD_PARTY.md and docs/BASELINE.md.

## Regression cases required before V1 completion

1. Original build: Life 1,892 / ES 6,091, calculated with saved outputs removed.
2. Eagle Vessel 16% → 20% global maximum ES, plus a no-change case.
3. All five jewels → 20%: current modifiers 15, 20, 14, 20, 16; additive change **+15 percentage points**. Test removing/replacing a jewel too.
4. Chest ES 200 → 400 as final local ES; distinguish from changing base ES,
   quality or a local increased modifier. Also test the actual exported chest.
5. Darkness Enthroned 94% with normal/greater/perfect Iron Rune as separate cases;
   compare replacing an occupied socket as well as adding to an empty one.
6. Ring-effectiveness belt: both rings, asymmetric modifiers, and replacement of
   Darkness Enthroned rather than stacking two equipped belts.
7. Life changes while wearing Atziri's Disdain: validate downstream ES changes.
8. Different active weapon/item/tree/config sets; irrelevant inactive items have no effect.

Each expected number needs provenance: engine revision and reference build export;
record in-game confirmation separately. The original fixture is an acceptance target,
not a complete set of scenario expectations.

## Explicit exclusions for V1

DPS, EHP, resistances as upgrade objectives, trading/prices, automatic item shopping,
account login, cloud storage, all unique items, every ascendancy and ongoing support
for future patches. Show unsupported inputs instead of silently treating them as zero.
Additional rulesets or interactions are later projects with their own acceptance cases.
