# ADR 0001: Image-based OS with bootc on the ostree backend

Status: accepted (2026-09-24, revised after design review)

## Context

Apex must update the base OS, kernel and desktop atomically, roll back automatically
after a bad update, and move between Fedora major versions safely. Fedora publishes
`quay.io/fedora/fedora-bootc:45`. bootc 1.16 has a weekly release cadence and a stable
status API (`org.containers.bootc/v1`).

## Decision

- Ship Apex as one signed OCI image and let `bootc` consume it.
- Use the default ostree backend with composefs, GRUB2, shim and bootupd.
- Generate the root filesystem with `bootc-base-imagectl build-rootfs --manifest=minimal`
  from the digest-pinned fedora-bootc:45 builder, then copy it `FROM scratch`.
- Apex-built RPMs join the compose through a local repository with priority 1, so there
  is one depsolve and it runs under the same `--exclude` guards.
- If build-rootfs with the GNOME set does not converge, fall back to `FROM fedora-bootc:45`
  plus `dnf5 install --setopt=install_weak_deps=False` and a rechunk (ADR 0013).
- Boot health and rollback are owned by Apex (ADR 0009), not greenboot-rs.

## Consequences

- `/usr` is read-only on the client. Client-side package layering is unsupported: a
  polkit rule denies rpm-ostree's install actions, because one layered package makes
  `bootc upgrade` refuse to run.
- The image may contain exactly one kernel, and CI builds the initramfs.
- Rollback relies on a GRUB environment boot counter, which only works on the ostree
  backend.

## Alternatives rejected

- **FROM fedora-silverblue:45.** It is unsigned and nightly, and it ships
  gnome-classic-session, qt5 and the rpm-ostree plugin for GNOME Software.
- **The composefs backend with a sealed UKI.** It is experimental: the on-disk format
  has changed during 1.16.x, and there is no boot counting.
- **systemd-sysupdate with mkosi.** Fedora has no producer infrastructure for it.
