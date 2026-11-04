# External calculation dependencies

The adapter downloads and executes unmodified source from these projects. The
source revisions are recorded in `pins.json`; sources and build outputs stay in
ignored `.local/` directories and are not vendored into this repository.

- [Path of Building Community (PoE2)](https://github.com/PathOfBuildingCommunity/PathOfBuilding-PoE2): original copyright David Gowor and community contributors. Licence/third-party notices are retained at `.local/pob2/LICENSE.md`.
- [LuaJIT](https://github.com/LuaJIT/LuaJIT): copyright Mike Pall and contributors; MIT licence retained at `.local/sources/luajit/COPYRIGHT`.
- [luautf8](https://github.com/starwing/luautf8): copyright Xavier Wang and contributors; MIT licence retained at `.local/sources/luautf8/LICENSE`.

Retain these licence/third-party notices if redistributing source or installed
artifacts. PoB game data remains subject to its upstream notices. No affiliation
with Grinding Gear Games or the PoB project is implied.
