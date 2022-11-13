import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup


class GithubDependentsInfo:
    def __init__(self, repo, **options) -> None:
        self.repo = repo
        self.url_init = "https://github.com/{}/network/dependents".format(self.repo)
        self.url_starts_with = "/{}/network/dependents".format(self.repo) + "?package_id="
        self.debug = True if "debug" in options and options["debug"] is True else False
        self.total_sum = 0
        self.total_public_sum = 0
        self.total_private_sum = 0
        self.dependent_repos = []

    def collect(self, **options):
        # List packages
        self.compute_packages()

        # for each package, get count by parsing GitHub HTML
        for package in self.dependent_repos:
            nextExists = True
            result = []

            # Build start page url
            if package["id"] is not None:
                url = self.url_init + "?package_id=" + package["id"]
                if self.debug is True:
                    print("Package " + package["name"] + ": browsing " + url + " ...")
            else:
                url = self.url_init + ""
                if self.debug is True:
                    print("Package " + self.repo + ": browsing" + url + " ...")
            package["url"] = url
            page_number = 1

            # Get total number of dependents from UI
            r = requests_retry_session().get(url)
            soup = BeautifulSoup(r.content, "html.parser")
            svg_item = soup.find("svg", {"class": "octicon-code-square"})
            if svg_item is not None:
                a_around_svg = svg_item.parent
                total_dependents = int(a_around_svg.text.replace("Repositories", "").strip())
            else:
                total_dependents = 0

            # Parse all dependent packages pages
            while nextExists:
                r = requests_retry_session().get(url)
                soup = BeautifulSoup(r.content, "html.parser")
                result = result + [
                    "{}/{}".format(
                        t.find("a", {"data-repository-hovercards-enabled": ""}).text,
                        t.find("a", {"data-hovercard-type": "repository"}).text,
                    )
                    for t in soup.findAll("div", {"class": "Box-row"})
                ]
                nextExists = False
                paginate_container = soup.find("div", {"class": "paginate-container"})
                if paginate_container is not None:
                    for u in paginate_container.findAll("a"):
                        if u.text == "Next":
                            nextExists = True
                            url = u["href"]
                            page_number = page_number + 1
                            if self.debug is True:
                                print("  - browsing page " + str(page_number))

            # Manage results for package
            result.sort()
            if self.debug is True:
                for r in result:
                    print(r)

            # Build package stats
            total_public_dependents = len(result)
            package["public_dependents"] = result
            package["public_dependents_number"] = total_public_dependents
            package["private_dependents_number"] = total_dependents - total_public_dependents
            package["total_dependents_number"] = total_dependents if total_dependents > 0 else total_public_dependents

            # Build total stats
            self.total_sum += package["total_dependents_number"]
            self.total_public_sum += package["public_dependents_number"]
            self.total_private_sum += package["private_dependents_number"]

            # Output
            if self.debug is True:
                print("Total for package: " + str(total_public_dependents))
                print("")

        # Build final result
        return self.build_result()

    # Get first url to see if there are multiple packages
    def compute_packages(self):
        r = requests_retry_session().get(self.url_init)
        soup = BeautifulSoup(r.content, "html.parser")
        for a in soup.find_all("a", href=True):
            if a["href"].startswith(self.url_starts_with):
                package_id = a["href"].rsplit("=", 1)[1]
                package_name = a.find("span").text.strip()
                if self.debug is True:
                    print(package_name)
                self.dependent_repos += [{"id": package_id, "name": package_name}]
        if len(self.dependent_repos) == 0:
            self.dependent_repos = [{"id": None, "name": self.repo}]

    # Build output results
    def build_result(self):
        if self.debug is True:
            print("Total dependents: " + str(self.total_sum))
        return {
            "public_dependents_repos": self.dependent_repos,
            "total_dependents_number": self.total_sum,
            "public_dependents_number": self.total_public_sum,
            "private_dependents_number": self.total_private_sum,
        }

    def print_result(self):
        print("Total: " + str(self.total_sum))
        print("Public: " + str(self.total_public_sum))
        print("Private: " + str(self.total_private_sum))

    def build_markdown(self, **options) -> str:
        md_lines = [f"# Dependents stats for {self.repo}", ""]
        badge_1 = self.build_badge("Dependents", self.total_sum)
        badge_2 = self.build_badge("Public%20Dependents", self.total_public_sum)
        badge_3 = self.build_badge("Private%20Dependents", self.total_private_sum)
        md_lines += [
            badge_1,
            badge_2,
            badge_3,
            "",
        ]

        for dep_repo in self.dependent_repos:
            md_lines += ["## Package " + dep_repo["name"], ""]
            if len(dep_repo["public_dependents"]) == 0:
                md_lines += ["No dependent repositories"]
            else:
                badge_1 = self.build_badge("Dependents", dep_repo["total_dependents_number"], dep_repo["url"])
                badge_2 = self.build_badge("Public%20Dependents", dep_repo["public_dependents_number"], dep_repo["url"])
                badge_3 = self.build_badge(
                    "Private%20Dependents", dep_repo["private_dependents_number"], dep_repo["url"]
                )
                md_lines += [
                    badge_1,
                    badge_2,
                    badge_3,
                    "",
                ]
                for repo1 in dep_repo["public_dependents"]:
                    md_lines += [f"  - [{repo1}](https://github.com/{repo1})"]
            md_lines += [""]
        md_lines += ["_Generated by [github-dependents-info](https://github.com/nvuillam/github-dependents-info)_"]
        md_lines_str = "\n".join(md_lines)

        # Write in file if requested
        if "file" in options:
            with open(options["file"], "w", encoding="utf-8") as f:
                f.write(md_lines_str)
                if self.debug is True:
                    print("Wrote markdown file " + options["file"])
        return md_lines_str

    def build_badge(self, type, nb, url=None):
        if url is None:
            url = f"https://github.com/{self.repo}/network/dependents"
        return f"[![](https://img.shields.io/static/v1?label={type}&message={str(nb)}&color=informational&logo=slickpic]({url})"


    def requests_retry_session(
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