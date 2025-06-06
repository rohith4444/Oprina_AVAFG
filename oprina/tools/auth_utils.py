# oprina/tools/auth_utils.py
"""
Central authentication utilities for Oprina voice assistant.
Based on ADK Voice Agent patterns for robust service connection management.
"""

import os
import sys
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(3):
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from services.logging.logger import setup_logger
from oprina.common.utils import (
    validate_tool_context, update_service_connection_status,
    get_service_connection_status, log_tool_execution
)
from oprina.common.session_keys import (
    USER_GMAIL_CONNECTED, USER_CALENDAR_CONNECTED, USER_EMAIL
)

from oprina.services.google_cloud.gmail_auth import get_gmail_service, check_gmail_connection
from oprina.services.google_cloud.calendar_auth import get_calendar_service, check_calendar_connection

logger = setup_logger("auth_utils", console_output=True)

# Service connection timeout (in seconds)
CONNECTION_TIMEOUT = 30

def ensure_gmail_connection(tool_context, function_name: str = "unknown") -> Tuple[bool, str, Optional[Any]]:
    """
    Ensure Gmail service connection is available and valid.
    
    Args:
        tool_context: ADK tool context
        function_name: Name of calling function for logging
        
    Returns:
        Tuple of (success: bool, message: str, service: Optional[gmail_service])
    """
    if not validate_tool_context(tool_context, f"{function_name}:ensure_gmail_connection"):
        return False, "Invalid tool context provided", None
    
    try:
        # Log connection attempt
        log_tool_execution(tool_context, "ensure_gmail_connection", "check_connection", True, 
                         f"Called by: {function_name}")
        
        # Check session state first
        connection_status = get_service_connection_status(tool_context, "gmail")
        
        if connection_status.get("connected", False):
            # Try to get existing service
            try:
                from services.google_cloud.gmail_auth import get_gmail_service, check_gmail_connection
                service = get_gmail_service()
                
                if service:
                    # Verify service is still working
                    verification = check_gmail_connection()
                    if verification.get("connected", False):
                        logger.info(f"Gmail connection verified for {function_name}")
                        return True, "Gmail connected", service
                    else:
                        logger.warning(f"Gmail connection verification failed: {verification.get('error', 'Unknown error')}")
                        # Fall through to re-authentication
                
            except Exception as e:
                logger.error(f"Error verifying Gmail service: {e}")
                # Fall through to re-authentication
        
        # Need to establish or re-establish connection
        success, message, service = _establish_gmail_connection(tool_context)
        
        if success:
            log_tool_execution(tool_context, "ensure_gmail_connection", "establish_connection", True, 
                             f"Gmail connected for {function_name}")
        else:
            log_tool_execution(tool_context, "ensure_gmail_connection", "establish_connection", False, 
                             f"Failed for {function_name}: {message}")
        
        return success, message, service
        
    except Exception as e:
        error_msg = f"Error ensuring Gmail connection: {str(e)}"
        logger.error(error_msg)
        log_tool_execution(tool_context, "ensure_gmail_connection", "error", False, error_msg)
        return False, error_msg, None

def ensure_calendar_connection(tool_context, function_name: str = "unknown") -> Tuple[bool, str, Optional[Any]]:
    """
    Ensure Calendar service connection is available and valid.
    
    Args:
        tool_context: ADK tool context
        function_name: Name of calling function for logging
        
    Returns:
        Tuple of (success: bool, message: str, service: Optional[calendar_service])
    """
    if not validate_tool_context(tool_context, f"{function_name}:ensure_calendar_connection"):
        return False, "Invalid tool context provided", None
    
    try:
        # Log connection attempt
        log_tool_execution(tool_context, "ensure_calendar_connection", "check_connection", True, 
                         f"Called by: {function_name}")
        
        # Check session state first
        connection_status = get_service_connection_status(tool_context, "calendar")
        
        if connection_status.get("connected", False):
            # Try to get existing service
            try:
                from services.google_cloud.calendar_auth import get_calendar_service, check_calendar_connection
                service = get_calendar_service()
                
                if service:
                    # Verify service is still working
                    verification = check_calendar_connection()
                    if verification.get("connected", False):
                        logger.info(f"Calendar connection verified for {function_name}")
                        return True, "Calendar connected", service
                    else:
                        logger.warning(f"Calendar connection verification failed: {verification.get('error', 'Unknown error')}")
                        # Fall through to re-authentication
                
            except Exception as e:
                logger.error(f"Error verifying Calendar service: {e}")
                # Fall through to re-authentication
        
        # Need to establish or re-establish connection
        success, message, service = _establish_calendar_connection(tool_context)
        
        if success:
            log_tool_execution(tool_context, "ensure_calendar_connection", "establish_connection", True, 
                             f"Calendar connected for {function_name}")
        else:
            log_tool_execution(tool_context, "ensure_calendar_connection", "establish_connection", False, 
                             f"Failed for {function_name}: {message}")
        
        return success, message, service
        
    except Exception as e:
        error_msg = f"Error ensuring Calendar connection: {str(e)}"
        logger.error(error_msg)
        log_tool_execution(tool_context, "ensure_calendar_connection", "error", False, error_msg)
        return False, error_msg, None

def check_all_service_connections(tool_context) -> Dict[str, Any]:
    """
    Check connection status for all services.
    
    Args:
        tool_context: ADK tool context
        
    Returns:
        Dict with connection status for all services
    """
    if not validate_tool_context(tool_context, "check_all_service_connections"):
        return {"error": "Invalid tool context"}
    
    try:
        log_tool_execution(tool_context, "check_all_service_connections", "check_all", True, "Checking all services")
        
        results = {
            "gmail": {"connected": False, "error": None},
            "calendar": {"connected": False, "error": None},
            "overall_status": "checking"
        }
        
        # Check Gmail
        gmail_success, gmail_message, _ = ensure_gmail_connection(tool_context, "check_all_services")
        results["gmail"]["connected"] = gmail_success
        if not gmail_success:
            results["gmail"]["error"] = gmail_message
        
        # Check Calendar
        calendar_success, calendar_message, _ = ensure_calendar_connection(tool_context, "check_all_services")
        results["calendar"]["connected"] = calendar_success
        if not calendar_success:
            results["calendar"]["error"] = calendar_message
        
        # Determine overall status
        if gmail_success and calendar_success:
            results["overall_status"] = "all_connected"
        elif gmail_success or calendar_success:
            results["overall_status"] = "partial_connected"
        else:
            results["overall_status"] = "disconnected"
        
        results["checked_at"] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "check_all_service_connections", "check_all", True, 
                         f"Status: {results['overall_status']}")
        
        return results
        
    except Exception as e:
        error_msg = f"Error checking service connections: {str(e)}"
        logger.error(error_msg)
        log_tool_execution(tool_context, "check_all_service_connections", "check_all", False, error_msg)
        return {"error": error_msg, "overall_status": "error"}

def _establish_gmail_connection(tool_context) -> Tuple[bool, str, Optional[Any]]:
    """
    Establish Gmail connection and update session state.
    
    Args:
        tool_context: ADK tool context
        
    Returns:
        Tuple of (success: bool, message: str, service: Optional[gmail_service])
    """
    try:
        from services.google_cloud.gmail_auth import get_gmail_service, check_gmail_connection
        
        # Attempt to get Gmail service
        service = get_gmail_service()
        
        if not service:
            update_service_connection_status(
                tool_context, "gmail", False, "",
                {"last_error": "Failed to create Gmail service", "last_attempt": datetime.utcnow().isoformat()}
            )
            return False, "Failed to create Gmail service. Please check your credentials.", None
        
        # Verify connection works
        connection_check = check_gmail_connection()
        
        if connection_check.get("connected", False):
            user_email = connection_check.get("user_email", "")
            
            # Update session state with successful connection
            update_service_connection_status(
                tool_context, "gmail", True, user_email,
                {
                    "last_connected": datetime.utcnow().isoformat(),
                    "messages_total": connection_check.get("messages_total", 0),
                    "threads_total": connection_check.get("threads_total", 0)
                }
            )
            
            return True, f"Gmail connected successfully as {user_email}", service
        else:
            error_msg = connection_check.get("error", "Unknown connection error")
            update_service_connection_status(
                tool_context, "gmail", False, "",
                {"last_error": error_msg, "last_attempt": datetime.utcnow().isoformat()}
            )
            return False, f"Gmail connection failed: {error_msg}", None
            
    except Exception as e:
        error_msg = f"Error establishing Gmail connection: {str(e)}"
        logger.error(error_msg)
        update_service_connection_status(
            tool_context, "gmail", False, "",
            {"last_error": error_msg, "last_attempt": datetime.utcnow().isoformat()}
        )
        return False, error_msg, None

def _establish_calendar_connection(tool_context) -> Tuple[bool, str, Optional[Any]]:
    """
    Establish Calendar connection and update session state.
    
    Args:
        tool_context: ADK tool context
        
    Returns:
        Tuple of (success: bool, message: str, service: Optional[calendar_service])
    """
    try:
        from services.google_cloud.calendar_auth import get_calendar_service, check_calendar_connection
        
        # Attempt to get Calendar service
        service = get_calendar_service()
        
        if not service:
            update_service_connection_status(
                tool_context, "calendar", False, "",
                {"last_error": "Failed to create Calendar service", "last_attempt": datetime.utcnow().isoformat()}
            )
            return False, "Failed to create Calendar service. Please check your credentials.", None
        
        # Verify connection works
        connection_check = check_calendar_connection()
        
        if connection_check.get("connected", False):
            calendar_count = connection_check.get("calendar_count", 0)
            primary_calendar = connection_check.get("primary_calendar", "")
            
            # Update session state with successful connection
            update_service_connection_status(
                tool_context, "calendar", True, "",
                {
                    "last_connected": datetime.utcnow().isoformat(),
                    "calendar_count": calendar_count,
                    "primary_calendar": primary_calendar,
                    "calendars": connection_check.get("calendars", [])
                }
            )
            
            return True, f"Calendar connected successfully with {calendar_count} calendars", service
        else:
            error_msg = connection_check.get("error", "Unknown connection error")
            update_service_connection_status(
                tool_context, "calendar", False, "",
                {"last_error": error_msg, "last_attempt": datetime.utcnow().isoformat()}
            )
            return False, f"Calendar connection failed: {error_msg}", None
            
    except Exception as e:
        error_msg = f"Error establishing Calendar connection: {str(e)}"
        logger.error(error_msg)
        update_service_connection_status(
            tool_context, "calendar", False, "",
            {"last_error": error_msg, "last_attempt": datetime.utcnow().isoformat()}
        )
        return False, error_msg, None

def get_connection_status_message(tool_context) -> str:
    """
    Get a user-friendly message about current connection status.
    
    Args:
        tool_context: ADK tool context
        
    Returns:
        Human-readable connection status message
    """
    if not validate_tool_context(tool_context, "get_connection_status_message"):
        return "Unable to check connection status"
    
    try:
        status = check_all_service_connections(tool_context)
        
        if status.get("overall_status") == "all_connected":
            gmail_status = get_service_connection_status(tool_context, "gmail")
            calendar_status = get_service_connection_status(tool_context, "calendar")
            
            user_email = gmail_status.get("user_email", "unknown")
            calendar_count = calendar_status.get("additional_info", {}).get("calendar_count", 0)
            
            return f"All services connected! Gmail: {user_email}, Calendar: {calendar_count} calendars available"
            
        elif status.get("overall_status") == "partial_connected":
            messages = []
            if status["gmail"]["connected"]:
                gmail_status = get_service_connection_status(tool_context, "gmail")
                user_email = gmail_status.get("user_email", "connected")
                messages.append(f"Gmail: Connected ({user_email})")
            else:
                messages.append(f"Gmail: Not connected - {status['gmail'].get('error', 'Unknown error')}")
            
            if status["calendar"]["connected"]:
                calendar_status = get_service_connection_status(tool_context, "calendar")
                calendar_count = calendar_status.get("additional_info", {}).get("calendar_count", 0)
                messages.append(f"Calendar: Connected ({calendar_count} calendars)")
            else:
                messages.append(f"Calendar: Not connected - {status['calendar'].get('error', 'Unknown error')}")
            
            return " | ".join(messages)
            
        else:
            return "No services connected. Please authenticate with Gmail and Calendar to get started."
            
    except Exception as e:
        logger.error(f"Error getting connection status message: {e}")
        return "Unable to determine connection status"

# Export main functions
__all__ = [
    "ensure_gmail_connection",
    "ensure_calendar_connection", 
    "check_all_service_connections",
    "get_connection_status_message"
]