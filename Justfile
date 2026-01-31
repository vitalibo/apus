[group: 'modules']
mod apus-shared "apus-shared/Justfile"
[group: 'modules']
mod apus-api "apus-api/Justfile"
[group: 'modules']
mod apus-cli "apus-cli/Justfile"

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
    just apus-cli::format {{ args }}

# run code style checks
check *args:
    just apus-shared::check {{ args }}
    just apus-api::check {{ args }}
    just apus-cli::check {{ args }}
    uv run pre-commit run --files $(git diff --name-only)

# run unit tests
test:
    just apus-shared::test
    just apus-api::test
    just apus-cli::test

# run unit tests with coverage
coverage *args:
    just apus-shared::coverage {{ args }}
    just apus-api::coverage {{ args }}
    just apus-cli::coverage {{ args }}

# clean workdir
clean:
    just apus-shared::clean
    just apus-api::clean
    just apus-cli::clean
    rm -rf ./cdk.out
