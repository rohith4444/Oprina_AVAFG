"""
Calendar Tools for ADK - Using Your Calendar Logic with ADK Patterns

Adapted from your existing calendar tools with:
- ADK tool context integration
- String returns for voice interaction
- Session state management
- Professional logging
- Connection checking via auth_utils
"""

import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time
import calendar

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(3):
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk.tools import FunctionTool
from oprina.services.logging.logger import setup_logger

# Import simplified auth utils
from oprina.tools.auth_utils import get_calendar_service

# Import ADK utility functions
from oprina.common.utils import (
    validate_tool_context, update_agent_activity, log_tool_execution
)

# Import session state constants
from oprina.common.session_keys import (
    CALENDAR_CURRENT, CALENDAR_LAST_FETCH, CALENDAR_LAST_LIST_START_DATE,
    CALENDAR_LAST_LIST_DAYS, CALENDAR_LAST_LIST_COUNT,
    CALENDAR_LAST_EVENT_CREATED, CALENDAR_LAST_EVENT_CREATED_AT, CALENDAR_LAST_CREATED_EVENT_ID,
    CALENDAR_LAST_UPDATED_EVENT, CALENDAR_LAST_EVENT_UPDATED_AT,
    CALENDAR_LAST_DELETED_EVENT, CALENDAR_LAST_DELETED_ID, CALENDAR_LAST_DELETED_AT
)

logger = setup_logger("calendar_tools", console_output=True)


# =============================================================================
# Timezone Helper Functions  
# =============================================================================

def _get_local_timezone() -> str:
    """Get the user's local timezone from various sources."""
    try:
        # Try to get timezone from system
        if hasattr(time, 'tzname') and time.tzname[0]:
            # Windows and some Unix systems
            tz_name = time.tzname[0] if not time.daylight else time.tzname[1]
            # Convert common abbreviations to IANA names
            tz_mapping = {
                'EST': 'America/New_York',
                'EDT': 'America/New_York', 
                'CST': 'America/Chicago',
                'CDT': 'America/Chicago',
                'MST': 'America/Denver',
                'MDT': 'America/Denver',
                'PST': 'America/Los_Angeles',
                'PDT': 'America/Los_Angeles',
            }
            return tz_mapping.get(tz_name, 'America/New_York')  # Default to Eastern
        
        # Fallback: try to determine from UTC offset
        utc_offset = -time.timezone / 3600  # Convert to hours
        if time.daylight:
            utc_offset += 1  # Adjust for DST
            
        # Map common UTC offsets to timezones (approximate)
        offset_mapping = {
            -8: 'America/Los_Angeles',  # PST
            -7: 'America/Denver',       # MST  
            -6: 'America/Chicago',      # CST
            -5: 'America/New_York',     # EST
            -4: 'America/New_York',     # EDT (approximate)
            0: 'UTC',
            1: 'Europe/London',
        }
        
        return offset_mapping.get(int(utc_offset), 'America/New_York')
        
    except Exception as e:
        logger.warning(f"Could not determine local timezone: {e}")
        return 'America/New_York'  # Safe default


def _get_local_now() -> datetime:
    """Get current datetime in user's local timezone."""
    # Get local time (not UTC)
    return datetime.now()


def _get_user_timezone_from_calendar(service) -> str:
    """Try to get user's timezone from their Calendar settings."""
    try:
        settings = service.settings().list().execute()
        for setting in settings.get("items", []):
            if setting.get("id") == "timezone":
                return setting.get("value", "America/New_York")
    except Exception as e:
        logger.debug(f"Could not get timezone from calendar settings: {e}")
    
    return _get_local_timezone()


# =============================================================================
# Calendar Event Creation Tool
# =============================================================================

def calendar_create_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    calendar_id: str = "primary",
    tool_context=None
) -> dict:
    """Create a new event in Google Calendar."""
    if not validate_tool_context(tool_context, "calendar_create_event"):
        return {"error": "No valid tool context provided"}
    
    try:
        # Log operation
        log_tool_execution(tool_context, "calendar_create_event", "create_event", True, 
                         f"Summary: '{summary}', Start: {start_time}, End: {end_time}")
        
        # Update agent activity
        update_agent_activity(tool_context, "calendar_agent", "creating_event")
        
        # Get Calendar service
        service = get_calendar_service()
        if not service:
            return {"error": "Calendar not set up. Please run: python setup_calendar.py"}
        
        # Parse times using your logic
        start_dt = _parse_datetime(start_time)
        end_dt = _parse_datetime(end_time)
        
        if not start_dt or not end_dt:
            return {"error": "Invalid date/time format. Please use format like 'YYYY-MM-DD HH:MM' or '2024-01-15 14:00'"}
        
        # Get user's timezone using the improved helper function
        timezone_id = _get_user_timezone_from_calendar(service)
        
        # Create event body (your logic)
        event_body = {
            "summary": summary,
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": timezone_id,
            },
            "end": {
                "dateTime": end_dt.isoformat(), 
                "timeZone": timezone_id
            }
        }
        
        # Add optional fields
        if description:
            event_body["description"] = description
        if location:
            event_body["location"] = location
        
        # Call the Calendar API to create the event
        event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        
        # Format response times for user
        start_formatted = start_dt.strftime('%A, %B %d at %I:%M %p')
        end_formatted = end_dt.strftime('%I:%M %p')
        
        # Update session state with rich data
        tool_context.state[CALENDAR_LAST_EVENT_CREATED] = {
            "id": event.get("id"),
            "summary": summary,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "start_formatted": start_formatted,
            "end_formatted": end_formatted,
            "location": location,
            "description": description,
            "event_link": event.get("htmlLink", ""),
            "timezone": timezone_id
        }
        tool_context.state[CALENDAR_LAST_EVENT_CREATED_AT] = _get_local_now().isoformat()
        tool_context.state[CALENDAR_LAST_CREATED_EVENT_ID] = event.get("id")
        
        # Return the actual event object (dict) for proper Google Calendar integration
        log_tool_execution(tool_context, "calendar_create_event", "create_event", True, "Event created successfully")
        
        return event
        
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        log_tool_execution(tool_context, "calendar_create_event", "create_event", False, str(e))
        return {"error": f"Error creating event: {str(e)}"}


# =============================================================================
# Calendar Event Listing Tool
# =============================================================================

def calendar_list_events(
    start_date: str = "",
    days: int = 7,
    calendar_id: str = "primary",
    tool_context=None
) -> str:
    """List upcoming calendar events within a specified date range."""
    if not validate_tool_context(tool_context, "calendar_list_events"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "calendar_list_events", "list_events", True, 
                         f"Start date: '{start_date}', Days: {days}")
        
        # Update agent activity
        update_agent_activity(tool_context, "calendar_agent", "listing_events")
        
        # Get Calendar service
        service = get_calendar_service()
        if not service:
            return "Calendar not set up. Please run: python setup_calendar.py"
        
        # Get user's timezone for proper date handling
        user_timezone = _get_user_timezone_from_calendar(service)
        
        # Set time range using local time (not UTC)
        if not start_date or start_date.strip() == "":
            start_time = _get_local_now()
            start_date_display = "today"
        else:
            try:
                # Parse the provided date and assume it's in user's local time
                start_time = datetime.strptime(start_date, "%Y-%m-%d")
                start_date_display = start_time.strftime('%B %d, %Y')
            except ValueError:
                return f"Invalid date format: {start_date}. Please use YYYY-MM-DD format."
        
        # If days is not provided or is invalid, default to 7 days
        if not days or days < 1:
            days = 7
        
        end_time = start_time + timedelta(days=days)
        
        # Format times for API call - Google Calendar API expects UTC times with Z suffix
        # So we need to convert local time to UTC for the API call
        utc_offset_seconds = time.timezone
        if time.daylight and time.localtime().tm_isdst:
            utc_offset_seconds = time.altzone
        
        start_time_utc = start_time + timedelta(seconds=utc_offset_seconds)
        end_time_utc = end_time + timedelta(seconds=utc_offset_seconds)
        
        time_min = start_time_utc.isoformat() + "Z"
        time_max = end_time_utc.isoformat() + "Z"
        
        # Call the Calendar API (your logic)
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=100,  # Large number to get all events
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        
        events = events_result.get("items", [])
        
        # Update session state
        tool_context.state[CALENDAR_LAST_FETCH] = _get_local_now().isoformat()
        tool_context.state[CALENDAR_LAST_LIST_START_DATE] = start_date if start_date else "today"
        tool_context.state[CALENDAR_LAST_LIST_DAYS] = days
        tool_context.state[CALENDAR_LAST_LIST_COUNT] = len(events)
        
        if not events:
            days_text = "today" if days == 1 else f"the next {days} days"
            return f"No upcoming events found for {days_text}."
        
        # Format events for voice response (your comprehensive formatting)
        formatted_events = []
        for event in events:
            summary = event.get("summary", "Untitled Event")
            start_time_formatted = _format_event_time(event.get("start", {}))
            location = event.get("location", "")
            location_text = f" at {location}" if location else ""
            
            formatted_events.append(f"{summary} - {start_time_formatted}{location_text}")
        
        # Store detailed events in session for other agents to use
        detailed_events = []
        for event in events:
            detailed_events.append({
                "id": event.get("id"),
                "summary": event.get("summary", "Untitled Event"),
                "start": _format_event_time(event.get("start", {})),
                "end": _format_event_time(event.get("end", {})),
                "location": event.get("location", ""),
                "description": event.get("description", ""),
                "link": event.get("htmlLink", "")
            })
        
        tool_context.state[CALENDAR_CURRENT] = detailed_events
        
        # Create voice-friendly response
        days_text = "today" if days == 1 else f"the next {days} days"
        response_lines = [f"Found {len(events)} event(s) for {days_text}:"]
        
        # Show first 5 events in voice response
        for i, event_text in enumerate(formatted_events[:5], 1):
            response_lines.append(f"{i}. {event_text}")
        
        if len(events) > 5:
            response_lines.append(f"... and {len(events) - 5} more events")
        
        log_tool_execution(tool_context, "calendar_list_events", "list_events", True, 
                         f"Retrieved {len(events)} events")
        
        return "\n".join(response_lines)
        
    except Exception as e:
        logger.error(f"Error listing calendar events: {e}")
        log_tool_execution(tool_context, "calendar_list_events", "list_events", False, str(e))
        return f"Error retrieving events: {str(e)}"


# =============================================================================
# Calendar Event Update Tool
# =============================================================================

def calendar_update_event(
    event_id: str,
    summary: str = "",
    start_time: str = "",
    end_time: str = "",
    description: str = "",
    location: str = "",
    calendar_id: str = "primary",
    tool_context=None
) -> dict:
    """Edit an existing event in Google Calendar - change title and/or reschedule."""
    if not validate_tool_context(tool_context, "calendar_update_event"):
        return {"error": "No valid tool context provided"}
    
    try:
        # Log operation
        log_tool_execution(tool_context, "calendar_update_event", "update_event", True, 
                         f"Event ID: '{event_id}', New Summary: '{summary}', Start: '{start_time}', End: '{end_time}'")
        
        # Update agent activity
        update_agent_activity(tool_context, "calendar_agent", "updating_event")
        
        # Get Calendar service
        service = get_calendar_service()
        if not service:
            return {"error": "Calendar not set up. Please run: python setup_calendar.py"}
        
        # First get the existing event (your logic)
        # Check if event_id looks like a Google Calendar ID or a title/summary
        if len(event_id) < 20 or " " in event_id:
            # Likely a title/summary, search for the event
            logger.info(f"Searching for event by title: '{event_id}'")
            event = _find_event_by_summary(service, event_id, calendar_id)
            if not event:
                return {"error": f"Event named '{event_id}' not found in calendar."}
            # Update event_id to the actual Google Calendar ID for the rest of the function
            actual_event_id = event.get("id")
            logger.info(f"Found event: '{event.get('summary')}' with ID: {actual_event_id}")
        else:
            # Looks like a proper Google Calendar ID
            try:
                event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
                actual_event_id = event_id
            except Exception:
                return {"error": f"Event with ID {event_id} not found in calendar."}
        
        original_summary = event.get("summary", "Event")
        logger.info(f"Original event summary: '{original_summary}'")
        
        # Update the event with new values (your logic)
        updated_fields = []
        
        if summary:
            logger.info(f"Updating summary from '{original_summary}' to '{summary}'")
            event["summary"] = summary
            updated_fields.append("title")
        
        if description:
            event["description"] = description
            updated_fields.append("description")
            
        if location:
            event["location"] = location
            updated_fields.append("location")
        
        # Check if any fields were actually updated
        if not updated_fields and not start_time and not end_time:
            return {"error": "No fields provided to update. Please specify summary, description, location, start_time, or end_time."}
        
        # Get timezone from the original event (your logic)
        timezone_id = "America/New_York"  # Default
        if "start" in event and "timeZone" in event["start"]:
            timezone_id = event["start"]["timeZone"]
        
        # Update start time if provided
        if start_time:
            start_dt = _parse_datetime(start_time)
            if not start_dt:
                return {"error": "Invalid start time format. Please use YYYY-MM-DD HH:MM format."}
            event["start"] = {"dateTime": start_dt.isoformat(), "timeZone": timezone_id}
            updated_fields.append("start time")
        
        # Update end time if provided
        if end_time:
            end_dt = _parse_datetime(end_time)
            if not end_dt:
                return {"error": "Invalid end time format. Please use YYYY-MM-DD HH:MM format."}
            event["end"] = {"dateTime": end_dt.isoformat(), "timeZone": timezone_id}
            updated_fields.append("end time")
        
        # Update the event
        logger.info(f"Calling Google Calendar API to update event {actual_event_id} with summary: '{event.get('summary')}'")
        updated_event = service.events().update(
            calendarId=calendar_id, 
            eventId=actual_event_id, 
            body=event
        ).execute()
        logger.info(f"API call completed. Updated event summary: '{updated_event.get('summary')}')")
        
        # Update session state
        tool_context.state[CALENDAR_LAST_UPDATED_EVENT] = {
            "id": actual_event_id,
            "original_summary": original_summary,
            "new_summary": updated_event.get("summary", original_summary),
            "updated_fields": updated_fields,
            "event_link": updated_event.get("htmlLink", "")
        }
        tool_context.state[CALENDAR_LAST_EVENT_UPDATED_AT] = _get_local_now().isoformat()
        
        log_tool_execution(tool_context, "calendar_update_event", "update_event", True, "Event updated successfully")
        
        # Return the actual updated event object (dict) from Google Calendar API
        return updated_event
        
    except Exception as e:
        logger.error(f"Error updating calendar event: {e}")
        log_tool_execution(tool_context, "calendar_update_event", "update_event", False, str(e))
        return {"error": f"Error updating event: {str(e)}"}


# =============================================================================
# Calendar Event Deletion Tool
# =============================================================================

def calendar_delete_event(
    event_id: str,
    confirm: bool = False,
    calendar_id: str = "primary",
    tool_context=None
) -> dict:
    """Delete an event from Google Calendar."""
    if not validate_tool_context(tool_context, "calendar_delete_event"):
        return {"error": "No valid tool context provided"}
    
    # Safety check - require explicit confirmation (your logic)
    if not confirm:
        return {"error": "Please confirm deletion by setting confirm=True. This action cannot be undone."}
    
    try:
        # Log operation
        log_tool_execution(tool_context, "calendar_delete_event", "delete_event", True, f"Event ID: {event_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "calendar_agent", "deleting_event")
        
        # Get Calendar service
        service = get_calendar_service()
        if not service:
            return {"error": "Calendar not set up. Please run: python setup_calendar.py"}
        
        # Get event details before deletion for better user feedback
        # Check if event_id looks like a Google Calendar ID or a title/summary
        if len(event_id) < 20 or " " in event_id:
            # Likely a title/summary, search for the event
            logger.info(f"Searching for event to delete by title: '{event_id}'")
            event = _find_event_by_summary(service, event_id, calendar_id)
            if not event:
                return {"error": f"Event named '{event_id}' not found in calendar."}
            # Update event_id to the actual Google Calendar ID for the rest of the function
            actual_event_id = event.get("id")
            logger.info(f"Found event to delete: '{event.get('summary')}' with ID: {actual_event_id}")
        else:
            # Looks like a proper Google Calendar ID
            try:
                event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
                actual_event_id = event_id
            except Exception:
                return {"error": f"Event with ID {event_id} not found in calendar."}
        
        event_summary = event.get("summary", "Event")
        event_start = _format_event_time(event.get("start", {}))
        
        # Call the Calendar API to delete the event
        logger.info(f"Calling Google Calendar API to delete event {actual_event_id} ('{event_summary}')")
        service.events().delete(calendarId=calendar_id, eventId=actual_event_id).execute()
        logger.info(f"Successfully deleted event '{event_summary}'")
        
        # Update session state
        tool_context.state[CALENDAR_LAST_DELETED_EVENT] = {
            "id": actual_event_id,
            "summary": event_summary,
            "start": event_start,
            "deleted_at": _get_local_now().isoformat()
        }
        tool_context.state[CALENDAR_LAST_DELETED_ID] = actual_event_id
        tool_context.state[CALENDAR_LAST_DELETED_AT] = _get_local_now().isoformat()
        
        log_tool_execution(tool_context, "calendar_delete_event", "delete_event", True, f"Event '{event_summary}' deleted")
        
        # Return success information as a dict
        return {
            "success": True,
            "message": f"Event '{event_summary}' (scheduled for {event_start}) has been deleted successfully",
            "deleted_event": {
                "id": actual_event_id,
                "summary": event_summary,
                "start": event_start,
                "deleted_at": _get_local_now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error deleting calendar event: {e}")
        log_tool_execution(tool_context, "calendar_delete_event", "delete_event", False, str(e))
        return {"error": f"Error deleting event: {str(e)}"}


# =============================================================================
# Helper Functions (Your Logic)
# =============================================================================

def _find_event_by_summary(service, summary_search: str, calendar_id: str = "primary", days_to_search: int = 30) -> Optional[dict]:
    """Find an event by searching for matching summary/title."""
    try:
        # Search within the next and previous days_to_search days
        start_time = _get_local_now() - timedelta(days=days_to_search)
        end_time = _get_local_now() + timedelta(days=days_to_search)
        
        # Convert to UTC for API call
        utc_offset_seconds = time.timezone
        if time.daylight and time.localtime().tm_isdst:
            utc_offset_seconds = time.altzone
        
        start_time_utc = start_time + timedelta(seconds=utc_offset_seconds)
        end_time_utc = end_time + timedelta(seconds=utc_offset_seconds)
        
        time_min = start_time_utc.isoformat() + "Z"
        time_max = end_time_utc.isoformat() + "Z"
        
        # Get events from the specified time range
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=100,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        
        events = events_result.get("items", [])
        
        # Search for events with matching summary (case insensitive partial match)
        summary_lower = summary_search.lower()
        for event in events:
            event_summary = event.get("summary", "").lower()
            if summary_lower in event_summary or event_summary in summary_lower:
                return event
                
        return None
        
    except Exception as e:
        logger.warning(f"Error searching for event by summary: {e}")
        return None

def _parse_datetime(datetime_str: str) -> Optional[datetime]:
    """Parse a datetime string into a datetime object (your logic)."""
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %I:%M %p",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %I:%M %p",
        "%m/%d/%Y",
        "%B %d, %Y %H:%M",
        "%B %d, %Y %I:%M %p",
        "%B %d, %Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    
    return None

def _format_event_time(event_time: dict) -> str:
    """Format an event time into a human-readable string with proper timezone handling."""
    if "dateTime" in event_time:
        # This is a datetime event
        dt_str = event_time["dateTime"]
        
        # Handle different datetime formats from Google Calendar
        if dt_str.endswith("Z"):
            # UTC time - convert to local time for display
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            # Convert UTC to local time for display
            utc_offset_seconds = time.timezone
            if time.daylight and time.localtime().tm_isdst:
                utc_offset_seconds = time.altzone
            local_dt = dt - timedelta(seconds=utc_offset_seconds)
            return local_dt.strftime("%A, %B %d at %I:%M %p")
        else:
            # Already has timezone info or is local time
            try:
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                return dt.strftime("%A, %B %d at %I:%M %p")
            except:
                return dt_str  # Fallback to original string
    elif "date" in event_time:
        # This is an all-day event
        try:
            date_obj = datetime.strptime(event_time['date'], "%Y-%m-%d")
            return f"{date_obj.strftime('%A, %B %d')} (All day)"
        except:
            return f"{event_time['date']} (All day)"
    return "Unknown time format"


# =============================================================================
# Create ADK Function Tools
# =============================================================================

# Event creation tool
calendar_create_event_tool = FunctionTool(func=calendar_create_event)

# Event listing tool
calendar_list_events_tool = FunctionTool(func=calendar_list_events)

# Event update tool
calendar_update_event_tool = FunctionTool(func=calendar_update_event)

# Event deletion tool
calendar_delete_event_tool = FunctionTool(func=calendar_delete_event)

# Calendar tools collection
CALENDAR_TOOLS = [
    calendar_create_event_tool,
    calendar_list_events_tool,
    calendar_update_event_tool,
    calendar_delete_event_tool
]

# Export for easy access
__all__ = [
    "calendar_create_event",
    "calendar_list_events", 
    "calendar_update_event",
    "calendar_delete_event",
    "CALENDAR_TOOLS"
]