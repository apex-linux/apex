# ADR 0011: Customisation boundaries

Status: superseded by [ADR 0014](0014-engine-level-desktop.md) (2026-09-28)

## Context

The brief asks for very deep GNOME customisation that stays HIG-native. The hard limits
are:

- libadwaita supports no custom themes;
- accent colours are a fixed enum of nine;
- Shell themes need an unsupported extension;
- icon themes barely affect libadwaita apps, which bundle their symbolic icons;
- GNOME Shell has no stable extension API;
- gnome-control-center has no panel plugin API.

## Decision

Customisation happens in five layers. Nothing outside them ships.

| Layer | Mechanism | Examples |
|---|---|---|
| A. Vendor defaults | `/usr/share/glib-2.0/schemas/90_apex.gschema.override`, compiled in the image, no locks, only keys that differ from upstream | dark style, favorite apps, Telex input source, power button `interactive` |
| B. Upstream UIs | GNOME Settings and the Extensions app own their keys; Apex links to them (`gnome-control-center display`, `power`, `users`) | scale, accent colour, wallpaper, charge limit, fingerprint |
| C. The Apex app (Rust, libadwaita) | Apex concepts only (updates, device status, first-run setup). From M2, a "Tweaks" page bound with `g_settings_bind` to keys that Settings does not show | fonts, window buttons and titlebar actions, focus mode, centre new windows, clock seconds and weekday, xkb options |
| D. Apex Shell extension (M2+) | `apex@sekirokenjii.github.io`; every feature behind a key in `io.github.sekirokenjii.Apex.Shell`; qualified in lockstep with the exact Shell in the image | update Quick Settings item, animation speed, top bar density |
| E. Refused | documented | custom GTK or libadwaita themes, gtk.css injection, arbitrary accent RGB, Shell user themes, icon-theme swapping as a feature, patched gnome-control-center, dconf locks |

## Consequences

- **Naming.** The Apex app is named for its job, not the brand: "Updates", with app ID
  `io.github.sekirokenjii.Apex.Updates` and keywords that include "Apex". It never
  duplicates a GNOME Settings page.
- **Why layer D is defensible.** Apex's advantage over extensions.gnome.org is that its
  extension is tested against the exact gnome-shell build it ships with, on every image.
