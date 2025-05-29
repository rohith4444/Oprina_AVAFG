"""
Direct Calendar Tools for ADK - Replaces MCP Integration

Simple ADK-compatible tools that use Google Calendar API directly through existing auth services.
No MCP bridge complexity - just direct function tools.
"""

import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(7):
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk.tools import FunctionTool
from services.google_cloud.calendar_auth import get_calendar_service, check_calendar_connection
from agents.voice.sub_agents.common import (
    USER_CALENDAR_CONNECTED
)
from services.logging.logger import setup_logger

logger = setup_logger("calendar_tools", console_output=True)


# =============================================================================
# Calendar Connection Tools
# =============================================================================

def calendar_check_connection(tool_context=None) -> str:
    """Check Calendar connection status."""
    try:
        if not tool_context or not hasattr(tool_context, 'session'):
            return "Unable to check Calendar connection - no session context"
        
        # Check session state first
        calendar_connected = tool_context.session.state.get(USER_CALENDAR_CONNECTED, False)
        
        if calendar_connected:
            # Verify actual connection
            connection_status = check_calendar_connection()
            if connection_status.get("connected", False):
                calendar_count = connection_status.get("calendar_count", 0)
                return f"Calendar connected with access to {calendar_count} calendars"
            else:
                return f"Calendar connection issue: {connection_status.get('error', 'Unknown error')}"
        else:
            return "Calendar not connected. Please authenticate with Google Calendar first."
            
    except Exception as e:
        logger.error(f"Error checking Calendar connection: {e}")
        return f"Error checking Calendar connection: {str(e)}"


def calendar_authenticate(tool_context=None) -> str:
    """Authenticate with Google Calendar."""
    try:
        # Test Calendar service creation
        service = get_calendar_service()
        
        if service:
            # Get calendar list to confirm connection
            calendar_list = service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            
            primary_calendar = next(
                (cal['summary'] for cal in calendars if cal.get('primary')), 
                'Primary Calendar'
            )
            
            return f"Calendar authentication successful. Primary calendar: {primary_calendar}"
        else:
            return "Calendar authentication failed. Please check your credentials."
            
    except Exception as e:
        logger.error(f"Calendar authentication error: {e}")
        return f"Calendar authentication failed: {str(e)}"


# =============================================================================
# Calendar Event Listing Tools
# =============================================================================

def calendar_list_events(
    days_ahead: int = 7, 
    max_results: int = 10, 
    calendar_id: str = "primary",
    tool_context=None
) -> str:
    """List upcoming calendar events."""
    try:
        if not tool_context.session.state.get(USER_CALENDAR_CONNECTED, False):
            return "Calendar not connected. Please authenticate first."
        
        service = get_calendar_service()
        if not service:
            return "Unable to connect to Calendar service"
        
        # Calculate time range
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        # Get events
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f"No events found in the next {days_ahead} days"
        
        # Format events
        response_lines = [f"Upcoming events (next {days_ahead} days):"]
        
        for i, event in enumerate(events[:max_results], 1):
            summary = event.get('summary', 'No title')
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            # Format start time
            if 'T' in start:  # DateTime event
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                start_formatted = start_dt.strftime('%Y-%m-%d %I:%M %p')
            else:  # All-day event
                start_formatted = f"{start} (All day)"
            
            location = event.get('location', '')
            location_text = f" | Location: {location}" if location else ""
            
            response_lines.append(f"{i}. {summary} - {start_formatted}{location_text}")
        
        if len(events) > max_results:
            response_lines.append(f"... and {len(events) - max_results} more events")
        
        return "\n".join(response_lines)
        
    except Exception as e:
        logger.error(f"Error listing calendar events: {e}")
        return f"Error retrieving calendar events: {str(e)}"


def calendar_get_today_events(tool_context=None) -> str:
    """Get today's calendar events."""
    return calendar_list_events(days_ahead=1, tool_context=tool_context)


def calendar_get_week_events(tool_context=None) -> str:
    """Get this week's calendar events."""
    return calendar_list_events(days_ahead=7, tool_context=tool_context)


# =============================================================================
# Calendar Event Creation Tools
# =============================================================================

def calendar_create_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    calendar_id: str = "primary",
    tool_context=None
) -> str:
    """Create a new calendar event."""
    try:
        if not tool_context.session.state.get(USER_CALENDAR_CONNECTED, False):
            return "Calendar not connected. Please authenticate first."
        
        service = get_calendar_service()
        if not service:
            return "Unable to connect to Calendar service"
        
        # Parse times
        try:
            start_dt = _parse_datetime(start_time)
            end_dt = _parse_datetime(end_time)
            
            if not start_dt or not end_dt:
                return "Invalid date/time format. Please use format like '2024-01-15 14:00' or '2024-01-15 2:00 PM'"
                
        except Exception as e:
            return f"Error parsing date/time: {str(e)}"
        
        # Get timezone from calendar
        timezone_id = "America/New_York"  # Default
        try:
            calendar_info = service.calendars().get(calendarId=calendar_id).execute()
            timezone_id = calendar_info.get('timeZone', timezone_id)
        except:
            pass
        
        # Create event body
        event_body = {
            'summary': summary,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': timezone_id,
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': timezone_id,
            }
        }
        
        if description:
            event_body['description'] = description
        if location:
            event_body['location'] = location
        
        # Create the event
        event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        
        # Format response
        start_formatted = start_dt.strftime('%Y-%m-%d %I:%M %p')
        end_formatted = end_dt.strftime('%I:%M %p')
        
        return f"Event '{summary}' created successfully on {start_formatted} to {end_formatted}"
        
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        return f"Error creating event: {str(e)}"


def calendar_create_quick_event(event_text: str, tool_context=None) -> str:
    """Create an event using quick text (like 'Meeting tomorrow 2pm')."""
    try:
        if not tool_context.session.state.get(USER_CALENDAR_CONNECTED, False):
            return "Calendar not connected. Please authenticate first."
        
        service = get_calendar_service()
        if not service:
            return "Unable to connect to Calendar service"
        
        # Use Google Calendar's quick add feature
        event = service.events().quickAdd(
            calendarId='primary',
            text=event_text
        ).execute()
        
        summary = event.get('summary', 'Event')
        start = event['start'].get('dateTime', event['start'].get('date'))
        
        if 'T' in start:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            start_formatted = start_dt.strftime('%Y-%m-%d %I:%M %p')
        else:
            start_formatted = f"{start} (All day)"
        
        return f"Quick event '{summary}' created for {start_formatted}"
        
    except Exception as e:
        logger.error(f"Error creating quick event: {e}")
        return f"Error creating quick event: {str(e)}"


# =============================================================================
# Calendar Event Management Tools
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
) -> str:
    """Update an existing calendar event."""
    try:
        if not tool_context.session.state.get(USER_CALENDAR_CONNECTED, False):
            return "Calendar not connected. Please authenticate first."
        
        service = get_calendar_service()
        if not service:
            return "Unable to connect to Calendar service"
        
        # Get existing event
        try:
            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        except:
            return f"Event with ID {event_id} not found"
        
        # Update fields
        if summary:
            event['summary'] = summary
        if description:
            event['description'] = description
        if location:
            event['location'] = location
        
        # Update times if provided
        if start_time:
            start_dt = _parse_datetime(start_time)
            if start_dt:
                timezone_id = event['start'].get('timeZone', 'America/New_York')
                event['start'] = {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': timezone_id
                }
        
        if end_time:
            end_dt = _parse_datetime(end_time)
            if end_dt:
                timezone_id = event['end'].get('timeZone', 'America/New_York')
                event['end'] = {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': timezone_id
                }
        
        # Update the event
        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event
        ).execute()
        
        return f"Event '{updated_event.get('summary', 'Event')}' updated successfully"
        
    except Exception as e:
        logger.error(f"Error updating calendar event: {e}")
        return f"Error updating event: {str(e)}"


def calendar_delete_event(event_id: str, calendar_id: str = "primary", tool_context=None) -> str:
    """Delete a calendar event."""
    try:
        if not tool_context.session.state.get(USER_CALENDAR_CONNECTED, False):
            return "Calendar not connected. Please authenticate first."
        
        service = get_calendar_service()
        if not service:
            return "Unable to connect to Calendar service"
        
        # Get event details before deletion
        try:
            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            event_summary = event.get('summary', 'Event')
        except:
            return f"Event with ID {event_id} not found"
        
        # Delete the event
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        
        return f"Event '{event_summary}' deleted successfully"
        
    except Exception as e:
        logger.error(f"Error deleting calendar event: {e}")
        return f"Error deleting event: {str(e)}"


# =============================================================================
# Calendar Availability Tools
# =============================================================================

def calendar_find_free_time(
    duration_minutes: int = 60,
    days_ahead: int = 7,
    working_hours_start: int = 9,
    working_hours_end: int = 17,
    calendar_id: str = "primary",
    tool_context=None
) -> str:
    """Find free time slots in the calendar."""
    try:
        if not tool_context.session.state.get(USER_CALENDAR_CONNECTED, False):
            return "Calendar not connected. Please authenticate first."
        
        service = get_calendar_service()
        if not service:
            return "Unable to connect to Calendar service"
        
        # Calculate time range
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        # Get busy times
        body = {
            'timeMin': time_min,
            'timeMax': time_max,
            'items': [{'id': calendar_id}]
        }
        
        freebusy_result = service.freebusy().query(body=body).execute()
        busy_times = freebusy_result.get('calendars', {}).get(calendar_id, {}).get('busy', [])
        
        # Find free slots
        free_slots = []
        current_time = now.replace(minute=0, second=0, microsecond=0)
        
        for day in range(days_ahead):
            day_start = current_time + timedelta(days=day)
            
            # Skip weekends
            if day_start.weekday() >= 5:
                continue
            
            # Check working hours
            work_start = day_start.replace(hour=working_hours_start, minute=0)
            work_end = day_start.replace(hour=working_hours_end, minute=0)
            
            # Find free slots in this day
            slot_start = work_start
            while slot_start + timedelta(minutes=duration_minutes) <= work_end:
                slot_end = slot_start + timedelta(minutes=duration_minutes)
                
                # Check if this slot conflicts with busy times
                is_free = True
                for busy_period in busy_times:
                    busy_start = datetime.fromisoformat(busy_period['start'].replace('Z', '+00:00'))
                    busy_end = datetime.fromisoformat(busy_period['end'].replace('Z', '+00:00'))
                    
                    # Check for overlap
                    if slot_start < busy_end and slot_end > busy_start:
                        is_free = False
                        break
                
                if is_free:
                    free_slots.append({
                        'start': slot_start.strftime('%Y-%m-%d %I:%M %p'),
                        'end': slot_end.strftime('%I:%M %p'),
                        'date': slot_start.strftime('%A, %B %d'),
                        'duration': duration_minutes
                    })
                
                # Move to next 30-minute slot
                slot_start += timedelta(minutes=30)
                
                # Limit results
                if len(free_slots) >= 10:
                    break
            
            if len(free_slots) >= 10:
                break
        
        if not free_slots:
            return f"No {duration_minutes}-minute free slots found in the next {days_ahead} days during working hours"
        
        # Format response
        response_lines = [f"Available {duration_minutes}-minute time slots:"]
        for i, slot in enumerate(free_slots[:5], 1):
            response_lines.append(f"{i}. {slot['date']} from {slot['start']} to {slot['end']}")
        
        if len(free_slots) > 5:
            response_lines.append(f"... and {len(free_slots) - 5} more available slots")
        
        return "\n".join(response_lines)
        
    except Exception as e:
        logger.error(f"Error finding free time: {e}")
        return f"Error finding free time: {str(e)}"


def calendar_check_availability(date: str, start_time: str, end_time: str, tool_context=None) -> str:
    """Check if a specific time slot is available."""
    try:
        if not tool_context.session.state.get(USER_CALENDAR_CONNECTED, False):
            return "Calendar not connected. Please authenticate first."
        
        service = get_calendar_service()
        if not service:
            return "Unable to connect to Calendar service"
        
        # Parse the requested time
        try:
            if ' ' in start_time:
                start_dt = _parse_datetime(f"{date} {start_time}")
                end_dt = _parse_datetime(f"{date} {end_time}")
            else:
                start_dt = _parse_datetime(f"{date} {start_time}")
                end_dt = _parse_datetime(f"{date} {end_time}")
                
            if not start_dt or not end_dt:
                return "Invalid date/time format. Use format like '2024-01-15 2:00 PM'"
                
        except Exception as e:
            return f"Error parsing date/time: {str(e)}"
        
        # Check for conflicts
        time_min = start_dt.isoformat() + 'Z'
        time_max = end_dt.isoformat() + 'Z'
        
        body = {
            'timeMin': time_min,
            'timeMax': time_max,
            'items': [{'id': 'primary'}]
        }
        
        freebusy_result = service.freebusy().query(body=body).execute()
        busy_times = freebusy_result.get('calendars', {}).get('primary', {}).get('busy', [])
        
        if busy_times:
            return f"Time slot from {start_time} to {end_time} on {date} is NOT available (conflicts found)"
        else:
            return f"Time slot from {start_time} to {end_time} on {date} is AVAILABLE"
        
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        return f"Error checking availability: {str(e)}"


# =============================================================================
# Calendar Information Tools
# =============================================================================

def calendar_get_current_time(tool_context=None) -> str:
    """Get current date and time."""
    try:
        now = datetime.now()
        
        return f"Current time: {now.strftime('%A, %B %d, %Y at %I:%M %p')}"
        
    except Exception as e:
        logger.error(f"Error getting current time: {e}")
        return f"Error getting current time: {str(e)}"


def calendar_list_calendars(tool_context=None) -> str:
    """List all available calendars."""
    try:
        if not tool_context.session.state.get(USER_CALENDAR_CONNECTED, False):
            return "Calendar not connected. Please authenticate first."
        
        service = get_calendar_service()
        if not service:
            return "Unable to connect to Calendar service"
        
        # Get calendar list
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        if not calendars:
            return "No calendars found"
        
        response_lines = [f"Available calendars ({len(calendars)}):"]
        for i, cal in enumerate(calendars, 1):
            summary = cal.get('summary', 'Unnamed Calendar')
            primary = " (Primary)" if cal.get('primary') else ""
            access_role = cal.get('accessRole', 'reader')
            
            response_lines.append(f"{i}. {summary}{primary} - {access_role}")
        
        return "\n".join(response_lines)
        
    except Exception as e:
        logger.error(f"Error listing calendars: {e}")
        return f"Error listing calendars: {str(e)}"


# =============================================================================
# Helper Functions
# =============================================================================

def _parse_datetime(datetime_str: str) -> Optional[datetime]:
    """Parse various datetime string formats."""
    formats = [
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


# =============================================================================
# Create ADK Function Tools
# =============================================================================

# Connection tools
calendar_check_connection_tool = FunctionTool(func=calendar_check_connection)
calendar_authenticate_tool = FunctionTool(func=calendar_authenticate)

# Event listing tools
calendar_list_events_tool = FunctionTool(func=calendar_list_events)
calendar_get_today_events_tool = FunctionTool(func=calendar_get_today_events)
calendar_get_week_events_tool = FunctionTool(func=calendar_get_week_events)

# Event creation tools
calendar_create_event_tool = FunctionTool(func=calendar_create_event)
calendar_create_quick_event_tool = FunctionTool(func=calendar_create_quick_event)

# Event management tools
calendar_update_event_tool = FunctionTool(func=calendar_update_event)
calendar_delete_event_tool = FunctionTool(func=calendar_delete_event)

# Availability tools
calendar_find_free_time_tool = FunctionTool(func=calendar_find_free_time)
calendar_check_availability_tool = FunctionTool(func=calendar_check_availability)

# Information tools
calendar_get_current_time_tool = FunctionTool(func=calendar_get_current_time)
calendar_list_calendars_tool = FunctionTool(func=calendar_list_calendars)

# Calendar tools collection
CALENDAR_TOOLS = [
    calendar_check_connection_tool,
    calendar_authenticate_tool,
    calendar_list_events_tool,
    calendar_get_today_events_tool,
    calendar_get_week_events_tool,
    calendar_create_event_tool,
    calendar_create_quick_event_tool,
    calendar_update_event_tool,
    calendar_delete_event_tool,
    calendar_find_free_time_tool,
    calendar_check_availability_tool,
    calendar_get_current_time_tool,
    calendar_list_calendars_tool
]

# Export for easy access
__all__ = [
    "calendar_check_connection",
    "calendar_authenticate",
    "calendar_list_events", 
    "calendar_get_today_events",
    "calendar_get_week_events",
    "calendar_create_event",
    "calendar_create_quick_event",
    "calendar_update_event",
    "calendar_delete_event",
    "calendar_find_free_time",
    "calendar_check_availability",
    "calendar_get_current_time",
    "calendar_list_calendars",
    "CALENDAR_TOOLS"
]


# =============================================================================
# Testing
# =============================================================================

if __name__ == "__main__":
    print("🧪 Testing Direct Calendar Tools...")
    
    # Mock tool context for testing
    class MockSession:
        def __init__(self):
            self.state = {USER_CALENDAR_CONNECTED: False}
    
    class MockToolContext:
        def __init__(self):
            self.session = MockSession()
    
    mock_context = MockToolContext()
    
    # Test connection check
    result = calendar_check_connection(mock_context)
    print(f"Connection check: {result}")
    
    # Test current time
    time_result = calendar_get_current_time(mock_context)
    print(f"Current time: {time_result}")
    
    print("✅ Direct Calendar tools created successfully!")