import json
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class GithubDependentsInfo:
    def __init__(self, repo, **options) -> None:
        self.repo = repo
        self.url_init = f"https://github.com/{self.repo}/network/dependents"
        self.url_starts_with = f"/{self.repo}/network/dependents" + "?package_id="
        self.sort_key = "name" if "sort_key" not in options else options["sort_key"]
        self.min_stars = None if "min_stars" not in options else options["min_stars"]
        self.json_output = True if "json_output" in options and options["json_output"] is True else False
        self.merge_packages = True if "merge_packages" in options and options["merge_packages"] is True else False
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
        self.total_sum = 0
        self.total_public_sum = 0
        self.total_private_sum = 0
        self.total_stars_sum = 0
        self.packages = []
        self.all_public_dependent_repos = []
        self.badges = {}
        self.result = {}

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
                if self.debug is True:
                    logging.info("Package " + package["name"] + ": browsing " + url + " ...")
            else:
                url = self.url_init + ""
                if self.debug is True:
                    logging.info("Package " + self.repo + ": browsing" + url + " ...")
            package["url"] = url
            package["public_dependent_stars"] = 0
            page_number = 1

            # Get total number of dependents from UI
            r = self.requests_retry_session().get(url)
            soup = BeautifulSoup(r.content, "html.parser")
            svg_item = soup.find("svg", {"class": "octicon-code-square"})
            if svg_item is not None:
                a_around_svg = svg_item.parent
                total_dependents = self.get_int(a_around_svg.text.replace("Repositories", "").strip())
            else:
                total_dependents = 0

            # Parse all dependent packages pages
            while nextExists:
                r = self.requests_retry_session().get(url)
                soup = BeautifulSoup(r.content, "html.parser")
                total_public_stars = 0

                # Browse page dependents
                for t in soup.findAll("div", {"class": "Box-row"}):
                    result_item = {
                        "name": "{}/{}".format(
                            t.find("a", {"data-repository-hovercards-enabled": ""}).text,
                            t.find("a", {"data-hovercard-type": "repository"}).text,
                        ),
                        "stars": self.get_int(
                            t.find("svg", {"class": "octicon-star"}).parent.text.strip().replace(",", "")
                        ),
                    }
                    # Skip result if less than minimum stars
                    if self.min_stars is not None and result_item["stars"] < self.min_stars:
                        continue
                    result += [result_item]
                    total_public_stars += result_item["stars"]

                # Check next page
                nextExists = False
                paginate_container = soup.find("div", {"class": "paginate-container"})
                if paginate_container is not None:
                    for u in paginate_container.findAll("a"):
                        if u.text == "Next":
                            nextExists = True
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
        self.badges["total"] = self.build_badge("Used%20by", self.total_sum)
        self.badges["public"] = self.build_badge("Used%20by%20(public)", self.total_public_sum)
        self.badges["private"] = self.build_badge("Used%20by%20(private)", self.total_private_sum)
        self.badges["stars"] = self.build_badge("Used%20by%20(stars)", self.total_stars_sum)
        # Build final result
        return self.build_result()

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
                sources_all_df.update(source_df)
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
    def build_result(self):
        self.result = {
            "all_public_dependent_repos": self.all_public_dependent_repos,
            "total_dependents_number": self.total_sum,
            "public_dependents_number": self.total_public_sum,
            "private_dependents_number": self.total_private_sum,
            "public_dependents_stars": self.total_stars_sum,
            "badges": self.badges,
        }
        if self.merge_packages is False:
            self.result["packages"] = (self.packages,)
        return self.result

    # Print output
    def print_result(self):
        if self.json_output is True:
            print(json.dumps(self.result, indent=4))
        else:
            print("Total: " + str(self.total_sum))
            print("Public: " + str(self.total_public_sum) + " (" + str(self.total_stars_sum) + " stars)")
            print("Private: " + str(self.total_private_sum))

    def build_markdown(self, **options) -> str:
        md_lines = [f"# Dependents stats for {self.repo}", ""]

        # Summary table
        if len(self.packages) > 1 and self.merge_packages is False:
            # Summary badges if there are multiple packages
            md_lines += [
                self.badges["total"],
                self.badges["public"],
                self.badges["private"],
                self.badges["stars"],
                "",
            ]

            md_lines += [
                "| Package    | Total  | Public | Private | Stars |",
                "| :--------  | -----: | -----: | -----:  | ----: |",
            ]
            for package in self.packages:
                name = "[" + package["name"] + "](#package-" + package["name"].replace("/", "").replace("@", "") + ")"
                badge_1 = package["badges"]["total"]
                badge_2 = package["badges"]["public"]
                badge_3 = package["badges"]["private"]
                badge_4 = package["badges"]["stars"]
                md_lines += [f"| {name}    | {badge_1}  | {badge_2} | {badge_3} | {badge_4} |"]
            md_lines += [""]

        # Single dependents list
        if self.merge_packages is True:
            md_lines += [
                self.badges["total"],
                self.badges["public"],
                self.badges["private"],
                self.badges["stars"],
                "",
            ]
            md_lines += ["| Repository | Stars  |", "| :--------  | -----: |"]
            for repo1 in self.all_public_dependent_repos:
                repo_label = repo1["name"]
                repo_stars = repo1["stars"]
                md_lines += [f"|[{repo_label}](https://github.com/{repo_label}) | {repo_stars} |"]
        # Dependents by package
        else:
            for package in self.packages:
                md_lines += ["## Package " + package["name"], ""]
                if len(package["public_dependents"]) == 0:
                    md_lines += ["No dependent repositories"]
                else:
                    md_lines += [
                        package["badges"]["total"],
                        package["badges"]["public"],
                        package["badges"]["private"],
                        package["badges"]["stars"],
                        "",
                    ]
                    md_lines += ["| Repository | Stars  |", "| :--------  | -----: |"]
                    for repo1 in package["public_dependents"]:
                        repo_label = repo1["name"]
                        repo_stars = repo1["stars"]
                        md_lines += [f"|[{repo_label}](https://github.com/{repo_label}) | {repo_stars} |"]
                md_lines += [""]

        # footer
        md_lines += ["_Generated by [github-dependents-info](https://github.com/nvuillam/github-dependents-info)_"]
        md_lines_str = "\n".join(md_lines)

        # Write in file if requested
        if "file" in options:
            with open(options["file"], "w", encoding="utf-8") as f:
                f.write(md_lines_str)
                if self.json_output is False:
                    print("Wrote markdown file " + options["file"])
        return md_lines_str

    def build_badge(self, label, nb, **options):
        if "url" in options:
            url = options["url"]
        else:
            url = f"https://github.com/{self.repo}/network/dependents"
        return f"[![](https://img.shields.io/static/v1?label={label}&message={str(nb)}&color={self.badge_color}&logo=slickpic)]({url})"

    def requests_retry_session(
        self,
        retries=3,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 504),
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
        # Read in the file
        with open(file_path, encoding="utf-8") as file:
            file_content = file.read()
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
        return int(number_as_string)
