# Apex Linux specification

This is the product specification for Apex Linux. It says what we are building,
in what order, and how we know a step is finished. How we work is in
[engineering.md](engineering.md).

## Goals

1.  **A general desktop distribution.** Apex runs on ordinary x86_64 UEFI
    computers. Hardware support is organized by component (a GPU, a Wi-Fi
    card, a fingerprint reader), never by one machine's profile.
2.  **Full support for the reference machine.** Every device in the
    [reference machine](#reference-machine) works out of the box. It is the
    first acceptance target, not the only one.
3.  **Visual quality.** The owner's design canvas is the source of truth for
    how Apex looks and behaves. A surface ships when it matches its handoff
    specification in light and dark themes.
4.  **Updates that cannot break the system.** The operating system is one
    image. An update replaces the image as a whole and a bad update rolls
    back.

## Non-goals

These are out of scope until the milestone that names them, because the
previous attempt spent its time here before it could boot:

*   A custom update daemon. Apex uses what `bootc` provides.
*   A custom kernel. Apex ships Fedora's kernel unless a reference device
    cannot work without a change.
*   Forking GNOME applications. Theming and extensions come first; a patch to
    an upstream component needs a reason an extension cannot satisfy.
*   Architectures other than x86_64.

## Architecture

Apex is an image-based Fedora system with a GNOME desktop:

*   **Base:** the Fedora `bootc` base image, currently Fedora 45.
*   **Image:** `apex-image` builds one OCI image from the base, the Fedora
    GNOME packages, and the Apex components. The same image installs to disk
    and delivers updates.
*   **Updates and rollback:** stock `bootc` (`bootc upgrade`,
    `bootc rollback`). The Settings panel in the design is a front end to it.
*   **Hardware:** `apex-hardware` holds rules keyed by device ID (udev,
    modprobe, kernel arguments, firmware lists) and the acceptance checks.
*   **Desktop:** `apex-desktop` holds the design tokens, the GNOME Shell
    extension, the GTK and Shell themes, the icon set, wallpapers, boot and
    greeter assets, and default settings.

### Repositories

| Repository | Produces | Main languages |
| --- | --- | --- |
| [`apex`](https://github.com/apex-linux/apex) | This specification, the engineering standards, the issue tracker | Markdown |
| [`apex-image`](https://github.com/apex-linux/apex-image) | The OS image, the installer media, the release pins | Containerfile, shell |
| [`apex-hardware`](https://github.com/apex-linux/apex-hardware) | Hardware rules and acceptance checks | Shell, Python, Rust |
| [`apex-desktop`](https://github.com/apex-linux/apex-desktop) | The look: tokens, Shell extension, themes, icons | JavaScript, CSS, SVG |
| [`.github`](https://github.com/apex-linux/.github) | Org profile, contribution files, the shared CI convention check | Markdown, YAML |

A new repository is created when a component has its own release cadence or
toolchain, not before.

### How the repositories meet

This follows the Pop!_OS model, where the build server builds the default
branch of every repository into a staging channel and a release is a short
list of pinned commits.

*   Every component repository exposes `just install <destdir>`, which
    installs its files under `<destdir>/usr` only.
*   `apex-image` builds from the tip of `main` of each component. The result
    is the rolling `main` image. No pull request is needed in `apex-image`
    when a component changes.
*   A release is one pull request to `apex-image` that updates
    `release/sync` (one `component=commit` line each) and one tag.

## Reference machine

ASUS Vivobook Pro 14X OLED, model M7400QC.

| Component | Device | Must work |
| --- | --- | --- |
| CPU | AMD Ryzen 5 5600H | Frequency scaling, power profiles, suspend (s2idle) and resume |
| Integrated GPU | AMD Radeon `1002:1638` | Drives the desktop on Wayland |
| Discrete GPU | NVIDIA RTX 3050 Mobile `10de:25a2`, no MUX | Powers down when idle (D3cold); runs an app on request |
| Display | 2880x1800 OLED, 90 Hz | Scale 2, 90 Hz, brightness control |
| Wi-Fi | Intel AX200 `8086:2723` | Connects, resumes after suspend |
| Bluetooth | Intel AX200 `8087:0029` | Pairs audio and input devices |
| Audio | Realtek ALC294 on Ryzen HD audio | Speakers, headphone jack, internal microphone |
| HDMI audio | AMD `1002:1637` | Output over HDMI |
| Fingerprint | ELAN `04f3:0c6e` | Enroll, unlock, authorize |
| Webcam | IMC UVC `13d3:5458` | Video in the camera app and the browser |
| Storage | WD SN770 NVMe | Install, TRIM |
| Input | Keyboard, touchpad, function keys | Gestures, backlight, hotkeys |
| Battery | ASUS WMI | 80% charge limit persists across reboot and resume |
| Firmware | UEFI | Boots with Secure Boot off; Secure Boot on is a later goal |

Each row becomes an automated or scripted check in `apex-hardware`. A row
is done when its check passes on the machine, not when a fix is written.

## Milestones

A milestone is finished when its exit criteria are demonstrated. Work on a
later milestone may run in parallel only when it does not delay the current
one.

### M0: It boots

*   `apex-image` builds on a developer machine and in CI.
*   The image boots to the GNOME greeter in a virtual machine.
*   CI publishes the rolling image to `ghcr.io/apex-linux/apex:main`.

**Exit:** `just build` then `just vm` reaches the greeter, from a clean
clone, on the reference machine.

### M1: It runs on the reference machine

*   Installer media installs Apex on real hardware.
*   Every row of the reference machine table passes its check.
*   The NVIDIA driver ships as prebuilt modules in an image flavor, so that
    machines without NVIDIA do not carry it.

**Exit:** the acceptance run on the M7400QC is green and recorded in
`apex-hardware`.

### M2: It looks like Apex

*   Boot splash, disk unlock, greeter and lock screen.
*   Top bar, dock, overview, launcher, window switcher, tiling, quick
    settings, calendar, notifications and on-screen displays.
*   Authentication and power-off dialogs.
*   Apex Symbolic icons, application icons, wallpapers, light and dark
    themes, and the nine accent colors.

**Exit:** the design owner signs off each surface against its handoff
specification, on the reference machine.

### M3: Updates you can trust

*   Images are signed and the system refuses unsigned images.
*   The Software Updates panel, the update health failure flow, and the
    Welcome first-run application.

**Exit:** an update, a forced bad update and its rollback are demonstrated
on the reference machine.

### M4: Applications

*   Files, Terminal and Apex Code redesigns, and Spotlight search.

**Exit:** defined when M3 closes.
