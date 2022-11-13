import requests
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
            page_number = 1

            # Get total number of dependents from UI
            r = requests.get(url)
            soup = BeautifulSoup(r.content, "html.parser")
            svg_item = soup.find("svg", {"class": "octicon-code-square"})
            a_around_svg = svg_item.parent
            total_dependents = int(a_around_svg.text.replace("Repositories", "").strip())

            # Parse all dependent packages pages
            while nextExists:
                r = requests.get(url)
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
            package["total_dependents_number"] = total_dependents

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
        r = requests.get(self.url_init)
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
