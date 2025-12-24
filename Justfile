[group: 'modules']
mod apus-shared "apus-shared/Justfile"
[group: 'modules']
mod apus-api "apus-api/Justfile"

# show available recipes
default:
    @just --list

# run code formatter
format:
    just apus-shared::format
    just apus-api::format

# run code style checks
style:
    just apus-shared::style
    just apus-api::style

# run unit tests
test:
    just apus-shared::test
    just apus-api::test

# clean workdir
clean:
    just apus-shared::clean
    just apus-api::clean
