# ADR 0012: Trust, keys and repositories

Status: superseded by ARCHITECTURE §4 and §5.1 (2026-09-28), and amended by
[ADR 0015](0015-cachyos-kernel-and-nvidia.md): its Secure Boot keys and third-party
repositories clauses are replaced by ADR 0015 §3, §5 and §7. The threat model is in
`docs/THREAT-MODEL.md`.

## Decision

- **Two repositories and two signing keys.**
  - `ghcr.io/apex-linux/apex-testing` is signed by a **CI key** held in the GitHub
    environment `testing`.
  - `ghcr.io/apex-linux/apex` is signed by a **release key** held in the environment
    `release`, which is restricted to `main` and needs manual approval.

  Qualification means membership in `apex`: the promotion job copies a qualified digest
  with `skopeo copy --preserve-digests` and signs it with the release key. There is no
  "qualified" label, because a label would change the digest.
- **Offline backup key.** Generated offline, encrypted, never stored in GitHub. It is
  listed in the laptop's policy next to the release key.
  - **Planned rotation:** image N adds the new key, N+1 signs with it, N+2 removes the
    old one.
  - **Compromise:** build an emergency image whose policy lists [backup, new-backup] and
    sign it locally with the backup key.
- **Client policy.** Every bootc call made by `apex-updated` runs with
  `CONTAINERS_POLICY_JSON=/usr/share/apex/containers/policy.json`:
  - default `reject`;
  - `sigstoreSigned` for exactly the two Apex repositories, each with its own keys;
  - no transport-level accept rules.

  The file lives in `/usr`, so a local edit to `/etc` cannot freeze it against a key
  rotation. `registries.d` enables sigstore attachments for `ghcr.io/apex-linux`, and
  the install config sets `enforce-container-sigpolicy = true`.
- **Monotonic versions.** The daemon refuses to apply a staged image whose manifest
  version is not higher than the booted one, unless the user explicitly confirms a
  downgrade. Promotion refuses to move a tag backwards. The UI warns when stable has not
  moved for 7 days.
- **cosign.** Legacy `.sig` format (`--new-bundle-format=false
  --use-signing-config=false`), because containers/image cannot verify the new bundle
  format yet. Rekor upload stays on, for leak detection; it is not required by the
  policy.
- **Secure Boot keys: none at M1.** The stock Fedora-signed kernel and no out-of-tree
  modules mean shim and Fedora keys cover the boot chain. A MOK is introduced only with
  the M2 NVIDIA or kernel work, under a separate decision covering:
  - offline generation;
  - signing in an isolated job that receives only the artifacts to sign;
  - dual-sign rotation;
  - an incident runbook using `mokutil --mokx`.
- **Third-party repositories: none at M1.** When NVIDIA arrives (negativo17), the repo
  key is committed and its fingerprint checked, `includepkgs` names exactly the needed
  packages, and NEVRAs and hashes are locked and bumped by reviewed PR. scx-scheds from
  a third-party COPR is not shipped.
- **Disk encryption:** LUKS2 with a passphrase and a recovery key (ADR 0010).
