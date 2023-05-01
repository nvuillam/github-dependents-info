# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] 2023-05-01

- Fix crash _ValueError: invalid literal for int() with base 10: '1\nRepository'_
- Upgrade dependencies
- Enable more linters in MegaLinter

## [1.0.0] 2023-06-04

- Add functionality for saving results to csv files, by @finlaymacklon in <https://github.com/nvuillam/github-dependents-info/pull/195>
- Upgrade dependencies

## [O.10.0] 2023-04-01

- Upgrade dependencies

## [O.9.0] 2023-02-05

- Add requests to requirements.txt by @edenlightning in <https://github.com/nvuillam/github-dependents-info/pull/127>
- Upgrade python dependencies

## [O.8.0] 2022-12-28

- New option `--markdownbadgecolor` to override default shields.io informational color
- Upgrade python dependencies

## [O.7.2] 2022-11-20

- Fix markdown hyperlink when package name contains arobase character
- Fix internal release CI

## [O.7.1] 2022-11-20

- Update documentation and add example of output markdown with angular/angular repo

## [O.7.0] 2022-11-17

- Fix cases when dependents count is superior to 1000 ([#27](https://github.com/nvuillam/github-dependents-info/issues/27))
- Internal CI
  - Fix release drafter
  - Update stale config
  - Remove useless greetings job

## [0.6.0] 2022-11-15

- New option `--mergepackages` to have all dependent repos in a single table in output markdown file
- Fix documentation

## [0.5.0] 2022-11-14

- Reformat json output to have `packages` and `all_dependent_repos` properties
- New option `--badgemarkdownfile` to insert/update an **Used by** badge in README.md or other markdown files between HTML tags `<!-- gh-dependents-info-used-by-start --><!-- gh-dependents-info-used-by-end -->`
- New option `--minstars` to filter repo with less than a number of stars
- Enhance documentation and add more examples
- Replace print() by logging python library

## [0.4.1] 2022-11-13

- Add version and downloads badges in README

## [0.4.0] 2022-11-13

- Fix documentation
- Fix CLI --repo argument

## [0.1.0] 2022-11-13

Initial version
