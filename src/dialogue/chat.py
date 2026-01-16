"""Chat module with Ollama streaming and tool calling support."""
from datetime import datetime, timedelta
from typing import Generator

from ollama import chat

from src.tools import TOOLS, TOOL_REGISTRY

MODEL = "qwen2.5:7b-instruct"


def _build_date_context() -> str:
    """Build a 7-day calendar for LLM date reference."""
    today = datetime.today()
    lines = []
    for i in range(7):
        day = today + timedelta(days=i)
        label = "today" if i == 0 else ("tomorrow" if i == 1 else day.strftime("%A"))
        lines.append(f"  - {label}: {day.strftime('%Y-%m-%d')} ({day.strftime('%A')})")
    return "\n".join(lines)


def build_system_prompt() -> str:
    """Build the system prompt with current date context."""
    today_text = datetime.today().strftime("%d %B %Y, %A")
    week_calendar = _build_date_context()

    return f"""
        You are a helpful assistant. 
        
        You can:
        - Answer general questions
        - Provide weather information for any location (7-day forecast)
        - Manage calendar events (list, create, update, delete appointments)
        
        Be concise and natural in your responses. When you need weather or calendar data,
        use the available tools. These tools provide the most accurate information.
        
        For general questions, respond directly.
        
        Current date: {today_text}
        
        Date reference (use for weekday calculations):
        {week_calendar}
        """


def _execute_tool(tool_name: str, tool_args: dict) -> str:
    """Execute a tool by name and return the result."""
    if tool_name not in TOOL_REGISTRY:
        return f"Unknown tool: {tool_name}"
    try:
        return TOOL_REGISTRY[tool_name](**tool_args)
    except Exception as e:
        return f"Error executing {tool_name}: {e}"


def _process_tool_calls(tool_calls: list, messages: list) -> None:
    """Execute tool calls and append results to messages."""
    for tool_call in tool_calls:
        result = _execute_tool(
            tool_call.function.name,
            tool_call.function.arguments,
        )
        messages.append({"role": "tool", "content": result})


def chat_stream(user_input: str, messages: list) -> Generator[str, None, None]:
    """
    Process a user message with streaming and tool calling support.

    Args:
        user_input: The user's message.
        messages: Conversation history (modified in-place).

    Yields:
        Chunks of the assistant's response.
    """
    messages.append({"role": "user", "content": user_input})

    while True:
        full_content = ""
        tool_calls = []

        # Stream response
        for chunk in chat(model=MODEL, messages=messages, tools=TOOLS, stream=True):
            if chunk.message.content:
                full_content += chunk.message.content
                yield chunk.message.content
            if chunk.message.tool_calls:
                tool_calls.extend(chunk.message.tool_calls)

        # No tool calls - done
        if not tool_calls:
            messages.append({"role": "assistant", "content": full_content})
            return

        # Record assistant message with tool calls
        messages.append({
            "role": "assistant",
            "content": full_content,
            "tool_calls": [
                {"function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in tool_calls
            ],
        })

        # Execute tools and continue loop for next response
        _process_tool_calls(tool_calls, messages)
