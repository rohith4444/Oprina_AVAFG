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

"""
Content Agent Package

This package contains the Content Agent responsible for:
- Email content summarization with adaptive detail levels
- Email reply generation with context awareness
- Content analysis (sentiment, topics, urgency)
- Text optimization for voice delivery
- Template-based content generation
"""
from .agent import create_content_agent

# Create instance only when explicitly requested
def get_content_agent():
    return create_content_agent()

__all__ = ["create_content_agent", "get_content_agent"]

# Package metadata
__version__ = "2.0.0"
__description__ = "ADK-integrated content processing agent with voice optimization"
