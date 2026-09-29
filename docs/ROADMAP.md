# Roadmap

Status: accepted (2026-09-28), with ADR 0014 and ADR 0015. The proposal it grew from is
kept as `docs/reviews/2026-09-28-roadmap.md`.

Slices are ordered by what the owner sees. Each slice from S1a on ends with an image
the owner can boot: in the desktop VM for S1a to S1c, on the laptop from S1d. Every
slice has exit criteria that can be checked. The hardware track runs in parallel from
day one.

Related documents:

- ADR 0014 (`docs/adr/0014-engine-level-desktop.md`), rewritten as "Engine-level
  desktop: rebuilt gnome-shell first": mechanisms, patch budgets, kill switches.
- ADR 0015 (`docs/adr/0015-cachyos-kernel-and-nvidia.md`): the CachyOS GCC kernel and
  the NVIDIA open modules, built as one pair.
- `design/SPEC.md`: geometry, settings, and the §8 items this roadmap schedules.
- The 2026-09-28 review (`docs/reviews/2026-09-28-review.md`): findings, cuts (§4), the
  decision sheet (§5) and the owner's answers (§5.3).
- The architecture delta (`docs/reviews/2026-09-28-architecture-delta.md`): the target
  system, with each unbuilt part tagged with its slice.

## What the answers changed

| Answer (review §5.3) | Effect on this plan |
|---|---|
| 1, 2: a rebuilt gnome-shell is the primary mechanism; the SCSS enters the package through an `@import` hook | The rebuild lane comes first (S1a), with gnome-shell as its first customer. The Apex layer lives in the package, with a stock fallback per hook. The `shelltheme` stage, the extensions and Dash to Dock are not built. The dock is Apex's own (S2a). |
| 6: Super+Space opens Spotlight | Input switching moves to Super+Alt+Space (S1b). Until Spotlight exists (S3a), Super+Space opens the stock overview search. |
| 14: dynamic glass everywhere | A patched `ShellBlurEffect` and a glass manager (S2b). A first performance run on the laptop in S2b; the full exit in S3a. Reduce Transparency stays the off switch. |
| 17: recommended boot handoff; Windows deleted later | The owner deleted Windows on 2026-09-29, before S4 (step W). S4 installs next to Ubuntu, with none of the Windows parts. |
| 22: CachyOS GCC kernel; NVIDIA modules built for exactly that kernel | A new slice, S1c, before the first laptop boot. The dGPU is used. |
| 26: build the §8 items now | Each item has a slice and a size ("Where the SPEC §8 items land"). |

The daily-driver date moves from 2027-02-12 to 2027-04-30. That is the cost of the
answers: about 11 weeks of owner time.

## Sizes and timing

- S is at most 1 day, M is 2 to 5 days, L is 1 to 3 weeks.
- Work that does not fit in 3 weeks is split into parts (S1a to S1d, S2a to S2d, S3a to
  S3c). A part keeps its slice number, so "S1" in other documents means all of S1.
- Weeks count from the day the owner accepts ADR 0014 and ADR 0015. Week 1 is the first
  full week after it.
- Target dates assume acceptance on Wednesday 2026-09-30, and one owner working with AI
  help about five days a week.
- From S1d on, standing work (kernel, NVIDIA and GNOME updates) takes about 1.5 to 2
  owner-days a month ("Standing work", below). Slice lengths include it.
- The dates include no holidays or breaks. A break moves every later date by its length.
  Tết falls on 2027-02-06, between S2c and S2d.
- Estimates carry about ±20 %. The first slices re-estimate the rest.

| Slice | The owner gets | Weeks after acceptance | Target dates | Size |
|---|---|---|---|---|
| S0 | The decisions applied, the hardware answers | until 2 days after | Sep 28 – Oct 2 | M |
| S1a | A rebuilt gnome-shell with its safety net and dev loop, in the desktop VM | 1–3 | Oct 5 – Oct 23 | L |
| S1b | The Apex theme, assets and Super+Space, in the desktop VM | 4–6 | Oct 26 – Nov 13 | L |
| S1c | The CachyOS kernel and NVIDIA pair in every image | 7–8 | Nov 16 – Nov 27 | L |
| S1d | Apex on the laptop from the USB SSD | 9–10 | Nov 30 – Dec 11 | L |
| S2a | The Apex dock and top bar | 11–13 | Dec 14 – Jan 1 | L |
| S2b | Dynamic glass, with a first laptop measurement | 14–15 | Jan 4 – Jan 15 | L |
| S2c | The Apex Desktop panel and live window radius | 16–18 | Jan 18 – Feb 5 | L |
| S2d | Updates in Settings and the Files window | 19–21 | Feb 8 – Feb 26 | L |
| S3a | Spotlight, overview, launcher; the glass exit | 22–24 | Mar 1 – Mar 19 | L |
| S3b | Lock screen and greeter | 25–26 | Mar 22 – Apr 2 | L |
| S4 | Daily driver on the internal disk | 27–28, then 2 weeks of use | Apr 5 – Apr 30 | L |
| S3c | Notifications, Quick Settings, motion, shadows | 29–30, during S4's use | Apr 19 – Apr 30 | L |
| S6 | Fedora 46 and GNOME 52 | 31–34 | May 3 – May 28, 2027 | L |
| S5 | Apex glyphs, if confirmed | 2 weeks after S6 | about June 2027 | L |
| W | Windows removal | owner-triggered; started 2026-09-29 | W1 and W4 done 2026-09-29; W2 in S4; W5 after the owner's speaker test | S to M |

S3c runs during S4's two weeks of use, so its changes reach the daily driver as
ordinary updates. The owner can move S4 earlier, to right after S2d (target
2027-03-01). Then S3a to S3c ship as updates to the daily driver, and the unlock-path
changes of S3b land on the only machine.

## Gates

Gates stay proportionate for one owner. ARCHITECTURE §11 has the details.

- **G1, build checks,** on every image build.
  - Kept: legacy, firmware, keys, secrets, signing, overlay, UEFI only, `--strict`
    schemas, `bootc container lint --fatal-warnings`.
  - From S1a: composefs is on; gnome-shell is `.apexN` at the NEVRA the lane locked, and
    signed with the Apex RPM key; the Apex marker is in the light and dark sheets
    (`grep -a` on the theme resource); upstream's sheets exist under
    `/org/gnome/shell/theme/stock/` (the lane and G2 check them); no
    `G_RESOURCE_OVERLAYS`, `--unsafe-mode` or `APEX_SHELL_TEST_FAULT` in `/usr` or
    `/etc`; the Apex schema compiles with `--strict`; the crash guard is installed.
  - From S1b: every `.desktop` `Icon=` resolves (with the Colloid icon theme); no two
    default bindings share a combo across `wm.keybindings`, mutter, the shell, media
    keys and the Apex schema.
  - From S1c (ADR 0015): exactly one kernel and one `kmod-nvidia` for it; every module
    signed by that build's key; NVIDIA `vermagic` equals the kernel; the kernel config
    assertions; one NVIDIA version across the modules, the userspace and the GSP
    firmware; the effective `modprobe` options; no nvidia, nouveau or nova module in the
    initramfs; no akmods, DKMS or kernel-devel; `nvidia-persistenced` disabled; the
    NVIDIA licence file present.
- **Lane checks,** on every package build: the SRPM signature, fuzz 0, the build, the
  Apex marker, the Apex RPM signature on what it built. For the kernel pair also: one
  signing key on every module (SHA-512 on the in-tree modules; SHA-256 on the NVIDIA
  ones, which kmodtool's `brp-kmodsign` always uses), no private key in any payload, the
  module count within ±5 % of the last pair, BTF present.
- **G2, headless shell,** from S1a, on every image build. The built image runs
  gnome-shell at scale 2 with fixtures and a fixed clock, twice: with the Apex layer,
  and with `APEX_SHELL_SAFE=1`. It fails on a `JS ERROR`. The safe run asserts stock
  values (for example thumbnail scale 0.05 and the stock stylesheet path). Metric
  assertions sit where a regression is likely (`design/SPEC.md` §7). A glass pixel test
  joins in S2b.
- **Goldens.** Captures of the real shell, approved by the owner screen by screen. An
  approved golden gates every `just publish` from then on.
- **G4, VM check,** weekly, and before publishing a change to the gnome-shell, mutter or
  gdm NVR, the kernel pair, `crates/apex-*`, the kargs or GRUB. Install, upgrade and
  counted rollback, then boot to GDM, log in, lock and unlock (from S1a). The full lock
  matrix joins in S3b. The VM exercises neither s2idle nor NVIDIA.
- **Hardware:** `docs/hardware/ACCEPTANCE.md`, run on the laptop. A kernel major bump
  and an NVIDIA driver bump each need one owner run before they publish.

## Calendar

External dates, checked 2026-09-28.

| Date | Item | Source |
|---|---|---|
| 2026-10-10 | GNOME 51.1. It reaches F45 around GA. It is the first shell and mutter update the lane absorbs (S1b exit). | https://release.gnome.org/calendar/ |
| About 2026-10-18 or -25 | Linux 7.3 (7.3-rc5 came out on 2026-09-27). The COPR built 7.2.0 about 103 h after its release. 7.2 goes EOL about 16 days after 7.3.0, as 7.1 did. K1 sees this bump; S1c starts on 7.3.y. | https://www.kernel.org/releases.json; COPR build list API |
| 2026-10-20; later targets 10-27 and 11-03 | Fedora 45 GA. Within 7 days, delete the updates-testing admission (review §4). From `FEDORA_GA_DATE` plus 7 days, every build fails while `updates-testing-allowlist.txt` has entries (the dated check in `image/Containerfile`'s repos stage). If GA slips, move `FEDORA_GA_DATE` first. | https://fedorapeople.org/groups/schedule/f-45/f-45-key-tasks.html (fetched 2026-09-28: final target 2026-10-20, then 10-27 and 11-03) |
| Late December 2026 to early January 2027 | Linux 7.4: the first kernel major bump through the lane, with owner review. 7.3 goes EOL about two weeks later. | estimate from the 7.1 to 7.3 cadence |
| 2027-02-09 | Fedora 46 branch point, 10 weeks before the 2027-04-20 target. The builder VM starts an unattended `FEDORA=46` compose that publishes nothing (S6 prep). | https://fedorapeople.org/groups/schedule/f-46/f-46-key-tasks.html (fetched 2026-09-28) |
| February to March 2027 | GNOME 52 beta and 52.0. The 52 schedule is not published; by the 51 cycle (beta 2026-08-01, 51.0 2026-09-12) the beta lands in early February and 52.0 in mid-March. F45 stays on GNOME 51. | https://release.gnome.org/calendar/ |
| 2027-04-20 | Fedora 46 GA target. | as above |
| 2027-11-24 | Fedora 45 EOL. `apex:46` must be on the laptop before it. The dated check on the COPR key (expires 2028-01-23) also starts failing that day, 60 days ahead. | https://fedorapeople.org/groups/schedule/f-45/f-45-key-tasks.html (fetched 2026-09-28); ADR 0015 |

## Standing work

From S1d on, every lane runs from the builder-VM timer on AC power: daily, and every 4
hours for the kernel poll. Expected owner time, from the Aug–Sep 2026 samples:

| Stream | Cadence | Owner time |
|---|---|---|
| GNOME point release (gnome-shell with mutter, libadwaita, gnome-control-center, nautilus) | about monthly; 5 shell releases in the 50.x cycle | 0.5 to 2 h when the series applies; a rebase otherwise |
| Kernel point release within a major | about weekly as the COPR builds them (7 builds of 7.2 from 2026-08-21 to 09-26; kernel.org made 8 point releases, 7.2.1 to 7.2.8, from 08-27 to 09-25) | none; it publishes after G1, G2 and G4 |
| Kernel hold at 72 h | in the sample, 2 of the 8 7.2 point releases first reached the COPR after more than 72 h: 7.2.4, which the COPR skipped, in 7.2.5 after about 138 h, and 7.2.6 after 98 h; 7.2.0 (103 h) was a major | a wait-or-break-glass decision, once or twice a month |
| Kernel major bump | every 9 to 10 weeks | 1 to 3 h of review plus a laptop acceptance run |
| NVIDIA driver bump | about monthly | the 7-day soak is unattended; one ACCEPTANCE §4 run, about 1 h |
| GNOME major | twice a year | 4 to 8 owner-days (S6) |

That is about 1.5 to 2 owner-days a month on average.

The kernel poll runs every 4 hours on AC, not daily. With a daily poll, the 48 h and
53 h releases of the sample would also have crossed 72 h once the build and G4 are
added. If the kernel holds still prove frequent, the lane can build from the signed
CachyOS tag and the spec at its git commit, without waiting for the COPR SRPM
(ADR 0015). Measure the tag-to-COPR lag during S4 before adding that.

## S0: Baseline, decisions and hardware answers (Sep 28 – Oct 2, M)

State on 2026-09-28:

- The baseline is commit a08a3eb ("chore: import baseline tree",
  2026-09-28 16:44 +0700), with the tag `baseline-2026-09-28` on it. The S0 commits on
  top of it, starting with the proposal documents, are pushed to `origin/main` on
  `github.com/SekiroKenjii/apex-fedora`.
- The owner answered the decision sheet the same day (review §5.3). ADR 0014 and
  ADR 0015 were accepted on 2026-09-28.
- The 12 workflows are one, `ci.yml`.
- `privacy-guard.sh` passes on the tree, with its `design/mockup/` exemption.

Remaining steps, in this order:

1. On GitHub, confirm that the repository is private, that the tag is there, and that
   no workflow ran on the push. If one ran, cancel it and turn Actions off. The
   baseline held 12 workflows: one called a build of up to 330 minutes, and the
   privacy guard failed on the mockup.
2. Run `just privacy` and a private-key scan over the tree. On 2026-09-28 the key scan
   found only the test fixture in `image/tests/t-secrets.sh`. The privacy guard
   reported 76 findings, all in `design/mockup/`: C2PA manifests and long lines.
3. Add the proposal documents as new files: the review, this roadmap, the delta,
   `design/SPEC.md`, ADR 0014 (rewritten) and ADR 0015.
4. The owner accepts or amends ADR 0014 and ADR 0015.
5. After acceptance, each change is a reviewable commit on the baseline:
   - ADR 0014 accepted: ADR 0011 superseded; ADR 0002 and ADR 0007 amended (delta A1,
     A2). ADR 0015 accepted: ADR 0005 superseded; ADR 0012 and ADR 0004 amended. This
     file replaces `docs/ROADMAP.md`. The delta is applied to `docs/ARCHITECTURE.md`.
   - `packaging/kernel/` (`copr.mk`, `apex-spec-header.inc`, `kernel-local`, `series`)
     deleted. The disabled ALC294 patch moves to `packaging/pkgs/kernel/patches/`.
   - `rd.shell=0` and `rd.emergency=reboot` removed from
     `image/system_files/usr/lib/bootc/kargs.d/10-apex.toml`, with the comments, tests
     and docs that cite them (review §4). `panic=10` stays.
   - The privacy guard exempts `design/mockup/` from its long-line and hex-run rules.
   - The 12 workflows become one, `ci.yml`. Actions go back on, and `ci.yml` runs
     green once.

In parallel, about 4 owner-hours on the current Ubuntu install (hardware track):

- the speaker test with no fix loaded (`docs/hardware/AUDIO.md` §2), and the `model=`
  alias experiment only if a row fails;
- the elanpress genuine and impostor score test;
- an s2idle baseline;
- the dGPU baseline measured on 2026-09-28 (595.91.07 open, RTD3 fine-grained, 95.9 %
  runtime-suspended, s2idle only, no MUX) written to `docs/hardware/`, plus one
  30-minute lid-closed s2idle run each with `NVreg_EnableS0ixPowerManagement=0` and
  `=1`.

- **Exit:**
  - no workflow ran on the push, and the repository is private;
  - ADR 0014 and ADR 0015 are accepted or amended;
  - `ci.yml` is green on `main`;
  - outside `docs/reviews/`, `grep -rn 'ADR 0005' docs` shows only its superseded
    status;
  - the audio result, the fingerprint verdict, the s2idle baseline and the two S0ix
    runs are recorded in `docs/hardware/`.
- **Owner sees:** the decisions in the repository, a green check, and possibly working
  speakers on Ubuntu the same day.

## S1a: The rebuilt shell and the dev loop (weeks 1–3, Oct 5 – Oct 23, L)

There is little to see in S1a. The price of answer 1 is that the lane, the loader and
the safety net come before the first Apex pixel.

- The generic rebuild lane (ARCHITECTURE §4.1), with gnome-shell as its first customer:
  - `apex-lane` (`crates/apex-lane`) and `packaging/pkgs/<pkg>/`: fuzz 0, `.apexN`, generated
    `includepkgs` and `excludepkgs`, `rpms.lock`, content keys;
  - `packaging/pkgs/gnome-shell/`: `pkg.env` with `on_fail=hold` and the hold family
    gnome-shell and mutter; the anchored `spec-edit` (the spec uses `%autorelease`);
    Source1 from `desktop/shell/`; `Requires: mutter = <the buildroot EVR>`;
  - the RPM signing key with an offline backup (answer 21); `[apex]` drops
    `gpgcheck=0`. It moves here from S2.
- Series 0001-build and 0002-loader with an empty layer: `hooks.js`, the configure and
  enable phases, a `try/catch` per feature.
- The safety net (ADR 0014): `apex.safe=1` and `APEX_SHELL_SAFE=1`; the `layer-enabled`
  and `disabled-features` keys, in the Apex schema; the crash guard (a user-unit
  drop-in with `OnFailure=apex-shell-safe.service`). A first `apex-desktop` build
  ships the schema and the crash guard's units (S1b fills the RPM). Until the agent's
  offer in S1b, the owner turns the layer back on with `gsettings`.
- The `sessionMode.js` hook: `'default'` draws a light shell. The override sets no
  `color-scheme`.
- The dev loop, printed by `just --list`:
  - JS and SCSS through `G_RESOURCE_OVERLAYS` and `gnome-shell --devkit` in the desktop
    VM, in seconds;
  - C through incremental ninja in an F45 toolbox and `bootc usroverlay`, 1 to 3
    minutes;
  - the lane RPM in 10 to 15 minutes;
  - image changes through `podman save | ssh … podman load` and
    `bootc switch --transport containers-storage`, about 10 minutes, keeping
    `/var/home` and `/etc`.
- G1 shell checks and the composefs check. G2, twice per build. G4 with boot to GDM,
  login, lock and unlock, triggered by a shell, mutter or gdm NVR change.
- The token file and the top-bar SCSS, as the proof of the `@import` hook.
- In parallel, in the builder VM: the kernel spike K1 (S1c).
- **Exit:**
  - a `.apex1` gnome-shell is built from the F45 SRPM; `rpm -qp --requires` shows
    `mutter = <EVR>`;
  - with the empty layer, G2 captures equal Fedora's stock shell outside the masks;
  - the safe G2 run asserts the stock values;
  - on the shipped build, with `APEX_SHELL_TEST_FAULT=enable` in the shell's
    environment, a feature that throws at enable is off for that session while the rest
    of the layer runs; with `APEX_SHELL_TEST_FAULT=abort-after-enable`, a shell that
    aborts within 60 s of enable sets `layer-enabled=false`, so the next login in the VM
    runs stock JS and CSS (ADR 0014, crash guard). G1 keeps the variable out of the
    image;
  - turning Dark Style off in Quick Settings gives a light shell with `color-scheme`
    `'default'`, and no agent runs;
  - an SCSS or JS change shows in the devkit shell within 15 s;
  - G4 passes install, counted rollback, login, lock and unlock.
- **Owner sees:** in the desktop VM, a shell from Apex's own package that looks like
  stock GNOME with the Apex top bar, light by default, and a 15-second edit loop.

## S1b: The Apex theme, assets and Super+Space (weeks 4–6, Oct 26 – Nov 13, L)

- Apex SCSS, light and dark, through the hook:
  - Quick Settings (stock submenus styled to match), the calendar and notifications on
    stock structure, the overview, the app grid;
  - the derived surfaces in `design/SPEC.md` §3.17.
- The `apex-desktop` noarch RPM:
  - the icon theme from a pinned Colloid commit;
  - fontconfig `ss03`, JetBrains Mono, `Adwaita Sans 10.125` and `JetBrains Mono 9.75`
    (answer 12), no hinting;
  - the Apex Aurora wallpapers, rendered with dithering at 2880×1800;
  - the terminal prompt colours and line spacing (screen 09);
  - the rewritten override, the rest of the Apex schema and its keybindings child
    schema.
- The app set from answer 10, in `image/packages/`.
- Super+Space (answer 6):
  - `toggle-spotlight=['<Super>space']` in
    `io.github.sekirokenjii.Apex.Desktop.Keybindings`, registered with
    `Main.wm.addKeybinding` in the normal and overview modes. It opens the stock
    overview search until S3a;
  - `switch-input-source=['<Super><Alt>space','XF86Keyboard']` and
    `switch-input-source-backward=['<Shift><Super><Alt>space','<Shift>XF86Keyboard']`
    in the override. No GNOME 51 default uses these combos. `per-window=true` stays;
  - `60-apex.xml`, so Settings > Keyboard lists and edits the binding;
  - the G1 combo check; the tooltip "Search (Super+Space)" and the first-login hint
    "Press Super+Space to search";
  - a Super tap still opens the overview, and Super+A the launcher.
- `apex-session-agent` v0 (Rust, user unit):
  - offers "Turn the Apex desktop back on" after the crash guard fires;
  - writes `~/.config/gtk-4.0/apex.css` for the window radius (14, answer 5);
  - writes the Ptyxis `apex.palette` with the accent caret (SPEC §8), after a spike
    checks that an open terminal reloads it.
- A Bazaar spike checks that the Flatpak override exposes `apex.css`.
- In the week after Fedora 45 GA: delete the updates-testing admission (review §4).
- A contact sheet per screen (G3, not a gate).
- **Exit:**
  - a new session in the VM starts light with the Apex theme, Colloid icons, JetBrains
    Mono and the wallpaper, and no `JS ERROR`;
  - Super+Space opens search, and IBus does not switch the input source on it;
    Super+Alt+Space switches English and Telex, shows the switcher when held, and the
    Shift variant goes back; the journal has no `Overwriting existing binding`; both
    rows show in Settings > Keyboard;
  - changing the accent recolours the caret in an open terminal within 1 s, or the
    owner decides on a small Ptyxis patch;
  - GNOME 51.1 (or the first shell and mutter update after S1a) was absorbed through
    the lane with fuzz 0, or rebased within its hold limit;
  - the owner signs off the contact sheets for 04 and 05 (styling), 07, 08 (styling)
    and 09, light and dark. They become the first approved goldens.
- **Owner sees:** the Apex skin on every stock surface, Colloid icons, JetBrains Mono,
  the wallpaper, Super+Space for search, and the accent caret in the terminal.

## S1c: The kernel and dGPU pair (weeks 7–8, Nov 16 – Nov 27, L)

It lands before the first laptop boot, for four reasons:

- every hardware row that S1d measures (speakers, s2idle, amd-pstate, RTD3) depends on
  the kernel and the driver, so each is measured once, on the kernel the owner chose;
- the Fedora-kernel variant built here is the A/B baseline for S1d and the break-glass
  image;
- with NVIDIA bound, GNOME sees a second GPU; the first laptop session should see the
  topology it will keep;
- the compose unknowns for a third-party kernel are settled in the builder VM, not on
  the laptop.

Fallback: if the pair is not green at the end of week 8, S1d goes ahead with the Fedora
kernel and the dGPU unbound (the plan before the answers). The pair then arrives as an
update, and S1d's kernel-dependent rows run again.

Before this slice, in parallel with S1a and S1b, **K1** (M, builder-VM compute, about 2
owner-hours):

1. Download the current COPR SRPM, check it with `rpm -K` against the pinned COPR key,
   store it, and `rpmbuild --rebuild` it unmodified in a fresh `fedora:45` container,
   twice, the second time with a warm ccache. Record wall time, peak RSS
   (`/usr/bin/time -v`), scratch disk and the ccache hit rate.
2. Compose an image with `build-rootfs --exclude` of the Fedora kernel names,
   `--install kernel-cachyos` and `--no-initramfs`, then depmod and dracut in the final
   stage.
3. Rebuild negativo17's nvidia-kmod for that kernel with a tmpfs key; check `modinfo`
   `vermagic` and `sig_key`.
4. Run `just vm-qualify`.
5. Repeat 1 and 3 when the COPR ships 7.3.0, to see whether NVIDIA 615 builds on the new
   major.

K1 exit: `bootc container lint --fatal-warnings` passes with an empty skip list; the
qualify run is green with SELinux enforcing and no module-load AVCs (which decides the
`domain_kernel_load_modules` boolean); the numbers are in
`packaging/pkgs/kernel/README.md`. The host has 14.5 GiB of RAM (`MemTotal`
15,229,740 kB) and the builder VM 6 GiB (`tools/builder-vm/README.md:58-60`). K1
decides between `-j6` at 6 GiB and a 10 GiB VM for kernel jobs, which run at night on
AC.

The slice (ADR 0015):

- `packaging/pkgs/kernel/`: `kernel.env` (COPR SRPM NEVR, sha256, COPR key, CachyOS tag
  key), `nvidia.env` (nvidia-kmod SRPM and the userspace NEVRs, negativo17 key),
  `kernel-spec.patch`, the kmod build, `series`, `patches/`, README.
- `apex-lane build kernel` runs the pair job, as a package kind of its own:
  - verify and mirror every SRPM and third-party binary at first sight (the COPR keeps
    5 builds, negativo17 the last 2 builds of each package);
  - one per-build module key in a tmpfs, built into that kernel and used for the NVIDIA
    modules in the same job, then shredded;
  - ccache, both rpmbuilds, the lane checks, rpmsign, `rpms.lock`, and a bump report
    (upstream delta, config and Patch0 diff, NVIDIA patch list).

  No persistent MOK exists until Secure Boot (W3). This keeps answer 21's two keys.
- Image integration: `excludepkgs` for exactly the Fedora kernel packages;
  `exclude.txt` adds akmods, akmod-nvidia, dkms, dkms-nvidia and kmodtool; the
  build-rootfs flags; depmod; dracut `--omit-drivers` for the nvidia modules; the
  rewritten `kernel.sh` with the config assertions.
- kargs: `module.sig_enforce=1`, `zswap.enabled=0`, and
  `module_blacklist=nouveau,nova_core` in place of the two blacklist kargs.
  `apex-dgpu.conf` is deleted.
- The NVIDIA userspace set from negativo17, mirrored with `nvidia.lock`; no X server
  parts and no nvidia-settings (the legacy gate is unchanged). `apex-nvidia.conf`,
  `61-apex-dgpu.rules` (runtime PM on `add|bind`, and `mutter-device-ignore` on the
  NVIDIA card), `nvidia-persistenced` disabled, `image/checks/nvidia.sh`.
- The pair lock and holds: one side moves per image, kernel first; a kernel hold at 72 h
  from the kernel.org release, then the owner chooses between waiting and the
  break-glass image; a kmod-only failure holds the old pair for 72 h (point release) or
  14 days (new major), then `degraded=nvidia` with the owner's publish override.
- `just kernel-bump`, polled every 4 hours on AC: automatic within a major; a major
  prints "waiting for owner" with the EOL countdown from `releases.json`.
- The break-glass variant, `just image KERNEL=fedora`: Fedora's signed kernel with the
  NVIDIA half built for it, no `sig_enforce`. Built once here.
- **Exit:**
  - an image with the pair passes G1, G2 and G4;
  - three rehearsals in the builder VM: a kernel point bump publishes unattended; an
    injected kmod failure holds the pair with the `held` label shown by
    `apexctl status`; an expired limit produces a `degraded=nvidia` image that passes
    G1;
  - a cold pair build takes at most 2 h and a warm one at most 1 h, without OOM;
  - the break-glass image boots in the builder VM.
- **Owner sees:** `uname -r` reading `7.3.y-cachyos1.apexN.fc45.x86_64` in the desktop
  VM, and the first automatic kernel bump.

## S1d: Apex on the laptop (weeks 9–10, Nov 30 – Dec 11, L)

- `just publish` in the builder VM: push under a unique tag, sign with cosign, move
  `:45`. It runs by hand and from the daily host timer on AC power (answer 20). It
  refuses an image whose degraded set grew, unless the owner overrides it.
- The cosign key, generated in the builder VM, and its offline backup. `policy.json`
  lists only these two keys. The `apex-testing` entry and `ci.pub` go.
- A public source artifact per published digest: the kernel and nvidia-kmod SRPMs and
  the Apex series (GPL; NVIDIA licence).
- The Plymouth script theme `apex` (SPEC §8): the black splash with the Apex wordmark
  (answer 17), the 160×3 bar with round ends, @2x assets, and its own LUKS prompt. The
  two-step theme stays as the fallback.
- Install on the external USB SSD, with LUKS2 (ADR 0010).
- The audio drop-in, if the S0 test failed a row and a `model=` alias won. CachyOS
  carries Realtek quirks for other ASUS models, so the winner is checked again on this
  kernel.
- ACCEPTANCE §4 rewritten for the NVIDIA driver: rows 4.1 to 4.9 and the wake counter
  (ADR 0015).
- The Flatpak GL.nvidia sync step in `apex-flatpak-update`.
- The driver-bump procedure: 7 days in negativo17, the Flathub extension present, and
  one owner run of ACCEPTANCE §4 from the staged deployment.
- K3, the A/B of the pair against the break-glass variant, both on the USB SSD with
  `bootc switch`: amd-s2idle, `last_hw_sleep`, overnight drain, 20 lid cycles, idle and
  video power, amd-pstate EPP writable and following tuned-ppd, speakers and headset
  mic, KVM for the builder VM, no SELinux AVCs.
- **Exit:**
  - the laptop boots Apex from the USB SSD, and `apexctl update check` finds a newer
    `:45` that `just publish` signed;
  - the owner signs off 01 (boot splash) on the laptop: sharp at DeviceScale 2, round
    bar ends, LUKS unlock works;
  - ACCEPTANCE §4 rows 4.1 to 4.5, 4.7 and 4.8 pass: RTD3 "Enabled (fine-grained)";
    at least 95 % runtime-suspended over 10 idle minutes; D3cold with video memory
    off; Vulkan, EGL and GLX offload through `switcherooctl` and the GNOME menu, then
    D3cold within 30 s; D3cold within 60 s after HDMI hotplug; a Flatpak offload app;
    `nvidia-smi -L`;
  - amdgpu is mutter's primary GPU, and GDM starts on Wayland (journal lines in
    `docs/hardware/`);
  - no K3 power row is more than 5 % worse on the pair than on the Fedora kernel, or
    the owner decides with the numbers;
  - Super and Alt sit next to each other on this keyboard, so Super+Alt+Space is one
    hand;
  - the speakers pass their rows, with no fix or with the drop-in.
- **Owner sees:** the Apex splash and desktop on the laptop, the CachyOS kernel, apps
  that run on the RTX 3050 on request, and updates from the signed image.

## S2a: The dock and the top bar (weeks 11–13, Dec 14 – Jan 1, L)

- ApexDock (ADR 0014), a subclass of upstream `Dash` in `js/ui/apex/dock/`, about 800
  lines:
  - hooks in `dash.js`: icon sizes 46, 54 and 62; the order ending with a 40 px
    separator, Show Apps and Trash; a full-colour Show Apps tile;
  - bottom gap 10, no strut, fullscreen tracking, intellihide, bottom-edge reveal;
  - the Trash item, the −6 px hover lift over .18 s, the running-indicator key,
    Ctrl+Alt+Tab focus;
  - the overview's own dash hidden, its Show Apps button bound to the dock's;
  - no Dash to Dock (the image never shipped it); the dock's keys live in the Apex
    schema.
- Top-bar hooks (SPEC §8): workspace dots 22×7 and 7×7 at .45; a 4×4 hot-corner zone
  next to the pressure barrier; the status-pill filter (camera, microphone, location,
  remote access, screen recording and sharing, unsafe mode and the input source stay);
  the focused-app name; the search button; the bar solid over maximised windows.
- The bar and dock keys of the Apex schema go live: `translucent-top-bar`,
  `show-focused-app-name`, `dock-icon-size`, `dock-intellihide`,
  `dock-running-indicators` and `dock-show-trash`.
- **Exit:**
  - G2 asserts bottom gap 10, radius 24, icon 54, and the order ending with separator,
    Show Apps, Trash; scripted intellihide and edge-reveal tests pass;
  - "Launch Using Discrete Graphics Card" appears in the dock menu on the laptop, and
    the app runs on NVIDIA;
  - the camera and microphone indicators still show during a Snapshot recording;
  - the owner signs off 03 (bar, dock, wallpaper, window corners) and the dock in 04 to
    08, light and dark. They become approved goldens.
- **Owner sees:** the floating Apex dock with its lift and Trash, the workspace dots,
  the app name in the bar, and a bar that turns solid over maximised windows.

## S2b: Dynamic glass (weeks 14–15, Jan 4 – Jan 15, L)

- Series 0003-blur, a C patch to `ShellBlurEffect` (at most 300 lines):
  - a saturation property, CSS's matrix in the existing final pass;
  - a corner-radius property;
  - background mode follows the actor's paint opacity;
  - downscale without the 256 px floor, box-filtered (a mipmapped sample, or chained
    halving if Cogl's mipmaps fail the pixel test);
  - the redraw-clip rule: re-blur only when the frame's redraw clip covers the whole
    glass box, otherwise draw the last result and queue a redraw of the box. This is
    the guard against the artifacts Blur my Shell documents, and it does not depend on
    JavaScript.
- The glass manager in `js/ui/apex/glass/`: bar, dock, Quick Settings, calendar, toast.
  It forwards window damage, moves, resizes and restacks under a glass surface as a
  redraw of that box, for latency only. The bar's glass is off while the bar is
  solid.
- Reduce Transparency and high contrast remove every blur effect and swap the tokens to
  solid. `disabled-features=['glass']` does the same for glass alone.
- A first performance run on the laptop (protocol below), scenarios A and B.
- **Exit:**
  - the G2 pixel test passes (a pattern under glass with partial damage, against a CPU
    reference blur); its first run fixes the tolerance, starting at a maximum error of
    3/255 and a mean of 1/255 per channel (`design/SPEC.md` §7.2);
  - 5 minutes of `CLUTTER_PAINT=damage-region` stress show no stale or black regions;
  - the stock unlock blur at default properties differs by 0 pixels from Fedora's build;
  - with Reduce Transparency on, G2 finds no blur effect on any actor;
  - scenarios A and B meet the glass thresholds below. If not, the levers apply here,
    in order: twice the downscale on the failing surface; a lower-quality step in the
    power-saver profile; then mutter's redraw-clip expansion, which puts mutter in the
    lane. That step is an ADR 0014 escalation: the owner decides it with these numbers.
- **Owner sees:** a frosted bar, dock and popovers that follow the windows beneath them,
  with the drawn saturation.

Glass protocol, on the laptop on battery, balanced profile, 90 Hz, 2880×1800:

- Sysprof, 60 s of mutter frame marks per scenario:
  - A: a 1080p60 video in a window that overlaps the dock, with Quick Settings open over
    it;
  - B: dragging a window under the dock and the popovers for 30 s;
  - C (S3a): 20 overview and app-grid toggles, and Spotlight over the video.
- Pass: p99 frame time at most 11.1 ms; at most 1 % dropped frames; p50 within 0.5 ms of
  the same run with Reduce Transparency.
- amdgpu `gpu_busy_percent` at 10 Hz: mean delta at most 5 points in A.
- Power: the mean `upower` energy rate, sampled every 10 s over three alternating
  10-minute runs each with glass and with Reduce Transparency, same windows, brightness
  50 %, Wi-Fi off. Idle delta at most 0.3 W; scenario A delta at most 0.5 W.

## S2c: The Apex Desktop panel and live radius (weeks 16–18, Jan 18 – Feb 5, L)

- gnome-control-center in the lane (`on_fail=hold`), with its dev tier: incremental
  ninja and `usroverlay` in the desktop VM, 1 to 3 minutes.
- Patch 0001: the Apex Desktop panel. The "Apex Tweaks" tile, an alias for
  `gnome-control-center apex`.
- libadwaita in the lane (SPEC §8): one patch loads `apex.css` into a provider at
  `GTK_STYLE_PROVIDER_PRIORITY_USER + 1` and reloads it when the file changes. GTK reads
  `gtk.css` once per process, so without the patch a stale value at user priority would
  win. Host apps then follow a radius change live; Flatpak apps keep reading `apex.css`
  at start. libadwaita reads no Apex schema (ADR 0014).
- libfprint through the lane (`on_fail=degrade`), if the S0 score test passed. Its RPMs
  are diffed against today's build before the verdict is applied. Then
  `packaging/libfprint/`, `oci-artifact.sh` and lock replay are deleted.
- **Exit:**
  - every row in `design/SPEC.md` §6.1 exists, is bound to its key and changes the live
    desktop;
  - a Corner Radius change updates open Files, Settings and Ptyxis windows within 1 s;
    maximised, tiled and fullscreen windows stay square; GTK apps start cleanly with no
    `apex.css`;
  - the owner signs off 10-settings-apex-desktop and 11. They become approved goldens.
- **Owner sees:** Settings with Apex Desktop first, where every switch, including
  Corner Radius, changes the open desktop at once.

## S2d: Updates in Settings and the Files window (weeks 19–21, Feb 8 – Feb 26, L)

- gnome-control-center patch 0002: coloured sidebar tiles in the mockup's order. The
  Appearance mapping is not needed after S1a.
- Patch 0003: the Software Updates row in System and its page on `Update1`.
- `Update1` and `apexctl status` expose the held and degraded lists from the image
  label, including a kernel hold with its 72 h clock and `degraded=nvidia`.
- `apex-session-agent`: the "Updates Ready" notification.
- nautilus in the lane: 0001 the disk footer, 0002 the item-count bar, 0003 a 72 px grid
  zoom level (SPEC §8).
- A hold drill: break a gnome-control-center patch on a branch and build the image.
- **Exit:**
  - System shows the real update count, and one update from `just publish` is applied
    from Settings;
  - the hold drill passes: the image builds with the last good package, the label lists
    it, and `apexctl status` and the Settings Updates page show it;
  - the owner signs off the other 10-* Settings screens and the Files window at the
    default zoom with 72 px icons. They become approved goldens.
- **Owner sees:** coloured Settings tiles, updates announced and applied from Settings,
  and the Files window as drawn.

## S3a: Spotlight, overview, launcher; the glass exit (weeks 22–24, Mar 1 – Mar 19, L)

- Spotlight in `js/ui/apex/spotlight/`: Apex's own rows over the stock search
  providers, with the drawn sections and caps (Calculator 1, Applications 4, Settings 3,
  Files 4), and the calculator copy toast. Super+Space now opens it.
- Overview: always-visible window titles; no workspace background cards; thumbnails
  150×94, shown from two workspaces (scale 0.104, threshold 1); the "No open windows"
  label.
- Launcher: 7 columns and 88 px; its own apps-only search pill.
- Glass on the overview and launcher scrims and on Spotlight. GNOME hides the window
  group in the overview, so each scrim blurs a non-reactive clone of `window_group`
  (wallpaper and windows) in actor mode, cached until the desktop beneath changes
  (ADR 0014). The bar and the dock over a scrim blur the scrim's result. Patch 0017
  puts the same glass on the OSDs, banners, Alt+Tab and the screenshot panel
  (`design/SPEC.md` §3.17).
- **Exit:**
  - Super+Space opens Spotlight; Up, Down, Enter and Esc work; a provider past a 1 s
    timeout does not hide the other sections;
  - with one busy workspace and the empty one, the thumbnails show;
  - the glass protocol passes scenarios A, B and C with every glass surface on;
  - the owner signs off 06, 06b, 07 and 08, light and dark. They become approved
    goldens.
- **Owner sees:** the Spotlight popup as drawn, overview titles and thumbnails,
  the launcher's own search, and glass everywhere without dropped frames.

## S3b: Lock screen and greeter (weeks 25–26, Mar 22 – Apr 2, L)

Series 0015-lock carries the review label "unlock path".

- Single stage, as drawn: the clock and the prompt show together, date above time,
  with the unlock hint. The prompt is torn down on blank and rebuilt on wake, so PAM and
  the fingerprint reader do not run while the screen is off.
- The SPEC §8 lock details: blur σ 30 with saturation 1.3; the field's own glass; the
  initial-letter avatar when the user has no picture; "Enter Password" only for PAM's
  exact `Password:` question.
- Greeter styling from the shared sheets. No Apex JS runs in the gdm mode.
- G4 gains the lock matrix.
- **Exit:**
  - the G4 matrix passes: right and wrong password, Esc, blank and wake, suspend and
    resume while locked, Reduce Motion, `loginctl unlock-session`, and `apex.safe=1`
    giving the stock two-stage lock;
  - a test PAM question other than `Password:` shows verbatim;
  - the owner signs off 02 and the greeter. They become approved goldens.
- **Owner sees:** the one-step lock screen as drawn, and an Apex login screen.

## S4: Daily driver (weeks 27–28, Apr 5 – Apr 16, L; then two weeks of use to Apr 30)

- The internal install (ADR 0010): LUKS2 with a recovery key, `/var` as its own btrfs
  subvolume, into the space Windows left (W2): sectors 1435648 to 903051263 of
  `nvme0n1`, 901615616 sectors or 429.9 GiB, between the ESP and Ubuntu's partition
  (measured 2026-09-29, `docs/INSTALL.md` §1 and §5.2). Nothing is shrunk. The ESP is
  shared with Ubuntu only.
- Ubuntu stays untouched as the fallback and builder host until Apex has passed its two
  weeks. When the owner removes it later, the builder VM and its keys move to Apex
  first (qemu-kvm from a toolbox), and one `just publish` from there succeeds before
  Ubuntu goes. Its partition starts right after Apex's, so the Apex root can then grow
  into it.
- The GRUB menu hidden unless the last boot failed (answer 17, a spike): the static
  `07_apex-menu.cfg`, and `apex-boot-assess` confirming every green boot in grubenv
  (`apex_ok=1`), not only armed ones (ARCHITECTURE §5.2, §5.5). Both ship in the image
  before the internal install, because bootupd copies static configs only at
  `bootc install`.
- Pin before arm: when applying over an unconfirmed or failed booted deployment, pin the
  last good deployment first.
- Fingerprint unlock through the authselect vendor profile, if the score test passed.
- K4: the status views show a kernel hold and its clock.
- N10, measured during the two weeks of use: s2idle rows, `nvidia-powerd` on and off,
  `NVreg_EnableS0ixPowerManagement`, the wake counter per idle hour. Add a post-resume
  runtime-PM toggle or the notifier fallback units only if a row fails.
- The OLED A/B (PSR, 60 Hz on battery, light against dark), and the acceptance
  additions (hardware track).
- **Exit:**
  - `docs/hardware/ACCEPTANCE.md` passes, including s2idle and §4.6;
  - the firmware boots Apex first, and the firmware's "Ubuntu" entry still starts
    Ubuntu;
  - `bootloader-update.service` is enabled and ran without failing (`docs/INSTALL.md`
    §9);
  - pin before arm fixes a failed build forward with one reboot, once, in the G4 VM;
  - one update is applied from Settings, and one `bootc rollback` is exercised;
  - at least one kernel point bump and one GNOME update were absorbed without owner
    work during the two weeks, or held and resolved within their limits;
  - two weeks of daily use on the internal disk, with automatic downloads.
- **Owner sees:** Apex as the daily system, suspend that holds the battery, and unlock
  by finger if the sensor allows it.

## S3c: Notifications, Quick Settings, motion, shadows (weeks 29–30, Apr 19 – Apr 30, L)

It runs during S4's two weeks of use and ships as updates.

- Notifications: a 38 px app-icon column and a flat list (groups expanded, headers
  hidden); Clear always visible, on the right; the Do Not Disturb footer switch.
- Quick Settings: Power Mode lit at Balanced through an `apex-lit` class (`checked` and
  the indicator binding stay stock); VPN after Airplane Mode; On/Off subtitles.
- Motion: an `environment.js` hook maps Apex's ease to `CUBIC_BEZIER` (.2,.8)(.2,1);
  window and overview durations. With `enable-animations=false` every transition takes
  0 ms.
- Two-layer shadows through shadow-layer actors under the popovers, Spotlight, the
  toast, the dock, window previews and the active thumbnail.
- **Exit:**
  - the power-profile indicator stays out of the status pill, and the toggle still
    switches between Balanced and the last profile;
  - G2 asserts the cubic-bezier mode on maximise and on the overview transition;
  - an idle desktop shows no extra repaints under `CLUTTER_PAINT=damage-region`;
  - the owner re-approves 04, 05 and every golden the shadows change.
- **Owner sees:** notifications and Quick Settings as drawn, the drawn easing, and the
  two-layer shadows.

## W: Windows removal (owner-triggered, 2026-09-29)

The owner deleted Windows on 2026-09-29 (answer 17), before S4. Nothing in Apex tooling
runs a destructive step; `docs/INSTALL.md` holds the runbook, and the owner types every
command.

The state on 2026-09-29, read without changing anything:

- `nvme0n1p2` (Microsoft reserved) and `p3` (Windows) are gone. The free space is
  sectors 1435648 to 903051263 (901615616 sectors, 429.9 GiB), between the ESP and
  Ubuntu's `p4` (`docs/INSTALL.md` §1).
- The ESP holds `EFI/ubuntu/` and `EFI/Boot/` (Ubuntu's shim as `bootx64.efi`, with
  `fbx64.efi`, `mmx64.efi` and two ia32 leftovers). `EFI/Microsoft/` is gone.
- The firmware entries: deleting Windows left a stale "Boot0000* Windows Boot Manager"
  in `BootOrder` 0002,0000,0003,0001,0004,0005. The owner removed it the same morning
  with `sudo efibootmgr -b 0000 -B`; `BootOrder` is now 0002,0003,0001,0004,0005.
- Secure Boot is disabled (`mokutil --sb-state`).
- No speaker fix is active on Ubuntu (`docs/hardware/AUDIO.md` §2).

The preconditions, as they stood:

- anything the owner needs from Windows is copied off: the owner's own check;
- the S0 speaker experiment: not run before W1. The fault's trigger went with Windows,
  and W5's test replaces it;
- BIOS updates without Windows: ASUS publishes EZ Flash files for this model and LVFS
  has none (`docs/INSTALL.md` §11, checked 2026-09-29). Whether this unit's setup
  screen shows the EZ Flash item is still to be checked on the laptop;
- the backups of `docs/INSTALL.md` §2: not checked here; they are taken fresh before S4
  anyway.

Steps:

| Step | Work | Size | Status |
|---|---|---|---|
| W1 | Delete `nvme0n1p2` (Microsoft reserved) and `p3` (Windows). Delete `EFI/Microsoft/` from the ESP and the "Windows Boot Manager" entry, found by its label (`docs/INSTALL.md` §2). | S | Done 2026-09-29 by the owner, including the stale entry; the §2 check confirms it again before S4 |
| W2 | Use the space: S4 installs Apex there, and Ubuntu stays as the fallback and builder host until Apex has passed its two weeks. W came before S4, so the plan for a second LUKS2 volume after S4 is dropped. | S–M | Planned in S4 |
| W3 | Optional, an owner decision: Secure Boot. A third key (the Apex Secure Boot key, RSA-2048, private in the builder VM with an offline backup), one `mokutil --import` and MokManager enrolment, an `sbsign` step for `vmlinuz` in the pair lane, and the karg `lockdown=integrity`. Modules stay verified by the per-build key built into each kernel, so `mokutil --trust-mok` is not needed. Secure Boot goes on only when both deployments carry signed kernels. The break-glass image then boots without NVIDIA, because the Fedora kernel does not trust the per-build key. | M | Optional, not started. Windows no longer blocks it; it waits for the owner and for signed kernels in both deployments |
| W4 | Remove what Windows needed: ACCEPTANCE rows 2.6 and 2.7; the Windows parts of `docs/INSTALL.md` (RTC in UTC, the BitLocker key, the Windows boot manager) and of `docs/RECOVERY.md` §5; the Windows sentences in `80-apex.preset`; ADR 0010's shared-ESP clause (a dated status line). Enable `bootloader-update.service` (ARCHITECTURE §5.5); the ESP backups of `docs/INSTALL.md` §2 and §9 stay the way back from a bad bootloader update. | S | Done 2026-09-29 in the repository; the service runs from the first image built with it |
| W5 | Audio. The owner runs `docs/hardware/AUDIO.md` §2 on Ubuntu: the speakers with no fix after a cold boot, a warm reboot from Linux, s2idle and a runtime resume, and the headset mic. All pass: delete the speaker drop-in (never built), the patch-firmware path (ADR 0004 superseded), the audio code still left from review §4, the Containerfile's audio step and `degraded=audio`. Any fails: the `model=` experiment (AUDIO.md §3). The headset-mic item (pin 0x19) stays. | S | Waits on the owner's test |

- **Exit:**
  - `efibootmgr` lists no Windows entry (met 2026-09-29), and the firmware
    boots Apex first (open until S4);
  - `bootloader-update.service` is enabled, and one boot after it ran is green (open
    until an image with it boots);
  - the speaker rows pass after a cold boot with the fix state W5 chose (open, waits on
    AUDIO.md §2);
  - no runbook step in `docs/` needs Windows (met; what still names Windows is record:
    ADR status lines, `docs/reviews/`, AUDIO.md §1, and the audio tools W5 deletes);
  - with W3: `mokutil --sb-state` reports enabled, the booted and rollback deployments
    both boot, NVIDIA loads, `amd-s2idle test` runs under lockdown, and
    `docs/RECOVERY.md` has the `mokutil --mokx` runbook.

## S5: Apex Symbolic glyphs (optional, two weeks, about June 2027, L)

- Only if the owner confirms it (answer 11, default: Colloid now, S5 optional).
- About 40 symbolic icons visible on mockup surfaces: the top bar, Quick Settings, the
  Files and Settings sidebars, and header-bar buttons.
- Redrawn on the 16 px grid from the free Hugeicons stroke-rounded set
  (`@hugeicons/core-free-icons`, MIT, notice kept), in the `Apex` icon theme. A glyph
  that exists only in Hugeicons Pro stays Adwaita.
- **Exit:** the glyph set passes an icon-resolution check, and the owner approves the
  contact sheet.

## S6: Fedora 46 and GNOME 52 (weeks 31–34, May 3 – May 28, 2027, L)

The port waits for S4. Fedora 45 is supported to 2027-11-24 and stays on GNOME 51, so
porting after 52.0 saves a second rebase against the betas. From the F46 branch point
(about 2027-02-09), the builder VM runs an unattended `FEDORA=46` compose that publishes
nothing and reports what breaks.

- A `next` lane: `FEDORA=46`, the fedora-bootc:46 digest, images tagged `apex:46`.
- Rebase the gnome-shell series (0001 to 0017, the dock hooks, 0003-blur), libadwaita,
  gnome-control-center and nautilus onto GNOME 52. Fix the selector drift the goldens
  flag. Re-approve changed goldens.
- The kernel pair on F46: the COPR's fedora-46 chroot and negativo17's fedora-46
  repository.
- `apexctl major-upgrade` (polkit):
  1. `ostree admin pin` on the current deployment;
  2. a read-only btrfs snapshot of the `/var` subvolume;
  3. `bootc switch --download-only` to `apex:46`;
  4. apply at the next restart, with the boot counter armed.
- F45 images carry a label naming `apex:46`. `Update1` exposes it. The Settings Updates
  page shows "Apex 46 is available" once the CLI has worked once.
- **Exit:**
  - `apex:46` passes G1, G2, G4 and hardware acceptance;
  - the laptop upgrades with one confirmation, and the pinned F45 entry still boots;
  - the budgets held (ADR 0014: at most 450 hook lines in at most 33 upstream files, of
    which the plan uses 31; at most 300 C lines), and the GNOME port took 8 owner-days
    or less.

## Where the SPEC §8 items land

Answer 26 builds these now. Items that another decision settles keep that decision's
default and are not built: app-chrome greys (4), radius 14 (5), the power-off
confirmation (8), the app set without Mail (10), glyphs (11), the name "Apex" (19), no
rows in stock panels (27). The privacy indicators in the status pill stay.

| Item | Slice | Size |
|---|---|---|
| Boot bar with radius 2 (Plymouth script theme, own LUKS prompt) | S1d | M |
| Terminal accent caret | S1b | S |
| Dock: lift, order, 40 px separator, full-colour Show Apps | S2a (own dock) | L |
| Workspace dots | S2a | S |
| Hot corner 4×4 | S2a | S |
| Status pill (privacy indicators kept) | S2a | S |
| Saturation on dynamic glass | S2b | M |
| Radius changes in open windows (libadwaita) | S2c | M |
| Files item-count bar (nautilus 0002) | S2d | M |
| Files 72 px zoom (nautilus 0003) | S2d | S |
| Spotlight sections and caps | S3a | L |
| Thumbnails 150×94 from two workspaces | S3a | S |
| Overview: always-visible titles, no workspace background cards | S3a | S |
| Overview and launcher scrims that blur the desktop with its windows | S3a | M |
| Launcher search pill | S3a | M |
| Lock: single stage, date above time, unlock hint | S3b | M |
| Lock blur σ 30 with saturation 1.3 | S3b | S |
| Lock field blur | S3b | S |
| Lock initial-letter avatar | S3b | S |
| Lock "Enter Password" | S3b | S |
| Notifications: icon column, flat list, Clear, footer | S3c | M |
| Power Mode lit at Balanced | S3c | S |
| Quick Settings: VPN after Airplane Mode; On/Off subtitles | S3c | S |
| Motion easing on stock animations | S3c | M |
| Two-layer shadows | S3c | S–M |

## Kernel and NVIDIA items

ADR 0015's rollout numbers the kernel steps K0 to K7 and the Ubuntu baseline N0. N1 to
N12 are this roadmap's numbers for the NVIDIA work in ADR 0015 §2 to §7. They land
here:

| Item | Slice |
|---|---|
| K0 records, deletions and ADR status lines | S0 apply |
| K1 spike | S1a–S1b, in parallel |
| K2 pair lane, image integration, kargs | S1c |
| K3 A/B against the Fedora kernel | S1d |
| K4 pair as default on the internal disk; status views | S4 (break-glass built in S1c) |
| K5 ALC294 quirk as a kernel patch | hardware track, only if the `model=` drop-in fails |
| K6 Secure Boot | W3 |
| K7 key-expiry checks, retention, build-time report | from S1c, continuous |
| N0 Ubuntu baseline and S0ix runs | S0 |
| N1 persistent MOK | replaced by the per-build key; a key for Secure Boot only in W3 |
| N2 kmod build | S1c, inside the pair job |
| N3 userspace mirror and guards | S1c |
| N4 system files and `nvidia.sh` | S1c |
| N5 ACCEPTANCE §4 on the laptop | S1d |
| N6 source artifact | S1d, before the first public push |
| N7 pair lock and holds | S1c |
| N8 driver-bump procedure | S1d; its exit is the first real bump |
| N9 Flatpak GL.nvidia sync | S1d |
| N10 s2idle, powerd and wake measurements | S4 |
| N11 Secure Boot runbook | W3 |
| N12 NVIDIA on F46 | S6 |

## Hardware track (parallel)

| When | Item | Exit |
|---|---|---|
| S0 | Speakers, on Ubuntu, with no fix loaded (Windows is gone, so its warm-reboot fault cannot recur): a cold boot, a warm reboot from Linux, s2idle, and a runtime resume (sound that starts after more than 1 s of silence, `power_save=1`); the headset mic (`docs/hardware/AUDIO.md` §2). All pass: W5. Any fails: try `options snd-hda-intel model=1043:10d3,1043:10d3`, then `1043:194e`, then `1043:1b11` (AUDIO.md §3). Each value is given twice because the HDMI controller probes first. | the rows of AUDIO.md §2.3 recorded in §2.4; with an alias, `picked fixup … for alias SSID` in the kernel log and the same rows passing |
| S1d | Only if S0 failed a row and an alias won: ship it as one line in `/usr/lib/modprobe.d/apex-audio.conf`, checked again on the CachyOS kernel. If the speakers failed and no alias passes: the patch firmware (ADR 0004) with COEFs measured in the failing state (AUDIO.md §4 to §6). If S0 passed every row: nothing ships, and W5 deletes the audio code. | the rows of AUDIO.md §2.3 on Apex |
| S1–S2 | If an alias won: send upstream a one-line `SND_PCI_QUIRK(0x1043, 0x1ab2, …)` to the working fixup, against tiwai/sound for-next, with the owner's Tested-by. If the drop-in fails its rows, carry it as an Apex kernel patch made against the CachyOS tag tree (K5). | patch posted; link in `docs/hardware/AUDIO.md` |
| S0 | Fingerprint, on Ubuntu: build filip-rs/libfprint `elanpress` at a pinned commit and run the genuine and impostor score test (FINGERPRINT.md §5). Never lower the threshold. | a recorded verdict |
| S2c–S4 | Pass: elanpress through the lane (`on_fail=degrade`) in S2c, and unlock-only PAM in S4. Fail: Fedora's stock libfprint and no PAM; effort goes upstream (!530). | ACCEPTANCE 6.5 |
| S0, S1d, S4 | s2idle: `amd-s2idle test` (`python-amd-debug-tools`); `last_hw_sleep` at least 90 % of a 30-minute lid-closed sleep; overnight drain at most 1 %/h; dGPU D3cold before and 60 s after resume; 20 lid cycles all wake. S0 on Ubuntu, S1d as K3 on both kernels, S4 during daily use. Fix only what fails. | ACCEPTANCE rows |
| S1c–S1d | dGPU: NVIDIA open modules with RTD3 (ADR 0015). One `module_blacklist=nouveau,nova_core` karg; the udev rule matches vendor `0x10de` display and audio classes. | ACCEPTANCE §4 |
| S4 | OLED: A/B PSR (`amdgpu.dcfeaturemask=0x8`) and 60 Hz on battery. Idle power in light against dark style. sRGB content on the P3 panel with mutter 51 colour management. | numbers recorded |
| S4 | Acceptance additions: amd-pstate-epp active and EPP writable on the pair; brightness and keyboard-backlight Fn keys; headset mic; webcam in Snapshot; external display. | one line each |

## Optional, owner-triggered

Each is independent and starts only when the owner asks.

- W3, Secure Boot (M). Windows no longer blocks it; it waits for a signed kernel in
  both deployments (the pair lane's `sbsign` step).
- Caps Lock as a one-key input toggle (`grp:caps_toggle`; Shift+Caps keeps Caps Lock)
  (S).
- Building the kernel from the signed CachyOS tag without waiting for the COPR, if the
  72 h limit trips often (M).
- A PipeWire filter-chain EQ for the internal speakers (M).
- A Rust DialPad daemon (M).
- The Rust IBus Vietnamese engine with automatic restore of English words (L).
- After S3b, spec-only rebuilds for the legacy allowlist, such as gdm `--without x11`
  (S each).

## Not planned

- A standalone Updates app. Updates live in Settings > System.
- A Tweaks page or app. Settings > Apex Desktop is the one home.
- Shell extensions shipped by Apex, and Dash to Dock. Extensions the owner installs are
  unsupported against the changed shell internals.
- Kernel modules built on the laptop: no akmods, DKMS or kernel-devel in the image.
- The CachyOS `-lto`, `-rt`, `-server` and `-lts` kernels, and Apex tuning of the
  CachyOS config.
- supergfxctl or a MUX switch: this model has none. Compositing on the dGPU.
- Restyling GTK3 and X11 windows.
- An installer ISO.
- A second image repository, a release environment, or testing-to-stable promotion.
- More GitHub workflows while the repository is private. GitHub runs `ci.yml`; packages
  and images build and publish from the builder VM.
- Issues opened by the build. A hold shows in `apexctl status` and the Settings Updates
  page.
- A patch-line counter in CI. The ADR 0014 patch budget is checked in review.

## Schedule risks

| Risk | Where it shows | Response |
|---|---|---|
| The third-party kernel does not compose cleanly (the `kernel` Provides, the COPR `%posttrans`, dracut order, `nvidia-boot-update`) | K1 | `kernel-spec.patch` and the lint; the fallback in S1c |
| NVIDIA 615 does not build on Linux 7.3 before 7.2 goes EOL | K1, October | the pair holds; S1d can start with `degraded=nvidia` or the Fedora-kernel fallback |
| A kernel job does not fit the laptop's 14.5 GiB next to the owner's work | K1 | `-j6`, night runs on AC, or a 10 GiB builder VM for kernel jobs only |
| Glass misses its frame budget on the Vega 7 | S2b, before the remaining surfaces exist | the three levers, in order; Reduce Transparency is always there |
| The own dock regresses (intellihide, drag and drop, external display) | S2a | G2 scripted tests and goldens |
| A GNOME point release breaks a hook while a slice is running | any week | hold, then rebase within 72 h (security) or 14 days |
| The unlock path breaks | S3b | per-hook stock fallback, the G4 matrix, `loginctl unlock-session` |
| Standing work grows past 2 days a month | from S1d | the owner cuts scope in S3c or later, or moves S4 earlier |
