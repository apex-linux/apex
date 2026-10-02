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
yourself. `bootc install to-disk` is not used on the laptop: it would wipe the Ubuntu
install, which stays as the fallback.

| Partition | Size | Content | Mounted at |
|---|---|---|---|
| EFI system partition | existing (shared with Ubuntu) | FAT | mounted by bootupd when needed |
| Apex `/boot` | ≥ 1 GiB, 2 GiB recommended | ext4, **not encrypted** | `/boot` (read-only) |
| Apex root | the rest of the space for Apex | LUKS2 → btrfs, subvolumes `root` and `var` | `/` (subvol `root`), `/var` (subvol `var`) |
| Ubuntu | unchanged | ext4 | — |

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

Internal disk on 2026-09-29, after the owner deleted Windows (ROADMAP W1), in 512-byte
sectors (`/sys/block/nvme0n1/nvme0n1p*/start` and `size`; 1953525168 sectors in all):

| Partition | Start | Sectors | Size | Content |
|---|---|---|---|---|
| `nvme0n1p1` | 2048 | 1433600 | 700 MiB | ESP: a 196 MiB FAT filesystem, 189 MiB free; `EFI/ubuntu/` and `EFI/Boot/` |
| free | 1435648 | 901615616 | 429.9 GiB | where Apex goes (§5.2, ROADMAP W2) |
| `nvme0n1p4` | 903051264 | 1050470400 | 500.9 GiB | Ubuntu, ext4 |

Nothing is shrunk or moved. Ubuntu stays as the fallback and the builder host until
Apex has passed its two weeks of daily use (ROADMAP S4). Its partition starts right
after the free space, so once Ubuntu is gone the Apex root can grow into it.

## 2. Prerequisites and backups

Prerequisites:

- A published, signed image: `ghcr.io/sekirokenjii/apex:45` exists, and its digest is
  the one `just publish` printed in the builder VM (S1d).
- The real signing keys are committed: in your checkout,
  `grep -rlx APEX-PLACEHOLDER-NOT-A-KEY image/system_files/usr/share/apex/keys` prints
  nothing, and the pull requests that added the keys state their fingerprints.
- A second USB stick with a copy of this repository at the commit you trust (the
  trust bootstrap reads the policy and keys from it).
- For the rehearsal: an external USB SSD of at least 64 GB that may be erased.
- AC power for the whole procedure.
- No Windows entry in the firmware boot entries (below).

**The stale Windows entry (ROADMAP W1).** Deleting Windows removed its files, not its
firmware boot entry, which then points at the deleted
`\EFI\MICROSOFT\BOOT\BOOTMGFW.EFI`. From Ubuntu (reading the entries needs no `sudo`):

```sh
efibootmgr | grep -i 'windows boot manager'      # nothing printed: nothing to remove, skip the rest
efibootmgr > ~/efibootmgr-before-w1.txt          # the entries as they were
n=$(efibootmgr | sed -n 's/^Boot\([0-9A-Fa-f]\{4\}\)[* ] Windows Boot Manager.*/\1/p')
printf '%s\n' "$n"                               # exactly one four-digit number, e.g. 0000
case $n in
    [0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]) sudo efibootmgr --bootnum "$n" --delete-bootnum ;;
    *) echo "not exactly one Windows entry: nothing deleted" ;;
esac
efibootmgr                                       # no Windows line, and BootOrder no longer lists that number
```

The number comes from the entry's label, not from an assumption: check that `printf`
printed one number and that the line of the first command carries it. The `case`
deletes only a single four-digit number: `efibootmgr --bootnum ""` would mean
`Boot0000`, which after an Apex install is usually Apex's own entry. If `printf`
printed two numbers, there are two Windows entries: run
`sudo efibootmgr --bootnum <number> --delete-bootnum` once per number, typed by hand.
`--delete-bootnum` also removes the number from `BootOrder` (efibootmgr 18,
`delete_var` in `src/efibootmgr.c`).

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

3. Check the backups: `tar --list --file=<BACKUP_DIR>/esp-<date>.tar | grep -i ubuntu/shimx64.efi`
   prints Ubuntu's shim, and the `home` copy opens.

Plan where the LUKS **passphrase** and the **recovery key** will be kept (a password
manager plus paper in a separate place). Losing both loses the data.

Apex keeps the hardware clock (RTC) in UTC, as Ubuntu on this laptop does (`timedatectl`
shows `RTC in local TZ: no`), so the two agree on the time.

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
   Secure Boot off, as it was on 2026-09-28. Apex's CachyOS kernel (S1c) is signed for
   Secure Boot only from the optional step W3, so with Secure Boot on it would not
   boot. The install enrols no MOK (ADR 0015 §7).
4. Connect to Wi-Fi, open a terminal and become root: `sudo -i`.
5. Tools: `cryptsetup --version; btrfs --version; podman --version; sgdisk --version;
   skopeo --version; cosign version`. Install what is missing with
   `dnf install gdisk skopeo` (Fedora-signed packages). For cosign, use Fedora's package
   if `dnf info cosign` finds one; otherwise download `cosign-linux-amd64` from the
   v3.1.x release on github.com/sigstore/cosign and check it against that release's
   `cosign_checksums.txt` before use.
6. Check SELinux is on: `getenforce` prints `Enforcing` (the `/var` step in §8 relies
   on it). Check Secure Boot is off: `mokutil --sb-state` prints `SecureBoot disabled`
   (`dnf install mokutil` if it is missing).

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

The free space already exists (§1). Nothing here moves or resizes a partition.

```sh
sgdisk --print "$TARGET_DISK"                   # partitions 1 and 4 only, as in §1; the gap between them
sgdisk --new=0:0:+2G --typecode=0:8300 --change-name=0:apex-boot "$TARGET_DISK"
sgdisk --new=0:0:0   --typecode=0:8304 --change-name=0:apex-root "$TARGET_DISK"
sgdisk --print "$TARGET_DISK"                   # 2 apex-boot from 1435648; 3 apex-root from 5629952 to 903051263
lsblk -o NAME,SIZE,FSTYPE,PARTLABEL "$TARGET_DISK"
ESP_PART=/dev/<existing ESP>; BOOT_PART=/dev/<new apex-boot>; ROOT_PART=/dev/<new apex-root>
```

Partition number `0` means "the first free number" and start `0` means the start of
the largest free block, end `0` its end (sgdisk(8)). With the §1 table that gives
`nvme0n1p2` apex-boot (2 GiB) and `nvme0n1p3` apex-root (897421312 sectors, 427.9 GiB),
the root ending on the sector before Ubuntu's partition; these numbers are worked out
from §1, not yet seen on the disk. If `sgdisk` prints other numbers, stop. Do **not**
format the existing ESP.

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

Choose the digest. Take it from the output of `just publish` in the builder VM (S1d),
then confirm the registry agrees and the version is the one you expect:

```sh
IMG=ghcr.io/sekirokenjii/apex
DIGEST=sha256:<digest from just publish>
skopeo inspect --format '{{.Digest}} {{index .Labels "org.opencontainers.image.version"}}' docker://$IMG:45
cosign verify --key /usr/share/apex/keys/release.pub "$IMG@$DIGEST"
```

Expect `skopeo` to print the same digest (it may be newer if `just publish` ran since;
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
  image's kargs from `/usr/lib/bootc/kargs.d/10-apex.toml` (`rhgb quiet panic=10`, the
  dGPU blacklist, `systemd.ssh_auto=no`).
- `--skip-finalize`: bootc would otherwise remount the target read-only and freeze it;
  §8 still has to write to it.
- Do **not** set `CONTAINERS_POLICY_JSON` and do **not** pass `--run-fetch-check`:
  bootc reads the source from local container storage, which the strict policy has no
  scope for. The signature was checked when you pulled.

bootc installs shim and GRUB through bootupd: it adds `EFI/fedora/` to the ESP,
replaces the fallback loader `EFI/BOOT/BOOTX64.EFI` (and `fbx64.efi`), writes the static
`/boot/grub2/grub.cfg` with the Apex boot-count snippet, and creates a firmware boot
entry named after the image's `/etc/system-release` at the front of the boot order.

What that does to Ubuntu (sources in ARCHITECTURE §5.5):

- `EFI/ubuntu/` and Ubuntu's firmware entry are not touched. Ubuntu's entry becomes
  second in the boot order and still starts Ubuntu from the firmware boot menu.
- Each `shim-signed` or GRUB package update on Ubuntu puts Ubuntu's entry first again,
  whatever debconf says. When the laptop starts Ubuntu on its own after you updated
  Ubuntu, put Apex back in front, from either system:

  ```sh
  efibootmgr                                     # BootOrder, and the numbers of "Fedora" and "Ubuntu"
  sudo efibootmgr --bootorder <Fedora>,<Ubuntu>,<the rest as listed>
  ```

- The fallback loader was Ubuntu's shim and is now Fedora's. Ubuntu's next GRUB package
  update puts its own shim back there, and a later Apex image with a new shim replaces
  it again. Both work: the fallback path is used only when no boot entry works, and
  either shim's fallback then recreates the entries of both systems.
- From then on `bootloader-update.service` keeps bootupd's files in `EFI/fedora/` and
  `EFI/BOOT/` current from the booted image, once per boot and only after
  `apex-boot-assess` has judged that boot green (ARCHITECTURE §5.5). It creates no
  firmware entry and does not reorder them.

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
systemctl is-enabled bootloader-update.service   # enabled
systemctl is-active apex-boot-assess.service    # active: the boot assessment has finished
systemctl show -p ActiveState -p Result bootloader-update.service   # then ActiveState=active, Result=success
sudo bootupctl status                            # Component EFI, Installed: grub2-1:2.12-…,shim-16.1-…; Update: At latest version
sudo cryptsetup luksDump /dev/<apex-root partition> | grep -A2 Tokens   # systemd-recovery
timedatectl                                      # RTC in local TZ: no; once online: System clock synchronized: yes
```

   GRUB writes `apex_ok=0` at every boot. The boot assessment writes `apex_ok=1` only
   after the green boot of an applied (armed) update
   ([ACCEPTANCE 8.3](hardware/ACCEPTANCE.md#8-updates)); after an ordinary boot it
   writes nothing. Other variables in the list are not Apex's. If `apex_ok` is missing,
   the Apex GRUB snippet did not run or could not write grubenv, and boot counting
   cannot work: stop and find out why.

   `Result=exec-condition` for `bootloader-update.service` means the assessment did not
   judge this boot green, so the ESP was left alone.
   `journalctl -b -u bootloader-update.service` says why, and
   `journalctl -b -u apex-boot-assess.service` which check failed.

   `RTC in local TZ: yes` means something set a local-time RTC: undo it with
   `sudo timedatectl set-local-rtc 0`. If the first boot seems to hang behind the
   splash, watch it in text mode (RECOVERY.md §1, "Watch a boot in text mode").

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

Ubuntu is not in the GRUB menu (bootupd's static configuration has no os-prober).
Start it from the firmware boot menu (Esc at the ASUS logo, "Ubuntu").

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
   The space is free again, and Ubuntu's partition was never touched.

If the partition table itself is damaged, `sgdisk --load-backup=<BACKUP_DIR>/gpt-<date>.bin
<INTERNAL_DISK>` restores the saved one. That overwrites the current table: use it only
when the table is broken, never to undo a working change.

## 11. BIOS updates without Windows

MyASUS and Windows Update no longer deliver BIOS updates. The two remaining paths, as
checked on 2026-09-29:

| Path | State |
|---|---|
| fwupd and LVFS | Not available. Ubuntu's fwupd sees the BIOS as an updatable UEFI capsule device ("System Firmware", version 785), but `fwupdmgr get-updates` lists it under "Devices with no available firmware updates": the LVFS metadata of 2026-09-28 has no entry for its GUID, and an LVFS search for `M7400QC` finds nothing. |
| ASUS EZ Flash | The path to use. ASUS publishes "BIOS for ASUS EZ Flash Utility" files for the M7400QC. The newest is 311 (2023-07-07, `M7400QCAS311.zip`, 7.63 MB), and the laptop already runs it (`cat /sys/class/dmi/id/bios_version` prints `M7400QC.311`). |

Not checked on this unit: that its setup screen offers the EZ Flash item. Look once
without changing anything: hold F2 and press the power button, open the Advanced
screen, find "ASUS Firmware Update" (or "ASUS EZ Flash 3 Utility"), then leave with
Esc and discard changes.

To see whether LVFS has gained this model, on Ubuntu (Ubuntu's `fwupd-refresh.timer`
refreshes the metadata): `fwupdmgr get-updates`. "System Firmware" under "Devices with
no available firmware updates" means it has not.

An update with EZ Flash, following ASUS's FAQ
([How to update BIOS with ASUS Firmware Update/EZ Flash](https://www.asus.com/support/faq/1008859/),
updated 2026-04-22):

1. From the M7400QC support page, "BIOS & FIRMWARE", download the file titled "BIOS
   for ASUS EZ Flash Utility", not "BIOS Update for Windows".
2. Check it: `sha256sum M7400QCAS<version>.zip` must equal the SHA-256 ASUS gives for
   the download (ASUS's support API returns one per file; for 311 it is
   `45ca4f62b680a1069b17704043f58947864ec063d0a710d4d5544a7e7f52a9d4`). Unzip it.
3. Put the extracted file on a USB stick with a FAT32 filesystem; ASUS requires FAT32:

   ```sh
   lsblk -o NAME,SIZE,MODEL,TRAN,FSTYPE           # the stick shows TRAN=usb; CHECK MODEL AND SIZE
   sudo mkfs.vfat -F 32 -n BIOS /dev/<stick partition>   # ERASES that partition
   udisksctl mount -b /dev/<stick partition>      # prints where it is mounted
   cp <extracted BIOS file> <mount point>/
   udisksctl unmount -b /dev/<stick partition>
   efibootmgr > ~/efibootmgr-before-bios.txt      # the boot entries, to compare afterwards
   ```

4. Connect AC; the battery must be at 20 % or more. Power off.
5. Hold F2 and press the power button. On the Advanced screen choose "ASUS Firmware
   Update" (or "ASUS EZ Flash 3 Utility"), then the stick and the file, and confirm.
   Do not power off while it writes; the laptop restarts by itself.
6. Afterwards, from Apex or Ubuntu: `cat /sys/class/dmi/id/bios_version` shows the new
   version, `mokutil --sb-state` still prints `SecureBoot disabled`, and `efibootmgr`
   matches `~/efibootmgr-before-bios.txt`. Whether this BIOS resets setup options or
   boot entries on update was not checked. If entries are missing, the firmware starts
   `EFI/BOOT/BOOTX64.EFI`, whose fallback recreates the Apex and Ubuntu entries
   (ARCHITECTURE §5.5); restore the order with `sudo efibootmgr --bootorder …`
   (RECOVERY.md §5.3). Then run [hardware/ACCEPTANCE.md](hardware/ACCEPTANCE.md) §1
   and §9.
