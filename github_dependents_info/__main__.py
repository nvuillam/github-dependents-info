import logging

import typer
from github_dependents_info import version
from github_dependents_info.gh_dependents_info import GithubDependentsInfo
from rich.console import Console

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
    repo: str = typer.Option(None, "-r", "--repo", help="Repository (ex: oxsecurity/megalinter)"),
    markdown_file: str = typer.Option(None, "-m", "--markdownfile", help="Output Markdown file path"),
    badge_markdown_file: str = typer.Option(
        None,
        "-b",
        "--badgemarkdownfile",
        help="Path to markdown file to insert/update Used By badge between tags <!-- gh-dependents-info-used-by-start --><!-- gh-dependents-info-used-by-end -->",
    ),
    badge_color: str = typer.Option("informational", "-c", "--markdownbadgecolor", help="Markdown badge color"),
    sort_key: str = typer.Option(None, "-s", "--sort", help="Sort of name(default) or stars"),
    min_stars: int = typer.Option(None, "-x", "--minstars", help="Filter dependents with less than X stars"),
    json_output: bool = typer.Option(
        False,
        "-j",
        "--json",
        help="Output in JSON format",
    ),
    csv_directory: str = typer.Option(
        None,
        "-c",
        "--csvdirectory",
        help="Path to directory for CSV files",
    ),
    merge_packages: bool = typer.Option(
        False,
        "-p",
        "--mergepackages",
        help="In case of multiple packages, merges results into a single list",
    ),
    verbose: bool = typer.Option(
        False,
        "-d",
        "--verbose",
        help="Prints the version of github-dependents-info package",
    ),
    overwrite: bool = typer.Option(
        False,
        "-o",
        "--overwrite",
        help="Overwrite existing CSV files in provided csv_directory. Default is to resume from existing progress.",
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
    # Init logger
    if verbose is True:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    # Check minimum arguments
    if repo is None:
        raise ValueError("--repo argument is mandatory")
    else:
        # Manage default values :)
        if sort_key is None:
            sort_key = "name"
        if min_stars is None:
            min_stars = 0
        # Create GithubDependentsInfo instance
        gh_deps_info = GithubDependentsInfo(
            repo,
            debug=verbose,
            overwrite_progress=overwrite,
            sort_key=sort_key,
            min_stars=min_stars,
            json_output=json_output,
            csv_directory=csv_directory,
            badge_markdown_file=badge_markdown_file,
            badge_color=badge_color,
            merge_packages=merge_packages,
        )
        # Collect data
        gh_deps_info.collect()
        # Write output markdown
        if markdown_file is not None:
            gh_deps_info.build_markdown(file=markdown_file)
        # Update existing markdown to add badge
        if badge_markdown_file is not None:
            gh_deps_info.write_badge(badge_markdown_file)
        # Print text or json result
        gh_deps_info.print_result()


if __name__ == "__main__":
    app()
