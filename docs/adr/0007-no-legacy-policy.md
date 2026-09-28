# ADR 0007: No legacy components, enforced by the build

Status: accepted (2026-09-24, revised after design review)

## Context

The Fedora comps groups for GNOME pull in the classic session, GTK3 apps, PackageKit
and Qt5. Even a minimal GNOME 51 install reaches `libgtk-3` through several packages:

- `xdg-desktop-portal-gtk`
- `xdg-user-dirs-gtk`
- `evolution-data-server`
- `gnome-desktop3`
- `gnome-autoar`
- `ibus`

## Decision

- **Explicit lists.** Install the desktop from explicit lists with weak dependencies
  off, guarded by `--exclude` at compose time.
- **Legacy gate** (`image/checks/legacy.sh`). It runs inside the final image. It takes
  the set of packages that require `libgtk-3.so.0()(64bit)` or the X server, or that are
  banned by name, and compares it with `image/audit/legacy-allowlist.txt` as a set
  difference. It uses rpm's own resolution, not a home-grown dependency parser.
- **Allowlist entries.** Each entry names its reason and the milestone that removes it.
  The list can only shrink.
- **No private forks for zero GTK3.** Apex does not fork network- or input-facing
  libraries (evolution-data-server, ibus) just to reach zero GTK3; that would take on
  their security updates. Allowlisted packages go away when upstream drops GTK3.

## Consequences

- A new dependency that pulls GTK3 back in fails CI and names the packages involved.
- Function beats purity where no modern replacement exists: gnome-disk-utility 46 stays
  allowlisted until GDU 51 ships as GTK4.
