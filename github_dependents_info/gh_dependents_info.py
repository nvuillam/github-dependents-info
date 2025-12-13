import json
import logging
import os
import re
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class GithubDependentsInfo:
    DEFAULT_PAGE_SIZE = 500

    def __init__(self, repo, **options) -> None:
        self.repo = repo
        self.outputrepo = self.repo if "outputrepo" not in options else options["outputrepo"]
        if self.outputrepo is None or self.outputrepo == "" or len(self.outputrepo) < 4:
            self.outputrepo = self.repo
        self.url_init = f"https://github.com/{self.repo}/network/dependents"
        self.url_starts_with = f"/{self.repo}/network/dependents" + "?package_id="
        self.sort_key = "name" if "sort_key" not in options else options["sort_key"]
        self.min_stars = None if "min_stars" not in options else options["min_stars"]
        self.json_output = True if "json_output" in options and options["json_output"] is True else False
        self.merge_packages = True if "merge_packages" in options and options["merge_packages"] is True else False
        self.doc_url = options["doc_url"] if "doc_url" in options else None
        self.markdown_file = options["markdown_file"] if "markdown_file" in options else None
        self.badge_color = options["badge_color"] if "badge_color" in options else "informational"
        self.debug = True if "debug" in options and options["debug"] is True else False
        self.overwrite_progress = (
            True if "overwrite_progress" in options and options["overwrite_progress"] is True else False
        )
        self.csv_directory = (
            Path(options["csv_directory"])
            if ("csv_directory" in options and options["csv_directory"] is not None)
            else None
        )
        self.owner = options["owner"] if "owner" in options else None
        self.page_size = self._sanitize_page_size(options.get("page_size", self.DEFAULT_PAGE_SIZE))
        self.total_sum = 0
        self.total_public_sum = 0
        self.total_private_sum = 0
        self.total_stars_sum = 0
        self.packages = []
        self.all_public_dependent_repos = []
        self.badges = {}
        self.result = {}
        self.time_delay = options["time_delay"] if "time_delay" in options else 0.1

    def collect(self):
        if self.overwrite_progress or not self.load_progress():
            self.compute_packages()
            self.save_progress_packages_list()  # only saves if csv_directory is provided

        # for each package, get count by parsing GitHub HTML
        for package in self.packages:
            # check if we have already computed this package on previous crawl
            if "public_dependents" in package:
                continue

            nextExists = True
            result = []

            # Build start page url
            if package["id"] is not None:
                url = self.url_init + "?package_id=" + package["id"]
                if self.owner:
                    url += "&owner=" + self.owner
                if self.debug is True:
                    logging.info("Package " + package["name"] + ": browsing " + url + " ...")
            else:
                url = self.url_init + ""
                if self.owner:
                    url += "?owner=" + self.owner
                if self.debug is True:
                    logging.info("Package " + self.repo + ": browsing" + url + " ...")
            package["url"] = url
            package["public_dependent_stars"] = 0
            page_number = 1

            # Get total number of dependents from UI
            r = self.requests_retry_session().get(url)
            soup = BeautifulSoup(r.content, "html.parser")
            svg_item = soup.find("a", {"class": "btn-link selected"})
            if svg_item is not None:
                a_around_svg = svg_item
                total_dependents = self.get_int(
                    a_around_svg.text.replace("Repositories", "").replace("Repository", "").strip()
                )
            else:
                total_dependents = 0

            # Parse all dependent packages pages
            while nextExists:
                r = self.requests_retry_session().get(url)
                soup = BeautifulSoup(r.content, "html.parser")
                total_public_stars = 0

                # Browse page dependents
                for t in soup.find_all("div", {"class": "Box-row"}):
                    owner_repo = self._extract_owner_repo(t)
                    if owner_repo is None:
                        if self.debug:
                            logging.warning("Skipping dependent row without repository link")
                        continue
                    owner_name, repo_name = owner_repo
                    star_svg = t.find("svg", {"class": "octicon-star"})
                    stars_text = "0"
                    if star_svg is not None and star_svg.parent is not None:
                        stars_text = star_svg.parent.get_text(strip=True)
                    result_item = {
                        "name": f"{owner_name}/{repo_name}",
                        "stars": self.get_int(stars_text.replace(",", "")),
                    }
                    # Collect avatar image
                    image = t.find_all("img", {"class": "avatar"})
                    if len(image) > 0 and image[0].attrs and "src" in image[0].attrs:
                        result_item["img"] = image[0].attrs["src"]
                    # Split owner and name
                    if "/" in result_item["name"]:
                        splits = str(result_item["name"]).split("/")
                        result_item["owner"] = splits[0]
                        result_item["repo_name"] = splits[1]
                    # Skip result if less than minimum stars
                    if self.min_stars is not None and result_item["stars"] < self.min_stars:
                        continue
                    result += [result_item]
                    total_public_stars += result_item["stars"]

                # Check next page
                nextExists = False
                paginate_container = soup.find("div", {"class": "paginate-container"})
                if paginate_container is not None:
                    for u in paginate_container.find_all("a"):
                        if u.text == "Next":
                            nextExists = True
                            time.sleep(self.time_delay)
                            url = u["href"]
                            page_number = page_number + 1
                            if self.debug is True:
                                logging.info("  - browsing page " + str(page_number))

            # Manage results for package
            if self.sort_key == "stars":
                result = sorted(result, key=lambda d: d[self.sort_key], reverse=True)
            else:
                result = sorted(result, key=lambda d: d[self.sort_key])
            if self.debug is True:
                for r in result:
                    logging.info(r)

            # Build package stats
            total_public_dependents = len(result)
            package["public_dependents"] = result
            package["public_dependents_number"] = total_public_dependents
            package["public_dependent_stars"] = total_public_stars
            package["private_dependents_number"] = total_dependents - total_public_dependents
            package["total_dependents_number"] = total_dependents if total_dependents > 0 else total_public_dependents

            # Build package badges
            package["badges"] = {}
            package["badges"]["total"] = self.build_badge(
                "Used%20by", package["total_dependents_number"], url=package["url"]
            )
            package["badges"]["public"] = self.build_badge(
                "Used%20by%20(public)", package["public_dependents_number"], url=package["url"]
            )
            package["badges"]["private"] = self.build_badge(
                "Used%20by%20(private)", package["private_dependents_number"], url=package["url"]
            )
            package["badges"]["stars"] = self.build_badge(
                "Used%20by%20(stars)", package["public_dependent_stars"], url=package["url"]
            )

            # Build total stats
            self.all_public_dependent_repos += result
            self.total_sum += package["total_dependents_number"]
            self.total_public_sum += package["public_dependents_number"]
            self.total_private_sum += package["private_dependents_number"]
            self.total_stars_sum += package["public_dependent_stars"]

            # Output
            if self.debug is True:
                logging.info("Total for package: " + str(total_public_dependents))
                logging.info("")
            # Save crawl progress
            self.save_progress(package)  # only saves if csv_directory is provided

        # make all_dependent_repos unique
        self.all_public_dependent_repos = list({v["name"]: v for v in self.all_public_dependent_repos}.values())

        # Sort packages and dependent repos
        if self.sort_key == "stars":
            self.packages = sorted(self.packages, key=lambda d: d["public_dependent_stars"], reverse=True)
            self.all_public_dependent_repos = sorted(
                self.all_public_dependent_repos, key=lambda d: d["stars"], reverse=True
            )
        else:
            self.packages = sorted(self.packages, key=lambda d: d["name"])
            self.all_public_dependent_repos = sorted(self.all_public_dependent_repos, key=lambda d: d["name"])

        # Build total badges
        doc_url_to_use = "https://github.com/nvuillam/github-dependents-info"
        if self.doc_url is not None:
            doc_url_to_use = self.doc_url
        elif self.markdown_file is not None:
            repo_url_part = self.outputrepo if "/" in self.outputrepo else self.repo
            doc_url_to_use = f"https://github.com/{repo_url_part}/blob/main/{self.markdown_file}"
        self.badges["total_doc_url"] = self.build_badge("Used%20by", self.total_sum, url=doc_url_to_use)

        self.badges["total"] = self.build_badge("Used%20by", self.total_sum)
        self.badges["public"] = self.build_badge("Used%20by%20(public)", self.total_public_sum)
        self.badges["private"] = self.build_badge("Used%20by%20(private)", self.total_private_sum)
        self.badges["stars"] = self.build_badge("Used%20by%20(stars)", self.total_stars_sum)
        # Build final result
        return self.build_result()

    def _extract_owner_repo(self, dependent_row):
        repo_anchor = dependent_row.find("a", {"data-hovercard-type": "repository"})
        if repo_anchor is None:
            repo_anchor = dependent_row.find("a", href=re.compile(r"/[^/]+/[^/]+"))
        if repo_anchor is None:
            return None
        repo_name = (repo_anchor.text or "").strip()
        owner_name = ""
        href_value = (repo_anchor.get("href") or "").split("?")[0].strip("/")
        path_parts = [part for part in href_value.split("/") if part]
        if len(path_parts) >= 2:
            owner_name = path_parts[-2]
            if not repo_name:
                repo_name = path_parts[-1]
        elif len(path_parts) == 1 and not repo_name:
            repo_name = path_parts[-1]

        if not owner_name:
            owner_anchor = dependent_row.find("a", {"data-hovercard-type": re.compile("(user|organization)")})
            if owner_anchor is not None and owner_anchor.text:
                owner_name = owner_anchor.text.strip()

        if not owner_name and repo_name and "/" in repo_name:
            splits = repo_name.split("/", 1)
            owner_name, repo_name = splits[0], splits[1]

        owner_name = owner_name.strip()
        repo_name = repo_name.strip()

        if owner_name and repo_name:
            return owner_name, repo_name

        return None

    # Get first url to see if there are multiple packages
    def compute_packages(self):
        r = self.requests_retry_session().get(self.url_init)
        soup = BeautifulSoup(r.content, "html.parser")
        for a in soup.find_all("a", href=True):
            if a["href"].startswith(self.url_starts_with):
                package_id = a["href"].rsplit("=", 1)[1]
                package_name = a.find("span").text.strip()
                if "{{" in package_name:
                    continue
                if self.debug is True:
                    logging.info(package_name)
                self.packages += [{"id": package_id, "name": package_name}]
        if len(self.packages) == 0:
            self.packages = [{"id": None, "name": self.repo}]

    # Save progress during the crawl
    def save_progress(self, package):
        if self.csv_directory is None:
            return
        self.csv_directory.mkdir(parents=False, exist_ok=True)
        file_path_sources = self.csv_directory / f"packages_{self.repo}.csv".replace("/", "-")
        file_path_dependents = self.csv_directory / f"dependents_{package['name']}.csv".replace("/", "-")

        keys_skip = ["public_dependents"]
        source_info = {k: v for (k, v) in package.items() if k not in keys_skip}
        dependents_info = package["public_dependents"]

        if not file_path_sources.exists():
            pd.json_normalize(source_info).to_csv(file_path_sources, mode="w", header=True)
        else:
            sources_all_df = pd.read_csv(file_path_sources, index_col=0)
            if package["name"] in sources_all_df["name"].values:
                # update the row with the new information
                sources_all_df.set_index("name", inplace=True)
                source_df = pd.json_normalize(source_info).set_index("name", drop=True)
                for column in source_df.columns:
                    if source_df[column].dtype == object and column in sources_all_df.columns:
                        sources_all_df[column] = sources_all_df[column].astype("object")
                    sources_all_df.loc[source_df.index, column] = source_df[column]
                sources_all_df.reset_index(inplace=True, drop=False)
                sources_all_df.to_csv(file_path_sources, mode="w", header=True)
            else:
                pd.json_normalize(source_info).to_csv(file_path_sources, mode="a", header=False)

        if (not file_path_dependents.exists() or self.overwrite_progress) and len(dependents_info) > 0:
            pd.DataFrame(dependents_info).to_csv(file_path_dependents, mode="w", header=True)

    def save_progress_packages_list(self):
        if self.csv_directory is None:
            return
        self.csv_directory.mkdir(parents=False, exist_ok=True)
        columns = [
            "id",
            "name",
            "url",
            "total_dependents_number",
            "public_dependents_number",
            "private_dependents_number",
            "public_dependent_stars",
            "badges.total",
            "badges.public",
            "badges.private",
            "badges.stars",
        ]
        file_path_sources = self.csv_directory / f"packages_{self.repo}.csv".replace("/", "-")
        if not file_path_sources.exists() or self.overwrite_progress:
            pd.DataFrame(self.packages, columns=columns).to_csv(file_path_sources, mode="w", header=True)

    # Load progress from previous crawl with the same repo
    def load_progress(self):
        if self.csv_directory is None:
            return False
        file_path_sources = self.csv_directory / f"packages_{self.repo}.csv".replace("/", "-")
        if file_path_sources.exists():
            self.packages = pd.read_csv(file_path_sources, index_col=0).replace({np.nan: None}).to_dict("records")
            for i, package in enumerate(self.packages):
                file_path_dependents = self.csv_directory / f"dependents_{package['name']}.csv".replace("/", "-")
                if file_path_dependents.exists():
                    self.packages[i]["public_dependents"] = (
                        pd.read_csv(file_path_dependents, index_col=0).replace({np.nan: None}).to_dict("records")
                    )
                    self.all_public_dependent_repos += self.packages[i]["public_dependents"]
                    self.total_sum += package["total_dependents_number"] if package["total_dependents_number"] else 0
                    self.total_public_sum += (
                        package["public_dependents_number"] if package["public_dependents_number"] else 0
                    )
                    self.total_private_sum += (
                        package["private_dependents_number"] if package["private_dependents_number"] else 0
                    )
                    self.total_stars_sum += (
                        package["public_dependent_stars"] if package["public_dependent_stars"] else 0
                    )
        return len(self.packages) > 0

    # Build result
    def build_markdown(self, **options) -> str:
        pages_data = self._paginate_dependents()
        total_pages = len(pages_data)
        base_file = options.get("file")
        page_paths = self._build_paginated_file_paths(base_file, total_pages)
        page_links = [self._format_link_target(path) if path else None for path in page_paths]

        rendered_pages = []
        for page_number, page_data in enumerate(pages_data, start=1):
            md_lines = self._build_markdown_page(page_number, total_pages, page_data, page_links)
            md_lines_str = "\n".join(md_lines)
            rendered_pages.append(md_lines_str)

            target_file = page_paths[page_number - 1]
            if target_file is not None:
                self._write_markdown_file(target_file, md_lines_str)

        if rendered_pages:
            return "\n\n".join(rendered_pages)
        return ""

    def _build_markdown_page(self, page_number, total_pages, page_data, page_links):
        md_lines = [f"# Dependents stats for {self.repo}", ""]
        md_lines += self._build_navigation_lines(page_number, total_pages, page_links)
        md_lines += self._build_summary_lines()

        if self.merge_packages is True:
            md_lines += self._build_merge_packages_section(page_data.get("merged_repos", []))
        else:
            page_packages = page_data.get("packages", {})
            include_empty_packages = page_number == 1
            md_lines += self._build_packages_section(page_packages, include_empty_packages)

        md_lines += self._build_navigation_lines(page_number, total_pages, page_links)
        md_lines += [
            "",
            "_Generated using [github-dependents-info]"
            "(https://github.com/nvuillam/github-dependents-info), "
            "by [Nicolas Vuillamy](https://github.com/nvuillam)_",
        ]
        return md_lines

    def _build_summary_lines(self):
        if len(self.packages) <= 1 or self.merge_packages is True:
            return []
        lines = [
            self.badges["total"],
            self.badges["public"],
            self.badges["private"],
            self.badges["stars"],
            "",
            "| Package    | Total  | Public | Private | Stars |",
            "| :--------  | -----: | -----: | -----:  | ----: |",
        ]
        for package in self.packages:
            anchor_name = package["name"].replace("/", "").replace("@", "")
            name = "[" + package["name"] + "](#package-" + anchor_name + ")"
            badge_1 = package["badges"]["total"]
            badge_2 = package["badges"]["public"]
            badge_3 = package["badges"]["private"]
            badge_4 = package["badges"]["stars"]
            lines += [f"| {name}    | {badge_1}  | {badge_2} | {badge_3} | {badge_4} |"]
        lines += [""]
        return lines

    def _build_merge_packages_section(self, repos_slice):
        lines = [
            self.badges["total"],
            self.badges["public"],
            self.badges["private"],
            self.badges["stars"],
            "",
        ]
        if len(repos_slice) == 0:
            lines += ["No dependent repositories", ""]
            return lines
        lines += ["| Repository | Stars  |", "| :--------  | -----: |"]
        for repo1 in repos_slice:
            self.build_repo_md_line(lines, repo1)
        lines += [""]
        return lines

    def _build_packages_section(self, page_packages, include_empty_packages):
        lines = []
        for index, package in enumerate(self.packages):
            repos_slice = page_packages.get(index)
            should_render = repos_slice is not None
            if include_empty_packages and len(package.get("public_dependents", [])) == 0:
                should_render = True
            if should_render is False:
                continue
            lines += ["## Package " + package["name"], ""]
            if not repos_slice:
                lines += ["No dependent repositories", ""]
                continue
            lines += [
                package["badges"]["total"],
                package["badges"]["public"],
                package["badges"]["private"],
                package["badges"]["stars"],
                "",
                "| Repository | Stars  |",
                "| :--------  | -----: |",
            ]
            for repo1 in repos_slice:
                self.build_repo_md_line(lines, repo1)
            lines += [""]
        return lines

    def _build_navigation_lines(self, page_number, total_pages, page_links):
        if total_pages <= 1:
            return []
        nav_parts = [f"Page {page_number} of {total_pages}"]
        if page_number > 1:
            previous_link = page_links[page_number - 2] if page_links else None
            if previous_link is not None:
                nav_parts.append(f"[Previous]({previous_link})")
            else:
                nav_parts.append("Previous")
        if page_number < total_pages:
            next_link = page_links[page_number] if page_links else None
            if next_link is not None:
                nav_parts.append(f"[Next]({next_link})")
            else:
                nav_parts.append("Next")
        return ["_" + " • ".join(nav_parts) + "_", ""]

    def _sanitize_page_size(self, page_size):
        try:
            page_size_int = int(page_size)
        except (TypeError, ValueError):
            return self.DEFAULT_PAGE_SIZE
        if page_size_int <= 0:
            return self.DEFAULT_PAGE_SIZE
        return page_size_int

    def _paginate_dependents(self):
        if self.merge_packages is True:
            return self._paginate_merged_dependents()
        return self._paginate_package_dependents()

    def _paginate_merged_dependents(self):
        repos = self.all_public_dependent_repos or []
        if len(repos) == 0:
            return [{"merged_repos": []}]
        pages = []
        for start in range(0, len(repos), self.page_size):
            pages.append({"merged_repos": repos[start : start + self.page_size]})
        return pages

    def _paginate_package_dependents(self):
        flat_entries = []
        for idx, package in enumerate(self.packages):
            for repo in package.get("public_dependents", []):
                flat_entries.append((idx, repo))
        if len(flat_entries) == 0:
            return [{"packages": {}}]
        pages = []
        for start in range(0, len(flat_entries), self.page_size):
            slice_entries = flat_entries[start : start + self.page_size]
            package_map = defaultdict(list)
            for pkg_index, repo in slice_entries:
                package_map[pkg_index].append(repo)
            pages.append({"packages": dict(package_map)})
        return pages

    def _build_paginated_file_paths(self, base_file, total_pages):
        if base_file is None:
            return [None] * total_pages
        paths = []
        root, ext = os.path.splitext(base_file)
        ext = ext if ext != "" else ".md"
        for page_number in range(1, total_pages + 1):
            if page_number == 1:
                paths.append(base_file)
            else:
                paths.append(f"{root}-page-{page_number}{ext}")
        return paths

    def _write_markdown_file(self, file_path, content):
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        if self.json_output is False:
            print("Wrote markdown file " + file_path)

    def _format_link_target(self, file_path):
        basename = os.path.basename(file_path)
        return basename.replace(" ", "%20")

    def build_repo_md_line(self, md_lines, repo1):
        repo_label = repo1["name"]
        repo_stars = repo1["stars"]
        image_md = ""
        if "img" in repo1:
            img = repo1["img"]
            image_md = f'<img class="avatar mr-2" src="{img}" width="20" height="20" alt=""> '
        if "owner" in repo1 and "repo_name" in repo1:
            owner_md = "[" + repo1["owner"] + "](https://github.com/" + repo1["owner"] + ")"
            repo_md = (
                "[" + repo1["repo_name"] + "](https://github.com/" + repo1["owner"] + "/" + repo1["repo_name"] + ")"
            )
            md_lines += [f"|{image_md} &nbsp; {owner_md} / {repo_md} | {repo_stars} |"]
        else:
            md_lines += [f"|{image_md} &nbsp; [{repo_label}](https://github.com/{repo_label}) | {repo_stars} |"]

    def build_badge(self, label, nb, **options):
        if "url" in options:
            url = options["url"]
        else:
            url = f"https://github.com/{self.repo}/network/dependents"
        return (
            f"[![Generated by github-dependents-info](https://img.shields.io/static/v1?label={label}&message={str(nb)}"
            + f"&color={self.badge_color}&logo=slickpic)]({url})"
        )

    def requests_retry_session(
        self,
        retries=10,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        session=None,
    ):
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    # Write badge in markdown file
    def write_badge(self, file_path="README.md", badge_key="total"):
        self.replace_in_file(
            file_path,
            "<!-- gh-dependents-info-used-by-start -->",
            "<!-- gh-dependents-info-used-by-end -->",
            self.badges[badge_key],
        )

    # Generic method to replace text between tags
    def replace_in_file(self, file_path, start, end, content, add_new_line=False):
        if not os.path.exists(file_path):
            print(f"[Warning] Can not update badge in not existing file {file_path}")
            return
        # Read in the file
        with open(file_path, encoding="utf-8") as file:
            file_content = file.read()
        if (start not in file_content) or (end not in file_content):
            print(f"[Warning] Can not update badge if it does not contain tags {start} and {end}")
            return
        # Replace the target string
        if add_new_line is True:
            replacement = f"{start}\n{content}\n{end}"
        else:
            replacement = f"{start}\n{content}{end}"
        regex = rf"{start}([\s\S]*?){end}"
        file_content = re.sub(regex, replacement, file_content, re.DOTALL)
        # Write the file out again
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(file_content)
        if self.json_output is False:
            print("Updated " + file.name + " between " + start + " and " + end)

    # Get integer from string
    def get_int(self, number_as_string: str):
        number_as_string = number_as_string.replace(",", "").replace(" ", "")
        try:
            return int(number_as_string)
        except Exception:
            logging.warning(f'WARNING: Unable to get integer from "{number_as_string}"')
            return 0
