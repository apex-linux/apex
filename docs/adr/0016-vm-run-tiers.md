# ADR 0016: VM runs confirm, they don't discover

Status: accepted (2026-10-30). It amends ARCHITECTURE §4 (`vm.yml`) and §11 (when G4
runs). Train `r18` brought it to apex-image's `main` (2026-10-30, d5f8d79): G4 first,
the qualify-only tier, `vm.yml`'s paths and summary, `ci-build`'s plan words. The new
`ci-build` is live once the owner runs `just vm-ci-install`. The signed-RPM cache moves
to `train/r20`, and the hosted tier and the keeper need the owner's decisions below.

## Context

`vm.yml` builds on one self-hosted runner, on the owner's laptop. Between the runner's
first job (2026-10-26 13:04 UTC) and 2026-10-30 14:20 UTC, 97.3 hours passed:

- The runner executed jobs for 22.2 hours. For 62.9 hours, work sat queued with no
  runner online.
- Runs 1 to 16 gave 11 verdicts, none green. The other 16 runs gave no verdict.
- A run took 110 minutes at the median. G2 ran first, for 62 to 70 minutes, and passed
  6 times out of 6. G4 started 78 to 96 minutes in and failed 6 times out of 6.
- G4 stops at its first failing row, so each run showed one G4 bug.
- A fix to the G4 harness alone still paid for a full rebuild and G2.
- `vm.yml`'s push paths missed `.github/scripts`. Harness fixes therefore needed manual
  dispatches, while a push that changed only `tools/runner` queued a pure replay.

The laptop was used to discover bugs one at a time, at about two hours each, and other
work waited behind it.

## Decision

A VM run confirms what cheaper tiers have already checked. Four tiers:

| Tier | Where | What it runs | Records or promotes |
|---|---|---|---|
| T1 | GitHub-hosted, every PR | each repository's `ci.yml`, plus apex-image's parity contracts: the QEMU flags, the user units, G4's markers checked against real-guest fixtures, and the provenance of the built image | no |
| T2 qualify-only | the builder VM, advisory | `qualify.sh local` on the image already built, then `qualify.sh local-diag` after a failure. No RPMs, lane, image build or G2 | never |
| T3 gate run | the builder VM | the full chain: components, RPMs, lane, image, G4 when due, G2 twice, the gates record, promotion | the only tier that does |
| T4 hosted VM preflight | GitHub-hosted with KVM | an advisory boot of the image on a hosted runner | no; experimental, owner-gated |

Rules:

- **T3 runs G4 first.** G4 runs before G2, and both always run, so one run reports both
  verdicts. The verdict is: G2 passed, and G4 passed or was not due. G4 writes its key
  to `_build/qualify/g4-pending.txt`. Only the gates record moves it to
  `_build/g4-passed.txt`, after G2 passed and the lane lock was unchanged; otherwise it
  is deleted. A G4 pass is therefore never recorded for an image whose G2 failed.
- **A G4 failure is diagnosed in the same run.** After a G4 failure, `local-diag`
  installs a fresh guest, logs in through the greeter, and runs each G4 unit after the
  login on its own. It reports every unit in `diag.md` and does not change the verdict.
- **T2 never records.** It writes neither the gates record nor the real G4 record, and
  never promotes. A T2 job ends as a non-success with a notice, so a green `vm.yml`
  always means a gates record. T2 runs only when all of these hold:
  1. Every file changed since the image's revision is a harness file.
  2. The last verdict for this image ID is a G4 failure, with components pinned.
  3. The harness digest differs from the one that failed.
  4. The image is under 72 hours old.
  5. The working tree is clean.

  The checks are one function, and any doubt means T3. A committed file switches T2
  on, so a one-line revert turns it off.
- **The harness has its own digest.** It is the sha256 of `qualify.sh`, `lib.sh` and
  `qualify-allowed-failures.txt`. G4's key gains a `harness` line, so a harness change
  makes G4 due once.
- **Only paths that change the image or the gates queue a run.** These are
  `components.lock`, `image/**`, the lane and its Cargo files, `tools/components.sh`,
  the build scripts of `tools/builder-vm`, and `qualify.sh`, its allowed failures,
  `image.sh`, `oci-artifact.sh`, `ci-host.sh` and `lib.sh`. `tools/runner/**`,
  `ci-build.sh` (live only after the owner installs it) and documentation queue nothing.
  A selftest check (`vm-paths-check.sh`, apex-image#146) walks every file the build
  and the gates source, run or read, starting from `vm.yml`'s steps. It fails on a file
  that no path covers, unless an exact allow line gives the reason. The first walk found
  `oci-artifact.sh` and `ci-host.sh` missing.
- **The daily run asks first.** A hosted `daily-due` job with only `actions: read`
  decides whether the scheduled run builds (apex-image#140). It skips, with a notice,
  when another `vm.yml` run is queued, waiting, pending or in progress. It also skips
  when `main`'s head had a build in the last 20 hours that gave a verdict: it passed, or
  it failed after G2 or G4 ran, which its step "A gate gave its verdict" records. A lost
  runner, a refusal or a failed lookup builds.
- **Trains.** PRs that touch those paths merge into an integration branch,
  `train/rNN`. The lead merges the train to `main` as one push, which queues one T3
  run. No such PR merges to `main` on its own.
- **Plans are fixed words.** `ci-build <sha> [daily|next|gate|g4]`:
  - empty means auto;
  - `daily` and `gate` force T3, and `gate` also forces G4 due;
  - `g4` forces T2 and refuses when T2's conditions fail.

  `ci-build` checks that the build honoured the word it was given, and refuses the run
  otherwise. Only auto, `daily` and `gate` may promote.
- **The summary reports stages.** The job summary reads `ci-build`'s own lines, not
  files the build left behind. It gives a timing table per stage and the furthest G4
  row reached. The failing G2 cases' logs and the diagnosis join the run's logs, and
  no private key from the guest does.
- **Signed RPMs are reused by content key** (`train/r20`). Each component's RPMs are
  cached under their own content key after signing. Before reuse, the cache is checked
  against `SHA256SUMS` and the Apex RPM key, and any mismatch rebuilds.
- **Nothing is weakened.** G2 still runs twice with the full case set and the 300 s
  glass stress in every T3. Promotion still needs G2 and G4 on the same image ID with
  the lane lock unchanged.

## Waiting for the owner

- **T4.** A spike on a standard hosted runner (apex-image#127, a draft that never
  merges) found `/dev/kvm` writable. Stock `fedora-bootc:45` booted 3 times out of 3,
  installing in 0.75 to 1.3 minutes and booting in about 0.4 minutes. T4 needs a
  hosted test-key mode for G1 that fails closed, and that changes THREAT-MODEL T3.
- **The keeper** (apex-image#129, held, off unless `vars.APEX_VM_KEEPER` is `on`). It
  is an hourly hosted workflow. It re-dispatches `vm.yml` after a run that gave no
  verdict, never replays a known verdict, and keeps a "VM status" issue. It needs
  `actions: write` on apex-image, which changes THREAT-MODEL T3.
- **Builder-VM autostart** (apex-image#128, opt-in). `runner.sh install --autostart`
  starts the builder VM with the runner, takes jobs only on AC power, and warns before
  a power-off in the middle of a job.

## Consequences

- A fix to the harness alone costs one G4 pass on the image already built, without
  the rebuild and G2's 62 to 70 minutes.
- A T3 run that fails G4 still reports G2, and reports every G4 unit after the login.
- The laptop's queue holds one run per train, not one per merge.
- The record invariant now lives in two places, `build-image.sh` and `qualify.sh`.
  `just vm-qualify` still records a G4 pass with no G2, as before. That is a manual
  step, outside `vm.yml`.
