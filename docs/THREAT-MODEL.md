# Threat model

This is a proportionate model for a single-user, single-laptop distribution. Controls
are named by the document that implements them.

## Assets

- The owner's data on the laptop.
- The integrity of the operating system and the boot chain on the laptop.
- The signing keys: the release key, the CI key and the offline backup key. From M2, a
  MOK if one is ever introduced.
- The GitHub account and the ghcr.io packages it owns. The Fedora (FAS) account, once
  COPR is used.
- Biometric data: fingerprint images and templates. A leaked fingerprint cannot be
  revoked.

## Trusted roots

- Fedora infrastructure and its package and signing keys.
- The owner's GitHub account, protected with hardware-key 2FA.
- The laptop's UEFI firmware.

## Threats in scope

| # | Threat | Controls |
|---|---|---|
| T1 | Theft or loss of the powered-off laptop | LUKS2 with a passphrase and a recovery key (ADR 0010) |
| T2 | Code running as the desktop user (browser, npm, an agent) tries to escalate through apex-updated, polkit or sudo | The polkit action table; the daemon reads no user files and exposes no writable properties; bootc argv comes from enums only; fingerprint is kept out of `system-auth` (ADR 0006, ADR 0008) |
| T3 | Compromise of one upstream input (a crate, an npm package, a GitHub Action or a third-party repository) that tries to steal CI secrets or persist | Actions pinned by SHA; no third-party actions in jobs that hold secrets; build jobs hold no secrets; M1 has no third-party RPM repositories; `cargo deny`; a CI scan of image layers for private keys; build-provenance attestations on cached RPM artifacts, verified before reuse |
| T4 | A compromised GitHub token or workflow tries to push, sign or retag images | Separate testing and release repositories and keys; the `release` environment requires manual approval; versions must increase; a staleness warning; the offline backup key for recovery (ADR 0012) |
| T5 | An attacker on the network or at the registry | Signature enforcement through a strict policy file under `/usr` (ADR 0012) |
| T6 | Leakage of biometric data during diagnostics | Diagnostics only in tmpfs; a CI guard against image and template files; redaction of hardware dumps (ADR 0006) |

## Accepted risks and out of scope

- **An attacker with repeated physical access** (evil maid). ostree with GRUB does not
  verify the initramfs, the kernel arguments or `/usr`. This needs the composefs and
  sealed-UKI track, which is future work.
- **Firmware or hardware implants.**
- **GitHub and ghcr.io seeing daily update checks.**
- **Fedora infrastructure compromise.**

## Incident runbooks

These live in `docs/RECOVERY.md` and cover:

- a leaked CI or release key: rotate, and sign an emergency image with the offline
  backup key;
- a compromised GitHub account or token: audit the tags, rotate the secrets;
- a compromised COPR account (M2);
- a leaked MOK (only if one is introduced).
