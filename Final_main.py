#!/usr/bin/env python3
"""
Final_main.py
─────────────────────────────────────────────
Entry point for the Hybrid Multi-Agent System.

Responsibilities:
  - Boot all components (LLM, Registry, Tools, Summarizer)
  - Expose run_agent(query) for both terminal and UI
  - Launch Gradio UI

✅ FIX: Dispatcher now handles its own intelligent replanning
        via a while loop with feedback. The retry loop here in
        run_agent() only handles summarizer-level validation.
        Redundant blind retries removed.
─────────────────────────────────────────────
"""

import time
import gradio as gr

from tools.tool_registry import ToolRegistry
from tools.weather        import WeatherTool
from tools.developer      import DeveloperTool
from tools.research       import ResearchTool
from llm                  import OllamaLLM
from summarizer           import SummarizerLLM
from dispatcher           import dispatch


# ═══════════════════════════════════════════════
#  BOOT — runs once when the module is imported
# ═══════════════════════════════════════════════

print("\n🚀 Booting Multi-Agent System...")

# 1. LLM (shared across planner + summarizer)
llm = OllamaLLM(model="llama3")

# 2. Tool Registry
registry = ToolRegistry()
registry.register(WeatherTool("https://api.open-meteo.com/v1/forecast"))
registry.register(DeveloperTool())
registry.register(ResearchTool())

print("\n📦 Registered Tools:")
for t in registry.list_tools():
    print(f"   • {t['name']}: {t['description']}")

# 3. Summarizer
summarizer = SummarizerLLM(model="llama3")

print("\n✅ System Ready.\n")


# ═══════════════════════════════════════════════
#  CORE AGENT FUNCTION
# ═══════════════════════════════════════════════

def run_agent(user_query: str) -> str:
    """
    Main agent pipeline:

    1. dispatcher.dispatch()
         └─ detect_tools()      → LLM picks tools
                └─ [WHILE LOOP] → replans with feedback if tools fail
         └─ extract_arguments() → LLM pulls args
         └─ run_tools()         → WeatherTool / ResearchTool / DeveloperTool

    2. SummarizerLLM.summarize()  → human-readable answer
    3. SummarizerLLM.validate()   → retry summarization if answer is off

    ✅ FIX: dispatch() handles its own replanning internally.
            This loop only retries the SUMMARIZER step, not dispatch.

    Returns the final summary string.
    """

    MAX_SUMMARY_RETRIES = 3

    # ── Step 1: Dispatch — handles its own replanning internally ──
    print(f"\n{'═'*45}")
    print(f"🚀 Running agent for: {user_query}")
    print(f"{'═'*45}")

    output     = dispatch(user_query, llm, registry)
    tools_used = output["tools_used"]
    results    = output["results"]
    attempts   = output["attempts"]

    print(f"\n✅ Dispatch complete in {attempts} attempt(s)")
    print(f"🛠️  Tools used: {tools_used}")
    print(f"📊 Raw Results: {results}")

    # ── Step 2 & 3: Summarize + Validate (with retry) ──
    summary = None

    for s_attempt in range(1, MAX_SUMMARY_RETRIES + 1):
        print(f"\n📝 Summarizer attempt {s_attempt}/{MAX_SUMMARY_RETRIES}")

        raw_results_list = list(results.values())
        summary = summarizer.summarize(raw_results_list)
        print(f"Summary: {summary}")

        is_valid = summarizer.validate(user_query, summary)
        print(f"✔️  Valid: {is_valid}")

        if is_valid:
            print("✅ Summary accepted.")
            break

        print("⚠️  Summary did not fully answer query. Retrying summarizer...")

    return _format_final_output(tools_used, results, summary, attempts)


# ═══════════════════════════════════════════════
#  OUTPUT FORMATTER
# ═══════════════════════════════════════════════

def _format_final_output(
    tools_used: list,
    results: dict,
    summary: str,
    attempts: int
) -> str:
    """
    Builds a clean markdown string for the UI.
    ✅ Now also shows how many dispatcher planning attempts were needed.
    """
    lines = []
    lines.append(f"### 🛠️ Tools Used: `{'`, `'.join(tools_used)}`")
    lines.append(f"*Dispatcher planning attempts: {attempts}*\n")
    lines.append("---")
    lines.append("### 📊 Raw Tool Results\n")

    for tool_name, result in results.items():
        lines.append(f"**{tool_name.capitalize()}:**")
        if isinstance(result, list):
            for item in result:
                lines.append(f"- {item}")
        elif isinstance(result, dict):
            for k, v in result.items():
                lines.append(f"- **{k}**: {v}")
        else:
            lines.append(str(result))
        lines.append("")

    lines.append("---")
    lines.append("### 🤖 AI Summary\n")
    lines.append(summary if summary else "_No summary generated._")

    return "\n".join(lines)


# ═══════════════════════════════════════════════
#  GRADIO UI
# ═══════════════════════════════════════════════

custom_css = """
body {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    color: white;
}
.gradio-container {
    background: transparent !important;
}
textarea, input {
    background-color: #1e1e2f !important;
    color: white !important;
    border: 1px solid #555 !important;
    border-radius: 8px !important;
}
button {
    background: linear-gradient(to right, #00c6ff, #0072ff) !important;
    color: white !important;
    font-weight: bold !important;
    border-radius: 8px !important;
}
"""


def gradio_run(user_query: str):
    """
    Streaming generator for Gradio — shows progress steps
    then yields the final result.
    """
    if not user_query.strip():
        yield "⚠️ Please enter a valid query."
        return

    yield "⏳ **Starting agent...**"
    time.sleep(0.3)

    yield "🧠 **LLM is selecting tools...**"
    time.sleep(0.3)

    yield "📋 **Extracting arguments...**"
    time.sleep(0.3)

    yield "🔧 **Running tools (Weather / Research / Developer)...**"
    time.sleep(0.3)

    yield "📝 **Summarizing results...**"

    # Run the actual agent
    result = run_agent(user_query)

    yield result


with gr.Blocks(css=custom_css, title="Hybrid Multi-Agent System") as demo:

    gr.Markdown("""
    # 🤖 Hybrid Multi-Agent System
    **Powered by:** Weather 🌤️ • Research 📚 • Developer 💻 • LLM Planner 🧠 • Summarizer ✍️
    """)

    with gr.Row():
        query_input = gr.Textbox(
            placeholder='e.g. "Weather in Delhi, explain climate change, and show quicksort on GitHub"',
            lines=3,
            label="🔍 Enter Your Query"
        )

    run_btn = gr.Button("🚀 Run Agent", variant="primary")

    output_display = gr.Markdown(label="Agent Response")

    run_btn.click(
        fn=gradio_run,
        inputs=query_input,
        outputs=output_display
    )

    gr.Examples(
        examples=[
            ["What is the weather in Mumbai?"],
            ["Explain machine learning"],
            ["Show me top quicksort repos on GitHub"],
            ["Weather in Delhi, explain climate change, and find Python sorting algorithms on GitHub"],
        ],
        inputs=query_input
    )


# ═══════════════════════════════════════════════
#  ENTRY POINTS
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--terminal":
        query = input("\nEnter your query: ").strip()
        print("\n" + run_agent(query))
    else:
        demo.launch()