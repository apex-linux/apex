# ADR 0002: Rust for every Apex component

Status: accepted (2026-09-24, revised after design review)

## Context

The brief allows Rust or Go.

- **Rust:** gtk4-rs 0.11.5 exposes GTK 4.24 (`v4_24`) and libadwaita-rs 0.9.2 exposes
  1.10 (`v1_10`). GNOME Core ships Rust apps (Loupe, Snapshot, Papers, Tour), and
  bootc, composefs and greenboot are Rust too.
- **Go:** gotk4 0.4.1 targets GTK 4.22, and its README warns of leaks and crashes.
  gotk4-adwaita has no tagged release, and no GNOME Core or Circle app is written in Go.

## Decision

Every Apex component is Rust: libraries, daemons, CLIs, GTK apps and build tooling.
There are two exceptions, both forced by the platform:

- The GNOME Shell extension (M2+) is TypeScript compiled to GJS.
- Kernel and libfprint patches are C.

## Consequences

- Daemons and clients share one crate for the D-Bus contract (`apex-dbus`) and one for
  the bootc JSON model (`apex-bootc`).
- One toolchain, pinned to Fedora's rust version, and one supply-chain policy
  (`cargo deny`) cover everything.
- **An enabled Shell extension runs inside the compositor.** A synchronous D-Bus call or
  a runaway timer in it freezes the whole desktop. The extension therefore holds
  presentation only, uses asynchronous proxies with timeouts, and is gated by a headless
  Shell smoke test before promotion.
