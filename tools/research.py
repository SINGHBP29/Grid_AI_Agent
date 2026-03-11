import requests
from .base import BaseTool


class ResearchTool(BaseTool):
    """
    ResearchTool retrieves summary information from Wikipedia
    using the official MediaWiki API.

    This tool is designed for knowledge-based queries.
    It returns structured JSON containing title and summary.
    """

    name = "research"
    description = "Search Wikipedia and return summary information"

    def run(self, query: str):
        """
        Fetch a plain-text summary of the given topic from Wikipedia.
        """

        url = "https://en.wikipedia.org/w/api.php"

        # MediaWiki API parameters
        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": True,     # Return plain text (no HTML)
            "titles": query,
            "format": "json",
            "redirects": 1           # Automatically resolve redirects
        }

        headers = {
            "User-Agent": "ResearchAgent/1.0 (bhsingh@griddynamics.com)"
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code != 200:
                return {"error": f"Wikipedia returned status {response.status_code}"}

            data = response.json()

            pages = data.get("query", {}).get("pages", {})

            # Wikipedia returns pages as a dictionary keyed by page ID
            for page in pages.values():
                if "extract" in page:
                    return {
                        "title": page.get("title"),
                        "summary": page.get("extract"),
                        "url": page.get("link")
                    }

            return {"error": "Topic not found"}

        except requests.RequestException as e:
            return {"error": f"Wikipedia request failed: {str(e)}"}


# Testing block
if __name__ == "__main__":
    tool = ResearchTool()
    result = tool.run("Artificial intelligence")
    print("\nResearch Tool Test Result:")
    print(result)
# if __name__ == "__main__":
#     tool = ResearchTool()
#     result = asyncio.run(tool.run("Artificial intelligence"))
#     print(result)