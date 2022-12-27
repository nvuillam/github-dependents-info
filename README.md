# github-dependents-info

<div align="center">

[![PyPI](https://img.shields.io/pypi/v/github-dependents-info)](https://pypi.org/project/github-dependents-info/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/github-dependents-info)](https://pypi.org/project/github-dependents-info/)
[![GitHub stars](https://img.shields.io/github/stars/nvuillam/github-dependents-info?cacheSeconds=3600)](https://github.com/nvuillam/github-dependents-info/stargazers/)
[![Build status](https://github.com/nvuillam/github-dependents-info/workflows/build/badge.svg?branch=main&event=push)](https://github.com/nvuillam/github-dependents-info/actions?query=workflow%3Abuild)
[![Python Version](https://img.shields.io/pypi/pyversions/github-dependents-info.svg)](https://pypi.org/project/github-dependents-info/)
[![Dependencies Status](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen.svg)](https://github.com/nvuillam/github-dependents-info/pulls?utf8=%E2%9C%93&q=is%3Apr%20author%3Aapp%2Fdependabot)

[![MegaLinter](https://github.com/nvuillam/github-dependents-info/workflows/MegaLinter/badge.svg?branch=main)](https://oxsecurity.github.io/megalinter)
[![License](https://img.shields.io/github/license/nvuillam/github-dependents-info)](https://github.com/nvuillam/github-dependents-info/blob/master/LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

Collect information about dependencies between a github repo and other repositories.

</div>

_________________
## 🚀 Features

GitHub API does not allow to collect information about package usage (**Used by** on home, **Dependents** in insights section)

This package uses GitHub HTML to collect dependents information and can:

- Output as text
- Output as json (including shields.io markdown badges)
- Generate summary markdown file
- Update existing markdown by inserting **Used by** badge within tags
  - `<!-- gh-dependents-info-used-by-start --><!-- gh-dependents-info-used-by-end -->`
- Handle multiple repositories packages
- Filter results using minimum stars

Badges example

[![](https://img.shields.io/static/v1?label=Used%20by&message=15&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)
[![](https://img.shields.io/static/v1?label=Used%20by%20(public)&message=11&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)
[![](https://img.shields.io/static/v1?label=Used%20by%20(private)&message=4&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)
[![](https://img.shields.io/static/v1?label=Used%20by%20(stars)&message=56&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)

<details>
  <summary>JSON output</summary>

```json
{
    "all_public_dependent_repos": [
        {
            "name": "CIT-SeniorDesign/CIT-SeniorDesign.github.io",
            "stars": 0
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
            "name": "RecuencoJones/vscode-groovy-lint-issue",
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
            "name": "aboe026/software-update-checker",
            "stars": 2
        },
        {
            "name": "katalon-labs/katalon-recorder-extension",
            "stars": 0
        },
        {
            "name": "mashafrancis/sa-jenkins",
            "stars": 0
        },
        {
            "name": "nvuillam/vscode-groovy-lint",
            "stars": 52
        },
        {
            "name": "run2cmd/dotfiles",
            "stars": 2
        }
    ],
    "packages": [
        {
            "id": null,
            "name": "nvuillam/npm-groovy-lint",
            "url": "https://github.com/nvuillam/npm-groovy-lint/network/dependents",
            "public_dependent_stars": 56,
            "public_dependents": [
                {
                    "name": "CIT-SeniorDesign/CIT-SeniorDesign.github.io",
                    "stars": 0
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
                    "name": "RecuencoJones/vscode-groovy-lint-issue",
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
                    "name": "aboe026/software-update-checker",
                    "stars": 2
                },
                {
                    "name": "katalon-labs/katalon-recorder-extension",
                    "stars": 0
                },
                {
                    "name": "mashafrancis/sa-jenkins",
                    "stars": 0
                },
                {
                    "name": "nvuillam/vscode-groovy-lint",
                    "stars": 52
                },
                {
                    "name": "run2cmd/dotfiles",
                    "stars": 2
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
</details>

<details>
  <summary>Markdown output for single package</summary>

```markdown
# Dependents stats for nvuillam/npm-groovy-lint

## Package nvuillam/npm-groovy-lint

[![](https://img.shields.io/static/v1?label=Used%20by&message=15&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)
[![](https://img.shields.io/static/v1?label=Used%20by%20(public)&message=11&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)
[![](https://img.shields.io/static/v1?label=Used%20by%20(private)&message=4&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)
[![](https://img.shields.io/static/v1?label=Used%20by%20(stars)&message=56&color=informational&logo=slickpic)](https://github.com/nvuillam/npm-groovy-lint/network/dependents)

| Repository                                                                                                    | Stars |
|:--------------------------------------------------------------------------------------------------------------|------:|
| [CIT-SeniorDesign/CIT-SeniorDesign.github.io](https://github.com/CIT-SeniorDesign/CIT-SeniorDesign.github.io) |     0 |
| [Moaz-Adel/Jobsity-Challenge](https://github.com/Moaz-Adel/Jobsity-Challenge)                                 |     0 |
| [Moaz-Adel/automation-exercise-cypress](https://github.com/Moaz-Adel/automation-exercise-cypress)             |     0 |
| [RecuencoJones/vscode-groovy-lint-issue](https://github.com/RecuencoJones/vscode-groovy-lint-issue)           |     0 |
| [aboe026/data-structures](https://github.com/aboe026/data-structures)                                         |     0 |
| [aboe026/shields.io-badge-results](https://github.com/aboe026/shields.io-badge-results)                       |     0 |
| [aboe026/software-update-checker](https://github.com/aboe026/software-update-checker)                         |     2 |
| [katalon-labs/katalon-recorder-extension](https://github.com/katalon-labs/katalon-recorder-extension)         |     0 |
| [mashafrancis/sa-jenkins](https://github.com/mashafrancis/sa-jenkins)                                         |     0 |
| [nvuillam/vscode-groovy-lint](https://github.com/nvuillam/vscode-groovy-lint)                                 |    52 |
| [run2cmd/dotfiles](https://github.com/run2cmd/dotfiles)                                                       |     2 |

_Generated by [github-dependents-info](https://github.com/nvuillam/github-dependents-info)_
```
</details>

Note: If your repository packages have millions of dependents, running github-dependent-infos could take hours, as it works by browsing and scraping HTML pages returned by GitHub. For example, [angular/angular dependents](assets/angular-package-usage.md) did run during several hours !
_________________
## ⚙️ Installation

```bash
pip install -U github-dependents-info
```

or install with `Poetry`

```bash
poetry add github-dependents-info
```

_________________
## 🛠️ Usage

```shell
    github-dependents-info [OPTIONS]
```

| Parameter                   | Type    | Description                                                                                                                                                                              |
|-----------------------------|---------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| --repo                      | String  | Repository. Example: `oxsecurity/megalinter`                                                                                                                                             |
| -b<br/> --badgemarkdownfile | String  | _(optional)_ Path to markdown file where to insert/update **Used by** badge <br/> (must contain tags `<!-- gh-dependents-info-used-by-start --><!-- gh-dependents-info-used-by-end -->`) |
| -s<br/> --sort              | String  | _(optional)_ Sort order: name (default) or stars                                                                                                                                         |
| -x<br/> --minstars          | String  | _(optional)_ If set, filters repositories to keep only those with more than X stars                                                                                                      |
| -m<br/> --markdownfile      | String  | _(optional)_ Output markdown file file                                                                                                                                                   |
| -p<br/> --mergepackages     | String  | _(optional)_ In case of multiple packages, merge their stats in a single one in markdown and json output                                                                                 |
| -j<br/> --json              | String  | _(optional)_ Output in json format                                                                                                                                                       |
| -v<br/> --version           | Boolean | _(optional)_ Displays version of github-dependents-info                                                                                                                                  |
| --verbose                   | Boolean | _(optional)_ Verbose output                                                                                                                                                              |

_________________
## 🧪 Examples

- Text output

      github-dependents-info --repo nvuillam/npm-groovy-lint

- JSON output

      github-dependents-info --repo nvuillam/npm-groovy-lint --json

- Insert/Update **Used by** markdown badge within an existing markdown file containing tags `<!-- gh-dependents-info-used-by-start --><!-- gh-dependents-info-used-by-end -->`

      github-dependents-info --repo nvuillam/npm-groovy-lint --badgemarkdownfile ./README.md

- Build markdown file with dependent repos (single package), sorted by name

      github-dependents-info --repo nvuillam/npm-groovy-lint --markdownfile ./docs/package-usage.md --verbose

- Build markdown file with dependent repos (single package), with minimum 10 stars

      github-dependents-info --repo nvuillam/npm-groovy-lint --markdownfile ./docs/package-usage.md --minstars 10 --verbose

- Build markdown file with dependent repos (multiple package), sorted by stars

      github-dependents-info --repo oxsecurity/megalinter --markdownfile ./docs/package-usage.md --sort stars --verbose

- Build markdown file with dependent repos (multiple package), with merged list of packages in output markdown

      github-dependents-info --repo oxsecurity/megalinter --markdownfile ./docs/package-usage.md --sort stars --mergepackages --verbose

_________________
## 🛡 License

[![License](https://img.shields.io/github/license/nvuillam/github-dependents-info)](https://github.com/nvuillam/github-dependents-info/blob/master/LICENSE)

This project is licensed under the terms of the `MIT` license. See [LICENSE](https://github.com/nvuillam/github-dependents-info/blob/master/LICENSE) for more details.

_________________
## Credits [![🚀 Your next Python package needs a bleeding-edge project structure.](https://img.shields.io/badge/python--package--template-%F0%9F%9A%80-brightgreen)](https://github.com/TezRomacH/python-package-template)

This package has been inspired by stackexchange post [How to use GitHub API to get a repository's dependents information in GitHub?](https://stackoverflow.com/questions/58734176/how-to-use-github-api-to-get-a-repositorys-dependents-information-in-github)
- [Bertrand Martel](https://github.com/bertrandmartel)
- [muvaf](https://stackoverflow.com/users/5233252/muvaf)
- [Mo Ganji](https://www.linkedin.com/in/mohganji/) <!-- markdown-link-check-disable-line -->

This project was generated with [`python-package-template`](https://github.com/TezRomacH/python-package-template)
