# ADR 0008: Updates download in the background; the user decides when to reboot

Status: accepted (2026-09-24, revised after design review)

## Context

The stock `bootc-fetch-apply-updates.timer` runs `bootc upgrade --apply`, which reboots.
bootc 1.16 supports `--check`, `--download-only`, `--from-downloaded`,
`--soft-reboot` and `switch`. It has no D-Bus API. Staged deployments that are only
downloaded are locked, and a reboot discards them.

## Decision

- **The stock timer is masked.** `apex-updated` is the only component that runs bootc,
  and every operation goes through one queue. bootc runs with a cleared environment and
  a strict `CONTAINERS_POLICY_JSON`.
- **State.** It is rebuilt from `bootc status` on start and on every
  `bootc-status-updated.target`. Only intent, a denylist of bad digests, and the last
  check are persisted.
- **Automatic runs** check, then download only when the gates pass. The gates are power,
  metered network, `/sysroot` and `/boot` space, the denylist, the bootc flags and a
  newer version. Nothing automatic runs while a user intent exists.
- **`Apply(expected_digest)`** verifies:
  - the staged digest and that it is download-only;
  - the version, read from the staged deployment's manifest;
  - the space gates.

  It then arms the boot counter and unlocks the stage for the next boot. It never
  reboots: the user's session calls `org.gnome.SessionManager.Reboot`.
- **Cancel** re-locks the stage. It never calls `bootc rollback`.
- **Rollback, channel switch and downgrade** are explicit polkit-authenticated actions.
- **Soft reboot and automated major upgrades are deferred.** Major upgrades follow a
  manual runbook until Fedora 46 branches.

## Consequences

- The laptop never reboots on its own. The one exception is an armed boot that fails its
  health checks while nobody is logged in (ADR 0009).
- What gets applied is exactly the digest the user reviewed.
- After a downloaded stage is lost at reboot, the next automatic run stages it again,
  which is fast because the image is cached.
