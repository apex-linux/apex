# Hardware acceptance (M7400QC)

Every hardware item Apex claims has a command and a numeric pass criterion here. M1 is
done when every numbered item passes on the laptop (ROADMAP M1 exit). Three things are
different: 8.4 runs in the qualification VM, never on the laptop; 6.5 is recorded at
M1 but only gates fingerprint unlock (M2); and §4 names the slice that needs each of
its rows. Run the items on an installed Apex, logged in to GNOME as the owner, on AC
power unless an item says otherwise. Commands that need root carry `sudo`.

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

## 4. dGPU: NVIDIA driver, runtime power and offload (S1c)

The RTX 3050 (`0000:01:00.0`, `10de:25a2`) has one PCI function and no MUX. It runs
NVIDIA's open kernel modules, built and signed for exactly the image's kernel. The AMD
iGPU drives the panel and HDMI and runs the shell. Apps use the dGPU only on request,
and it idles in D3cold otherwise
([ARCHITECTURE §6.4](../ARCHITECTURE.md#64-gpu-and-power),
[ADR 0015 §6](../adr/0015-cachyos-kernel-and-nvidia.md#6-hybrid-graphics-and-power)).

- S1d needs 4.1 to 4.5, 4.7 and 4.8.
- 4.6 and 4.9 are measured in S4. 4.6 also runs in the kernel A/B (K3, S1d).
- Each NVIDIA release and each new kernel line runs this section on the laptop before
  it publishes (ARCHITECTURE §4.3).

Setup for 4.x:

```sh
dev=/sys/bus/pci/devices/0000:01:00.0
gpu=/proc/driver/nvidia/gpus/0000:01:00.0
d3cold_within() {  # d3cold_within SECONDS: polls sysfs only, which never wakes the GPU
    local s
    for ((s = 0; s <= $1; s++)); do
        [ "$(<"$dev/power_state")" = D3cold ] && { echo "D3cold after $s s"; return 0; }
        sleep 1
    done
    echo "FAIL: $(<"$dev/power_state") after $1 s"
    return 1
}
```

4.4 needs `vulkaninfo`, `eglinfo` and `glxinfo`, which the image does not ship. Install
them into a transient `/usr` overlay, which the next boot discards:
`sudo bootc usroverlay`, then `sudo dnf install vulkan-tools egl-utils glx-utils`.

| # | Check | Command | Pass |
|---|---|---|---|
| 4.1 | Driver bound, fine-grained RTD3, modules signed by this kernel's key | `readlink $dev/driver; cat $dev/power/control`<br>`grep 'Runtime D3 status' $gpu/power`<br>`grep '^DynamicPowerManagement:' /proc/driver/nvidia/params`<br>`lsmod \| grep -cE '^(nouveau\|nova_core) '`<br>`modinfo -F signer nvidia amdgpu; cat /sys/module/module/parameters/sig_enforce` | path ends in `/nvidia`; `auto`; `Enabled (fine-grained)`; `DynamicPowerManagement: 2`; `0`; two equal lines, `Apex kernel <uname -r> <content key>`, then `Y`. On the break-glass image the two signers differ (`amdgpu` carries Fedora's) and `sig_enforce` is `N`; record that ([RECOVERY §8.2](../RECOVERY.md#82-the-break-glass-image-fedoras-kernel-s1c)) |
| 4.2 | Idle share | `bash dgpu-idle.sh 600` under the idle conditions below | suspended share ≥ 95.0 % |
| 4.3 | Power state and video memory after idle | printed by the script; then `grep 'Video Memory' $gpu/power` | `runtime_status=suspended`, `power_state=D3cold`; `Video Memory: Off` |
| 4.4 | Offload: Vulkan, EGL and GLX, and the GNOME menu | `switcherooctl list`<br>`switcherooctl launch vulkaninfo --summary \| grep deviceName`<br>`switcherooctl launch eglinfo -B \| grep -c 'RTX 3050'`<br>`switcherooctl launch glxinfo -B \| grep -c 'RTX 3050'`<br>`d3cold_within 30`<br>then right-click Text Editor in the app grid, "Launch using Discrete Graphics Card"; `nvidia-smi`; close Text Editor; `d3cold_within 30` | two devices, the NVIDIA one with `Default: no`; one `deviceName`, the RTX 3050; both counts ≥ 1; D3cold within 30 s; `nvidia-smi` lists a `gnome-text-editor` process; D3cold within 30 s after it closes |
| 4.5 | HDMI hotplug stays on the iGPU | `udevadm info -q property /dev/dri/by-path/pci-0000:01:00.0-card \| grep -c mutter-device-ignore`<br>`journalctl -b -o cat _COMM=gnome-shell \| grep -E 'selected as primary\|Added device'`<br>plug in an HDMI display and wait until it shows the desktop; `d3cold_within 60`; unplug it; `d3cold_within 60` | ≥ 1; the primary GPU is the card whose `Added device` line names `amdgpu`, and no line names the NVIDIA card; D3cold within 60 s after the plug and after the unplug |
| 4.6 | s2idle with the driver bound | `grep -E '^(UseKernelSuspendNotifiers\|EnableS0ixPowerManagement\|PreserveVideoMemoryAllocations):' /proc/driver/nvidia/params`<br>`systemctl list-unit-files 'nvidia-suspend*' 'nvidia-resume*' 'nvidia-hibernate*'`<br>`d3cold_within 60`; close the lid for at least 5 minutes, open it and unlock; `d3cold_within 60`; the `glxinfo` line of 4.4 | three lines ending in `: 1`; `0 unit files listed.`; D3cold before the lid closes; D3cold within 60 s after resume; `glxinfo` still counts ≥ 1 |
| 4.7 | A Flatpak app on the dGPU | `v=$(tr . - </sys/module/nvidia/version)`<br>`flatpak list --runtime --columns=application \| grep '^org.freedesktop.Platform.GL.nvidia-'`<br>right-click Bazaar in the app grid, "Launch using Discrete Graphics Card"; `nvidia-smi`; close Bazaar; `d3cold_within 30` | exactly one line, `org.freedesktop.Platform.GL.nvidia-$v`; `nvidia-smi` lists a `bazaar` process; D3cold within 30 s after it closes |
| 4.8 | `nvidia-smi` and one driver version | `nvidia-smi -L`<br>`nvidia-smi --query-gpu=driver_version --format=csv,noheader; cat /sys/module/nvidia/version`<br>`rpm -q --qf '%{VERSION}\n' nvidia-driver nvidia-kmod-common kmod-nvidia-$(uname -r)`<br>`d3cold_within 30` | `GPU 0: NVIDIA GeForce RTX 3050 …`; the five versions are equal; D3cold within 30 s |
| 4.9 | Dynamic Boost costs no idle power | on battery: `systemctl is-active nvidia-powerd`; `bash dgpu-idle.sh 600`<br>then `sudo systemctl stop nvidia-powerd`; `bash dgpu-idle.sh 600`; `sudo systemctl start nvidia-powerd`<br>after each run: `grep . /sys/devices/system/cpu/cpufreq/policy*/{scaling,cpuinfo}_max_freq` | `active`; both runs pass 4.2; the mean battery power with `nvidia-powerd` is at most 0.1 W above the run without it; after each run, every `scaling_max_freq` equals its `cpuinfo_max_freq`. If a criterion fails, `nvidia-powerd` is turned off (ADR 0015 §6) |

Idle conditions: logged in, one Ptyxis window and one Nautilus window open, nothing
else started, laptop not touched during the window (the screen may blank). Wait 60 s
after opening the windows, then run the script. **Do not** run `nvidia-smi`, `nvtop`,
`vulkaninfo` or `lspci -v` (config-space reads wake the device) during the window, and
read nothing under `/proc/driver/nvidia`. Read `$gpu/power` only before and after it.

```bash
#!/usr/bin/env bash
# dgpu-idle.sh [SECONDS]: the dGPU's runtime-suspended share over an idle window, the
# wakes seen and the mean battery power. Reads only sysfs; nothing here wakes the GPU.
set -euo pipefail
dev=/sys/bus/pci/devices/0000:01:00.0
bat=/sys/class/power_supply/BAT0
secs=${1:-600}
read_pm() { printf '%s %s\n' "$(<"$dev/power/runtime_active_time")" "$(<"$dev/power/runtime_suspended_time")"; }
read_uw() {  # battery power in µW; meaningful on battery only
    if [ -r "$bat/power_now" ]; then cat "$bat/power_now"
    else echo $(($(<"$bat/current_now") * $(<"$bat/voltage_now") / 1000000)); fi
}
printf 'control=%s driver=%s\n' "$(<"$dev/power/control")" "$(basename "$(readlink "$dev/driver" 2>/dev/null || echo none)")"
read -r a0 s0 < <(read_pm)
wakes=0 uw=0 n=0 prev=$(<"$dev/power/runtime_status")
for ((t = 1; t <= secs; t++)); do
    sleep 1
    cur=$(<"$dev/power/runtime_status")
    [[ $prev == suspended && $cur != suspended ]] && wakes=$((wakes + 1))
    prev=$cur
    if ((t % 10 == 0)); then uw=$((uw + $(read_uw))) n=$((n + 1)); fi
done
read -r a1 s1 < <(read_pm)
da=$((a1 - a0)) ds=$((s1 - s0)) total=$((da + ds))
((total > 0)) || { echo "FAIL: no runtime PM accounting (is power/control 'auto'?)"; exit 1; }
share=$((ds * 1000 / total))
printf 'window %d s: active %d ms, suspended %d ms, suspended share %d.%d %%\n' \
    "$secs" "$da" "$ds" $((share / 10)) $((share % 10))
printf 'wakes seen (1 s sampling): %d, %d per hour\n' "$wakes" $((wakes * 3600 / secs))
((n == 0)) || printf 'battery (%s): %d mW mean\n' "$(<"$bat/status")" $((uw / n / 1000))
printf 'now: runtime_status=%s power_state=%s\n' "$(<"$dev/power/runtime_status")" "$(<"$dev/power_state")"
if ((share >= 950)); then echo PASS; else echo "FAIL: below 95.0 %"; exit 1; fi
```

Run it as `bash dgpu-idle.sh 600` (no root needed). The wake count is informative:
record it per idle hour, with `nvidia-powerd` on and off, in S4 (ROADMAP N10). A wake
shorter than 1 s can fall between two samples; the active time still counts it.

**No driver bound.** No driver binds the GPU on images before the pair ships (S1c),
in the S1d fallback on Fedora's kernel, with `degraded=nvidia`, and on the break-glass
image with Secure Boot on (ADR 0015 §4). A udev rule still sets `power/control=auto`,
so the GPU reaches D3cold unbound. Record 4.1 and 4.4 to 4.9 as "degraded" (§0), and
check instead:

- `readlink $dev/driver` prints nothing, and `cat $dev/power/control` prints `auto`;
- 4.2 passes;
- 4.3 passes without the `Video Memory` line.

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

8.4: `.github/scripts/qualify.sh red` does this in the builder VM (`just qualify-local`
prints the commands); GitHub does not run it. To run it by hand in the VM: install
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

## 9. Secure Boot and lockdown (recorded, no pass/fail)

```sh
mokutil --sb-state 2>/dev/null ||
    od -An -t u1 /sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c | awk '{print "SecureBoot=" $NF}'
cat /sys/kernel/security/lockdown
cat /sys/module/module/parameters/sig_enforce
mokutil --list-enrolled 2>/dev/null | grep -E 'SHA1 Fingerprint|Subject:'
```

Record the output. What to expect:

| State | Secure Boot | `lockdown` | Apex Secure Boot key |
|---|---|---|---|
| Until step W3 | `SecureBoot disabled` | `[none] integrity confidentiality` | not enrolled |
| From W3, if the owner turns it on | `SecureBoot enabled` | `none [integrity] confidentiality` | enrolled |
| After W3, turned off again ([RECOVERY §8.3](../RECOVERY.md#83-back-from-secure-boot-w3)) | `SecureBoot disabled` | `none [integrity] confidentiality` | enrolled |

- Secure Boot was off on this laptop on 2026-09-28.
- `sig_enforce` is `Y` on the pair whether Secure Boot is on or off. Each kernel trusts
  only the module key built into it (S1c, ADR 0015 §3).
- Turning Secure Boot on is the optional step W3, after Windows is removed. It follows
  [ADR 0015 §7](../adr/0015-cachyos-kernel-and-nvidia.md#7-secure-boot-when-and-how).
  From S1c until W3 the CachyOS kernel is not signed for Secure Boot, so turning it on
  stops Apex from booting.
- From W3, `integrity` comes from the `lockdown=integrity` kernel argument, which stays
  when Secure Boot is turned off again. CachyOS lacks Fedora's patch that turns
  lockdown on with Secure Boot.
- When the key is enrolled, one `SHA1 Fingerprint` equals, ignoring case, the output
  of `openssl x509 -inform DER -in /usr/share/apex/keys/apex-sb.der -noout -fingerprint -sha1`.

## Acceptance record template

```
Date:            YYYY-MM-DD
Image:           ghcr.io/sekirokenjii/apex@sha256:…   version 45.YYYYMMDD.N
Kernel / BIOS:   … / M7400QC.…
NVIDIA:          /sys/module/nvidia/version, or "not bound"
Secure Boot:     enabled|disabled, lockdown: …, sig_enforce: Y|N
Degraded:        none | audio | fingerprint | nvidia

1.1 … 1.6   pass/fail   notes
2.1 … 2.7   pass/fail   COEF 0x0f/0x1b/0x40 after E: …  after C: …
3.1 … 3.4   pass/fail
4.1 … 4.9   pass/fail/degraded   suspended share: …. %; wakes per idle hour: …; nvidia-powerd: +… mW
5.1 … 5.3   pass/fail
6.1 … 6.5   pass/fail   soak: worst lift-to-end … ms; score test: genuine …/30, impostor …/60, max impostor score …
7.1 … 7.3   pass/fail
8.1 … 8.4   pass/fail   applied digest: …   (8.4: _build/qualify/results.md)
```
