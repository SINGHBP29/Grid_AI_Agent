from .weather import WeatherTool
from .developer import DeveloperTool
from .research import ResearchTool

class ToolRegistry:
    """
    ToolRegistry manages all available tools.

    It allows:
    - Registering tools
    - Fetching tools by name
    - Listing tools for LLM selection
    """

    def __init__(self):
        # Dictionary: { tool_name: tool_instance }
        self._tools = {}

    def register(self, tool):
        """
        Register a tool instance.
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")

        self._tools[tool.name] = tool

    def get(self, name):
        """
        Return tool instance by name.
        """
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found.")

        return self._tools[name]

    def list_tools(self):
        """
        Return tool metadata for LLM decision-making.
        """
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self._tools.values()
        ]

    def has_tool(self, name):
        """
        Returns True if the tool is registered, else False.
        """
        return name in self._tools


# -----------------------------------------------------
# Test Block
# -----------------------------------------------------

if __name__ == "__main__":

    # Create registry
    registry = ToolRegistry()
    weather_url = "https://api.open-meteo.com/v1/forecast"

    # Register tools
    registry.register(WeatherTool(weather_url))
    registry.register(DeveloperTool())
    registry.register(ResearchTool())

    # Show available tools
    print("\nAvailable Tools for LLM:")
    for tool in registry.list_tools():
        print(f"- {tool['name']}: {tool['description']}")

    # Simulate LLM choosing a tool
    selected_tool_name = "weather"

    try:
        tool = registry.get(selected_tool_name)

        # Call tool with example input
        result = tool.run(city="London")

        print("\nTool Output:")
        print(result)

    except ValueError as e:
        print(f"\nError: {e}")