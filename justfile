# Lists the available recipes.
default:
    @just --list

# Checks Markdown against the Google documentation style guide.
lint:
    npx --yes markdownlint-cli2@0.24.1 "**/*.md"
