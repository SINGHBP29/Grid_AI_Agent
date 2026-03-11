from abc import ABC, abstractmethod


class BaseTool(ABC):
    """
    BaseTool is an abstract base class.

    All tools (weather, research, developer, etc.)
    must inherit from this class.

    This ensures every tool:
    - Has a name
    - Has a description
    - Implements a run() method
    """

    name: str
    description: str

    @abstractmethod
    def run(self, **kwargs):
        """
        run() is the execution method of the tool.

        It receives structured input (not natural language)
        and returns raw structured data.

        IMPORTANT:
        # This method does NOT use LLM.
        Tools are deterministic executors.
        """
        pass