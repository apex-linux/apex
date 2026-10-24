# Apex design direction

Adopted 2026-10-23. It replaces `design/SPEC.md` and the HTML mockup in `design/mockup/`,
which are gone. Mechanisms and budgets stay in
[ADR 0014](adr/0014-engine-level-desktop.md); this page holds the look, the product
rules and the settings contract.

## Where the design lives

- **The canvas.** The owner's design canvas "Apex Fedora Mockups"
  (https://claude.ai/artifact/SGQU9LufXFUsDeYAQFqnef) is the visual reference. Its
  boards are numbered (table below).
- **Iteration.** The canvas and the code evolve together. A slice implements its boards.
  When building one shows a better answer (a stock widget that already does the job, a
  size that does not fit a real string), the board changes in the same piece of work.
  Nothing in the repository cites the canvas by line or pixel.
- **Tokens are code.** The canonical values are the SCSS tokens in
  `desktop/shell/data/theme/apex/_apex-tokens.scss`. G2 reads its expectations from that
  file. Icons, wallpapers and fonts live with `apex-desktop`.
- **Sign-off.** For each slice, the owner approves captures of the real shell placed
  beside the matching boards. Approved captures become G2's goldens. Renders of the
  canvas never gate anything.

## Visual principles

- Clean, modern and flat. No gradients anywhere (owner, 2026-10-21): every fill is one
  flat colour.
- Glass, a live blur of what is really beneath, is the only soft effect, and only on
  shell surfaces: the top bar, the dock, Quick Settings, the calendar, toasts, OSDs,
  banners, the window switcher, Spotlight, the overview and launcher scrims, and the lock
  screen. Text-heavy modal dialogs stay solid. Decision 14 and ADR 0014 hold the cost
  model and the acceptance.
- The shell is light by default. Dark Style switches it, and every board has a dark
  variant.
- Accent: one of libadwaita's nine accents (blue `#3584e4` by default, teal, green,
  yellow, orange, red, pink, purple, slate), driven by `accent-color`. It is drawn raw in
  both variants. White on the accent. Selection tint is the accent at 16 %.
- Wallpaper: Apex Facets, light and dark. It has a flat ground, nested rounded squares
  turned 45° low on the right, and a small pair top left. The sources are
  `desktop/wallpapers/apex-facets-{light,dark}.svg`.
- Type: Adwaita Sans with `ss03` (fontconfig), and JetBrains Mono. The font keys are
  `'Adwaita Sans 10.125'` (13.5 px) and `'JetBrains Mono 9.75'` (13 px); hinting is off
  (decisions 12 and 13). The canvas draws Inter with `cv05` and `ss03`, which is the same
  design.
- Icons:
  - App icons are full-colour Colloid, from a pinned upstream commit.
  - Symbolic icons are **Apex Symbolic**, drawn in-house (board 31; decision 11 resolved
    2026-10-23). They sit on a 16 px grid with a 1 px keyline, a 1.75 px stroke, and
    round caps and joins. Small closed shapes get solid cores, and inactive parts sit
    at 35 %. Larger renders keep the same pixel weight.
  - Folder and file icons are flat, with folders in the accent. Folder emblems come from
    the Apex Symbolic set (S7).
- Motion: one curve, `cubic-bezier(.2,.8,.2,1)`, with short fixed durations. Window
  geometry takes .3 s, overview and launcher fades .2 s, popovers .18 s and the dock
  hide .38 s.
- App chrome keeps libadwaita's own colours, metrics and window shadows (decision 4).
  The window radius is the one app-chrome value Apex changes (decision 5).

## Boards

| Board | Surface | Slice |
|---|---|---|
| 01 | Boot splash: diamond, "Apex" wordmark, progress bar; no footer | S1d |
| 30 | Disk unlock: the passphrase field in the boot splash | S1d |
| 31 | Apex Symbolic contact sheet | S1b |
| 32 | Terminal: sessions | T1 |
| 33 | Terminal: split panes, needs you | T2 |
| 34 | Calendar and notifications | S1b (styling), S3c |
| 35 | Overview | S1b (styling), S3a |
| 36 | Launcher | S1b (styling), S3a |
| 11 | Settings: Apex Desktop (top and scrolled) | C1 (S2c) |
| 18 | Settings: Software Updates | C2 (S2d) |
| 26 | Update health failure | C2 (S2d) |
| 22 | Edge tiling | S2a |
| 15 | Window switcher | S3a |
| 16 | OSD, banner and popup menu | S3a (glass), S3c |
| 19 | Screenshot UI | S3a |
| 20 | Lock screen | S3b |
| 12 | GDM greeter | S3b |
| 13 | Authentication dialog (polkit) | S3b |
| 14 | Power off dialog | S3c |
| 17 | Quick Settings: Wi-Fi submenu | S3c |
| 23, 24 | Settings: Appearance, Power (stock panels, restyled) | C2 (S2c) |
| 25 | Fingerprint enrollment | S4 |
| 21 | Welcome | not scheduled |
| 27, 28, 29 | Files: Home, list and details, search | F1 (0001–0003), F2 (0004–0007) |

The desktop with dock and top bar and Spotlight are drawn on the canvas when their
slice starts. Until then the rules below and the tokens define them. Board 17 also
shows the main Quick Settings panel.

## Product rules

These are behaviour decisions, kept from the old spec and the owner's decision sheet
(`docs/reviews/2026-09-28-review.md` §5).

**Everywhere**

- Live data only. Versions come from `Update1`, the GNOME and Fedora versions from the
  system, and memory, kernel, disk, hostname (`apex`) and refresh rate from the machine.
  Mockup text is never shipped.
- Reduce Transparency swaps the glass tints for solid tokens through an `apex-solid`
  root class and removes every blur effect. High contrast does the same and keeps
  upstream's colours. `disabled-features=['glass']` removes the effects and keeps the
  tints.
- Reduce Motion sets `enable-animations` (inverted) and the a11y `reduced-motion` key
  together.
- Surfaces with no board derive from the tokens:
  - transient surfaces that copy a glass surface's geometry take its glass;
  - modal dialogs are solid, radius 26;
  - popup menus are solid, radius 14, rows 34;
  - gnome-initial-setup and GTK dialogs stay libadwaita stock.

**Boot.**

- Plymouth `apex` script theme, with the progress bar driven by real boot progress and
  round ends.
- The LUKS prompt is the lock screen's field, drawn by the theme. Esc shows Plymouth's
  text view, which always shows the prompt.
- The `apex-twostep` fallback theme stays installed.
- GRUB stays hidden unless the previous boot failed (decision 17).

**Greeter and lock.**

- The greeter keeps `prefer-dark` and the stock layout over a pre-blurred greeter image.
- The lock is a single stage (decision 7): clock and prompt together, date above time,
  and the hint "Press Enter to unlock".
- The prompt is torn down when the screen blanks, so PAM and the fingerprint reader do
  not run while it is off. Lock-screen notifications are off.
- The avatar shows the user's picture, or else the initial letter. "Enter Password"
  replaces only PAM's exact `Password:`; every other PAM question shows verbatim.
- `apex.safe=1` gives the stock lock.

**Top bar.**

- Glass, or solid when a window on the primary monitor is maximised and no overlay is
  open, or when Translucent Top Bar is off.
- The Activities pill holds the diamond and the workspace dots, then the focused app's
  name, or "Desktop" when nothing has focus.
- The centred clock is followed by an accent dot when unread notifications exist and Do
  Not Disturb is off.
- Search button (Super+Space). The status pill shows network, volume and battery only.
  The privacy, recording, unsafe-mode, input-source and accessibility indicators still
  show (decision 26).
- A 4 × 4 hot corner, with the stock barrier kept. Both follow `enable-hot-corners`.

**Dock.**

- Floating and centred. Favourites first: Files, Web, Calendar, Music, Text Editor,
  Terminal, Software, Settings (no Mail, decision 10).
- Then running non-favourites, then the separator, Show Apps (full colour) and Trash
  (with Empty Trash).
- Hide Behind Maximized Windows: the bottom edge reveals the dock through a threshold-0
  barrier. The dock reserves no strut and hides under fullscreen.
- It stays visible in the overview and the app grid, whose own dash is hidden.
- Ctrl+Alt+Tab reaches it. "Launch Using Discrete Graphics Card" stays in the menu.

**Windows.**

- Minimise, maximise and close. Corner radius 0, 8, 14 (default) or 20; maximised,
  tiled and fullscreen windows are square.
- Dragging to the top edge maximises.

**Quick Settings.**

- Toggle order: Wi-Fi, Bluetooth, Power Mode, Night Light, Dark Style, Do Not Disturb,
  Airplane Mode, VPN.
- Subtitles show state ("Until 07:00", "On", "Off"). Power Mode is lit at every profile;
  its `checked` state stays stock.
- Round buttons: Screenshot, Settings, Lock, Power. The power menu is stock, and Restart
  and Power Off ask for confirmation (decision 8).

**Notifications and calendar.**

- A flat, newest-first list of cards, with the close button always visible.
- Footer: a Do Not Disturb switch and Clear, always shown on the right.
- The first weekday follows the locale; times follow `clock-format`.

**Spotlight.**

- One engine behind Super+Space, the bar button, the overview pill and typing in the
  overview. The Super tap still opens the overview.
- Sections and caps: Calculator 1, Applications 4, Settings 3, Files 4.
- Each provider has a 1 s budget; a slow section is left out of that query.
- Enter on a calculator result copies it and shows a toast.

**Overview and launcher.**

- Workspace thumbnails show from two workspaces. Window titles are always visible, and
  there are no workspace background cards.
- The launcher's pill searches apps only and filters the grid in place. The grid is 7 × 4
  with 88 px icons; paging and folders stay. Super+A opens it.

**Terminal.**

- Ptyxis, with JetBrains Mono at line height 1.6 (`cell-height-scale` 1.21), rebuilt
  with the Apex terminal series (boards 32 and 33).
- A sessions sidebar replaces the tab bar.
  - Sessions are grouped by where they run: this computer, each toolbox or distrobox
    container, each ssh host.
  - Each row shows the title, the program and its state, a relative time and a status:
    running, done, failed, needs you, or none when idle. Programs that report progress
    (OSC 9;4) draw a 2 px accent bar along the row's bottom edge.
  - A session needs you when it rang the bell or sent a desktop notification while
    unfocused. It stays marked until it is focused.
  - The footer counts the sessions per status.
- The sidebar's header holds New session and the main menu. The content header shows
  the session's title, its path, a tag naming the foreground program, and the session
  menu (⋮).
- A session splits right or down into two panes. Each pane has its own header, and the
  unfocused pane is dimmed.
- The sidebar is flat, in the window's colours. Glass stays on shell surfaces.
- A coloured prompt via `/etc/profile.d/apex-prompt.sh`.
- The caret follows the accent through a user palette written by apex-session-agent.

**Settings.**

- Apex Desktop is the first panel, and the sidebar has coloured tiles in a fixed order.
- Stock panels gain no rows (decision 27); every Apex option lives in the Apex Desktop
  panel. The one exception is Power's "Graphics and Display" group (board 24): the dGPU's
  state and Lower Refresh Rate on Battery (the owner, 2026-10-24).
- The System panel's Software Updates row opens an Apex page on `Update1`: state,
  changes, held and degraded packages, and Download, Restart and Roll Back. polkit stays
  in the daemon.
- The Apex Desktop header shows the booted image version, the GNOME Shell version and
  session, and the Fedora version. The launcher's "Apex Tweaks" opens the panel.

**Files.**

- Adds a disk footer for the filesystem holding `$HOME` (not composefs `/`), an
  item-count bar and a 72 px default zoom (0001–0003).
- The recent strip shows the four newest existing recent items on Home in grid view. It
  hides when empty or when `files-recent-strip` is off.
- The details pane is the end pane of an overlay split view, so below 900 px it overlays
  the view.
- Search chips (All, Folders, Documents, Images, Audio & Video) filter the shown results
  only and never the search. Counts update live.
- A two-option grid/list toggle.
- Folders follow the accent through nine `Apex-<accent>` themes, switched only while
  `icon-theme` names an Apex theme. With the schema missing, Files uses the defaults.

**Toast.**

- The first-login hint "Press Super+Space to search" shows once, and not under Do Not
  Disturb.
- Screenshots keep GNOME's stock notification.

## Settings contract

### Apex Desktop panel rows

| Group | Row | Subtitle | Default | Backing key |
|---|---|---|---|---|
| Top Bar | Translucent Top Bar | Turns solid when a window is maximized | on | `translucent-top-bar` |
| Top Bar | Show Focused App Name | | on | `show-focused-app-name` |
| Top Bar | Show Date in Clock | | on | `org.gnome.desktop.interface clock-show-date` and `clock-show-weekday`, set together |
| Top Bar | Show Battery Percentage | | on | `org.gnome.desktop.interface show-battery-percentage` |
| Top Bar | Hot Corner | Touch the top-left corner to open the overview | on | `org.gnome.desktop.interface enable-hot-corners` |
| Dock | Icon Size (S, M, L) | | M | `dock-icon-size`: drawn at 46, 54 and 62 px |
| Dock | Hide Behind Maximized Windows | Move the pointer to the bottom edge to reveal it | on | `dock-intellihide` |
| Dock | Show Running Indicators | | on | `dock-running-indicators` |
| Dock | Show Trash | | on | `dock-show-trash` |
| Windows | Corner Radius (0, 8, 14, 20) | Maximized windows are always square | 14 | `window-corner-radius` |
| Windows | Titlebar Buttons (All, Close only) | | All | `org.gnome.desktop.wm.preferences button-layout`: `appmenu:minimize,maximize,close` or `appmenu:close` |
| Windows | Drag to Top Edge to Maximize | | on | `org.gnome.mutter edge-tiling` |
| Effects | Reduce Transparency | Replace glass surfaces with solid colors | off | `reduce-transparency` |
| Effects | Reduce Motion | Disable window and dock animations | off | `enable-animations` (inverted) and a11y `reduced-motion` |

Every row changes the running desktop at once. A row that sets two keys binds the first
and writes the second in its change handler.

### Schema `io.github.apex_linux.Apex.Desktop`

Only keys with no upstream home. The schema ships in `apex-desktop`. The layer treats a
missing schema as safe mode and reads every key live, with one limit: a shell that started
with the layer on follows `layer-enabled` and `disabled-features` as they change, while a
shell that started stock (the key false, a kill switch, or no schema) stays stock until
the next login.

| Key | Type | Default | Read by |
|---|---|---|---|
| `translucent-top-bar` | `b` | `true` | layer |
| `show-focused-app-name` | `b` | `true` | layer |
| `dock-icon-size` | `s`: `'small'`, `'medium'`, `'large'` | `'medium'` | layer |
| `dock-intellihide` | `b` | `true` | layer |
| `dock-running-indicators` | `b` | `true` | layer |
| `dock-show-trash` | `b` | `true` | layer |
| `window-corner-radius` | `u`, 0 to 20 | `14` | apex-session-agent |
| `reduce-transparency` | `b` | `false` | layer |
| `layer-enabled` | `b` | `true` | layer; the crash guard sets it to `false` |
| `disabled-features` | `as` | `[]` | layer: `glass`, `dock`, `spotlight`, `lock`, `motion`, `notifications`, `overview`, `panel`, `quick-settings`, `shadows` |
| `files-details-pane` | `b` | `false` | nautilus |
| `files-recent-strip` | `b` | `true` | nautilus |
| `search-hint-shown` | `b` | `false` | layer: set once "Press Super+Space to search" has shown |

Child schema `io.github.apex_linux.Apex.Desktop.Keybindings`: `toggle-spotlight` (`as`,
`['<Super>space']`).

apex-session-agent writes `apex.css` atomically when `window-corner-radius` changes, and
`~/.config/gtk-4.0/gtk.css` imports it. It holds `:root { --window-radius: Npx; }` plus
`--window-radius: 0px` for maximised, fullscreen, tiled and `solid-csd` windows. The
resets are needed because a user-priority rule beats libadwaita's own. The libadwaita
patch loads the same file at `USER + 1` and reloads it on change, so host apps follow it
live.

### Vendor defaults

`90_apex.gschema.override` keeps the input sources and `power-button-action`, and adds:

| Schema | Key | Value |
|---|---|---|
| `org.gnome.desktop.interface` | `font-name`, `document-font-name` | `'Adwaita Sans 10.125'` |
| | `monospace-font-name` | `'JetBrains Mono 9.75'` |
| | `font-hinting` | `'none'` |
| | `icon-theme` | `'Apex'` |
| | `show-battery-percentage`, `clock-show-weekday` | `true` |
| `org.gnome.desktop.wm.preferences` | `button-layout` | `'appmenu:minimize,maximize,close'` |
| `org.gnome.desktop.wm.keybindings` | `switch-input-source` | `['<Super><Alt>space', 'XF86Keyboard']` |
| | `switch-input-source-backward` | `['<Shift><Super><Alt>space', '<Shift>XF86Keyboard']` |
| `org.gnome.desktop.background` | `picture-uri`, `picture-uri-dark` | the Apex Facets files |
| `org.gnome.desktop.notifications` | `show-in-lock-screen` | `false` |
| `org.gnome.desktop.search-providers` | `sort-order` | Calculator, Settings, Files |
| `org.gnome.shell` | `favorite-apps` | Files, Web, Calendar, Music, Text Editor, Ptyxis, Bazaar, Settings |

- `color-scheme` stays at the stock `'default'`: patch 0002 makes that a light shell.
- No `enabled-extensions`; Apex ships no shell extension.
- `font-rendering` stays `'automatic'`. If GTK 4 still hints at scale 2, the override
  adds `font-rendering='manual'`.

### Keyboard shortcuts

| Action | Keys |
|---|---|
| Spotlight | Super+Space |
| Next / previous input source (English ↔ Vietnamese Telex) | Super+Alt+Space / Shift+Super+Alt+Space; XF86Keyboard |
| Overview | Super tap, hot corner, Activities, three-finger swipe |
| Launcher | Super+A |
| Window menu | Alt+Space |

Ctrl+Space stays free for IDEs. The xkb Ctrl+Shift and Alt+Shift toggles are not used.
`60-apex.xml` lists "Open Spotlight" in Settings > Keyboard.

## Engineering notes

- St reads one shadow per `box-shadow`. The layer draws each further layer with a
  shadow-layer actor; a 1 px ring becomes a 1 px border.
- CSS `blur(N)` is a Gaussian σ of N logical px. `Shell.BlurEffect` takes a radius in
  device px with σ = radius / 2, so radius = 2 × N × scale.
- Glass re-blurs only when the frame's redraw clip covers its whole box, so idle costs
  nothing and no stale pixels are sampled. The layer forwards window damage, moves and
  restacking as redraws of every glass box they touch.
- Patch 0002 gives the user and unlock-dialog modes `'prefer-light'`, so `'default'` and
  the stock Dark Style toggle both work. In safe mode the shell is stock again.
- Moving input-source switching to Super+Alt+Space frees Super+Space for Spotlight. The
  override is system-wide, so the greeter and the lock screen use the same keys.
