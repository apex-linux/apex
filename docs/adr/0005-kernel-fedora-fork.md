# ADR 0005: Machine-tuned kernel as a thin fork of Fedora's kernel (M2, gated)

Status: superseded by [ADR 0015](0015-cachyos-kernel-and-nvidia.md) (2026-09-28)

## Context

Fedora 45 ships kernel 7.2.7-300.fc45. Its spec has official hooks: `kernel-local`,
`linux-kernel-test.patch`, `%kcflags` and `buildid`. The alternatives each have a
problem:

- **CachyOS COPR kernels** are unsigned, lag behind Fedora stable, and lack Fedora's
  redhat patch. Without that patch, MOK-signed kmods do not load under Secure Boot.
- **Turning off debuginfo** strips BTF, and sched_ext goes with it.
- **Clang ThinLTO with BTF** disables `CONFIG_RUST`.

A kernel fork also adds CVE latency and a trust root (the COPR account), and the only
kernel change that is required, the audio fix, can be shipped without it (ADR 0004).

## Decision

- **M1 ships the stock, Fedora-signed kernel.**
- **M2 prepares the fork in `packaging/kernel/`.** It is built in COPR from Fedora
  dist-git f45 with:
  - `%define buildid .1.apex` and `%kcflags -march=znver3 -mtune=znver3`;
  - no debug, selftests or efiuki variants;
  - `kernel-local` enabling `RCU_LAZY` with `RCU_NOCB_CPU_DEFAULT_ALL` and building
    `CPU_IDLE_GOV_TEO`, and pinning every Fedora default Apex depends on;
  - the hardware patches that are not upstream yet in `linux-kernel-test.patch`.
- **Adopt the fork only when all of these hold:**
  - power and latency measurements show a benefit over stock;
  - a bot rebases automatically on every F45 stable kernel;
  - the image falls back to the stock Fedora kernel automatically when the fork lags
    Fedora by more than 72 h, or when Bodhi marks a kernel update as security;
  - the NEVRAs and RPM hashes are locked and the COPR signing key is committed;
  - `excludepkgs=kernel*` is set on the Fedora repos for fork builds.

## Consequences

- EEVDF stays the scheduler. scx A/B tests run from a transient `bootc usroverlay`,
  never from a third-party COPR package.
- The VM qualification must use `-cpu host`, because the fork uses Zen 3 instructions.
