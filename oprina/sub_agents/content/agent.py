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

"""Content agent for Oprina, handling content generation and analysis."""

from google.adk.agents import Agent
from google.genai.types import GenerateContentConfig

from oprina.sub_agents.content import prompt

# Content agent definition
content_agent = Agent(
    model="gemini-2.0-flash-001",
    name="content_agent",
    description="""Content agent that handles content generation, summarization, formatting, and analysis for emails and documents.""",
    instruction=prompt.CONTENT_AGENT_INSTR,
    generate_content_config=GenerateContentConfig(
        temperature=0.0, top_p=0.5
    )
) 