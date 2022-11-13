# github-dependents-info

<div align="center">

[![Build status](https://github.com/nvuillam/github-dependents-info/workflows/build/badge.svg?branch=master&event=push)](https://github.com/nvuillam/github-dependents-info/actions?query=workflow%3Abuild)
[![Python Version](https://img.shields.io/pypi/pyversions/github-dependents-info.svg)](https://pypi.org/project/github-dependents-info/)
[![Dependencies Status](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen.svg)](https://github.com/nvuillam/github-dependents-info/pulls?utf8=%E2%9C%93&q=is%3Apr%20author%3Aapp%2Fdependabot)

[![MegaLinter](https://github.com/nvuillam/github-dependents-info/workflows/MegaLinter/badge.svg?branch=master)](https://oxsecurity.github.io/megalinter)
[![License](https://img.shields.io/github/license/nvuillam/github-dependents-info)](https://github.com/nvuillam/github-dependents-info/blob/master/LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

Collect information about dependencies between a github repo and other repositories. Results available in JSON, markdown and badges.

</div>

## 🚀 Features

## Installation

```bash
pip install -U github-dependents-info
```

or install with `Poetry`

```bash
poetry add github-dependents-info
```

## Usage

```shell
    github-dependents-info [OPTIONS]
```

| Parameter              | Type    | Description                                           |
|------------------------|---------|-------------------------------------------------------|
| --repo                 | String  | Repository. Example: `oxsecurity/megalinter`          |
| -m<br/> --markdownfile | String  | (optional) Output markdown file file                  |
| -j<br/> --json         | String  | (optional) Output in json format                      |
| -v<br/> --version      | Boolean | (optional) Displays version of github-dependents-info |
| --verbose              | Boolean | (optional) Verbose output                             |

## Examples

Text output

`github-dependents-info --repo nvuillam/npm-groovy-lint`

JSON output

`github-dependents-info --repo nvuillam/npm-groovy-lint --json`

Build markdown file with dependent repos (single package)

`github-dependents-info --repo nvuillam/npm-groovy-lint --markdownfile ./assets/package-usage.md --verbose`

Build markdown file with dependent repos (multiple package)

`github-dependents-info --repo oxsecurity/megalinter --markdownfile ./assets/package-usage.md --verbose`

## 🛡 License

[![License](https://img.shields.io/github/license/nvuillam/github-dependents-info)](https://github.com/nvuillam/github-dependents-info/blob/master/LICENSE)

This project is licensed under the terms of the `MIT` license. See [LICENSE](https://github.com/nvuillam/github-dependents-info/blob/master/LICENSE) for more details.

## Credits [![🚀 Your next Python package needs a bleeding-edge project structure.](https://img.shields.io/badge/python--package--template-%F0%9F%9A%80-brightgreen)](https://github.com/TezRomacH/python-package-template)

This project was generated with [`python-package-template`](https://github.com/TezRomacH/python-package-template)
