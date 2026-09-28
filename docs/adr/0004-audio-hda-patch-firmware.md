# ADR 0004: ALC294 speaker fix through measured HDA patch firmware, then an upstream quirk

Status: accepted (2026-09-24, revised after design review); amended by ADR 0015 (2026-09-28): a
`model=` alias is tried first (ARCHITECTURE §6.2), and a kernel quirk ships through the
kernel pair lane only if the alias fails

## Context

No kernel tree has a quirk for SSID `1043:1ab2`, the pin tables do not match, and there
is no smart amplifier. The community workaround decodes to COEF 0x1b = 0x7f4b and COEF
0x0f = 0x7774 on NID 0x20. That result is **confounded**: the procedure ends with a full
power-off, which on its own resets the codec.

Related ASUS ALC294 bugs point at COEF 0x1b bit 10 being left cleared by the Windows
driver, but that hypothesis is unverified for this model. Writing the whole value 0x4e4b
broke cold boot on the UX461FN.

Fedora and Ubuntu kernels enable `CONFIG_SND_HDA_PATCH_LOADER`. The HDA core replays
`[verb]` lines at probe and on every runtime and system resume, before `alc_init`.

## Decision

1. **Measure first.** `hardware/m7400qc/audio/coef-dump.sh` (sudo, `hda-verb`) records
   COEFs 0x0f, 0x1b and 0x40:
   - A: after a cold boot;
   - B: after a warm reboot from Windows;
   - C: with the fix loaded;
   - D: after suspend with the fix;
   - E: after a cold boot with the fix.

   The dump runs on the current Ubuntu install of this laptop before Apex exists.
2. Record the cold values in `hardware/m7400qc/profile.toml`. The rendered `[verb]`
   writes `cold(0x1b) | 0x0400`. COEF 0x0f is written only if dumps A and B differ
   there.
3. `apexctl profile render` refuses to render without measured values. Until they exist,
   the image ships no audio fix and carries the label `degraded=audio`.
4. Ship `/usr/lib/firmware/apex/alc294-m7400qc.fw` with
   `options snd-hda-intel patch=` and four identical entries (slots follow probe order).
   The file has no `[model]` or `[pincfg]` lines, so it coexists with a future upstream
   quirk.
5. The kernel quirk `ALC294_FIXUP_ASUS_COEF_1B_BIT10` (a read-modify-write of bit 10,
   chained to `ALC294_FIXUP_ASUS_HPE`) is sent upstream with the measured values and a
   Tested-by.
6. A CI canary opens an issue when Fedora's module contains the SSID. The firmware file
   is removed by hand, after the hardware test passes without it.

## Consequences

- The stock Fedora kernel gets working audio without a rebuild, once the values are
  measured.
- Failures of the patch loader are silent in the kernel log. A reported (non-rollback)
  health check therefore verifies `init_verbs` on the ALC294 hwdep.

## Alternatives rejected

- **A systemd unit running `hda-verb`.** It races codec probe and is lost on runtime
  suspend.
- **Whole-value writes from another laptop's quirk.** The bits may differ on this unit.
- **The 0x7f4b workaround value.** It sets undocumented bits, and the evidence for it is
  confounded.
