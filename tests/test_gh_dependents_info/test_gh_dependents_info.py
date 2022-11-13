"""Tests for gh_dependents_info"""
import os
import tempfile
import uuid

from github_dependents_info import GithubDependentsInfo


def test_collect_stats_single_package():
    repo = "nvuillam/npm-groovy-lint"
    gh_deps_info = GithubDependentsInfo(repo)
    repo_stats = gh_deps_info.collect(debug=True)
    assert repo_stats["public_dependents_number"] > 0
    tmp_md_file = tempfile.gettempdir() + os.path.sep + str(uuid.uuid4()) + "-test-single.md"
    md = gh_deps_info.build_markdown(file=tmp_md_file)
    assert md.count("\n") > 10
    with open(tmp_md_file, "r", encoding="utf-8") as file:
        md_content = file.read()
        assert md_content.count("\n") > 10


def test_collect_stats_multi_package():
    repo = "oxsecurity/megalinter"
    gh_deps_info = GithubDependentsInfo(repo)
    repo_stats = gh_deps_info.collect(debug=True)
    assert repo_stats["public_dependents_number"] > 0
    tmp_md_file = tempfile.gettempdir() + os.path.sep + str(uuid.uuid4()) + "-test-multiple.md"
    md = gh_deps_info.build_markdown(file=tmp_md_file)
    assert md.count("\n") > 100
    with open(tmp_md_file, "r", encoding="utf-8") as file:
        md_content = file.read()
        assert md_content.count("\n") > 100
