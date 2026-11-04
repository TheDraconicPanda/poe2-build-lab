# PoE2 Build Lab — browser edition

A static, browser-only Life/ES upgrade workbench for GitHub Pages and Safari 17+.
**No Python server, account, PC access or external calculation API is needed to use
it.** The pinned PoB2 engine runs as Lua 5.4 WebAssembly in a browser worker.

The supplied Abyssal Lich still independently recalculates **1,892 Life / 6,091 ES**,
with saved totals removed. Jewel, chest, Darkness Enthroned and current Ingenuity
comparisons are preserved. The engine download is about 4.2 MB gzip; calculations
and imported build data stay on your device. Only passive tree `0_5` is supported.

## Open on Safari

The Pages workflow deploys the generated `dist/` directory. In this repository's
**Settings → Pages → Build and deployment → Source**, select **GitHub Actions**.
Run/re-run the **Build, test and deploy browser app** workflow. Its deployment
output provides the live HTTPS address. No hosting account or API key is needed.

The expected address for this repository is
`https://thedraconicpanda.github.io/poe2-build-lab/` **after the Pages workflow succeeds**.
A prepared workflow or Git push alone does not establish a successful deployment.
See [deployment and Safari validation](docs/BROWSER.md).

## Use and save

1. Paste a PoB2 export code, or choose an XML/text export from Files, then Import.
2. The original export and current comparison inputs are saved in this browser's
   IndexedDB. Use **Save current** after changing settings you want to keep.
3. Use **Recalculate baseline** or **Compare upgrades**. Work runs in a worker so
   the page remains responsive; **Cancel calculation** stops the worker.
4. Use **Export backup** to save JSON to Files, and **Restore backup from Files**
   to restore it on this or another device. Restores preserve existing saved copies.
5. Once offline caching finishes, you can reopen the page and recalculate offline.
   Safari can optionally add the site to the Home Screen.

Browser storage belongs to this device/browser/site address. Private browsing,
clearing website data or storage eviction can remove it; a Files backup is a
separate copy. Saves do not sync through GitHub or leave your browser. Closing a
tab stops an in-progress calculation. Low-memory devices may need to close other
heavy tabs before loading the engine. Nothing runs on your PC when using Pages.

## Build or preview the static site

Build-time tools: Node 24, Python 3.12+, Git. No native Lua compiler is needed.

```sh
npm ci
npm run build
npm run serve
```

`npm run build` packages exact PoB source revision
`bb52d6b368307457eb9c54bb13f1829993d390b1`, retaining licences and recording its
asset checksum. It generates static files under ignored `dist/`. The preview is
only a file server; all calculation happens in the browser. Use an HTTP(S) origin;
opening `index.html` directly from Files is not supported by worker/cache APIs.

## Validation

With the static preview running and Playwright installed:

```sh
python tests/browser_static_smoke.py
python tests/browser_engine_parity.py
# Safari-engine runs (WebKit must be installed):
BROWSER_ENGINE=webkit python scripts/ci_browser_tests.py
```

The Pages workflow installs WebKit and gates deployment on these tests. The local
static smoke covers import, on-device baseline/scenarios, touch layout, local
save/reload, JSON backup restoration and an **offline recalculation after reload**.
Parity tests cover all prior fixture vectors, rune tiers, ring-side differences,
poisoned saved totals and Unicode item names, and assert that no POSTs are sent.

`app.py`, `engine/` and the native Python tests are retained as a reference oracle
for regression work. They are **not deployed** to Pages. To run those developer
reference tests, use `python scripts/setup_engine.py` first, then
`python -m unittest discover -s tests -v`.

## Scope and known limits

Engine/snapshot results are validated for the supplied build, not all 0.5.5 rules.
Spirit remains diagnostic (the original engine gives 38 unreserved, export 36),
and comparisons show insufficient-Spirit and unparsed-modifier notes. Chest ES
holds the rest of that item fixed. Ingenuity templates cover the current separate
20–30% per-ring version. Game acceptance remains pending a before/after upgrade
check; a single controlled jewel change is the agreed inexpensive first check.

See [browser architecture](docs/BROWSER.md), [baseline](docs/BASELINE.md),
[scenarios](docs/SCENARIOS.md), [interactions](docs/INTERACTIONS.md), and
[third-party notices](engine/THIRD_PARTY.md). The app is not affiliated with GGG.
