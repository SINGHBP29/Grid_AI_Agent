import requests
from .base import BaseTool


class DeveloperTool(BaseTool):
    """
    DeveloperTool helps developers search for resources.

    It can fetch:
    - Top starred repositories from GitHub
    - Top voted questions from StackOverflow

    The user can choose which source to search.
    """

    name = "developer"
    description = "Search GitHub or StackOverflow for programming topics."

    def run(self, query: str, source: str = "github"):
        """
        Main entry point of the tool.

        Parameters:
        - query  : What the user wants to search
        - source : 'github' or 'stackoverflow'

        Returns only the selected source results.
        """

        source = source.lower()

        if source == "github":
            return self._search_github(query)

        elif source == "stackoverflow":
            return self._search_stackoverflow(query)

        else:
            return {
                "error": "Invalid source. Please use 'github' or 'stackoverflow'."
            }

    # -----------------------------------------------------
    # GitHub Search
    # -----------------------------------------------------

    def _search_github(self, query: str):
        """
        Search GitHub repositories sorted by stars.
        Returns top 5 repositories.
        """

        url = "https://api.github.com/search/repositories"

        params = {
            "q": query,
            "sort": "stars",        # Sort by popularity
            "order": "desc",
            "per_page": 5           # Limit results
        }

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "DeveloperTool/1.0"
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()

            repositories = []

            # Extract only useful fields
            for repo in data.get("items", []):
                repositories.append({
                    "name": repo.get("name"),
                    "url": repo.get("html_url"),
                    "stars": repo.get("stargazers_count"),
                    "description": repo.get("description")
                })

            return repositories

        except requests.RequestException as e:
            return {"error": f"GitHub API error: {str(e)}"}

    # -----------------------------------------------------
    # StackOverflow Search
    # -----------------------------------------------------

    def _search_stackoverflow(self, query: str):
        """
        Search StackOverflow questions sorted by votes.
        Returns top 5 questions.
        """

        url = "https://api.stackexchange.com/2.3/search"

        params = {
            "order": "desc",
            "sort": "votes",          # Highest voted first
            "intitle": query,
            "site": "stackoverflow",
            "pagesize": 5
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            questions = []

            # Extract only relevant information
            for item in data.get("items", []):
                questions.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "score": item.get("score"),
                    "is_answered": item.get("is_answered")
                })

            return questions

        except requests.RequestException as e:
            return {"error": f"StackOverflow API error: {str(e)}"}



if __name__ == "__main__":

    tool = DeveloperTool()

    print("\n--- GitHub Results ---")
    github_results = tool.run("binary search python", source="github")
    print(github_results)

    print("\n--- StackOverflow Results ---")
    so_results = tool.run("binary search python", source="stackoverflow")
    print(so_results)