"""Content agent. Handles content processing and analysis."""

from google.adk.agents import Agent

from oprina.sub_agents.content import prompt
from oprina.tools.content import CONTENT_TOOLS

content_agent = Agent(
    model="gemini-1.5-flash",
    name="content_agent", 
    description="Handles content processing, analysis, and reply generation for emails and text",
    instruction=prompt.CONTENT_AGENT_INSTR,
    tools=CONTENT_TOOLS,
)