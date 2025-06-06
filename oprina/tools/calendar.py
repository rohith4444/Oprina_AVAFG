"""
Direct Calendar Tools for ADK - Complete ADK Integration

Simple ADK-compatible tools that use Google Calendar API directly through existing auth services
with proper tool_context validation, session state management, and comprehensive logging.
"""

import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(3):  # Updated for new structure depth
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk.tools import FunctionTool
from services.google_cloud.calendar_auth import get_calendar_service, check_calendar_connection
from services.logging.logger import setup_logger

# Import ADK utility functions
from oprina.common.utils import (
    validate_tool_context, update_agent_activity, get_user_preferences,
    update_service_connection_status, get_service_connection_status, log_tool_execution
)

# Import session state constants
from oprina.common.session_keys import (
    USER_CALENDAR_CONNECTED, USER_NAME, USER_PREFERENCES,
    CALENDAR_CURRENT, CALENDAR_LAST_FETCH, CALENDAR_UPCOMING_COUNT, CALENDAR_LAST_EVENT_CREATED,
    CALENDAR_LAST_QUERY_DAYS, CALENDAR_LAST_EVENT_CREATED_AT, CALENDAR_LAST_CREATED_EVENT_ID,
    CALENDAR_LAST_QUICK_EVENT, CALENDAR_LAST_QUICK_EVENT_AT,
    CALENDAR_LAST_UPDATED_EVENT, CALENDAR_LAST_EVENT_UPDATED_AT, CALENDAR_LAST_DELETED_EVENT,
    CALENDAR_LAST_FREE_TIME_SEARCH, CALENDAR_LAST_FREE_SLOTS, CALENDAR_LAST_AVAILABILITY_CHECK,
    CALENDAR_LAST_TIME_REQUEST, CALENDAR_AVAILABLE_CALENDARS, CALENDAR_CALENDARS_LIST_AT, CALENDAR_CALENDARS_COUNT
)

logger = setup_logger("calendar_tools", console_output=True)


# =============================================================================
# Calendar Connection Tools
# =============================================================================

def calendar_check_connection(tool_context=None) -> str:
    """Check Calendar connection status with comprehensive ADK integration."""
    if not validate_tool_context(tool_context, "calendar_check_connection"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "calendar_check_connection", "status_check", True, "Checking Calendar connection")
        
        # Update agent activity
        update_agent_activity(tool_context, "calendar_agent", "checking_connection")
        
        # Check session state first using constants
        calendar_connected = tool_context.session.state.get(USER_CALENDAR_CONNECTED, False)
        
        if calendar_connected:
            # Verify actual connection
            connection_status = check_calendar_connection()
            if connection_status.get("connected", False):
                calendar_count = connection_status.get("calendar_count", 0)
                
                # Update session state
                update_service_connection_status(
                    tool_context, "calendar", True, "",
                    {"last_check": datetime.utcnow().isoformat(), "calendar_count": calendar_count}
                )
                
                return f"Calendar connected with access to {calendar_count} calendars"
            else:
                error_msg = connection_status.get('error', 'Unknown error')
                log_tool_execution(tool_context, "calendar_check_connection", "status_check", False, error_msg)
                
                # Update session state with error
                update_service_connection_status(
                    tool_context, "calendar", False, "",
                    {"last_error": error_msg, "last_check": datetime.utcnow().isoformat()}
                )
                
                return f"Calendar connection issue: {error_msg}"
        else:
            return "Calendar not connected. Please authenticate with Google Calendar first."
            
    except Exception as e:
        logger.error(f"Error checking Calendar connection: {e}")
        log_tool_execution(tool_context, "calendar_check_connection", "status_check", False, str(e))
        return f"Error checking Calendar connection: {str(e)}"


def calendar_authenticate(tool_context=None) -> str:
    """Authenticate with Calendar and update session state."""
    if not validate_tool_context(tool_context, "calendar_authenticate"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "calendar_authenticate", "authenticate", True, "Starting Calendar authentication")
        
        # Update agent activity
        update_agent_activity(tool_context, "calendar_agent", "authenticating")
        
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
            
            # Update session state with successful authentication
            update_service_connection_status(
                tool_context, "calendar", True, "",
                {
                    "authenticated_at": datetime.utcnow().isoformat(),
                    "calendar_count": len(calendars),
                    "primary_calendar": primary_calendar
                }
            )
            
            log_tool_execution(tool_context, "calendar_authenticate", "authenticate", True, f"Authenticated with {len(calendars)} calendars")
            return f"Calendar authentication successful. Primary calendar: {primary_calendar}"
        else:
            log_tool_execution(tool_context, "calendar_authenticate", "authenticate", False, "Service creation failed")
            return "Calendar authentication failed. Please check your credentials."
            
    except Exception as e:
        logger.error(f"Calendar authentication error: {e}")
        log_tool_execution(tool_context, "calendar_authenticate", "authenticate", False, str(e))
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
    """List upcoming calendar events with ADK integration."""
    if not validate_tool_context(tool_context, "calendar_list_events"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "calendar_list_events", "list_events", True, 
                         f"Days ahead: {days_ahead}, Max results: {max_results}")
        
        # Update agent activity
        update_agent_activity(tool_context, "calendar_agent", "listing_events")
        
        if not tool_context.session.state.get(USER_CALENDAR_CONNECTED, False):
            return "Calendar not connected. Please authenticate first."
        
        service = get_calendar_service()
        if not service:
            log_tool_execution(tool_context, "calendar_list_events", "list_events", False, "Calendar service unavailable")
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
            response = f"No events found in the next {days_ahead} days"
            
            # Update session state even for empty results using constants
            tool_context.session.state[CALENDAR_LAST_FETCH] = datetime.utcnow().isoformat()
            tool_context.session.state[CALENDAR_UPCOMING_COUNT] = 0
            tool_context.session.state[CALENDAR_CURRENT] = []
            
            return response
        
        # Format events
        response_lines = [f"Upcoming events (next {days_ahead} days):"]
        event_summaries = []
        
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
            
            event_info = {
                "id": event.get('id'),
                "summary": summary,
                "start": start_formatted,
                "location": location
            }
            event_summaries.append(event_info)
            
            response_lines.append(f"{i}. {summary} - {start_formatted}{location_text}")
        
        if len(events) > max_results:
            response_lines.append(f"... and {len(events) - max_results} more events")
        
        # Update session state with results using constants
        tool_context.session.state[CALENDAR_LAST_FETCH] = datetime.utcnow().isoformat()
        tool_context.session.state[CALENDAR_UPCOMING_COUNT] = len(event_summaries)
        tool_context.session.state[CALENDAR_CURRENT] = event_summaries
        tool_context.session.state[CALENDAR_LAST_QUERY_DAYS] = days_ahead
        
        log_tool_execution(tool_context, "calendar_list_events", "list_events", True, 
                         f"Retrieved {len(event_summaries)} events")
        
        return "\n".join(response_lines)
        
    except Exception as e:
        logger.error(f"Error listing calendar events: {e}")
        log_tool_execution(tool_context, "calendar_list_events", "list_events", False, str(e))
        return f"Error retrieving calendar events: {str(e)}"


def calendar_get_today_events(tool_context=None) -> str:
    """Get today's calendar events with ADK integration."""
    if not validate_tool_context(tool_context, "calendar_get_today_events"):
        return "Error: No valid tool context provided"
    
    # Update agent activity
    update_agent_activity(tool_context, "calendar_agent", "getting_today_events")
    
    return calendar_list_events(days_ahead=1, tool_context=tool_context)


def calendar_get_week_events(tool_context=None) -> str:
    """Get this week's calendar events with ADK integration."""
    if not validate_tool_context(tool_context, "calendar_get_week_events"):
        return "Error: No valid tool context provided"
    
    # Update agent activity
    update_agent_activity(tool_context, "calendar_agent", "getting_week_events")
    
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
    """Create a new calendar event with ADK integration."""
    if not validate_tool_context(tool_context, "calendar_create_event"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "calendar_create_event", "create_event", True, 
                         f"Summary: '{summary}', Start: {start_time}, End: {end_time}")
        
        # Update agent activity
        update_agent_activity(tool_context, "calendar_agent", "creating_event")
        
        if not tool_context.session.state.get(USER_CALENDAR_CONNECTED, False):
            return "Calendar not connected. Please authenticate first."
        
        service = get_calendar_service()
        if not service:
            log_tool_execution(tool_context, "calendar_create_event", "create_event", False, "Calendar service unavailable")
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
        
        # Update session state using constants
        tool_context.session.state[CALENDAR_LAST_EVENT_CREATED] = {
            "id": event.get('id'),
            "summary": summary,
            "start": start_formatted,
            "end": end_formatted,
            "location": location,
            "description": description
        }
        tool_context.session.state[CALENDAR_LAST_EVENT_CREATED_AT] = datetime.utcnow().isoformat()
        tool_context.session.state[CALENDAR_LAST_CREATED_EVENT_ID] = event.get('id')
        
        log_tool_execution(tool_context, "calendar_create_event", "create_event", True, "Event created successfully")
        return f"Event '{summary}' created successfully on {start_formatted} to {end_formatted}"
        
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        log_tool_execution(tool_context, "calendar_create_event", "create_event", False, str(e))
        return f"Error creating event: {str(e)}"


def calendar_create_quick_event(event_text: str, tool_context=None) -> str:
    """Create an event using quick text with ADK integration."""
    if not validate_tool_context(tool_context, "calendar_create_quick_event"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "calendar_create_quick_event", "quick_create", True, 
                         f"Event text: '{event_text}'")
        
        # Update agent activity
        update_agent_activity(tool_context, "calendar_agent", "creating_quick_event")
        
        if not tool_context.session.state.get(USER_CALENDAR_CONNECTED, False):
            return "Calendar not connected. Please authenticate first."
        
        service = get_calendar_service()
        if not service:
            log_tool_execution(tool_context, "calendar_create_quick_event", "quick_create", False, "Calendar service unavailable")
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
        
        # Update session state using constants
        tool_context.session.state[CALENDAR_LAST_QUICK_EVENT] = {
            "id": event.get('id'),
            "summary": summary,
            "start": start_formatted,
            "original_text": event_text
        }
        tool_context.session.state[CALENDAR_LAST_QUICK_EVENT_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "calendar_create_quick_event", "quick_create", True, "Quick event created")
        return f"Quick event '{summary}' created for {start_formatted}"
        
    except Exception as e:
        logger.error(f"Error creating quick event: {e}")
        log_tool_execution(tool_context, "calendar_create_quick_event", "quick_create", False, str(e))
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
    """Update an existing calendar event with ADK integration."""
    if not validate_tool_context(tool_context, "calendar_update_event"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "calendar_update_event", "update_event", True, 
                         f"Event ID: {event_id}, Summary: '{summary}'")
        
        # Update agent activity
        update_agent_activity(tool_context, "calendar_agent", "updating_event")
        
        if not tool_context.session.state.get(USER_CALENDAR_CONNECTED, False):
            return "Calendar not connected. Please authenticate first."
        
        service = get_calendar_service()
        if not service:
            log_tool_execution(tool_context, "calendar_update_event", "update_event", False, "Calendar service unavailable")
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
        
        # Update session state using constants
        updated_fields = []
        if summary:
            updated_fields.append('summary')
        if description:
            updated_fields.append('description')
        if location:
            updated_fields.append('location')
        if start_time:
            updated_fields.append('start_time')
        if end_time:
            updated_fields.append('end_time')

        tool_context.session.state[CALENDAR_LAST_UPDATED_EVENT] = {
            "id": event_id,
            "summary": updated_event.get('summary', 'Event'),
            "updated_fields": updated_fields
        }
        
        tool_context.session.state[CALENDAR_LAST_EVENT_UPDATED_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "calendar_update_event", "update_event", True, "Event updated successfully")
        return f"Event '{updated_event.get('summary', 'Event')}' updated successfully"
        
    except Exception as e:
        logger.error(f"Error updating calendar event: {e}")
        log_tool_execution(tool_context, "calendar_update_event", "update_event", False, str(e))
        return f"Error updating event: {str(e)}"


def calendar_delete_event(event_id: str, calendar_id: str = "primary", tool_context=None) -> str:
    """Delete a calendar event with ADK integration."""
    if not validate_tool_context(tool_context, "calendar_delete_event"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "calendar_delete_event", "delete_event", True, f"Event ID: {event_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "calendar_agent", "deleting_event")
        
        if not tool_context.session.state.get(USER_CALENDAR_CONNECTED, False):
            return "Calendar not connected. Please authenticate first."
        
        service = get_calendar_service()
        if not service:
            log_tool_execution(tool_context, "calendar_delete_event", "delete_event", False, "Calendar service unavailable")
            return "Unable to connect to Calendar service"
        
        # Get event details before deletion
        try:
            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            event_summary = event.get('summary', 'Event')
        except:
            return f"Event with ID {event_id} not found"
        
        # Delete the event
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        
        # Update session state using constants
        tool_context.session.state[CALENDAR_LAST_DELETED_EVENT] = {
            "id": event_id,
            "summary": event_summary,
            "deleted_at": datetime.utcnow().isoformat()
        }
        
        log_tool_execution(tool_context, "calendar_delete_event", "delete_event", True, f"Event '{event_summary}' deleted")
        return f"Event '{event_summary}' deleted successfully"
        
    except Exception as e:
        logger.error(f"Error deleting calendar event: {e}")
        log_tool_execution(tool_context, "calendar_delete_event", "delete_event", False, str(e))
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
    """Find free time slots in the calendar with ADK integration."""
    if not validate_tool_context(tool_context, "calendar_find_free_time"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "calendar_find_free_time", "find_free_time", True, 
                         f"Duration: {duration_minutes}min, Days: {days_ahead}, Hours: {working_hours_start}-{working_hours_end}")
        
        # Update agent activity
        update_agent_activity(tool_context, "calendar_agent", "finding_free_time")
        
        if not tool_context.session.state.get(USER_CALENDAR_CONNECTED, False):
            return "Calendar not connected. Please authenticate first."
        
        service = get_calendar_service()
        if not service:
            log_tool_execution(tool_context, "calendar_find_free_time", "find_free_time", False, "Calendar service unavailable")
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
            result = f"No {duration_minutes}-minute free slots found in the next {days_ahead} days during working hours"
        else:
            # Format response
            response_lines = [f"Available {duration_minutes}-minute time slots:"]
            for i, slot in enumerate(free_slots[:5], 1):
                response_lines.append(f"{i}. {slot['date']} from {slot['start']} to {slot['end']}")
            
            if len(free_slots) > 5:
                response_lines.append(f"... and {len(free_slots) - 5} more available slots")
            
            result = "\n".join(response_lines)
        
        # Update session state using constants
        tool_context.session.state[CALENDAR_LAST_FREE_TIME_SEARCH] = {
            "duration_minutes": duration_minutes,
            "days_ahead": days_ahead,
            "working_hours": f"{working_hours_start}-{working_hours_end}",
            "slots_found": len(free_slots),
            "search_at": datetime.utcnow().isoformat()
        }
        tool_context.session.state[CALENDAR_LAST_FREE_SLOTS] = free_slots[:10]  # Store up to 10 slots
        
        log_tool_execution(tool_context, "calendar_find_free_time", "find_free_time", True, 
                         f"Found {len(free_slots)} free slots")
        return result
        
    except Exception as e:
        logger.error(f"Error finding free time: {e}")
        log_tool_execution(tool_context, "calendar_find_free_time", "find_free_time", False, str(e))
        return f"Error finding free time: {str(e)}"


def calendar_check_availability(date: str, start_time: str, end_time: str, tool_context=None) -> str:
    """Check if a specific time slot is available with ADK integration."""
    if not validate_tool_context(tool_context, "calendar_check_availability"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "calendar_check_availability", "check_availability", True, 
                         f"Date: {date}, Time: {start_time}-{end_time}")
        
        # Update agent activity
        update_agent_activity(tool_context, "calendar_agent", "checking_availability")
        
        if not tool_context.session.state.get(USER_CALENDAR_CONNECTED, False):
            return "Calendar not connected. Please authenticate first."
        
        service = get_calendar_service()
        if not service:
            log_tool_execution(tool_context, "calendar_check_availability", "check_availability", False, "Calendar service unavailable")
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
        
        is_available = len(busy_times) == 0
        
        # Update session state using constants
        tool_context.session.state[CALENDAR_LAST_AVAILABILITY_CHECK] = {
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "available": is_available,
            "checked_at": datetime.utcnow().isoformat()
        }
        
        if is_available:
            result = f"Time slot from {start_time} to {end_time} on {date} is AVAILABLE"
        else:
            result = f"Time slot from {start_time} to {end_time} on {date} is NOT available (conflicts found)"
        
        log_tool_execution(tool_context, "calendar_check_availability", "check_availability", True, 
                         f"Availability: {is_available}")
        return result
        
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        log_tool_execution(tool_context, "calendar_check_availability", "check_availability", False, str(e))
        return f"Error checking availability: {str(e)}"


# =============================================================================
# Calendar Information Tools
# =============================================================================

def calendar_get_current_time(tool_context=None) -> str:
    """Get current date and time with ADK integration."""
    if not validate_tool_context(tool_context, "calendar_get_current_time"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "calendar_get_current_time", "get_time", True, "Getting current time")
        
        # Update agent activity
        update_agent_activity(tool_context, "calendar_agent", "getting_current_time")
        
        now = datetime.now()
        
        # Update session state using constants
        tool_context.session.state[CALENDAR_LAST_TIME_REQUEST] = now.isoformat()
        
        result = f"Current time: {now.strftime('%A, %B %d, %Y at %I:%M %p')}"
        
        log_tool_execution(tool_context, "calendar_get_current_time", "get_time", True, "Current time provided")
        return result
        
    except Exception as e:
        logger.error(f"Error getting current time: {e}")
        log_tool_execution(tool_context, "calendar_get_current_time", "get_time", False, str(e))
        return f"Error getting current time: {str(e)}"


def calendar_list_calendars(tool_context=None) -> str:
    """List all available calendars with ADK integration."""
    if not validate_tool_context(tool_context, "calendar_list_calendars"):
        return "Error: No valid tool context provided"
    
    try:
        # Log operation
        log_tool_execution(tool_context, "calendar_list_calendars", "list_calendars", True, "Listing calendars")
        
        # Update agent activity
        update_agent_activity(tool_context, "calendar_agent", "listing_calendars")
        
        if not tool_context.session.state.get(USER_CALENDAR_CONNECTED, False):
            return "Calendar not connected. Please authenticate first."
        
        service = get_calendar_service()
        if not service:
            log_tool_execution(tool_context, "calendar_list_calendars", "list_calendars", False, "Calendar service unavailable")
            return "Unable to connect to Calendar service"
        
        # Get calendar list
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        if not calendars:
            return "No calendars found"
        
        response_lines = [f"Available calendars ({len(calendars)}):"]
        calendar_summaries = []
        
        for i, cal in enumerate(calendars, 1):
            summary = cal.get('summary', 'Unnamed Calendar')
            primary = " (Primary)" if cal.get('primary') else ""
            access_role = cal.get('accessRole', 'reader')
            
            calendar_info = {
                "id": cal.get('id'),
                "summary": summary,
                "primary": cal.get('primary', False),
                "access_role": access_role
            }
            calendar_summaries.append(calendar_info)
            
            response_lines.append(f"{i}. {summary}{primary} - {access_role}")
        
        # Update session state using constants
        tool_context.session.state[CALENDAR_AVAILABLE_CALENDARS] = calendar_summaries
        tool_context.session.state[CALENDAR_CALENDARS_LIST_AT] = datetime.utcnow().isoformat()
        tool_context.session.state[CALENDAR_CALENDARS_COUNT] = len(calendars)
        
        log_tool_execution(tool_context, "calendar_list_calendars", "list_calendars", True, 
                         f"Listed {len(calendars)} calendars")
        return "\n".join(response_lines)
        
    except Exception as e:
        logger.error(f"Error listing calendars: {e}")
        log_tool_execution(tool_context, "calendar_list_calendars", "list_calendars", False, str(e))
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
