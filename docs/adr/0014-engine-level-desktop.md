# ADR 0014: Engine-level desktop, rebuilt gnome-shell first

Status: accepted (2026-09-28). It records the owner's answers of 2026-09-28 to the
decision sheet (`docs/reviews/2026-09-28-review.md` §5). It supersedes ADR 0011 and
amends ADR 0002 and ADR 0007. Decision 22 (kernel and dGPU) is
[ADR 0015](0015-cachyos-kernel-and-nvidia.md). Amended 2026-09-29: the owner deleted
Windows before S4 (ROADMAP W1), so under "Boot handoff" only the case after Windows
applies: bootloader updates are on, and Ubuntu, not Windows, starts from the firmware
boot menu (ARCHITECTURE §5.5). Amended 2026-10-21: the flat Apex Facets wallpaper
replaces Apex Aurora, and no surface uses a gradient. Amended 2026-10-21
again: the Files redesign adds nautilus patches 0004 to 0007, which raise
the nautilus budget from 160 to 400 changed lines in upstream files, and flat icons in
the `Apex` theme with nine accent-variant themes. Amended 2026-10-23: the owner's design
canvas replaces the HTML mockup and `design/SPEC.md` as the standard
([DESIGN.md](../DESIGN.md)), and the Apex Symbolic glyphs (decision 11) land in S1b.
Amended 2026-10-24: at the owner's request, Ptyxis joins the lane with the Apex
terminal series (canvas boards 32 and 33, ROADMAP T1 and T2). Amended 2026-10-24 again:
the owner chose to patch nautilus and gnome-control-center rather than write new apps
(ROADMAP F and C), and decision 27 makes one exception, Power's "Graphics and Display"
group (board 24).

## Context

- The owner's defining requirement is the design. Since 2026-10-23 that is the owner's
  design canvas, described in [DESIGN.md](../DESIGN.md); this ADR was written against the
  earlier HTML mockup and its spec.
- ADR 0011 refuses Shell themes, gtk.css, icon-theme swapping and a patched
  gnome-control-center (ADR 0011:27), and leaves the shell to one later extension
  (ADR 0011:26). Today the desktop is stock GNOME 51 plus five vendor defaults
  (`90_apex.gschema.override:9-32`).
- One premise of ADR 0011 is false: Shell themes need no extension (ADR 0011:12).
  gnome-shell reads its stylesheet from `resource:///org/gnome/shell/theme/` first
  (`js/ui/main.js:414-435`). The other premises hold: libadwaita has no theme API,
  accents are a fixed set of nine, and gnome-control-center has no panel plugin API
  (`shell/cc-panel-loader.c:86-119`).

The owner's answers that shape this ADR (2026-09-28):

| # | Answer |
|---|---|
| 1 | A rebuilt gnome-shell is the primary mechanism, not an overlay. ADR 0011 is superseded. |
| 2 | The Apex SCSS enters the gnome-shell package through an `@import` hook. sassc runs at build; the shipped CSS is deleted in `%prep`. |
| 6 | Super+Space opens Spotlight. Input switching moves to another key (§ Keys). |
| 14 | Dynamic blur on every drawn glass surface (bar, dock, popovers, scrims), with the design's saturation. It must hold 90 Hz at 2880×1800 on the Vega 7 iGPU. Reduce Transparency is the off switch. |
| 17 | Black splash with the Apex wordmark; GRUB menu hidden unless the last boot failed. Dual boot now; the owner removes Windows later. |
| 22 | The CachyOS GCC kernel, with NVIDIA open modules built for exactly that kernel (ADR 0015). The RTX 3050 is used. |
| 26 | Build the design's engine-level details now (then listed in `design/SPEC.md` §8), with the rebuilt packages they need. Items another decision settles keep that decision's default: 4, 5, 8, 10, 11, 19 and 27. The privacy indicators in the status pill stay. |
| Others | The recommended defaults, including 18: hold limits of 72 h for a security update and 14 days otherwise. |

Facts this design rests on. Upstream line references are to the GNOME 51.0 tags
(2026-09-14), mutter 51.0 and libadwaita 1.10.0; web facts were checked on 2026-09-28.

- Fedora's f45 `gnome-shell.spec` builds 51.0 with one patch and `%autosetup -S git`,
  has no `BuildRequires: sassc`, and requires `mutter >= 51.0`
  (`gnome-shell.spec:25, 36, 88, 178`;
  https://src.fedoraproject.org/rpms/gnome-shell/raw/f45/f/gnome-shell.spec).
- The release tarball ships compiled `gnome-shell-{light,dark,high-contrast}.css`, made
  by a dist script (`meson.build:351`). `data/theme/meson.build:52` runs sassc only when
  the CSS is missing. Deleting the shipped CSS in `%prep` is what makes the hook work.
- The entry files only set `$variant` and `$contrast`, then import `_colors`,
  `_drawing`, `_common` and `_widgets` (`data/theme/gnome-shell-light.scss:1-7`).
- The JS modules compile into one gresource (`js/meson.build:4-9`) that is linked into
  libshell (`src/meson.build:215`). A second compiled resource links the same way.
- `ShellBlurEffect` has three properties: radius, brightness and mode
  (`src/shell-blur-effect.c:96-98`). In background mode it re-blurs on every paint
  (`:597-617`), forces opacity 255 (`:642`), and never downscales a texture whose short
  side is under 256 device px (`:53, 290-310`). Its only stock user is the unlock
  dialog, in actor mode (`js/ui/unlockDialog.js:789, 803-816`).
- Blur my Shell documents black-rectangle artifacts from clipped redraws. Its fix turns
  clipped redraws off, which slows the whole system even with no blur on screen
  (https://github.com/aunetx/blur-my-shell/blob/master/README.md).
- GNOME Shell had five point releases in the 50 cycle, from 50.1 on 2026-04-14 to 50.5
  on 2026-09-15 (https://gitlab.gnome.org/GNOME/gnome-shell/-/tags). A rebuilt shell is
  rebased about once a month.
- One maintainer carries the result. Ubuntu carries 78 gnome-shell patches with a team.

## Decision

The design is the standard ([DESIGN.md](../DESIGN.md)). A deviation needs a hard reason (physics, safety, a real
conflict, or a large engine cost) and an owner decision. The approved ones are listed
under Deviations.

### Mechanism per component

| Component | Mechanism | Signed by | Budget |
|---|---|---|---|
| gnome-shell | Fedora f45 SRPM rebuilt in the lane. Theme: the Apex SCSS through the `@import` hook. Behaviour: the Apex layer, in-tree under `js/ui/apex/`. Glass: a `ShellBlurEffect` patch. | Apex RPM key | Hook hunks: at most 450 changed lines in at most 33 upstream files. C: at most 300 changed lines in `src/shell-blur-effect.{c,h}`. |
| Dock | ApexDock, part of the Apex layer, a subclass of upstream `Dash` (`js/ui/dash.js:305`) | (gnome-shell) | About 700 to 900 lines of Apex JS; its `dash.js` hooks count in the shell budget |
| mutter | Fedora binary, pinned to the exact EVR gnome-shell was built against; mirrored unmodified into `[apex]` | Fedora | 0 patches |
| libadwaita | Fedora SRPM plus one patch: the window radius follows `apex.css` live | Apex RPM key | 1 patch, at most 80 changed lines |
| GTK 4 | stock | Fedora | 0 |
| gnome-control-center | Fedora SRPM plus 3 patches: the Apex Desktop panel; coloured sidebar tiles in the design's order; the Software Updates row and page | Apex RPM key | At most 150 changed lines in upstream files |
| nautilus | Fedora SRPM plus up to 7 patches for seven features: the disk-usage footer; the item-count bar; a 72 px grid zoom level; the details pane; the recent strip; the search chips; the view toggle group. Features that need no upstream line hang off one window hook and get no patch file | Apex RPM key | At most 400 changed lines in upstream files. The Apex widgets are added files under `src/apex/` and do not count. |
| gdm | stock. Its greeter runs the rebuilt shell in the gdm mode: Apex CSS, stock JS. | Fedora | 0 |
| Plymouth | stock, plus the `apex` script theme and the `apex-twostep` fallback theme (data files) | Fedora | 0 |
| Ptyxis | Fedora SRPM rebuilt in the lane, plus the Apex terminal series: a sessions sidebar grouped by host, container and ssh, with each session's status; pane headers and two-pane splits. The colours stay the user palette that `apex-session-agent` writes. | Apex RPM key | At most 400 changed lines in upstream files, in hook hunks. The Apex widgets are added files under `src/apex/` and do not count. |
| Icons, fonts, wallpaper, defaults | `apex-desktop` noarch RPM: the `Apex` icon theme (app icons from a pinned Colloid commit; flat folder and file icons from Apex templates, with nine `Apex-<accent>` folder themes), fontconfig `ss03`, JetBrains Mono, Apex Facets, `90_apex.gschema.override`, the Apex schema | Apex RPM key | n/a |
| Kernel and NVIDIA | ADR 0015 | Apex RPM key | ADR 0015 |

The budgets are review rules, not build checks. A change that would exceed one amends
this ADR first. Build steps and patch-queue commands are in ARCHITECTURE §4.1 and §7.4.

### The gnome-shell package

Repository layout:

- `desktop/shell/` holds the Apex-owned sources. It ships as `Source1`, a `git archive`
  of the directory, and is part of the content key. It is GPL-2.0-or-later, like
  gnome-shell, so any piece can be offered upstream.
  - `js/ui/apex/**`: the Apex layer.
  - `data/theme/apex/**`: `_apex-tokens.scss`, `_apex.scss` and its partials,
    `_apex-structure.scss`, assets, and a `meson.build` that lists them as dependencies.
  - `apex.gresource.xml`, with the prefixes `/org/gnome/shell/ui/apex`,
    `/org/gnome/shell/theme/apex` and `/org/gnome/shell/theme/stock`.
- `packaging/pkgs/gnome-shell/` holds `pkg.env` (`source=fedora-srpm`, `on_fail=hold`,
  hold family `gnome-shell`), `spec-edit`, `series` and `patches/`.

`spec-edit` makes anchored insertions and fails when an anchor is missing. It survives
Fedora's spec churn better than a diff of the spec. It adds:

- `Source1` and `BuildRequires: sassc`;
- after `%autosetup`: unpack `Source1`; move upstream's `gnome-shell-light.css` and
  `gnome-shell-dark.css` to `data/theme/apex/stock/`; delete
  `gnome-shell-high-contrast.css`. Meson then finds no CSS, and sassc compiles all
  three entry files with their hooks. Upstream's own compiled sheets become the
  safe-mode sheets;
- `BuildRequires: mutter-devel = E:V-R` and `Requires: mutter%{?_isa} = E:V-R`, using
  the EVR in the buildroot, so the tested pair moves together;
- `.apexN` on `Release`.

The series applies through the spec's own `%autosetup -S git`, so there is no fuzz.
Patches hold hook hunks only; all logic lives in `desktop/shell/`. There is one patch
per concern, so a rebase conflict names its feature.

| Patch | Upstream files | Hunks |
|---|---|---|
| 0001-build | `js/meson.build`, `src/meson.build`, `data/theme/meson.build`, `data/theme/gnome-shell-{light,dark,high-contrast}.scss` | Compile `apex.gresource.xml` and link it next to `js_resources`; `subdir('apex')`; in light and dark, `@import "apex/apex-tokens"` after `_colors` and `@import "apex/apex"` last; in high contrast, `@import "apex/apex-structure"` last, so Apex-owned actors keep their geometry with high-contrast colours |
| 0002-loader | `js/ui/main.js`, `js/ui/sessionMode.js` | A static import of `ui/apex/hooks.js`; an awaited dynamic import of `ui/apex/layer.js` in `try/catch` before `LayoutManager` is built; `enable()` at `startup-prepared`; in safe mode, stylesheets come from `theme/stock/`; `colorScheme: 'prefer-light'` for the user and unlock-dialog modes |
| 0003-blur | `src/shell-blur-effect.{c,h}` | §Glass |
| 0010-panel | `js/ui/panel.js`, `js/ui/layout.js` | Workspace dots; the status-pill filter; the 4×4 hot-corner hover zone |
| 0011-quick-settings | `js/ui/panel.js`, `js/ui/status/powerProfiles.js`, `js/ui/quickSettings.js`, `js/ui/status/network.js` | VPN after Airplane Mode; a per-item hook for On/Off subtitles; the `apex-lit` class on Power Mode, leaving `checked` stock (`powerProfiles.js:127`); two constructor hooks for board 17: the toggle menu's header subtitle on the title's row, and the active Wi-Fi row's `:checked` from the start with its lock after the name |
| 0012-message-list | `js/ui/messageList.js`, `js/ui/calendar.js` | 32 px icon column (board 34); flat list; Clear always visible, on the right; the Do Not Disturb footer switch |
| 0013-overview | `js/ui/overview.js`, `js/ui/overviewControls.js`, `js/ui/searchController.js`, `js/ui/workspace.js`, `js/ui/windowPreview.js`, `js/ui/workspaceThumbnail.js`, `js/ui/appDisplay.js` | The scrim over a clone of the desktop; thumbnails; always-visible titles, whose rows leave room for the caption and stop above the dock; the wallpaper in each workspace thumbnail; no workspace background cards; typing goes to Spotlight, or to the launcher's own pill while the app grid shows (`searchController.js:156`); the 7×88 grid |
| 0014-dash | `js/ui/dash.js` | ApexDock: fixed icon sizes, the order's tail, a full-colour Show Apps icon |
| 0015-lock | `js/ui/unlockDialog.js`, `js/ui/userWidget.js`, `js/gdm/authPrompt.js` | Single stage; blur values; the field's glass; the initial-letter avatar; "Enter Password". The patch carries the review label "unlock path". |
| 0016-motion | `js/ui/environment.js`, `js/ui/windowManager.js`, `js/ui/overview.js`, `js/ui/overviewControls.js`, `js/ui/boxpointer.js` | The EASE curve for every `ease()` that asks for it; the drawn durations |
| 0017-polkit | `js/ui/components/polkitAgent.js` | One behaviour hook after `AuthenticationDialog._init`: board 13's shield, the "Administrator" subtitle and the Details expander (action id and vendor). The fingerprint hint is upstream's info message, restyled |
| 0018-end-session | `js/ui/endSessionDialog.js` | One behaviour hook after `_updateButtons`: board 14's icon circle, Restart beside Power Off through stock's `ConfirmedReboot`, and the button row's gap and widths. The countdown keeps stock's translated text |

The plan touches 31 upstream files besides the two C files, which leaves two in
reserve. Estimate: 250 to 330 lines of hunks, about 250 lines of C, 5,000 to 6,000
lines of Apex JS, and about 1,500 lines of SCSS.

Rebase cost:

| Release | Work | Cost |
|---|---|---|
| Point (51.x), about monthly | `just pkg-rebase gnome-shell <nvr>` (`git am -3`), then the gates | 0.5 to 2 h when the series applies |
| Major (52, with Fedora 46) | Rebase the series, ApexDock and the C patch onto GNOME 52 in the `next` lane after S4 (roadmap S6, May to June 2027); from the F46 branch point (2027-02-09) an unattended F46 compose reports what breaks; re-approve changed goldens | 4 to 8 owner-days |

Dev loop:

| Change | Loop | Time |
|---|---|---|
| Apex JS, SCSS, and the hunks in upstream JS | A nested `gnome-shell --devkit` in the desktop VM with `G_RESOURCE_OVERLAYS` pointing `/org/gnome/shell/ui` and `/org/gnome/shell/theme` at the prepared tree and the sassc output (https://docs.gtk.org/gio/struct.Resource.html) | seconds |
| C | Incremental ninja in an F45 toolbox, then `bootc usroverlay` | 1 to 3 min |
| The RPM through the lane | `just pkg-build gnome-shell` (apex-lane) | 10 to 15 min |

A G1 check fails if `G_RESOURCE_OVERLAYS` or `--unsafe-mode` appears in the image's
environment or unit files.

### The Apex layer lives in-tree

The shell code is part of the gnome-shell package, not a set of extensions:

- A hook that no longer fits fails the build (a patch conflict, or G2), instead of
  doing nothing at runtime as an extension's prototype override does.
- There is no extension version gate and no coupling to `disable-user-extensions`.
- CSS, JS and C ship in one package version.
- No Apex JS runs in the gdm mode, by construction. The greeter runs the rebuilt binary
  with the Apex CSS and stock JS, so it is the canary for every shell build.

Contract:

- `hooks.js` is the only Apex module that upstream files import. It imports only GLib
  and Gio, has no side effects at load, and never throws.
- Its API: `value(name, stock)`; `run(name, ...args)`, which returns `undefined` so the
  caller runs its stock code; `safe()`.
- A provider that throws is disabled for the session and logged once. In the gdm mode
  every hook returns stock.
- Two phases. `configure` holds pure value providers and runs before the UI exists.
  `enable` builds actors at `startup-prepared`. Each feature is its own module inside
  its own `try/catch`. A feature that throws is disabled, and its hooks return stock.
- The layer looks up the Apex schema before use. A missing schema means safe mode.

Kill switches, strongest first:

| Switch | Scope | Effect |
|---|---|---|
| `apex.safe=1` on the kernel command line, or `APEX_SHELL_SAFE=1` | every session | No layer. Every hook returns stock. Upstream's stylesheets load from `theme/stock/`. The colour scheme is stock. |
| `layer-enabled=false` | one user | The same, for that user's sessions. The crash guard sets it; so can the owner. The greeter keeps the Apex CSS. |
| `disabled-features` | one user | The named features are off, and their hooks return stock. |
| `reduce-transparency` | one user | Glass off, solid tokens. |

Crash guard. GNOME's extension safety net does not cover in-tree code, so Apex adds its
own:

- The layer creates `%t/apex-shell-starting` at enable and removes it after 60 s or at
  shutdown, as the extension manager does with its own file
  (`js/ui/extensionSystem.js:53-73`).
- A user-unit drop-in, `org.gnome.Shell@.service.d/50-apex.conf`, adds
  `OnFailure=apex-shell-safe.service`. Like `org.gnome.Shell-disable-extensions.service`,
  that unit has `DefaultDependencies=no` and runs next to the session shutdown.
- It sets `layer-enabled=false` when the file exists, or when this is the second shell
  failure on the booted deployment (a counter in `$XDG_STATE_HOME/apex/`, keyed by the
  deployment digest). It leaves a marker, and `apex-session-agent` then offers "Turn the
  Apex desktop back on".
- Exit status 1 is not a failure for that unit (`SuccessExitStatus=1`,
  `data/org.gnome.Shell@.service.in:22`). gnome-shell exits 1 when `init.js` throws
  (`src/main.c:697-721`), which only the static import graph can cause. G2 loads that
  graph on every build.

What catches a broken shell:

| Failure | Caught by | Result |
|---|---|---|
| A patch conflict, a sassc error or a C build error | the lane | The family is held; nothing is published. |
| A syntax or import error in the static import graph | G2, which runs the headless shell from the built image | Held. |
| A hook throws on one code path | `hooks.js` | Stock at that call site; logged once. |
| A feature throws at enable | the layer | That feature is off for the session. |
| The shell dies within 60 s of enable, or twice on one deployment | the crash guard | The next login runs stock JS and CSS; the agent offers to turn Apex back on. |
| The shell cannot start in any mode (a C crash, a broken `main.js` hunk) | the boot assessment's session check: the greeter is never active for 20 s (ADR 0009; `crates/apex-boot/src/bin/apex-boot-assess/session.rs:1-16`) | On an armed boot, counted rollback and the digest on the denylist. On an unarmed boot, a report, and the GRUB menu shows at the next boot. |
| The lock screen breaks | the G4 lock and unlock matrix, before publishing | The hooks fall back to the stock two-stage flow. `loginctl unlock-session` from a VT or SSH still unlocks (`js/ui/screenShield.js:153-155`). |
| Glass is too slow | the S2b and S3a measurements | Reduce Transparency, or `disabled-features=['glass']`. |

### Hold on failure

A Fedora update to a rebuilt package is absorbed automatically when the series applies
and every gate passes. Otherwise the family is held (decision 18).

| Hold family | Members | Stock fallback at the limit |
|---|---|---|
| gnome-shell | gnome-shell, gnome-shell-common, mutter, mutter-common | Fedora's gnome-shell and mutter: stock GNOME Shell with no Apex layer, theme, dock or glass until the rebase. Icons, fonts, wallpaper, window radius and the Settings panel stay. |
| libadwaita | libadwaita | Fedora's libadwaita: the radius changes at the next app start |
| gnome-control-center | gnome-control-center, its `-filesystem` subpackage | Stock Settings: no Apex Desktop panel, stock sidebar (`degraded=settings`) |
| nautilus | nautilus and its subpackages | Stock Files (`degraded=files`) |
| ptyxis | ptyxis | Stock Ptyxis: tabs, no sessions sidebar, pane headers or live palette reload (`degraded=terminal`) |

- `rpms.lock` does not advance for the family, and the last good builds keep winning
  through `[apex]` priority 1.
- mutter is held with the shell. The lane mirrors the Fedora-signed mutter RPMs it built
  against into `[apex]`, unmodified, because Fedora's updates repository keeps only the
  newest build. `[apex]` trusts the Apex RPM key and Fedora's key.
- Limits: 72 h when the newer Fedora build of any member is a security update, 14 days
  otherwise. At the limit the owner rebases or ships the stock fallback.
- The build prints every hold and whether it blocks a security update. The image label,
  `apexctl status` and the Settings Updates page show it. The build opens no issue.
- Nothing degrades a design package to stock on its own.
- G4 (install, boot to GDM, log in, lock and unlock) runs before `just publish` whenever
  the gnome-shell, mutter or gdm NVR in `rpms.lock` changes.
- libfprint degrades instead of holding (ADR 0006). The kernel pair holds under
  ADR 0015's rules.

### Escalation

Escalation now means one of these. Each is an owner decision, with a measured need or a
named design detail:

- **mutter joins the lane with a patch.** The one candidate today is exported
  redraw-clip expansion for glass (§Glass, lever 3). mutter then leaves Fedora's
  signature. It is already in the gnome-shell hold family.
- **Another package is rebuilt**, for example GTK, or a spec-only rebuild under
  ADR 0007.
- **A budget above would be exceeded.**
- **A hook conflicts at two consecutive point releases.** The owner then picks one:
  upstream the change, reshape the hook, or drop the feature.

### Glass everywhere (decision 14)

Every glass surface of the design samples what is really beneath
it, live, and pays only when that changes.

| Surface | σ (CSS px) | Saturation | Mode |
|---|---|---|---|
| Top bar | 24 | 1.6 | background |
| Dock | 28 | 1.8 | background |
| Quick Settings, calendar, toast | 30 | 1.8 | background |
| Spotlight | 34 | 1.8 | background |
| Overview scrim | 36 | 1.5 | actor mode over a clone of the desktop |
| Launcher scrim | 40 | 1.6 | as the overview |
| Lock background | 30 | 1.3 | actor mode over the wallpaper, then the drawn `rgba(8,10,20,.34)` overlay |
| Lock password field | 20 | none | background |
| Edge-tiling preview | 20 | 1.6 | background, on a glass actor below the preview and inset to its inner rect: the effect blurs its actor's whole box, and mutter sizes the preview to the tile, clear border included |

- The radius in device px is 2 × σ × scale, since `ClutterBlur` uses σ = radius / 2
  (mutter `clutter/clutter/clutter-blur.c:362`).
- The derived transient surfaces ([DESIGN.md](../DESIGN.md)) take the glass of the drawn surface they
  copy.
- **Scrims.** GNOME hides `window_group`, which holds the wallpaper and the windows,
  while the overview shows (`js/ui/layout.js:984-988`). The design's scrims blur the
  desktop as it was, windows included. The layer places a non-reactive
  `Clutter.Clone` of `window_group` under the scrim and blurs it in actor mode. Actor
  mode keeps its result until the actor is dirty (`shell-blur-effect.c:610-611`), so a
  still desktop costs one blur per overview open. Actor mode does not grow the actor's
  paint volume by the blur radius, so a window's own damage would re-blur only its
  rectangle and leave the halo around it stale. The glass manager forwards window damage
  (`damaged`, moves and restacks) to the whole scrim in the same frame, and that is what
  keeps the halo correct; growing the paint volume in C has no room in 0003's 300 lines.
  A G2 pixel test proves that a window damaged under the scrim updates the blur, and
  that without the forwarding the halo stays stale.
- **One scrim per monitor.** Each monitor gets its own scrim, the size of that monitor
  and laid out in its first frame, over a clone of `window_group` moved by the
  monitor's origin. Each blurs at its monitor's resource scale. The scrims are rebuilt
  on `monitors-changed`. One stage-wide scrim would blur at the highest scale, so a
  scale-1 external display would cost four times its pixels, and it would also blur
  the stage corners no monitor shows. Modelled cost per scrim re-blur
  (`0014-blurcost.py`):

  | Layout | One stage-wide scrim | A scrim per monitor |
  |---|---|---|
  | The panel alone, scale 2 | 4.71 ms | 4.71 ms |
  | The panel and a 1920×1080 display, both at scale 2 | 7.84 ms | 6.59 ms |
  | The panel at 2 and a 1920×1080 display at 1 | 13.18 ms | 6.60 ms |

  The stage-wide scrim missed the 11.1 ms frame at 90 Hz with a mixed-scale
  external display; per monitor it fits. The laptop protocol measures the real cost.
- **Glass over glass.** The bar and the dock over a scrim blur the scrim's result, as
  drawn. The scrim is cached, so this costs about 0.3 ms per scrim change.
- **Shadows.** The `shadows` feature's second layer is an actor above its surface,
  clipped to outside the rounded shape, so a glass surface never blurs its own shadow.

Patch 0003 to `ShellBlurEffect`. At default property values the effect is
byte-identical to Fedora's, so the unlock dialog and any other caller are unchanged.

| Item | Property (default) | What it does |
|---|---|---|
| a | `saturation` (1.0) | A snippet in the final pass: `c.rgb = clamp(mix(vec3(dot(c.rgb, vec3(0.213, 0.715, 0.072))), c.rgb, s), 0.0, c.a)`. This is CSS's `saturate()` matrix (https://www.w3.org/TR/filter-effects-1/), applied after the blur as in CSS, in the pass that already applies brightness. It adds no pass. |
| b | `corner-radius` (0) | Antialiased rounded-rect coverage in the same pass, for the drawn radii 18 to 26 |
| c | `follow-opacity` (false) | Background mode uses the actor's paint opacity. Stock forces 255 (`:642`), which pops an opaque blurred rectangle in at the start of every fade. |
| d | `fine` (false) | Downscale to the smallest power of two with σ / ds ≤ 4 and a texture side of at least 4 px, without the 256 px floor. The reduction is box-filtered in one pass whose taps sit on 2×2 texel corners, the exact mean of the ds×ds footprint that chained halving gives (Cogl's mipmaps go stale after a blit), so moving content does not shimmer. |
| e | `fine` | In background mode, re-blur only when the frame's redraw clip covers the whole actor box. Otherwise draw the last result, and queue a redraw only when the clip reaches into the box: a clip that meets only the paint volume (a box-shadow) changed nothing behind it. A blit then never reads pixels this frame did not repaint, which is where the documented artifacts come from, and two glass surfaces whose shadows reach each other's boxes never queue each other's redraws (G2's load cases found that loop at about 58 Hz). Correctness never depends on JavaScript finding every source of damage. |
| f | `fine` | The last result is kept per stage view. |

The glass manager (`js/ui/apex/glass/`):

- keeps a registry of glass surfaces, with pause rules: the bar's glass is off while
  the bar is solid; the dock is not painted while hidden; chrome is hidden under
  fullscreen windows; popovers blur only while mapped;
- forwards damage, for latency only: a window actor's `damaged` signal (mutter
  `src/compositor/meta-window-actor.c:250-262`), its position, size and stacking
  changes, and background changes queue a redraw of every glass box they touch, the
  box alone (`queue_redraw_with_clip`), never its paint volume, whose shadow would
  re-blur the glass beside it. The re-blur then lands in the same frame. A missed
  source costs one frame of lag, never a wrong frame;
- turns glass off for Reduce Transparency (effects removed; a root style class swaps
  the tokens to their solid values), for high contrast, and for
  `disabled-features=['glass']`.

Cost model. It counts Gaussian taps (`1 + 2·ceil(1.5σ)` per pixel per pass,
`clutter-blur.c:90`) and framebuffer bytes, at 25 GB/s and 25 Gtaps/s effective, half
of the Vega 7's peak. It is committed as [`0014-blurcost.py`](0014-blurcost.py). It is a model, not
a measurement.

| Surface, per re-blur | Stock (ms) | Patched (ms) |
|---|---|---|
| Top bar, 2880×64 device px (σ 48 px, never downscaled by stock) | 2.35 | 0.17 |
| Dock, about 1200×124 (σ 56 px) | 2.18 | 0.14 |
| Quick Settings | 0.69 | 0.58 |
| Calendar | 1.53 | 1.28 |
| Spotlight | 1.33 | 1.07 |
| Toast | 0.65 | 0.04 |
| A full-screen scrim or the lock background | about 4.6 | about 4.7; bandwidth-bound, cached while still |

- Idle cost is zero: nothing repaints.
- The worst steady cases: a video under the dock re-blurs it at the video's frame rate,
  about 0.15 ms per frame; a video under the overview scrim costs about 4.7 ms per video
  frame while the overview is open.

Acceptance, measured on the laptop (battery, balanced profile, 90 Hz, 2880×1800),
against the same run with Reduce Transparency: scenarios A and B first in S2b, every row
in S3a, and again after any change to patch 0003 or the glass manager:

| Row | Pass |
|---|---|
| Sysprof, 60 s of mutter frame marks, in three scenarios. A: a 1080p60 video in a window that overlaps the dock, with Quick Settings open over it. B: a window dragged under the dock and the popovers for 30 s. C: 20 overview and app-grid toggles over a playing video. | p99 frame time ≤ 11.1 ms; dropped frames ≤ 1 %; p50 within 0.5 ms of Reduce Transparency |
| amdgpu `gpu_busy_percent`, sampled at 10 Hz in scenario A | mean delta ≤ 5 points |
| Power: `upower` energy rate every 10 s, three alternating 10-minute runs each, brightness 50 %, Wi-Fi off | idle delta ≤ 0.3 W; scenario A delta ≤ 0.5 W |
| Correctness | the G2 pixel test passes (per channel: max 4/255 more than ds/2 px inside the box, max 12/255 within ds/2 of its edge, mean 1/255 over the box; llvmpipe as the reference renderer); 5 minutes of the glass stress show no stale or black frame; a `CLUTTER_PAINT=damage-region` run shows the forwarded damage covering each glass box |

If a row fails, the levers in order:

1. ds × 2 on the failing surface.
2. Under the power-saver profile, ds × 2 everywhere, and the scrims re-blur at most at
   30 Hz.
3. The one mutter change: exported redraw-clip expansion, which removes the extra frame
   that item e queues (Escalation).
4. The owner decides with the numbers, for example cached glass on one surface.

Reduce Transparency always turns glass off.

### Keys: Super+Space and input switching (decision 6)

| Action | Keys | Where it is set |
|---|---|---|
| Spotlight | Super+Space | `toggle-spotlight` in `io.github.apex_linux.Apex.Desktop.Keybindings` |
| Next input source (English ↔ Vietnamese Telex) | Super+Alt+Space; XF86Keyboard | `org.gnome.desktop.wm.keybindings switch-input-source`, in the vendor override |
| Previous input source | Shift+Super+Alt+Space; Shift+XF86Keyboard | `switch-input-source-backward`, in the vendor override |
| Overview | Super tap; hot corner; Activities pill; three-finger swipe | stock |
| Launcher | Super+A | stock |
| Window menu | Alt+Space | stock |
| Ctrl+Space | not bound | left to IDEs and editors |

- GNOME binds Super+Space and Shift+Super+Space to input switching, and Alt+Space to
  the window menu (gsettings-desktop-schemas 51.0,
  `org.gnome.desktop.wm.keybindings.gschema.xml.in:146-148, 330-339`). The override
  moves the input bindings, so Super+Space is free.
- Super+Alt+Space keeps input switching in the Super+Space family and keeps GNOME's
  hold-and-repeat switcher popup, because the indicator binds the key through
  `Main.wm.addKeybinding` (`js/ui/status/keyboard.js:349-363`). No GNOME 51 default in
  the wm, mutter, shell or media-keys schemas uses it, and IDEs do not bind it. With two
  sources, forward and backward both toggle.
- The layer registers Spotlight with `Main.wm.addKeybinding(name, settings,
  Meta.KeyBindingFlags.NONE, Shell.ActionMode.NORMAL | Shell.ActionMode.OVERVIEW,
  handler)` (`js/ui/windowManager.js:1105-1110`) and removes it on disable.
  `/usr/share/gnome-control-center/keybindings/60-apex.xml` lists it, so Settings >
  Keyboard shows it and can change it.
- The override is system-wide, so the greeter and the lock screen switch input with
  the same keys. `per-window=true` stays, so a terminal keeps English. The en/vi
  indicator stays in the bar; it is the only visible Telex state.
- A G1 check fails when two default bindings share a combination across the wm,
  mutter, shell, media-keys and Apex schemas.
- Rejected: the xkb toggles `grp:ctrl_shift_toggle` and `grp:alt_shift_toggle`. mutter
  consumes the `ISO_Next_Group` press (mutter `src/core/keybindings.c:474-558,
  1627-1654`), and while Ctrl is held Shift stops acting as Shift. That breaks
  Ctrl+Shift+C, V, T and P in Ptyxis and editors. Ctrl+Space for input: IDE completion.
- Optional, not the default: Caps Lock as a one-key toggle
  (`xkb-options ['grp:caps_toggle']`; Shift+Caps Lock keeps Caps Lock).
- Checked in the desktop VM in S1b: IBus does not act on its own `<Super>space`
  trigger under GNOME. Checked on the laptop in S1d: Super and Alt sit next to each
  other on the M7400QC's bottom row.
- Text: the search tooltip reads "Search (Super+Space)", and the first-login toast
  "Press Super+Space to search".

### Boot handoff (decision 17)

- The Plymouth `apex` script theme draws the drawn splash: black, the diamond and the
  Apex wordmark, a 160×3 bar with round ends, and its own LUKS prompt. The two-step
  `apex-twostep` theme stays installed as the fallback. Esc at boot shows Plymouth's
  text view, which always shows the passphrase prompt. The look is boards 01 and 30
  ([DESIGN.md](../DESIGN.md)).
- The GRUB menu stays hidden unless the last boot failed. Esc, F4 or Shift during the
  hidden timeout shows it. bootupd's static `grub-static-pre.cfg` always shows the menu
  for 1 s, so a static snippet, `07_apex-menu.cfg`, reads the previous boot's
  `apex_ok` and hides the menu only after a confirmed boot (ARCHITECTURE §5.5; an S4
  spike). Fedora's `menu_auto_hide` does not apply: bootupd's static config does not
  carry it, and `boot_success` needs a writable `/boot`.
- While Windows shares the ESP (S4): Windows starts from the firmware boot menu (Esc at
  the ASUS logo). GRUB gets no Windows entry, because a chainload changes what the TPM
  measures (`docs/INSTALL.md:420-423`). Bootloader updates stay off.
- After the owner removes Windows: the Windows rows leave the S4 checks, bootloader
  updates are turned back on, and Secure Boot becomes possible (ADR 0015 §7) without a
  shared ESP's SBAT and BitLocker risks.

### App chrome, style and Flatpak

- Accents stay libadwaita's nine. There is no arbitrary RGB.
- Shell surfaces use the design's tokens. App chrome keeps libadwaita's colours and
  metrics (decision 4).
- Window radius 14, as drawn (decision 5). Maximised, tiled and fullscreen windows stay
  square.
  - `apex-session-agent` writes `~/.config/gtk-4.0/apex.css` (the value and the `0px`
    resets, [DESIGN.md](../DESIGN.md#settings-contract)) and imports it from `gtk.css`. GTK reads `gtk.css` once per
    process.
  - The libadwaita patch loads the same file into a provider at
    `GTK_STYLE_PROVIDER_PRIORITY_USER + 1` and reloads it when a `GFileMonitor` reports
    a change. Host apps then follow a radius change live, and a stale copy loaded at
    user priority never wins. libadwaita reads no Apex schema, so no GTK app depends on
    Apex being installed. The file is user-writable, as `gtk.css` already is, so this
    adds no trust boundary.
  - Flatpak apps use their runtime's libadwaita. A system Flatpak override grants
    `xdg-config/gtk-4.0:ro`, so they read `apex.css` at start if the Bazaar spike
    passes. Otherwise they keep 15 px corners (decision 5).
- Colour variables never go into user CSS: GNOME Text Editor recolours at `THEME+1`,
  and a user rule would flatten it.
- Light is the default, as drawn. Patch 0002 sets the user and unlock-dialog modes to
  `colorScheme: 'prefer-light'`, which maps `color-scheme 'default'` to the light
  stylesheet (`js/ui/main.js:437-452`; stock is `'prefer-dark'`,
  `js/ui/sessionMode.js:25`). The stock Dark Style toggle and Settings > Appearance
  write `'default'` for light, so they now work unchanged. The vendor override no
  longer sets `color-scheme`, `apex-session-agent` does not rewrite it, and
  gnome-control-center needs no Appearance mapping.
- The gdm mode keeps `'prefer-dark'`. The greeter rules are the same in both variants.
- The design's apps ship as image RPMs where Fedora packages them. Software is Bazaar, a
  Flathub app with no Fedora package. Other Flatpak apps keep their own chrome.

### Settings

- One schema, `io.github.apex_linux.Apex.Desktop`, with one child schema,
  `.Keybindings`, holds only keys with no upstream home. The dock's keys live there
  now. Every other row of the Apex Desktop panel binds a stock GNOME key.
- The Apex Desktop panel is the one home for Apex settings. Stock panels gain no rows
  (decision 27). One stock panel changes behaviour: System's Software Updates row opens
  the Apex updates page.
- "Apex Tweaks" is a `.desktop` entry for `gnome-control-center apex`. There is no
  separate Updates app.

### Language

- Rust for Apex's own daemons, agents and CLIs, and for dev tools with real logic.
- GJS ES modules inside gnome-shell (`desktop/shell/js/ui/apex/`), written the way
  upstream writes them. No TypeScript, and no shell extensions.
- C inside gnome-shell (`ShellBlurEffect`), libadwaita, gnome-control-center (with
  Blueprint) and nautilus. The platform forces this: panels are compiled in, and
  nautilus has no sidebar plugin API.
- C for kernel and libfprint patches. SCSS for themes. The Plymouth script language for
  the boot splash. Bash for build glue. No Go.

### Deviations

HIG deviations the owner approved (decision 24):

| Deviation | Why |
|---|---|
| A persistent floating dock | Core of the design |
| A translucent top bar | Core of the design; solid when a window is maximised |
| The focused-app name in the bar | Core of the design; a label, no app menu |
| Coloured Settings sidebar tiles | Owner's design; one CSS class per panel |
| Full-colour Colloid app icons | Owner's design; symbolic icons stay Adwaita |
| A search popup separate from the overview | One search engine behind every entry point |

Design details the build does not follow. Each is settled by an owner decision:

| Detail | Decision | Why |
|---|---|---|
| App-chrome greys, 14 px header titles, 10 px control spacing, window shadows, widget metrics | 4 | libadwaita's values. A libadwaita colour patch would reach host apps only and split Flatpak apps into a second tier. |
| Radius 14 in Flatpak windows | 5 | 15 if the Bazaar spike fails |
| One-tap Restart in Quick Settings | 8 | A stray tap would end the session and lose unsaved work. |
| The Mail tile | 10 | No GTK4 GNOME mail client exists. |
| Hugeicons glyphs | 11 | Resolved 2026-10-23: Apex Symbolic, drawn in-house, ships in S1b; app icons stay Colloid |
| The "Apex Fedora" name | 19 | Fedora's trademark rules; the product is "Apex" |
| Rows in stock Settings panels | 27 | One home: the Apex Desktop panel, except Power's "Graphics and Display" group (board 24) |
| Ctrl+Space or Alt+Space for search | 6 | IDE completion and mutter's window menu; Super+Space instead |
| A status pill with only network, volume and battery | 26 | Built, except that the camera, microphone, location, remote-access and screen-sharing indicators still show while active: they are a safety signal |
| No input-source indicator in the bar | 6 | The en/vi indicator stays: with two sources switched per window, it is the only visible sign that Telex is on |

Two gaps have no path: GTK3 and X11 windows keep their own chrome.

## Consequences

- gnome-shell, libadwaita, gnome-control-center, nautilus and Ptyxis carry the Apex RPM
  signature, not Fedora's. mutter, GTK, gdm and Plymouth stay Fedora-signed binaries;
  mutter is pinned to the shell's build.
- Ptyxis is its own hold family. When its series fails to apply, the image keeps the
  last good build; with none, stock Ptyxis ships and the image is `degraded=terminal`.
- The lock screen, the polkit agent and the portal helper live in the rebuilt shell.
  Their fixes arrive through the lane: automatically when the series applies and the
  gates pass, otherwise within the hold limits. A failed rebase past 72 h for a
  security fix means a fully stock shell, not a partial Apex desktop.
- Every Fedora gnome-shell or mutter update means an Apex rebuild and a G4 run. Plan on
  monthly rebase work, 0.5 to 2 hours when clean. A GNOME major costs 4 to 8
  owner-days.
- `rpm -V gnome-shell` is clean: the theme is inside the package.
- A broken hook returns stock at its call site. A broken layer returns stock JS and CSS
  at the next login. A shell that cannot start fails the boot check and rolls back on
  an armed boot.
- Extensions the user installs may break against the changed internals. Apex ships none
  and does not support them.
- The input-switching habit changes: Super+Alt+Space, not Super+Space or a UniKey-style
  Ctrl+Shift.
- The answers together move the daily driver about 11 weeks, from 2027-02-12 to
  2027-04-30 (roadmap). Building the design's engine-level details now is part of that: S3c,
  and parts of S1b, S1d, S2a to S2d, S3a and S3b. S4 then lands next to the Fedora 46 GA
  target (2027-04-20), after GNOME 52.0, and the GNOME 52 port (S6) follows it.
- The iGPU composites every frame, including all glass; ADR 0015 keeps mutter off the
  NVIDIA card. PRIME-offloaded frames are copied to the iGPU and add memory traffic
  next to the glass. S3a measures without them; S4 measures once with an offloaded app.

## Alternatives rejected

- **Overlay first** (decision 1's recommended default): a replacement
  `gnome-shell-theme.gresource` built at image build, two first-party extensions with
  six override slots, and a vendored Dash to Dock. It kept Fedora's signature and needed
  no rebuild per point release. The owner chose the rebuilt shell: decision 26's items
  need more than the slots allow, saturation on dynamic glass needs C, and a broken
  override silently does nothing at runtime.
- **Replacing the RPM-owned theme gresource at image build** (decision 2's default).
  Moot once the shell is rebuilt; it also left `rpm -V` with a modified file.
- **Apex behaviour as extensions on top of the rebuilt shell.** Two loaders, a version
  gate, the `disable-user-extensions` coupling, and runtime prototype overrides that
  hide a conflict until a user trips it.
- **Dash to Dock with an Apex patch series.** Decision 26 needs changes to its code (the
  order's tail, the separator, the hover lift, the Show Apps tile). It injects into
  `ControlsManagerLayout`, `WorkspacesView`, `WorkspaceBackground` and
  `OverviewAdjustment`, the internals Apex's overview hunks change, so the two would
  fight at runtime. It would also be a second rebase stream. Dash to Dock declared
  GNOME 50 and 51 before their releases, so lag is not the reason. It stays the
  fallback if ApexDock cannot pass its goldens by the end of S2a.
- **Static glass on always-visible surfaces** (decision 14's default). The owner chose
  dynamic glass everywhere.
- **Invalidating the blur only from JavaScript damage tracking.** Every missed source
  (a workspace-switch clone, a window transform, a shell actor underneath) would show
  stale glass. Item e is correct by construction; the JavaScript only removes latency.
- **Patching mutter from the start.** It takes mutter off Fedora's signature for a need
  not yet measured.
- **A libadwaita patch that reads an Apex GSettings key.** Every GTK app would depend on
  an Apex schema. The patch watches the file the agent already writes.
- **A St patch for multi-layer `box-shadow`.** It needs C in `st-theme-node*.c`,
  beyond the C budget. Shadow-layer actors carry the second layer.
- **A custom JSON session mode.** A mode named like a built-in one is ignored
  (`js/ui/sessionMode.js:109-110`), and JSON modes exclude the unlock dialog (`:122`).
- **COPR or Packit as the build host for GNOME packages.** It adds a trust root and a
  second build system. ADR 0015 uses a COPR SRPM only as a signed input to the same
  lane.
- **mutter patches for window corners.** libadwaita draws corners and shadows in the
  client.

## Changes to other documents

Nothing changes before the owner accepts this ADR and the baseline commit exists.
Then, in one commit:

- ADR 0011: status `superseded by ADR 0014`.
- ADR 0002: new title, Decision and Consequences (delta edit A1): GJS inside
  gnome-shell, no TypeScript, no extensions; status adds `amended by ADR 0014`.
- ADR 0007: lines 25-29 (delta edit A2): entries name a removal condition; spec-only
  rebuilds through the lane are allowed; status adds `amended by ADR 0014`.
- ARCHITECTURE: §4.1 (gnome-shell is the lane's first package, `spec-edit`, the
  mirrored mutter), §4.2 (hold families), §4.3 (release cost), §7.3 and §7.4 (the
  desktop layer), §11 (G1, G2 and G4).
- Roadmap: the lane moves to S1a; the dock is Apex's own (S2a); glass starts on the bar,
  the dock and the popovers in S2b and covers every surface in S3a; a new S3c holds
  notifications, Quick Settings, motion and shadows.
- `design/SPEC.md`: rewritten for these answers (removed 2026-10-23 for
  [DESIGN.md](../DESIGN.md)).
- `tools/design/blurcost.py`, now [`0014-blurcost.py`](0014-blurcost.py): the cost model.
- Review §5: the owner's answers are recorded under the table.
