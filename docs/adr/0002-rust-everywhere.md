# ADR 0002: Rust for Apex's own components

Status: accepted (2026-09-24, revised after design review); amended by ADR 0014

## Context

The brief allows Rust or Go.

- **Rust:** gtk4-rs 0.11.5 exposes GTK 4.24 (`v4_24`) and libadwaita-rs 0.9.2 exposes
  1.10 (`v1_10`). GNOME Core ships Rust apps (Loupe, Snapshot, Papers, Tour), and
  bootc, composefs and greenboot are Rust too.
- **Go:** gotk4 0.4.1 targets GTK 4.22, and its README warns of leaks and crashes.
  gotk4-adwaita has no tagged release, and no GNOME Core or Circle app is written in Go.

## Decision

Apex's own daemons, agents, CLIs and dev tools with real logic are Rust. Code that
lives inside another project is written the way that project writes it:

- The Apex layer inside gnome-shell is GJS ES modules. No TypeScript.
- Patches to gnome-shell's blur effect, libadwaita, gnome-control-center and nautilus
  are C, with Blueprint where the project uses it.
- Themes are SCSS, the boot splash is Plymouth script, and build glue is Bash.
- Kernel and libfprint patches are C.

There is no Go (ADR 0014).

## Consequences

- Daemons and clients share one crate for the D-Bus contract (`apex-dbus`) and one for
  the bootc JSON model (`apex-bootc`).
- One toolchain, pinned to Fedora's rust version, and one supply-chain policy
  (`cargo deny`) cover everything.
- **Apex code inside gnome-shell runs in the compositor.** A synchronous D-Bus call or
  a runaway timer in it freezes the whole desktop. The Apex layer therefore uses
  asynchronous proxies with timeouts, falls back to stock at every hook, and is gated
  by the headless shell check (G2) before an image is published.
