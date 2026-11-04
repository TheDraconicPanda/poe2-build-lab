# Browser-only architecture, deployment and Safari

## What changed

The primary app is static. No `/api` calculation request, proxy, tunnel, local PC
service, login, analytics or cloud save is involved. GitHub Pages serves the UI,
WASM runtime and pinned engine/data assets. Builds and comparison inputs live in
IndexedDB on the device. Exported backups are ordinary JSON files Safari can save
to Files. A scoped service worker caches the static assets for offline use.

The former Python/native engine remains an optional **developer reference**, not
a requirement for opening the app. Python runs during site packaging on Actions;
it does not run in Safari or need a hosted backend.

## Engine port and scope

`wasmoon@1.16.0` supplies the Lua 5.4 WASM runtime. The existing PoB source snapshot
is packaged at build time. The worker verifies a SHA-256 checksum before mounting
its in-memory virtual filesystem, creates an isolated Lua state for each result,
and closes it afterward. Calculations run away from the UI thread. Cancellation
terminates the worker. Imported XML and scenario metadata are temporary virtual
files; no device filesystem paths are exposed to the engine.

`build_browser.py` expands the pinned source's newer LuaJIT syntax (compound
assignment, optional access, `continue`, one lambda) into equivalent Lua 5.4
syntax in generated assets. It leaves the original checkout untouched. A local
`table` binding fixes the upstream JSON encoder's Lua-5.4 environment access.
The first empty-build frame is deferred until an actual import is loaded.

`browser/compat.lua` provides 32-bit bit operations, Lua-5.1-compatible numeric
formatting and headless UTF-8 GUI helpers. The UTF-8 pattern wrappers are for the
unused desktop controls/numeric formatter, not a replacement desktop UI; the
browser owns its text inputs. Integer display coercion and nonfinite placeholder
formatting do not change Life/ES arithmetic. UTF-8 item-name round-trips are tested.
PoB's Life/ES calculations, item modifiers, passive data, conversions and rounding
remain in the upstream modules. This is still a build-specific validated port,
not proof of parity for every PoB feature or arbitrary build.

The initial successful probe reproduced 1,892 / 6,091 in about five seconds on the
development machine, with about 187 MB of Lua state memory **plus** runtime/data
and browser overhead. These are not measurements of an iPhone. Real device speed
and memory must be checked on the user's Safari.

## Persistence and offline behavior

Imports auto-save the original export and the currently selected comparison.
Successful comparisons auto-save their input settings. **Save current** explicitly
saves changed fields/name without running a calculation. Results are recomputed,
not restored as if newly verified. No arbitrary local folder access is assumed.

JSON backups contain versioned build exports, names and scenario settings.
Restoration validates imports and scenarios before writing them and gives restored
copies fresh IDs when needed. Browser-storage failures are shown, with file-backup
fallback. Device/site storage is not GitHub sync. Browser eviction/private-mode
limits remain applicable. Export a backup for a durable user-controlled copy.

All necessary calculation assets are cached before offline-ready is reported.
Caches and IndexedDB names are scoped to this site's path, preserving other apps
hosted under the same GitHub Pages origin. Asset changes update the cache version.
Offline tests reload the page, restore the saved build from IndexedDB, create a
fresh worker and recalculate the baseline while the context is offline.

## GitHub Pages

`.github/workflows/pages.yml` builds, tests and deploys `dist/`. No API credentials
are included in source. Build downloads are pinned; the published bundle retains
PoB2, Wasmoon and Lua licence notices. All runtime assets are served from this site.

If Pages is not enabled, set repository **Settings → Pages → Source → GitHub
Actions**, then run/re-run the workflow. GitHub's configure-pages action explicitly
requires an additional administrative token for automatic first-time enablement;
the default Actions token is sufficient for deployment **after** Pages is enabled.
The project does not ask for or store a PAT to work around that account setting.

The expected project URL is `https://thedraconicpanda.github.io/poe2-build-lab/`
when the deployment succeeds. The path prefix matters; asset references, workers,
manifest and service-worker scope use relative paths. Do not infer deployment
success from a repository commit or a build artifact alone.

## Safari validation

Target: Safari 17+ on an iPhone/iPad, with WASM, IndexedDB, module workers and
DecompressionStream. Form text is at least 16 px to avoid iPhone focus zoom, touch
targets are at least 44 px, and tables scroll within the page. No Chromium-only
File System Access API is used. JSON download/upload works with Files.

Local Chromium static tests cover the full UI and offline persistence. Direct local
WebKit installation was blocked by the cloud network policy at the official browser
download hosts. The GitHub workflow installs WebKit on its runner and gates deploy
on smoke and parity tests there. Until that run and an actual iPhone test complete,
do not describe this as device-verified Safari support.

After deployment: open the HTTPS URL in Safari, import your PoB, recalculate the
baseline, change Eagle Vessel 16% → 20%, save/export a backup, close/reopen Safari
and reload the saved build. Expected Life/ES remain 1,892 / 6,091 originally and
1,892 / 6,129 for that controlled jewel modifier change. Confirm the real replacement
jewel has no other changed Life/ES-relevant modifiers before using that game test.
