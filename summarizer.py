import json
from llm import OllamaLLM

SYSTEM_PROMPT_SUMMARIZE = """
You are a summarizer. Summarize the results from the tools in a concise, human-readable way.
Return JSON in the following format:
{
  "summary": "..."
}
"""

SYSTEM_PROMPT_VALIDATE = """You are a validator. Check if the summary answers the original query.
Return ONLY JSON:
{
  "valid": true
}

Rules:
- Ignore minor wording differences.
- Only check if the content contains the answer to the user query.
- Do not add any extra text.
"""

class SummarizerLLM:
    """
    Handles LLM summarization and validation of tool outputs.
    """

    def __init__(self, model="llama3"):
        self.llm = OllamaLLM(model=model)

    def summarize(self, tool_results: list) -> str:
        """
        Summarizes tool outputs.
        """
        query_text = "\n".join([str(res) for res in tool_results])

        response = self.llm.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_SUMMARIZE},
                {"role": "user", "content": query_text}
            ],
            format="json"
        )

        try:
            data = json.loads(response["message"]["content"])
            return data.get("summary", "")
        except Exception:
            return "Unable to summarize results."

    def validate(self, user_query: str, summary: str) -> bool:
        """
        Validates if summary answers the original query.
        """
        response = self.llm.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_VALIDATE},
                {"role": "user", "content": f"Query: {user_query}\nSummary: {summary}"}
            ],
            format="json"
        )

        try:
            data = json.loads(response["message"]["content"])
            return data.get("valid", False)
        except Exception:
            return False
if "__main__" == __name__:
    summarizer = SummarizerLLM()
    print(summarizer.summarize())