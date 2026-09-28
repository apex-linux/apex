# ARCHITECTURE.md delta

Status: proposed (2026-09-28), updated for the owner's answers of 2026-09-28. Path in
the repository: `docs/reviews/2026-09-28-architecture-delta.md`.

Nothing in the repository changes before the owner accepts
[ADR 0014](../adr/0014-engine-level-desktop.md) and
[ADR 0015](../adr/0015-cachyos-kernel-and-nvidia.md) and the baseline commit exists.
This delta is applied after that point, in the same change that replaces
`docs/ROADMAP.md` with the [proposed roadmap](2026-09-28-roadmap.md). Each cut named
below is its own commit on top of the baseline.

Line numbers refer to `docs/ARCHITECTURE.md` at the baseline commit (572 lines). Apply
the edits from the bottom up, so earlier line numbers stay valid. E7 waits for Fedora 45
GA and is applied later, found by its quoted text.

Each edit quotes the old text and gives the new text. A block longer than 14 lines is
quoted by its first three and last two lines, with the exact line range. Everything in
the range is replaced.

After these edits, the document describes the target system, in about 850 lines
(from 572). It absorbs the build, kernel and desktop detail that the ADRs no longer
carry. A part that is not built yet names its slice in the proposed roadmap, for example
(S1a). The tag is removed when the slice ships. The update and boot stack stays at its
frozen scope. Its contracts live in the D-Bus XML and the Rust code.

The owner answered the decision sheet in the [review](2026-09-28-review.md) on
2026-09-28 (§5.3): the recommended default for every row, except these. Slice tags follow
the revised [roadmap](2026-09-28-roadmap.md); step W is the Windows removal.

| # | Answer | Edits |
|---|---|---|
| 1, 2 | A rebuilt gnome-shell is the primary mechanism. The Apex SCSS enters the package through an `@import` hook; the shipped CSS is moved aside in `%prep`. ADR 0011 is still superseded. | E1, E3, E4, E5, E8, E17, E19, E20, E21, A1 |
| 6 | Super+Space opens Spotlight. Input switching moves to Super+Alt+Space. | E16, E17 |
| 14 | Dynamic blur on every drawn surface, with the drawn saturation. Reduce Transparency turns it off. | E17, E21 |
| 17 | The recommended default, and a plan for the simplification after the owner deletes Windows | E9 |
| 22 | The CachyOS GCC kernel, and NVIDIA's open modules built for exactly that kernel and signed with that build's key ([ADR 0015](../adr/0015-cachyos-kernel-and-nvidia.md)). Secure Boot is off today. | E1, E3–E6b, E8, E9, E11, E13, E13b, E14, E19–E21 |
| 26 | Build the `design/SPEC.md` §8 items now, with the rebuilt packages they need. Items settled by decisions 4, 5, 8, 10, 11, 19 and 27 keep those defaults. The privacy indicators stay. | E4, E8, E17, E19, E20 |

A1 and A2 edit ADR 0002 and ADR 0007 in the same commit. The status-line changes of the
other ADRs are listed in the review (§4) and in ADR 0015.

| Edit | Section | Lines | Action |
|---|---|---|---|
| E1 | Introduction | 3-8 | replace |
| E2 | Review history | 10-13 | replace |
| E3 | §1 Goals and non-goals | 17-41 | replace |
| E4 | §2 The system at a glance | 43-64 | replace |
| E5 | §3 One depsolve | 78-82 | replace |
| E6 | §3 Fallback base | 83-86 | delete |
| E6b | §3 One kernel per image | 87-88 | replace |
| E7 | §3 Fedora 45 pre-release | 93-96 | delete at GA |
| E8 | §4 Build and publish pipeline | 98-131 | replace |
| E9 | §5 Updates (5.1 to 5.3) | 133-302 | replace |
| E10 | §6 Introduction | 306-309 | replace |
| E11 | §6.2 Audio | 323-351 | replace |
| E12 | §6.3 Fingerprint, driver text | 357-367 | replace |
| E12b | §6.3 Fingerprint, PAM | 369-373 | replace |
| E13 | §6.4 dGPU | 377-382 | replace |
| E13b | §6.4 CPU | 383-384 | replace |
| E14 | §6.4 Kernel and OLED | 392-396 | replace |
| E14b | §7.1 Allowlist entries | 407-408 | replace |
| E15 | §7.1 App set rows | 412-413 | replace |
| E16 | §7.2 Input methods | 430-434 | replace |
| E17 | §7.3 Vendor defaults, and a new §7.4 | 436-453 | replace |
| E18 | §8 Display: scale, docking and migration | 459-477 | replace |
| E19 | §9 Our components | 479-517 | replace |
| E20 | §10 Repository layout | 519-529 | replace |
| E21 | §11 Quality gates | 531-554 | replace |
| E22 | §12 What the design review changed | 556-572 | delete |
| A1 | ADR 0002 | 1, 3, 17-21, 29-32 | replace |
| A2 | ADR 0007 | 3, 25-29 | replace |

## E1. Introduction (lines 3-8)

Why: The desktop is now a first-class part of the system, and not every component is
Rust. The kernel is CachyOS's (decision 22). The document describes the target and tags
what is not built yet.

Old:

````markdown
Apex is a personal, image-based Linux distribution for one machine: the ASUS Vivobook
Pro 14X OLED **M7400QC**. It is built on **Fedora 45** and **GNOME 51**, and every
component we write ourselves is in **Rust**. This document is the source of truth for
how the pieces fit together. Each non-obvious decision has an ADR in [`adr/`](adr/).
The security model is in [THREAT-MODEL.md](THREAT-MODEL.md) and the milestones are in
[ROADMAP.md](ROADMAP.md).
````

New:

````markdown
Apex is a personal, image-based Linux distribution for one machine: the ASUS Vivobook
Pro 14X OLED **M7400QC**. It is built on **Fedora 45**, **GNOME 51** and the
**CachyOS** kernel. Its desktop follows the owner's mockup in
[`design/mockup/`](../design/mockup/), specified in [design/SPEC.md](../design/SPEC.md).
Apex's own daemons, agents and tools are in **Rust**. Code that lives inside a GNOME
project is written in that project's language
([ADR 0014](adr/0014-engine-level-desktop.md)).

This document describes the target system. A part that is not built yet names its
roadmap slice, for example (S1a). Each non-obvious decision has an ADR in
[`adr/`](adr/). The security model is in [THREAT-MODEL.md](THREAT-MODEL.md) and the
slices are in [ROADMAP.md](ROADMAP.md).
````

## E2. Review history (lines 10-13)

Why: An architecture document does not carry a review changelog (§12 is deleted in
E22).

Old:

````markdown
Upstream facts were checked on 2026-09-23 and 2026-09-24, while Fedora 45 was in beta
(GA target 2026-10-20). The design then went through an adversarial review covering
upgrade safety, supply chain, hardware correctness, HIG and product, and build
feasibility. Section 12 records what that review changed.
````

New:

````markdown
Upstream facts were last checked on 2026-09-28, while Fedora 45 was in beta (GA target
2026-10-20).
````

## E3. §1 Goals and non-goals (lines 17-41)

Why: Goal 6 and two non-goals forbade the mockup (ADR 0014 supersedes ADR 0011). The
desktop moves to second place, because it is the owner's defining requirement, and it
is reached with a rebuilt gnome-shell (decisions 1 and 2). The dGPU is now used, and
the tuning goal names the CachyOS kernel (decision 22). App chrome keeps libadwaita's
palette (decision 4, default).

Old (lines 17-41, 25 lines, quoted in part):

````markdown
Goals, in priority order:

1. **Hardware that works.** Speaker audio on the ALC294 (codec subsystem `1043:1ab2`),
[… 20 lines …]
- Hand-maintained forks of large upstream projects.
- Bit-for-bit reproducible builds. Every input is still pinned.
````

New:

````markdown
Goals, in priority order:

1. **Hardware that works.** Speaker audio on the ALC294 (codec subsystem `1043:1ab2`),
   the ELAN `04f3:0c6e` fingerprint reader, the RTX 3050 on request with the GPU in
   D3cold otherwise, s2idle, all firmware, and the 80 % battery charge limit. Every fix
   is measured on the laptop, has an acceptance row, and is written so it can go
   upstream.
2. **The Apex desktop.** The mockup is the standard. Apex reaches it with a rebuilt
   gnome-shell that carries the Apex layer, and small patch series on other GNOME
   packages, within the budgets of [ADR 0014](adr/0014-engine-level-desktop.md). A
   deviation needs a hard reason and the owner's approval. Approved deviations are
   listed in ADR 0014.
3. **A fully modern GNOME.** GNOME 51 on Wayland only, GTK4/libadwaita apps only, and no
   X11 session. GTK3 is allowed only through an allowlist that can only shrink.
4. **Pixel-exact rendering** on the 2880×1800 (~242 PPI) Samsung OLED at 90 Hz.
5. **Safe updates.** OS, kernel and desktop update atomically in the background.
   Nothing reboots without the user, what gets applied is what the user saw, and a
   broken update rolls back from GRUB or on its own.
6. **Tuned for this machine,** in measured steps: the CachyOS kernel
   ([ADR 0015](adr/0015-cachyos-kernel-and-nvidia.md)), dGPU runtime D3cold, the
   charge limit, s2idle residency, then panel power (PSR, 60 Hz on battery).

Non-goals:

- Other machines.
- Fleet features: one laptop, one owner who is also its admin.
- X11 and the GNOME Classic session.
- Client-side rpm-ostree layering.
- Restyling libadwaita app chrome beyond the window radius.
- Forks of large upstream projects. Apex carries small patch series on Fedora SRPMs
  within the ADR 0014 budgets, and rebuilds the CachyOS kernel without changing its
  configuration (ADR 0015).
- Bit-for-bit reproducible builds. Every input is still pinned.
````

## E4. §2 The system at a glance (lines 43-64)

Why: The diagram showed five workflows, two repositories, two keys, KVM qualification
per candidate and an Updates app. The target has one workflow, one image repository,
two keys, two package lanes and a rebuilt shell.

Old (lines 43-64, 22 lines, quoted in part):

````markdown
## 2. The system at a glance

```
[… 17 lines …]
 └──────────────────────────────────────────────────────────────────────────────────────┘
```
````

New:

````markdown
## 2. The system at a glance

```
 GitHub (private repository): ci.yml only

 Builder VM on the laptop: just publish (S1d)         Upstream inputs, each with a pinned key
 ┌──────────────────────────────────────────────────┐  registry.fedoraproject.org/fedora-bootc:45@digest
 │ GNOME lane (S1a) rebuild.sh: gnome-shell         │  Fedora 45 repos, signed SRPMs, Koji (mutter pin)
 │   (+ desktop/shell), mutter pinned, libadwaita,  │  COPR kernel-cachyos SRPM, CachyOS signed tag
 │   gnome-control-center, nautilus, libfprint      │  negativo17 nvidia-kmod SRPM and userspace
 │ kernel lane (S1c): kernel-cachyos + kmod-nvidia, │                  │
 │   one key per build ▸ signed RPMs ▸ rpms.lock    │◀─────────────────┘
 │ image: build-rootfs ▸ G1 ▸ G2 ▸ rechunk ▸ push   │
 │   ▸ cosign sign ▸ :45 ▸ source artifact          │
 └──────────────────────────────────────────────────┘
                        │ bootc pull (strict policy, one key plus its backup)
 ┌─────────────────────────────────── laptop (M7400QC) ───────────────────────────────────┐
 │ UEFI ▸ shim ▸ GRUB (hidden menu S4, boot counter) ▸ Plymouth apex ▸ ostree (composefs) │
 │ kernel-cachyos + NVIDIA open modules (S1c) · AMD iGPU composites · dGPU on request     │
 │ apex-boot-assess: health checks ▸ green / red ▸ counted rollback                       │
 │ apex-updated (system bus, polkit) ── single writer, fork/exec ──▶ bootc                │
 │ gnome-shell .apexN: Apex theme and layer (S1a) · ApexDock (S2a) · glass (S2b)          │
 │   · Spotlight (S3a) · lock (S3b); mutter Fedora-signed, pinned to the shell's EVR      │
 │ libadwaita .apexN: live window radius (S2c)                                            │
 │ apex-session-agent (S1b): radius file · terminal caret · re-enable offer · updates     │
 │ Settings .apexN (S2c): Apex Desktop panel · Software Updates ◀── Update1 (D-Bus)       │
 │ Files .apexN (S2d): disk footer · item count · 72 px zoom                              │
 │ apexctl (CLI) ◀── Update1                                                              │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```
````

## E5. §3 One depsolve (lines 78-82)

Why: The lane now rebuilds gnome-shell, libadwaita, gnome-control-center, nautilus and
the kernel pair, and Fedora 45 enforces package signatures. The local repository is
therefore signed, and its package lists are generated. The NVIDIA userspace keeps
negativo17's signature in a repository of its own (ADR 0015 §5).

Old:

````markdown
- **One depsolve.** Apex's own RPMs, the patched libfprint and later any kmods reach the
  compose through a local repository: `createrepo_c` generates it, it has priority 1, and
  `excludepkgs=libfprint` is set on the Fedora repos. There is therefore exactly one
  dependency resolution, and it runs under the same exclude guards. A derived-stage
  `dnf install`, which would bypass the guards, is not used.
````

New:

````markdown
- **One depsolve.** Apex-built RPMs reach the compose through the local repository
  `[apex]`, with priority 1: Apex's own packages, the rebuilt GNOME packages
  (gnome-shell, libadwaita, gnome-control-center, nautilus and, if kept, libfprint)
  and the kernel pair (`kernel-cachyos` and `kmod-nvidia`, S1c). `createrepo_c`
  generates it, and from S1a its Apex-built RPMs are signed with the Apex RPM key. It
  also holds, unmodified and with Fedora's signature, the mutter build that gnome-shell
  requires, so the pin holds after Fedora moves on; `[apex]` trusts exactly the Apex
  RPM key and Fedora's key. Its `includepkgs` list, and the matching `excludepkgs` on
  the Fedora repos, are generated from the built and pinned RPM names. Fedora's kernel
  packages are excluded by exact name, so `kernel-headers` and `kernel-tools` stay
  Fedora's. A second local repository, `[apex-nvidia]` (S1c), holds the mirrored
  negativo17 userspace with negativo17's signature. There is still exactly one
  dependency resolution, and it runs under the same exclude guards. A derived-stage
  `dnf install`, which would bypass the guards, is not used.
````

## E6. §3 Fallback base (lines 83-86)

Why: `build-rootfs` converged and installed in the builder VM on 2026-09-24. The
proposal cuts the `COMPOSE=dnf` fallback and `spike.yml` (the review, §4, lists the
`Containerfile` lines).

Old:

````markdown
- **Fallback base.** If `build-rootfs` with the GNOME package set does not converge on
  GitHub runners, the fallback is `FROM fedora-bootc:45` followed by
  `dnf5 install --setopt=install_weak_deps=False` and a rechunk. This is recorded in
  [ADR 0013](adr/0013-build-pipeline.md).
````

New: delete these lines.

## E6b. §3 One kernel per image (lines 87-88)

Why: Images are built in the builder VM, not in CI. The kernel is the CachyOS pair
(decision 22), and the compose leaves `depmod` and the initramfs to the final stage.

Old:

````markdown
- **One kernel per image.** `bootc container lint` enforces this, and CI builds the
  initramfs for that exact kernel.
````

New:

````markdown
- **One kernel per image:** `kernel-cachyos`, with `kmod-nvidia` built for it (§4.2,
  S1c). `bootc container lint --fatal-warnings` enforces one kernel and an empty
  `/boot`. `build-rootfs` runs with `--no-initramfs`; the final stage runs `depmod` and
  generates the one initramfs.
````

## E7. §3 Fedora 45 pre-release (lines 93-96)

Why: Delete when Fedora 45 is GA (target 2026-10-20), in the same commit as the
admission code in `image/Containerfile`, the allowlist file and `t-repos.sh`. From GA
plus 7 days, the dated check fails every build until the allowlist is emptied.

Old:

````markdown
- **Fedora 45 pre-release.** Until GA, `updates-testing` stays disabled. Only the named
  Bodhi update for GNOME 51.0 (FEDORA-2026-48a7996f9c: GTK 4.24.0, libadwaita 1.10.0,
  GLib 2.90, …) is admitted, through an NEVRA allowlist. A dated check fails the build
  once GA plus 7 days have passed while that allowlist is still non-empty.
````

New: delete these lines.

## E8. §4 Build and publish pipeline (lines 98-131)

Why: The proposal replaces the repository's 12 workflows, including the five this
section describes, with one `ci.yml`. While the repository is private, images are built
and published from the builder VM (decision 20). The rebuild lane is generic, starts
with gnome-shell in S1a (decisions 1 and 2), and holds design packages instead of
degrading them. The kernel and NVIDIA lane is ADR 0015's pair. The hold limits are
decision 18's. The lane, hold and release detail moved here from ADR 0014 and ADR 0015.

Old (lines 98-131, 34 lines, quoted in part):

````markdown
## 4. Build and publish pipeline

([ADR 0013](adr/0013-build-pipeline.md))
[… 29 lines …]
  run in jobs that hold secrets. Checkout uses `persist-credentials: false`. The token is
  read-only except in the publish jobs.
````

New:

````markdown
## 4. Build and publish

([ADR 0014](adr/0014-engine-level-desktop.md),
[ADR 0015](adr/0015-cachyos-kernel-and-nvidia.md). This section supersedes
[ADR 0013](adr/0013-build-pipeline.md).)

While the repository is private, GitHub runs one workflow, `ci.yml`. Packages and
images are built in the builder VM ([`tools/builder-vm/`](../tools/builder-vm/)) and
published from it with `just publish` (S1d), by hand or from a daily host timer on AC
power. The builder VM runs on the laptop: under Ubuntu today, and under Apex once
Ubuntu is removed. The same `just` recipes run in the builder VM and in `ci.yml`.

| Step | What it does | Output |
|---|---|---|
| `ci.yml` | on every push: fmt, clippy `-D warnings`, nextest (wall-clock tests in a slow profile), `cargo deny`, ESLint on `desktop/shell/js/`, sassc on the Apex SCSS, blueprint-compiler, shellcheck, privacy guard | pass or fail |
| packages | `packaging/rebuild.sh <pkg>` for each directory in `packaging/pkgs/` (§4.1), and the kernel pair job (§4.2) | signed RPMs stored by content key; `packaging/rpms.lock` |
| image | `build-rootfs` → build checks (G1) → headless shell (G2) → rechunk with `--previous-build` → push under a unique tag → cosign sign → move `:45` | `ghcr.io/sekirokenjii/apex:45`, and a public source artifact per digest (§4.2, S1d) |

Rules:

- **Keys.** The RPM signing key (S1a) and the cosign key (S1d) live in the builder VM,
  each with an offline backup. Module-signing keys are made per kernel build and die
  with the job (§4.2). A third key comes only with Secure Boot (§5.1).
- **Skip unchanged builds.** A content key label hashes the base digest, `rpms.lock`,
  the git trees of `image/`, `desktop/` and `hardware/`, and every installed package's
  name, EVR and arch. A build whose key equals the current `:45` publishes nothing.
- **Rechunk continuity.** Rechunking always passes `--previous-build`, so daily updates
  download only what changed.
- **Monotonic versions.** `:45` moves only to a higher `45.YYYYMMDD.N`, and only after
  G1 and G2 pass. A change to `crates/apex-*`, the kargs, GRUB, the gnome-shell,
  mutter or gdm NVR, or the kernel pair is published only after a G4 run (§11).
- **Visible state.** The image labels `io.github.sekirokenjii.apex.degraded` and
  `io.github.sekirokenjii.apex.held` list what is degraded or held. `apexctl status`
  and Settings > System > Software Updates show both (S2d). Nothing opens issues.
  `just publish` refuses an image whose degraded set grew, unless the owner passes an
  explicit override (S1d).
- **Supply-chain hygiene.** Every action is pinned by full SHA. Checkout uses
  `persist-credentials: false`. The GitHub token is read-only.

### 4.1 Rebuild lane (S1a)

- `packaging/rebuild.sh <pkg>` generalises `packaging/libfprint/build.sh`. Each package
  has `packaging/pkgs/<pkg>/` with `pkg.env`, `series` and `patches/`. `pkg.env` names
  the source (`fedora-srpm`, `copr-srpm`, or `git` plus a commit), the failure policy
  (`on_fail=hold` or `on_fail=degrade`) and the hold family.
- Kept from the libfprint build: the SRPM signature check against a pinned key, a fresh
  digest-pinned `fedora:45` container per build, and the content key. The key is the
  source NVR plus a hash of the series, the patches and the script.
- Added: patches apply with fuzz 0. The release suffix is `.apexN`, where N is
  `git rev-list --count` over the package directory. `rpmsign` uses the Apex RPM key,
  so `[apex]` drops `gpgcheck=0`. `includepkgs` for `[apex]` and `excludepkgs` for the
  Fedora repos are generated from the built RPM names.
- The built set of each package is stored by its content key. `packaging/rpms.lock`
  names the set each image uses. Third-party inputs (the COPR and negativo17 SRPMs and
  the negativo17 binaries) are stored at first sight: the COPR keeps 5 builds per
  package and negativo17 the last two builds of each package.

| Package | Source | Series | On failure |
|---|---|---|---|
| gnome-shell | Fedora SRPM, plus `desktop/shell/` as Source1 | hook hunks and the `ShellBlurEffect` patch (§7.4) | hold, as one family with mutter |
| libadwaita (S2c) | Fedora SRPM | 1: the live window radius | hold |
| gnome-control-center (S2c–S2d) | Fedora SRPM | 3: the Apex Desktop panel, the sidebar tiles, Software Updates | hold |
| nautilus (S2d) | Fedora SRPM | 3: the disk footer, the item count, a 72 px zoom level | hold |
| libfprint, if the score test passes (S2c) | `git`: filip-rs/libfprint `elanpress` at a pinned commit | its series | degrade |
| kernel-cachyos and kmod-nvidia (S1c) | the COPR and negativo17 SRPMs | §4.2 | hold (§4.3) |

- **Patch queues.** The series files in the repository are the source of truth.
  `just pkg-prep <pkg>` unpacks the SRPM into a git work tree in the builder VM, one
  commit per patch. `just pkg-export <pkg>` writes `git format-patch` output back.
  `just pkg-rebase <pkg> <nvr>` applies the series to a new SRPM with `git am -3`.
- **Dev loop.** Shell JS and SCSS: `G_RESOURCE_OVERLAYS` over the prepared tree with
  `gnome-shell --devkit` in the desktop VM, seconds per change. C in a GNOME package:
  incremental ninja in an F45 toolbox and `bootc usroverlay`, 1 to 3 minutes. A lane
  RPM: 10 to 15 minutes.
- The patch budgets in ADR 0014 are checked in review. No script counts lines.

### 4.2 Kernel and NVIDIA lane (S1c)

([ADR 0015](adr/0015-cachyos-kernel-and-nvidia.md))

- `packaging/pkgs/kernel/` holds `kernel.env` (the COPR package, the chroot
  `fedora-45-x86_64`, the SRPM NEVR and sha256, the COPR key and the CachyOS tag key),
  `nvidia.env` (the `nvidia-kmod` SRPM and the userspace NEVRs, each with sha256, and
  the negativo17 key), `kernel-spec.patch`, `series`, `patches/` and a README with the
  measured build numbers. The `nvidia-kmod` spec needs no patch: kmodtool takes
  `--define 'kernels <uname-r>'` before the spec's `buildforkernels akmod`.
- Every bump checks its inputs: `rpm -K` against the pinned keys, `git verify-tag` of
  the CachyOS tag, and a diff of that tag's `git archive` against the SRPM's Source0. It
  writes a bump report: the upstream stable delta, the config and BORE-patch diffs
  against the previous pair (both come from unpinned URLs), and the NVIDIA patch list.
  A config change other than new symbols holds the bump for the owner.
- The pair job runs in one fresh container with a persistent ccache volume, at low CPU
  weight. It first generates an ECDSA P-384 module key and certificate on a tmpfs.
  `kernel-spec.patch` sets the `.apexN` release, turns source fetching off, points
  `CONFIG_MODULE_SIG_KEY` at that key, applies `series`, and reduces `%posttrans` and
  `%preun` to `depmod`. The kernel builds its builtin keyring from the key's certificate
  and signs every in-tree module with it.
- Then, in the same container, the kmod build installs the `kernel-cachyos-devel` just
  built, and fails when its GCC major differs from the kernel's
  `CONFIG_CC_VERSION_TEXT`. It runs `rpmbuild --define 'kernels <uname-r>'` through
  kmodtool, which signs every NVIDIA module with the same key. The tmpfs is shredded;
  only the certificate is kept. A driver bump therefore rebuilds the whole pair, the
  kernel from a warm ccache.
- Gates. The pair holds on any failure:
  - patches apply with fuzz 0, and both builds succeed;
  - every module, in-tree and NVIDIA, carries one signature, made with this build's key
    and SHA-512 or SHA-256;
  - the NVIDIA modules' vermagic equals the kernel release;
  - no private key material in any payload;
  - the kernel config assertions of G1 (§11), and BTF present;
  - the module count within 5 % of the previous pair.
- After the gates: `rpmsign`, then `rpms.lock`. The store keeps `vmlinux` with DWARF,
  `System.map`, the config, the log and `kernel-cachyos-devel` for the last 4 pairs;
  none of it enters the image. Each public image digest gets a public source artifact:
  both SRPMs, the spec patches and the series.
- A builder timer, every 4 hours on AC, polls the COPR API and negativo17's repodata.
  Same-line kernel bumps publish unattended when the gates, G1, G2 and G4 pass. A new
  line and a new driver wait for the owner (§4.3). One side of the pair moves per image,
  the kernel first.
- Budget, to be measured in the K1 spike: kernel 45–90 min cold and 20–45 min with a
  warm ccache, kmod 3–5 min, about 25 GB of scratch plus 15 GB of ccache. Kernel jobs
  need about 10 GiB of VM RAM, or `-j6` in less.

### 4.3 Hold on failure

| Failing input | What happens | Limit |
|---|---|---|
| gnome-shell with its mutter, libadwaita, gnome-control-center or nautilus: a patch no longer applies, the build fails, or a gate or an approved golden fails | `rpms.lock` does not advance. The last good `.apexN` build keeps winning through `[apex]` priority 1, and gnome-shell keeps its exact mutter from `[apex]`. The build prints the hold and whether the newer Fedora build is a security update. The label, `apexctl status` and the Settings Updates page show it. | 72 h for a security update, 14 days otherwise. Then the owner rebases the series or ships stock for that package. For gnome-shell that means the stock Fedora pair, and a stock desktop until the rebase. |
| libfprint, if kept (§6.3) | The image ships Fedora's stock libfprint with the label `degraded=fingerprint`. | none |
| A kernel point release on the running line: no COPR build yet, or an input check, the build or a gate fails | `rpms.lock` keeps the last good pair, and the label says `held=kernel-cachyos`. | 72 h from the kernel.org release; every stable release counts as a security update. Then the owner waits, or publishes the break-glass image `just image KERNEL=fedora`: Fedora's signed kernel with the NVIDIA half built for it. |
| The kmod for a new kernel | The last good pair stays, and other updates flow. The label says `held=kernel-cachyos (nvidia)`. | 72 h for a point release, 14 days for a new line. Then the owner may publish the new kernel with `degraded=nvidia`, through the degraded override: the dGPU stays unbound in D3cold. |
| A new kernel line | Waits for the owner's review of the bump report, and for the laptop rows | 14 days from the COPR's first build of the line; the old line's end of life upstream is the hard stop |
| A new NVIDIA release | 7 days of soak in negativo17, the matching Flathub `GL.nvidia` extension, and the owner's ACCEPTANCE §4 run on the staged deployment. A release named in an NVIDIA security bulletin skips the soak. | none; the current driver keeps working |
| A Fedora package or a kernel pair that regresses on this laptop | `packaging/hold.txt` pins the last good signed build, or the last good pair by content key. | until fixed, within the limits above |

Nothing degrades a design package or the NVIDIA driver to stock on its own. In the
August and September 2026 sample, two of the eight 7.2 point releases first reached the
COPR more than 72 h after their kernel.org release: 7.2.4, which the COPR skipped, in
7.2.5 after about 138 h, and 7.2.6 after 98 h. The kernel row therefore asks the owner
once or twice a month.

### 4.4 Release cost

| Release | Work | Expected cost |
|---|---|---|
| GNOME point (51.x), about monthly: five in the 50 cycle | `just pkg-rebase gnome-shell <nvr>` with the mutter pin. libadwaita, gnome-control-center and nautilus rebuild when their content key changes. G1, G2 and G4 decide. | 0.5 to 2 hours per release when the series applies |
| GNOME major (52, with Fedora 46) | In the `next` lane after S4 (§5.4, S6): rebase every series, the ApexDock hooks and the blur patch onto GNOME 52, and re-approve changed goldens. From the F46 branch point an unattended F46 compose reports what breaks. | 4 to 8 owner-days |
| Kernel point (7.x.y), about weekly as the COPR builds them | none: the lane and the gates decide | builder time only |
| Kernel line (7.x to 7.x+1), every 9 to 10 weeks | the bump report, a config review and the laptop rows; the kmod may wait for a negativo17 patch | 1 to 3 owner-hours of review when the kmod builds, plus a laptop acceptance run |
| NVIDIA driver, about monthly | the soak, the Flathub check and ACCEPTANCE §4 on the laptop; the pair rebuilds with it | about 1 owner-hour |
````

## E9. §5 Updates (5.1 to 5.3) (lines 133-302)

Why: §5 restated contracts that live in the D-Bus XML, the Rust code and ADR 0008 and
0009. The same grubenv semantics are written four times across the docs. The contracts
stay in code. Counted rollback is kept; `rd.shell=0 rd.emergency=reboot` go and
`panic=10` stays (decision 16). The commit that removes them also updates the files
that name them (listed in the review, §4). One cosign key and one RPM key, each with a
backup (decision 21); modules are signed with a per-build key, and a third key comes
only with Secure Boot (ADR 0015). The image package is public (decision 20). The boot
handoff follows decision 17, and a new §5.5 plans the simplification after the owner
deletes Windows. No GRUB entry chainloads Windows, because that changes what the TPM
measures and BitLocker would ask for its recovery key (`docs/INSTALL.md:420-423`).
bootupd's static config shows the menu for 1 s on every boot (`grub-static-pre.cfg`:
`set timeout_style=menu`, `set timeout=1`), and the assessment writes `apex_ok=1` only
for armed boots (`crates/apex-boot/src/decide.rs:69-71`).

Old (lines 133-302, 170 lines, quoted in part):

````markdown
## 5. Updates

([ADR 0008](adr/0008-update-policy.md))
[… 165 lines …]
required first-boot check verifies that `/boot/grub2/grub.cfg` contains the Apex snippet
marker.
````

New:

````markdown
## 5. Updates

([ADR 0008](adr/0008-update-policy.md), [ADR 0009](adr/0009-boot-assessment.md))

The update and boot stack is frozen at its current scope. It is the safety net for the
desktop and kernel work: a shell, greeter or kernel that cannot start never produces a
session that lives for 20 s, so the counted boot rolls it back. The contract is the
D-Bus XML `crates/apex-dbus/data/io.github.sekirokenjii.Apex.Update1.xml` together with
the Rust types.

### 5.1 Channel, trust and keys

This section supersedes the signing and repository rules of
[ADR 0012](adr/0012-trust-and-keys.md).
[ADR 0015](adr/0015-cachyos-kernel-and-nvidia.md) amends its Secure Boot and
third-party clauses.

- One repository, `ghcr.io/sekirokenjii/apex`, with the tags `45` and `45.YYYYMMDD.N`,
  signed with one cosign key. The laptop's policy also lists the public half of the
  key's offline backup. The image package is public, since the image holds no secrets,
  so the laptop pulls without a token.
- The laptop's bootc calls run with
  `CONTAINERS_POLICY_JSON=/usr/share/apex/containers/policy.json`: default reject,
  `sigstoreSigned` for the Apex repository only, and no transport-wide accept rules. The
  general policy used by podman and toolbox stays Fedora's default.
- Apex holds two persistent keys, the cosign key and the RPM key. Each private key
  lives in the builder VM on the laptop (§4), with an offline backup. The keys
  therefore guard against tampering in the registry and in transit, not against a
  compromised laptop. The table also lists the per-build module key and the Secure Boot
  key that step W3 may add.

| Key | Signs | Public half | Since |
|---|---|---|---|
| cosign | images | `policy.json`, next to the backup key | S1d |
| RPM (OpenPGP) | Apex-built RPMs in `[apex]` | the repos stage of the image build | S1a |
| Module key, one per kernel build (ECDSA P-384) | the kernel's in-tree modules and the NVIDIA modules of the same pair | built into that kernel; the certificate is kept in the store and named in `manifest.json` | S1c |
| Apex MOK (RSA-2048 X.509, `codeSigning`), only with Secure Boot | `vmlinuz`, in an isolated step | `packaging/keys/apex-sb.der`, shipped as `/usr/share/apex/keys/apex-sb.der`, and enrolled with `mokutil` | W3 |

- The module key never outlives its job, so there is nothing to rotate or revoke. The
  Apex MOK is a third persistent key, and the owner decides it when turning Secure Boot
  on (ADR 0015 §7).
- Pinned third-party keys: Fedora's (base image, SRPMs, Koji builds), the COPR
  `bieszczaders/kernel-cachyos` key (`537D EED3 3436 B036 7F5B 26D5 B3E3 132C F108 59CF`,
  expires 2028-01-23), the CachyOS tag signer
  (`E8B9 AA39 F054 E30E 8290 D492 C3C4 8208 57F6 54FE`) and negativo17
  (`0C5D 0F47 0484 AE2F C40A 9B65 97F3 0089 93E8 909B`, expires 2029-08-31). A dated
  build check fails 60 days before a pinned key expires.

### 5.2 Daemon

- `apex-updated` is the only component that runs bootc, and every operation goes through
  one queue. It never reboots. The session reboots through
  `org.gnome.SessionManager.Reboot`.
- State is rebuilt from `bootc status`. Only the user's intent, a denylist of digests
  that failed health checks, the last check and the last health failure are persisted.
- A timer checks daily. When the gates pass (AC or enough battery, an unmetered network,
  free space, not denylisted, a newer version), it runs `bootc upgrade --download-only`.
- `Apply(expected_digest)` checks the staged digest and its version, arms the boot
  counter and runs `bootc upgrade --from-downloaded`. What gets applied is what the user
  saw.
- Front ends: Settings > System > Software Updates (S2d), the "Updates Ready"
  notification from `apex-session-agent` (S2d), and `apexctl`. Settings and
  `apexctl status` also list degraded and held packages (S2d).
- Allowed changes, and only these:
  - pin the last good deployment before arming over an unconfirmed or failed boot, so a
    bad build can be fixed forward (S4);
  - confirm every green boot in grubenv (`apex_ok=1`), not only armed ones, so GRUB can
    hide its menu (§5.5, S4);
  - `apexctl major-upgrade` (§5.4, S6);
  - expose the degraded and held package lists, the kernel hold clock and the
    next-major label through `Update1` and `apexctl status` (S2d);
  - remove SwitchChannel with its downgrade waiver, DiscardStaged, the idle exit, the
    rate limiter, the Stale property and `civil.rs`;
  - one shared types crate, only when a schema change would otherwise touch two copies.

### 5.3 Boot assessment and rollback

- Only `Apply` arms the GRUB counter, under Apex-owned grubenv names. A static GRUB
  snippet counts armed boots and boots the previous deployment after three attempts.
- `panic=10` turns kernel panics into reboots, so the counter moves. The initramfs
  rescue shell stays available. An emergency or rescue shell in the real root during a
  counted boot reboots after 60 s. An initramfs failure waits at the dracut shell, and a
  forced power-off moves the counter.
- `apex-boot-assess` runs the checks: a greeter or user session active for 20 s,
  NetworkManager and logind active, `apex-updated` answers, no listed unit failed, and
  the GRUB snippet marker present once. Hardware checks are reported only, among them
  the dGPU's runtime PM and, from S1c, a bound NVIDIA driver whose version matches the
  manifest.
- Green clears the counter. Red with nobody logged in reboots, so the counter moves. Red
  with a session active notifies and offers "Roll back".
- Manual recovery is always the GRUB menu (§5.5) or `bootc rollback`
  ([RECOVERY.md](RECOVERY.md)).

### 5.4 Fedora majors (S6)

- From the Fedora 46 branch point (2027-02-09), the builder VM composes `FEDORA=46`
  unattended and publishes nothing; it reports what breaks. After S4, the `next` lane
  builds and publishes `apex:46` (S6). Tags stay per major, so no timer crosses a major
  on its own. The `next` lane also moves the kernel pair and the negativo17 mirror to
  Fedora 46.
- F45 images carry a label that names `apex:46`. `Update1` exposes it, and Settings
  shows that Apex 46 is available.
- `apexctl major-upgrade` pins the current deployment, takes a read-only snapshot of the
  `/var` subvolume, switches with `--download-only` and applies at the next restart with
  the counter armed. The pinned F45 entry stays in GRUB until the owner unpins it.

### 5.5 Boot loader, the ESP and Windows

- **Boot handoff** (decision 17): the firmware logo, then GRUB with its menu hidden,
  then the black Plymouth `apex` splash with the wordmark (§7.4), then GDM.
- **The menu (S4).** bootupd's `grub-static-pre.cfg` shows the menu for 1 s on every
  boot. A second static snippet, `07_apex-menu.cfg` in the `apex` RPM, runs before the
  counter snippet and reads the previous boot's `apex_ok`:
  - confirmed green: `timeout_style=hidden` and `timeout=1`. Esc, F4 or Shift during
    that second shows the menu
    ([GRUB manual](https://www.gnu.org/software/grub/manual/grub/html_node/timeout_005fstyle.html));
  - unconfirmed or failed: the menu shows for 5 s;
  - `menu_show_once_timeout` still works ([RECOVERY.md](RECOVERY.md) §1).
- This needs every green boot confirmed in grubenv (§5.2). The counter snippet already
  resets `apex_ok=0` at every boot (`08_apex-bootcount.cfg:101-103`), and its marker
  does not change.
- bootupd copies static configs only at `bootc install` (`08_apex-bootcount.cfg:12-16`).
  The snippet therefore ships in the image before the internal-disk install (S4). The
  USB SSD keeps the 1 s menu unless it is reinstalled.
- **While Windows is installed,** the ESP is shared (ADR 0010):
  - GRUB has no Windows entry. A chainload from GRUB changes what the TPM measures, and
    BitLocker would ask for its recovery key (`docs/INSTALL.md:420-423`). Windows
    starts from the firmware boot menu (Esc at the ASUS logo);
  - `bootloader-update.service` stays disabled (`80-apex.preset:37-44`). The owner runs
    `sudo bootupctl update` by hand, on AC, after a green boot;
  - Secure Boot stays off. With bootloader updates off, a Windows Update SBAT
    revocation could stop the old shim or GRUB from booting. Turning it on also changes
    PCR 7, so BitLocker would ask for its recovery key if Windows had turned it on (the
    Windows volume is not encrypted on 2026-09-28).
- **After the owner deletes Windows** (step W, owner-triggered):
  1. The Microsoft reserved and Windows partitions, `EFI/Microsoft/` on the ESP and the
     "Windows Boot Manager" firmware entry (`efibootmgr -b <n> -B`) go. The owner types
     every command; `docs/INSTALL.md` has the runbook.
  2. The space: before S4, Apex installs there, and Ubuntu stays as the fallback until
     Apex has passed its two weeks. After S4, it lies before the Apex partitions and
     cannot extend them, so it becomes a second LUKS2 btrfs volume, unlocked with a
     keyfile from the encrypted root, for the builder VM and container storage.
  3. Enable `bootloader-update.service`. The ESP then holds only shim and GRUB (and
     Ubuntu's files while Ubuntu stays). bootupd's UEFI updates are safe against power
     loss, Fedora Atomic Desktops run them by default, and with Secure Boot on an
     outdated shim or GRUB is the larger risk (SBAT). A bad shim or GRUB still breaks
     every deployment; the ESP backups of INSTALL.md §2 and §9 stay the recovery path.
  4. Secure Boot becomes an owner choice, with bootloader updates on and no BitLocker
     in the way (step W3, ADR 0015 §7).
  5. INSTALL.md, RECOVERY.md §5, ADR 0010, the UEFI-only bullet in §3 and the
     `80-apex.preset` comment drop their shared-ESP text.
````

## E10. §6 Introduction (lines 306-309)

Why: The profile renderer maintains one static file and an audio fix that was never
measured. The proposal commits `monitors.xml` and cuts the renderer: its monitors half
first, its audio half after the audio experiment.

Old:

````markdown
Machine facts live in [`hardware/m7400qc/profile.toml`](../hardware/m7400qc/profile.toml).
The files derived from it (HDA patch firmware, `monitors.xml`) are rendered by
`apexctl profile render`, and `apexctl profile render --check` fails CI when the committed files differ. Acceptance tests
with numbers are in [hardware/ACCEPTANCE.md](hardware/ACCEPTANCE.md).
````

New:

````markdown
Machine facts live in [`hardware/m7400qc/profile.toml`](../hardware/m7400qc/profile.toml).
`hardware/m7400qc/monitors.xml` is a committed static file. Acceptance tests with
numbers are in [hardware/ACCEPTANCE.md](hardware/ACCEPTANCE.md).
````

## E11. §6.2 Audio (lines 323-351)

Why: An existing kernel fixup can be tried with zero code, and the `model=` drop-in is
the fix form (decision 23, default). The carried kernel patch no longer applies to
v7.3-rc4. With the CachyOS kernel rebuilt in Apex's lane, a quirk can be carried there
if the drop-in fails (ADR 0015 §8).

Old (lines 323-351, 29 lines, quoted in part):

````markdown
### 6.2 Audio: Realtek ALC294, subsystem `1043:1ab2`

([ADR 0004](adr/0004-audio-hda-patch-firmware.md))
[… 24 lines …]
The procedure can run **today on the Ubuntu dev install** of this laptop (its kernel has
`CONFIG_SND_HDA_PATCH_LOADER=y` and `hda-verb` is installed), before Apex exists.
````

New:

````markdown
### 6.2 Audio: Realtek ALC294, subsystem `1043:1ab2`

([ADR 0004](adr/0004-audio-hda-patch-firmware.md), amended by
[ADR 0015](adr/0015-cachyos-kernel-and-nvidia.md))

No kernel tree has a quirk for this SSID. Upstream maps the similar ASUS K6500ZC to the
existing `ALC294_FIXUP_ASUS_SPK`, which sets EAPD (COEF 0x0f) and COEF 0x40 and chains
the headset-mic pin (commit 713f040cd222).

1. On this laptop (S0), try `options snd-hda-intel model=1043:10d3,1043:10d3`, then
   `1043:194e` and `1043:1b11`. `model=` is indexed by probe order, and the HDMI
   controller probes first, so the value is given twice.
2. Ship the winner as one line in `/usr/lib/modprobe.d/apex-audio.conf` (S1d), after
   checking it again on the CachyOS kernel, which carries Realtek quirks for other ASUS
   models. `snd-hda-intel` stays out of the initramfs, so the option applies at probe.
3. Acceptance: `picked fixup` in dmesg; the speakers work after a cold boot, after a
   Windows restart and after s2idle; the headset mic records.
4. Only if no fixup survives a Windows restart: HDA patch firmware with the measured
   COEF `0x1b` bit-10 write (ADR 0004). The CachyOS kernel keeps the patch loader,
   `RECONFIG` and `HWDEP`, and G1 asserts them.
5. Upstream: a one-line `SND_PCI_QUIRK(0x1043, 0x1ab2, …)` to the working fixup, with
   the owner's Tested-by. The kernel lane (§4.2) carries it only if the drop-in fails
   its rows, and drops it once the CachyOS tree has it. The drop-in goes when the
   running kernel has the quirk.

Until a fix is measured, the image carries `degraded=audio`.
````

## E12. §6.3 Fingerprint, driver text (lines 357-367)

Why: Enrollment is not recognition. 0002 bounds 0001's retry, so the two stay together
while they ship. The press-mode driver is the one path that may verify. If the score
test fails, a rebuild that only enrolls has no use.

Old:

````markdown
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
````

New:

````markdown
libfprint's `elan` driver treats any pre-scan status other than 0x55 as a protocol error
(MR !655, unmerged). Patches 0001 and 0002 in `packaging/libfprint/series` let
enrollment finish on 0x0c6e. 0002 bounds 0001's retry, so the lock screen never polls
at 100 Hz, and the two ship together or not at all. That swipe pipeline is not known to
verify on this press sensor: other units report genuine scores of 0 to 19 against a
threshold of 24.

The press-mode driver `elanpress` (filip-rs/libfprint) targets this USB ID. It is an
experiment: a personal fork, tested on another laptop. The genuine and impostor score
test ([FINGERPRINT.md](hardware/FINGERPRINT.md) §5) decides, on this unit (S0):

- **Pass:** `elanpress` enters the rebuild lane as a `git` source with
  `on_fail=degrade` (S2c).
- **Fail:** the image ships Fedora's stock libfprint. `packaging/libfprint/` and the
  `degraded=fingerprint` label go, and the effort goes upstream (MR !530).
````

## E12b. §6.3 Fingerprint, PAM (lines 369-373)

Why: Milestone M1 no longer exists. The score test gates PAM.

Old:

````markdown
Fingerprint is **not** in PAM at M1. Enrollment works in Settings > Users. It is
enabled for screen unlock only, never `system-auth`, sudo or polkit, through an Apex
authselect vendor profile once the genuine and impostor score test passes. The sensor
is in the power key, so `power-button-action='interactive'`: pressing it on the lock
screen does nothing.
````

New:

````markdown
Fingerprint is **not** in PAM until the score test passes. Then it is enabled for
screen unlock only, never `system-auth`, sudo or polkit, through an Apex authselect
vendor profile (S4). The sensor is in the power key, so
`power-button-action='interactive'`: pressing it on the lock screen does nothing.
````

## E13. §6.4 dGPU (lines 377-382)

Why: The owner chose NVIDIA's modules for the dGPU (decision 22, ADR 0015). Three layers
(`modprobe.blacklist=`, `rd.driver.blacklist=` and `apex-dgpu.conf`) do the work of one
kernel argument. The udev rule matched one device ID only. On this laptop under Ubuntu
(2026-09-28), fine-grained RTD3 already reaches D3cold with the driver loaded, 95.9 %
of the time since boot.

Old:

````markdown
- **dGPU (M1):** no NVIDIA driver. nouveau and nova-core are blacklisted, also in the
  initramfs. A udev rule sets `power/control=auto` for the GA107 when it is added, so
  the unbound device can reach D3cold through its root port. The panel and HDMI are on
  the iGPU. Acceptance: at least 95 % runtime-suspended over 10 minutes idle. Two ways
  to use the dGPU come in M2: NVIDIA 615 open kmods signed with a MOK
  ([ADR 0012](adr/0012-trust-and-keys.md)), or nouveau with NVK.
````

New:

````markdown
- **dGPU** ([ADR 0015](adr/0015-cachyos-kernel-and-nvidia.md), S1c): the RTX 3050
  (GA107M, `10de:25a2`) runs NVIDIA's open kernel modules. They are built in the kernel
  lane for exactly the image's kernel and signed with that build's key (§4.2). Until the
  pair ships, images keep Fedora's kernel with the dGPU unbound.
  - The AMD iGPU is `boot_vga`, drives the panel and HDMI, and runs gnome-shell with all
    glass. There is no MUX and no dGPU switch. A udev rule tags the NVIDIA DRM card
    `mutter-device-ignore`, generated from `drives_displays = false` in the profile, so
    mutter and the greeter never open it.
  - Apps use the dGPU on request: "Launch using Discrete Graphics Card"
    (switcheroo-control), desktop entries with `PrefersNonDefaultGPU`, and
    `switcherooctl launch`.
  - The userspace is negativo17's, Wayland only, from `[apex-nvidia]` (§3). The Xorg
    driver, `nvidia-settings` (GTK3) and `nvidia-xconfig` are excluded.
  - Runtime power: fine-grained RTD3 (`NVreg_DynamicPowerManagement=0x02` in
    `/usr/lib/modprobe.d/apex-nvidia.conf`). A udev rule sets `power/control=auto` on
    `add` and `bind` for every NVIDIA display or audio function, so the GPU also reaches
    D3cold unbound. `nvidia-persistenced` is disabled, because UVM persistence keeps the
    GPU awake.
  - System sleep: the driver's kernel suspend notifiers, with no `nvidia-suspend`
    units. negativo17's `nvidia.conf` turns S0ix handling on. `nvidia-powerd` (Dynamic
    Boost) stays only if it costs no idle power (S4).
  - nouveau and nova: one kernel argument, `module_blacklist=nouveau,nova_core` (S1c).
    It replaces `modprobe.blacklist=`, `rd.driver.blacklist=` and `apex-dgpu.conf`. The
    initramfs holds no NVIDIA, nouveau or nova module.
  - `apex-flatpak-update` installs the Flathub `GL.nvidia` extension that matches
    `/sys/module/nvidia/version`.
  - Acceptance: at least 95 % runtime-suspended over 10 minutes idle, `D3cold` with
    VRAM off, offload that returns to `D3cold` within 30 s, and `D3cold` before and
    after s2idle ([hardware/ACCEPTANCE.md](hardware/ACCEPTANCE.md) §4).
  - When the kmod cannot follow a kernel, the owner may publish `degraded=nvidia`: the
    dGPU stays unbound in D3cold (§4.3).
````

## E13b. §6.4 CPU (lines 383-384)

Why: The default mode now comes from the CachyOS kernel. Its config sets
`X86_AMD_PSTATE_DEFAULT_MODE=3`, as Fedora's does. CachyOS adds an `epp_boost` that is
off by default. Nothing checked EPP before (review F7).

Old:

````markdown
- **CPU:** amd-pstate in EPP mode (Fedora's default). tuned-ppd with an
  `apex-performance` profile that drops the server VM tunables.
````

New:

````markdown
- **CPU:** amd-pstate in active (EPP) mode, the default of both the CachyOS and the
  Fedora kernel (`X86_AMD_PSTATE_DEFAULT_MODE=3`). CachyOS's `epp_boost` stays off.
  tuned-ppd with an `apex-performance` profile that drops the server VM tunables.
  Acceptance: EPP is writable and follows the power mode, on both kernels (S1d).
````

## E14. §6.4 Kernel and OLED (lines 392-396)

Why: The kernel is CachyOS's GCC build, rebuilt in Apex's lane (decision 22,
ADR 0015, which supersedes ADR 0005). The CachyOS config enables zswap
(`ZSWAP_DEFAULT_ON`), while the image ships `zram-generator-defaults`
(`image/packages/base.txt:41`). The dark default contradicted the mockup. s2idle had no
acceptance row.

Old:

````markdown
- **Kernel:** the stock Fedora kernel in M1. The Zen 3 kernel fork (COPR) is M2,
  gated on power and latency measurements and on an automated rebase with fallback
  ([ADR 0005](adr/0005-kernel-fedora-fork.md)).
- **OLED:** amdgpu defaults: no ABM on OLED, PSR off on DCN 2.1, and no VRR range in
  the EDID. The dark style is the default.
````

New:

````markdown
- **Kernel** ([ADR 0015](adr/0015-cachyos-kernel-and-nvidia.md), S1c): CachyOS's GCC
  build, `kernel-cachyos` (BORE, HZ 1000, x86-64-v3), rebuilt from the COPR's signed
  SRPM (§4.2). The configuration is CachyOS's; only `MODULE_SIG_KEY` changes, to the
  pair's per-build key. The kernel arguments add `module.sig_enforce=1` and
  `zswap.enabled=0` (Apex uses zram). CachyOS defaults that differ from Fedora's (full
  preemption, BORE, THP always, split-lock mitigation off) are measured against a
  Fedora-kernel build of the same image (S1d); `preempt=lazy` and `kernel.sched_bore=0`
  revert two of them without a rebuild. That Fedora-kernel build stays buildable as the
  break-glass image (§4.3). This supersedes [ADR 0005](adr/0005-kernel-fedora-fork.md).
- **OLED:** amdgpu defaults: no ABM on OLED, PSR off on DCN 2.1, and no VRR range in the
  EDID. PSR (`amdgpu.dcfeaturemask=0x8`) and 60 Hz on battery are measured before they
  are turned on (S4). The default style is light, as drawn (§7.4).
- **Suspend:** s2idle only. Acceptance measures hardware-sleep residency, overnight
  drain, and dGPU D3cold before and after resume, on the CachyOS kernel with the NVIDIA
  driver loaded (S1d, S4).
````

## E14b. §7.1 Allowlist entries (lines 407-408)

Why: Milestones no longer exist. ADR 0007 gets the same wording (A2).

Old:

````markdown
compares the result with `image/audit/legacy-allowlist.txt` as a set difference. Each
allowlist entry names the milestone that removes it.
````

New:

````markdown
compares the result with `image/audit/legacy-allowlist.txt` as a set difference. Each
allowlist entry names its reason and the condition that removes it. The gate also fails
on any file under `/usr/lib64/xorg/modules/drivers/`, which keeps the NVIDIA Xorg driver
out.
````

## E15. §7.1 App set rows (lines 412-413)

Why: The mockup's dock and grid show Music and Maps. Tour is not in the mockup. Firefox
is not a libadwaita app and is part of a large first-boot download. The rows follow the
answer on the app set (decision 10, default).

Old:

````markdown
| Core | GNOME Shell, Settings, Nautilus + Sushi, Ptyxis, Text Editor, Loupe, Papers, Showtime, Decibels, Snapshot, System Monitor, Baobab, Calculator, Characters, Clocks, Calendar, Contacts, Weather, Font Viewer, Logs, Yelp, Tour, Extensions | image RPM |
| Browser | Epiphany (GTK4) in the image; Firefox preinstalled | RPM / Flatpak |
````

New:

````markdown
| Core | GNOME Shell, Settings, Nautilus + Sushi, Ptyxis, Text Editor, Loupe, Papers, Showtime, Decibels, Music, Maps, Snapshot, System Monitor, Baobab, Calculator, Characters, Clocks, Calendar, Contacts, Weather, Font Viewer, Logs, Yelp, Extensions | image RPM |
| Browser | Epiphany (GTK4) in the image; Firefox installed on request | RPM / Flatpak |
````

## E16. §7.2 Input methods (lines 430-434)

Why: Super+Space opens Spotlight (decision 6). GNOME binds it to `switch-input-source`
(gsettings-desktop-schemas 51.0,
`org.gnome.desktop.wm.keybindings.gschema.xml.in:330-339`), and the image ships two
sources (`90_apex.gschema.override:13-19`). No GNOME 51 default in `wm.keybindings`,
mutter or gnome-shell uses Super+Alt+Space. Alt+Space alone stays mutter's window menu.
Milestone M3 no longer exists.

Old:

````markdown
IBus is GNOME Shell's input framework. The defaults are input sources
`[('xkb','us'), ('ibus','m17n:vi:telex')]`, Super+Space to switch, and per-window
sources, so a terminal can stay in English. ibus-bamboo is not shipped: it links GTK3,
libX11 and libXtst, and its mouse capture triggers Remote Interaction prompts. A Rust
IBus engine with auto-restore of English words is specified in the roadmap (M3).
````

New:

````markdown
IBus is GNOME Shell's input framework. The defaults are input sources
`[('xkb','us'), ('ibus','m17n:vi:telex')]` and per-window sources, so a terminal can
stay in English. Super+Space opens Spotlight (§7.4), so switching sources moves to
Super+Alt+Space, and Shift+Super+Alt+Space goes back (S1b). The combination keeps
GNOME's hold-to-pick switcher, no GNOME 51 default uses it, and IDEs do not bind it.
With two sources, both directions toggle. The en/vi indicator in the top bar shows the
active source. xkb group toggles such as Ctrl+Shift are not used: mutter consumes the
group-switch key press, so Shift stops acting as Shift while Ctrl is held, which breaks
Ctrl+Shift shortcuts in Ptyxis and editors (mutter 51 `src/core/keybindings.c:474-558`).
ibus-bamboo is not shipped: it links GTK3, libX11 and libXtst, and its mouse capture
triggers Remote Interaction prompts. A Rust IBus engine with auto-restore of English
words is an optional roadmap item.
````

## E17. §7.3 Vendor defaults, and a new §7.4 (lines 436-453)

Why: §7.3 said upstream UIs own all settings and Apex adds nothing to them. The desktop
layer had no section. The owner chose a rebuilt gnome-shell as the primary mechanism,
with the Apex SCSS entering through an `@import` hook (decisions 1 and 2), dynamic glass
everywhere (decision 14), Super+Space for Spotlight (decision 6), and the
`design/SPEC.md` §8 items built now (decision 26). Upstream facts behind the mechanisms
(GNOME 51.0):

- The release tarball ships compiled CSS, and `data/theme/meson.build` runs sassc only
  when the CSS is missing, so the hook works only if `%prep` moves the CSS aside.
- `gnome-shell-light.scss` and `-dark.scss` import `_colors`, `_drawing`, `_common` and
  `_widgets`; the hooks go after `_colors` and at the end.
- The shell draws its light sheet only for `'prefer-light'`, and every session mode
  inherits `'prefer-dark'` (`js/ui/main.js:437-452`, `js/ui/sessionMode.js:21-26`).
- In background mode `ShellBlurEffect` re-blurs on every paint, forces opacity 255, and
  never downscales a surface shorter than 256 px (`src/shell-blur-effect.c:46-54,
  286-315, 598-617`). At scale 2 the bar and the dock are never downscaled.
- An exception while evaluating the shell's JS makes `main.c` exit with status 1, which
  `org.gnome.Shell@.service` counts as success; GNOME's extension safety net does not
  cover code inside the package.

Dash to Dock is not used: the drawn order, separator, lift and Show Apps tile need
changes to its code, and it injects into the overview internals the Apex hooks change.

Old (lines 436-453, 18 lines, quoted in part):

````markdown
### 7.3 Vendor defaults and customisation

([ADR 0011](adr/0011-customisation-boundaries.md))
[… 13 lines …]
from there), and the symlinks that `systemctl enable`, `mask` and `set-default` create
under `/etc/systemd/system`.
````

New:

````markdown
### 7.3 Vendor defaults

Defaults ship as `/usr/share/glib-2.0/schemas/90_apex.gschema.override`, compiled at
build time, with no dconf locks. They set the mockup's defaults on stock keys where
stock differs: fonts and hinting, icon theme, button layout, clock fields, battery
percentage, wallpaper, lock-screen notifications, search order, favourites and the
input-source shortcuts (§7.2). They keep the input sources and the power-key action.
`color-scheme` keeps GNOME's `'default'`, which the rebuilt shell draws light (§7.4).
The stock accent, blue, already matches. The calendar's first weekday and the clock
format follow the locale. The values are in [design/SPEC.md](../design/SPEC.md) §6.

The only files Apex places in `/etc` are `/etc/xdg/monitors.xml`, the fontconfig links,
`/etc/plymouth/plymouthd.conf` (written by `plymouth-set-default-theme`, plus
`DeviceScale=2`, S1d), `/etc/profile.d/apex-prompt.sh` (the terminal prompt colours,
S1b), `/etc/tuned/ppd.conf` (tuned-ppd reads its profile mapping only from there), and
the symlinks that `systemctl enable`, `mask` and `set-default` create under
`/etc/systemd/system`.

### 7.4 Desktop layer

([ADR 0014](adr/0014-engine-level-desktop.md), [design/SPEC.md](../design/SPEC.md))

gnome-shell is rebuilt with the Apex layer inside it. libadwaita, gnome-control-center
and nautilus carry small series. mutter, GTK, gdm, Ptyxis and Plymouth stay
Fedora-signed binaries. mutter is pinned to the exact EVR the shell was built against
and mirrored unmodified into `[apex]` (§3).

| Part | Mechanism | Slice |
|---|---|---|
| Shell theme | The Apex SCSS, compiled into gnome-shell's own resource through two `@import` hooks | S1a–S1b |
| Shell behaviour | The Apex layer, `js/ui/apex/` in the gnome-shell package, with its safety net | loader and safety net S1a; top bar S2a; Spotlight, overview and launcher S3a; notifications, Quick Settings, motion and shadows S3c |
| Dock | ApexDock, a subclass of upstream `Dash` inside the layer | S2a |
| Glass | Dynamic blur with saturation on every drawn surface: a C patch to `ShellBlurEffect` and a JS glass manager | S2b; scrims and Spotlight S3a |
| Lock screen | Single stage, date above time, blur σ 30 with saturation, the field's glass, an initial-letter avatar, "Enter Password" for PAM's exact `Password:` question only | S3b |
| Greeter | The rebuilt shell with the Apex CSS and stock JS | S3b |
| Window radius | `apex.css` from `apex-session-agent`, read at app start; a libadwaita patch that makes host apps follow it live | S1b; live S2c |
| Settings | gnome-control-center, 3 patches: the Apex Desktop panel; coloured sidebar tiles in the mockup's order; the Software Updates row and page on `Update1` | S2c–S2d |
| Files | nautilus, 3 patches: the disk-usage footer, the item-count bar, a 72 px grid zoom level | S2d |
| Terminal | Ptyxis; `apex-session-agent` writes a user palette whose cursor is the accent | S1b |
| Boot splash | Plymouth script theme `apex`: rounded bar, @2x assets, its own LUKS prompt. The two-step `apex-twostep` theme stays installed as the fallback. | S1d |
| GRUB | Menu hidden unless the last boot failed (§5.5) | S4 |
| Assets | the `apex-desktop` noarch RPM | S1b |

**Shell package** (`packaging/pkgs/gnome-shell/`).

- Source1 is a git archive of `desktop/shell/`: the layer, the Apex SCSS and assets,
  and `apex.gresource.xml`. That resource is compiled and linked into libshell next to
  upstream's, so a new Apex file never edits upstream's resource list.
  `desktop/shell/` is GPL-2.0-or-later, gnome-shell's licence.
- A spec-edit script inserts at fixed anchors and fails when one is missing, because
  Fedora's spec uses `%autorelease`. It adds Source1, `BuildRequires: sassc`,
  `Requires: mutter = <EVR in the buildroot>` and the `.apexN` release.
- In `%prep`, the shipped `gnome-shell-light.css` and `-dark.css` move into the Apex
  resource as the safe-mode sheets, and `gnome-shell-high-contrast.css` is deleted.
  sassc then builds all three sheets with the hooks in place.
- The series holds hook hunks only, one patch per concern: build, loader, blur, panel,
  Quick Settings, message list, overview, dash, lock, motion, derived glass. All logic
  lives in `desktop/shell/`. Budget (ADR 0014): at most 450 changed lines of hook hunks
  in at most 33 upstream files (the plan uses 31), and at most 300 lines of C in
  `shell-blur-effect.{c,h}`.
- mutter's one possible change, redraw-clip expansion for glass, is made only if the
  S2b or S3a measurement shows the need, and only by the owner's decision (ADR 0014,
  Escalation). It would take mutter off Fedora's signature.

**Layer contract.**

- Upstream files import only `ui/apex/hooks.js`. It has no side effects at load and
  never throws. A hook with no provider, or with a provider that throws, gives the
  stock value. A provider that throws is turned off for the session and logged once.
- Features load in two phases, each in its own module and `try/catch`: value providers
  before the UI exists, and actors at `startup-prepared`.
- In the gdm mode every hook returns stock.
- Kill switches, strongest first: the kernel argument `apex.safe=1` or
  `APEX_SHELL_SAFE=1` (no layer, upstream's sheets, the stock colour scheme); the
  per-user `layer-enabled` key; `disabled-features`; Reduce Transparency, for glass.
  `APEX_SHELL_TEST=1` turns on the test hook G2 uses.
- Crash guard: the layer creates `%t/apex-shell-starting` at enable and removes it
  after 60 s. The drop-in `org.gnome.Shell@.service.d/50-apex.conf` adds
  `OnFailure=apex-shell-safe.service`, gated on that file; the service sets
  `layer-enabled=false`. A second shell failure on the same deployment trips it too.
  `apex-session-agent` then offers to turn the Apex desktop back on. The unit counts
  exit status 1 as success, so G2 must catch an import error.
- A shell that cannot start in any mode never keeps the greeter active for 20 s, so the
  counted boot rolls it back (§5.3).
- Apex ships no shell extensions. Extensions the user installs are unsupported against
  the changed internals.

**Colour scheme.** A session-mode hook sets `'prefer-light'` for the user and
unlock-dialog modes, so GNOME's `'default'` draws a light shell. The Quick Settings
Dark Style toggle and Settings > Appearance then work unchanged. No agent rewrites the
key, and no Settings patch maps it.

**Glass** (decision 14). Every surface the mockup draws with `backdrop-filter` gets
dynamic blur with the drawn saturation. The values are in
[design/SPEC.md](../design/SPEC.md) §2.6.

- The `ShellBlurEffect` patch adds a saturation stage (CSS's luma matrix, in the
  brightness pass), a corner radius, a background mode that follows the actor's
  opacity, and downscaling without the 256 px floor. In background mode it re-blurs
  only when the frame's redraw clip covers the whole glass box; otherwise it draws its
  last result and queues a redraw of the box. A blit therefore never reads pixels the
  frame did not repaint, and correctness does not depend on JavaScript.
- A JS glass manager forwards window damage, moves, resizes, restacking and background
  changes as redraws of the glass boxes they touch, for latency only: a missed source
  costs one frame. The overview and launcher scrims blur a non-reactive clone of
  `window_group` (wallpaper and windows) in actor mode, because GNOME hides the window
  group in the overview; the result is cached until the desktop beneath changes. The
  bar and the dock over a scrim blur the scrim's result, as drawn. The lock background
  is an actor-mode blur of the lock's wallpaper. An idle desktop re-blurs nothing.
- Off switches: Reduce Transparency, high contrast, and `disabled-features=['glass']`.
- Acceptance (a first run in S2b, the full exit in S3a; laptop on battery, 90 Hz,
  2880×1800): in three Sysprof scenarios, p99 frame time at most 11.1 ms with at most
  1 % dropped frames, and p50 within 0.5 ms of Reduce Transparency; `gpu_busy_percent`
  at most 5 points higher; idle power at most 0.3 W higher, and a video under the dock
  at most 0.5 W higher. The levers if it fails, in order: coarser downscaling on the
  failing surface, a power-saver quality step, then the mutter change (an owner
  decision).

**Keybindings** (decision 6, S1b). `toggle-spotlight`, default `['<Super>space']`,
lives in `io.github.sekirokenjii.Apex.Desktop.Keybindings`. The layer registers it for
the normal and overview modes.
`/usr/share/gnome-control-center/keybindings/60-apex.xml` lists it, so Settings >
Keyboard can change it. A Super tap opens the overview, and Super+A the launcher. Input
switching is in §7.2.

**Dock.** ApexDock subclasses upstream `Dash`, so it keeps favourites, running apps,
drag and drop, labels, and the app menu with "Launch Using Discrete Graphics Card". Its
own code places it 10 px above the bottom without a strut, hides it over maximised
windows, reveals it at the bottom edge, and adds Trash, the −6 px hover lift, the drawn
order and separator, the full-colour Show Apps tile, the running-indicator toggle and
the glass. The overview's own dash is hidden, and its Show Apps button follows the
dock's. Dash to Dock is not shipped.

**Window radius.** `apex-session-agent` writes `~/.config/gtk-4.0/apex.css` atomically
(the radius and the `0px` resets for maximised, tiled and fullscreen windows) and
imports it from `gtk.css`, which GTK reads once per process. The libadwaita patch loads
the same file into a provider at `GTK_STYLE_PROVIDER_PRIORITY_USER + 1` and reloads it
when a `GFileMonitor` reports a change, so host apps follow a radius change live and a
stale copy at user priority never wins. libadwaita reads no Apex schema. Flatpak apps
read `apex.css` at start through the system Flatpak override if the Bazaar spike
passes, and keep libadwaita's 15 px otherwise. Colour variables never go into user CSS.

**Settings.** One schema, `io.github.sekirokenjii.Apex.Desktop`, with a `.Keybindings`
child, holds only keys with no upstream home. Every other row of the Apex Desktop panel
binds a stock GNOME key. Stock panels gain no rows (decision 27). System's Software
Updates row opens the Apex updates page. "Apex Tweaks" is a `.desktop` entry that runs
`gnome-control-center apex`. There is no separate Updates app.

**apex-desktop** (noarch, built from `desktop/` except `desktop/shell/`) holds the
`Apex` icon theme from a pinned Colloid commit (`Inherits=Adwaita,hicolor`), the Apex
Aurora wallpapers, both Plymouth themes, fontconfig `ss03`, the terminal prompt snippet
and Ptyxis profile default, the gschema override, the Apex schemas, `60-apex.xml`, and a
tmpfiles entry that creates the system Flatpak override. It is separate from the Rust
`apex` RPM, so an asset change never rebuilds cargo. Its `License:` tag covers Apex's
own files (GPL-3.0-or-later), Colloid (GPL-3.0) and, from S5, the Hugeicons-derived
glyphs (MIT).

- Every app in the Apex dock and default app grid ships as an image RPM, except
  Software. Software is Bazaar, which has no Fedora package and stays a Flatpak.
  Flatpak apps keep stock chrome apart from the window radius.
- The boot splash is set with `plymouth-set-default-theme apex` before the image's
  dracut run. The script theme uses device-resolution assets, because Plymouth's script
  API has no scale call. A spike settles whether its coordinates are logical or device
  pixels at `DeviceScale=2`. The two-step theme stays installed as the fallback. Esc at
  boot shows Plymouth's text view, which always shows the passphrase prompt, so a script
  bug cannot hide it for good. The script theme's LUKS prompt is tested on the laptop
  before S4.
````

## E18. §8 Display: scale, docking and migration (lines 459-477)

Why: The Xwayland claim was never measured. The docking agent and the Setup checklist
belonged to the Updates app, which is dropped. `monitors.xml` is no longer rendered.
Hinting follows the mockup: none (settled in the review, §5; ADR 0003 is amended).

Old (lines 459-477, 19 lines, quoted in part):

````markdown
- **Default scale 2 on the panel.** `/etc/xdg/monitors.xml` is rendered from the profile:
  `eDP-1`, SDC, `0x4154`, serial `0x00000000`, rate `90.001434326171875`. At scale 2
  every surface is 1:1: GTK4, GNOME Shell's Clutter/St UI, the cursor, GTK3 and HiDPI
[… 14 lines …]
  first-run Setup checklist (M2) offers "Sharpest (200 %, recommended)" or "More space
  (167 %)".
````

New:

````markdown
- **Default scale 2 on the panel.** `/etc/xdg/monitors.xml` is a committed file:
  `eDP-1`, SDC, `0x4154`, serial `0x00000000`, rate `90.001434326171875`. At scale 2,
  GTK4, GNOME Shell's Clutter/St UI, the cursor and GTK3 render 1:1. X11 clients through
  Xwayland are not measured yet, and this claim does not cover them until they are. At
  5/3 all but GTK4 are resampled, and GTK4 borders only align every 3 logical pixels.
  The workspace is 1440×900, which is the mockup's stage. For more room, the supported
  choice is 5/3, not text scaling.
- **Docked.** mutter recomputes the scale for any monitor set it has no stored config
  for. The AOC Q24G2 at scale 1 is about 123 effective DPI, close to the panel's 121 at
  scale 2, so windows keep the same physical size on both screens.
- **Fonts.** Grayscale antialiasing, no hinting (as drawn) and subpixel positioning.
  fontconfig `10-sub-pixel-none` covers clients that are not GTK4. The keys are in
  [design/SPEC.md](../design/SPEC.md) §6. No mutter experimental keys (mutter 51
  removed the old key).
- **Custom drawing.** Our own drawing uses GTK 4.24's `Snapshot::set_snap`. That
  affects only custom drawing: stock libadwaita widgets are not snapped at 5/3.
- **Migration.** A user `~/.config/monitors.xml` overrides the system default.
````

## E19. §9 Our components (lines 479-517)

Why: The table listed only update and boot crates, an Updates app and a TypeScript
extension. Apex code now lives in the Rust workspace, inside gnome-shell, in four GNOME
series and in the kernel lane.

Old (lines 479-517, 39 lines, quoted in part):

````markdown
## 9. Our components (Rust workspace)

| Crate | Milestone | Responsibility |
[… 34 lines …]
  one `make install` target that is also used for development. Release is derived from
  git. Binaries are built with `cargo auditable`.
````

New:

````markdown
## 9. Our components

| Component | Language | Responsibility |
|---|---|---|
| `apex-bootc` | Rust | Lenient serde model of the bootc status API; invocation builder (argv from enums, `env_clear`, fixed `PATH`, strict `CONTAINERS_POLICY_JSON`); process runner |
| `apex-update` | Rust | Pure engine: snapshot, gates, state derivation, atomic stores, version ordering, `rpmvercmp`, manifest diff |
| `apex-boot` | Rust | Boot assessment: grubenv codec, decision table, checks with timeouts; binary `apex-boot-assess` |
| `apex-dbus` | Rust, XML | The `io.github.sekirokenjii.Apex.Update1` contract. The XML also feeds gdbus-codegen in gnome-control-center (S2d). |
| `apex-updated` | Rust | System bus service: one operation queue, polkit (system-bus-name subject), hardened unit |
| `apex-session-agent` (S1b) | Rust | User unit: writes `apex.css` for the window radius and the Ptyxis accent palette, offers to turn the Apex desktop back on after the crash guard trips, posts update notifications (S2d) |
| `apexctl` | Rust | CLI: `status` (degraded and held packages, the kernel pair and its hold clock, S2d), `update …`, `hw report`, `major-upgrade` (S6) |
| Apex layer (S1a–S3c) | GJS, C | `desktop/shell/`: shell behaviour, ApexDock, the glass manager; the `ShellBlurEffect` patch |
| GNOME series (S1a–S2d) | C, Blueprint | `packaging/pkgs/{gnome-shell,libadwaita,gnome-control-center,nautilus}/` |
| Kernel and NVIDIA lane (S1c) | Bash, spec patches | `packaging/pkgs/kernel/`: the pair job, its gates and the bump report |
| Shell theme (S1a–S1b) | SCSS | `desktop/shell/data/theme/apex/` |
| Boot splash (S1d) | Plymouth script | `desktop/plymouth/` |

Rules:

- **Pure core, thin shells.** Every decision is a pure function with unit tests.
  Binaries only perform I/O. Clock, power, network, filesystem space and polkit sit
  behind traits.
- **Async.** Daemons use tokio `current_thread` with zbus. `apex-session-agent` uses the
  GLib main loop, because GSettings and notifications live there. The Apex layer uses
  asynchronous D-Bus with timeouts only.
- **bootc drift.** Parsing is lenient: no `deny_unknown_fields`, and `#[serde(other)]`
  on enums. The fixtures come from bootc's own test data.
- **Root daemon hygiene.** It reads only `/usr/share/apex` and `/etc/apex`, never a
  user's home. It has no writable D-Bus properties. bootc argv is built from enums plus
  the compile-time image references. The unit is hardened within what bootc tolerates.
- **IDs.** One family, prefix `io.github.sekirokenjii.Apex`: bus `…Apex.Update1`,
  schemas `…Apex.Desktop` and `…Apex.Desktop.Keybindings`, polkit
  `io.github.sekirokenjii.apex.update.*`, labels `io.github.sekirokenjii.apex.*`.
  There are no extension UUIDs.
- **Packaging.** Two RPMs come from this repository: `apex` (Rust binaries and units,
  built with `cargo auditable`) and `apex-desktop` (noarch assets; a first build in S1a
  carries only the Apex schema, S1b fills it), so an asset change never rebuilds cargo.
  The shell code ships inside the rebuilt gnome-shell. Release is derived from git.
````

## E20. §10 Repository layout (lines 519-529)

Why: New directories for the shell layer, the design and the lanes. One workflow
remains. `packaging/kernel/` is replaced by `packaging/pkgs/kernel/`
(ADR 0015).

Old:

````markdown
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
````

New:

````markdown
## 10. Repository layout

```
Cargo.toml  Makefile  Justfile  rust-toolchain.toml  deny.toml
crates/       apex-bootc apex-update apex-boot apex-dbus apex-updated apexctl
              apex-session-agent (S1b)
desktop/      shell/ (js/ui/apex/, data/theme/apex/, apex.gresource.xml; S1a)
              schemas/ (S1a); icons/ plymouth/ wallpaper/ fontconfig/ ptyxis/ (S1b)
design/       mockup/ (the mockup, support.js, icons/), SPEC.md,
              renders/ (generated by `just design-render`, not committed)
hardware/     m7400qc/profile.toml, m7400qc/monitors.xml
image/        Containerfile, packages/*.txt, system_files/ (rootfs overlay), checks/, audit/
packaging/    apex.spec, apex-desktop.spec (S1a), rebuild.sh, rpms.lock, hold.txt,
              pkgs/<pkg>/ (gnome-shell, libadwaita, gnome-control-center, nautilus,
              kernel, libfprint if kept), keys/apex-sb.der (W3)
tests/shots/  headless harness, metric assertions, approved goldens (S1a)
tools/        builder-vm/, design/render-mockup.cjs
.github/      workflows/ci.yml
docs/         ARCHITECTURE, THREAT-MODEL, ROADMAP, INSTALL, RECOVERY, adr/, hardware/,
              reviews/
```
````

## E21. §11 Quality gates (lines 531-554)

Why: Gates now check the rebuilt shell and the kernel pair, in proportion to one owner:
cheap build checks, a few metric assertions where a regression is likely, and goldens
only for screens the owner approved. Per-candidate KVM qualification, self-tests of CI
scripts and comment-matching tests go. The `rpm -V gnome-shell` and extension checks go
with the overlay; checks on the rebuilt package replace them.

Old (lines 531-554, 24 lines, quoted in part):

````markdown
## 11. Quality gates

- **Rust:** fmt, clippy (pedantic, `-D warnings`), unit, property and snapshot tests,
[… 19 lines …]
- **Hardware:** [hardware/ACCEPTANCE.md](hardware/ACCEPTANCE.md), run on the laptop.
  Each hardware fix has a numeric pass criterion.
````

New:

````markdown
## 11. Quality gates

| Gate | When | Checks |
|---|---|---|
| G1 build checks | every image build | `bootc container lint --fatal-warnings` (skips justified in a file that can only shrink; it is empty); the legacy gate; firmware files; one kernel, and an initramfs with amdgpu and its green_sardine firmware, the microcode and the LUKS2 modules, and without snd-hda-intel, nouveau or nova; no keys or secrets in any layer; rpm signature enforcement untouched; the overlay's units, udev rules and tmpfiles validate; UEFI only; `glib-compile-schemas --strict` on the override; composefs on. Desktop (S1a): gnome-shell, and each GNOME package rebuilt later, is an `.apexN` build signed with the Apex RPM key; gnome-shell's `Requires: mutter =` matches the installed mutter, which carries Fedora's signature; the Apex marker is in the light and dark sheets and the structure marker in the high-contrast sheet, upstream's sheets are under `/org/gnome/shell/theme/stock/`, and `rpm -V gnome-shell` is clean; no shell extension in `/usr/share/gnome-shell/extensions/`; every `.desktop` `Icon=` resolves; no `G_RESOURCE_OVERLAYS` or `--unsafe-mode` in `/usr` or `/etc`. Plymouth (S1d): the default theme is `apex`, `DeviceScale=2` is set, and `apex-twostep` is installed. From S1b: no two default keybindings share a combination across `wm.keybindings`, mutter, the shell, media keys and the Apex schema. Kernel pair (S1c): the kernel is named `*-cachyos*.apex*`; config assertions (`SCHED_CLASS_EXT`, `DEBUG_INFO_BTF`, `X86_AMD_PSTATE` mode 3, `AMD_PMC`, `ASUS_WMI`, the HDA patch loader, `RECONFIG`, `HWDEP` and ALC269, `MODULE_SIG`, `IMA_ARCH_POLICY`, `EROFS`, `OVERLAY`, `DM_CRYPT`, selinux in `CONFIG_LSM`, `X86_64_VERSION` at most 3); every module signed by the one key built into this kernel, whose certificate matches `manifest.json`; NVIDIA vermagic equals the kernel; one NVIDIA version across the kmod, `nvidia-driver`, `nvidia-kmod-common` and the GSP firmware; the initramfs also holds erofs, overlay and `aesni_intel` (a module on CachyOS), and no nvidia module; no `/usr/src/kernels`, akmods, dkms, `xorg-x11-nvidia` or `nvidia-settings`; the effective modprobe options; `nvidia-persistenced` disabled; `/etc/kernel/cmdline` and `/etc/default/grub` untouched; the NVIDIA licence present. From W3: `sbverify` of `vmlinuz` against the Apex MOK. |
| G2 headless shell (S1a) | every image build, about 3 minutes | the built image runs `gnome-shell --headless --virtual-monitor 2880x1800` at scale 2, in light and dark, with python-dbusmock fixtures and a fixed clock; the whole static import graph loads, and no `JS ERROR`. It runs twice. With the layer: a few metric assertions where a regression is likely (bar height, dock position and size, launcher columns, window radius), approved goldens with per-scene masks, and from S2b a glass pixel test (a known pattern under glass with partial damage, against a CPU reference blur, within a tolerance that its first run fixes, starting at 3/255 maximum and 1/255 mean per channel; [design/SPEC.md](../design/SPEC.md) §7.2). With `APEX_SHELL_SAFE=1`: stock values, such as thumbnail scale 0.05 and the stock sheet path. |
| G3 contact sheet (S1b) | on demand; not a gate | mockup render, shell capture and their difference for each screen; the owner approves goldens from it |
| Lane (S1a) | every package build | the SRPM signature verifies; patches apply with fuzz 0; the build succeeds; the Apex marker is present; for the kernel pair, the gates in §4.2 |
| G4 VM check | weekly, and before publishing a change to `crates/apex-*`, the kargs, GRUB, the gnome-shell, mutter or gdm NVR, or the kernel pair | in the builder VM (`-cpu host`): install, upgrade and counted rollback; boot to GDM, log in, lock and unlock (S1a); no failed system or user units; the runtime assertions moved out of `system.sh` and `power.sh` (journal persistence, one NTP client, the tuned profile). From S1c: `module.sig_enforce` holds, and SELinux is enforcing with no module-load denials. From S3b: the lock matrix (right and wrong password, Esc, blank and wake, suspend and resume while locked, Reduce Motion, `apex.safe=1` giving the stock two-stage lock, `loginctl unlock-session`); greeter and lock goldens once approved |
| Hardware | per slice, on the laptop | [hardware/ACCEPTANCE.md](hardware/ACCEPTANCE.md); each fix has a numeric pass criterion. The G4 VM exercises neither NVIDIA nor s2idle, so each new kernel line and each NVIDIA release runs ACCEPTANCE §4 and the s2idle rows. The glass rows run in S2b and S3a, and again after a blur change. |

`ci.yml` checks the code on every push (§4). The ADR 0014 patch budgets are a review
rule, not a gate. Chromium renders of the mockup are never a gate: they use another
renderer, web fonts and CSS blur, so no threshold would pass.
````

## E22. §12 What the design review changed (lines 556-572)

Why: A review changelog is history, not architecture. The 2026-09-28 review is kept at
`docs/reviews/2026-09-28-review.md`.

Old (lines 556-572, 17 lines, quoted in part):

````markdown
## 12. What the design review changed

| Finding | Change |
[… 12 lines …]
| First install would wipe Windows and Ubuntu | An install ADR: `to-filesystem` onto a prepared LUKS2 + btrfs layout, keeping Windows (ADR 0010) |
| NVIDIA, MOK, COPR kernel and third-party repos in M1 | Moved to M2; the M1 supply chain is Fedora plus Apex only |
````

New: delete these lines.

## A1. ADR 0002 (lines 1, 3, 17-21, 29-32)

Why: Code inside a GNOME project follows that project's language (ADR 0014). Apex code
now runs inside gnome-shell rather than as extensions, and promotion is gone. The
existing build glue is Bash.

Old (line 1):

````markdown
# ADR 0002: Rust for every Apex component
````

New:

````markdown
# ADR 0002: Rust for Apex's own components
````

Old (line 3):

````markdown
Status: accepted (2026-09-24, revised after design review)
````

New:

````markdown
Status: accepted (2026-09-24, revised after design review); amended by ADR 0014
````

Old (lines 17-21):

````markdown
Every Apex component is Rust: libraries, daemons, CLIs, GTK apps and build tooling.
There are two exceptions, both forced by the platform:

- The GNOME Shell extension (M2+) is TypeScript compiled to GJS.
- Kernel and libfprint patches are C.
````

New:

````markdown
Apex's own daemons, agents, CLIs and dev tools with real logic are Rust. Code that
lives inside another project is written the way that project writes it:

- The Apex layer inside gnome-shell is GJS ES modules. No TypeScript.
- Patches to gnome-shell's blur effect, libadwaita, gnome-control-center and nautilus
  are C, with Blueprint where the project uses it.
- Themes are SCSS, the boot splash is Plymouth script, and build glue is Bash.
- Kernel and libfprint patches are C.

There is no Go (ADR 0014).
````

Old (lines 29-32):

````markdown
- **An enabled Shell extension runs inside the compositor.** A synchronous D-Bus call or
  a runaway timer in it freezes the whole desktop. The extension therefore holds
  presentation only, uses asynchronous proxies with timeouts, and is gated by a headless
  Shell smoke test before promotion.
````

New:

````markdown
- **Apex code inside gnome-shell runs in the compositor.** A synchronous D-Bus call or
  a runaway timer in it freezes the whole desktop. The Apex layer therefore uses
  asynchronous proxies with timeouts, falls back to stock at every hook, and is gated
  by the headless shell check (G2) before an image is published.
````

## A2. ADR 0007 (lines 3, 25-29)

Why: Milestones no longer exist. The ADR 0014 lane allows spec-only rebuilds, which
this ADR forbade by implication.

Old (line 3):

````markdown
Status: accepted (2026-09-24, revised after design review)
````

New:

````markdown
Status: accepted (2026-09-24, revised after design review); amended by ADR 0014
````

Old (lines 25-29):

````markdown
- **Allowlist entries.** Each entry names its reason and the milestone that removes it.
  The list can only shrink.
- **No private forks for zero GTK3.** Apex does not fork network- or input-facing
  libraries (evolution-data-server, ibus) just to reach zero GTK3; that would take on
  their security updates. Allowlisted packages go away when upstream drops GTK3.
````

New:

````markdown
- **Allowlist entries.** Each entry names its reason and the condition that removes it.
  The list can only shrink.
- **No rebuilds of network- or input-facing libraries for zero GTK3.** Apex does not
  rebuild evolution-data-server, ibus or similar libraries just to drop GTK3; that would
  take on their security updates. A spec-only rebuild through the ADR 0014 lane (no
  source patches, for example gdm `--without x11`) is allowed after the desktop slices
  ship. It takes that package off Fedora's signature.
````
