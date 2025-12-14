import asyncio
import json
import logging
import math
import os
import re
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup


class GithubDependentsInfo:
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
        self.max_scraped_pages = options["max_scraped_pages"] if "max_scraped_pages" in options else 0
        self.max_concurrent_requests = options.get("max_concurrent_requests", 10)
        self.pagination = True if "pagination" not in options else options["pagination"]
        self.page_size = options.get("page_size", 500)
        self.total_sum = 0
        self.total_public_sum = 0
        self.total_private_sum = 0
        self.total_stars_sum = 0
        self.packages = []
        self.all_public_dependent_repos = []
        self.badges = {}
        self.result = {}
        self.time_delay = options["time_delay"] if "time_delay" in options else 0.1
        self.http_retry_attempts = options.get("http_retry_attempts", 5)
        self.http_retry_initial_delay = options.get("http_retry_initial_delay", max(self.time_delay, 1.0))
        self.http_retry_backoff = options.get("http_retry_backoff", 2.0)
        self.http_retry_max_delay = options.get("http_retry_max_delay", 60.0)

    def collect(self):
        """Main entry point - synchronous wrapper for async collection."""
        return asyncio.run(self.collect_async())

    async def collect_async(self):
        if self.overwrite_progress or not self.load_progress():
            await self.compute_packages_async()
            self.save_progress_packages_list()  # only saves if csv_directory is provided

        async with self.get_http_client() as client:
            # Process packages sequentially to avoid overwhelming GitHub
            for package in self.packages:
                # check if we have already computed this package on previous crawl
                if "public_dependents" in package:
                    continue

                # Build start page url
                if package["id"] is not None:
                    url = self.url_init + "?package_id=" + package["id"]
                    if self.owner:
                        url += "&owner=" + self.owner
                    if self.debug is True:
                        logging.info("Package " + package["name"] + ": browsing " + url + " ...")
                else:
                    url = self.url_init
                    if self.owner:
                        url += "?owner=" + self.owner
                    if self.debug is True:
                        logging.info("Package " + self.repo + ": browsing " + url + " ...")
                package["url"] = url
                package["public_dependent_stars"] = 0

                # Fetch all pages for this package in parallel
                result, total_dependents, total_public_stars = await self.fetch_all_package_pages(client, package)

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
                package["total_dependents_number"] = (
                    total_dependents if total_dependents > 0 else total_public_dependents
                )

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
    async def compute_packages_async(self):
        async with self.get_http_client() as client:
            semaphore = asyncio.Semaphore(self.max_concurrent_requests)
            content = await self.fetch_page(client, self.url_init, semaphore)
            soup = BeautifulSoup(content, "html.parser")
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
        # Determine if pagination should be applied
        use_pagination = self.pagination

        # Calculate total number of repos to potentially paginate
        total_repos = 0
        if self.merge_packages is True:
            total_repos = len(self.all_public_dependent_repos)
        else:
            # For per-package display, count total across all packages
            for package in self.packages:
                total_repos += len(package.get("public_dependents", []))

        # Determine if we need multiple pages
        needs_pagination = use_pagination and total_repos > self.page_size

        if needs_pagination:
            # Generate paginated markdown files
            return self._build_paginated_markdown(**options)
        else:
            # Generate a single markdown file
            return self._build_single_markdown(**options)

    def _build_footer(self) -> list:
        """Build the standard footer for markdown files."""
        return [
            "",
            "_Generated using [github-dependents-info]"
            "(https://github.com/nvuillam/github-dependents-info), "
            "by [Nicolas Vuillamy](https://github.com/nvuillam)_",
        ]

    def _append_summary_table(self, md_lines: list) -> None:
        """Append the multi-package summary table when applicable."""
        if len(self.packages) <= 1 or self.merge_packages:
            return

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

    def _build_single_markdown(self, **options) -> str:
        """Build a single markdown file without pagination."""
        md_lines = [f"# Dependents stats for {self.repo}", ""]

        # Summary table
        self._append_summary_table(md_lines)

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
                self.build_repo_md_line(md_lines, repo1)
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
                        self.build_repo_md_line(md_lines, repo1)
                md_lines += [""]

        # footer
        md_lines += self._build_footer()
        md_lines_str = "\n".join(md_lines)

        # Write in file if requested
        if "file" in options:
            os.makedirs(os.path.dirname(options["file"]), exist_ok=True)
            with open(options["file"], "w", encoding="utf-8") as f:
                f.write(md_lines_str)
                if self.json_output is False:
                    print("Wrote markdown file " + options["file"])
        return md_lines_str

    def _build_paginated_markdown(self, **options) -> str:
        """Build multiple paginated markdown files."""
        # Calculate number of pages needed
        if self.merge_packages is True:
            total_repos = len(self.all_public_dependent_repos)
        else:
            # For per-package display, we'll paginate the entire content
            total_repos = sum(len(package.get("public_dependents", [])) for package in self.packages)

        total_pages = max(1, math.ceil(total_repos / self.page_size))

        if "file" not in options:
            # If no file is specified, just return the first page as a string
            return self._build_markdown_page(1, total_pages, **options)

        base_file = options["file"]
        # Split the file path to add page suffixes
        file_path = Path(base_file)
        base_name = file_path.stem
        extension = file_path.suffix
        parent_dir = file_path.parent

        # Generate each page
        os.makedirs(parent_dir, exist_ok=True)
        for page_num in range(1, total_pages + 1):
            if page_num == 1:
                page_file = base_file
            else:
                page_file = str(parent_dir / f"{base_name}-{page_num}{extension}")

            md_content = self._build_markdown_page(page_num, total_pages, file_path=file_path)

            with open(page_file, "w", encoding="utf-8") as f:
                f.write(md_content)
                if self.json_output is False:
                    print(f"Wrote markdown file {page_file}")

        # Return the first page content
        return self._build_markdown_page(1, total_pages, file_path=file_path)

    def _build_markdown_page(self, page_num: int, total_pages: int, **options) -> str:
        """Build a single page of paginated markdown."""
        md_lines = [f"# Dependents stats for {self.repo}", ""]

        # Summary table (only on first page)
        if page_num == 1:
            self._append_summary_table(md_lines)

        # Calculate start and end indices for this page
        start_idx = (page_num - 1) * self.page_size
        end_idx = start_idx + self.page_size

        # Single dependents list (merged packages)
        if self.merge_packages is True:
            if page_num == 1:
                md_lines += [
                    self.badges["total"],
                    self.badges["public"],
                    self.badges["private"],
                    self.badges["stars"],
                    "",
                ]
            md_lines += ["| Repository | Stars  |", "| :--------  | -----: |"]
            page_repos = self.all_public_dependent_repos[start_idx:end_idx]
            for repo1 in page_repos:
                self.build_repo_md_line(md_lines, repo1)
        # Dependents by package
        else:
            # For per-package display, we need to paginate across all packages
            all_package_items = []
            for package in self.packages:
                for repo1 in package.get("public_dependents", []):
                    all_package_items.append((package, repo1))

            # If this is page 1 and there are empty packages, show them first
            if page_num == 1:
                for package in self.packages:
                    if len(package.get("public_dependents", [])) == 0:
                        md_lines += ["## Package " + package["name"], ""]
                        md_lines += ["No dependent repositories"]
                        md_lines += [""]

            page_items = all_package_items[start_idx:end_idx]

            # Determine which packages are being continued from previous page
            packages_started_before_page = set()
            if start_idx > 0:
                for package, _ in all_package_items[:start_idx]:
                    packages_started_before_page.add(package["name"])
                # Remove packages that have finished before this page
                packages_on_this_page = set()
                for package, _ in page_items:
                    packages_on_this_page.add(package["name"])
                packages_started_before_page = packages_started_before_page.intersection(packages_on_this_page)

            # Group items by package for display
            current_package_name = None
            for package, repo1 in page_items:
                if package["name"] != current_package_name:
                    if current_package_name is not None:
                        md_lines += [""]  # Add spacing between packages
                    current_package_name = package["name"]

                    # Only add header and badges if this package starts on this page
                    is_continuation = package["name"] in packages_started_before_page

                    md_lines += ["## Package " + package["name"], ""]
                    if not is_continuation:
                        md_lines += [
                            package["badges"]["total"],
                            package["badges"]["public"],
                            package["badges"]["private"],
                            package["badges"]["stars"],
                            "",
                        ]
                    md_lines += ["| Repository | Stars  |", "| :--------  | -----: |"]

                self.build_repo_md_line(md_lines, repo1)

        md_lines += [""]

        # Add page navigation at bottom if multiple pages
        if total_pages > 1:
            nav_line = self._build_page_navigation(page_num, total_pages, **options)
            md_lines += [f'<div align="center">{nav_line}</div>', ""]

        # footer
        md_lines += self._build_footer()

        return "\n".join(md_lines)

    def _build_page_navigation(self, page_num: int, total_pages: int, **options) -> str:
        """Build navigation links for pagination."""
        nav_parts = []

        # Get the file path info if provided
        file_path = options.get("file_path")
        if file_path:
            base_name = file_path.stem
            extension = file_path.suffix
        else:
            base_name = "page"
            extension = ".md"

        # Previous link
        if page_num > 1:
            if page_num == 2:
                prev_file = f"{base_name}{extension}"
            else:
                prev_file = f"{base_name}-{page_num - 1}{extension}"
            nav_parts.append(f'<a href="{prev_file}">⬅️ Previous</a>')
        else:
            nav_parts.append("<span>⬅️ Previous</span>")

        # Page indicator
        nav_parts.append(f"<span>Page {page_num} of {total_pages}</span>")

        # Next link
        if page_num < total_pages:
            next_file = f"{base_name}-{page_num + 1}{extension}"
            nav_parts.append(f'<a href="{next_file}">Next ➡️</a>')
        else:
            nav_parts.append("<span>Next ➡️</span>")

        return " | ".join(nav_parts)

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

    def get_http_client(self):
        """Create an httpx client with retry configuration."""
        transport = httpx.AsyncHTTPTransport(retries=10)
        return httpx.AsyncClient(
            transport=transport,
            timeout=30.0,
            follow_redirects=True,
        )

    def _compute_retry_delay(self, attempt: int, response: httpx.Response | None = None) -> float:
        """Calculate delay before next retry using headers or exponential backoff."""
        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    wait_seconds = float(retry_after)
                    if wait_seconds > 0:
                        return min(wait_seconds, self.http_retry_max_delay)
                except ValueError:
                    pass
        delay = self.http_retry_initial_delay * (self.http_retry_backoff ** max(attempt - 1, 0))
        return min(delay, self.http_retry_max_delay)

    async def fetch_page(self, client, url, semaphore):
        """Fetch a single page with rate limiting."""
        last_error = None
        for attempt in range(1, self.http_retry_attempts + 1):
            try:
                async with semaphore:
                    await asyncio.sleep(self.time_delay)
                    response = await client.get(url)
                response.raise_for_status()
                return response.text
            except httpx.HTTPStatusError as exc:  # type: ignore[attr-defined]
                last_error = exc
                status_code = exc.response.status_code
                should_retry = status_code == 429 or 500 <= status_code < 600
                if not should_retry or attempt == self.http_retry_attempts:
                    raise
                delay = self._compute_retry_delay(attempt, response=exc.response)
                if self.debug:
                    logging.warning(
                        "HTTP %s while fetching %s (attempt %s/%s). Retrying in %.1fs",
                        status_code,
                        url,
                        attempt,
                        self.http_retry_attempts,
                        delay,
                    )
                await asyncio.sleep(delay)
            except (httpx.RequestError, httpx.TimeoutException) as exc:  # type: ignore[attr-defined]
                last_error = exc
                if attempt == self.http_retry_attempts:
                    raise
                delay = self._compute_retry_delay(attempt)
                if self.debug:
                    logging.warning(
                        "Request error while fetching %s (attempt %s/%s): %s. Retrying in %.1fs",
                        url,
                        attempt,
                        self.http_retry_attempts,
                        exc,
                        delay,
                    )
                await asyncio.sleep(delay)
        if last_error is not None:
            raise last_error

    async def fetch_all_package_pages(self, client, package):
        """Fetch all pages for a package in parallel."""
        # First, get the initial page to determine total dependents and discover all page URLs
        url = package["url"]
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        # Fetch initial page
        initial_content = await self.fetch_page(client, url, semaphore)
        soup = BeautifulSoup(initial_content, "html.parser")

        # Get total number of dependents from UI
        svg_item = soup.find("a", {"class": "btn-link selected"})
        if svg_item is not None:
            a_around_svg = svg_item
            total_dependents = self.get_int(
                a_around_svg.text.replace("Repositories", "").replace("Repository", "").strip()
            )
        else:
            total_dependents = 0

        # Discover all page URLs first
        pages_content = [initial_content]  # Store the initial page content
        urls_to_fetch = []  # Additional pages to fetch
        page_number = 1
        current_soup = soup

        while True:
            next_link = None
            paginate_container = current_soup.find("div", {"class": "paginate-container"})
            if paginate_container is not None:
                for u in paginate_container.find_all("a"):
                    if u.text == "Next":
                        # Check if we've reached the max pages limit
                        if self.max_scraped_pages > 0 and page_number >= self.max_scraped_pages:
                            if self.debug is True:
                                logging.info(f"  - reached max scraped pages limit ({self.max_scraped_pages})")
                            break
                        next_link = u["href"]
                        page_number += 1
                        if self.debug is True:
                            logging.info(f"  - discovered page {page_number}")
                        break

            if next_link is None:
                break

            urls_to_fetch.append(next_link)
            # Fetch the next page to discover more pages
            try:
                current_content = await self.fetch_page(client, next_link, semaphore)
                current_soup = BeautifulSoup(current_content, "html.parser")
            except (httpx.RequestError, httpx.TimeoutException) as e:
                if self.debug:
                    logging.warning(f"Failed to fetch page during discovery: {e}")
                break

        # Fetch additional pages in parallel if any
        if urls_to_fetch:
            if self.debug:
                logging.info(f"  - fetching {len(urls_to_fetch)} additional pages in parallel...")
            tasks = [self.fetch_page(client, page_url, semaphore) for page_url in urls_to_fetch]
            additional_pages = await asyncio.gather(*tasks, return_exceptions=True)
            pages_content += additional_pages

        # Process all pages
        result = []

        for page_content in pages_content:
            if isinstance(page_content, Exception):
                if self.debug:
                    logging.warning(f"Failed to fetch page: {page_content}")
                continue

            soup = BeautifulSoup(page_content, "html.parser")

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
                result.append(result_item)

        # Remove duplicates using dictionary comprehension
        unique_result = list({item["name"]: item for item in result}.values())

        # Calculate total stars after deduplication
        total_public_stars = sum(item["stars"] for item in unique_result)

        return unique_result, total_dependents, total_public_stars

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
