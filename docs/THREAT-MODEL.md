# Threat model

This is a proportionate model for a single-user, single-laptop distribution. Controls
are named by the document that implements them.

## Assets

- The owner's data on the laptop.
- The integrity of the operating system and the boot chain on the laptop.
- The signing keys: the release key, the CI key and the offline backup key; the Apex
  RPM key (S1a), in the builder VM and on offline media. From step W3, the Apex Secure
  Boot key, if the owner turns Secure Boot on (ADR 0015 §7). No module-signing key
  persists: each kernel build makes its own and shreds it (S1c, ADR 0015 §3).
- The GitHub account and the ghcr.io packages it owns.
- Biometric data: fingerprint images and templates. A leaked fingerprint cannot be
  revoked.

## Trusted roots

- Fedora infrastructure and its package and signing keys.
- From S1c (ADR 0015), three third-party kernel and NVIDIA sources, each with a pinned
  key (fingerprints in ARCHITECTURE §5.1):
  - CachyOS: the signed kernel source tag;
  - the COPR `bieszczaders/kernel-cachyos`: the SRPM Apex rebuilds, including the
    kernel config and the BORE patch it fetches from unpinned URLs;
  - negativo17: the `nvidia-kmod` SRPM and the NVIDIA userspace. The userspace is
    NVIDIA's own binaries, which Apex does not rebuild, so NVIDIA is trusted too.
- The owner's GitHub account, protected with hardware-key 2FA.
- The laptop's UEFI firmware.

## Threats in scope

| # | Threat | Controls |
|---|---|---|
| T1 | Theft or loss of the powered-off laptop | LUKS2 with a passphrase and a recovery key (ADR 0010) |
| T2 | Code running as the desktop user (browser, npm, an agent) tries to escalate through apex-updated, polkit or sudo | The polkit action table; the daemon reads no user files and exposes no writable properties; bootc argv comes from enums only; fingerprint is kept out of `system-auth` (ADR 0006, ADR 0008) |
| T3 | Compromise of one upstream input (a crate, an npm package, a GitHub Action, the CachyOS source, the COPR SRPM or negativo17's packages) that tries to steal secrets or signing keys, or persist | GitHub-hosted jobs run only each repository's `ci.yml`: actions pinned by SHA, a read-only token, and no secret in any job. apex-image's `vm.yml` runs on a self-hosted runner: no `pull_request` trigger, a runner group that accepts only `vm.yml` on `main`, a throwaway rootless container per job whose only secret is its one-job registration, and a way into the builder VM through one forced command that builds a commit of `main`; no signing key or store leaves the VM (`tools/runner/`). `cargo deny`; every image build scans its root filesystem for private keys (`image/checks/secrets.sh`). Apex's RPMs are signed with the Apex RPM key in the builder VM after their build container exits, and no build container mounts the key's GnuPG home; the compose's `[apex]` accepts only that key's and Fedora's signatures (`gpgcheck=1`), and G1 checks that every Apex package carries that key's signature (packaging/README.md, "Signing"). The kernel and NVIDIA inputs (S1c, ADR 0015 §2 to §5): the COPR SRPM and negativo17's SRPM and binaries are checked against their pinned keys, locked by NEVR and sha256, and mirrored at first sight, so the compose never contacts negativo17.org; the CachyOS tag passes `git verify-tag` and must match the SRPM's Source0; the kernel is rebuilt from the signed SRPM, so COPR's build hosts leave the chain; each bump writes a report with the config and BORE-patch diffs, and a config change, a new kernel line or a new driver waits for the owner; the per-build module key lives on a tmpfs and is shredded with its job; from W3, the Apex Secure Boot key reaches only an isolated step that signs `vmlinuz` |
| T4 | A compromised GitHub token or workflow tries to push, sign or retag images | Separate testing and release repositories and keys; the `release` environment requires manual approval; versions must increase; a staleness warning; the offline backup key for recovery (ADR 0012) |
| T5 | An attacker on the network or at the registry | Signature enforcement through a strict policy file under `/usr` (ADR 0012) |
| T6 | Leakage of biometric data during diagnostics | Diagnostics only in tmpfs; a CI guard against image and template files; redaction of hardware dumps (ADR 0006) |

## Accepted risks and out of scope

- **An attacker with repeated physical access** (evil maid). ostree with GRUB does not
  verify the initramfs, the kernel arguments or `/usr`. This needs the composefs and
  sealed-UKI track, which is future work. Secure Boot stays off until the optional
  step W3 (ADR 0015 §7), and even then it covers only shim, GRUB and the kernel.
- **Kernel security latency** (S1c). The CachyOS kernel leaves Fedora's signature and
  Bodhi's gating. In August and September 2026 the COPR built a kernel.org release
  13 to 103 h after it came out, and a release it skipped waited up to about 138 h for
  the next build. Whether CachyOS receives embargoed fixes is unverified. After 72 h
  the owner chooses between waiting and the break-glass image with Fedora's kernel
  (ADR 0015 §4).
- **A compromised negativo17 key** (S1c). Its NVIDIA binaries are not rebuilt, so only
  the owner's review of a lock bump would catch a malicious build.
- **Firmware or hardware implants.**
- **GitHub and ghcr.io seeing daily update checks.**
- **Fedora infrastructure compromise.**

## Incident runbooks

These live in `docs/RECOVERY.md` and cover:

- a leaked CI or release key: rotate, and sign an emergency image with the offline
  backup key;
- a compromised GitHub account or token: audit the tags, rotate the secrets;
- a lost, exposed or rotated Apex RPM key (§6.8);
- a suspect kernel or NVIDIA input: hold the pair, or replace the running kernel with
  the break-glass image (S1c);
- a leaked Apex Secure Boot key: enrol a successor, then revoke the old key with
  `mokutil --mokx` (W3).
