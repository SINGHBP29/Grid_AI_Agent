import ollama


class OllamaLLM:
    """
    Handles connection to Ollama model.
    """

    def __init__(self, model: str = "llama3"):
        self.model = model
        print(f"✅ OllamaLLM initialized with model: {self.model}")

    def chat(self, messages, format=None):
        """
        Generic chat method.
        """
        return ollama.chat(
            model=self.model,
            messages=messages,
            format=format
        )


if __name__ == "__main__":

    # Initialize LLM
    llm = OllamaLLM()

    # Simple test message
    response = llm.chat(
        messages=[
            {"role": "user", "content": "Say hello in one sentence."}
        ]
    )

    print("\nLLM Response:")
    print(response["message"]["content"])