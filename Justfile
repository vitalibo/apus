[group: 'modules']
mod apus-shared "apus-shared/Justfile"
[group: 'modules']
mod apus-api "apus-api/Justfile"

# show available recipes
default:
    @just --list

# install dependencies
sync:
    uv sync --locked --all-packages --dev

# run code formatter
format *args:
    just apus-shared::format {{ args }}
    just apus-api::format {{ args }}

# run code style checks
check *args:
    just apus-shared::check {{ args }}
    just apus-api::check {{ args }}
    uv run pre-commit run --files $(git diff --name-only)

# run unit tests
test:
    just apus-shared::test
    just apus-api::test

# clean workdir
clean:
    just apus-shared::clean
    just apus-api::clean
