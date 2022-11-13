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

GitHub API does not allow to collect information about package usage (Used by insights section)

This package uses GitHu:b HTML to collect information and output it as text or json, or generate a markdown file.

JSON example

```json
{
    "public_dependents_repos": [
        {
            "id": null,
            "name": "nvuillam/npm-groovy-lint",
            "url": "https://github.com/nvuillam/npm-groovy-lint/network/dependents",
            "public_dependent_stars": 56,
            "public_dependents": [
                {
                    "name": "nvuillam/vscode-groovy-lint",
                    "stars": 52
                },
                {
                    "name": "run2cmd/dotfiles",
                    "stars": 2
                },
                {
                    "name": "aboe026/software-update-checker",
                    "stars": 2
                },
                {
                    "name": "Moaz-Adel/Jobsity-Challenge",
                    "stars": 0
                },
                {
                    "name": "Moaz-Adel/automation-exercise-cypress",
                    "stars": 0
                },
                {
                    "name": "mashafrancis/sa-jenkins",
                    "stars": 0
                },
                {
                    "name": "katalon-labs/katalon-recorder-extension",
                    "stars": 0
                },
                {
                    "name": "aboe026/data-structures",
                    "stars": 0
                },
                {
                    "name": "aboe026/shields.io-badge-results",
                    "stars": 0
                },
                {
                    "name": "CIT-SeniorDesign/CIT-SeniorDesign.github.io",
                    "stars": 0
                },
                {
                    "name": "RecuencoJones/vscode-groovy-lint-issue",
                    "stars": 0
                }
            ],
            "public_dependents_number": 11,
            "private_dependents_number": 4,
            "total_dependents_number": 15,
            "badges": {
                "total": "[![](https://img.shields.io/static/v1?label=Used%20by&message=15&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)",
                "public": "[![](https://img.shields.io/static/v1?label=Used%20by%20(public)&message=11&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)",
                "private": "[![](https://img.shields.io/static/v1?label=Used%20by%20(private)&message=4&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)",
                "stars": "[![](https://img.shields.io/static/v1?label=Used%20by%20(stars)&message=56&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)"
            }
        }
    ],
    "total_dependents_number": 15,
    "public_dependents_number": 11,
    "private_dependents_number": 4,
    "public_dependents_stars": 56,
    "badges": {
        "total": "[![](https://img.shields.io/static/v1?label=Used%20by&message=15&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)",
        "public": "[![](https://img.shields.io/static/v1?label=Used%20by%20(public)&message=11&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)",
        "private": "[![](https://img.shields.io/static/v1?label=Used%20by%20(private)&message=4&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)",
        "stars": "[![](https://img.shields.io/static/v1?label=Used%20by%20(stars)&message=56&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)"
    }
}
```

Markdown example

```markdown
# Dependents stats for nvuillam/npm-groovy-lint

[![](https://img.shields.io/static/v1?label=Used%20by&message=15&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)
[![](https://img.shields.io/static/v1?label=Used%20by%20(public)&message=11&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)
[![](https://img.shields.io/static/v1?label=Used%20by%20(private)&message=4&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)
[![](https://img.shields.io/static/v1?label=Used%20by%20(stars)&message=56&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)

## Package nvuillam/npm-groovy-lint

[![](https://img.shields.io/static/v1?label=Used%20by&message=15&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)
[![](https://img.shields.io/static/v1?label=Used%20by%20(public)&message=11&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)
[![](https://img.shields.io/static/v1?label=Used%20by%20(private)&message=4&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)
[![](https://img.shields.io/static/v1?label=Used%20by%20(stars)&message=56&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)

| Repository                                                                                                    | Stars |
|:--------------------------------------------------------------------------------------------------------------|------:|
| [nvuillam/vscode-groovy-lint](https://github.com/nvuillam/vscode-groovy-lint)                                 |    52 |
| [run2cmd/dotfiles](https://github.com/run2cmd/dotfiles)                                                       |     2 |
| [aboe026/software-update-checker](https://github.com/aboe026/software-update-checker)                         |     2 |
| [Moaz-Adel/Jobsity-Challenge](https://github.com/Moaz-Adel/Jobsity-Challenge)                                 |     0 |
| [Moaz-Adel/automation-exercise-cypress](https://github.com/Moaz-Adel/automation-exercise-cypress)             |     0 |
| [mashafrancis/sa-jenkins](https://github.com/mashafrancis/sa-jenkins)                                         |     0 |
| [katalon-labs/katalon-recorder-extension](https://github.com/katalon-labs/katalon-recorder-extension)         |     0 |
| [aboe026/data-structures](https://github.com/aboe026/data-structures)                                         |     0 |
| [aboe026/shields.io-badge-results](https://github.com/aboe026/shields.io-badge-results)                       |     0 |
| [CIT-SeniorDesign/CIT-SeniorDesign.github.io](https://github.com/CIT-SeniorDesign/CIT-SeniorDesign.github.io) |     0 |
| [RecuencoJones/vscode-groovy-lint-issue](https://github.com/RecuencoJones/vscode-groovy-lint-issue)           |     0 |

_Generated by [github-dependents-info](https://github.com/nvuillam/github-dependents-info)_
```

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
| -s<br/> --sort         | String  | (optional) Sort order: name (default) or stars        |
| -m<br/> --markdownfile | String  | (optional) Output markdown file file                  |
| -j<br/> --json         | String  | (optional) Output in json format                      |
| -v<br/> --version      | Boolean | (optional) Displays version of github-dependents-info |
| --verbose              | Boolean | (optional) Verbose output                             |

## Examples

Text output

`github-dependents-info --repo nvuillam/npm-groovy-lint`

JSON output

`github-dependents-info --repo nvuillam/npm-groovy-lint --json`

Build markdown file with dependent repos (single package), sorted by name

`github-dependents-info --repo nvuillam/npm-groovy-lint --markdownfile ./assets/package-usage.md --verbose`

Build markdown file with dependent repos (multiple package), sorted by stars

`github-dependents-info --repo oxsecurity/megalinter --markdownfile ./assets/package-usage.md --sort stars --verbose`

## 🛡 License

[![License](https://img.shields.io/github/license/nvuillam/github-dependents-info)](https://github.com/nvuillam/github-dependents-info/blob/master/LICENSE)

This project is licensed under the terms of the `MIT` license. See [LICENSE](https://github.com/nvuillam/github-dependents-info/blob/master/LICENSE) for more details.

## Credits [![🚀 Your next Python package needs a bleeding-edge project structure.](https://img.shields.io/badge/python--package--template-%F0%9F%9A%80-brightgreen)](https://github.com/TezRomacH/python-package-template)

This package has been inspired by stackexchange post [How to use GitHub API to get a repository's dependents information in GitHub?](https://stackoverflow.com/questions/58734176/how-to-use-github-api-to-get-a-repositorys-dependents-information-in-github)
- [Bertrand Martel](https://github.com/bertrandmartel)
- [muvaf](https://stackoverflow.com/users/5233252/muvaf)
- [Mo Ganji](https://linkedin.com/in/mohganji)

This project was generated with [`python-package-template`](https://github.com/TezRomacH/python-package-template)
