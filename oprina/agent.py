"""Oprina root agent - Multimodal voice assistant for Gmail and Calendar."""

from google.adk.agents import Agent
from oprina.config import get_config
from oprina import prompt
from oprina.sub_agents.email.agent import email_agent
from oprina.sub_agents.calendar.agent import calendar_agent

config = get_config()

root_agent = Agent(
    model=get_config()["agent_model"],  # Use config for model
    name="oprina_root_agent",
    description="Multimodal voice-enabled Gmail and Calendar assistant",
    instruction=prompt.ROOT_AGENT_INSTR,
    sub_agents=[
        email_agent,
        calendar_agent
    ],
)