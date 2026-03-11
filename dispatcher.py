import json

#  Responsibilities:
#    1. Ask LLM which tools are needed     (detect_tools)
#    2. Ask LLM to extract arguments       (extract_arguments)
#    3. Run every tool via ToolRegistry    (run_tools)
#    4. Return raw results dict            (dispatch)
#
#  ✅ FIX: dispatch() now uses a WHILE LOOP for intelligent replanning.
#          If tools return errors, feedback is passed back to detect_tools()
#          so the LLM can replan — not just blindly retry.

VALID_TOOLS = {"weather", "developer", "research"}
MAX_REPLAN_ATTEMPTS = 3


# ─────────────────────────────────────────────
#  STEP 1 — LLM selects which tools to call
# ─────────────────────────────────────────────

def detect_tools(llm, user_query: str, feedback: str = None) -> list[str]:
    """
    Sends the user query to OllamaLLM and asks it to decide
    which tools are needed.

    ✅ FIX: Accepts optional `feedback` string.
    If this is a retry, feedback from previous failed attempt
    is appended so the LLM can make a better decision.

    Returns: ["weather", "research"]  ← example
    """

    SYSTEM_PROMPT = """
You are a tool selector for a multi-agent system.

Available tools:
- "weather"   : weather, temperature, forecast, wind, rain for a city
- "developer" : coding topics, GitHub repos, StackOverflow questions
- "research"  : general knowledge, definitions, Wikipedia-style explanations

Given the user query, return ONLY valid JSON — no extra text:
{
  "tools": ["tool1", "tool2"]
}

Rules:
- Include ONLY tools that are genuinely needed.
- You can return one, two, or all three tools.
- Only use these exact names: "weather", "developer", "research"
- If a previous attempt failed, pick DIFFERENT or MORE APPROPRIATE tools.
"""

    # ✅ Append feedback to user message if this is a retry
    user_message = user_query
    if feedback:
        user_message += f"\n\n[REPLANNING FEEDBACK]: {feedback}. Please select different or corrected tools."

    response = llm.chat(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message}
        ],
        format="json"
    )

    try:
        data  = json.loads(response["message"]["content"])
        tools = data.get("tools", [])
        # Safety: filter out any hallucinated tool names
        tools = [t for t in tools if t in VALID_TOOLS]
        return tools if tools else ["research"]   # safe fallback
    except Exception:
        return ["research"]


# ─────────────────────────────────────────────
#  STEP 2 — LLM extracts arguments per tool
# ─────────────────────────────────────────────

def extract_arguments(llm, user_query: str, tools_needed: list[str]) -> dict:
    """
    Sends a second LLM call to extract structured arguments
    for each detected tool.

    Returns:
    {
        "weather":   {"city": "Mumbai"},
        "developer": {"query": "quicksort", "source": "github"},
        "research":  {"query": "machine learning"}
    }
    """

    tool_list_str = ", ".join(tools_needed)

    SYSTEM_PROMPT = f"""
You are an argument extractor for these tools: {tool_list_str}.

Return ONLY valid JSON — no markdown, no extra text:
{{
  "weather":   {{"city": "<city name or null>"}},
  "developer": {{"query": "<search term or null>", "source": "github"}},
  "research":  {{"query": "<topic or null>"}}
}}

Rules:
- Only fill arguments for tools in this list: {tool_list_str}
- Set values to null if not applicable.
- Never add extra keys.
"""

    response = llm.chat(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_query}
        ],
        format="json"
    )

    try:
        all_args = json.loads(response["message"]["content"])
        # Return only the tools we actually need
        return {
            tool: all_args[tool]
            for tool in tools_needed
            if tool in all_args
        }
    except Exception:
        return {tool: {} for tool in tools_needed}


# ─────────────────────────────────────────────
#  STEP 3 — Execute every detected tool
# ─────────────────────────────────────────────

def run_tools(registry, tool_arguments: dict) -> dict:
    """
    Calls registry.get(tool_name).run(**args) for each tool.

    Returns:
    {
        "weather":   {"city": "Mumbai", "temperature": 32, ...},
        "research":  {"title": "...", "summary": "..."},
        "developer": [{"name": "...", "stars": 4200, ...}]
    }
    """

    results = {}

    for tool_name, args in tool_arguments.items():
        print(f"\n🔧 Running [{tool_name}] with args: {args}")

        try:
            tool = registry.get(tool_name)

            # Strip null values — tools don't accept None
            clean_args = {k: v for k, v in args.items() if v is not None}

            results[tool_name] = tool.run(**clean_args)

        except Exception as e:
            results[tool_name] = {"error": str(e)}

    return results


# ─────────────────────────────────────────────
#  MASTER DISPATCHER  ✅ FIXED WITH WHILE LOOP
# ─────────────────────────────────────────────

def dispatch(user_query: str, llm, registry) -> dict:
    """
    Full 3-step pipeline with intelligent WHILE LOOP replanning:

      Step 1 → LLM picks tools         (detect_tools)
      Step 2 → LLM extracts arguments  (extract_arguments)
      Step 3 → Tools are executed      (run_tools)

    ✅ FIX: If any tool returns an error, feedback is built and
    the planner (detect_tools) is called AGAIN with that feedback.
    This repeats until:
      - All tools succeed (no errors), OR
      - MAX_REPLAN_ATTEMPTS is reached

    Called by Final_main.py like:
        output = dispatch(user_query, llm, registry)

    Returns:
    {
        "tools_used": ["weather", "research"],
        "results": {
            "weather":  { ... },
            "research": { ... }
        },
        "attempts": 2     ← how many planning attempts were needed
    }
    """

    attempt      = 0
    feedback     = None        # No feedback on first attempt
    tools_needed = []
    results      = {}

    # ─────────────────────────────────────────
    #  WHILE LOOP — replan until success or max
    # ─────────────────────────────────────────
    while attempt < MAX_REPLAN_ATTEMPTS:
        attempt += 1

        print(f"\n{'─'*45}")
        print(f"🔁 Dispatcher — Planning Attempt #{attempt}/{MAX_REPLAN_ATTEMPTS}")
        if feedback:
            print(f"📣 Feedback to planner: {feedback}")
        print(f"{'─'*45}")

        # ── Step 1: Replan (with feedback if retry) ──
        tools_needed = detect_tools(llm, user_query, feedback)
        print(f"📌 Tools selected: {tools_needed}")

        # ── Step 2: Extract arguments ──
        tool_arguments = extract_arguments(llm, user_query, tools_needed)
        print(f"📋 Arguments extracted: {tool_arguments}")

        # ── Step 3: Run tools ──
        results = run_tools(registry, tool_arguments)
        print(f"📊 Raw results: {results}")

        # ── Check for errors in results ──
        errors = {
            tool_name: res
            for tool_name, res in results.items()
            if isinstance(res, dict) and "error" in res
        }

        if not errors:
            # ✅ All tools succeeded — exit loop
            print(f"\n✅ All tools succeeded on attempt #{attempt}")
            break

        # ❌ Some tools failed — build feedback for next iteration
        feedback = (
            f"The following tools returned errors on attempt #{attempt}: "
            + ", ".join([f"{k} → {v['error']}" for k, v in errors.items()])
            + ". Please select different or corrected tools."
        )
        print(f"\n⚠️  Errors detected. Replanning with feedback...")

    else:
        # While loop exhausted all attempts
        print(f"\n❌ Dispatcher exhausted {MAX_REPLAN_ATTEMPTS} attempts. Returning best available results.")

    return {
        "tools_used": tools_needed,
        "results":    results,
        "attempts":   attempt
    }