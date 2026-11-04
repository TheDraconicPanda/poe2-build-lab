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

## Browser distribution

The static build distributes PoB source/data, Wasmoon's Lua 5.4 WebAssembly runtime
and platform compatibility adapters. Generated syntax adaptations are documented
in docs/BROWSER.md. The published site's `licenses/` directory includes the full
PoB2 third-party notices, Wasmoon's MIT licence, and Lua's MIT licence. The native
LuaJIT and luautf8 binaries are not part of the browser distribution.
