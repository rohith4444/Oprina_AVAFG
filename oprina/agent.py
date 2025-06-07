"""Oprina root agent - Multimodal voice assistant for Gmail and Calendar."""

from google.adk.agents import Agent
from oprina import prompt
from oprina.sub_agents.email.agent import email_agent
from oprina.sub_agents.calendar.agent import calendar_agent
 
# from oprina.tools.memory import load_user_profile

root_agent = Agent(
    model="gemini-2.0-flash",  # Multimodal model
    name="oprina_root_agent",
    description="Multimodal voice-enabled Gmail and Calendar assistant",
    instruction=prompt.ROOT_AGENT_INSTR,
    sub_agents=[
        email_agent,
        calendar_agent
    ]  
)