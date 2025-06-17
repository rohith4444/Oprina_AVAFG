"""
Simple OAuth response models for Oprina API.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class OAuthUrlResponse(BaseModel):
    """Response containing OAuth authorization URL."""
    authorization_url: str = Field(..., description="Google OAuth authorization URL")
    state: str = Field(..., description="OAuth state parameter")
    service: Optional[str] = Field(None, description="Service being connected")
    purpose: str = Field(..., description="OAuth purpose (connect/login/signup)")
    
    class Config:
        schema_extra = {
            "example": {
                "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
                "state": "user123:gmail_connect:abc123",
                "service": "gmail",
                "purpose": "connect"
            }
        }


class OAuthCallbackResponse(BaseModel):
    """Response from OAuth callback processing."""
    success: bool = Field(..., description="Whether OAuth flow succeeded")
    action: str = Field(..., description="Action performed (connect/login/signup)")
    service: Optional[str] = Field(None, description="Service connected (for connect actions)")
    user_id: Optional[str] = Field(None, description="User ID (for connect actions)")
    user: Optional[Dict[str, Any]] = Field(None, description="User data (for auth actions)")
    redirect_url: str = Field(..., description="URL to redirect user to")
    connected_email: Optional[str] = Field(None, description="Email of connected service")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "action": "connect",
                "service": "gmail",
                "user_id": "user-123",
                "redirect_url": "http://localhost:3000/settings",
                "connected_email": "user@gmail.com"
            }
        }


class ServiceConnectionStatus(BaseModel):
    """Status of a single service connection."""
    connected: bool = Field(..., description="Whether service is connected")
    email: Optional[str] = Field(None, description="Connected email address")


class ConnectionStatusResponse(BaseModel):
    """Response showing all service connection statuses."""
    gmail: ServiceConnectionStatus = Field(..., description="Gmail connection status")
    calendar: ServiceConnectionStatus = Field(..., description="Calendar connection status")
    
    class Config:
        schema_extra = {
            "example": {
                "gmail": {
                    "connected": True,
                    "email": "user@gmail.com"
                },
                "calendar": {
                    "connected": False,
                    "email": None
                }
            }
        }


class DisconnectResponse(BaseModel):
    """Response from service disconnection."""
    success: bool = Field(..., description="Whether disconnection succeeded")
    service: str = Field(..., description="Service that was disconnected")
    action: str = Field(..., description="Action performed")
    user_id: str = Field(..., description="User ID")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "service": "gmail", 
                "action": "disconnect",
                "user_id": "user-123"
            }
        }


class GoogleAuthResponse(BaseModel):
    """Response from Google login/signup."""
    success: bool = Field(..., description="Whether authentication succeeded")
    action: str = Field(..., description="Action performed (login/signup)")
    user: Dict[str, Any] = Field(..., description="User data")
    token: str = Field(..., description="JWT authentication token")
    redirect_url: str = Field(..., description="URL to redirect user to")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "action": "login",
                "user": {
                    "id": "user-123",
                    "email": "user@gmail.com",
                    "full_name": "John Doe"
                },
                "token": "jwt-token-here",
                "redirect_url": "http://localhost:3000/dashboard"
            }
        }