"""Collect information about dependencies between a github repo and other repositories. Results available in JSON, markdown and badges."""

from importlib import metadata as importlib_metadata

from .gh_dependents_info import GithubDependentsInfo  # noqa


def get_version() -> str:
    try:
        return importlib_metadata.version(__name__)
    except importlib_metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


version: str = get_version()
