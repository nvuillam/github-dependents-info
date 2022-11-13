"""Collect information about dependencies between a github repo and other repositories. Results available in JSON, markdown and badges."""

import sys

from .gh_dependents_info import GithubDependentsInfo

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata


def get_version() -> str:
    try:
        return importlib_metadata.version(__name__)
    except importlib_metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


version: str = get_version()
