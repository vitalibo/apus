[group: 'modules']
mod apus-shared "apus-shared/Justfile"
[group: 'modules']
mod apus-api "apus-api/Justfile"

# show available recipes
default:
    @just --list

# install dependencies
install:
    uv sync --locked --all-packages --all-extras --dev

# run code formatter
format *args:
    just apus-shared::format {{ args }}
    just apus-api::format {{ args }}

# run code style checks
style *args:
    just apus-shared::style {{ args }}
    just apus-api::style {{ args }}
    uv run pre-commit run --files $(git diff --name-only)

# run unit tests
test:
    just apus-shared::test
    just apus-api::test

# clean workdir
clean:
    just apus-shared::clean
    just apus-api::clean
