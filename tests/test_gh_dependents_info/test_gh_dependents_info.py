"""Tests for gh_dependents_info"""

import os
import tempfile
import uuid

from github_dependents_info import GithubDependentsInfo

SINGLE_PACKAGE_REPO = "nvuillam/npm-groovy-lint"
SINGLE_PACKAGE_TOTAL_DOC_URL = "https://nvuillam/npm-groovy-lint"
SINGLE_PACKAGE_REPO_PUBLIC_DEPENDENTS_MIN = 10
MULTI_PACKAGE_REPO = "nvuillam/github-dependents-info"
MULTI_PACKAGE_REPO_PUBLIC_DEPENDENTS_MIN = 10


def test_collect_stats_single_package():
    # Check generate single package stats file
    repo = SINGLE_PACKAGE_REPO
    tmp_md_file = tempfile.gettempdir() + os.path.sep + str(uuid.uuid4()) + "-test-single.md"
    gh_deps_info = GithubDependentsInfo(
        repo, debug=True, sort_key="stars", badge_color="pink", markdown_file=tmp_md_file
    )
    repo_stats = gh_deps_info.collect()
    assert repo_stats["public_dependents_number"] > SINGLE_PACKAGE_REPO_PUBLIC_DEPENDENTS_MIN

    md = gh_deps_info.build_markdown(file=tmp_md_file)
    assert md.count("\n") > SINGLE_PACKAGE_REPO_PUBLIC_DEPENDENTS_MIN
    assert "pink" in md
    with open(tmp_md_file, encoding="utf-8") as file:
        md_content = file.read()
        assert md_content.count("\n") > SINGLE_PACKAGE_REPO_PUBLIC_DEPENDENTS_MIN
    # Check Update README file
    tmp_readme_file = tempfile.gettempdir() + os.path.sep + str(uuid.uuid4()) + "-test-single-readme.md"
    with open(tmp_readme_file, "w", encoding="utf-8") as file:
        file.write(
            "<!-- gh-dependents-info-used-by-start -->" + "shouldBeReplaced" + "<!-- gh-dependents-info-used-by-end -->"
        )

    gh_deps_info.badges["total_doc_url"] = SINGLE_PACKAGE_TOTAL_DOC_URL
    gh_deps_info.write_badge(tmp_readme_file, "total_doc_url")
    with open(tmp_readme_file, encoding="utf-8") as file:
        readme_content = file.read()
    assert "shouldBeReplaced" not in readme_content
    assert SINGLE_PACKAGE_REPO in readme_content


def test_collect_stats_multi_package():
    repo = MULTI_PACKAGE_REPO
    gh_deps_info = GithubDependentsInfo(repo, debug=True, sort_key="stars")
    repo_stats = gh_deps_info.collect()
    assert repo_stats["public_dependents_number"] > MULTI_PACKAGE_REPO_PUBLIC_DEPENDENTS_MIN
    tmp_md_file = tempfile.gettempdir() + os.path.sep + str(uuid.uuid4()) + "-test-multiple.md"
    md = gh_deps_info.build_markdown(file=tmp_md_file)
    assert md.count("\n") > MULTI_PACKAGE_REPO_PUBLIC_DEPENDENTS_MIN
    with open(tmp_md_file, encoding="utf-8") as file:
        md_content = file.read()
        assert md_content.count("\n") > MULTI_PACKAGE_REPO_PUBLIC_DEPENDENTS_MIN


def test_collect_stats_min_stars():
    repo = SINGLE_PACKAGE_REPO
    gh_deps_info = GithubDependentsInfo(repo, debug=True, sort_key="stars", min_stars=10)
    repo_stats = gh_deps_info.collect()
    assert repo_stats["public_dependents_number"] > 1
    assert repo_stats["public_dependents_number"] < 10


def test_collect_csv():
    repo = SINGLE_PACKAGE_REPO
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
    repo = MULTI_PACKAGE_REPO
    with tempfile.TemporaryDirectory() as csv_directory:
        gh_deps_info = GithubDependentsInfo(
            repo, debug=True, sort_key="stars", min_stars=0, csv_directory=csv_directory
        )
        gh_deps_info.collect()
        assert len(gh_deps_info.packages) >= 2
        assert os.path.isfile(csv_directory + os.path.sep + f"packages_{repo.replace('/', '-')}.csv")
        packages_with_entries = 0
        for package in gh_deps_info.packages:
            if package["public_dependents_number"] <= 0:
                continue
            packages_with_entries += 1
            assert os.path.isfile(csv_directory + os.path.sep + f"dependents_{package['name'].replace('/', '-')}.csv")
        assert packages_with_entries >= 2
