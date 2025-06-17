"""
Simple OAuth request models for Oprina API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class OAuthConnectRequest(BaseModel):
    service: str = Field(..., description="Service to connect", pattern="^(gmail|calendar)$") 

class OAuthDisconnectRequest(BaseModel):
    service: str = Field(..., description="Service to disconnect", pattern="^(gmail|calendar)$")   