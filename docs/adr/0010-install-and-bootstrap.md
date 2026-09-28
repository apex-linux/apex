# ADR 0010: First install and bootstrap on the only laptop

Status: proposed (2026-09-24). The partition plan needs the owner's decision.

## Context

The target laptop is also the development machine. It runs Ubuntu 26.04 and dual-boots
Windows, and Windows is needed for the ADR 0004 COEF measurements. `bootc install
to-disk --wipe` would destroy both. `bootc switch` works only from an ostree or bootc
system. Both documented bootstrap paths trust the first image on first use (TOFU).
bootc's built-in `tpm2-luks` option drops passphrase slots and has no recovery key.

## Decision

- **Supported path:** `bootc install to-filesystem` onto a disk laid out in advance:
  - keep Windows and share its ESP;
  - an ext4 `/boot` of at least 1 GiB;
  - LUKS2 with a passphrase plus a recovery key (FIDO2 optional later);
  - btrfs inside it, with `/var` as its own subvolume, so snapshots are possible before
    a major upgrade.
- **Where to run it:** from a live USB, or from an Apex installer ISO once
  `image-builder bootc-generic-iso` is wired up (M2). The first rehearsal installs onto
  an external USB SSD, so the internal disk is untouched until Apex has passed the
  hardware acceptance tests.
- **Trust bootstrap:**
  1. Install the Apex policy and public key into the live environment first.
  2. Verify the key fingerprint against this git repository.
  3. Install by digest after `cosign verify`, with `--enforce-container-sigpolicy`.
- **Before the internal install:** back up `/home` and the Windows recovery key.
  Enrolling a MOK is not needed at M1, because there are no Apex Secure Boot keys.
- **Recovery** (`docs/RECOVERY.md`):
  - reaching the rollback entry despite the static GRUB menu's 1 s timeout;
  - `bootc rollback` from a live USB;
  - restoring the ESP.

## Consequences

- There is no automated destructive step anywhere in Apex tooling. `INSTALL.md` is a
  runbook the owner follows.
