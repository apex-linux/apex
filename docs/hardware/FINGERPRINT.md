# Fingerprint: ELAN `04f3:0c6e` in the power key

Decision: [ADR 0006](../adr/0006-fingerprint-libfprint-rebuild.md). Architecture:
[§6.3](../ARCHITECTURE.md#63-fingerprint-elan-04f30c6e). The patches and their exact
log lines: [packaging/libfprint/patches/README.md](../../packaging/libfprint/patches/README.md).
Acceptance: [ACCEPTANCE.md](ACCEPTANCE.md) §6.

At M1 the reader enrolls prints in Settings > Users, but **fingerprint is not in PAM**:
nothing unlocks with it. Screen unlock comes later, only after the score test in §5
passes. This page is the procedure for getting there without leaking biometric data.

## 1. Findings (2026-09-23)

- **Driver.** libfprint claims `04f3:0c6e` with its `elan` image driver: swipe mode,
  NBIS/bozorth3 matching, threshold 24. Fedora 45 ships `libfprint-1.94.100-1.fc45` and
  `fprintd-1.94.5-6.fc45` with no downstream patches.
- **The bug.** The driver sends a pre-scan command and accepts only the answer `0x55`
  (finger present). Only the 0x0c58 sensor gets retries for the transient answers `0x00`
  (not ready) and `0xaf` (busy or finger removed). Any other answer on 0x0c6e ends the
  session with `FP_DEVICE_ERROR_PROTO`, which fprintd reports as `enroll-disconnected`.
  fprintd runs an identify before every enroll to check for duplicates, so the very
  first capture is often the one that fails.
- **On this laptop** the journal shows the protocol error four times: on Jul 12, Sep 07
  and Sep 09 during the duplicate check, and once more on Sep 09 in the middle of an
  enrollment.
- **Upstream.** MR !582 (in v1.94.100) added the retry for 0x0c58 only. MR !655, which
  removes the model gate for every ELAN device, is open and unreviewed. Draft MR !647
  adds a settle delay after the stop command. MR !530 (press mode with SIGFM matching)
  is unmerged. The same failure is reported on 0x0c6e in issues #402, #500 (Vivobook Pro
  14X), #732, #808, #814 (includes the sibling M3500QC) and #879.
- **Matching quality is unknown.** ASUS lists the sensor as "integrated with Power
  Key": it is a press sensor, but the driver stitches 7 to 30 frames of a finger that
  does not move, as if it were swiped. Owners of other units report genuine bozorth3
  scores of 0 to 19 against the threshold of 24. Nobody has measured this unit.
- **USB.** bcdDevice 5.00, full speed, one vendor-class interface. On this host it is
  `/sys/bus/usb/devices/3-1`, with `power/control=auto` from libfprint's hwdb and
  `autosuspend_delay_ms=2000`; it sits in `suspended` when unused.

## 2. The patch series

The builder VM rebuilds the SRPM Fedora ships (`.github/scripts/libfprint.sh build`),
after `rpmkeys -K` verifies it, with the patches listed in `packaging/libfprint/series`.
The rebuild carries the release suffix `.apex1`. If a listed patch stops applying, the
image ships stock libfprint and is labelled `degraded=fingerprint`; OS updates never
block on it.

| Patch | State | Effect on 0x0c6e |
|---|---|---|
| `0001-elan-Retry-transient-pre-scan-status-on-04f3-0c6e` | enabled | Own quirk bit `ELAN_0C6E`, so `0x00`/`0xaf` are retried instead of ending the session. Logs every pre-scan answer (`pre-scan status: 0x55`). Equivalent to a subset of !655. |
| `0002-elan-Bound-transient-retries-with-lift-semantics` | enabled | **Lift semantics:** a transient answer after at least one frame means the finger was lifted, so the capture ends at once (image with ≥ 7 frames, else "swipe too short"). **Bound:** with no frame yet, retries back off 10, 50, then 200 ms, and a run of transient answers ends after `ELAN_CMD_TIMEOUT` (10 s) on the normal timeout path, never as a protocol error. Without 0002, a sensor that answers at once polls at 100 Hz for as long as a lock screen waits. |
| `0101-elan-Recover-from-dark-frame-on-0c6e` | carried, disabled | **Dark frame:** a frame darker than the background (the finger was already on the key when calibration took the background) reports "remove finger and retry" at once instead of ending the session, and that capture's frames are dropped. **Lift wait:** the capture then goes on polling, 50 ms after each frame, and drops every frame until the finger is lifted (a read timeout, or `0x00`/`0xaf`) or 10 s have passed; only then is finger-off reported, so the next calibration normally takes its background without the finger. **Bound:** at most 3 such retries in a row; the 4th dark frame is the stock session error. A capture without a dark frame resets the count. |
| `0102-elan-Settle-after-stop` | carried, disabled | Backport of !647: 10 ms settle after the stop command. |

A 01xx patch is enabled only when a log from this laptop shows its trigger: for 0101,
`frame darker than background` followed by `failed in state 3`; for 0102, a calibration
that times out right after `STOP_CAPTURE_NUM_STATES completed successfully`.
`packaging/libfprint/series` explains how to promote one. Drop 0001 and 0002 once
upstream retries `0x00`/`0xaf` on 0x0c6e: 0001 then stops applying, which is the
signal.

Once 0101 is enabled, a capture that starts with the finger already on the key gives
one `asking to remove the finger (retry N of 3)` line, `frame dropped` lines while the
finger stays, then the lift, and only then the next calibration. The
[patches README](../../packaging/libfprint/patches/README.md#which-log-lines-to-look-for)
lists the exact lines.

## 3. Privacy rules (normative)

A fingerprint cannot be revoked. These rules apply to every diagnostic step on this
page and to anything an agent does with its output.

1. **Work only in a tmpfs directory:** `/run/user/$UID/fpdiag`, mode 0700. Never in the
   repository, `/tmp` on disk, or `$HOME`. `shred` does not erase data on an SSD or a
   copy-on-write filesystem, so nothing biometric may reach a disk in the first place.
2. **Check swap first.** `swapon --show` must list only `zram` devices (RAM). If a disk
   swap file or partition is listed, run the biometric steps with swap off
   (`sudo swapoff -a`, afterwards `sudo swapon -a`), because tmpfs pages can be swapped
   out.
3. **Debug output: `G_MESSAGES_DEBUG=all` only.** It shows state-machine steps,
   calibration means, frame counts, the pre-scan bytes and `score N/24`, and no image
   data.
4. **`FP_DEBUG_TRANSFER=1` is for one question only** (which byte the sensor sends) and
   only on an unpatched build, since 0001 already logs that byte. It hex-dumps every USB
   transfer, **including raw sensor frames**, and the dump format depends on the
   version: libfprint 1.94.100 and later (Fedora 45) print a transfer on one line, but
   1.94.9 and earlier, and Ubuntu's stock `1.95.1+tod1` (the unpatched build on the
   Ubuntu dev install), print 16 bytes per line, about 110 characters. A length limit
   alone therefore keeps every frame. Filter in the pipe, before anything is written,
   with `fpfilter.awk` (below), which works with both formats; add
   `FP_DEBUG_TRANSFER=1` to the §4 command and change nothing else.
5. **Never set either variable in a systemd unit or drop-in** for `fprintd.service`.
   The journal is on disk.
6. **Never commit, attach or paste:** `*.pgm` images, `*.variant` print files (the
   libfprint examples write `enrolled.pgm`, `verify.pgm` and `test-storage.variant` to
   the working directory), anything under `/var/lib/fprint`, umockdev recordings
   (`*.ioctl`, `*.umockdev`; they contain images), usbmon captures (`*.pcap`,
   `*.pcapng`), any log line of 400 characters or more, or any hex-dump line longer
   than 4 bytes, however short the line. The CI privacy guard (ADR 0006) runs on pull
   requests and on pushes to `main`. It rejects these file types, anything
   under `var/lib/fprint`, and lines longer than 400 characters that hold a long run of
   hex bytes. It does not replace your own check: it runs only after a push, when the
   branch may already be public, and it does not look for short hex-dump lines such as
   the 16-byte lines of older libfprint (rule 4). Check a change yourself before
   committing it. All three commands must print nothing:

   ```sh
   git diff --cached --name-only | grep -E '\.(pgm|variant|ioctl|umockdev|pcapng?)$'
   git diff --cached -U0 | grep -nE '^\+.*: ([0-9A-Fa-f]{2} ?){5,} *$'
   git diff --cached -U0 | awk '/^\+/ && length($0) > 400'
   ```
7. **Before sharing a log** (with upstream or in the repository), keep only the lines
   you need (`grep`), and remove the hostname, user name, serial numbers and MAC
   addresses.
8. **umockdev recordings for upstream** are made only with a surface that is not an
   enrolled finger (for example the side of a knuckle), and are never stored in this
   repository.
9. **Clean up** with `rm -rf /run/user/$UID/fpdiag` and a reboot or logout.

**The log filter.** Every log on this page goes through `fpfilter.awk` before it is
written. Create the file in the tmpfs directory once per session:

```sh
install -d -m 0700 /run/user/$UID/fpdiag && cd /run/user/$UID/fpdiag
cat > fpfilter.awk <<'EOF'
# fpfilter.awk: drop libfprint debug output that can hold image data (FINGERPRINT.md §3).
# A dump line is a line whose text after a ": " is only hex bytes, in either format:
# "0a1b2c…" (libfprint 1.94.100 and later) or "0a 1b 2c " (16 bytes per line, older).
# At most two digit-only bytes without a space ("delta: 34") are not a dump.
# The dump line right after the "Transfer … submitted" or "… completed" line of a
# transfer of at most 4 bytes is kept: commands and status answers. Every other dump
# line is dropped, however short. Lines of 400 characters or more are dropped too.
/Transfer .* (submitted|completed)/ {
    max = -1; s = $0
    while (match(s, /length -?[0-9]+/)) {
        n = substr(s, RSTART + 7, RLENGTH - 7) + 0
        if (n > max) max = n
        s = substr(s, RSTART + RLENGTH)
    }
    small = (max >= 0 && max <= 4)
}
match($0, /: ([0-9A-Fa-f][0-9A-Fa-f] ?)+ *$/) {
    tail = substr($0, RSTART + 2)
    if (tail ~ /[A-Fa-f ]/ || length(tail) > 4) {
        if (!small) next
        small = 0
    }
}
length($0) < 400 { print; fflush() }
EOF
```

It drops every dump line of an image read, in any length and format, and keeps the
answer byte rule 4 asks about. It also drops ordinary lines that end in hex-looking
text after a `: ` (for example `delta: 123456`); that loss is accepted.

Run it as `(trap '' INT; exec awk -f fpfilter.awk)`, as the commands below do. Then awk
ignores Ctrl+C and ends when the program writing into the pipe has ended, so the log is
complete: mawk, the awk on Ubuntu, reads a pipe in large blocks, and killing it would
lose the last lines. `fflush()` writes each line out at once.

## 4. Safe diagnostic procedure

This works on Apex (patched libfprint in the image) and on the Ubuntu dev install
with a libfprint build that has patches 0001 and 0002. It uses fprintd itself, so no
image files are written anywhere.

```sh
install -d -m 0700 /run/user/$UID/fpdiag && cd /run/user/$UID/fpdiag
test -s fpfilter.awk                            # the §3 log filter is in place
swapon --show                                   # only zram, or swap off (rule 2)
sudo systemctl stop fprintd.service
sudo systemctl mask --runtime fprintd.service   # nothing can D-Bus-activate the stock one mid-test
# Terminal 1: fprintd in the foreground, debug log straight into tmpfs.
sudo env G_MESSAGES_DEBUG=all /usr/libexec/fprintd --no-timeout 2>&1 |
    (trap '' INT; exec awk -f fpfilter.awk) > fprintd.log
# Terminal 2: exercise the reader.
fprintd-enroll -f right-index-finger            # or fprintd-verify -f right-index-finger
```

Afterwards: Ctrl+C in terminal 1, then

```sh
sudo systemctl unmask --runtime fprintd.service
grep -E 'pre-scan status|finger lifted|transient pre-scan|swipe too short|darker than background|dark frame|protocol error|failed in state|score [0-9]+/24' fprintd.log
```

What the lines mean is tabulated in
[packaging/libfprint/patches/README.md](../../packaging/libfprint/patches/README.md#which-log-lines-to-look-for).
The `pre-scan status` lines are safe to share with upstream (issue #879 or MR !655).

On the Ubuntu dev install, build libfprint with only the elan driver and run the same
steps against that build (`LD_LIBRARY_PATH` pointing at `_build/libfprint`), or use the
`img-capture` example with its image written to `/dev/null`:

```sh
meson setup _build -Ddrivers=elan -Ddoc=false -Dintrospection=false \
    -Dinstalled-tests=false -Dudev_rules=disabled -Dudev_hwdb=disabled
meson compile -C _build
cd /run/user/$UID/fpdiag
sudo env G_MESSAGES_DEBUG=all FP_DRIVERS_ALLOWLIST=elan \
    ~/src/libfprint/_build/examples/img-capture /dev/null 2>&1 |
    (trap '' INT; exec awk -f fpfilter.awk) > capture.log
```

Never set `FP_DEVICE_EMULATION=1` on real hardware: it makes the driver accept any
byte and hides the bug.

## 5. Genuine and impostor score measurement

Fingerprint unlock is enabled only if this test passes. Never lower `bz3_threshold`
to make it pass.

Setup: the §4 foreground fprintd with its debug log in tmpfs. Delete old prints
(`fprintd-delete "$USER"`), then enroll the right index finger with
`fprintd-enroll -f right-index-finger`. The enrollment must complete (§6 of
ACCEPTANCE.md). Press the key the way you would to unlock: a light touch, no click.

1. **Genuine: 30 attempts** with the enrolled finger:

   ```sh
   before=$(grep -c 'score [0-9]*/24' fprintd.log)
   for i in $(seq 30); do fprintd-verify -f right-index-finger | grep 'Verify result'; done | tee genuine.txt
   grep -o 'score [0-9]*/24' fprintd.log | tail -n +"$((before + 1))" > genuine-scores.txt
   ```

2. **Impostor: 60 attempts**, 10 each with the left index, left middle, left thumb,
   right middle, right ring and right thumb, same command with `impostor.txt` and
   `impostor-scores.txt`.

3. Count: `grep -c verify-match genuine.txt impostor.txt`, and the highest impostor
   score with `sort -t' ' -k2 -n impostor-scores.txt | tail -1`.

| Measure | Pass |
|---|---|
| Genuine acceptance | ≥ 24 of 30 attempts end in `verify-match` (false rejection ≤ 20 %) |
| Impostor acceptance | 0 of 60 attempts end in `verify-match` (95 % upper bound on false acceptance ≈ 5 %) |
| Impostor margin | highest impostor score ≤ 12 (half the threshold) |
| Stability | no `enroll-disconnected`, `verify-disconnected` or `protocol error` in the whole run |

Keep only the counts and the score lists (numbers only) as the record. Delete the
logs when done (§3 rule 9). If genuine scores stay far below 24, as reported on other
units, the elan swipe pipeline is not usable on this sensor: fingerprint stays out of
PAM, and the next step is upstream press-mode work (!530), not tuning.

## 6. Lock-screen soak test

Goal: after each touch and lift the capture ends quickly, the driver does not poll
continuously, and the reader powers down once it is released. The failure this
catches is the 100 Hz poll loop that patch 0002 bounds.

At M1 (fingerprint not in PAM) run it with `fprintd-verify` standing in for the lock
screen. Before enabling unlock (M2) run it again on the real lock screen with the Apex
authselect profile selected.

```sh
# §4 foreground fprintd running, log in /run/user/$UID/fpdiag/fprintd.log
dev=$(for d in /sys/bus/usb/devices/*; do
        [ "$(cat "$d/idVendor" 2>/dev/null):$(cat "$d/idProduct" 2>/dev/null)" = 04f3:0c6e ] && echo "$d"; done)
delay=$(cat "$dev/power/autosuspend_delay_ms")
for i in $(seq 20); do
    echo "cycle $i: touch the sensor, then lift"
    fprintd-verify -f right-index-finger | grep 'Verify result'
    t0=$(date +%s%N)
    until [ "$(cat "$dev/power/runtime_status")" = suspended ]; do
        sleep 0.1
        [ $(( ($(date +%s%N) - t0) / 1000000 )) -le $((delay + 1000)) ] || { echo "cycle $i: FAIL, not suspended"; break; }
    done
    echo "cycle $i: suspended $(( ($(date +%s%N) - t0) / 1000000 )) ms after release (limit $((delay + 1000)))"
done
```

Then evaluate the log (POSIX awk, works with mawk and gawk):

```sh
awk '
function ms(s,  a) { split(s, a, /[:.]/); return ((a[1] * 60 + a[2]) * 60 + a[3]) * 1000 + a[4] }
match($0, /[0-9][0-9]:[0-9][0-9]:[0-9][0-9]\.[0-9][0-9][0-9]/) { t = ms(substr($0, RSTART, RLENGTH)) }
/pre-scan status: 0x55/ { last = t; open = 1 }
open && (/finger lifted/ || /failed in state 1 with error: transfer timed out/) {
    n++; d = t - last; if (d > worst) worst = d; open = 0 }
/transient pre-scan status .*retry/ { s = int(t / 1000); r[s]++; if (r[s] > rate) rate = r[s] }
/protocol error/ { proto++ }
END { printf "lifts %d, worst lift-to-end %d ms, worst retry rate %d/s, protocol errors %d\n", n, worst, rate, proto }
' /run/user/$UID/fpdiag/fprintd.log
```

| Measure | Pass |
|---|---|
| Cycles | 20 touch-and-lift cycles, each with a `Verify result` line |
| End of capture | every lift ends the capture within 1000 ms of the last `0x55` frame (the awk "worst lift-to-end") |
| Polling | at most 5 `transient pre-scan status ... retry` lines in any second |
| Protocol errors | 0 |
| Power | after each cycle the reader reads `suspended` within 1 s after its autosuspend delay (`autosuspend_delay_ms` + 1000 ms, 3000 ms on this host) |

On the real lock screen, lock with Super+L, do the 20 cycles on the lock screen, then
unlock with the password. The log criteria are the same. The power criterion applies
from the moment the session is unlocked, because the lock screen keeps the reader open
while it waits for a finger.

## 7. PAM policy

- **M1: fingerprint is not in PAM.** The image does not enable authselect's
  `with-fingerprint` feature. Enrolled prints exist but unlock nothing.
- **Why not `with-fingerprint`:** on Fedora that feature adds `pam_fprintd` to
  `system-auth` as well, which `sudo`, `su` and polkit include. The power-key sensor
  would then satisfy every administrator prompt, including Apex's own rollback and
  channel-switch actions.
- **Later (M2), unlock only**, and only after §5 and §6 pass: an Apex authselect
  vendor profile in `/usr/share/authselect/vendor/apex/`, derived from `local`, whose
  `fingerprint-auth` includes `pam_fprintd` (used by `gdm-fingerprint` for the login and
  lock screens) and whose `system-auth` never does. The image selects it. Image checks:
  `grep -c pam_fprintd /etc/pam.d/system-auth` prints 0 and
  `grep -c pam_fprintd /etc/pam.d/fingerprint-auth` prints at least 1.
- A fingerprint unlock does not unlock the oo7 keyring at login; the password still
  does that.

## 8. The power key

The sensor is the power key, so the image sets
`org.gnome.settings-daemon.plugins.power power-button-action='interactive'`
(`/usr/share/glib-2.0/schemas/90_apex.gschema.override`):

- on the lock screen a press does nothing, so a firm touch cannot suspend the laptop;
- on an unlocked desktop a press opens the cancellable power-off dialog.

Check: `gsettings get org.gnome.settings-daemon.plugins.power power-button-action`
prints `'interactive'`. The user can still change it in Settings > Power; no dconf lock
is used.
