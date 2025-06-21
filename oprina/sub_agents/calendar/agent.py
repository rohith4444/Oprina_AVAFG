"""Calendar agent. Handles Google Calendar operations."""

from google.adk.agents import Agent

from oprina.sub_agents.calendar import prompt
import os

# Smart tool selection
TOOLS_MODE = os.getenv("OPRINA_TOOLS_MODE")
print(f"🔧 CALENDAR AGENT USING TOOLS_MODE: {TOOLS_MODE}")

if TOOLS_MODE == "prod":
    from oprina.tools_prod import CALENDAR_TOOLS
    print("📁 Using tools_prod")
else:
    from oprina.tools import CALENDAR_TOOLS
    print("📁 Using tools_local")

calendar_agent = Agent(
    model="gemini-2.0-flash",
    name="calendar_agent",
    description="Handles Google Calendar operations including events, scheduling, and availability",
    instruction=prompt.CALENDAR_AGENT_INSTR,
    tools=CALENDAR_TOOLS,
)

# # ADK evaluation framework expects 'root_agent' variable
# root_agent = calendar_agent