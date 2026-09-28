# Audio: Realtek ALC294 speakers on the M7400QC

Decision: [ADR 0004](../adr/0004-audio-hda-patch-firmware.md). Architecture:
[§6.2](../ARCHITECTURE.md#62-audio-realtek-alc294-subsystem-10431ab2). Acceptance:
[ACCEPTANCE.md](ACCEPTANCE.md) §2.

The fix is an HDA patch firmware file rendered from **values measured on this laptop**.
Until `hardware/m7400qc/profile.toml` holds those measurements, `apexctl profile
render` produces no firmware file and the image carries `degraded=audio`. This page
explains why, and gives the exact procedure that produces the measurements.

Facts were checked on 2026-09-23 and 2026-09-24 against the kernel trees named below
and on this laptop (Ubuntu 26.04, kernel 7.0.0-31-generic, BIOS M7400QC.311).

## 1. Findings

### The codec

| Item | Value |
|---|---|
| Codec | Realtek ALC294, revision 0x100004 |
| `vendor_id` / `subsystem_id` | `0x10ec0294` / `0x10431ab2` (PCI SSID `1043:1ab2`) |
| Controller | `0000:04:00.6` (analog HDA). `0000:04:00.1` is the HDMI controller with codec `0x1002aa01` |
| hwdep on the Ubuntu host today | `/dev/snd/hwC1D0` (card 1, address 0). The scripts find it by vendor and subsystem, never by number |
| COEF widget | NID `0x20`, vendor-defined, 130 coefficients |
| `snd_hda_intel` | `power_save=1`: the codec runtime-suspends about 1 s after the last stream closes |

Pins, from `/sys/class/sound/hwC1D0/init_pin_configs`:

| NID | Default config | Meaning |
|---|---|---|
| 0x12 | `0x90a60130` | internal digital mic (DMIC) |
| 0x13 | `0x40000000` | unused |
| 0x14 | `0x90170110` | internal speakers, fed by DAC 0x02, EAPD capable |
| 0x15–0x1b | `0x411111f0` | not connected (includes 0x17, and 0x19, the usual ASUS headset-mic pin) |
| 0x1d | `0x40663b05` | unused |
| 0x1e, 0x1f | `0x411111f0` | not connected |
| 0x21 | `0x04211020` | headphone jack, right side |

### No quirk, no smart amplifier

- **No kernel tree has a quirk for SSID `1043:1ab2`**, and there is no M7400, M7401,
  M7600, K6400 or M3400 entry. Checked: mainline v7.3-rc4 (re-checked 2026-09-24),
  stable 7.2.7 (Fedora 45's `kernel-7.2.7-300.fc45`), linux-next next-20260922,
  `tiwai/sound.git` for-next and for-linus, longterm 6.18.53 and 6.12.111.
- The four ALC294 ASUS pin quirks (HPE, MIC and two SPK) do not match the pin table
  above either. The driver therefore applies **no fixup at all**: the kernel log has no
  `picked fixup` line, and the codec runs on generic auto-configuration.
- **There is no smart amplifier.** ACPI has no `CSC3551`, `TIAS2781` or `TXNW2781`
  device, the only I2C clients are two HID devices, and there are no SPI devices. The
  speakers are driven by the ALC294's own amplifier on pin 0x14. Every CS35L41 or
  TAS2781 fixup is wrong for this laptop.
- The headset-mic pin 0x19 is left unconfigured by the BIOS, so a TRRS headset mic
  does not work out of the box. That is a separate item and not part of this fix.

### The fault and the leading hypothesis

After a **warm reboot from Windows** the speakers are silent or crackle ("chewed tape")
until the laptop is fully powered off. A cold boot straight into Linux works.

The leading hypothesis, **not yet verified on this unit**: the Windows Realtek driver
clears bit 10 of COEF 0x1b (Realtek's default 0x4e4b becomes 0x4a4b), and the codec
keeps that state across a warm reboot. The same pattern is documented for the ASUS
UX431DA (kernel bugzilla 207553, also AMD with ALC294), UX461FN (219415) and UX333FA
(221452), and for the Intel Hades Canyon ALC700 (upstream commit 1fcccdc20a76,
2026-08-21, which restores only bit 10 at init).

### The `0x477` packing pitfall

The community workaround for this laptop (Ask Ubuntu question 1420976) runs:

```
hda-verb /dev/snd/hwC1D0 0x20 0x500 0x1b
hda-verb /dev/snd/hwC1D0 0x20 0x477 0x4a4b
hda-verb /dev/snd/hwC1D0 0x20 0x500 0xf
hda-verb /dev/snd/hwC1D0 0x20 0x477 0x74
```

`hda-verb` packs its arguments as `nid << 24 | verb << 8 | param` (alsa-tools
`HDA_VERB()`), and the kernel's hwdep ioctl splits that word again into a 16-bit verb
and an 8-bit parameter. "Set" verbs such as SET_COEF_INDEX (`0x5`) and SET_PROC_COEF
(`0x4`) are 4-bit verbs with a 16-bit payload, so any bits in the low byte of the
12-bit verb are OR-ed into the payload:

| Command line | Word sent | Codec sees | Effect |
|---|---|---|---|
| `0x20 0x500 0x1b` | `0x2005001b` | verb 5, payload `0x001b` | SET_COEF_INDEX 0x1b (as intended) |
| `0x20 0x477 0x4a4b` | `0x20047f4b` | verb 4, payload `0x7f4b` | SET_PROC_COEF **0x7f4b**, not 0x4a4b |
| `0x20 0x500 0xf` | `0x2005000f` | verb 5, payload `0x000f` | SET_COEF_INDEX 0x0f |
| `0x20 0x477 0x74` | `0x20047774` | verb 4, payload `0x7774` | SET_PROC_COEF 0x7774 (EAPD high, as in `ALC294_FIXUP_ASUS_HPE`) |
| `0x20 0x400 0x4a4b` | `0x20044a4b` | verb 4, payload `0x4a4b` | the correct way to write 0x4a4b |

So the workaround really writes COEF 0x1b = **0x7f4b**. Compared with the Realtek
default 0x4e4b, that sets bit 10 but also bits 8, 12 and 13 (`0x7f4b ^ 0x4e4b =
0x3100`), which are undocumented.

Rule: write a 4-bit verb as `0x500` or `0x400` with the whole 16-bit value in the last
argument, or use the symbolic names (`SET_COEF_INDEX`, `GET_PROC_COEF`). The kernel's
`[verb]` lines in a patch file are packed the same way (`verb << 8 | param`), so the
rule applies there too. `try-fix.sh` refuses any verb other than `0x500` and `0x400`.

### Why the community evidence is confounded

The workaround's instructions end with a **full power-off**. A power-off on its own
resets the codec, and it is the documented cure for the fault. The fact that audio
works afterwards therefore says nothing about the verbs. Worse, the verbs do not write
what their authors intended (0x7f4b, see above), and one M7400QC owner needed
`alsa force-reload` on top. None of it is evidence for a particular COEF value.

### Why measurement gates the fix

- `[verb]` lines are replayed at probe **and on every runtime and system resume**. With
  `power_save=1` that is roughly every time sound starts after a second of silence. A
  wrong bit would be forced over and over.
- Writing the whole value 0x4e4b is exactly what broke **cold boot** on the UX461FN
  (bugzilla 219415). This unit's cold value may differ from Realtek's default in other
  bits.
- COEF 0x0f and 0x40 may or may not matter here. They are written only if the
  after-Windows dump shows they differ.

So the renderer writes `cold_value | 0x0400` for COEF 0x1b (profile.toml
`[audio.fix].rules`), plus the cold values of any index in `restore_if_windows_differs`
that changed after Windows, and nothing without a measured cold value.

## 2. How the fix works

- `hardware/m7400qc/generated/alc294-m7400qc.fw` has a `[codec]` line
  `0x10ec0294 0x10431ab2 0` and `[verb]` lines on NID 0x20. It has no `[model]` or
  `[pincfg]`, so it coexists with a future kernel quirk.
- `hardware/m7400qc/generated/apex-audio.conf` sets
  `options snd-hda-intel patch=apex/alc294-m7400qc.fw` with four identical entries,
  because patch slots follow controller probe order, not PCI address.
- At probe, `snd-hda-intel` logs `Applying patch firmware 'apex/alc294-m7400qc.fw'`,
  loads the file and stores the `[verb]` lines in the codec's `init_verbs`. The HDA
  core replays them before the Realtek init code, at probe and at every resume.
- **Failures are silent.** A missing file only logs
  `Cannot load firmware, continue without patching`; a line the parser does not like is
  skipped without a message, and a line longer than 127 bytes makes the loader drop the
  rest of the file. The only reliable check is `/sys/class/sound/hwC*D0/init_verbs` on
  the ALC294 hwdep. The renderer writes the `[verb]` lines in exactly the format the
  kernel prints there (`0x20 0x500 0x001b`), so the two compare as text. Apex reports it
  (never as a rollback trigger) in the boot assessment and in `apexctl hw report`.
- In the image the file is `/usr/lib/firmware/apex/alc294-m7400qc.fw`. An image check
  confirms `snd-hda-intel` is not in the initramfs, where the file would be missing.

## 3. Measurement procedure (A–E)

Runs on the Ubuntu install of this laptop today, and later on Apex. You need root,
the repository checked out, and `hda-verb` (alsa-tools, already installed here).

Tools, in `hardware/m7400qc/audio/`:

- `coef-dump.sh PHASE`: reads COEFs 0x0f, 0x1b and 0x40 (add `--extra 0x2a,0x3a` for
  more), prints a summary and a TOML fragment, and saves both to
  `/var/tmp/apex-audio/PHASE-<UTC time>.txt`. It **only reads**: it never sends a
  coefficient write. It refuses to run while a stream is playing or recording on the
  card, and it refuses a phase whose fix state is wrong: A or B with the fix loaded, or
  C to E without it or with loaded `init_verbs` that are not the `[verb]` lines of
  `hardware/m7400qc/generated/alc294-m7400qc.fw`. See `coef-dump.sh --help`.
- `try-fix.sh install|revert|status`: puts the rendered fix on the host or removes it;
  `status` compares the loaded `init_verbs` with the rendered file.
- The speaker test in §3.7.

Below, `$A` is `hardware/m7400qc/audio` in your checkout.

> **Power-off means power-off.** "Shut down" in Linux or Windows, unplug the AC
> adapter, wait 30 seconds, then power on. "Restart" is a warm reboot. Windows Fast
> Startup does not matter for these steps: Restart never uses it, and phase A and E
> start from a Linux shutdown.

### 3.1 Phase A: cold boot, no fix

```sh
sudo $A/try-fix.sh status        # both files "absent", init_verbs empty
# If the fix is installed: sudo $A/try-fix.sh revert
# Shut down, unplug AC, wait 30 s, power on, boot Ubuntu (not Windows), log in.
sudo $A/coef-dump.sh A
```

Then run the speaker test (§3.7). On a cold boot the speakers should work. Write
down the result.

### 3.2 Phase B: warm reboot from Windows, no fix

1. Boot Windows (firmware boot menu: press Esc while the ASUS logo shows, then pick
   Windows Boot Manager). Log in and play sound through the speakers for 10 s.
2. Choose **Restart** and boot Ubuntu.
3. Run the speaker test (§3.7) **first** and record what you hear: silent, crackling,
   or fine.
4. `sudo $A/coef-dump.sh B`. The report compares every index with the newest A report
   and names the changed bits.

Interpretation:

| Result | Meaning | Next step |
|---|---|---|
| Speakers fail and only 0x1b differs, in bit 10 | The hypothesis holds | Record A and B, render, continue with C |
| 0x0f or 0x40 differ as well | Windows also changes those | They are already in `restore_if_windows_differs`; the renderer restores their cold values |
| Speakers fail but A and B are identical | The hypothesis is wrong for this unit | Do not ship a fix. Dump more indexes (`--extra`, or all of them, §3.8) and investigate |
| Speakers work after Windows | The fault did not reproduce | Repeat B once more (play longer in Windows). Do not render without a reproduced fault |

### 3.3 Record and render

Paste the fragments into `hardware/m7400qc/profile.toml` (§4), render, and install the
result on the host:

```sh
just render                       # or: cargo run -q -p apexctl -- profile render
sudo $A/try-fix.sh install        # validates, copies, checks the initramfs
```

### 3.4 Phase C: fix loaded, warm reboot from Windows

This is the test that matters: the fix must repair the after-Windows state **without a
power-off**.

1. Boot Windows, play sound for 10 s, **Restart** into Ubuntu.
2. `sudo $A/try-fix.sh status` lists the ALC294's `init_verbs` and says
   `match: equal to the [verb] lines of ../generated/alc294-m7400qc.fw`, and
   `sudo journalctl -k -b | grep -E 'Applying patch firmware|Cannot load firmware'`
   shows `Applying patch firmware 'apex/alc294-m7400qc.fw'` and no `Cannot load`.
3. `sudo $A/coef-dump.sh C`, then the speaker test (§3.7).

Pass: COEF 0x1b has bit 10 set (the report says `SET`), and the speaker test passes.

### 3.5 Phase D: after suspend, fix loaded

Right after C, in the same boot:

```sh
systemctl suspend                 # wake the laptop, wait 5 s
sudo $A/coef-dump.sh D
```

Then the speaker test. Pass: same values as C, speaker test passes.

### 3.6 Phase E: cold boot with the fix

Shut down, unplug AC, wait 30 s, power on into Ubuntu, then:

```sh
sudo $A/coef-dump.sh E
```

Then the speaker test. Pass: the speaker test passes (this is the UX461FN regression
check), and COEF 0x1b equals the rendered value.

### 3.7 Speaker test (bypasses PipeWire, low volume)

PipeWire and any effects chain can hide or cause artefacts, so play straight to the
ALSA device. Unplug headphones first (auto-mute would silence the speakers).

```sh
hw=$(grep -lx 0x10431ab2 /sys/class/sound/hwC*D*/subsystem_id); hw=${hw%/subsystem_id}; hw=${hw##*/}
card=${hw#hwC}; card=${card%D*}; addr=${hw##*D}; echo "ALC294 is card $card, codec $addr"
systemctl --user stop pipewire.socket pipewire-pulse.socket pipewire.service pipewire-pulse.service wireplumber.service
amixer -c "$card" sset Master 30% unmute
amixer -c "$card" sset Speaker 100% unmute
speaker-test -D "plughw:$card,0" -c 2 -r 48000 -t wav -l 1
timeout 30 speaker-test -D "plughw:$card,0" -c 2 -r 48000 -t sine -f 440
sleep 5; cat /sys/bus/hdaudio/devices/hdaudioC${card}D${addr}/power/runtime_status   # "suspended"
timeout 10 speaker-test -D "plughw:$card,0" -c 2 -r 48000 -t sine -f 440      # after a runtime resume
systemctl --user start pipewire.socket pipewire-pulse.socket wireplumber.service
```

Pass: "Front Left" from the left speaker and "Front Right" from the right; a steady
440 Hz tone for 30 s with no dropouts, crackle or rhythmic gating; the same tone again
after the codec was runtime-suspended.

### 3.8 Full dump (only for investigation)

To see all 130 coefficients, use the kernel's own dumper (it also only selects slots
and reads):

```sh
echo 1 | sudo tee /sys/module/snd_hda_codec/parameters/dump_coef
sudo grep -E '^    Coeff 0x' "/proc/asound/card$card/codec#0" > /tmp/coef-all.txt
echo -1 | sudo tee /sys/module/snd_hda_codec/parameters/dump_coef   # back to the default
```

This is also how to read COEFs on Apex, where alsa-tools is not installed.

## 4. Filling `profile.toml`

1. Replace the commented `# [audio.measurements]` block with the fragment from the
   phase-A report (the `[audio.measurements]` header, `date`, `bios`, `kernel` and
   `cold_boot`).
2. Add the `after_windows = [...]` line from the phase-B report under it. Both are
   needed: `restore_if_windows_differs` lists 0x0f and 0x40, so the renderer refuses to
   render without the phase-B dump.
3. Optionally add the `with_fix_loaded`, `with_fix_after_suspend` and
   `with_fix_cold_boot` lines from C, D and E. `apexctl` accepts these keys and checks
   them (no index twice), but they are informative and never rendered.
4. Keep `bios` and `kernel` from phase A. If phase B ran under a different BIOS, redo
   A and B under the same one.

`apexctl` parses the profile strictly: every table rejects unknown keys, so paste the
lines as printed (a typo such as `after_window` is an error, not an ignored line).
`date` must be a plain date, `bios` and `kernel` 1 to 64 printable ASCII characters,
and no COEF index may appear twice in one list; `coef-dump.sh` prints them that way
and adds a `# NOTE` line above the fragment when a value it read does not fit.

The result looks like this (values are placeholders, not measurements):

```toml
[audio.measurements]
date = 2026-09-25
bios = "M7400QC.311"
kernel = "7.0.0-31-generic"
cold_boot = [ { index = 0x0f, value = 0x.... }, { index = 0x1b, value = 0x.... }, { index = 0x40, value = 0x.... } ]
after_windows = [ { index = 0x0f, value = 0x.... }, { index = 0x1b, value = 0x.... }, { index = 0x40, value = 0x.... } ]
```

Render and check:

```sh
just render          # or: cargo run -q -p apexctl -- profile render
just render-check    # exit 1 and a diff if the committed files differ from the profile
```

`profile render` writes `hardware/m7400qc/generated/alc294-m7400qc.fw` and
`apex-audio.conf` (and `monitors.xml`). Read the `.fw` file before testing it. With the
placeholder values of the renderer's golden test (0x0f differs after Windows, 0x40
does not) it looks like this, after a few provenance comments:

```
[codec]
0x10ec0294 0x10431ab2 0

[verb]
# COEF 0x40: 0x8800 after cold boot and after Windows; not written.
# COEF 0x0f: restore the cold-boot value 0x7770 (after Windows: 0x7774).
0x20 0x500 0x000f
0x20 0x400 0x7770
# COEF 0x1b: cold boot 0x4a4b, clear 0x0000, set 0x0400 -> 0x4e4b.
0x20 0x500 0x001b
0x20 0x400 0x4e4b
```

Each written COEF is a `# COEF` comment and a pair of zero-padded lines,
`0x20 0x500 <index>` then `0x20 0x400 <value>`, in the kernel's `init_verbs` format.
The 0x1b value is the phase-A value with bit 0x0400 set, and an index from
`restore_if_windows_differs` is written only when its phase-B value differs. The
`apex-audio.conf` next to it is one `options snd-hda-intel patch=` line with four
`apex/alc294-m7400qc.fw` entries. Commit `profile.toml` and the generated files in the
same change; CI fails when they disagree.

## 5. Testing on Ubuntu with `try-fix.sh`

```sh
sudo $A/try-fix.sh install   # copy the fix to /lib/firmware/apex and /etc/modprobe.d
sudo $A/try-fix.sh status    # files present? what did the kernel load? equal to the rendered file?
sudo $A/try-fix.sh revert    # remove exactly those two files
```

`install` refuses unless:

- the `.fw` file's `[codec]` line is exactly `0x10ec0294 0x10431ab2 0`, it has only
  `[codec]` and `[verb]` sections, every verb is `0x500` or `0x400` on NID 0x20 in
  index/value pairs, written in the renderer's zero-padded form (`0x20 0x500 0x001b`),
  and no line is longer than 127 bytes;
- `apex-audio.conf` is a single `options snd-hda-intel patch=` line with four entries,
  all `apex/alc294-m7400qc.fw`;
- the running kernel has `CONFIG_SND_HDA_PATCH_LOADER=y`;
- no other modprobe.d file sets `snd-hda-intel patch=`.

Both actions are idempotent, print what to do next and how to verify. After `revert`,
remember that the codec keeps the values the fix wrote until it loses power: measure
A or B only after a power-off or a Windows round trip.

### If `snd-hda-intel` is in the initramfs

`try-fix.sh` checks with `lsinitramfs`. On this host the module is expected to be absent
(`MODULES=most` does not include sound). If it is present, the driver probes inside the
initramfs, before `/lib/firmware` is reachable, and the fix is not applied. Then:

1. Add a hook so the firmware file is copied into the initramfs, as
   `/etc/initramfs-tools/hooks/apex-audio` (mode 0755):

   ```sh
   #!/bin/sh
   PREREQ=""
   prereqs() { echo "$PREREQ"; }
   case "$1" in prereqs) prereqs; exit 0 ;; esac
   . /usr/share/initramfs-tools/hook-functions
   copy_file firmware /lib/firmware/apex/alc294-m7400qc.fw
   ```

2. Run `sudo update-initramfs -u` yourself (`mkinitramfs` copies
   `/etc/modprobe.d/*.conf` into the image, so the option is picked up too).
3. After `try-fix.sh revert`, delete the hook and run `sudo update-initramfs -u` again.

## 6. Upstream submission

The kernel patch is `packaging/pkgs/kernel/patches/0001-ALSA-hda-realtek-Fix-speaker-output-on-ASUS-M7400QC.patch`.
It adds `ALC294_FIXUP_ASUS_COEF_1B_BIT10` (a read-modify-write of bit 10 of COEF 0x1b at
every init, chained to `ALC294_FIXUP_ASUS_HPE`) and the quirk
`SND_PCI_QUIRK(0x1043, 0x1ab2, "ASUS M7400QC", ...)`. It applies to v7.3-rc4,
next-20260922, `tiwai/sound.git` for-next and for-linus and v7.2.7, and it is
**compile-tested only**. Send it only after phases A–E pass.

Update the patch first:

1. **Author.** Replace `Your Name <you@example.org>` in `From:` and `Signed-off-by:`
   with your real name and address.
2. **Commit message.** Replace the `0x4e4b -> 0x4a4b` sentence with the measured A and
   B values, state that the fault needs no power-off to fix with the patch applied
   (phase C), and that cold boot (E) and suspend (D) still work. Remove anything the
   dumps did not confirm.
3. **Chain.** If 0x0f did not differ between A and B and the speakers work without
   it, change `.chain_id` to `ALC294_FIXUP_ASUS_HEADSET_MIC`. If a TRRS headset mic
   does not work on pin 0x19 with the chain, end the chain before the headset-mic
   fixups and say so in the message.
4. **Tested-by.** Add `Tested-by:` only after running a kernel with the patch (the
   `.fw` test proves the values, not the patch). The Apex kernel fork (M2) or a
   rebuilt `snd-hda-codec-alc269` module for the running kernel both work; remove the
   `.fw` fix (`try-fix.sh revert`, power-off) before that test.

Then, in a checkout of `tiwai/sound.git` (`for-next`):

```sh
git am /path/to/0001-ALSA-hda-realtek-Fix-speaker-output-on-ASUS-M7400QC.patch
./scripts/checkpatch.pl --strict -g HEAD      # expected: 0 errors; one warning about Cc: stable without Fixes:
make allmodconfig && make W=1 sound/hda/codecs/realtek/
git format-patch -1 -o outgoing/
./scripts/get_maintainer.pl outgoing/0001-*.patch
git send-email --dry-run --to=tiwai@suse.com --cc=perex@perex.cz \
    --cc=linux-sound@vger.kernel.org --cc=kailang@realtek.com outgoing/0001-*.patch
git send-email --to=tiwai@suse.com --cc=perex@perex.cz \
    --cc=linux-sound@vger.kernel.org --cc=kailang@realtek.com outgoing/0001-*.patch
```

- `get_maintainer.pl` is authoritative. Today it names Takashi Iwai
  <tiwai@suse.com> and Jaroslav Kysela <perex@perex.cz> (MAINTAINERS "SOUND") and
  linux-sound@vger.kernel.org. Kailang Yang (Realtek) is a customary Cc for ALC
  quirks, not a listed maintainer.
- `Cc: <stable@vger.kernel.org>` is a trailer in the patch; `git send-email` adds it
  to the Cc list automatically. That is how the fix reaches Fedora's 7.2.y and 7.3.y.
- Before sending, search lore for an existing patch in a browser (it has a bot check):
  `https://lore.kernel.org/linux-sound/?q=1ab2`.
- Copy the final patch back into `packaging/pkgs/kernel/patches/` so the repository matches
  what was sent.

## 7. CI canary and removal of the firmware file

The weekly canary (`.github/workflows/canaries.yml`, probe `canaries.sh audio`)
downloads Fedora 45's current `kernel-modules` RPM and looks for the quirk's SSID bytes
in `snd-hda-codec-alc269.ko`. `SND_PCI_QUIRK(0x1043, 0x1ab2, ...)` is stored
little-endian, so the bytes are `43 10 b2 1a`. The same check by hand, on an installed
system:

```sh
KVER=$(ls /usr/lib/modules | sort -V | tail -1)
p=$(modinfo -k "$KVER" -n snd-hda-codec-alc269)
case $p in *.xz) xz -dc "$p" ;; *.zst) zstd -dc "$p" ;; *) cat "$p" ;; esac |
    python3 -c 'import sys; print(sys.stdin.buffer.read().count(b"\x43\x10\xb2\x1a"))'
```

`0` means no quirk. On the Ubuntu 7.0.0-31 module today: `1043:1ab2` = 0,
`1043:1b11` (UX431DA) = 1.

When the count becomes non-zero the job **opens an issue; it never removes the file**.
The bytes prove that an entry exists, not that it applies the bit-10 fix (upstream could
map the SSID to `ALC294_FIXUP_ASUS_HPE` alone), and four bytes can also match by
chance. Without `[model]` lines the firmware file and a kernel quirk coexist safely.

Removing the file is a manual change, after this test on Apex:

1. Read the upstream quirk and note which fixup it maps to.
2. Disable the patch file for one boot by shadowing the image's modprobe file (a file
   in `/etc/modprobe.d` with the same name overrides the one in `/usr/lib/modprobe.d`):
   `echo '# disabled for the canary test' | sudo tee /etc/modprobe.d/apex-audio.conf`
3. Power off, then run phases B and C of the acceptance test with no fix loaded
   (`init_verbs` empty). If the speakers work after a Windows warm reboot and after a
   cold boot, send a PR that removes the firmware file and the modprobe file from the
   image. That PR also changes the profile schema: in schema 1 `[audio.fix]` is a
   required table, and a profile without `[audio.measurements]` makes the image build
   label the image `degraded=audio`. So `apexctl`, the profile and the Containerfile's
   audio step change together, for example with a schema-2 key that says the kernel
   quirk covers this codec.
4. `sudo rm /etc/modprobe.d/apex-audio.conf` to restore the fix until that PR ships.
