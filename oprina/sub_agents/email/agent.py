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

"""Email agent for Oprina, handling Gmail operations."""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig

from oprina.sub_agents.email import prompt

# Email agent definition
email_agent = Agent(
    model="gemini-2.0-flash-001",
    name="email_agent",
    description="""Email agent that handles Gmail operations including:
    - Searching and reading emails
    - Composing and sending emails
    - Managing email labels and organization
    - Handling email attachments
    - Processing email threads and conversations""",
    instruction=prompt.EMAIL_AGENT_INSTR,
    generate_content_config=GenerateContentConfig(
        temperature=0.0, top_p=0.5
    )
) 