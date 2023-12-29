"""Tests for gh_dependents_info"""
import os
import tempfile
import uuid

from github_dependents_info import GithubDependentsInfo


def test_collect_stats_single_package():
    repo = "nvuillam/npm-groovy-lint"
    tmp_md_file = tempfile.gettempdir() + os.path.sep + str(uuid.uuid4()) + "-test-single.md"
    gh_deps_info = GithubDependentsInfo(
        repo, debug=True, sort_key="stars", badge_color="pink", markdown_file=tmp_md_file
    )
    repo_stats = gh_deps_info.collect()
    assert repo_stats["public_dependents_number"] > 10

    md = gh_deps_info.build_markdown(file=tmp_md_file)
    assert md.count("\n") > 10
    assert "pink" in md
    with open(tmp_md_file, encoding="utf-8") as file:
        md_content = file.read()
        assert md_content.count("\n") > 10


def test_collect_stats_multi_package():
    repo = "oxsecurity/megalinter"
    gh_deps_info = GithubDependentsInfo(repo, debug=True, sort_key="stars")
    repo_stats = gh_deps_info.collect()
    assert repo_stats["public_dependents_number"] > 100
    tmp_md_file = tempfile.gettempdir() + os.path.sep + str(uuid.uuid4()) + "-test-multiple.md"
    md = gh_deps_info.build_markdown(file=tmp_md_file)
    assert md.count("\n") > 100
    with open(tmp_md_file, encoding="utf-8") as file:
        md_content = file.read()
        assert md_content.count("\n") > 100


def test_collect_stats_min_stars():
    repo = "nvuillam/npm-groovy-lint"
    gh_deps_info = GithubDependentsInfo(repo, debug=True, sort_key="stars", min_stars=10)
    repo_stats = gh_deps_info.collect()
    assert repo_stats["public_dependents_number"] < 10


def test_collect_csv():
    repo = "nvuillam/npm-groovy-lint"
    with tempfile.TemporaryDirectory() as csv_directory:
        gh_deps_info = GithubDependentsInfo(
            repo, debug=True, sort_key="stars", min_stars=10, csv_directory=csv_directory
        )
        gh_deps_info.collect()
        assert os.path.isfile(csv_directory + os.path.sep + f"packages_{repo.replace('/', '-')}.csv")
        assert os.path.isfile(
            csv_directory + os.path.sep + f"dependents_{gh_deps_info.packages[0]['name'].replace('/', '-')}.csv"
        )


def test_collect_csv_multi_package():
    repo = "oxsecurity/megalinter"
    with tempfile.TemporaryDirectory() as csv_directory:
        gh_deps_info = GithubDependentsInfo(
            repo, debug=True, sort_key="stars", min_stars=10, csv_directory=csv_directory
        )
        gh_deps_info.collect()
        assert os.path.isfile(csv_directory + os.path.sep + f"packages_{repo.replace('/', '-')}.csv")
        for package in gh_deps_info.packages:
            if package["public_dependents_number"] <= 0:
                continue
            assert os.path.isfile(csv_directory + os.path.sep + f"dependents_{package['name'].replace('/', '-')}.csv")
