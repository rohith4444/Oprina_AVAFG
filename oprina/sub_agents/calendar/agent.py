# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Calendar agent for Oprina, handling Google Calendar operations."""

from google.adk.agents import Agent
from google.genai.types import GenerateContentConfig

from oprina.sub_agents.calendar import prompt

# Calendar agent definition
calendar_agent = Agent(
    model="gemini-2.0-flash-001",
    name="calendar_agent",
    description="""Calendar agent that handles Google Calendar operations including:
    - Searching and reading calendar events
    - Creating, updating, and deleting events
    - Managing event invitations and attendees
    - Organizing and categorizing calendar events
    - Checking availability and resolving conflicts""",
    instruction=prompt.CALENDAR_AGENT_INSTR,
    generate_content_config=GenerateContentConfig(
        temperature=0.0, top_p=0.5
    )
) 