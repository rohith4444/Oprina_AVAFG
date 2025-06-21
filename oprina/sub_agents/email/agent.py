"""Email agent. Handles Gmail operations using the Gmail API."""

from google.adk.agents import Agent

from oprina.sub_agents.email import prompt
import os

# Smart tool selection
TOOLS_MODE = os.getenv("OPRINA_TOOLS_MODE")
print(f"🔧 Gmail AGENT USING TOOLS_MODE: {TOOLS_MODE}")

if TOOLS_MODE == "prod":
    from oprina.tools_prod import GMAIL_TOOLS
    print("📁 Using tools_prod")
else:
    from oprina.tools import GMAIL_TOOLS
    print("📁 Using tools_local")

email_agent = Agent(
    model="gemini-2.0-flash",
    name="email_agent",
    description="Handles Gmail operations with direct API access and session state integration",
    instruction=prompt.EMAIL_AGENT_INSTR,
    tools=GMAIL_TOOLS,
)

# # ADK evaluation framework expects 'root_agent' variable
# root_agent = email_agent