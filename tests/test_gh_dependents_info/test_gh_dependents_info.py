"""Tests for gh_dependents_info"""

import os
import tempfile
import uuid

from github_dependents_info import GithubDependentsInfo


def test_collect_stats_single_package():
    # Check generate single package stats file
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
    # Check Update README file
    tmp_readme_file = tempfile.gettempdir() + os.path.sep + str(uuid.uuid4()) + "-test-single-readme.md"
    with open(tmp_readme_file, "w", encoding="utf-8") as file:
        file.write(
            "<!-- gh-dependents-info-used-by-start -->" + "shouldBeReplaced" + "<!-- gh-dependents-info-used-by-end -->"
        )

    gh_deps_info.badges["total_doc_url"] = "https://nvuillam/npm-groovy-lint"
    gh_deps_info.write_badge(tmp_readme_file, "total_doc_url")
    with open(tmp_readme_file, encoding="utf-8") as file:
        readme_content = file.read()
    assert "shouldBeReplaced" not in readme_content
    assert "nvuillam/npm-groovy-lint" in readme_content


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


def test_markdown_pagination_creates_multiple_files():
    repo = "nvuillam/npm-groovy-lint"
    with tempfile.TemporaryDirectory() as tmp_directory:
        base_file = os.path.join(tmp_directory, "dependents.md")
        gh_deps_info = GithubDependentsInfo(
            repo,
            debug=True,
            sort_key="stars",
            page_size=1,
            markdown_file=base_file,
        )
        gh_deps_info.collect()
        md = gh_deps_info.build_markdown(file=base_file)
        assert md != ""
        assert os.path.isfile(base_file)
        second_page = os.path.join(tmp_directory, "dependents-page-2.md")
        assert os.path.isfile(second_page)
        with open(second_page, encoding="utf-8") as page_file:
            page_two_content = page_file.read()
        assert "Page 2 of" in page_two_content
        assert "[Previous](dependents.md)" in page_two_content


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
