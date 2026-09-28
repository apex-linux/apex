# Roadmap

Milestones are ordered by risk. Each one has exit criteria that can be checked.

## M0: Foundation (in progress, 2026-09-24)

- Research, architecture, ADRs and the threat model.
- Rust workspace:
  - `apex-bootc`, `apex-update`, `apex-boot` and `apex-dbus`, all with tests;
  - `apex-updated` and `apexctl`.
- The image definition, system files and image checks.
- Packaging: the apex RPM, and libfprint with the series file.
- CI workflows, including the build-rootfs spike.
- **Exit:** the workspace builds and passes fmt, clippy and tests locally; the spike
  workflow is ready to run.

## M0.5: Hardware measurements on the current Ubuntu install (owner, sudo)

- **Audio:** COEF dumps A–E (`hardware/m7400qc/audio/coef-dump.sh`). Then try the
  rendered `.fw` file through `/etc/modprobe.d` on Ubuntu and record the result.
- **Fingerprint (optional):** the safe libfprint capture log with patches 0001 and 0002
  (docs/hardware/FINGERPRINT.md).
- **Exit:** the measured COEF values are committed to `profile.toml`.

## M1: First bootable Apex on this laptop

- `image.yml` and `qualify.yml` are green. `apex-testing:45` is published and signed.
- A qualified digest is promoted to `apex:45`.
- Installed first on an external USB SSD (ADR 0010).
- **Exit:** docs/hardware/ACCEPTANCE.md passes on the laptop. That covers:
  - audio, including after suspend and after Windows;
  - Wi-Fi and Bluetooth;
  - the charge limit;
  - dGPU in D3cold at least 95 % of the time;
  - scale 2 in GDM and in the session;
  - fingerprint enrollment works.

  An update is applied through `apexctl`, and a forced red boot rolls back.

## M1.1: Internal-disk install

- LUKS2, btrfs and a shared ESP with Windows (ADR 0010).
- **Exit:** a week of daily use with automatic downloads and at least one applied update.

## M2: Native UI and optional hardware paths

- **The Updates app** (`io.github.sekirokenjii.Apex.Updates`, GTK4/libadwaita): the
  Updates, This Device and Setup pages, a session notifier, restarts through
  gnome-session, and the docking scale agent.
- **The Tweaks page** (ADR 0011, layer C).
- **dGPU use:** NVIDIA 615 open kmods with a MOK (a separate ADR), or nouveau with NVK,
  depending on what the owner needs.
- **Kernel fork** (ADR 0005), once its gates are met.
- **The installer ISO** (`image-builder bootc-generic-iso`).
- **Fingerprint unlock** through the Apex authselect profile, after the score test.

## M3: Deeper customisation

- **Apex Shell extension** (ADR 0011, layer D), with a headless Shell smoke test in CI.
- **Rust IBus Vietnamese engine.** Acceptance criteria:
  - automatic restore of English words;
  - tone marks can be typed anywhere in the syllable;
  - new-style tone placement by default;
  - no backslash mode toggle;
  - surrounding-text support;
  - a libadwaita preferences window.

## Fedora 46 (around 2027-02)

- The manual runbook for 45 → 46: switch with download-only, pin the last F45
  deployment, and snapshot `/var` first.
- Automate it after one successful manual run.
