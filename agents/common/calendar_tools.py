"""
Calendar Tools for ADK Integration

This module provides direct Calendar API tools that follow the ADK FunctionTool pattern.
These tools replace the MCP client approach with direct API calls.
"""

import os
import sys
import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import project modules
from config.settings import settings
from services.google_cloud.calendar_auth import get_calendar_service, check_calendar_connection
from services.logging.logger import setup_logger

# Configure logging
logger = setup_logger("calendar_tools", console_output=True)

# --- ADK Imports with Fallback ---
try:
    from google.adk.tools import FunctionTool
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    ADK_IMPORT_ERROR = "ADK not available, running in fallback mode"
    
    # Fallback implementation
    class FunctionTool:
        def __init__(self, func=None, **kwargs):
            self.func = func
            self.name = kwargs.get('name', func.__name__ if func else 'unknown')
            self.description = kwargs.get('description', '')
            self.parameters = kwargs.get('parameters', {})
            
        def __call__(self, *args, **kwargs):
            if self.func:
                return self.func(*args, **kwargs)
            return {"error": "Function not implemented"}

def calendar_check_connection(tool_context=None) -> str:
    """
    Check if Calendar is connected and authenticated.
    
    Args:
        tool_context: The tool context containing session information
        
    Returns:
        str: Connection status message
    """
    logger.info("Checking Calendar connection...")
    
    # Check connection using the Calendar auth service
    connection_status = check_calendar_connection()
    
    if connection_status.get("connected", False) and connection_status.get("api_test", False):
        calendar_count = connection_status.get("calendar_count", 0)
        primary_calendar = connection_status.get("primary_calendar", "Unknown")
        return f"Calendar is connected and authenticated. Found {calendar_count} calendars, primary: {primary_calendar}."
    else:
        error = connection_status.get("error", "Unknown error")
        return f"Calendar is not connected. Error: {error}"

def calendar_authenticate(tool_context=None) -> str:
    """
    Authenticate with Calendar.
    
    Args:
        tool_context: The tool context containing session information
        
    Returns:
        str: Authentication status message
    """
    logger.info("Authenticating with Calendar...")
    
    # Get Calendar service (this will trigger OAuth flow if needed)
    service = get_calendar_service(force_refresh=True)
    
    if service:
        # Get calendar list to confirm authentication
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        primary_calendar = next((cal['summary'] for cal in calendars if cal.get('primary')), 'Unknown')
        return f"Successfully authenticated with Calendar. Primary calendar: {primary_calendar}."
    else:
        return "Failed to authenticate with Calendar. Please try again."

def calendar_list_events(tool_context=None, time_min: Optional[str] = None, time_max: Optional[str] = None, 
                        max_results: int = 10, single_events: bool = True) -> Dict[str, Any]:
    """
    List Calendar events.
    
    Args:
        tool_context: The tool context containing session information
        time_min: Start time for events (ISO format)
        time_max: End time for events (ISO format)
        max_results: Maximum number of results to return
        single_events: Whether to expand recurring events
        
    Returns:
        Dict[str, Any]: List of events
    """
    logger.info(f"Listing Calendar events, max_results: {max_results}")
    
    # Get Calendar service
    service = get_calendar_service()
    
    if not service:
        return {"error": "Calendar service not available. Please authenticate first."}
    
    try:
        # Set default time range if not provided
        if not time_min:
            time_min = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        
        if not time_max:
            # Default to 7 days from now
            time_max = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat() + 'Z'
        
        # List events
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=single_events,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return {"events": [], "count": 0}
        
        # Format events
        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            event_obj = {
                'id': event['id'],
                'summary': event.get('summary', 'No Title'),
                'description': event.get('description', ''),
                'location': event.get('location', ''),
                'start': start,
                'end': end,
                'creator': event.get('creator', {}).get('email', 'Unknown'),
                'attendees': [attendee.get('email', 'Unknown') for attendee in event.get('attendees', [])]
            }
            
            event_list.append(event_obj)
        
        return {
            "events": event_list,
            "count": len(event_list)
        }
        
    except Exception as e:
        logger.error(f"Error listing Calendar events: {e}")
        return {"error": f"Failed to list Calendar events: {str(e)}"}

def calendar_get_event(tool_context=None, event_id: str = "") -> Dict[str, Any]:
    """
    Get a Calendar event.
    
    Args:
        tool_context: The tool context containing session information
        event_id: Event ID
        
    Returns:
        Dict[str, Any]: Event details
    """
    logger.info(f"Getting Calendar event: {event_id}")
    
    # Get Calendar service
    service = get_calendar_service()
    
    if not service:
        return {"error": "Calendar service not available. Please authenticate first."}
    
    try:
        # Get event
        event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        # Format event
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        
        event_obj = {
            'id': event['id'],
            'summary': event.get('summary', 'No Title'),
            'description': event.get('description', ''),
            'location': event.get('location', ''),
            'start': start,
            'end': end,
            'creator': event.get('creator', {}).get('email', 'Unknown'),
            'attendees': [attendee.get('email', 'Unknown') for attendee in event.get('attendees', [])]
        }
        
        return event_obj
        
    except Exception as e:
        logger.error(f"Error getting Calendar event: {e}")
        return {"error": f"Failed to get Calendar event: {str(e)}"}

def calendar_create_event(tool_context=None, summary: str = "", start_time: str = "", end_time: str = "",
                         description: Optional[str] = None, location: Optional[str] = None,
                         attendees: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Create a Calendar event.
    
    Args:
        tool_context: The tool context containing session information
        summary: Event summary/title
        start_time: Start time (ISO format)
        end_time: End time (ISO format)
        description: Event description
        location: Event location
        attendees: List of attendee email addresses
        
    Returns:
        Dict[str, Any]: Created event details
    """
    logger.info(f"Creating Calendar event: {summary}")
    
    # Get Calendar service
    service = get_calendar_service()
    
    if not service:
        return {"error": "Calendar service not available. Please authenticate first."}
    
    try:
        # Create event
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            }
        }
        
        if description:
            event['description'] = description
        
        if location:
            event['location'] = location
        
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        # Insert event
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        
        # Format response
        start = created_event['start'].get('dateTime', created_event['start'].get('date'))
        end = created_event['end'].get('dateTime', created_event['end'].get('date'))
        
        event_obj = {
            'id': created_event['id'],
            'summary': created_event.get('summary', 'No Title'),
            'description': created_event.get('description', ''),
            'location': created_event.get('location', ''),
            'start': start,
            'end': end,
            'creator': created_event.get('creator', {}).get('email', 'Unknown'),
            'attendees': [attendee.get('email', 'Unknown') for attendee in created_event.get('attendees', [])]
        }
        
        return event_obj
        
    except Exception as e:
        logger.error(f"Error creating Calendar event: {e}")
        return {"error": f"Failed to create Calendar event: {str(e)}"}

def calendar_update_event(tool_context=None, event_id: str = "", summary: Optional[str] = None,
                         start_time: Optional[str] = None, end_time: Optional[str] = None,
                         description: Optional[str] = None, location: Optional[str] = None,
                         attendees: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Update a Calendar event.
    
    Args:
        tool_context: The tool context containing session information
        event_id: Event ID
        summary: Event summary/title
        start_time: Start time (ISO format)
        end_time: End time (ISO format)
        description: Event description
        location: Event location
        attendees: List of attendee email addresses
        
    Returns:
        Dict[str, Any]: Updated event details
    """
    logger.info(f"Updating Calendar event: {event_id}")
    
    # Get Calendar service
    service = get_calendar_service()
    
    if not service:
        return {"error": "Calendar service not available. Please authenticate first."}
    
    try:
        # Get existing event
        existing_event = service.events().get(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        # Update fields if provided
        if summary:
            existing_event['summary'] = summary
        
        if start_time:
            existing_event['start'] = {
                'dateTime': start_time,
                'timeZone': 'UTC',
            }
        
        if end_time:
            existing_event['end'] = {
                'dateTime': end_time,
                'timeZone': 'UTC',
            }
        
        if description:
            existing_event['description'] = description
        
        if location:
            existing_event['location'] = location
        
        if attendees:
            existing_event['attendees'] = [{'email': email} for email in attendees]
        
        # Update event
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=existing_event
        ).execute()
        
        # Format response
        start = updated_event['start'].get('dateTime', updated_event['start'].get('date'))
        end = updated_event['end'].get('dateTime', updated_event['end'].get('date'))
        
        event_obj = {
            'id': updated_event['id'],
            'summary': updated_event.get('summary', 'No Title'),
            'description': updated_event.get('description', ''),
            'location': updated_event.get('location', ''),
            'start': start,
            'end': end,
            'creator': updated_event.get('creator', {}).get('email', 'Unknown'),
            'attendees': [attendee.get('email', 'Unknown') for attendee in updated_event.get('attendees', [])]
        }
        
        return event_obj
        
    except Exception as e:
        logger.error(f"Error updating Calendar event: {e}")
        return {"error": f"Failed to update Calendar event: {str(e)}"}

def calendar_delete_event(tool_context=None, event_id: str = "") -> Dict[str, Any]:
    """
    Delete a Calendar event.
    
    Args:
        tool_context: The tool context containing session information
        event_id: Event ID
        
    Returns:
        Dict[str, Any]: Status
    """
    logger.info(f"Deleting Calendar event: {event_id}")
    
    # Get Calendar service
    service = get_calendar_service()
    
    if not service:
        return {"error": "Calendar service not available. Please authenticate first."}
    
    try:
        # Delete event
        service.events().delete(
            calendarId='primary',
            eventId=event_id
        ).execute()
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error deleting Calendar event: {e}")
        return {"error": f"Failed to delete Calendar event: {str(e)}"}

# Create ADK FunctionTools
if ADK_AVAILABLE:
    calendar_check_connection_tool = FunctionTool(
        func=calendar_check_connection,
        name="calendar_check_connection",
        description="Check if Calendar is connected and authenticated."
    )
    
    calendar_authenticate_tool = FunctionTool(
        func=calendar_authenticate,
        name="calendar_authenticate",
        description="Authenticate with Calendar."
    )
    
    calendar_list_events_tool = FunctionTool(
        func=calendar_list_events,
        name="calendar_list_events",
        description="List Calendar events.",
        parameters={
            "time_min": {"type": "string", "description": "Start time for events (ISO format)"},
            "time_max": {"type": "string", "description": "End time for events (ISO format)"},
            "max_results": {"type": "integer", "description": "Maximum number of results to return"},
            "single_events": {"type": "boolean", "description": "Whether to expand recurring events"}
        }
    )
    
    calendar_get_event_tool = FunctionTool(
        func=calendar_get_event,
        name="calendar_get_event",
        description="Get a Calendar event.",
        parameters={
            "event_id": {"type": "string", "description": "Event ID"}
        }
    )
    
    calendar_create_event_tool = FunctionTool(
        func=calendar_create_event,
        name="calendar_create_event",
        description="Create a Calendar event.",
        parameters={
            "summary": {"type": "string", "description": "Event summary/title"},
            "start_time": {"type": "string", "description": "Start time (ISO format)"},
            "end_time": {"type": "string", "description": "End time (ISO format)"},
            "description": {"type": "string", "description": "Event description"},
            "location": {"type": "string", "description": "Event location"},
            "attendees": {"type": "array", "items": {"type": "string"}, "description": "List of attendee email addresses"}
        }
    )
    
    calendar_update_event_tool = FunctionTool(
        func=calendar_update_event,
        name="calendar_update_event",
        description="Update a Calendar event.",
        parameters={
            "event_id": {"type": "string", "description": "Event ID"},
            "summary": {"type": "string", "description": "Event summary/title"},
            "start_time": {"type": "string", "description": "Start time (ISO format)"},
            "end_time": {"type": "string", "description": "End time (ISO format)"},
            "description": {"type": "string", "description": "Event description"},
            "location": {"type": "string", "description": "Event location"},
            "attendees": {"type": "array", "items": {"type": "string"}, "description": "List of attendee email addresses"}
        }
    )
    
    calendar_delete_event_tool = FunctionTool(
        func=calendar_delete_event,
        name="calendar_delete_event",
        description="Delete a Calendar event.",
        parameters={
            "event_id": {"type": "string", "description": "Event ID"}
        }
    )
    
    # List of all Calendar tools
    calendar_tools = [
        calendar_check_connection_tool,
        calendar_authenticate_tool,
        calendar_list_events_tool,
        calendar_get_event_tool,
        calendar_create_event_tool,
        calendar_update_event_tool,
        calendar_delete_event_tool
    ]
else:
    # Fallback tools
    calendar_tools = [
        calendar_check_connection,
        calendar_authenticate,
        calendar_list_events,
        calendar_get_event,
        calendar_create_event,
        calendar_update_event,
        calendar_delete_event
    ] 