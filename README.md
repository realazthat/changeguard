<!--

WARNING: This file is auto-generated by snipinator. Do not edit directly.
SOURCE: `README.md.jinja2`.

-->
<!--


-->

# ChangeGuard

![Top language][9] ![GitHub License][3] [![PyPI - Version][4]][5]
[![Python Version][8]][5]

|         | Status                     | Stable                    | Unstable                  |                    |
| ------- | -------------------------- | ------------------------- | ------------------------- | ------------------ |
| Master  | [![Build and Test][1]][2]  | [![since tagged][6]][10]  |                           | ![last commit][7]  |
| Develop | [![Build and Test][11]][2] | [![since tagged][12]][13] | [![since tagged][15]][16] | ![last commit][14] |

CLI to check if your repository/directory files have changed over the span of a
script.

## What

Like hashdeep, but customized to check if any of the original files in a
repository/directory change over the course of a precommit script.

## Features

- Can use any sha256sum-like command (uses xxhash by default).
- Use `.changeguard-ignore` to ignore files that should not be checked for
  changes.

## Getting Started

### Install

#### Tested on

- WSL2 Ubuntu 20.04, Python 3.8.0
- Ubuntu 20.04, Python 3.8.0, 3.9.0, 3.10.0, 3.11.0, 3.12.0, tested in GitHub
  Actions workflow
  ([build-and-test.yml](./.github/workflows/build-and-test.yml)).

**Requirements:**

- Linux-like environment
  - Why: Uses pexpect.spawn().
- Python 3.8+
  - Why: Some dev dependencies require Python 3.8+.

```bash
# Install from pypi (https://pypi.org/project/changeguard/)
pip install changeguard

# Install from git (https://github.com/realazthat/changeguard)
pip install git+https://github.com/realazthat/changeguard.git@v0.3.0
```

### Use

## Contributions

### Development environment: Linux-like

- For running `pre.sh` (Linux-like environment).
  - Requires `pyenv`, or an exact matching version of python as in
    [`.python-version`](./.python-version).
  - `nvm` for prettier (markdown formatting).
  - `bash`, `grep`, `xxd`, `git`, `xxhash` (for scripts/workflows/tests).
  - `jq`, ([installation](https://jqlang.github.io/jq/)) required for
    [yq](https://github.com/kislyuk/yq), which is itself required for our
    `README.md` generation, which uses `tomlq` (from the
    [yq](https://github.com/kislyuk/yq) package) to include version strings from
    `pyproject.toml`.
  - Requires `nodejs` (for act).
  - Requires `go` (to run act).
  - `docker` (for act).

### Commit Process

1. (Optionally) Fork the `develop` branch.
2. Stage your files: `git add path/to/file.py`.
3. `bash scripts/pre.sh`, this will format, lint, and test the code.
4. `git status` check if anything changed (generated `README.md` for
   example), if so, `git add` the changes, and go back to the previous step.
5. `git commit -m "..."`.
6. Make a PR to `develop` (or push to develop if you have the rights).

## Release Process

These instructions are for maintainers of the project.

1. `develop` branch: Run `bash scripts/pre.sh` to ensure everything
   is in order.
2. `develop` branch: Bump the version in `pyproject.toml`, following
   semantic versioning principles. Also modify the `last_unstable_release` and
   `last_stable_release` in the `[tool.changeguard-project-metadata]` table as
   appropriate.
3. `develop` branch: Commit these changes with a message like "Prepare release
   X.Y.Z". (See the contributions section [above](#commit-process)).
4. `master` branch: Merge the `develop` branch into the `master` branch:
   `git checkout master && git merge develop --no-ff`.
5. `master` branch: Tag the release: Create a git tag for the release with
   `git tag -a vX.Y.Z -m "Version X.Y.Z"`.
6. Publish to PyPI: Publish the release to PyPI with
   `bash scripts/deploy-to-pypi.sh`.
7. Push to GitHub: Push the commit and tags to GitHub with `git push` and
   `git push --tags`.
8. `git checkout develop && git merge master` The `--no-ff` option adds a commit
   to the master branch for the merge, so refork the develop branch from the
   master branch.
9. `git push origin develop` Push the develop branch to GitHub.

[1]:
  https://github.com/realazthat/changeguard/actions/workflows/build-and-test.yml/badge.svg?branch=master
[2]:
  https://github.com/realazthat/changeguard/actions/workflows/build-and-test.yml
[3]: https://img.shields.io/github/license/realazthat/changeguard
[4]: https://img.shields.io/pypi/v/changeguard
[5]: https://pypi.org/project/changeguard/
[6]:
  https://img.shields.io/github/commits-since/realazthat/changeguard/v0.3.0/master
[7]: https://img.shields.io/github/last-commit/realazthat/changeguard/master
[8]: https://img.shields.io/pypi/pyversions/changeguard
[9]:
  https://img.shields.io/github/languages/top/realazthat/changeguard.svg?&cacheSeconds=28800
[10]:
  https://github.com/realazthat/changeguard/compare/v0.3.0...master
[11]:
  https://github.com/realazthat/changeguard/actions/workflows/build-and-test.yml/badge.svg?branch=develop
[12]:
  https://img.shields.io/github/commits-since/realazthat/changeguard/v0.3.0/develop
[13]:
  https://github.com/realazthat/changeguard/compare/v0.3.0...develop
[14]: https://img.shields.io/github/last-commit/realazthat/changeguard/develop
[15]:
  https://img.shields.io/github/commits-since/realazthat/changeguard/v0.3.0/develop
[16]:
  https://github.com/realazthat/changeguard/compare/v0.3.0...develop
