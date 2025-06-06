# oprina/tools/connection_tools.py
"""
Connection management tools for Oprina voice assistant.
Provides user-facing tools for authentication and connection management.
"""

import os
import sys
from typing import Dict, Any

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(3):
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk.tools import FunctionTool
from services.logging.logger import setup_logger

from oprina.common.utils import (
    validate_tool_context, update_agent_activity, log_tool_execution
)
from oprina.tools.auth_utils import (
    ensure_gmail_connection, ensure_calendar_connection,
    check_all_service_connections, get_connection_status_message
)

logger = setup_logger("connection_tools", console_output=True)


def check_all_connections(tool_context=None) -> str:
    """
    Check connection status for all services (Gmail and Calendar).
    
    Args:
        tool_context: ADK tool context
        
    Returns:
        Human-readable connection status message
    """
    if not validate_tool_context(tool_context, "check_all_connections"):
        return "Error: Unable to check connections"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "check_all_connections", "check_status", True, "Checking all service connections")
        
        # Update agent activity
        update_agent_activity(tool_context, "connection_manager", "checking_all_connections")
        
        # Get connection status message
        status_message = get_connection_status_message(tool_context)
        
        log_tool_execution(tool_context, "check_all_connections", "check_status", True, "Connection status retrieved")
        return status_message
        
    except Exception as e:
        error_msg = f"Error checking connections: {str(e)}"
        logger.error(error_msg)
        log_tool_execution(tool_context, "check_all_connections", "check_status", False, error_msg)
        return error_msg


def authenticate_gmail(force_reauth: bool = False, tool_context=None) -> str:
    """
    Authenticate with Gmail service.
    
    Args:
        force_reauth: Force re-authentication even if already connected
        tool_context: ADK tool context
        
    Returns:
        Authentication result message
    """
    if not validate_tool_context(tool_context, "authenticate_gmail"):
        return "Error: Unable to authenticate Gmail"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "authenticate_gmail", "authenticate", True, f"Force reauth: {force_reauth}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "authenticating_gmail")
        
        # Import authentication function
        from services.google_cloud.gmail_auth import authenticate_gmail as auth_gmail
        
        # Perform authentication
        auth_result = auth_gmail(force_reauth=force_reauth)
        
        if auth_result.get("success", False):
            # Update session state through ensure_gmail_connection
            success, message, _ = ensure_gmail_connection(tool_context, "authenticate_gmail")
            
            if success:
                user_email = auth_result.get("user_email", "user")
                result_msg = f"Gmail authentication successful! Connected as {user_email}"
                log_tool_execution(tool_context, "authenticate_gmail", "authenticate", True, result_msg)
                return result_msg
            else:
                log_tool_execution(tool_context, "authenticate_gmail", "authenticate", False, message)
                return f"Authentication completed but connection verification failed: {message}"
        else:
            error_msg = auth_result.get("message", "Authentication failed")
            log_tool_execution(tool_context, "authenticate_gmail", "authenticate", False, error_msg)
            return f"Gmail authentication failed: {error_msg}"
            
    except Exception as e:
        error_msg = f"Error during Gmail authentication: {str(e)}"
        logger.error(error_msg)
        log_tool_execution(tool_context, "authenticate_gmail", "authenticate", False, error_msg)
        return error_msg


def authenticate_calendar(force_reauth: bool = False, tool_context=None) -> str:
    """
    Authenticate with Calendar service.
    
    Args:
        force_reauth: Force re-authentication even if already connected
        tool_context: ADK tool context
        
    Returns:
        Authentication result message
    """
    if not validate_tool_context(tool_context, "authenticate_calendar"):
        return "Error: Unable to authenticate Calendar"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "authenticate_calendar", "authenticate", True, f"Force reauth: {force_reauth}")
        
        # Update agent activity
        update_agent_activity(tool_context, "calendar_agent", "authenticating_calendar")
        
        # Import authentication function
        from services.google_cloud.calendar_auth import authenticate_calendar as auth_calendar
        
        # Perform authentication
        auth_result = auth_calendar(force_reauth=force_reauth)
        
        if auth_result.get("success", False):
            # Update session state through ensure_calendar_connection
            success, message, _ = ensure_calendar_connection(tool_context, "authenticate_calendar")
            
            if success:
                calendar_count = auth_result.get("calendar_count", 0)
                primary_calendar = auth_result.get("primary_calendar", "")
                result_msg = f"Calendar authentication successful! Connected to {calendar_count} calendars"
                if primary_calendar:
                    result_msg += f" (Primary: {primary_calendar})"
                
                log_tool_execution(tool_context, "authenticate_calendar", "authenticate", True, result_msg)
                return result_msg
            else:
                log_tool_execution(tool_context, "authenticate_calendar", "authenticate", False, message)
                return f"Authentication completed but connection verification failed: {message}"
        else:
            error_msg = auth_result.get("message", "Authentication failed")
            log_tool_execution(tool_context, "authenticate_calendar", "authenticate", False, error_msg)
            return f"Calendar authentication failed: {error_msg}"
            
    except Exception as e:
        error_msg = f"Error during Calendar authentication: {str(e)}"
        logger.error(error_msg)
        log_tool_execution(tool_context, "authenticate_calendar", "authenticate", False, error_msg)
        return error_msg


def authenticate_all_services(force_reauth: bool = False, tool_context=None) -> str:
    """
    Authenticate with all services (Gmail and Calendar).
    
    Args:
        force_reauth: Force re-authentication even if already connected
        tool_context: ADK tool context
        
    Returns:
        Authentication result message for all services
    """
    if not validate_tool_context(tool_context, "authenticate_all_services"):
        return "Error: Unable to authenticate services"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "authenticate_all_services", "authenticate_all", True, 
                         f"Force reauth: {force_reauth}")
        
        # Update agent activity
        update_agent_activity(tool_context, "connection_manager", "authenticating_all_services")
        
        results = []
        
        # Authenticate Gmail
        gmail_result = authenticate_gmail(force_reauth=force_reauth, tool_context=tool_context)
        results.append(f"Gmail: {gmail_result}")
        
        # Authenticate Calendar
        calendar_result = authenticate_calendar(force_reauth=force_reauth, tool_context=tool_context)
        results.append(f"Calendar: {calendar_result}")
        
        # Get overall status
        final_status = check_all_connections(tool_context=tool_context)
        
        response = "Authentication Results:\n" + "\n".join(results) + f"\n\nFinal Status: {final_status}"
        
        log_tool_execution(tool_context, "authenticate_all_services", "authenticate_all", True, 
                         "All service authentication completed")
        
        return response
        
    except Exception as e:
        error_msg = f"Error during service authentication: {str(e)}"
        logger.error(error_msg)
        log_tool_execution(tool_context, "authenticate_all_services", "authenticate_all", False, error_msg)
        return error_msg


def get_detailed_connection_info(tool_context=None) -> str:
    """
    Get detailed connection information for all services.
    
    Args:
        tool_context: ADK tool context
        
    Returns:
        Detailed connection status information
    """
    if not validate_tool_context(tool_context, "get_detailed_connection_info"):
        return "Error: Unable to get connection information"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "get_detailed_connection_info", "get_details", True, 
                         "Getting detailed connection info")
        
        # Update agent activity
        update_agent_activity(tool_context, "connection_manager", "getting_connection_details")
        
        # Get detailed status
        status = check_all_service_connections(tool_context)
        
        if status.get("error"):
            return f"Error getting connection details: {status['error']}"
        
        # Format detailed response
        response_lines = ["Connection Details:"]
        
        # Gmail details
        if status["gmail"]["connected"]:
            from services.google_cloud.gmail_auth import get_gmail_auth_status
            gmail_status = get_gmail_auth_status()
            response_lines.append(f"✅ Gmail: Connected")
            response_lines.append(f"   - Last check: {gmail_status.get('last_check', 'Unknown')}")
            response_lines.append(f"   - Token valid: {gmail_status.get('token_files_exist', {}).get('token', False)}")
        else:
            response_lines.append(f"❌ Gmail: Not connected - {status['gmail'].get('error', 'Unknown error')}")
        
        # Calendar details
        if status["calendar"]["connected"]:
            from services.google_cloud.calendar_auth import get_calendar_auth_status
            calendar_status = get_calendar_auth_status()
            response_lines.append(f"✅ Calendar: Connected")
            response_lines.append(f"   - Calendars cached: {calendar_status.get('cached_calendars', 0)}")
            response_lines.append(f"   - Last check: {calendar_status.get('last_check', 'Unknown')}")
            response_lines.append(f"   - Token valid: {calendar_status.get('token_files_exist', {}).get('token', False)}")
        else:
            response_lines.append(f"❌ Calendar: Not connected - {status['calendar'].get('error', 'Unknown error')}")
        
        response_lines.append(f"\nOverall Status: {status.get('overall_status', 'unknown')}")
        response_lines.append(f"Checked at: {status.get('checked_at', 'unknown')}")
        
        result = "\n".join(response_lines)
        
        log_tool_execution(tool_context, "get_detailed_connection_info", "get_details", True, 
                         "Detailed connection info retrieved")
        
        return result
        
    except Exception as e:
        error_msg = f"Error getting detailed connection info: {str(e)}"
        logger.error(error_msg)
        log_tool_execution(tool_context, "get_detailed_connection_info", "get_details", False, error_msg)
        return error_msg


# Create ADK Function Tools
check_all_connections_tool = FunctionTool(func=check_all_connections)
authenticate_gmail_tool = FunctionTool(func=authenticate_gmail)
authenticate_calendar_tool = FunctionTool(func=authenticate_calendar)
authenticate_all_services_tool = FunctionTool(func=authenticate_all_services)
get_detailed_connection_info_tool = FunctionTool(func=get_detailed_connection_info)

# Connection tools collection
CONNECTION_TOOLS = [
    check_all_connections_tool,
    authenticate_gmail_tool,
    authenticate_calendar_tool,
    authenticate_all_services_tool,
    get_detailed_connection_info_tool
]

# Export for easy access
__all__ = [
    "check_all_connections",
    "authenticate_gmail",
    "authenticate_calendar", 
    "authenticate_all_services",
    "get_detailed_connection_info",
    "CONNECTION_TOOLS"
]