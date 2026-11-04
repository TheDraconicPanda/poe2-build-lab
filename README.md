# PoE2 Build Lab

A local web workbench for understanding character defences and comparing upgrades.
Initial target: **PoE2 0.5.5**, the supplied level 93 Abyssal Lich. The user confirmed
that the exported **1,892 Life and 6,091 maximum ES** match the game.

## Run

Requires Python 3.12 or newer. No package installation, API keys, database, or network
access is needed to run the app.

```sh
cd /workspace/poe2-build-lab
python app.py --port 8000
```

Open the app with a local browser. Paste a PoB2 export code, or choose an exported
XML/text file and click Import. The server binds to loopback only. Imports are held
in memory and not written to disk. The included regression fixture has item Unique
IDs removed; it is not automatically loaded into the interface.

```sh
python -m unittest discover -s tests -v
```

Current features: compressed-code/XML import, active equipment and allocated-jewel
inventory, selected quest choices, saved PoB statistics, game-value comparison,
and a clearly marked jewel sensitivity worksheet (one jewel or all jewels).

**The independent calculation engine is not implemented.** Saved PlayerStat values
are reference targets, not evidence of recalculation. The sensitivity worksheet
requires the complete global increased-ES pool and assumes unchanged base ES,
more multipliers and modifier applicability. It is not a purchase recommendation.
Chest, rune and ring-effectiveness predictions are deliberately not offered yet.

See [the finite project scope](docs/PROJECT.md) and
[calculation research](docs/CALCULATIONS.md) for acceptance gates and remaining work.
