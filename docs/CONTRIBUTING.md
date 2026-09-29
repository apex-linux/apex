# Contributing

## Code explains itself

This is a standing rule for every line of code from now on, not a cleanup done once and
forgotten.

- Names and structure carry the meaning: precise names, small functions, and named
  constants and types instead of explanatory comments.
- A comment is only for a why the code cannot say: an upstream bug or version quirk, a
  safety or security constraint, or a non-obvious external contract. One or two lines.
- No comment restates the code.
- No essays or usage blocks in file headers. Usage text belongs in a `usage()` or
  `--help` that the code prints.
- No "§N" references to documents in code.
- No tests that assert comment text.
- SPDX lines stay.

## The comment guard

`apex-lint` (`crates/apex-lint`) holds every change to the rule. ci.yml runs it in the
Rust job, and `just check` runs it too. A guard failure is a failing check.

| Rule           | Fails when                                                                  |
| -------------- | --------------------------------------------------------------------------- |
| `block`        | more than 2 comment lines with no code between them; blank lines do not split a block, except that the file's header comment ends at its first blank line |
| `density`      | in a file of 40 or more non-blank lines, comments are above 8% of them      |
| `unterminated` | the file ends inside a string, block comment, here-document or spec-edit block, so the guard cannot classify its lines |

A comment line is a line whose first non-blank characters are its language's comment
marker:

- `#`: shell, Python, TOML, YAML, RPM spec, Justfile, Containerfile, Makefile,
  meson.build, systemd units and drop-ins, udev rules, GRUB snippets, keyfiles, `.env`,
  patch `series`, spec-edit, ignore files and the package and allow lists (`.txt`).
- `//` and `/* */`, with `///` and `//!`: Rust, JavaScript (polkit rules included) and
  SCSS. A Rust `#[doc = "..."]` or `#![doc = "..."]` attribute is a doc comment too.
- A here-document that an interpreter runs is lexed as that interpreter's code, so its
  comments count: `python3 - <<'PY'`, `bash -s <<EOF`, `RUN <<EOF` in a Containerfile,
  and a here-document whose first line is a shebang (a script being written).

These are not comment lines:

- a shebang, also a Justfile recipe's;
- the SPDX line and one bare comment line after it;
- Containerfile parser directives at the top;
- the one comment line directly above a Justfile recipe, which `just --list` prints;
- tool directives, which neither count nor split a block: `shellcheck`,
  `eslint-disable`, `eslint-enable`, `renovate:`, `pylint:` and `prettier-ignore`;
- lines of a here-document that is data (`cat >file <<EOF`, a `while` loop's input);
- lines inside multi-line strings and template literals;
- the text lines of a spec-edit block (between `after` or `replace` and `end`), which
  are content of the edited spec;
- SCSS loud comments (`/*! */`), which stay in the compiled CSS.

The guard does not see trailing comments (`code # why`), comments inside a multi-line
quoted program (`jq '...'`, `awk '...'`) or Python docstrings. The rule still applies to
them.

Out of scope, as not authored here or not code: `design/mockup/`, test data
(`tests/fixtures/`, `tests/golden/`), Markdown, patches, insta snapshots, `Cargo.lock`,
JSON, SVG and XML.

## Running it

```bash
just lint-comments                       # every git-tracked file in scope
just lint-comments image/ Justfile       # files, or the git-listed files of directories
cargo run -p apex-lint --locked -- comments --json
```

Each violation prints as `path:line: rule: message`. To fix one, rename, extract or
delete until the code says it; keep only the why, in one or two lines.

To check that a comment cleanup changed nothing but comments, compare the file without
its comment lines before and after:

```bash
cargo run -q -p apex-lint -- strip FILE >before
# edit FILE
cargo run -q -p apex-lint -- strip FILE >after
diff -B before after
```
