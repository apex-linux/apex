# ADR 0017: Apex Code is GNOME Builder with an Apex series

Status: accepted (2026-11-03). The owner picked the base and set no patch budget. It
adds track E to the ROADMAP; canvas boards 40 and 41 are the first sketch.

## Context

Apex needs a code editor that belongs to the system the way Files, Settings and the
terminal do. A reskin of VSCodium was considered and dropped:
- an extension reaches only colours, icons and settings, never the workbench's layout,
  title bar or panels, so boards 40 and 41 could not be built that way;
- Electron carries a Chromium per window, a RAM cost nothing outside it can lower;
- it stands outside the chain the other apps share: the accent, radius, high contrast and
  Apex Symbolic from libadwaita, the AT-SPI gates, G2 and the lane.

Fedora 45 ships GNOME Builder 50 (`gnome-builder-50.0-5.fc45`), on GTK4, libadwaita,
libdex and jsonrpc-glib. Builder already has LSP clients, meson, cargo and npm builds,
podman and toolbox runtimes, git, a VTE terminal and gdb.

## Decision

1. **Apex Code is GNOME Builder rebuilt in the lane with an Apex series**, as nautilus,
   gnome-control-center and Ptyxis are. The recipe lives in `apex-gnome`
   (`packaging/pkgs/gnome-builder/`), with its own hold family (`degraded=code`): a
   failed build ships Fedora's Builder. The app id stays `org.gnome.Builder`; the name
   shown, the icon and the about page say Apex Code.
2. **No ADR 0014 budget for this series** (owner, 2026-11-03). Each patch still says
   what it changes and why, and the lane's checks apply as to every series.
3. **Zed's strengths are taken as goals, not code:**
   - latency and startup budgets, measured in E0 and held by a test;
   - a fuzzy file and command palette (Zed's finder) on Builder's global search;
   - inline diagnostics and code actions, LSP first;
   - multibuffers: search results and diagnostics edited across files in one view;
   - an agent panel speaking the Agent Client Protocol (ACP), so an agent such as Claude
     Code runs inside the editor. Whether ACP fits Builder is checked in E0.
   Zed's multiplayer needs a server and is out of scope.
4. **On bootc, builds and language servers run in a toolbox or podman runtime**, never
   on the host. The image ships Builder and its runtimes, not the toolchains.
5. **VSCodium stays the user's choice**: its releases ship RPMs, which a user can layer
   or install in a toolbox. Apex neither preinstalls nor brands it.

## Consequences

- Apex Code follows the accent, dark style, high contrast and radius with no sync code,
  and its AT-SPI tree is GTK's, so the bounds and contrast gates apply to it.
- Builder's plugin set is smaller than VS Code's marketplace. That is accepted, with
  VSCodium as the escape hatch.
- The series is the largest Apex carries; each Builder bump costs a rebase, which the
  lane's hold keeps from blocking an image.
- E0 decides the numbers: RAM, latency and startup budgets.
