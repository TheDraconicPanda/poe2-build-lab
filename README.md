# PoE2 Build Lab

A local web workbench for character defences and upgrade research. The supplied
level 93 Abyssal Lich's **1,892 Life / 6,091 ES** now independently recalculate
with a pinned PoB2 engine, with saved outputs removed. The user confirmed these
totals in PoE2 0.5.5. See [the exact breakdown](docs/BASELINE.md).

## Setup and run

The importer needs Python 3.12+. The calculation engine additionally needs Git,
Make, GCC and HTTPS access to GitHub during installation. It uses LuaJIT and
luautf8, built locally from exact source commits in `engine/pins.json`.

```sh
cd /workspace/poe2-build-lab
python scripts/setup_engine.py
python app.py --port 8000
```

Setup installs into ignored `.local/` paths, preserves TLS verification and checks
source commits. It does not modify upstream calculation/data files. It is repeatable;
existing pinned checkouts are reused. Dependencies keep their upstream licence
files. Nothing is published or uploaded by setup. No API keys or database are needed.
Once installed, calculation runs offline. Live server processes must restart after
restoring an environment snapshot; dependencies persist only if included in that snapshot.

Open the app with a local browser. Paste a PoB2 export code, or load an XML/text
export and click Import. Then click **Recalculate baseline** for calculated totals,
reference differences, ES contribution rows, the modifier source ledger and engine
coverage notes. The server binds to loopback only. Imports use temporary files
which are removed after calculation and are not saved as build history.

Without engine setup, importing still works; recalculation reports the missing
installation explicitly. Only passive tree `0_5` is accepted for calculation.
The engine snapshot is validated against the supplied build, not every 0.5.5 build.
An unparsed staff Archon modifier is surfaced instead of silently hidden.

## Validate

```sh
# Full suite, including real engine calculations (requires setup above):
python -m unittest discover -s tests -v
# Import-only suite without the engine:
python -m unittest discover -s tests -p test_import.py -v
# Optional browser smoke: running server + Playwright + /usr/bin/chromium:
python tests/browser_smoke.py
```

The engine tests poison/remove saved outputs and change real item Life to check
that calculation is independent and changes propagate to ES. Browser smoke checks
imports, calculated totals, the ledger, game comparison, engine-backed upgrade scenarios, mobile layout and errors.
The regression fixture has item Unique IDs removed.

The **Compare upgrades** form recalculates both sides through the engine: edit one
jewel's increased-ES modifier, set all supported jewels to one target, remove a
jewel, change chest final local ES, or combine these. Results show Life/ES totals,
absolute/relative differences, precise edits and coverage notes. Changing form
inputs hides stale results. All other item properties stay fixed; chest ES is not
a complete item replacement or a crafting feasibility check.

[Scenario validation and results](docs/SCENARIOS.md) include independent PoB input
edits, no-change checks and a literal 200 → 400 chest comparison. These are
pinned-engine predictions, not additional in-game measurements. Rune and
ring-effectiveness interactions remain the next milestone.

See [the finite V1 plan](docs/PROJECT.md), [calculation research](docs/CALCULATIONS.md),
and [engine attribution](engine/THIRD_PARTY.md).
