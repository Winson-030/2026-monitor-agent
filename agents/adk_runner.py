"""Shared ADK runner — used by both Telegram and Web to invoke the agent."""

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from agents.agent import root_agent

# Shared runner — Telegram messages route through the same agent as the Web UI
_session_service = InMemorySessionService()

_runner = Runner(
    agent=root_agent,
    app_name="gcp_monitor_agent",
    session_service=_session_service,
)


async def process_message(user_id: str, session_id: str, text: str) -> str:
    """Process a user message through the ADK agent and return the response.

    Args:
        user_id: Identifier for the user (e.g., 'telegram')
        session_id: Unique session key (e.g., 'tg-123456789')
        text: The user's message text

    Returns:
        The agent's final text response
    """
    # Ensure session exists (InMemorySessionService requires explicit creation)
    existing = await _session_service.get_session(
        app_name="gcp_monitor_agent", user_id=user_id, session_id=session_id
    )
    if existing is None:
        await _session_service.create_session(
            app_name="gcp_monitor_agent", user_id=user_id, session_id=session_id
        )

    content = Content(role="user", parts=[Part.from_text(text=text)])
    final_text: str = ""

    async for event in _runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        if event.content and event.content.parts and event.is_final_response():
            for part in event.content.parts:
                if part.text:
                    final_text += part.text

    return final_text.strip() or "Sorry, I couldn't generate a response."
