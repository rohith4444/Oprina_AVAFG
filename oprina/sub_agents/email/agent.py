"""Email agent. Handles Gmail operations using the Gmail API."""

from google.adk.agents import Agent

from oprina.sub_agents.email import prompt
from oprina.tools.gmail import GMAIL_TOOLS

email_agent = Agent(
    model="gemini-2.0-flash",
    name="email_agent",
    description="Handles Gmail operations with direct API access and session state integration",
    instruction=prompt.EMAIL_AGENT_INSTR,
    tools=GMAIL_TOOLS,
)