import os
import json
import logging
from tempfile import TemporaryDirectory
import requests
from bs4 import BeautifulSoup
from pkginfo import Wheel, SDist



logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PackageCrawler:
    def __init__(self, url="https://pypi.org/simple/"):
        """
        Initializes the PackageCrawler class with a default url to 'https://pypi.org/simple/' or a provided url.
        
        Parameters:
            url (str): The URL to be used for crawling packages. Default is 'https://pypi.org/simple/'.
        
        Returns:
            None
        """
        self.repo_url = url
        self.packages = self._get_packages(self.repo_url)
    
    def _add_base_url(self, url):
        return f"{self.repo_url.rstrip('/simple/')}{url}"

    def _get_packages(self, url):
        """
        Retrieves a list of packages from the specified URL.

        Parameters:
            url (str): The URL to retrieve the packages from.

        Returns:
            list: A list of packages, where each package is represented as a tuple containing the package name (str) and the package URL (str).

        Raises:
            Exception: If there is an error making the request or parsing the HTML content.

        Notes:
            - If the 'packages.json' file already exists, the function will skip the request and load the packages from the file instead.
            - The function uses a cached session to make the request and caches the response for future use.
            - The function parses the HTML content of the response and extracts the package links.
            - The function saves the packages as a JSON file named 'packages.json' for future use.
        """

        if os.path.exists('packages.json'):
            logger.debug("packages.json exists, skipping request")
            with open('packages.json') as f:
                packages = json.load(f)
        else:
            self.logger.debug("packages.json does not exist, making request")

            links = get_links(self.repo_url)

            # Take links and create a list with both the name and the url which can then be saved as a json
            packages = [(link.string,  self._add_base_url(link['href'])) for link in links]
            # save packages as a json file
            with open('packages.json', 'w') as f:
                json.dump(packages, f, indent=2)

        return packages
    
def get_links(url) -> list:
    """
    Retrieves a list of links from the specified URL.

    Parameters:
        url (str): The URL to retrieve the links from.

    Returns:
        list: A list of links.

    Raises:
        Exception: If there is an error making the request or parsing the HTML content.

    Notes:
        - The function uses a cached session to make the request and caches the response for future use.
        - The function parses the HTML content of the response and extracts the package links."""
    try:
        res = requests.get(url)
        logger.debug("Successfully made the request to %s", url)
    except Exception as e:
        logger.error("Failed to make the request: %s", e)
        # Handle the exception or exit gracefully
    logger.debug("Parsing the HTML content...")
    packages_soup = BeautifulSoup(res.text, 'html.parser')
    logger.debug("HTML parsing complete.")

    logger.debug("Extracting links...")
    links = packages_soup.find_all('a')
    logger.debug("Extracted %d links.", len(links))
    return [(link.string, link['href']) for link in links]
    

class Package:
    def __init__(self, name, repo_url="https://pypi.org/simple/"):
        self.name = name
        self.repo_url = repo_url
        self.package_versions = get_links(self.repo_url + name)
        self.package_versions.sort(key=lambda x: x[0])
        self.latest_version = self.package_versions[-1]
        self.metadata = self.extract_metadata(*self.latest_version)

    def extract_metadata(self, filename, url):
        with TemporaryDirectory() as tmpdir:
            logger.debug("Downloading %s from %s to %s", filename, url, tmpdir)
            response = requests.get(url)
            logger.debug("Received response with status code %d", response.status_code)
            pkgpath = os.path.join(tmpdir, filename)
            with open(pkgpath, 'wb') as f:
                f.write(response.content)
            logger.debug("Saved package to %s", pkgpath)

            if pkgpath.endswith('.tar.gz'):
                dist = SDist
            elif pkgpath.endswith('.whl'): 
                dist = Wheel
            pkg = dist(pkgpath)       
            
            return pkg


package = Package("pandas")