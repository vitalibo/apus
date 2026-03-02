[group: 'modules']
mod apus-shared "apus-shared/Justfile"
[group: 'modules']
mod apus-api "apus-api/Justfile"
[group: 'modules']
mod apus-cli "apus-cli/Justfile"
[group: 'modules']
mod apus-monitoring "apus-monitoring/Justfile"

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
    just apus-monitoring::format {{ args }}
    just apus-cli::format {{ args }}

# run code style checks
check *args:
    just apus-shared::check {{ args }}
    just apus-api::check {{ args }}
    just apus-monitoring::check {{ args }}
    just apus-cli::check {{ args }}
    uv run pre-commit run --files $(git diff --name-only)

# run unit tests
test:
    just apus-shared::test
    just apus-api::test
    just apus-monitoring::test
    just apus-cli::test

# run unit tests with coverage
coverage *args:
    just apus-shared::coverage {{ args }}
    just apus-api::coverage {{ args }}
    just apus-monitoring::coverage {{ args }}
    just apus-cli::coverage {{ args }}

# build packages
build *args:
    just apus-shared::build {{ args }}
    just apus-api::build {{ args }}
    just apus-monitoring::build {{ args }}
    just apus-cli::build {{ args }}

# clean workdir
clean:
    just apus-shared::clean
    just apus-api::clean
    just apus-monitoring::clean
    just apus-cli::clean
    rm -rf ./cdk.out
