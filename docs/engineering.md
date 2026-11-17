# Engineering standards

These rules apply to every repository in the `apex-linux` organization. What
we are building is in [spec.md](spec.md).

## Principles

1.  **Working software first.** A change is valuable when the image boots
    and the thing works on real hardware. Process, documents and tooling
    exist only to serve that.
2.  **Small changes, merged daily.** One purpose per pull request.
3.  **Fast checks.** CI for a pull request finishes in under ten minutes.
4.  **Copy what works.** Before inventing a workflow or a tool, look at how
    [Pop!_OS](https://github.com/pop-os) does it and do that.

## Style

Follow the [Google style guides](https://google.github.io/styleguide/)
exactly. The formatter and linter settings below implement them; where a
tool and a guide disagree, the guide wins.

| Language | Guide | Format | Lint |
| --- | --- | --- | --- |
| Rust | [rustguide](https://google.github.io/styleguide/rustguide.html) | `rustfmt`, `max_width = 100` | `clippy -D warnings` |
| C and C++ | [cppguide](https://google.github.io/styleguide/cppguide.html) | `clang-format`, `BasedOnStyle: Google` | `clang-tidy`, `cpplint` |
| Go | [go](https://google.github.io/styleguide/go/) | `gofmt` | `golangci-lint` |
| Python | [pyguide](https://google.github.io/styleguide/pyguide.html) | `pyink`, `isort` profile `google` | `pylint`, `mypy --strict` |
| JavaScript | [jsguide](https://google.github.io/styleguide/jsguide.html) | ESLint stylistic rules | ESLint |
| Shell | [shellguide](https://google.github.io/styleguide/shellguide.html) | `shfmt -i 2 -ci -bn` | `shellcheck` |
| Markdown | [docguide](https://google.github.io/styleguide/docguide/style.html) | 80 columns | `markdownlint-cli2` |

Line length is 80 columns, except Rust (100) and Go (no limit).

### Rust

*   Follow the Google Rust guide, and through it the official Rust style
    guide and API guidelines. Rules it tags for Chromium or Fuchsia only do
    not apply.
*   Pin a stable toolchain in `rust-toolchain.toml`. Set only the `rustfmt`
    options that stable supports.
*   No glob imports. Prefer `expect` with a reason over `unwrap`. Every
    `unsafe` block has a `SAFETY:` comment. Public items have doc comments
    (`missing_docs`).

### C and C++

*   The C++ guide also governs C: formatting, naming, header guards, 80
    columns, two-space indentation.
*   File names are lowercase with underscores; tests end in `_test.cc`.

### Go

*   `gofmt` output is mandatory. Exported names have doc comments that start
    with the name. Error strings are lowercase without trailing punctuation.

### Python

*   Python 3.14, managed with `uv`; all tool settings live in
    `pyproject.toml`.
*   Google docstrings (`Args:`, `Returns:`, `Raises:`), type annotations on
    every public API, four-space indentation.
*   Follow the design of
    [etl-pipeline-boilerplate](https://github.com/SekiroKenjii/etl-pipeline-boilerplate):
    ports and adapters, a hand-written composition root, layered settings
    validated at start-up, one error hierarchy with one exit-code table, and
    tests that enforce the import rules between layers.

### JavaScript

*   ES modules, `const` and `let`, single quotes, semicolons, two-space
    indentation, named exports.
*   One exception: a GNOME Shell extension's entry point must be a default
    export, because the Shell loader requires it.

### Shell

*   Bash only, starting with `#!/bin/bash`. Use `[[ ]]`, `$(...)` and quoted
    `"${var}"`. Errors go to standard error. A script with functions has a
    `main`.
*   If a script grows past about a hundred lines or needs data structures,
    write it in Python or Rust instead.

### Markdown

*   One H1 per file, ATX headings, fenced code blocks with a language, no
    trailing whitespace.

### Code we do not own

A patch to an upstream project (GNOME, the kernel, libfprint) follows that
project's style, not ours. Keep patches small and send them upstream.

## Project layout

New code starts from the owner's starter kits. The shape is the same in
every language:

*   **Entry points** (`apps/`, `cmd/`, `entrypoints/`) are composition roots.
    They wire things together and contain no logic.
*   **`kernel`** is the shared vocabulary: pure, no I/O.
*   **`platform`** is technical capability: configuration, logging, OS
    wrappers. It knows nothing about features.
*   **`modules/<name>`** holds one feature each, with a public facade and a
    `contract`, and private `domain`, `application`, `infrastructure` and
    `transport` layers that nothing outside the module may import.
*   **`testkit`** holds shared fixtures and fakes.

Use only the parts a project needs. A repository of shell and data does not
need this structure.

## Source control

We practice
[trunk-based development](https://trunkbaseddevelopment.com/).

*   **Trunk** is `main`. It always builds and passes CI.
*   **Branches** are short-lived: one purpose, one author, merged within two
    days, deleted on merge. Name them `<topic>` in lowercase with hyphens,
    for example `dock-autohide`. Keep one branch in flight per author.
*   **Merging** is squash only, so history is linear and one pull request is
    one commit. The pull request title becomes the commit subject and its
    description becomes the body.
*   **Review** does not gate a merge. Merge when CI is green; the owner
    reviews what landed and asks for a follow-up or a revert. Ask for review
    before merging when a change is hard to undo.
*   **Unfinished work** goes to trunk dark, behind a setting or a build
    argument that defaults to off. It never waits on a long-lived branch.
    Remove the flag once the feature ships.
*   **Releases** are tags on trunk, named `vYY.MM.N`. Cut a release branch
    only when an old release needs a fix: fix on trunk first, then
    cherry-pick to the branch. Release branches never merge back.
*   **A broken trunk** is fixed or reverted before anything else lands.

## Commit messages

Follow [How to Write a Git Commit Message](https://cbea.ms/git-commit/):

1.  Separate subject from body with a blank line.
2.  Limit the subject line to 50 characters. CI rejects a pull request
    title over 65, which leaves room for the number GitHub appends.
3.  Capitalize the subject line.
4.  Do not end the subject line with a period.
5.  Use the imperative mood in the subject line.
6.  Wrap the body at 72 characters.
7.  Use the body to explain what and why, not how.

```text
Power down the NVIDIA GPU when idle

The discrete GPU stayed in D0 because nothing enabled runtime power
management for it. Set power/control to auto for NVIDIA display
controllers so the device reaches D3cold when no client uses it.
```

No type prefixes such as `feat:` or `fix:`.

## Continuous integration

Modeled on Pop!_OS, whose repositories carry one small workflow or none.

*   **One workflow per repository**, `ci.yml`, triggered by pushes to `main`
    and by pull requests.
*   **A few short jobs**: format, lint, test, and for `apex-image` the image
    build. Each job installs its tools and runs a `just` recipe.
*   **CI runs what developers run.** Every check is a `just` recipe that
    works the same on a laptop. CI contains no logic of its own.
*   **The shared convention check** lives in the `.github` repository and is
    called as a job. It checks the pull request title.
*   **Publishing** happens only in `apex-image`, on pushes to `main`.

CI does not do these things: boot matrices in virtual machines, sign-off
gates, cross-repository version pins per change, scheduled workflows, or
storing the output of CI runs in a repository. Adding a second workflow to a
repository needs the owner's agreement.

## Protecting the development machine

Builds run on the owner's laptop, which has 16 GB of memory and a nearly
full disk. A crash costs more than a slow build.

*   **Check before heavy work.** Run `just doctor` before an image build, a
    virtual machine, or a large compile. It refuses to continue with less
    than 25 GB of free disk or 4 GB of available memory.
*   **Clean, then build.** When `just doctor` fails, free space first:
    remove Apex's own old images and build caches. Never delete another
    project's images, volumes or files without asking the owner.
*   **One heavy job at a time.** Heavy recipes take the lock
    `~/.cache/apex/heavy.lock` with `flock`, so two sessions cannot build at
    once.
*   **Stay off `/tmp`.** It is memory-backed. Large files go under
    `~/.cache/apex/` or the repository's ignored `build/` directory.
*   **Bound the load.** Limit build parallelism to half the cores and give a
    virtual machine at most 4 GB of memory.

## Documentation

*   Each repository has a `README.md` that says what it produces and how to
    build and test it.
*   Record a decision only when it is expensive to reverse, as a short file
    in `docs/adr/`. Do not document process.
*   Comments say why. Code that needs a comment to say what should be
    rewritten.
