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


def test_collect_stats_owner():
    repo = "nvuillam/npm-groovy-lint"
    gh_deps_info = GithubDependentsInfo(repo, debug=True, owner="nvuillam")
    repo_stats = gh_deps_info.collect()
    assert repo_stats["public_dependents_number"] < 10


def test_collect_stats_max_scraped_pages():
    repo = SINGLE_PACKAGE_REPO
    gh_deps_info = GithubDependentsInfo(repo, debug=True, sort_key="stars", max_scraped_pages=1)
    repo_stats = gh_deps_info.collect()
    # With max_scraped_pages=1, we should get at most 30 dependents (1 page = ~30 items)
    assert repo_stats["public_dependents_number"] > 0
    assert repo_stats["public_dependents_number"] <= 30


def test_pagination_enabled_by_default():
    """Test that pagination is enabled by default."""
    repo = SINGLE_PACKAGE_REPO
    gh_deps_info = GithubDependentsInfo(repo, debug=True)
    assert gh_deps_info.pagination is True
    assert gh_deps_info.page_size == 500


def test_pagination_disabled():
    """Test that pagination can be disabled."""
    repo = SINGLE_PACKAGE_REPO
    gh_deps_info = GithubDependentsInfo(repo, debug=True, pagination=False)
    assert gh_deps_info.pagination is False


def test_custom_page_size():
    """Test that custom page size can be set."""
    repo = SINGLE_PACKAGE_REPO
    gh_deps_info = GithubDependentsInfo(repo, debug=True, page_size=100)
    assert gh_deps_info.page_size == 100


def test_pagination_single_page():
    """Test that no pagination files are created when results fit on one page."""
    repo = SINGLE_PACKAGE_REPO
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_md_file = os.path.join(tmp_dir, "test-single-page.md")
        gh_deps_info = GithubDependentsInfo(
            repo, debug=True, sort_key="stars", max_scraped_pages=1, pagination=True, page_size=100
        )
        gh_deps_info.collect()
        md = gh_deps_info.build_markdown(file=tmp_md_file)

        # Should only have one file since results fit on one page
        assert os.path.isfile(tmp_md_file)
        assert not os.path.isfile(os.path.join(tmp_dir, "test-single-page-2.md"))

        # Check that navigation is not in the file
        with open(tmp_md_file, encoding="utf-8") as file:
            content = file.read()
            assert "Page 1 of" not in content


def test_pagination_multiple_pages():
    """Test that multiple pagination files are created when results exceed page size."""
    repo = SINGLE_PACKAGE_REPO
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_md_file = os.path.join(tmp_dir, "test-multi-page.md")
        # Use a very small page size to force multiple pages
        gh_deps_info = GithubDependentsInfo(
            repo, debug=True, sort_key="stars", max_scraped_pages=2, pagination=True, page_size=5
        )
        gh_deps_info.collect()

        # Should have results that span multiple pages
        if gh_deps_info.result["public_dependents_number"] > 5:
            md = gh_deps_info.build_markdown(file=tmp_md_file)

            # Check that multiple files were created
            assert os.path.isfile(tmp_md_file)
            assert os.path.isfile(os.path.join(tmp_dir, "test-multi-page-2.md"))

            # Check navigation in first page
            with open(tmp_md_file, encoding="utf-8") as file:
                content = file.read()
                assert "Page 1 of" in content
                assert "Next ➡️" in content
                assert "test-multi-page-2.md" in content

            # Check navigation in second page
            with open(os.path.join(tmp_dir, "test-multi-page-2.md"), encoding="utf-8") as file:
                content = file.read()
                assert "Page 2 of" in content
                assert "Previous" in content
                assert "test-multi-page.md" in content


def test_pagination_disabled_no_split():
    """Test that when pagination is disabled, all results go into one file."""
    repo = SINGLE_PACKAGE_REPO
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_md_file = os.path.join(tmp_dir, "test-no-pagination.md")
        gh_deps_info = GithubDependentsInfo(
            repo, debug=True, sort_key="stars", max_scraped_pages=2, pagination=False, page_size=5
        )
        gh_deps_info.collect()
        md = gh_deps_info.build_markdown(file=tmp_md_file)

        # Should only have one file even if results exceed page size
        assert os.path.isfile(tmp_md_file)
        assert not os.path.isfile(os.path.join(tmp_dir, "test-no-pagination-2.md"))

        # Check that navigation is not in the file
        with open(tmp_md_file, encoding="utf-8") as file:
            content = file.read()
            assert "Page 1 of" not in content
