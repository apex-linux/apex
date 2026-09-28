# Recovery

Runbooks for when an update, the boot chain or a signing key goes wrong. They follow
[ADR 0009](adr/0009-boot-assessment.md) (boot assessment),
[ADR 0010](adr/0010-install-and-bootstrap.md) (install and recovery) and
[ADR 0012](adr/0012-trust-and-keys.md) (keys), and implement the incident runbooks the
[threat model](THREAT-MODEL.md) names. Device names are placeholders in `<…>`.

| Symptom | Go to |
|---|---|
| The new version misbehaves, but the laptop boots | §2 |
| A notification or `apexctl status` says the update failed its health checks | §3 |
| The new version does not boot | §1 (it usually recovers by itself) |
| Neither version boots, or the GRUB menu cannot be reached | §4 |
| "No bootable device", firmware boots Windows only, ESP damaged | §5 |
| A signing key or the GitHub account may be compromised | §6 |
| You applied an update and want to cancel it before the restart | §7.1 |
| Follow the testing channel, or go back to stable | §7.2 |
| You want to see the boot messages behind the splash | §1, "Watch a boot in text mode" |

## 1. The boot menu and the previous deployment

**How the menu behaves.** bootupd's static GRUB configuration
(`grub-static-pre.cfg`) sets `timeout_style=menu` and `timeout=1`: the menu is
**always shown, for 1 second**. Fedora's auto-hidden menu (`menu_auto_hide`, Shift or
Esc to reveal it, `grub2-set-bootflag`) is not part of the static configuration and
does not apply. Any key pressed while the menu is visible stops the countdown. Use the
arrow keys: Esc during power-on opens the ASUS firmware boot menu instead. Start
tapping ↓ as soon as the ASUS logo disappears.

**Entries.** `10_blscfg` lists one entry per ostree deployment: entry 0 is the default
(normally the newest), entry 1 the previous deployment. The titles end in
`(ostree:0)` and `(ostree:1)`. Then comes "UEFI Firmware Settings". Windows is not in
this menu; start it from the firmware boot menu.

**Writing grubenv on a running Apex.** bootc mounts `/boot` read-only, and it stays
read-only for the whole system. Every `grub2-editenv … set|unset` below therefore runs
inside `unshare --mount --propagation private`, a private mount namespace in which only
that one command sees `/boot` remounted read-write. `apex-updated` and
`apex-boot-assess` write grubenv the same way (M1 contract §5). The namespace ends when
`grub2-editenv` exits, and `findmnt -no OPTIONS /boot` still starts with `ro`
afterwards. Never run a plain `sudo mount -o remount,rw /boot`: that makes `/boot`
writable for every process until someone remounts it read-only. Reading needs no
remount: `sudo grub2-editenv /boot/grub2/grubenv list`.

**Show the menu longer at the next boot**, from a running Apex:

```sh
sudo unshare --mount --propagation private -- sh -c \
    'mount -n -o remount,rw /boot && exec grub2-editenv /boot/grub2/grubenv set menu_show_once_timeout=30'
```

bootupd's `14_menu_show_once.cfg` shows the menu for that many seconds once and then
unsets the variable.

**Automatic fallback.** After `apexctl update apply`, the update is armed
(`apex_target=<digest> apex_counter=3 apex_ok=0` in grubenv). A new deployment that
fails to reach a green boot assessment gets exactly three boots; the fourth boot is
entry 1, the previous deployment. Early failures count too:

- a kernel panic or an initramfs failure reboots, because the image boots with
  `panic=10 rd.shell=0 rd.emergency=reboot`;
- a counted boot that stops in emergency or rescue mode reboots by itself after a delay
  that the console announces (drop-ins for `emergency.service` and `rescue.service`, M1
  contract §2). To keep that shell for a diagnosis, run
  `systemctl stop apex-emergency-reboot.timer` in it; the boot has still used one of
  the three attempts. Emergency and rescue mode outside a counted boot are unchanged.

On the fourth boot the boot assessment does two things, in this order:

1. It stores `apex_counter=3`. This is a hedge: if the next step is cut short, the
   next boot is a counted boot of entry 0. It is never an uncounted boot of an entry 1
   that may by then be the failed update.
2. It reports the fallback to `apex-updated`, which denylists the failed digest and
   makes the running deployment the default (`bootc rollback`). Then `apex_target` and
   `apex_counter` are unset (ADR 0009, Fallback row).

Afterwards `apexctl status` shows the previous version booted and no longer says
"rollback queued", and `sudo grub2-editenv /boot/grub2/grubenv list` shows no
`apex_target`. You only need the menu when no update is armed. Fedora's own
`boot_success` and greenboot's `boot_counter` play no part in this; Apex uses only the
`apex_*` variables.

**A fallback that did not finish** leaves a state that looks like the manual pick
below. This happens, for example, when `apex-updated` could not be reached. The previous
version runs but is not the default yet, and grubenv still holds `apex_target` with the
hedge `apex_counter=3`. `journalctl -b -u apex-boot-assess.service` shows a
`decision: fallback …` line, then a failed step and a line saying that the hedge stays.
Handle it like the manual pick. If instead `apexctl status` does not say "rollback
queued" but grubenv still holds `apex_target` and `apex_counter=3`, the rollback did
happen and only the disarm was lost: the next boot of the previous version clears the
arming (`decision: inconsistent`), or disarm by hand as shown below ("To disarm a
pending boot count by hand").

**Booting entry 1 by hand does not change the default.** The next boot starts entry 0
again, and `apexctl status` says so (state `rollback-queued` in `--json`):

```text
The running 45.20260920.110 is not the default: the newer version 45.20260924.117 will start at the next boot (rollback queued).
This happens after an older version is started from the boot menu.
To keep running 45.20260920.110, first check whether 45.20260924.117 is an update whose boot check is still running (apex_target is set):
sudo grub2-editenv /boot/grub2/grubenv list
Then follow docs/RECOVERY.md §1, which says what is safe in each case.
Automatic updates are paused until the next boot.
```

`apexctl update rollback` refuses in this state ("apexctl update rollback cannot undo a
queued rollback") and prints the same advice. apexctl cannot see whether an update is
armed, because the update service does not publish the arming, so check grubenv
yourself:

```sh
sudo grub2-editenv /boot/grub2/grubenv list                    # apex_target set, or not?
journalctl -b -u apex-boot-assess.service | grep 'decision:'   # target-skipped: an armed update was skipped
```

**`apex_target` is set:** entry 0 is an applied update whose boots are still being
counted. Do **not** run `sudo bootc rollback` now. After a boot of entry 1 picked by
hand, the boot assessment keeps the arming ("target-skipped"), because the update is
still the default. `bootc rollback` swaps entries 0 and 1 without touching grubenv. With
`apex_counter` at `0` (or `-1`), the next boot would then start the failed update again,
as entry 1 and without a boot count. If it fails before userspace, it would fail that
way on every boot. Pick one of these instead:

- **Let the count finish (preferred).** Restart and pick entry 1 again at each boot
  until GRUB falls back by itself. Every boot counts, including one of entry 1 picked by
  hand, and at most `apex_counter` + 1 restarts are needed; with `apex_counter=0` it is
  the very next one. On the boot where GRUB falls back, the automatic fallback above
  makes entry 1 the default, denylists the update and disarms. Then `apexctl status` no
  longer says "rollback queued", and `grub2-editenv … list` shows no `apex_target`. If
  you let GRUB start the update instead and it reaches a green desktop, the update is
  confirmed and stays the default; to leave it then, run
  `apexctl update rollback --mark-bad` there (§2), which also denylists it.
- **Keep the running deployment now,** for example when `apex-updated` does not work.
  Disarm first, then swap, then pause automatic downloads. The update is not denylisted
  this way:

  ```sh
  sudo unshare --mount --propagation private -- sh -c \
      'mount -n -o remount,rw /boot && exec grub2-editenv /boot/grub2/grubenv unset apex_target apex_counter'
  sudo grub2-editenv /boot/grub2/grubenv list      # no apex_target, no apex_counter
  sudo bootc rollback                              # prints "notice: Reverting queued rollback state"
  sudo systemctl disable --now apex-update-auto.timer
  ```

  Do not restart until the disarm and `bootc rollback` have both succeeded; if one
  fails, repeat it. Undo the timer change with `enable --now` once a newer build exists.

**`apex_target` is not set:** no update is armed. Make the running deployment the
default:

```sh
sudo bootc rollback      # prints "notice: Reverting queued rollback state"
```

Rollback does not pull, so no signature policy is involved. Check the state first: if
an armed update had used up its three boots, the fallback has already made entry 1 the
default, `apexctl status` no longer says "rollback queued", and running
`bootc rollback` again would queue the bad deployment.

To disarm a pending boot count by hand (for example when `apex-updated` cannot run):

```sh
sudo unshare --mount --propagation private -- sh -c \
    'mount -n -o remount,rw /boot && exec grub2-editenv /boot/grub2/grubenv unset apex_target apex_counter'
```

This only removes the automatic fallback: an applied update still boots next, now
without a boot count. Before the restart, `apexctl update discard` disarms and also
locks the update again (§7.1; it needs the network).

**Watch a boot in text mode.** The image boots with `rhgb quiet`: Plymouth's graphical
splash, and kernel and systemd messages on the console only for errors. The journal has
every message either way (`journalctl -b`). To see them on screen for one boot, for
example when a boot seems to hang behind the splash:

1. Know whether an update is armed (`apex_target` in
   `sudo grub2-editenv /boot/grub2/grubenv list`, or in the §4 live-USB read). GRUB
   counts an armed boot before the menu appears, so an edited boot of an armed update
   uses one of its three attempts like any other boot, and a typo that stops the boot
   wastes one. Without an armed update, a failed edited boot changes nothing.
2. Give yourself time at the menu: set `menu_show_once_timeout=30` as above, or press ↓
   while the menu shows.
3. Select the entry and press `e`. In the line that starts with `linux`, delete the
   words `rhgb` and `quiet` and change nothing else. The same line holds `root=`,
   `rootflags=`, `rd.luks.uuid=` and `ostree=`, which the boot needs.
4. Press Ctrl+X or F10 to boot the edited entry. Esc discards the edit and returns to
   the menu.

Nothing is saved: the next boot uses the image's arguments again
(`/usr/lib/bootc/kargs.d/10-apex.toml`). Without `rhgb`, Plymouth stays in text mode,
and the LUKS passphrase prompt appears among the boot messages.

## 2. Rolling back from a running system

```sh
apexctl status                       # which digest is booted, which is the rollback
apexctl update rollback --mark-bad   # the running version is bad: go back and never offer it again
apexctl update rollback              # go back without marking the running version bad
```

Both ask for the administrator password (polkit `…update.rollback`, `auth_admin`), queue
the rollback deployment as the default (`bootc rollback`), disarm a pending boot count
and print that a reboot is needed. Then restart from the GNOME menu.

- `--mark-bad` adds the **booted** digest to the denylist. Never use it while you are
  booted into the good, older deployment: it would denylist the good one.
- If `apexctl status` says "rollback queued" (you picked entry 1 by hand), both
  commands refuse (exit 3) with "apexctl update rollback cannot undo a queued rollback"
  and point to §1. Keep the running deployment as §1 describes, and check grubenv for
  `apex_target` before any `sudo bootc rollback`.
- Both refuse (exit 2) when the other deployment is on the denylist ("… failed before
  and is marked as bad, so it is not started again"). After an automatic fallback the
  other deployment is the failed update, which stays installed until the next update
  replaces it.
- A staged update is discarded by the rollback.
- `/etc` changes made since the previous deployment was last booted do not carry over
  (bootc-rollback(8)): for example new Wi-Fi connections or a changed password. `/var`,
  including `/var/home`, is not affected.
- The daemon offers a digest again unless it is denylisted. After a rollback without
  `--mark-bad` from a bad update, pause automatic downloads until a newer build
  exists: `sudo systemctl disable --now apex-update-auto.timer` (undo with
  `enable --now`).

If `apex-updated` itself is broken, use bootc directly; rollback does not pull, so it
needs no signature policy. `bootc rollback` does not touch grubenv, so disarm a pending
boot count first: an armed count at `0` would otherwise start the deployment you are
leaving again at the next boot, as entry 1 and without a boot count.

```sh
sudo grub2-editenv /boot/grub2/grubenv list      # apex_target set? then disarm:
sudo unshare --mount --propagation private -- sh -c \
    'mount -n -o remount,rw /boot && exec grub2-editenv /boot/grub2/grubenv unset apex_target apex_counter'
sudo grub2-editenv /boot/grub2/grubenv list      # no apex_target, no apex_counter
sudo bootc rollback
sudo bootc status        # "rollback queued" / next boot: rollback deployment
```

Do not restart until the disarm and `bootc rollback` have both succeeded. Nothing is
denylisted this way: pause automatic downloads as above.

## 3. Health failure after an update

When a newly applied deployment fails a required check (ADR 0009) while you are logged
in, Apex does not reboot under you. `apex-boot-assess` records the failure,
`apex-updated` publishes it, and the laptop keeps running the new deployment.

```sh
apexctl status                                         # "The last update failed its health checks." and the digest
apexctl status --json                                  # "health_failure": "sha256:…" (null when none)
sudo cat /var/lib/apex/health-failure.json             # {"digest": …, "failed_checks": [...], "at": …}
journalctl -b -u apex-boot-assess.service              # what failed and why
```

Decide:

- **Roll back** (the normal case): `apexctl update rollback --mark-bad`, then restart.
  The failed digest is denylisted and not offered again; a newer build will be.
- **Keep it** (the check failed for a local reason you have fixed): restart. The boot
  count is still armed, so the next boot is assessed again; a green boot clears
  `HealthFailure`. Three red boots in a row fall back automatically (§1). To clear the
  notice without restarting, after reading it:

  ```sh
  apexctl update acknowledge     # exit 3 when no failure is recorded
  ```

  It removes the notice and `/var/lib/apex/health-failure.json`, nothing else: nothing
  is rolled back, and the boot count stays armed. It needs no password in your own
  active session (polkit `…update.discard`).

  Until a green boot confirms the running version, `apexctl update apply` refuses
  (exit 2) to install another update on top of it. The refusal says that the running
  version failed its startup check and to go back to the previous version first (while
  `health-failure.json` names it), or that it has not passed its startup check yet
  (while grubenv is still armed for it, also after `acknowledge`). Installing another
  update would remove the last version known to work: after the restart only the new
  update and the unconfirmed one would remain (M1 contract §5, arming precondition).

Related states (`"state"` in `apexctl status --json`):

- `finalize-failed`: the update was not installed at shutdown. Check
  `ls /boot/ostree/finalize-failure.stamp`, `df -h /boot` and
  `journalctl -b -1 -u ostree-finalize-staged.service`. Nothing was changed; download
  and apply again once the cause is fixed.
- `rollback-queued`: the other deployment starts at the next boot, either because you
  ran `apexctl update rollback` or because you picked entry 1 by hand. Restart to go
  there, or keep the running deployment as §1 describes (`apexctl update rollback`
  refuses while a rollback is queued). After `apexctl update rollback` no update is
  armed and `sudo bootc rollback` cancels it; after picking entry 1 by hand with an
  armed update, do not run `sudo bootc rollback` (§1). Cancelling does not remove a
  `--mark-bad` denylist entry.

## 4. From a live USB

Use this when the GRUB menu cannot be used, or neither deployment boots. Boot the
Fedora 45 live USB (INSTALL.md §4), open a terminal, `sudo -i`, then open and mount the
installed system:

```sh
lsblk -o NAME,SIZE,FSTYPE,PARTLABEL                   # find apex-boot, apex-root and the ESP
cryptsetup open /dev/<apex-root partition> apex-root  # passphrase or recovery key
mkdir -p /mnt/sysroot /mnt/var
mount -o subvol=root /dev/mapper/apex-root /mnt/sysroot
mount /dev/<apex-boot partition> /mnt/sysroot/boot
mount -o subvol=var,ro /dev/mapper/apex-root /mnt/var  # logs only
```

Read the logs of the failed boots:

```sh
journalctl --directory=/mnt/var/log/journal --list-boots
journalctl --directory=/mnt/var/log/journal -b -1 -p warning
grub2-editenv /mnt/sysroot/boot/grub2/grubenv list    # apex_target, apex_counter, apex_ok
```

The live system mounted the Apex `/boot` read-write itself, so `grub2-editenv` needs no
namespace here. `apex_counter=-1` means GRUB has already fallen back to entry 1.

`bootc rollback` works only on the booted system, so from the live USB pick one of
these:

**A. Show the menu once, then keep the previous deployment (preferred).**

```sh
grub2-editenv /mnt/sysroot/boot/grub2/grubenv set menu_show_once_timeout=30
```

Reboot and choose entry 1. What happens then depends on the grubenv values read
above:

- **No `apex_target`:** no update is armed and grubenv stays as it is. `apexctl status`
  says "rollback queued"; make the running deployment the default with
  `sudo bootc rollback` (§1).
- **`apex_counter` is `0` or `-1`:** GRUB boots entry 1 by itself at this boot, and the
  automatic fallback (§1) makes it the default, denylists the failed digest and
  disarms. Nothing else to do. If `apexctl status` still says "rollback queued"
  afterwards, the fallback did not finish: continue as §1 describes for a set
  `apex_target`.
- **`apex_counter` is `1`, `2` or `3`:** the update is still the default, so the boot
  assessment keeps the arming ("target-skipped") and GRUB goes on counting. Do not run
  `sudo bootc rollback`; restart until GRUB falls back by itself ("Let the count
  finish" in §1). A `3` can also be the hedge of a fallback that did not finish (§1);
  the steps are the same.

**B. Make the previous deployment the default from the live system.** This is what
`bootc rollback` does underneath (reorder the ostree deployments):

```sh
dnf install ostree                                    # in the live session
ostree admin --sysroot=/mnt/sysroot status            # index 0 is the default, 1 the previous
ostree admin --sysroot=/mnt/sysroot set-default 1
grub2-editenv /mnt/sysroot/boot/grub2/grubenv unset apex_target apex_counter
ostree admin --sysroot=/mnt/sysroot status            # the previous deployment is now first
```

Unsetting the counter is required: while `apex_target` is set and `apex_counter` is
`-1` (or `0`), the Apex GRUB snippet boots entry 1 on every boot, which after
`set-default 1` would be the bad deployment. After booting, pause automatic downloads
as in §2, because the bad digest was not denylisted.

After A or B, unmount before rebooting:
`umount /mnt/var /mnt/sysroot/boot /mnt/sysroot && cryptsetup close apex-root`.

**C. Both deployments are broken: reinstall, keeping `/var`.** Only the `root`
subvolume and `/boot` are rebuilt. The LUKS container, the `var` subvolume (with
`/var/home`, Flatpaks and the denylist) and the ESP stay. Before starting, copy what you
cannot lose to an external drive anyway, while `/mnt/var` is still mounted:

```sh
rsync -aHAX --info=progress2 /mnt/var/home/ <BACKUP_DIR>/home/
umount /mnt/var /mnt/sysroot/boot /mnt/sysroot
```

Then, with `apex-root` still open, set the placeholders by hand (§5.1 and §5.2 of
INSTALL.md set them too, but they also partition the disk: do not run them), and
rebuild the root subvolume and `/boot`:

```sh
lsblk -o NAME,SIZE,FSTYPE,PARTLABEL                   # PARTLABEL apex-boot, apex-root; the ESP
ESP_PART=/dev/<ESP>; BOOT_PART=/dev/<apex-boot partition>; ROOT_PART=/dev/<apex-root partition>
mkdir -p /mnt/btrfs && mount -o subvolid=5 /dev/mapper/apex-root /mnt/btrfs
btrfs subvolume list /mnt/btrfs                       # root, var (maybe var/…); no root/… entry
mv /mnt/btrfs/root /mnt/btrfs/root-old                # the broken system, kept for now
btrfs subvolume create /mnt/btrfs/root
btrfs subvolume create /mnt/btrfs/install-tmp
mkfs.ext4 -L apex-boot "$BOOT_PART"                   # it must report the old label apex-boot
```

`mkfs.ext4` asks before overwriting; answer `y` only when it names the `apex-boot`
filesystem. Empty `/boot` is required: bootupd keeps an existing `grubenv`, and a stale
arming from the broken system would steer the first boot. Continue with INSTALL.md:
§4 steps 4 to 6 (network, tools, SELinux) if this live session has not done them, the
second block of §5.3 ("Mount the target", not `mkfs` or `luksFormat`), then §6 and §7
as written. In §8, skip `cp -a --reflink=always …` and `chcon …`: the `var`
subvolume already holds `/var` and its SELinux label. Run only the lines that set
`STATEROOT`, `DEPLOY` and `BTRFS_UUID`, append the `/var` line to `$DEPLOY/etc/fstab`,
and unmount as §8 says.

After the first boot, GNOME Initial Setup asks for an account again, because `/etc` is
new. Use the same user name as before, then check `ls -ln /var/home`: the owner of
your home directory must be your `id -u`; if it is not, run
`sudo chown -R "$USER": "/var/home/$USER"`. Other `/etc` settings, such as Wi-Fi
networks, start from the image defaults; the old ones are in
`root-old/ostree/deploy/default/deploy/*/etc`. Delete `root-old` once you no longer
need it, from the live USB after the `cryptsetup open` of §4 and the `subvolid=5` mount
above: `btrfs subvolume delete /mnt/btrfs/root-old`.

If the `var` subvolume itself is the problem, or the btrfs filesystem or the LUKS
header is damaged, the only way left is INSTALL.md §5.3 onwards. That **erases the whole
Apex root partition, `/var/home` included**: make the `rsync` copy above first and check
that it opens, unmount everything on `apex-root` and `cryptsetup close apex-root`
(`luksFormat` refuses an open device), and set the three placeholders by hand as above.

## 5. Restoring the ESP and firmware boot entries

The ESP is shared with Windows. INSTALL.md §2 took a file backup before Apex was
installed (`esp-<date>.tar`) and §9 one afterwards (`esp-apex-<date>.tar`).

### 5.1 File-level restore

```sh
mkdir -p /mnt/esp && mount /dev/<ESP> /mnt/esp
ls /mnt/esp/EFI                                        # Microsoft, fedora, BOOT, ...
```

- **Repair Apex's boot files:** `tar --extract --file=<BACKUP_DIR>/esp-apex-<date>.tar --directory=/mnt/esp`
- **Remove Apex from the ESP** (undo an install): `rm -r /mnt/esp/EFI/fedora`, then
  `tar --extract --file=<BACKUP_DIR>/esp-<date>.tar --directory=/mnt/esp` to put back the
  fallback loader `EFI/BOOT/BOOTX64.EFI` that bootupd replaced.

Extracting overwrites files of the same name and leaves other files alone.
`umount /mnt/esp` when done.

### 5.2 Damaged ESP filesystem

```sh
fsck.vfat -a /dev/<ESP>                               # try a repair first
```

Only if that fails: `mkfs.vfat -F 32 -n EFI /dev/<ESP>` (this **erases** the ESP,
including Windows' boot files), then extract `esp-<date>.tar` (Windows and anything
else from before Apex) and then `esp-apex-<date>.tar` (Apex's files).

### 5.3 Firmware boot entries

```sh
efibootmgr -v                                          # compare with efibootmgr-<date>.txt from the backup
efibootmgr --create --disk <DISK> --part <ESP number> --label "Windows Boot Manager" \
    --loader '\EFI\Microsoft\Boot\bootmgfw.efi'
efibootmgr --create --disk <DISK> --part <ESP number> --label "Fedora" \
    --loader '\EFI\fedora\shimx64.efi'
efibootmgr --bootorder <XXXX>,<YYYY>
```

Without any entry, the firmware boots `EFI/BOOT/BOOTX64.EFI`; shim's fallback then
recreates the Fedora entry from `EFI/fedora/BOOTX64.CSV` by itself.

### 5.4 From a running Apex

```sh
sudo bootupctl status      # installed and available bootloader versions
sudo bootupctl validate    # checks the installed EFI files against bootupd's record
sudo bootupctl update      # rewrites outdated EFI files from the booted image
```

bootupd never regenerates the static `/boot/grub2/grub.cfg`; if it is lost or lacks the
`# apex-bootcount v1` marker, copy it back from your backup
(`<BACKUP_DIR>/grub.cfg`, INSTALL.md §9) until `apexctl boot repair-grub` exists (M2).

## 6. Key and account compromise

Keys (ADR 0012, `image/system_files/usr/share/apex/keys/README.md`):

| Key | Signs | Private half | Trusted by the laptop through |
|---|---|---|---|
| release | `ghcr.io/sekirokenjii/apex` (stable) | GitHub environment `release` (`COSIGN_PRIVATE_KEY`, `COSIGN_PASSWORD`) | `/usr/share/apex/keys/release.pub` |
| offline backup | emergencies only | encrypted, on two offline media | `/usr/share/apex/keys/release-backup.pub` |
| CI | `ghcr.io/sekirokenjii/apex-testing` | GitHub environment `testing` | `/usr/share/apex/keys/ci.pub` |

Rules for every procedure below:

- The policy that verifies an update is the one in the **booted** image. A new key
  must ship in an image before anything is signed with it.
- Signing always uses the legacy format:
  `cosign sign --yes --new-bundle-format=false --use-signing-config=false --key <key> ghcr.io/sekirokenjii/apex@sha256:<digest>`.
  Rekor upload stays on, which makes signatures searchable:
  `rekor-cli search --public-key <file>.pub --pki-format x509`.
- Record every new key's fingerprint in its pull request:
  `openssl pkey -pubin -in <file>.pub -outform DER | sha256sum`.
- Generate and use offline keys on a freshly booted live USB, keys on removable media,
  working directory in `/run/user/$UID` (tmpfs).

### 6.1 Planned rotation (no compromise)

For the release key: image N adds the new public key as an extra `keyPaths` entry next
to the old one; N+1 is the first image signed with the new key; N+2 removes the old
key. Rehearse it once per Fedora major in the qualification VM.

### 6.2 CI key leaked

Impact: someone can sign `apex-testing` images. Only a laptop that follows the testing
channel trusts them.

1. If the laptop follows testing (the `Channel` row of `apexctl status` says
   `testing (running image)`, or a Staged row says "from the testing channel"), switch
   to stable as §7.2 describes (administrator password):

   ```sh
   apexctl update channel stable    # downloads the stable image, locked; exit 3 if already on stable
   apexctl status                   # Staged … "locked: not used at the next boot"
   apexctl update apply             # then restart
   ```

   `apply` installs the stable build even when it is the same build as the running
   testing build or an older one. The channel switch, confirmed with the administrator
   password, counts as the confirmation a downgrade needs. When it is the same image
   (stable builds are testing builds promoted by digest), only the origin changes and
   no boot count is armed; otherwise the next boot is counted as after any `apply`.
   From the switch on, checks and downloads use only `ghcr.io/sekirokenjii/apex`. The
   `Channel` row changes to `stable (running image)` once the stable image has booted.
   The testing build you were running is then the rollback deployment: do not roll
   back to it. Compare its digest with the CI runs in step 5: if it does not match one,
   reinstall from stable (INSTALL.md) instead.
2. Remove the leaked secret: `gh secret delete COSIGN_PRIVATE_KEY --env testing` and
   `gh secret delete COSIGN_PASSWORD --env testing`.
3. Generate a new CI key and store it:
   `cosign generate-key-pair --output-key-prefix apex-ci`, then
   `gh secret set COSIGN_PRIVATE_KEY --env testing < apex-ci.key`,
   `gh secret set COSIGN_PASSWORD --env testing` (prompts), and delete `apex-ci.key`.
4. Replace `image/system_files/usr/share/apex/keys/ci.pub` with `apex-ci.pub` in a pull
   request. The next stable image carries it; testing builds signed with the new key
   verify on laptops that booted that image.
5. Audit: `rekor-cli search --public-key <old ci.pub> --pki-format x509` and
   `skopeo list-tags docker://ghcr.io/sekirokenjii/apex-testing`; every signature and
   tag must match a CI run. Delete unknown package versions on ghcr.io.

### 6.3 Release key leaked (emergency)

Impact: someone can sign images the laptop accepts as stable. Act before the laptop
downloads anything.

1. **Contain.** On the laptop: `sudo systemctl disable --now apex-update-auto.timer`.
   On GitHub: `gh secret delete COSIGN_PRIVATE_KEY --env release`,
   `gh secret delete COSIGN_PASSWORD --env release`, `gh workflow disable qualify.yml`.
   If the leak came through the GitHub account, do §6.5 first.
2. **Find what was signed.** `rekor-cli search --public-key release.pub --pki-format x509`
   lists every signature made with the key; `rekor-cli get --uuid <uuid>` shows each.
   Compare with the promotion runs of `qualify.yml`. Check where `:45` points:
   `skopeo inspect --format '{{.Digest}} {{index .Labels "org.opencontainers.image.version"}}' docker://ghcr.io/sekirokenjii/apex:45`.
3. **New backup key**, offline: `cosign generate-key-pair --output-key-prefix apex-release-backup-2`.
   Keep `apex-release-backup-2.key` encrypted on two offline media.
4. **Emergency image E**, built on a trusted machine (not in CI), from the last
   known-good digest `<GOOD>`. Its policy trusts `[backup, new backup]`: the current
   offline backup key becomes `release.pub`, the new one `release-backup.pub`, and the
   leaked key is gone. E needs a version higher than anything published, because the
   daemon refuses downgrades.

   ```sh
   mkdir e && cd e
   cp <offline media>/apex-release-backup.pub release.pub
   cp <offline media>/apex-release-backup-2.pub release-backup.pub
   podman run --rm ghcr.io/sekirokenjii/apex@<GOOD> cat /usr/share/apex/manifest.json > manifest.json
   python3 -c 'import json,sys; m=json.load(open("manifest.json")); m["version"]=sys.argv[1]; json.dump(m, open("manifest.json","w"), indent=2)' 45.<YYYYMMDD>.<N>
   cat > Containerfile <<'EOF'
   FROM ghcr.io/sekirokenjii/apex@<GOOD>
   COPY release.pub release-backup.pub /usr/share/apex/keys/
   COPY manifest.json /usr/share/apex/manifest.json
   LABEL org.opencontainers.image.version="45.<YYYYMMDD>.<N>"
   RUN bootc container lint
   EOF
   podman build -t localhost/apex-emergency .
   podman login ghcr.io                                  # with a new token (§6.5)
   podman push --digestfile e.digest localhost/apex-emergency docker://ghcr.io/sekirokenjii/apex:45.<YYYYMMDD>.<N>
   cosign sign --yes --new-bundle-format=false --use-signing-config=false \
       --key <offline media>/apex-release-backup.key ghcr.io/sekirokenjii/apex@$(cat e.digest)
   cosign verify --key release.pub ghcr.io/sekirokenjii/apex@$(cat e.digest)
   skopeo copy --preserve-digests docker://ghcr.io/sekirokenjii/apex@$(cat e.digest) \
       docker://ghcr.io/sekirokenjii/apex:45
   ```

5. **Apply E on the laptop**, checking the digest by eye because the laptop still
   trusts the leaked key until E is booted:

   ```sh
   apexctl update check && apexctl update download
   apexctl status                                        # staged digest must equal e.digest
   apexctl update apply --digest sha256:<e.digest>
   ```

   Restart. After boot, `cat /usr/share/apex/keys/release.pub` is the old backup key.
6. **Back to CI signing** with a fresh release key R2 (planned rotation, §6.1): E+1,
   signed locally with the old backup key, adds R2 as an extra `keyPaths` entry; E+2 is
   signed by CI with R2 (new secrets in the `release` environment); E+3 leaves
   `release.pub` = R2 and `release-backup.pub` = the new backup. Re-enable the timer
   (`sudo systemctl enable --now apex-update-auto.timer`) once E+2 is applied.

### 6.4 Offline backup key lost or exposed

Generate a new backup key offline (§6.3 step 3) and replace `release-backup.pub` in a
normal release; the backup key signs nothing in normal operation, so one image is
enough. If it was exposed, run the Rekor search of §6.3 step 2 with the old backup
key: any signature you did not make means a compromise, and §6.3 applies with a
freshly generated pair of keys.

### 6.5 GitHub account or token compromised

1. **Lock the account:** change the password, check that 2FA is the hardware key only,
   and revoke sessions, personal access tokens, SSH and deploy keys, and OAuth and
   GitHub App authorisations (GitHub settings).
2. **Freeze:** `gh workflow disable image.yml`, `gh workflow disable qualify.yml`, and on
   the laptop `sudo systemctl disable --now apex-update-auto.timer`.
3. **Audit:** recent commits and workflow changes on `main`
   (`git log --since=<date> -- .github/`), Actions runs and every approval of the
   `release` environment, branch protection and environment settings,
   `gh secret list --env release` and `--env testing`, and the tags and digests of both
   repositories (`skopeo list-tags docker://ghcr.io/sekirokenjii/apex`).
4. **Rotate:** if any unexpected run could read the `testing` environment, do §6.2; if
   any could read `release` (an approval you did not give), do §6.3.
5. **Retag:** if `:45` points at a digest that no legitimate promotion produced, move it
   back to the newest legitimate one with
   `skopeo copy --preserve-digests docker://ghcr.io/sekirokenjii/apex@<digest> docker://ghcr.io/sekirokenjii/apex:45`,
   and delete unknown package versions. The laptop's monotonic version check refuses
   an older image even if a tag points at one; the staleness warning shows a frozen tag.
6. Re-enable the workflows and the timer when done.

### 6.6 Not applicable at M1

- **Leaked MOK:** Apex has no Secure Boot keys of its own at M1. The runbook
  (`mokutil --mokx --import`, then `mokutil --delete`) comes with the M2 decision that
  introduces a MOK.
- **Compromised COPR or Fedora account:** M1 uses no COPR (the kernel fork is M2).

## 7. Cancelling an applied update, changing the channel

### 7.1 Cancel an applied update before the restart

```sh
apexctl update discard     # no password in your own active session (polkit …update.discard)
apexctl status             # Staged … "locked: not used at the next boot", or no Staged row
```

bootc cannot lock a stage in place. Discard therefore runs a new download-only upgrade,
which pulls the channel's tag again (M1 contract §6). That has consequences:

- **It needs the network.** Offline it fails and says that the update is still set to
  install at the next restart. Nothing has changed then: the update installs at the
  next restart, and the boot count stays armed to protect that boot. Try again once
  online.
- **It is refused where a download would be** (exit 2) whenever it may have to
  download a newer build: not enough space, on battery below 50 %, or on a metered
  connection. The message says that cancelling may download a newer update, and why it
  cannot now.
- **It may leave a newer build staged, still locked.** The output first says that the
  applied version will not be installed at the next restart. Then it says either that
  the channel still offers that build, which is now locked again, or that the channel
  has moved on and its current build replaced the one you applied, also locked. Either
  way it prints the locked build's version and full digest and the exact
  `apexctl update apply --digest …` command. Nothing installs at the next restart.
  Review a newer build with `apexctl update changes` before you apply it.
- **It cannot cancel when the channel points back at the running build** (a withdrawn
  update). Then there is nothing to lock, discard fails, and the applied update still
  installs at the next restart, protected by the boot count.

Discard succeeds only when bootc reports a locked stage and a fresh status confirms that
nothing unlocked boots next. Only then does it unset `apex_target` and `apex_counter`.
When it fails, the boot count stays armed for whatever boots next, because the update
may still install. Check with `apexctl status`: a Staged row marked "locked: not used
at the next boot", or no Staged row, means nothing installs. Discard never runs
`bootc rollback`. It exits 3 when no applied update is waiting, and it is refused while
a rollback is queued (§1).

### 7.2 Follow another channel

```sh
apexctl update channel testing     # administrator password (polkit …update.switch-channel)
apexctl status                     # Staged … locked, "from the testing channel (signed with the CI key, not qualified for stable)"
apexctl update changes             # optional: what the switch changes
apexctl update apply               # then restart
```

- `update channel` does not change what boots. It downloads the channel's current
  image and stages it locked, like `apexctl update download`, and prints "Apex now
  follows the testing channel. Its image … is downloaded and stays locked until you
  apply it." From then on, checks and downloads use the new channel. The switch takes
  effect only with `apexctl update apply` and a restart.
- `apply` installs a stage made by `update channel` even when it is not newer than the
  running version: the administrator password of the switch is the confirmation. When
  the stage is the very image that is running (stable builds are testing builds
  promoted by digest), only the origin changes. `apply` then unlocks it **without
  arming** the boot count, because this image has already booted here. Otherwise the
  next boot is counted as after any `apply` (§1).
- Until the new image has booted, the `Channel` row keeps naming the channel of the
  running image, for example `stable (running image)`.
- `update channel` exits 3 when the system already follows that channel. It is refused
  (exit 2) while an applied update waits for the restart ("An update is already set to
  install at the next restart. Cancel it first …"; cancel it with §7.1) or while a
  rollback is queued (§1).
- Testing images are signed with the CI key and are not qualified for stable. To go
  back, run `apexctl update channel stable`, then `apexctl update apply`, then restart
  (§6.2 step 1 explains what that installs).
