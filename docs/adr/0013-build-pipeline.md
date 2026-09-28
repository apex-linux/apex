# ADR 0013: Build pipeline on GitHub-hosted runners

Status: accepted (2026-09-24). The build-rootfs spike is still pending.

## Context

A single job that builds everything would:

- need about 40–44 GB of disk at peak, against roughly 53 GB free after cleanup;
- recompile Rust, libfprint and kmods on every daily run;
- push tags before signing them;
- test the image only with an ephemeral VM boot, which never exercises GRUB, the boot
  counter or the upgrade path.

Composing a full GNOME set with build-rootfs on Ubuntu runners has not been shown to
work.

## Decision

- **Workflows.** `rust.yml`, `rpms.yml` and `libfprint.yml` publish content-addressed
  OCI artifacts (`apex-rpms:<key>`, `apex-libfprint:<key>`). `image.yml` only
  assembles. `qualify.yml` runs a real install and upgrade under KVM and promotes.
- **Disk.**
  - Free up runner space first.
  - Put the rootful graphroot on `/mnt` using a btrfs loopback with zstd.
  - Preflight `df` checks fail fast.
  - Prune builder images before rechunking.
  - Push with skopeo from an `oci:` directory.
  - Record `du` and `df` for every step in the job summary.
- **Podman flags** proven on Ubuntu runners: rootful podman with
  `--cap-add=SYS_ADMIN,NET_ADMIN --device /dev/fuse --security-opt seccomp=unconfined
  --security-opt label=disable`. Every pull is wrapped in a retry.
- **Publishing.**
  1. Push under a unique tag.
  2. Sign the digest.
  3. Copy the manifest to the channel tag.

  Publish and promote jobs run under non-cancelling concurrency groups, and versions
  must increase.
- **Rechunking** passes `--previous-build` and a fixed `--max-layers`. A content key
  label lets scheduled runs skip publishing when nothing changed.
- **Spike first.** `spike.yml` runs build-rootfs with the full GNOME list and records
  time, peak disk and peak RAM. If it does not converge within a few days, the fallback
  is `FROM fedora-bootc:45` plus `dnf5 install --setopt=install_weak_deps=False`, then a
  rechunk.
- **Replay.** Every image build emits a lock list, and `workflow_dispatch` can replay one
  through `--lock`. After GA, a single build argument switches off updates-testing.
- **Local development.**
  - Rust runs on the host with a fake bootc.
  - UI (M2) builds use the Flatpak `org.gnome.Sdk//51`.
  - Image and RPM work runs in a user-mode Fedora 45 KVM builder VM on the host, which
    needs no root and uses nested KVM for tests (`tools/builder-vm/`,
    `just vm-create` then `just vm-image`).
