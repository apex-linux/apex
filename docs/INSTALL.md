# Installing Apex

Runbook for [ADR 0010](adr/0010-install-and-bootstrap.md). Recovery is in
[RECOVERY.md](RECOVERY.md); the hardware checks after installing are in
[hardware/ACCEPTANCE.md](hardware/ACCEPTANCE.md).

> [!CAUTION]
> **This runbook can destroy data.** Apex tooling never runs a destructive step for you;
> you type every command. All device names below are **placeholders** such as
> `<TARGET_DISK>`. Never paste a command before you have replaced every placeholder
> and checked it against `lsblk` output from the same session. If any output differs
> from what this page says to expect, **stop** and find out why.
>
> - Do the **rehearsal on an external USB SSD first** (§3). The internal disk is not
>   touched until Apex has passed the hardware acceptance tests from that SSD.
> - Make and verify the backups in §2 before the internal install.
> - Read the whole page before starting.

## 1. What you get

The supported path is `bootc install to-filesystem` onto a disk you have laid out
yourself. `bootc install to-disk` is not used on the laptop: it would wipe Windows and
the Ubuntu install.

| Partition | Size | Content | Mounted at |
|---|---|---|---|
| EFI system partition | existing (shared with Windows) | FAT | mounted by bootupd when needed |
| Microsoft reserved, Windows | unchanged | NTFS | — |
| Apex `/boot` | ≥ 1 GiB, 2 GiB recommended | ext4, **not encrypted** | `/boot` (read-only) |
| Apex root | the rest of the space for Apex | LUKS2 → btrfs, subvolumes `root` and `var` | `/` (subvol `root`), `/var` (subvol `var`) |

Why this layout:

- `/boot` holds up to three kernel and initramfs sets during an update, plus a pinned
  Fedora 45 set after the first major upgrade. GRUB must read it and write `grubenv`
  in place for boot counting (ADR 0009), which does not work on btrfs or an encrypted
  filesystem.
- LUKS2 has a **passphrase and a recovery key**. bootc's own `tpm2-luks` option is not
  used: it drops passphrase slots and has no recovery key.
- `/var` is its own btrfs subvolume, so it can be snapshotted before a Fedora major
  upgrade. `/var` holds `/var/home`, Flatpaks and all machine state.

The rehearsal SSD gets the same layout with its own new ESP.

Internal disk today (2026-09-23): `nvme0n1p1` ESP (700 MiB partition, 196 MiB FAT
filesystem, 158 MiB free), `p2` Microsoft reserved, `p3` Windows, `p4` Ubuntu (ext4,
the rest of the disk). There is no free space. Before M1.1 the owner decides where the
Apex partitions come from: shrink the Ubuntu partition (offline, from the live USB), or
remove Ubuntu once Apex has passed a week of daily use (ROADMAP M1.1). That decision is
not made here.

## 2. Prerequisites and backups

Prerequisites:

- A promoted, signed image: `ghcr.io/sekirokenjii/apex:45` exists and its digest is
  listed in the promotion run of `qualify.yml`.
- The real signing keys are committed: in your checkout,
  `grep -rlx APEX-PLACEHOLDER-NOT-A-KEY image/system_files/usr/share/apex/keys` prints
  nothing, and the pull requests that added the keys state their fingerprints.
- A second USB stick with a copy of this repository at the commit you trust (the
  trust bootstrap reads the policy and keys from it).
- For the rehearsal: an external USB SSD of at least 64 GB that may be erased.
- AC power for the whole procedure.
- The audio measurements of M0.5 are committed (`[audio.measurements]` in
  `hardware/m7400qc/profile.toml`). They need Windows; do them before you change the
  internal disk.

Backups (from the running Ubuntu, before the internal install; cheap enough to do
before the rehearsal too). `<BACKUP_DIR>` is on an external drive:

```sh
# 1. Personal data
sudo rsync -aHAX --info=progress2 /home/ <BACKUP_DIR>/home/
# 2. The EFI system partition, the firmware boot entries and the partition table
sudo tar --create --file=<BACKUP_DIR>/esp-$(date +%F).tar --directory=/boot/efi .
sudo efibootmgr -v > <BACKUP_DIR>/efibootmgr-$(date +%F).txt
sudo sgdisk --backup=<BACKUP_DIR>/gpt-$(date +%F).bin <INTERNAL_DISK>
lsblk -o NAME,SIZE,FSTYPE,UUID,PARTUUID,PARTLABEL > <BACKUP_DIR>/lsblk-$(date +%F).txt
```

3. **Windows BitLocker recovery key.** In Windows, an administrator prompt:
   `manage-bde -protectors -get C:`, or your Microsoft account's recovery-key page.
   Write it down offline. Firmware boot-order changes and Secure Boot changes can make
   Windows ask for it.
4. Check the backups: `tar --list --file=<BACKUP_DIR>/esp-<date>.tar | grep -i microsoft/boot/bootmgfw.efi`
   prints the Windows boot manager, and the `home` copy opens.

Plan where the LUKS **passphrase** and the **recovery key** will be kept (a password
manager plus paper in a separate place). Losing both loses the data.

**Windows clock (dual boot), once, while you are in Windows.** Apex keeps the hardware
clock (RTC) in UTC. There is no `LOCAL` line in `/etc/adjtime`, so systemd reads the RTC
as UTC. Fedora's `/etc/chrony.conf` has `rtcsync`, so once chronyd has synchronised the
clock, the kernel copies the system time into the RTC every 11 minutes, in UTC. Windows
reads the RTC as local time by default. After Apex has run, Windows then shows a time
that is off by the UTC offset (7 hours in Asia/Ho_Chi_Minh). When Windows corrects its
clock, it writes local time back, and Apex runs 7 hours fast until chronyd has network
and steps the clock. Ubuntu on this laptop already keeps the RTC in UTC (`timedatectl`
shows `RTC in local TZ: no`), so if Windows shows the right time after Ubuntu has run,
the setting below is probably in place already. Tell Windows that the RTC is UTC, in an
administrator Command Prompt:

```bat
reg query "HKLM\SYSTEM\CurrentControlSet\Control\TimeZoneInformation" /v RealTimeIsUniversal
reg add "HKLM\SYSTEM\CurrentControlSet\Control\TimeZoneInformation" /v RealTimeIsUniversal /t REG_DWORD /d 1 /f
reg query "HKLM\SYSTEM\CurrentControlSet\Control\TimeZoneInformation" /v RealTimeIsUniversal
```

The first `reg query` shows whether the value is already there (otherwise it reports
that it cannot find it). `reg add` prints "The operation completed successfully.", and
the last `reg query` must show `RealTimeIsUniversal    REG_DWORD    0x1`. Restart
Windows, then press "Sync now" once under Settings > Time & language > Date & time.
From then on Windows reads and writes the RTC as UTC. Microsoft does not document this
value on Microsoft Learn; it is the long-standing dual-boot setting
([Arch Wiki: UTC in Microsoft Windows](https://wiki.archlinux.org/title/System_time#UTC_in_Microsoft_Windows)).
To undo it:
`reg delete "HKLM\SYSTEM\CurrentControlSet\Control\TimeZoneInformation" /v RealTimeIsUniversal /f`.
Keep `/v RealTimeIsUniversal` in that command: without it, `reg delete` removes the
whole `TimeZoneInformation` key.

Apex does not switch Linux to a local-time RTC (`timedatectl set-local-rtc 1`), for
three reasons:

- timedatectl(1) itself says a local-time RTC is not fully supported, causes problems
  with time-zone changes and daylight-saving adjustments, and should be avoided. A UTC
  RTC stays correct when you travel.
- Ubuntu on this laptop keeps the RTC in UTC. While both are installed, a local-time Apex
  and a UTC Ubuntu would each rewrite the RTC in their own way.
- The switch is a machine-local line in `/etc/adjtime`. Apex keeps `/etc` at the image
  defaults apart from the few files ARCHITECTURE §7.3 lists, and a setting that only
  Windows needs belongs in Windows.

## 3. Rehearsal on an external USB SSD

Do §4 to §8 with the USB SSD as `<TARGET_DISK>` and the whole-disk layout of §5.1. Then
boot the SSD from the firmware boot menu (Esc while the ASUS logo shows) and run
[hardware/ACCEPTANCE.md](hardware/ACCEPTANCE.md). Only when it passes, repeat §4 to §8
for the internal disk with the layout of §5.2.

The rehearsal does not touch the internal disk. It only adds a firmware boot entry
for the SSD (§10 removes it).

## 4. Live USB

1. Download Fedora Workstation 45 Live for x86_64 and its `CHECKSUM` file from
   fedoraproject.org, and verify them as Fedora documents:

   ```sh
   curl -O https://fedoraproject.org/fedora.gpg
   gpgv --keyring ./fedora.gpg Fedora-Workstation-45-*-x86_64-CHECKSUM
   sha256sum -c --ignore-missing Fedora-Workstation-45-*-x86_64-CHECKSUM
   ```

2. Write it to the stick with Fedora Media Writer or GNOME Disks ("Restore Disk
   Image").
3. Boot it: Esc at the ASUS logo, pick the stick's UEFI entry, "Try Fedora". Leave
   Secure Boot as it is.
4. Connect to Wi-Fi, open a terminal and become root: `sudo -i`.
5. Tools: `cryptsetup --version; btrfs --version; podman --version; sgdisk --version;
   skopeo --version; cosign version`. Install what is missing with
   `dnf install gdisk skopeo` (Fedora-signed packages). For cosign, use Fedora's package
   if `dnf info cosign` finds one; otherwise download `cosign-linux-amd64` from the
   v3.1.x release on github.com/sigstore/cosign and check it against that release's
   `cosign_checksums.txt` before use.
6. Check SELinux is on: `getenforce` prints `Enforcing` (the `/var` step in §8 relies
   on it).

## 5. Partitions and filesystems

Identify the target and set the placeholders once, in the root shell:

```sh
lsblk -d -o NAME,SIZE,MODEL,TRAN,SERIAL        # the USB SSD shows TRAN=usb
TARGET_DISK=/dev/<target-disk>                  # CHECK MODEL, SIZE AND SERIAL TWICE
```

### 5.1 Rehearsal SSD (whole disk)

```sh
sgdisk --zap-all "$TARGET_DISK"                 # ERASES THE WHOLE DISK
sgdisk --new=1:0:+600M --typecode=1:ef00 --change-name=1:"EFI system partition" \
       --new=2:0:+2G   --typecode=2:8300 --change-name=2:apex-boot \
       --new=3:0:0     --typecode=3:8304 --change-name=3:apex-root "$TARGET_DISK"
lsblk -o NAME,SIZE,PARTLABEL "$TARGET_DISK"
ESP_PART=/dev/<partition 1>; BOOT_PART=/dev/<partition 2>; ROOT_PART=/dev/<partition 3>
mkfs.vfat -F 32 -n EFI "$ESP_PART"
```

### 5.2 Internal disk (existing ESP, free space prepared)

The free space must already exist (§1). Nothing here moves or resizes a partition.

```sh
sgdisk --print "$TARGET_DISK"                   # note the free space at the end
sgdisk --new=0:0:+2G --typecode=0:8300 --change-name=0:apex-boot "$TARGET_DISK"
sgdisk --new=0:0:0   --typecode=0:8304 --change-name=0:apex-root "$TARGET_DISK"
lsblk -o NAME,SIZE,FSTYPE,PARTLABEL "$TARGET_DISK"
ESP_PART=/dev/<existing ESP>; BOOT_PART=/dev/<new apex-boot>; ROOT_PART=/dev/<new apex-root>
```

Partition number `0` means "the first free number" and start `0` means the start of
the largest free block (sgdisk(8)). Do **not** format the existing ESP.

### 5.3 `/boot`, LUKS2 and btrfs (both cases)

```sh
mkfs.ext4 -L apex-boot "$BOOT_PART"
cryptsetup luksFormat --type luks2 --label apex-root "$ROOT_PART"   # type YES, then the passphrase
cryptsetup open "$ROOT_PART" apex-root
systemd-cryptenroll --recovery-key "$ROOT_PART"                     # asks for the passphrase, prints the recovery key
cryptsetup luksDump "$ROOT_PART"                                    # Keyslots 0 and 1; Tokens: systemd-recovery
mkfs.btrfs -L apex /dev/mapper/apex-root
mkdir -p /mnt/btrfs && mount -o subvolid=5 /dev/mapper/apex-root /mnt/btrfs
btrfs subvolume create /mnt/btrfs/root
btrfs subvolume create /mnt/btrfs/var
btrfs subvolume create /mnt/btrfs/install-tmp                       # temporary container storage
```

Write the recovery key down now and test it once:
`cryptsetup open --test-passphrase "$ROOT_PART"` and type the recovery key.

Mount the target, and put the live system's container storage on the target disk
(the live system keeps its own changes in RAM, which is too small for the image):

```sh
mkdir -p /mnt/apex
mount -o subvol=root /dev/mapper/apex-root /mnt/apex
mkdir /mnt/apex/boot && mount "$BOOT_PART" /mnt/apex/boot
mkdir /mnt/apex/boot/efi && mount "$ESP_PART" /mnt/apex/boot/efi
mkdir -p /var/lib/containers && mount -o subvol=install-tmp /dev/mapper/apex-root /var/lib/containers
findmnt -R /mnt/apex
```

`bootc install to-filesystem` requires the target root to be empty apart from mount
points; `/mnt/apex` now holds only the `boot` mount.

## 6. Trust bootstrap

Both documented bootstrap paths are trust-on-first-use unless the live system knows
Apex's keys before it pulls anything. Install the policy and keys **from your trusted
copy of the repository**, check the key fingerprints, and pull only by digest.

```sh
SRC=<mount point of the second USB stick>/apex-fedora          # trusted checkout
F=$SRC/image/system_files
install -D -m 0644 $F/usr/share/apex/keys/release.pub         /usr/share/apex/keys/release.pub
install -D -m 0644 $F/usr/share/apex/keys/release-backup.pub  /usr/share/apex/keys/release-backup.pub
install -D -m 0644 $F/usr/share/apex/keys/ci.pub              /usr/share/apex/keys/ci.pub
install -D -m 0644 $F/usr/share/apex/containers/policy.json   /usr/share/apex/containers/policy.json
install -D -m 0644 $F/usr/share/containers/registries.d/apex.yaml /etc/containers/registries.d/apex.yaml
[ -e /etc/containers/policy.json ] && cp -a /etc/containers/policy.json /etc/containers/policy.json.live-orig
install -m 0644 /usr/share/apex/containers/policy.json /etc/containers/policy.json
grep -lx APEX-PLACEHOLDER-NOT-A-KEY /usr/share/apex/keys/*.pub  # must print nothing
```

Check the fingerprints over two independent channels:

```sh
for k in release release-backup; do
    printf '%-15s ' "$k"; openssl pkey -pubin -in /usr/share/apex/keys/$k.pub -outform DER | sha256sum
done
# the same key as GitHub serves it, at the commit you trust:
curl -fsSL https://raw.githubusercontent.com/sekirokenjii/apex-fedora/<COMMIT>/image/system_files/usr/share/apex/keys/release.pub |
    openssl pkey -pubin -outform DER | sha256sum
```

All three must equal the fingerprints recorded in the pull requests that added the
keys (`image/system_files/usr/share/apex/keys/README.md`). If anything differs,
**stop**.

The strict policy is now the live system's policy. Prove it rejects foreign images:

```sh
podman pull quay.io/fedora/fedora:45          # must FAIL: rejected by policy
```

Choose the digest. Take it from the promotion run of `qualify.yml` (the release
record), then confirm the registry agrees and the version is the one you expect:

```sh
IMG=ghcr.io/sekirokenjii/apex
DIGEST=sha256:<digest from the promotion run>
skopeo inspect --format '{{.Digest}} {{index .Labels "org.opencontainers.image.version"}}' docker://$IMG:45
cosign verify --key /usr/share/apex/keys/release.pub "$IMG@$DIGEST"
```

Expect `skopeo` to print the same digest (it may be newer if a promotion happened since;
then use the newer one and repeat). `cosign verify` must exit 0 and report that the
claims were validated and the signature was verified against the specified public key.
An image signed in an emergency with the backup key verifies with
`--key /usr/share/apex/keys/release-backup.pub` instead (RECOVERY.md §6).

Pull by digest (the policy checks the signature again) and inspect the image:

```sh
podman pull "$IMG@$DIGEST"
podman run --rm "$IMG@$DIGEST" cat /usr/share/apex/manifest.json | python3 -c \
    'import json,sys; m=json.load(sys.stdin); print(m["version"], "degraded:", m["degraded"])'
podman run --rm "$IMG@$DIGEST" sh -c 'lsinitrd /usr/lib/modules/*/initramfs.img | grep -c systemd-cryptsetup'
```

The last command must print at least 1: without `systemd-cryptsetup` in the initramfs
the LUKS root cannot be opened at boot. If it prints 0, stop and report it against the
image.

## 7. Install

```sh
LUKS_UUID=$(cryptsetup luksUUID "$ROOT_PART")
podman run --rm --privileged --pid=host --ipc=host \
    --security-opt label=type:unconfined_t \
    -v /dev:/dev -v /var/lib/containers:/var/lib/containers -v /mnt/apex:/target \
    "$IMG@$DIGEST" \
    bootc install to-filesystem \
        --enforce-container-sigpolicy \
        --target-imgref "$IMG:45" \
        --karg "rd.luks.uuid=$LUKS_UUID" \
        --skip-finalize \
        /target
```

What each option does (bootc-install-to-filesystem(8), bootc 1.16):

- `--enforce-container-sigpolicy`: the installed origin is `ostree-image-signed:`, so
  later pulls require a signature policy (the image's install config sets the same).
- `--target-imgref "$IMG:45"`: updates follow the `45` tag. Without it the installed
  system would stay pinned to the digest used for the install.
- `--karg rd.luks.uuid=…`: the initramfs opens the LUKS root. bootc adds
  `root=UUID=<btrfs>`, `rootflags=subvol=/root` and `boot=UUID=<boot>` itself, plus the
  image's kargs from `/usr/lib/bootc/kargs.d/10-apex.toml` (`rhgb quiet panic=10
  rd.shell=0 rd.emergency=reboot`, the dGPU blacklist, `systemd.ssh_auto=no`).
- `--skip-finalize`: bootc would otherwise remount the target read-only and freeze it;
  §8 still has to write to it.
- Do **not** set `CONTAINERS_POLICY_JSON` and do **not** pass `--run-fetch-check`:
  bootc reads the source from local container storage, which the strict policy has no
  scope for. The signature was checked when you pulled.

bootc installs shim and GRUB through bootupd: it adds `EFI/fedora/` to the ESP,
replaces the fallback loader `EFI/BOOT/BOOTX64.EFI` (and `fbx64.efi`), writes the static
`/boot/grub2/grub.cfg` with the Apex boot-count snippet, and creates a firmware boot
entry named after the image's `/etc/system-release` at the front of the boot order.
Windows' `EFI/Microsoft/` is not touched.

## 8. `/var` subvolume, then unmount

bootc created `/var` inside the root subvolume (`ostree/deploy/default/var`). Move its
content to the `var` subvolume and mount that at `/var`:

```sh
STATEROOT=/mnt/btrfs/root/ostree/deploy/default
DEPLOY=$(ls -d "$STATEROOT"/deploy/*.0)          # exactly one directory
cp -a --reflink=always "$STATEROOT/var/." /mnt/btrfs/var/
chcon --reference="$STATEROOT/var" /mnt/btrfs/var
ls -Zd "$STATEROOT/var" /mnt/btrfs/var           # same context on both
BTRFS_UUID=$(blkid -s UUID -o value /dev/mapper/apex-root)
echo "UUID=$BTRFS_UUID /var btrfs subvol=/var 0 0" >> "$DEPLOY/etc/fstab"
cat "$DEPLOY/etc/fstab"                          # the /boot line bootc wrote, plus /var
```

With `/var` listed in `/etc/fstab`, ostree does not bind-mount its own copy (its
generator skips `/var` when fstab has it), so the copy left in the stateroot is unused.
You may delete it after the first successful boot.

Unmount and close:

```sh
sync
umount -R /var/lib/containers                    # -R: also what an interrupted podman left mounted below it
btrfs subvolume delete /mnt/btrfs/install-tmp
umount /mnt/apex/boot/efi /mnt/apex/boot /mnt/apex /mnt/btrfs
cryptsetup close apex-root
```

## 9. First boot

1. Reboot and remove the live USB. For the SSD, pick it in the firmware boot menu.
2. The GRUB menu shows for 1 s, then the LUKS passphrase prompt appears.
3. GNOME Initial Setup creates your account. On the Typing page, add
   "Vietnamese (Telex)" if you want it; the image already offers it.
4. Check, in a terminal:

```sh
apexctl status                                   # booted digest = $DIGEST; "Channel    stable (running image)"
sudo bootc status                                # image ghcr.io/sekirokenjii/apex:45, signed transport
cat /proc/cmdline                                # has rd.luks.uuid=… root=UUID=… rootflags=subvol=/root rhgb quiet panic=10 …, in any order
findmnt /var; findmnt /boot                      # /var: btrfs [/var]; /boot: ext4, ro
sudo grep -c '^# apex-bootcount v1' /boot/grub2/grub.cfg   # 1 (grub.cfg is mode 0600)
sudo grub2-editenv /boot/grub2/grubenv list      # apex_ok=0; no apex_target, no apex_counter
systemctl --failed                               # 0 loaded units listed
sudo cryptsetup luksDump /dev/<apex-root partition> | grep -A2 Tokens   # systemd-recovery
timedatectl                                      # RTC in local TZ: no; once online: System clock synchronized: yes
```

   GRUB writes `apex_ok=0` at every boot. The boot assessment writes `apex_ok=1` only
   after the green boot of an applied (armed) update
   ([ACCEPTANCE 8.3](hardware/ACCEPTANCE.md#8-updates)); after an ordinary boot it
   writes nothing. Other variables in the list are not Apex's. If `apex_ok` is missing,
   the Apex GRUB snippet did not run or could not write grubenv, and boot counting
   cannot work: stop and find out why.

   `RTC in local TZ: yes` means something set a local-time RTC: undo it with
   `sudo timedatectl set-local-rtc 0` and set up Windows as §2 describes. If the first
   boot seems to hang behind the splash, watch it in text mode (RECOVERY.md §1, "Watch
   a boot in text mode").

5. Back up the boot files Apex added: the ESP (mount it first, it is not mounted by
   default) and the static GRUB configuration, which bootupd never regenerates
   (RECOVERY.md §5):

   ```sh
   sudo mount -o ro /dev/<ESP> /boot/efi
   sudo tar --create --file=<BACKUP_DIR>/esp-apex-$(date +%F).tar --directory=/boot/efi .
   sudo umount /boot/efi
   sudo cp /boot/grub2/grub.cfg <BACKUP_DIR>/grub.cfg
   ```

6. Run [hardware/ACCEPTANCE.md](hardware/ACCEPTANCE.md).

Windows is not in the GRUB menu (bootupd's static configuration has no os-prober).
Start it from the firmware boot menu (Esc at the ASUS logo, "Windows Boot Manager").
Do not add a GRUB chainload entry for Windows: it changes what the TPM measures, and
BitLocker would ask for its recovery key.

## 10. Undoing an installation attempt

**Rehearsal SSD:** unplug it. Remove its firmware boot entry from any Linux:

```sh
sudo efibootmgr                                  # find the entry that points at the SSD
sudo efibootmgr --bootnum <XXXX> --delete-bootnum
```

**Internal disk**, from the live USB (§4):

1. Restore the ESP files that bootupd replaced, from the backup taken in §2:
   RECOVERY.md §5.1 (file-level restore; it also removes `EFI/fedora/`).
2. Delete the firmware boot entry bootupd created (as above), and restore the boot
   order you saved in `efibootmgr-<date>.txt`:
   `efibootmgr --bootorder <XXXX>,<YYYY>,…`
3. Remove the Apex partitions (**check the numbers against `lsblk` first**):
   `sgdisk --delete=<apex-root number> --delete=<apex-boot number> <TARGET_DISK>`.
4. If Ubuntu's partition was shrunk for the install, grow it back offline
   (`sgdisk` to recreate the partition with the same start sector, then
   `e2fsck -f` and `resize2fs`), or restore from the §2 backups.

If the partition table itself is damaged, `sgdisk --load-backup=<BACKUP_DIR>/gpt-<date>.bin
<INTERNAL_DISK>` restores the saved one. That overwrites the current table: use it only
when the table is broken, never to undo a working change.
