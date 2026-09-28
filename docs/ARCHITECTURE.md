# Apex architecture

Apex is a personal, image-based Linux distribution for one machine: the ASUS Vivobook
Pro 14X OLED **M7400QC**. It is built on **Fedora 45** and **GNOME 51**, and every
component we write ourselves is in **Rust**. This document is the source of truth for
how the pieces fit together. Each non-obvious decision has an ADR in [`adr/`](adr/).
The security model is in [THREAT-MODEL.md](THREAT-MODEL.md) and the milestones are in
[ROADMAP.md](ROADMAP.md).

Upstream facts were checked on 2026-09-23 and 2026-09-24, while Fedora 45 was in beta
(GA target 2026-10-20). The design then went through an adversarial review covering
upgrade safety, supply chain, hardware correctness, HIG and product, and build
feasibility. Section 12 records what that review changed.

## 1. Goals and non-goals

Goals, in priority order:

1. **Hardware that works.** Speaker audio on the ALC294 (codec subsystem `1043:1ab2`),
   the ELAN `04f3:0c6e` fingerprint reader, all firmware, and the 80 % battery charge
   limit. Every fix is written so that it can be submitted upstream, and every fix has an
   acceptance test on the real laptop.
2. **Safe, automatic updates.** OS, kernel and desktop update atomically in the
   background. Nothing reboots without the user, a broken update rolls back on its own,
   and what gets applied is exactly what the user saw.
3. **A fully modern GNOME.** GNOME 51 on Wayland only, GTK4/libadwaita apps only, and no
   X11 session. GTK3 is allowed only through an allowlist that can only shrink.
4. **Pixel-exact rendering** on the 2880×1800 (~242 PPI) Samsung OLED at 90 Hz.
5. **Tuned for this machine,** in measured steps: first power gating of the dGPU and the
   charge limit, then a Zen 3 kernel once measurements show it helps.
6. **HIG-native customisation** through supported APIs only
   ([ADR 0011](adr/0011-customisation-boundaries.md)).

Non-goals:

- Other machines.
- X11 and the GNOME Classic session.
- Client-side rpm-ostree layering.
- Custom GTK or libadwaita themes.
- Hand-maintained forks of large upstream projects.
- Bit-for-bit reproducible builds. Every input is still pinned.

## 2. The system at a glance

```
 GitHub (main branch, protected)                         Fedora infrastructure (trusted root)
 ┌───────────────────────────────────────────────┐       registry.fedoraproject.org/fedora-bootc:45@digest
 │ rust.yml     fmt·clippy·test·deny (F45 ctr)   │       Fedora 45 repos (+ named updates-testing
 │ rpms.yml     apex RPM  ─▶ ghcr apex-rpms:<k>  │        builds until GA, by NEVRA allowlist)
 │ libfprint.yml patched  ─▶ ghcr apex-libfprint │                    │
 │ image.yml    build-rootfs ▸ checks ▸ rechunk  │◀───────────────────┘
 │              ▸ push apex-testing@digest ▸ sign(CI key)
 │ qualify.yml  KVM: install ▸ boot ▸ upgrade ▸ rollback ▸ negative tests
 │              ▸ [release env] copy to apex ▸ sign(release key) ▸ tag :45
 └───────────────────────────────────────────────┘
                              │ bootc pull (strict policy, release keys)
 ┌──────────────────────────── laptop (M7400QC) ───────────────────────────────────────┐
 │ UEFI ▸ shim ▸ GRUB (static cfg + Apex boot counter) ▸ ostree deployment (composefs) │
 │   apex-boot-assess (Rust): health checks ▸ green / red ▸ counted rollback           │
 │   apex-updated (Rust, system bus, polkit) ── single writer, fork/exec ──▶ bootc      │
 │        ▲ D-Bus                                                                       │
 │   apexctl (CLI) · Updates app + session notifier (M2) · Shell extension (M2+)        │
 └──────────────────────────────────────────────────────────────────────────────────────┘
```

## 3. Delivery model: bootc on the ostree backend

The OS is one OCI image, consumed by `bootc` ([ADR 0001](adr/0001-image-based-bootc.md)).

- **Backend.** The default ostree backend with composefs, a read-only sysroot, and GRUB2
  with shim and bootupd. The composefs-native backend with sealed UKIs is still
  experimental in bootc 1.16.
- **Base content.** The builder is the digest-pinned `fedora-bootc:45`, pulled from
  `registry.fedoraproject.org`. quay.io deletes digests as soon as no tag points at them
  (within about a day), so a pin to quay.io stops working almost at once.
  It runs `bootc-base-imagectl build-rootfs --manifest=minimal` with the Apex install
  list and `--exclude` guards (`image/packages/`). The result is copied `FROM scratch`.
- **One depsolve.** Apex's own RPMs, the patched libfprint and later any kmods reach the
  compose through a local repository: `createrepo_c` generates it, it has priority 1, and
  `excludepkgs=libfprint` is set on the Fedora repos. There is therefore exactly one
  dependency resolution, and it runs under the same exclude guards. A derived-stage
  `dnf install`, which would bypass the guards, is not used.
- **Fallback base.** If `build-rootfs` with the GNOME package set does not converge on
  GitHub runners, the fallback is `FROM fedora-bootc:45` followed by
  `dnf5 install --setopt=install_weak_deps=False` and a rechunk. This is recorded in
  [ADR 0013](adr/0013-build-pipeline.md).
- **One kernel per image.** `bootc container lint` enforces this, and CI builds the
  initramfs for that exact kernel.
- **UEFI only.** The final stage removes bootupd's BIOS component metadata, so
  `bootc install` never runs `grub2-install --target i386-pc` onto the disk the laptop
  shares with Windows. `grub2-pc` itself stays installed, because the minimal manifest
  requires `grub2`, which only it provides. An image check enforces this.
- **Fedora 45 pre-release.** Until GA, `updates-testing` stays disabled. Only the named
  Bodhi update for GNOME 51.0 (FEDORA-2026-48a7996f9c: GTK 4.24.0, libadwaita 1.10.0,
  GLib 2.90, …) is admitted, through an NEVRA allowlist. A dated check fails the build
  once GA plus 7 days have passed while that allowlist is still non-empty.

## 4. Build and publish pipeline

([ADR 0013](adr/0013-build-pipeline.md))

| Workflow | Job and privileges | Output |
|---|---|---|
| `rust.yml` | PRs and pushes; runs in a digest-pinned `registry.fedoraproject.org/fedora:45` container; read-only token | fmt, clippy `-D warnings`, tests, `cargo deny` |
| `rpms.yml` | key = hash(crates, packaging, Makefile, Cargo.toml, Cargo.lock, the build recipe and repository options, Fedora rust NEVR); on a cache miss, `rpmbuild` in fedora:45; artifacts carry build-provenance attestations that the image job verifies | OCI artifact `ghcr.io/sekirokenjii/apex-rpms:<key>` |
| `libfprint.yml` | key = Fedora libfprint NEVR plus a hash of the enabled patches; rebuilds Fedora's SRPM after verifying its signature | `apex-libfprint:<key>`; if a patch fails to apply, the job **degrades** to stock libfprint and opens an issue |
| `image.yml` | no secrets during the build; rootful podman on a graphroot on `/mnt`; `build-rootfs` → image checks → rechunk with `--previous-build` → push to `apex-testing` under a unique tag → sign that digest (CI key, environment `testing`) → tag `:45` | `ghcr.io/sekirokenjii/apex-testing:45` |
| `qualify.yml` | KVM with OVMF: `bootc install to-filesystem` of the candidate onto an ESP + ext4 `/boot` + btrfs root, like the laptop; boot; assertions; upgrade from the current stable; rollback test; negative signature tests | on success, in environment `release` (main only, manual approval): `skopeo copy --preserve-digests` to `ghcr.io/sekirokenjii/apex`, sign with the release key, move `:45` if the version increases |

Rules:

- **Only published images are tested.** Qualification boots the digest that was already
  signed. Promotion copies that same digest; nothing is rebuilt.
- **Degrade instead of blocking.** A libfprint patch that no longer applies, or (in M2)
  an NVIDIA kmod that does not build, produces a working image with the label
  `io.github.sekirokenjii.apex.degraded=<what>` rather than stopping all security
  updates. The label is shown in `apexctl status`.
- **Skip unchanged builds.** A content key is stored as a label. It hashes the base
  digest, the degraded list, the apex-rpms and apex-libfprint keys, the git trees of
  `image/` and `hardware/`, and every installed package's name, EVR and arch. A scheduled run
  whose key equals the current `45` publishes nothing.
- **Rechunk continuity.** The rechunk step always passes
  `--previous-build docker://ghcr.io/sekirokenjii/apex-testing:45`, so daily updates
  download only what changed.
- **Monotonic promotion.** The `45` tag only moves to a strictly higher
  `org.opencontainers.image.version` (`45.YYYYMMDD.N`), built from a commit that
  descends from the tag's current commit. A deliberate rollback is a revert commit. Promotion runs under
  `concurrency: promote-45` without cancellation.
- **Supply-chain hygiene.** Every action is pinned by full SHA. Third-party actions never
  run in jobs that hold secrets. Checkout uses `persist-credentials: false`. The token is
  read-only except in the publish jobs.

## 5. Updates

([ADR 0008](adr/0008-update-policy.md))

### 5.1 Channels and trust

| Repository | Signed with | Tags |
|---|---|---|
| `ghcr.io/sekirokenjii/apex` | release key (primary), plus an offline backup key | `45` (stable), `45.YYYYMMDD.N` |
| `ghcr.io/sekirokenjii/apex-testing` | CI key | `45`, `sha-<git>-<run>` |

Being in `apex` is what "qualified" means. There is no label for it
([ADR 0012](adr/0012-trust-and-keys.md)).

The laptop's bootc calls always run with
`CONTAINERS_POLICY_JSON=/usr/share/apex/containers/policy.json`. That policy:

- defaults to reject;
- accepts `ghcr.io/sekirokenjii/apex` only when signed with a release key;
- accepts `apex-testing` only with the CI key;
- has no transport-wide accept rules.

The general container policy used by podman and toolbox stays Fedora's lenient default,
because that is a different trust decision.

### 5.2 Engine (`apex-update` crate, pure) and daemon (`apex-updated`)

The engine rebuilds its state from `bootc status --format=json --format-version=1`
when the daemon starts, before and after every queued operation, and on reads when the
state is older than 10 s (which also covers bootc runs made outside the daemon). It never
runs `bootc status` while its own bootc operation holds the sysroot lock. The daemon
persists only (contract §4):

- the user's intent (`/var/lib/apex/intent.json`: `{digest, created}`);
- a denylist of digests that failed health checks;
- the last remote check result;
- the last boot's health failure (`health-failure.json`, shared with `apex-boot-assess`).

The daemon is the **only** component that runs bootc. All operations go through one
queue.

States are derived in this order of precedence: incompatible, usr-overlay,
rollback-queued, ready-for-reboot, staged, finalize-failed, health-failure (only while
its digest is booted), available, up-to-date.

| Derived state | Condition |
|---|---|
| `UpToDate` | the remote digest equals the booted or staged digest |
| `Available` | remote digest ∉ {booted, staged}, not denylisted, and remote version > booted version |
| `Downloading` | an operation is running (`--progress-fd` is used only if the bootc version supports it; otherwise progress is unknown) |
| `Staged` | a staged deployment exists with `downloadOnly = true` |
| `ReadyForReboot` | a staged deployment exists with `downloadOnly = false` (the user applied it) |
| `RollbackQueued`, `Incompatible`, `UsrOverlay` | taken from the bootc status flags; automatic operations stop |
| `FinalizeFailed` | `/boot/ostree/finalize-failure.stamp` exists, or `ostree-boot-complete` failed |
| `HealthFailure` | the last boot of a newly applied digest was red |

Automatic run (a systemd timer, daily and 15 minutes after boot):

1. `bootc upgrade --check`.
2. If `Available`, check the gates.
3. If the gates pass, `bootc upgrade --download-only`.
4. Skipped entirely while an intent exists, so it never re-locks or replaces what the
   user chose.

The gates are pure functions over a `SystemSnapshot`. Each one returns a reason that can
be shown to the user:

- **Power:** AC, or battery ≥ 50 % (≥ 20 % to unlock).
- **Network:** not metered (read from NetworkManager).
- **Space:** `/sysroot` free ≥ image size + 2 GiB; `/boot` free ≥ 1.2 × the staged
  kernel plus initramfs.
- **Denylist:** the digest has not failed health checks before.
- **bootc flags:** no `rollbackQueued`, `incompatible` or `usrOverlay`.
- **Version:** the version is newer; a downgrade needs explicit confirmation.

`Apply(expected_digest)`:

1. Checks that the staged digest equals `expected_digest` and is still download-only.
2. Reads the version from the **staged deployment's** `/usr/share/apex/manifest.json`
   (verified content, not registry labels) and checks it increased.
3. Checks the `/boot` space gate.
4. Arms the boot counter ([§5.3](#53-boot-assessment-and-rollback)).
5. Runs `bootc upgrade --from-downloaded` to unlock the stage for the next boot.
6. Writes the intent.

The daemon **never reboots**. The user's session requests the reboot through
`org.gnome.SessionManager.Reboot`, so unsaved-work inhibitors and the end-session
dialog still apply. The CLI tells the user to reboot. Soft reboot is deferred until CI
shows it is often eligible.

Cancel, meaning discard a staged update, re-locks it with `bootc upgrade
--download-only`. That pulls the channel tag, so it needs the network and may stage a
newer build, still locked. The daemon accepts the result only when bootc reports a
locked stage; otherwise the arming and the intent stay. Cancel never calls
`bootc rollback`.

Concurrency: all bootc calls go through one queue. A Check during a download answers
Busy, the Check rate limit counts successful checks only, identical calls join the
running operation, and fallback reports go to the front of the queue.

Fedora major upgrades (45 → 46) are a documented manual runbook until Fedora 46
branches: switch with `--download-only`, pin the last F45 deployment, and snapshot
`/var` first. They will be automated after that.

### 5.3 Boot assessment and rollback

([ADR 0009](adr/0009-boot-assessment.md))

greenboot-rs 0.16.4 does not fit this laptop:

- It arms rollback for download-only stages.
- It reboots by itself, even inside a user session.
- It starts counting only after the first failure, so a panic before userspace is never
  rolled back.
- Its default checks turn DNS failures into rollbacks.

Apex replaces it with **`apex-boot-assess`** (Rust). It uses the same GRUB environment
mechanism under Apex-owned variable names:

- **Arming.** Only `Apply` arms: it sets `apex_target=<digest> apex_counter=3
  apex_ok=0` in grubenv. These are Apex-owned names: Fedora's `grub2-set-bootflag`
  writes `boot_success` after every login, which would otherwise mark a failed armed
  boot as good. The static GRUB snippet (`08_apex-bootcount.cfg`) decrements the counter
  on every armed boot that has not been confirmed, sets `fallback=1` so a kernel GRUB
  cannot load falls through at once, and after three attempts boots entry 1, the
  previous deployment. The kernel arguments `panic=10 rd.shell=0 rd.emergency=reboot`
  turn panics and initramfs failures into reboots, so the counter moves.
- **Writes to grubenv.** bootc mounts `/boot` read-only. Every write runs
  `grub2-editenv` inside a private mount namespace in which `/boot` has been remounted
  read-write, so the host never sees a writable `/boot`.
- **Checks.** Each check has a 30 s timeout:
  - a greeter or user session has been active for 20 s;
  - NetworkManager and logind are active;
  - `apex-updated` answers `Ping` (which fails when bootc status cannot be read);
  - no failures among an explicit list of units;
  - `/boot/grub2/grub.cfg` contains the Apex snippet marker exactly once, before the
    BLS entries.

  Hardware checks (audio `init_verbs`, charge limit, dGPU runtime PM) are **reported
  only**, never rollback triggers.
- **Green:** set `apex_ok=1`, unset the counter and `apex_target`, clear the intent.
- **Red, armed, nobody logged in:** reboot so the counter moves.
- **Red, armed, user session active:** do not reboot. Notify, and offer "Roll back" (an
  explicit polkit action).
- **Red, not armed** (an ordinary boot with no update): report only.
- **Fallback detected** (booted digest ≠ `apex_target` and the counter is exhausted):
  1. `apex-boot-assess` writes the hedge `apex_counter=3`, so a lost reply can never
     leave GRUB pointing at the failed target.
  2. It sends `ReportBoot("fallback")`. The daemon runs `bootc rollback` so the good
     deployment becomes the default, denylists the target, and unsets the variables
     before replying.
  3. On a lost reply the assessment reads `bootc status` again and keeps the hedge
     unless the rollback happened.
- **Target skipped** (another deployment runs while the target may still be the default,
  for example after `fallback=1` or a manual menu pick): the arming stays, so GRUB goes
  on counting the target.
- **Arming precondition** (contract §5): the booted deployment comes from an image, a
  different image is staged, and the booted deployment is neither armed nor recorded as
  failed. After finalization ostree keeps only the new deployment and the booted one, so
  entry 1 exists even on a fresh install, and it is a confirmed deployment.
- **Emergency shell while counting:** drop-ins for `emergency.service` and
  `rescue.service` reboot after 60 s when an armed boot is being counted, so the counter
  keeps moving. A normal emergency shell is not affected.
- **Race with Apply:** `Apply` answers Busy while `apex-boot-assess.service` is still
  assessing the current boot, so a fresh arming can never be cleared by a stale
  assessment.

The GRUB snippet is installed at `bootc install` time (bootupd static configs). A
required first-boot check verifies that `/boot/grub2/grub.cfg` contains the Apex snippet
marker.

## 6. Hardware enablement (M7400QC)

Machine facts live in [`hardware/m7400qc/profile.toml`](../hardware/m7400qc/profile.toml).
The files derived from it (HDA patch firmware, `monitors.xml`) are rendered by
`apexctl profile render`, and `apexctl profile render --check` fails CI when the committed files differ. Acceptance tests
with numbers are in [hardware/ACCEPTANCE.md](hardware/ACCEPTANCE.md).

### 6.1 Firmware

Weak dependencies are off, so these firmware packages are listed explicitly:

- `amd-gpu-firmware` (Cezanne PSP/DMUB/VCN)
- `amd-ucode-firmware` (early microcode 0x0a500012)
- `iwlwifi-mvm-firmware` (AX200; pulls in `iwlbluetooth-firmware`)
- `linux-firmware`

Image checks confirm the specific files exist, and that the amdgpu firmware and the
microcode cpio are inside the initramfs.

### 6.2 Audio: Realtek ALC294, subsystem `1043:1ab2`

([ADR 0004](adr/0004-audio-hda-patch-firmware.md))

No kernel tree has a quirk for this machine, and there is no smart amplifier. The fix
is an HDA patch firmware file whose `[verb]` lines the HDA core replays at probe and on
every runtime and system resume. **The values ship only after they are measured on this
unit.**

1. `hardware/m7400qc/audio/coef-dump.sh`, run with sudo, records COEFs 0x0f, 0x1b and
   0x40 after a cold boot, after a warm reboot from Windows, and with the fix loaded.
2. The measured cold value goes into `profile.toml`. The verb written is
   `cold_value | 0x0400` for COEF 0x1b (bit 10), plus 0x0f only if the dump shows it
   matters.
3. The renderer refuses to produce the firmware file without a measured value. Until
   then the image ships without the audio fix, labelled `degraded=audio`.
4. `snd-hda-intel patch=` gets four identical entries, because slots are assigned by
   probe order.
5. An image check confirms that `snd-hda-intel` is not in the initramfs.
6. A reported check confirms that `init_verbs` contains the generated verbs.

The upstream kernel quirk (`ALC294_FIXUP_ASUS_COEF_1B_BIT10`) is prepared in
`packaging/kernel/` and is sent upstream only with the measured values and a
Tested-by. A CI canary opens an issue when Fedora's `snd-hda-codec-alc269.ko` contains
the SSID. The firmware file is removed by hand, after the hardware test passes without
it.

The procedure can run **today on the Ubuntu dev install** of this laptop (its kernel has
`CONFIG_SND_HDA_PATCH_LOADER=y` and `hda-verb` is installed), before Apex exists.

### 6.3 Fingerprint: ELAN `04f3:0c6e`

([ADR 0006](adr/0006-fingerprint-libfprint-rebuild.md))

libfprint's `elan` driver treats any pre-scan status other than 0x55 as a protocol
error. The upstream fix (MR !655) is unmerged. `libfprint.yml` rebuilds Fedora's own
SRPM with the patches listed in `packaging/libfprint/series`:

- **0001** gives 0x0c6e its own quirk bit, so it gets the existing 0x00/0xaf retry path.
- **0002** bounds that retry and adds lift semantics. A transient status after at least
  one frame means the finger was lifted, so the capture completes. With zero frames the
  driver backs off (10, 50 then 200 ms) within the command timeout and then takes the
  existing timeout path. Without this, the lock screen could poll at 100 Hz forever.
- The dark-frame and settle-delay patches stay in the tree but are **not** in `series`,
  until the diagnostic log shows their trigger.

Fingerprint is **not** in PAM at M1. Enrollment works in Settings > Users. It is
enabled for screen unlock only, never `system-auth`, sudo or polkit, through an Apex
authselect vendor profile once the genuine and impostor score test passes. The sensor
is in the power key, so `power-button-action='interactive'`: pressing it on the lock
screen does nothing.

### 6.4 GPU and power

- **dGPU (M1):** no NVIDIA driver. nouveau and nova-core are blacklisted, also in the
  initramfs. A udev rule sets `power/control=auto` for the GA107 when it is added, so
  the unbound device can reach D3cold through its root port. The panel and HDMI are on
  the iGPU. Acceptance: at least 95 % runtime-suspended over 10 minutes idle. Two ways
  to use the dGPU come in M2: NVIDIA 615 open kmods signed with a MOK
  ([ADR 0012](adr/0012-trust-and-keys.md)), or nouveau with NVK.
- **CPU:** amd-pstate in EPP mode (Fedora's default). tuned-ppd with an
  `apex-performance` profile that drops the server VM tunables.
- **Battery:** UPower's default hwdb already sets an 80 % end threshold, but it never
  sees this laptop's threshold attribute, because asus-wmi adds it after BAT0 appears
  and sends no uevent. Apex ships three things:
  - a udev rule that re-triggers BAT0 when `asus-nb-wmi` binds;
  - an `upower.service` drop-in that waits, with a bound, for the attribute;
  - a tmpfiles entry that turns the limit on by default (`charging-threshold-status` =
    `1`, created only when missing, so the user's later choice in Settings stays).
- **Kernel:** the stock Fedora kernel in M1. The Zen 3 kernel fork (COPR) is M2,
  gated on power and latency measurements and on an automated rebase with fallback
  ([ADR 0005](adr/0005-kernel-fedora-fork.md)).
- **OLED:** amdgpu defaults: no ABM on OLED, PSR off on DCN 2.1, and no VRR range in
  the EDID. The dark style is the default.

## 7. Desktop

### 7.1 Package policy and app set

([ADR 0007](adr/0007-no-legacy-policy.md))

The desktop is installed from explicit lists (`image/packages/*.txt`) with weak
dependencies off, guarded by `--exclude` and by the legacy gate (`image/checks/legacy.sh`).
That gate queries `rpm -q --whatrequires` for `libgtk-3.so.0` and the X server, and
compares the result with `image/audit/legacy-allowlist.txt` as a set difference. Each
allowlist entry names the milestone that removes it.

| Area | Apex default | Channel |
|---|---|---|
| Core | GNOME Shell, Settings, Nautilus + Sushi, Ptyxis, Text Editor, Loupe, Papers, Showtime, Decibels, Snapshot, System Monitor, Baobab, Calculator, Characters, Clocks, Calendar, Contacts, Weather, Font Viewer, Logs, Yelp, Tour, Extensions | image RPM |
| Browser | Epiphany (GTK4) in the image; Firefox preinstalled | RPM / Flatpak |
| Apps | Bazaar (GNOME Circle), preinstalled; Flathub remote configured | Flatpak |
| Disks | gnome-disk-utility 46 (GTK3, allowlisted until GDU 51 ships as GTK4) | image RPM |
| Secrets | oo7 (daemon, PAM, portal); Key Rack via Flathub | RPM |
| Never shipped | gnome-terminal, gedit, eog, evince, totem, cheese, rhythmbox, seahorse, gnome-keyring, gnome-classic-session, the Xorg server, PackageKit, gnome-software | none |

- **Flatpaks.** Preinstalls come from `/usr/share/flatpak/preinstall.d` through a
  network-online oneshot, plus a retry timer that covers a first boot without network.
  `apex-flatpak-update.timer` updates system Flatpaks every 6 hours, only on AC power
  and on an unmetered connection.
- **Firmware updates.** gnome-firmware (GTK4).
- **Locale.** `glibc-langpack-en`, `glibc-langpack-vi` and `hunspell-vi`.
- **Accessibility.** `orca`.
- **Toolbox.** `podman` and `toolbox` for the developer loop.

### 7.2 Input methods

IBus is GNOME Shell's input framework. The defaults are input sources
`[('xkb','us'), ('ibus','m17n:vi:telex')]`, Super+Space to switch, and per-window
sources, so a terminal can stay in English. ibus-bamboo is not shipped: it links GTK3,
libX11 and libXtst, and its mouse capture triggers Remote Interaction prompts. A Rust
IBus engine with auto-restore of English words is specified in the roadmap (M3).

### 7.3 Vendor defaults and customisation

([ADR 0011](adr/0011-customisation-boundaries.md))

Defaults ship as `/usr/share/glib-2.0/schemas/90_apex.gschema.override`, compiled at
build time, with no dconf locks. It overrides only keys that differ from upstream:

- `color-scheme`
- `favorite-apps`
- `input-sources`
- `power-button-action`
- `enabled-extensions` (from M2)

Upstream UIs own upstream settings, and Apex links to them. Apex's own app covers only
what is unique to Apex. The only files Apex places in `/etc` are `/etc/xdg/monitors.xml`,
the fontconfig link, `/etc/tuned/ppd.conf` (tuned-ppd reads its profile mapping only
from there), and the symlinks that `systemctl enable`, `mask` and `set-default` create
under `/etc/systemd/system`.

## 8. Display: pixel-exact by default

([ADR 0003](adr/0003-display-integer-scale.md))

- **Default scale 2 on the panel.** `/etc/xdg/monitors.xml` is rendered from the profile:
  `eDP-1`, SDC, `0x4154`, serial `0x00000000`, rate `90.001434326171875`. At scale 2
  every surface is 1:1: GTK4, GNOME Shell's Clutter/St UI, the cursor, GTK3 and HiDPI
  Xwayland. At 5/3 all but GTK4 are resampled, and GTK4 borders only align every 3
  logical pixels. The workspace is 1440×900; for more room the supported choice is 5/3,
  not text scaling.
- **Docked.** mutter recomputes the scale for any monitor set it has no stored config
  for. From M2, the user-session agent sets the panel back to 2 the first time a new set
  appears, using the "Keep changes?" pattern, and suggests scale 1 for the external
  monitor. The AOC Q24G2 at scale 1 is about 123 effective DPI, close to the panel's 121
  at scale 2, so windows keep the same physical size on both screens.
- **Fonts.** `font-rendering=automatic` (grayscale antialiasing, slight hinting,
  subpixel positioning), and fontconfig `10-sub-pixel-none` for clients that are not
  GTK4. No mutter experimental keys (mutter 51 removed the old key).
- **Custom drawing.** Our own drawing uses GTK 4.24's `Snapshot::set_snap`. That
  affects only custom drawing: stock libadwaita widgets are not snapped at 5/3.
- **Migration.** A user `~/.config/monitors.xml` overrides the system default. The
  first-run Setup checklist (M2) offers "Sharpest (200 %, recommended)" or "More space
  (167 %)".

## 9. Our components (Rust workspace)

| Crate | Milestone | Responsibility |
|---|---|---|
| `apex-bootc` | M1 | Lenient serde model of the bootc status v1 API; progress JSON Lines; `Bootc` invocation builder (argv from enums only, `env_clear`, fixed `PATH`, strict `CONTAINERS_POLICY_JSON`); `CommandRunner` trait with a tokio implementation and a scripted fake |
| `apex-update` | M1 | Pure engine: snapshot, gates, state derivation, intent and denylist stores (atomic writes), version ordering, `rpmvercmp` and manifest diff |
| `apex-boot` | M1 | Boot assessment: grubenv codec, the pure decision table, check runner with timeouts; binary `apex-boot-assess` |
| `apex-dbus` | M1 | The `io.github.sekirokenjii.Apex.Update1` contract: names, error names, value types and the zbus proxy shared by every client |
| `apex-updated` | M1 | System bus service: single operation queue, polkit (system-bus-name subject), rate limiting, sd-notify, hardened unit |
| `apexctl` | M1 | CLI: `status`, `update …`, `profile render|check`, `hw audio snapshot`, `hw report` |
| Updates app | M2 | GTK4/libadwaita app `io.github.sekirokenjii.Apex.Updates`: Updates, This Device (read-only) and Setup pages, plus a session notifier |
| Shell extension | M2+ | `apex@sekirokenjii.github.io`: TypeScript to GJS, async D-Bus only, settings in `io.github.sekirokenjii.Apex.Shell`, gated by a headless Shell smoke test in CI |

Rules:

- **Pure core, thin shells.** Every decision is a pure function with unit tests and
  property tests. Binaries only perform I/O. Clock, power, network, filesystem space and
  polkit sit behind traits.
- **Async.** Daemons use tokio `current_thread` with zbus on tokio. GUI code (M2) uses
  the GLib main loop.
- **bootc drift.** Parsing is lenient: no `deny_unknown_fields`, and `#[serde(other)]`
  on enums. The fixtures come from bootc's own test data plus captures from the qualify
  VM, one set per bootc version. The qualify job runs `apexctl status --json` in the VM
  as a contract test.
- **Root daemon hygiene.**
  - It reads only `/usr/share/apex` and `/etc/apex`, never a user's home.
  - It has no writable D-Bus properties.
  - bootc argv is built from enums plus the compile-time image references.
  - The Check method is rate-limited.
  - The unit is hardened within what bootc tolerates.
- **IDs.** One family, prefix `io.github.sekirokenjii.Apex`:
  - apps `…Apex.<App>`
  - bus `…Apex.Update1`
  - polkit `io.github.sekirokenjii.apex.update.*` (lowercase)
  - labels `io.github.sekirokenjii.apex.*`
  - extension UUID `apex@sekirokenjii.github.io`
- **Packaging.** A single `apex` RPM (with `apex-updates` split out in M2) is built from
  one `make install` target that is also used for development. Release is derived from
  git. Binaries are built with `cargo auditable`.

## 10. Repository layout

```
Cargo.toml  Makefile  Justfile  rust-toolchain.toml  deny.toml
crates/       apex-bootc apex-update apex-boot apex-dbus apex-updated apexctl
hardware/     m7400qc/profile.toml, audio/ (coef-dump.sh, try-fix.sh), generated/ (rendered monitors.xml, .fw)
image/        Containerfile, packages/*.txt, system_files/ (rootfs overlay), checks/, audit/
packaging/    apex.spec, libfprint/ (series, patches, build.sh), kernel/ (M2 overlay, ALC294 quirk)
.github/      workflows
docs/         ARCHITECTURE, THREAT-MODEL, ROADMAP, INSTALL, RECOVERY, adr/, hardware/
```

## 11. Quality gates

- **Rust:** fmt, clippy (pedantic, `-D warnings`), unit, property and snapshot tests,
  and `cargo deny`. The toolchain is pinned to Fedora's rust (1.98.1), and CI asserts
  that the two match.
- **Image:**
  - `bootc container lint --fatal-warnings`, with skips justified in a file that can
    only shrink;
  - the legacy gate;
  - firmware files present;
  - exactly one kernel;
  - initramfs contents;
  - no private keys in any layer;
  - no `macros.verify` override and no `--nosignature`;
  - the profile renders match the committed files;
  - desktop, metainfo, gschema, D-Bus, polkit and systemd files all validate.
- **Qualification:** a real `bootc install` under KVM with OVMF, then:
  - health green and grubenv clean;
  - upgrade from the current stable;
  - a reboot with a download-only stage present, with no change;
  - an injected red check leads to a counted rollback;
  - unsigned, wrong-key and foreign-registry references are all rejected.
- **Hardware:** [hardware/ACCEPTANCE.md](hardware/ACCEPTANCE.md), run on the laptop.
  Each hardware fix has a numeric pass criterion.

## 12. What the design review changed

| Finding | Change |
|---|---|
| greenboot-rs rolls back when a download-only stage exists; reboots inside the session; never counts pre-userspace failures | `apex-boot-assess` with arming on apply, `panic=10` and emergency-reboot kargs, and no reboot while a session is active (ADR 0009) |
| An automatic download could re-lock or replace the update the user chose | Intent model; `Apply(expected_digest)`; a single writer |
| A qualification label cannot exist on an already-signed digest | Separate testing and release repositories and keys; qualification = membership in `apex` (ADR 0012) |
| `matchRepository` allows tag substitution and downgrade | Monotonic version checks in the daemon and in promotion; staleness warning |
| Firmware and microcode missing with weak dependencies off | An explicit firmware list plus file checks |
| The charge limit is never applied (udev ordering, off by default) | Re-trigger rule, UPower drop-in, tmpfiles default-on |
| Audio COEF values unmeasured | Measurement becomes a gate; the image degrades until it is done |
| The fingerprint retry can poll forever | A bounded retry with lift semantics ships together with 0001 |
| Fingerprint enters sudo and polkit through `with-fingerprint` | Not in PAM at M1; later unlock-only through a vendor profile |
| "Apex Settings" duplicates GNOME Settings and breaks the HIG naming rules | The Updates app (M2) covers only Apex concepts and links to Settings (ADR 0011) |
| Monolithic build, disk budget, unproven build-rootfs | Split jobs, OCI artifacts, a graphroot on `/mnt`, a spike and a fallback (ADR 0013) |
| First install would wipe Windows and Ubuntu | An install ADR: `to-filesystem` onto a prepared LUKS2 + btrfs layout, keeping Windows (ADR 0010) |
| NVIDIA, MOK, COPR kernel and third-party repos in M1 | Moved to M2; the M1 supply chain is Fedora plus Apex only |
