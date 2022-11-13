from typing import Optional

import json
from enum import Enum
from random import choice

import typer
from rich.console import Console

from github_dependents_info import version
from github_dependents_info.gh_dependents_info import GithubDependentsInfo

app = typer.Typer(
    name="github-dependents-info",
    help="Collect information about dependencies between a github repo and other repositories. Results available in JSON, markdown and badges.",
    add_completion=False,
)
console = Console()


def version_callback(print_version: bool) -> None:
    """Print the version of the package."""
    if print_version:
        console.print(f"[yellow]github-dependents-info[/] version: [bold blue]{version}[/]")
        raise typer.Exit()


@app.command(name="")
def main(
    repo: str = typer.Option(..., help="Repository (ex: oxsecurity/megalinter)"),
    markdown_file: str = typer.Option(None, "-m", "--markdownfile", help="Output Markdown file path"),
    json_output: bool = typer.Option(
        False,
        "-j",
        "--json",
        help="Output in JSON format",
    ),
    verbose: bool = typer.Option(
        False,
        "-d",
        "--verbose",
        help="Prints the version of github-dependents-info package",
    ),
    print_version: bool = typer.Option(
        None,
        "-v",
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Prints the version of the github-dependents-info package.",
    ),
) -> None:
    if repo is not None:
        gh_deps_info = GithubDependentsInfo(repo, debug=verbose)
        repo_stats = gh_deps_info.collect()
        if markdown_file is not None:
            gh_deps_info.build_markdown(file=markdown_file)
            if json_output is False:
                print("Wrote markdown file " + markdown_file)
        if json_output is True:
            print(json.dumps(repo_stats, indent=4))
        else:
            gh_deps_info.print_result()


if __name__ == "__main__":
    app()
