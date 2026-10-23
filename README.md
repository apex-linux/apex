# Apex

Apex is a personal, image-based Linux distribution for exactly one laptop: the ASUS
Vivobook Pro 14X OLED **M7400QC** (Ryzen 5 5600H, RTX 3050 Mobile, Realtek ALC294,
ELAN fingerprint reader, Samsung 2880×1800 OLED at 90 Hz).

- **Base:** Fedora 45 delivered with bootc. Updates are atomic and signed, the laptop
  never reboots behind your back, and a bad update rolls back after a counted number of
  failed boots.
- **Desktop:** GNOME 51 on Wayland only, with GTK4/libadwaita apps. Legacy components
  are removed and kept out by a build gate.
- **Display:** pixel-exact by default (integer scale 2 on the built-in panel).
- **Hardware:** fixes for this machine: ALC294 speakers, the ELAN `04f3:0c6e` reader,
  firmware, dGPU power gating and the battery charge limit. Each fix is meant to go
  upstream.
- **Components:** everything Apex writes itself is Rust.

> Status: **S1a built; step M in progress**: the move to the `apex-linux` GitHub
> organisation. S1a's exit is recorded with its first green G2 on the self-hosted runner.
> Nothing here is ready to install yet. See [docs/ROADMAP.md](docs/ROADMAP.md).

## Read first

- [Architecture](docs/ARCHITECTURE.md): how the pieces fit, and why.
- [Design direction](docs/DESIGN.md): the look, the product rules and the settings
  contract.
- [Decisions](docs/adr/): one ADR per non-obvious choice.
- [M1 contract](https://github.com/apex-linux/apex-system/blob/main/docs/specs/M1-IMPLEMENTATION.md): names, paths and formats shared
  between components.
- [Threat model](docs/THREAT-MODEL.md).
- Hardware procedures and acceptance tests: [docs/hardware/](docs/hardware/).
- [Install](docs/INSTALL.md) and [recovery](docs/RECOVERY.md) runbooks.
- [Contributing](docs/CONTRIBUTING.md): code explains itself, and the comment guard
  that holds every change to it.

## Repositories

This repository holds the documentation. The code lives next to it in the
[apex-linux](https://github.com/apex-linux) organisation:

| Repository | What it holds |
|---|---|
| [apex-system](https://github.com/apex-linux/apex-system) | The update and boot stack in Rust (`apex-updated`, `apexctl`, `apex-boot`, `apex-bootc`, `apex-update`, `apex-dbus`), the machine profile in `hardware/`, the `apex` RPM |
| [apex-gnome](https://github.com/apex-linux/apex-gnome) | The Apex layer of GNOME Shell (`desktop/shell`), its rebuild recipe, and the layer and G2 tests |
| [apex-desktop](https://github.com/apex-linux/apex-desktop) | The settings schema, vendor defaults, wallpapers and the shell crash guard; the `apex-desktop` RPM |
| [apex-kernel](https://github.com/apex-linux/apex-kernel) | The kernel lane's patches and the libfprint rebuild |
| [apex-image](https://github.com/apex-linux/apex-image) | The bootc image, the rebuild lane `apex-lane`, the builder VM, and the gates that decide what ships |
| [apex-ci](https://github.com/apex-linux/apex-ci) | The CI tooling every repository shares: actions, the comment guard `apex-lint` and the Renovate preset |

Dependencies flow one way: the components never read each other, and apex-image pins
each of them by commit in `components.lock`.

## Development

Each repository builds and checks on its own with `just check`. Packages and images
build in a Fedora 45 builder VM
([ARCHITECTURE §4](docs/ARCHITECTURE.md#4-build-and-publish)), driven by apex-image.
GitHub-hosted CI checks every pull request and every push to `main`. Hardware
measurements need root and are run by hand.

## License

GPL-3.0-or-later. Patches in apex-gnome and apex-kernel carry the licenses of the
projects they modify (GPL-2.0-or-later for GNOME Shell, GPL-2.0 for the kernel, LGPL-2.1-or-later
for libfprint).
