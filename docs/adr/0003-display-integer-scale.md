# ADR 0003: Integer scale 2 as the default for the built-in OLED

Status: accepted (2026-09-24, revised after design review); amended by ADR 0014 (2026-09-28: no hinting)

## Context

The panel is 2880×1800 on 14 inches, about 242 PPI. Mutter 51 picks 5/3, the offered
scale closest to 242/135 ≈ 1.79. At a scale p/q, a logical coordinate lands on a device
pixel only when L·p mod q = 0, which at 5/3 means every third logical pixel. GNOME
Shell's own UI, the cursor, GTK3 clients and HiDPI Xwayland clients render at
ceil(scale) = 2 and are then scaled down with linear filtering. GTK4 windows are painted
1:1 at both scales, but CSS borders inside them are antialiased at 5/3. Text looks about
the same at both scales.

## Decision

- **Scale.** Ship `/etc/xdg/monitors.xml`, rendered from the hardware profile, with
  scale 2 for `eDP-1 / SDC / 0x4154 / serial 0x00000000` at the exact mode rate
  90.001434326171875 Hz. It covers the built-in panel only. 5/3 stays selectable in
  Settings, and it is the supported way to get more space.
- **Fonts.** GTK font rendering with grayscale antialiasing and no hinting, as the design draws
  (ADR 0014; [DESIGN.md](../DESIGN.md#vendor-defaults)),
  fontconfig subpixel rendering `none` for clients that are not GTK4, and no mutter
  experimental keys.
- **Docking (M2).** The user-session agent restores scale 2 for the panel the first time
  a new monitor set appears, using the "Keep changes?" pattern, and suggests scale 1 for
  the external monitor.

## Consequences

- The logical workspace is 1440×900.
- `text-scaling-factor` below 1.0 is **not** a supported density tool: Settings 51
  clamps its Text Size control to 1.00–2.00.
- A user `~/.config/monitors.xml` overrides the system file. The Setup checklist offers
  "Sharpest" or "More space" in plain words.

## Alternatives rejected

- **5/3.** It is the upstream default, but most of the scene is not pixel-exact at that scale.
- **9/5.** It needs a mutter patch.
- **`org.gnome.desktop.interface scaling-factor`.** It forces the scale on every
  monitor, including external ones.
