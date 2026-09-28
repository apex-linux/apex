# ADR 0006: Fix the ELAN 04f3:0c6e by rebuilding Fedora's libfprint with bounded quirk patches

Status: accepted (2026-09-24, revised after design review)

## Context

libfprint's `elan` driver treats any pre-scan status other than 0x55 as a protocol
error. The retry for the transient answers 0x00 and 0xaf is gated to 0x0c58, and it has
no bound: a sensor that answers at once would poll at 100 Hz forever. The upstream
generalisation (MR !655) is open. This laptop's journal shows the protocol error four
times.

The sensor is a press sensor in the power key, but the driver stitches its frames as if
the finger were swiped. Match quality is therefore unmeasured: other units report
genuine scores of 0–19 against a threshold of 24.

## Decision

- **Build.** `libfprint.yml` rebuilds the libfprint SRPM that Fedora currently ships,
  from the same repositories as the compose. It first verifies the SRPM signature with
  `rpmkeys -K` and fails on anything but OK. It applies the patches listed in
  `packaging/libfprint/series`, sets the release suffix `.apex1`, and publishes the
  result as an OCI artifact.
- **Patch 0001:** a quirk bit for 0x0c6e in the transient-retry mask.
- **Patch 0002:** a bounded retry with lift semantics. A transient status after at
  least one frame means the finger was lifted, so the capture completes. With zero
  frames the driver backs off 10, 50 and then 200 ms within the command timeout, then
  takes the timeout path.
- **Not in `series`:** the dark-frame and settle-delay patches, until a debug log shows
  their trigger.
- **A patch fails to apply:** ship Fedora's stock libfprint, label the image
  `degraded=fingerprint` and open an issue. Never block OS updates.
- **Not in PAM at M1.** After the genuine and impostor acceptance test passes, enable
  it for screen unlock only, through an Apex authselect vendor profile whose
  `system-auth` never includes `pam_fprintd`.
- **Power key:** `power-button-action='interactive'`.

## Consequences

- **Privacy.** Diagnostics run only in a tmpfs directory. Raw frames, `.pgm` images,
  templates and umockdev recordings never enter the repository, and a CI guard rejects
  them.
