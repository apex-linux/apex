# ADR 0009: Apex boot assessment replaces greenboot-rs

Status: accepted (2026-09-24); amended 2026-09-28: `panic=10` only, the initramfs keeps
dracut's rescue shell

## Context

greenboot-rs 0.16.4, the health-check framework in Fedora 45, was read at source level.
Four problems make it unsuitable here:

1. **It rolls back when nothing was applied.** Its rollback trigger arms for any staged
   deployment, including a locked download-only one. An ordinary reboot then runs
   `bootc rollback`, so the default silently moves back one version.
2. **It reboots inside a user session.** Any failed check triggers `systemctl reboot`,
   whether or not a user is logged in.
3. **It misses early failures.** Boot counting starts only after the first failed check
   in userspace, so a panic or initramfs failure in a new deployment is never rolled
   back.
4. **Its default checks turn network conditions into rollbacks** (the DNS and repository
   checks).

## Decision

Apex ships `apex-boot-assess` (crate `apex-boot`). It keeps the proven mechanism (GRUB
environment variables, a static GRUB snippet, `bootc rollback`) under Apex-owned names
and changes the policy.

- **Arming (only by `Apply`).** `apex_target=<digest> apex_counter=3 apex_ok=0`.
  - The names are Apex-owned. Fedora's `grub2-set-bootflag` and
    `grub-boot-success.timer` set `boot_success=1` after a login, which would mark a
    failed armed boot as good.
  - The precondition is that the booted deployment comes from an image and a different
    image is staged. After finalization ostree makes the staged deployment entry 0 and
    keeps the booted one as entry 1, so entry 1 is a real deployment, never the
    firmware-setup entry.
  - `/boot` is read-only on bootc systems, so writes run `grub2-editenv` in a private
    mount namespace in which `/boot` has been remounted read-write.
- **GRUB snippet** `08_apex-bootcount.cfg` (bootupd static config):
  - when `apex_target` is set, `apex_ok` is not 1 and `apex_counter` is 3, 2 or 1,
    decrement the counter, set `fallback=1` and boot the default;
  - when the counter is 0 or out of range, store -1 and set `default=1` (the previous
    deployment);
  - set and save `apex_ok=0` at every boot, after the counting, so userspace has to
    confirm each boot again.
- **Kernel arguments** (`/usr/lib/bootc/kargs.d`): `panic=10`. A kernel panic reboots,
  and the counter moves. An initramfs failure waits at the dracut rescue shell until a
  forced power-off, which also moves the counter.
- **Required checks,** each with a 30 s timeout:
  - a greeter or user session has been active for at least 20 s;
  - NetworkManager and systemd-logind are active;
  - `apex-updated` answers `Ping`;
  - none of an explicit list of units has failed;
  - `/boot/grub2/grub.cfg` contains the Apex snippet marker.
- **Reported checks** (never a rollback): audio `init_verbs`, charge threshold, dGPU
  runtime PM, the fingerprint device, the image-source check (booted image is a registry
  transport, the expected repository, and verified by policy), and `grub-cfg-current`
  (the installed snippet is the current version).

The decision table is a pure function of the grubenv values, the booted digest, the boot
order reported by `bootc status` (which deployment is the default), the check results and
whether a user may be logged in. When logind cannot answer, Apex assumes a user may be
logged in and never reboots.

| Situation | Decision | Action |
|---|---|---|
| All required checks green | Green | armed: `apex_ok=1`, unset `apex_target` and `apex_counter`, clear the intent; not armed: unset a stray `apex_counter` if there is one, otherwise write nothing |
| Red, armed, booted = target, nobody logged in, GRUB counted this boot | RedArmedNoSession | `apex_ok=0`, report `red`, `systemctl reboot` so the counter moves |
| Red, armed, booted = target, a user may be logged in (or a reboot would not make progress) | RedArmedSession | no reboot; publish `HealthFailure`; the user chooses "Roll back" |
| Red, not armed | RedUnarmed | report only |
| Armed, booted ≠ target, counter exhausted (GRUB fell back) | Fallback | write the hedge `apex_counter=3` first, then `ReportBoot("fallback")`; the daemon runs `bootc rollback`, denylists the target and disarms before replying; on a lost reply the assessment re-reads `bootc status` and keeps the hedge unless the rollback happened |
| Armed and counted, booted ≠ target, target may still be the default (`fallback=1` or a manual menu pick) | TargetSkipped | keep the arming so GRUB goes on counting the target; write the hedge only when the counter is 0 and the boot order is unknown; report this boot as ordinary |
| Armed, but the target is certainly not the default, GRUB does not count, or the target runs while another deployment is the default | Inconsistent | clear the arming; report this boot as ordinary |

Rows in which the booted digest differs from the target are evaluated first, because they
describe which deployment is actually running. A counter still at 3 with booted ≠ target
means Apply armed during this boot, after GRUB ran; that arming is left untouched.

**Arming precondition** (enforced by `apex_boot::check_arming` in `Apply`):
- the booted deployment comes from an image;
- a different image is staged;
- the booted deployment is not itself armed or recorded as failed.

Finalization keeps only the new deployment and the booted one. Arming on top of an
unconfirmed deployment would make it the only fallback, with the last good one pruned.

**Qualification hook.** A root-owned `/var/lib/apex/force-red` naming the booted digest
adds a failing required check `forced-red`, so the KVM qualification can drive the whole
counted-rollback path. When the file is absent or names another digest, nothing changes.

## Consequences

- **Early-boot failures.** A failure that drops the real root into `emergency.target`
  (after switch-root) does not reboot by itself. Drop-ins for `emergency.service` and
  `rescue.service` reboot after a short delay while an armed boot is being counted, so
  the counter still moves.
- **Boot counting follows the static config installed at `bootc install`.** bootupd does
  not regenerate it later, so the marker check makes a missing snippet visible, and
  `apexctl boot repair-grub` (M2) can reinstall it.
- **Upstream contribution.** The download-only fix is reported to greenboot-rs upstream.
  Apex does not depend on it.
- **Testing.** Every row of the decision table is tested in unit tests and in a boot
  simulation. The KVM qualification covers a fresh install, a download-only stage that
  survives a reboot, and an injected red check (the `force-red` hook) that leads to a
  counted rollback. A panicking-image scenario is still open.
