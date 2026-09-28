# Hardware acceptance (M7400QC)

Every hardware item Apex claims has a command and a numeric pass criterion here. M1 is
done when every numbered item passes on the laptop (ROADMAP M1 exit). Two items are
different: 8.4 runs in the qualification VM, never on the laptop, and 6.5 is recorded
at M1 but only gates fingerprint unlock (M2). Run the items on an installed Apex,
logged in to GNOME as the owner, on AC power unless an item says otherwise. Commands
that need root carry `sudo`.

Machine facts come from [hardware/m7400qc/profile.toml](../../hardware/m7400qc/profile.toml).
Details and background: [AUDIO.md](AUDIO.md), [FINGERPRINT.md](FINGERPRINT.md),
[ARCHITECTURE §6](../ARCHITECTURE.md#6-hardware-enablement-m7400qc).

Useful everywhere:

```sh
apexctl hw report     # read-only summary: audio init_verbs, charge threshold, dGPU runtime PM, fingerprint device
apexctl status        # booted, staged and rollback deployments, degraded components
```

`apexctl hw report` is a convenience; the pass criteria below use the raw commands.

## 0. Record

Start the acceptance record (template at the end) with:

```sh
apexctl status --json > /tmp/apex-status.json      # image digest and version
uname -r
cat /sys/class/dmi/id/bios_version                 # M7400QC.311 or newer
```

If `apexctl status` lists `degraded` components, the matching items below are
expected to fail and are recorded as "degraded", not as a regression.

## 1. Firmware

| # | Check | Command | Pass |
|---|---|---|---|
| 1.1 | amdgpu bound, DMUB and VCN firmware loaded | `readlink /sys/bus/pci/devices/0000:04:00.0/driver`<br>`journalctl -k -b \| grep -cE 'amdgpu 0000:04:00.0: .*(DMUB hardware initialized\|Found VCN firmware)'` | path ends in `/amdgpu`; count ≥ 2 |
| 1.2 | 90 Hz on the panel (needs amdgpu) | `gdctl show \| grep -A1 'Current mode'` | `2880x1800@90.001` |
| 1.3 | Wi-Fi firmware (AX200) | `journalctl -k -b \| grep -E 'iwlwifi .*loaded firmware version .*cc-a0-.*\.ucode op_mode iwlmvm'`<br>`nmcli -t -f TYPE,STATE device \| grep '^wifi:'` | one matching line; `wifi:connected` |
| 1.4 | Bluetooth firmware | `journalctl -k -b \| grep -cE 'Bluetooth: hci0: (Found device firmware: intel/ibt-20-1-3\.sfi\|Firmware loaded in)'`<br>`bluetoothctl show \| grep Powered` | count = 2; `Powered: yes` |
| 1.5 | CPU microcode 0x0a500012 or newer, early loading in place | `grep '^microcode' /proc/cpuinfo \| sort -u`<br>`[ $(($(awk '/^microcode/ {print $3; exit}' /proc/cpuinfo))) -ge $((0xa500012)) ] && echo ok`<br>`journalctl -k -b \| grep -E 'microcode: (Current revision\|Updated early from)'`<br>`sudo lsinitrd /usr/lib/modules/$(uname -r)/initramfs.img \| grep -c 'kernel/x86/microcode/AuthenticAMD\.bin'` | exactly one cpuinfo line (cpuinfo prints the revision without the leading zero, `0xa500012`); `ok`; a `Current revision: 0x…` line with the same revision; count ≥ 1. `Updated early from: 0x…` appears when the early loader applied the image's patch (BIOS 311 carries 0x0a50000d). It can be missing when the firmware already carries this patch or a newer one, and that passes too: note the BIOS version |
| 1.6 | No missing firmware | `journalctl -k -b \| grep 'Direct firmware load for .* failed'` | no lines. (A line for a newer iwlwifi `.ucode` API is acceptable only if 1.3 shows an older one loaded.) |

## 2. Audio (ALC294)

Setup for 2.x:

```sh
hw=$(grep -lx 0x10431ab2 /sys/class/sound/hwC*D*/subsystem_id); hw=${hw%/subsystem_id}
card=${hw##*/hwC}; card=${card%D*}; addr=${hw##*D}
coefs() {  # root; the kernel's own read-only COEF dump
    echo 1 | sudo tee /sys/module/snd_hda_codec/parameters/dump_coef >/dev/null
    sudo grep -E '^    Coeff 0x(0f|1b|40):' "/proc/asound/card$card/codec#$addr"
    echo -1 | sudo tee /sys/module/snd_hda_codec/parameters/dump_coef >/dev/null
}
```

The **speaker test** is [AUDIO.md §3.7](AUDIO.md#37-speaker-test-bypasses-pipewire-low-volume):
PipeWire stopped, Master at 30 %, `speaker-test -t wav` then a 30 s 440 Hz sine and a
10 s sine after a runtime suspend. It passes when both channels are heard from the
correct side and the tones are steady, with no dropout, crackle or gating.

| # | Check | Command | Pass |
|---|---|---|---|
| 2.1 | Patch file applied | `diff "$hw/init_verbs" <(sed -n '/^\[verb\]$/,/^\[/{/^0x/p}' /usr/lib/firmware/apex/alc294-m7400qc.fw)`<br>`journalctl -k -b \| grep -E 'Applying patch firmware\|Cannot load firmware'` | `diff` prints nothing and `init_verbs` is not empty (the renderer writes the `[verb]` lines in the kernel's `init_verbs` format, `0x20 0x500 0x001b`, so they compare byte for byte); `Applying patch firmware 'apex/alc294-m7400qc.fw'` and no `Cannot load firmware` |
| 2.2 | Not in the initramfs | `sudo lsinitrd /usr/lib/modules/$(uname -r)/initramfs.img \| grep -c 'snd-hda-intel'` | 0 |
| 2.3 | Cold boot (phase E) | shut down, unplug AC, wait 30 s, power on, log in; `coefs`; speaker test | 0x1b has bit 0x0400 set and equals the rendered value; speaker test passes |
| 2.4 | Runtime resume | inside the speaker test: `cat /sys/bus/hdaudio/devices/hdaudioC${card}D${addr}/power/runtime_status` after 5 s idle, then play again | `suspended`; the tone after it plays cleanly |
| 2.5 | Suspend and resume (phase D) | `systemctl suspend`, wake, wait 5 s; `coefs`; speaker test; `diff` of 2.1 again | values as in 2.3; speaker test passes; `init_verbs` unchanged |
| 2.6 | Windows round trip (phase C) | firmware boot menu (Esc at the ASUS logo), Windows, play sound 10 s, **Restart** into Apex (no power-off); `coefs`; speaker test | bit 0x0400 of 0x1b set; speaker test passes |
| 2.7 | Phases A and B on record | `grep -A4 '^\[audio.measurements\]' hardware/m7400qc/profile.toml` in the repository | `cold_boot` and `after_windows` present (measured on Ubuntu in M0.5, AUDIO.md §3) |

## 3. Battery charge limit

| # | Check | Command | Pass |
|---|---|---|---|
| 3.1 | After a cold boot (power off, then on) | `busctl get-property org.freedesktop.UPower /org/freedesktop/UPower/devices/battery_BAT0 org.freedesktop.UPower.Device ChargeThresholdSupported ChargeThresholdEnabled`<br>`cat /sys/class/power_supply/BAT0/charge_control_end_threshold` | `b true` twice; `80` |
| 3.2 | After suspend and resume | `systemctl suspend`, wake, wait 60 s, the same two commands | `b true` twice; `80` |
| 3.3 | After a reboot | reboot, the same two commands | `b true` twice; `80` |
| 3.4 | Default-on state file | `sudo cat /var/lib/upower/charging-threshold-status; echo` | `1` (unless you turned the limit off in Settings > Power, which must stick) |

## 4. dGPU runtime power management (M1: no driver)

At M1 no driver binds the RTX 3050 (`0000:01:00.0`, `10de:25a2`); a udev rule sets
`power/control=auto` so the root port can cut its power.

| # | Check | Command | Pass |
|---|---|---|---|
| 4.1 | No driver, runtime PM allowed | `readlink /sys/bus/pci/devices/0000:01:00.0/driver; cat /sys/bus/pci/devices/0000:01:00.0/power/control` | no driver link; `auto` |
| 4.2 | Idle share | the script below, 10 minutes idle | suspended share ≥ 95.0 % |
| 4.3 | Power state after idle | printed by the script | `runtime_status=suspended`, `power_state=D3cold` |

Idle conditions: logged in, one Ptyxis window and one Nautilus window open, nothing
else started, laptop not touched during the window (the screen may blank). Wait 60 s
after opening the windows, then run the script. **Do not** run `nvidia-smi`, `nvtop`,
`vulkaninfo`, `lspci -v` (config-space reads wake the device) or read
`/proc/driver/nvidia` during the window; with a driver loaded later (M2), the same
rules apply.

```bash
#!/usr/bin/env bash
# dgpu-idle.sh [SECONDS]: runtime-suspended share of the dGPU over an idle window.
# Reads only sysfs PM counters (milliseconds); nothing here wakes the GPU.
set -euo pipefail
dev=/sys/bus/pci/devices/0000:01:00.0
secs=${1:-600}
read_pm() { printf '%s %s\n' "$(<"$dev/power/runtime_active_time")" "$(<"$dev/power/runtime_suspended_time")"; }
printf 'control=%s driver=%s\n' "$(<"$dev/power/control")" "$(basename "$(readlink "$dev/driver" 2>/dev/null || echo none)")"
read -r a0 s0 < <(read_pm)
sleep "$secs"
read -r a1 s1 < <(read_pm)
da=$((a1 - a0)) ds=$((s1 - s0)) total=$((da + ds))
((total > 0)) || { echo "FAIL: no runtime PM accounting (is power/control 'auto'?)"; exit 1; }
share=$((ds * 1000 / total))
printf 'window %d s: active %d ms, suspended %d ms, suspended share %d.%d %%\n' \
    "$secs" "$da" "$ds" $((share / 10)) $((share % 10))
printf 'now: runtime_status=%s power_state=%s\n' "$(<"$dev/power/runtime_status")" "$(<"$dev/power_state")"
if ((share >= 950)); then echo PASS; else echo "FAIL: below 95.0 %"; exit 1; fi
```

Run it as `bash dgpu-idle.sh 600` (no root needed). For the record, also note the
counters' growth when Text Editor is started and closed five times
(informative, no criterion at M1).

## 5. Display

| # | Check | Command | Pass |
|---|---|---|---|
| 5.1 | Scale 2 in the session | `gdctl show` | under `Logical monitor #1`: `Scale: 2.0`; `eDP-1` current mode `2880x1800@90.001` |
| 5.2 | Scale 2 on the login screen | see below | `Scale: 2.0` |
| 5.3 | GTK4 gets the integer scale | `WAYLAND_DEBUG=1 gnome-text-editor --standalone 2>&1 \| grep -m1 -o 'preferred_scale([0-9]*)'` (close the window afterwards) | `preferred_scale(240)` (240/120 = 2; 5/3 would be 200) |

5.2, on the GDM login screen: press Ctrl+Alt+F3, log in on the text console, then

```sh
for s in $(loginctl list-sessions --no-legend | awk '{print $1}'); do
    [ "$(loginctl show-session "$s" -p Class --value)" = greeter ] && loginctl show-session "$s" -p User --value
done                                    # prints the greeter's uid, e.g. 60578
uid=<that uid>
sudo setpriv --reuid "$uid" --regid "$(id -g "$uid")" --clear-groups \
    env XDG_RUNTIME_DIR=/run/user/$uid DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$uid/bus gdctl show
```

Log out of the console (`exit`) and return with Ctrl+Alt+F1. A user
`~/.config/monitors.xml` overrides the system default; 5.1 must be run by a user
without one, or after choosing 200 % in Settings > Displays.

## 6. Fingerprint

Details: [FINGERPRINT.md](FINGERPRINT.md). Use the §4 foreground fprintd there if you
want the debug log; otherwise the stock service is fine for 6.1.

| # | Check | Command | Pass |
|---|---|---|---|
| 6.1 | Enrollment, 5 of 5 stages, three times in a row | `fprintd-delete "$USER"; fprintd-enroll -f right-index-finger` (repeat three times) | each run prints `enroll-stage-passed` 4 times and ends with `Enroll result: enroll-completed`; at most 5 retry results (`enroll-retry-scan`, `enroll-swipe-too-short`, `enroll-remove-and-retry`) per run; never `enroll-disconnected`, `enroll-failed` or `enroll-unknown-error` |
| 6.2 | Soak test | FINGERPRINT.md §6 | 20 cycles; every capture ends ≤ 1000 ms after the lift; ≤ 5 retry lines per second; 0 protocol errors; reader `suspended` within `autosuspend_delay_ms` + 1000 ms after each release |
| 6.3 | Not in PAM (M1) | `grep -c pam_fprintd /etc/pam.d/system-auth /etc/pam.d/fingerprint-auth` | `system-auth:0`. At M1 `fingerprint-auth` is authselect's stub; with the M2 profile it must be ≥ 1 |
| 6.4 | Power key | `gsettings get org.gnome.settings-daemon.plugins.power power-button-action`; press the key on the lock screen | `'interactive'`; nothing happens on the lock screen |
| 6.5 | Score test (gate for unlock, M2) | FINGERPRINT.md §5 | recorded; unlock is enabled only if it passes |

## 7. Input

| # | Check | Command | Pass |
|---|---|---|---|
| 7.1 | Defaults | `gsettings get org.gnome.desktop.input-sources sources; gsettings get org.gnome.desktop.input-sources per-window` | `[('xkb', 'us'), ('ibus', 'm17n:vi:telex')]`; `true` |
| 7.2 | Vietnamese Telex | in Text Editor, Super+Space to Vietnamese, type `Tieengs Vieetj cos daaus, ddi ddaau` | the text reads exactly `Tiếng Việt có dấu, đi đâu` with no correction |
| 7.3 | Per-window sources | Text Editor on Vietnamese, click into Ptyxis, type `ls`; click back into Text Editor and type `ddi` | Ptyxis gets `ls` in English; Text Editor is still Vietnamese and shows `đi` |

## 8. Updates

| # | Check | Command | Pass |
|---|---|---|---|
| 8.1 | Check and download | `apexctl update check`, `apexctl update download`, `apexctl status` | status shows a staged deployment marked download-only with the new version |
| 8.2 | Reboot with a download-only stage changes nothing | reboot; `apexctl status --json` | booted digest unchanged; rollback deployment unchanged |
| 8.3 | Apply, reboot, green | `apexctl update download` (restages from cache), `apexctl update changes`, `apexctl update apply` (prints "Reboot to finish the update."), `findmnt -no OPTIONS /boot`, reboot from the GNOME menu, log in, wait 2 min; `apexctl status`; `sudo grub2-editenv /boot/grub2/grubenv list`; `findmnt -no OPTIONS /boot`; `systemctl status apex-boot-assess.service`; `sudo grep -c '^# apex-bootcount v1' /boot/grub2/grub.cfg` (bootupd writes grub.cfg with mode 0600) | booted digest = the applied one and state `up-to-date`; grubenv has `apex_ok=1` and no `apex_target` or `apex_counter` (Apex ignores Fedora's `boot_success`); both `findmnt` outputs start with `ro` (grubenv is written in a private mount namespace); the service ended successfully; marker count 1 |
| 8.4 | Injected failing check → counted rollback | **in the qualification VM (KVM, OVMF, real GRUB), never on the laptop** | see below |

8.4: `qualify.yml` does this on every candidate. To run it by hand in the VM: install
the current stable, then download and apply a candidate built with a test-only unit
that is on the required-unit list and always fails. Do not log in. Pass:

- the VM reboots by itself after each red boot, with no session active;
- the candidate gets exactly three boots (GRUB counts `apex_counter` 3 → 2 → 1 → 0, see
  `crates/apex-boot/data/08_apex-bootcount.cfg`), and the fourth boot is GRUB entry 1,
  the previous deployment. GRUB stores `apex_counter=-1`. On that boot the boot
  assessment writes the hedge `apex_counter=3` and reports the fallback,
  `apex-updated` denylists the candidate and runs `bootc rollback`, and the variables
  are unset (RECOVERY.md §1); `journalctl -b -u apex-boot-assess.service` shows
  `decision: fallback`;
- on that boot, `apexctl status` shows the previous digest booted and default,
  `sudo cat /var/lib/apex/denylist.json` lists the candidate, and
  `sudo grub2-editenv /boot/grub2/grubenv list` shows no `apex_target` or `apex_counter`;
- `apexctl update check` does not offer the denylisted digest again.

## 9. Secure Boot state (recorded, no pass/fail at M1)

```sh
mokutil --sb-state 2>/dev/null ||
    od -An -t u1 /sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c | awk '{print "SecureBoot=" $NF}'
cat /sys/kernel/security/lockdown
```

Record the output. At M1 Apex has no Secure Boot keys of its own: the stock
Fedora-signed shim, GRUB and kernel boot with Secure Boot on or off. On this laptop it
was off on 2026-09-23. Turning it on is a separate decision (ADR 0012); Windows
BitLocker may then ask for its recovery key once.

## Acceptance record template

```
Date:            YYYY-MM-DD
Image:           ghcr.io/sekirokenjii/apex@sha256:…   version 45.YYYYMMDD.N
Kernel / BIOS:   … / M7400QC.…
Secure Boot:     enabled|disabled, lockdown: …
Degraded:        none | audio | fingerprint

1.1 … 1.6   pass/fail   notes
2.1 … 2.7   pass/fail   COEF 0x0f/0x1b/0x40 after E: …  after C: …
3.1 … 3.4   pass/fail
4.1 … 4.3   pass/fail   suspended share: …. %
5.1 … 5.3   pass/fail
6.1 … 6.5   pass/fail   soak: worst lift-to-end … ms; score test: genuine …/30, impostor …/60, max impostor score …
7.1 … 7.3   pass/fail
8.1 … 8.4   pass/fail   applied digest: …   (8.4: qualify run URL)
```
