# Apex Linux

Apex is a desktop Linux distribution: an image-based Fedora system with a
GNOME desktop built to the Apex design. It targets ordinary x86_64
computers and treats visual quality as a requirement.

This repository holds the specification, the engineering standards and the
issue tracker. The code lives in the component repositories.

## Status

Apex is being rebuilt from scratch. Nothing is installable yet. The current
milestone is **M0: It boots**; see the [specification](docs/spec.md).

## Repositories

| Repository | Produces |
| --- | --- |
| [`apex`](https://github.com/apex-linux/apex) | Specification, standards, issues |
| [`apex-image`](https://github.com/apex-linux/apex-image) | The OS image and installer media |
| [`apex-hardware`](https://github.com/apex-linux/apex-hardware) | Hardware rules and acceptance checks |
| [`apex-desktop`](https://github.com/apex-linux/apex-desktop) | Design tokens, Shell extension, themes, icons |

## Documents

*   [Specification](docs/spec.md): goals, architecture, reference machine,
    milestones.
*   [Engineering standards](docs/engineering.md): style, source control,
    commit messages, CI, and how to keep the development machine safe.

## Working on this repository

```bash
just lint
```

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
