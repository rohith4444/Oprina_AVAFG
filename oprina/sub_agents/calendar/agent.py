"""Calendar agent. Handles Google Calendar operations."""

from google.adk.agents import Agent

from oprina.sub_agents.calendar import prompt
from oprina.tools.calendar import CALENDAR_TOOLS

calendar_agent = Agent(
    model="gemini-2.0-flash",
    name="calendar_agent",
    description="Handles Google Calendar operations including events, scheduling, and availability",
    instruction=prompt.CALENDAR_AGENT_INSTR,
    tools=CALENDAR_TOOLS,
)

# ADK evaluation framework expects 'root_agent' variable
root_agent = calendar_agent