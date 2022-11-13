"""Tests for gh_dependents_info"""

from github_dependents_info import GithubDependentsInfo


def test_collect_stats_single_package():
    """Example test with parametrization."""
    repo = "nvuillam/npm-groovy-lint"
    gh_deps_info = GithubDependentsInfo(repo)
    repo_stats = gh_deps_info.collect(debug=True)    
    assert repo_stats["public_dependents_number"] > 0

def test_collect_stats_multi_package():
    """Example test with parametrization."""
    repo = "oxsecurity/megalinter"
    gh_deps_info = GithubDependentsInfo(repo)
    repo_stats = gh_deps_info.collect(debug=True)    
    assert repo_stats["public_dependents_number"] > 0
