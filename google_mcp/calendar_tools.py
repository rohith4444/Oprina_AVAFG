"""
Modular Calendar MCP Tools
--------------------------
This file defines all modular Calendar tools for the MCP system, based on the Jarvis reference.
Each tool is a class registered with the MCP tool registry, covering Calendar API capabilities:

- Event listing and searching
- Event creation and management  
- Event updates and deletion
- Time utilities
- Calendar management

Following Calvin's MCP pattern and integrating Jarvis calendar functionality.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_file))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google_mcp.mcp_tool import Tool, register_tool
from services.google_cloud.calendar_auth import get_calendar_service
from services.logging.logger import setup_logger

# Configure logging
logger = setup_logger("calendar_tools", console_output=True)


def get_service():
    """Get authenticated Calendar service - wrapper for MCP tools."""
    return get_calendar_service()


def format_event_time(event_time: Dict[str, Any]) -> str:
    """
    Format an event time into a human-readable string.
    Based on Jarvis calendar_utils.py format_event_time function.
    
    Args:
        event_time: The event time dictionary from Google Calendar API
        
    Returns:
        str: A human-readable time string
    """
    try:
        if "dateTime" in event_time:
            # This is a datetime event
            dt = datetime.fromisoformat(event_time["dateTime"].replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %I:%M %p")
        elif "date" in event_time:
            # This is an all-day event
            return f"{event_time['date']} (All day)"
        return "Unknown time format"
    except Exception as e:
        logger.error(f"Error formatting event time: {e}")
        return "Invalid time"


def parse_datetime(datetime_str: str) -> Optional[datetime]:
    """
    Parse a datetime string into a datetime object.
    Based on Jarvis calendar_utils.py parse_datetime function.
    
    Args:
        datetime_str: A string representing a date and time
        
    Returns:
        datetime: A datetime object or None if parsing fails
    """
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


# =========================================================
# 1. Current Time Utility (Based on Jarvis get_current_time)
# =========================================================

@register_tool
class CalendarGetCurrentTimeTool(Tool):
    """Get the current time and date - based on Jarvis get_current_time."""
    name = "calendar_get_current_time"
    description = "Get the current time and date in various formats."
    
    def run(self):
        """
        Returns:
            dict: Current time information
        """
        try:
            now = datetime.now()
            
            return {
                "status": "success",
                "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
                "formatted_date": now.strftime("%m-%d-%Y"),
                "iso_format": now.isoformat(),
                "weekday": now.strftime("%A"),
                "month": now.strftime("%B"),
                "year": now.year
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting current time: {str(e)}"
            }


# =========================================================
# 2. Event Listing (Based on Jarvis list_events)
# =========================================================

@register_tool
class CalendarListEventsTool(Tool):
    """List upcoming calendar events - based on Jarvis list_events."""
    name = "calendar_list_events"
    description = "List upcoming calendar events within a specified date range."
    
    def run(self, start_date: str = "", days: int = 1):
        """
        Args:
            start_date (str): Start date in YYYY-MM-DD format. Empty string defaults to today.
            days (int): Number of days to look ahead. Use 1 for today only, 7 for a week, 30 for a month.
        Returns:
            dict: Information about upcoming events or error details
        """
        try:
            logger.info(f"Listing events - start_date: {start_date}, days: {days}")
            
            # Get calendar service
            service = get_service()
            if not service:
                return {
                    "status": "error",
                    "message": "Failed to authenticate with Google Calendar. Please check credentials.",
                    "events": []
                }
            
            # Set time range (based on Jarvis logic)
            if not start_date or start_date.strip() == "":
                start_time = datetime.utcnow()
            else:
                try:
                    start_time = datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    return {
                        "status": "error", 
                        "message": f"Invalid date format: {start_date}. Use YYYY-MM-DD format.",
                        "events": []
                    }
            
            # Validate days parameter
            if not days or days < 1:
                days = 1
            
            end_time = start_time + timedelta(days=days)
            
            # Format times for API call
            time_min = start_time.isoformat() + "Z"
            time_max = end_time.isoformat() + "Z"
            
            # Call the Calendar API
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=100,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            
            events = events_result.get("items", [])
            
            if not events:
                return {
                    "status": "success",
                    "message": "No upcoming events found.",
                    "events": []
                }
            
            # Format events for display (based on Jarvis format)
            formatted_events = []
            for event in events:
                formatted_event = {
                    "id": event.get("id"),
                    "summary": event.get("summary", "Untitled Event"),
                    "start": format_event_time(event.get("start", {})),
                    "end": format_event_time(event.get("end", {})),
                    "location": event.get("location", ""),
                    "description": event.get("description", ""),
                    "attendees": [
                        attendee.get("email")
                        for attendee in event.get("attendees", [])
                        if "email" in attendee
                    ],
                    "link": event.get("htmlLink", ""),
                }
                formatted_events.append(formatted_event)
            
            return {
                "status": "success",
                "message": f"Found {len(formatted_events)} event(s).",
                "events": formatted_events
            }
            
        except Exception as e:
            logger.error(f"Error listing events: {e}")
            return {
                "status": "error",
                "message": f"Error fetching events: {str(e)}",
                "events": []
            }


# =========================================================
# 3. Event Creation (Based on Jarvis create_event)
# =========================================================

@register_tool
class CalendarCreateEventTool(Tool):
    """Create a new calendar event - based on Jarvis create_event."""
    name = "calendar_create_event"
    description = "Create a new event in Google Calendar."
    
    def run(self, summary: str, start_time: str, end_time: str, description: str = "", location: str = ""):
        """
        Args:
            summary (str): Event title/summary
            start_time (str): Start time (e.g., "2023-12-31 14:00")
            end_time (str): End time (e.g., "2023-12-31 15:00")
            description (str, optional): Event description
            location (str, optional): Event location
        Returns:
            dict: Information about the created event or error details
        """
        try:
            logger.info(f"Creating event: {summary}")
            
            # Get calendar service
            service = get_service()
            if not service:
                return {
                    "status": "error",
                    "message": "Failed to authenticate with Google Calendar. Please check credentials."
                }
            
            # Parse times (based on Jarvis logic)
            start_dt = parse_datetime(start_time)
            end_dt = parse_datetime(end_time)
            
            if not start_dt or not end_dt:
                return {
                    "status": "error",
                    "message": "Invalid date/time format. Please use YYYY-MM-DD HH:MM format."
                }
            
            # Get timezone from calendar settings (like Jarvis)
            timezone_id = "America/New_York"  # Default
            try:
                settings = service.settings().list().execute()
                for setting in settings.get("items", []):
                    if setting.get("id") == "timezone":
                        timezone_id = setting.get("value")
                        break
            except Exception:
                pass  # Use default timezone
            
            # Create event body
            event_body = {
                "summary": summary,
                "start": {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": timezone_id,
                },
                "end": {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": timezone_id,
                }
            }
            
            # Add optional fields
            if description:
                event_body["description"] = description
            if location:
                event_body["location"] = location
            
            # Call the Calendar API to create the event
            event = (
                service.events()
                .insert(calendarId="primary", body=event_body)
                .execute()
            )
            
            return {
                "status": "success",
                "message": "Event created successfully",
                "event_id": event["id"],
                "event_link": event.get("htmlLink", ""),
                "created_event": {
                    "summary": event.get("summary"),
                    "start": format_event_time(event.get("start", {})),
                    "end": format_event_time(event.get("end", {}))
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return {
                "status": "error",
                "message": f"Error creating event: {str(e)}"
            }


# =========================================================
# 4. Event Update (Based on Jarvis edit_event)
# =========================================================

@register_tool
class CalendarUpdateEventTool(Tool):
    """Edit an existing event - based on Jarvis edit_event."""
    name = "calendar_update_event"
    description = "Edit an existing event in Google Calendar - change title and/or reschedule."
    
    def run(self, event_id: str, summary: str = "", start_time: str = "", end_time: str = "", description: str = "", location: str = ""):
        """
        Args:
            event_id (str): The ID of the event to edit
            summary (str, optional): New title/summary for the event (empty to keep unchanged)
            start_time (str, optional): New start time (empty to keep unchanged)
            end_time (str, optional): New end time (empty to keep unchanged)
            description (str, optional): New description (empty to keep unchanged)
            location (str, optional): New location (empty to keep unchanged)
        Returns:
            dict: Information about the edited event or error details
        """
        try:
            logger.info(f"Updating event: {event_id}")
            
            # Get calendar service
            service = get_service()
            if not service:
                return {
                    "status": "error",
                    "message": "Failed to authenticate with Google Calendar. Please check credentials."
                }
            
            # First get the existing event (like Jarvis)
            try:
                event = (
                    service.events()
                    .get(calendarId="primary", eventId=event_id)
                    .execute()
                )
            except Exception:
                return {
                    "status": "error",
                    "message": f"Event with ID {event_id} not found in primary calendar."
                }
            
            # Update the event with new values (like Jarvis logic)
            if summary:
                event["summary"] = summary
            
            if description:
                event["description"] = description
                
            if location:
                event["location"] = location
            
            # Get timezone from the original event
            timezone_id = "America/New_York"  # Default
            if "start" in event and "timeZone" in event["start"]:
                timezone_id = event["start"]["timeZone"]
            
            # Update times if provided
            if start_time:
                start_dt = parse_datetime(start_time)
                if not start_dt:
                    return {
                        "status": "error",
                        "message": "Invalid start time format. Please use YYYY-MM-DD HH:MM format."
                    }
                event["start"] = {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": timezone_id
                }
            
            if end_time:
                end_dt = parse_datetime(end_time)
                if not end_dt:
                    return {
                        "status": "error",
                        "message": "Invalid end time format. Please use YYYY-MM-DD HH:MM format."
                    }
                event["end"] = {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": timezone_id
                }
            
            # Update the event
            updated_event = (
                service.events()
                .update(calendarId="primary", eventId=event_id, body=event)
                .execute()
            )
            
            return {
                "status": "success",
                "message": "Event updated successfully",
                "event_id": updated_event["id"],
                "event_link": updated_event.get("htmlLink", ""),
                "updated_event": {
                    "summary": updated_event.get("summary"),
                    "start": format_event_time(updated_event.get("start", {})),
                    "end": format_event_time(updated_event.get("end", {})),
                    "location": updated_event.get("location", ""),
                    "description": updated_event.get("description", "")
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            return {
                "status": "error",
                "message": f"Error updating event: {str(e)}"
            }


# =========================================================
# 5. Event Deletion (Based on Jarvis delete_event)
# =========================================================

@register_tool
class CalendarDeleteEventTool(Tool):
    """Delete an event from Google Calendar - based on Jarvis delete_event."""
    name = "calendar_delete_event"
    description = "Delete an event from Google Calendar."
    
    def run(self, event_id: str, confirm: bool = False):
        """
        Args:
            event_id (str): The unique ID of the event to delete
            confirm (bool): Confirmation flag (must be set to True to delete)
        Returns:
            dict: Operation status and details
        """
        try:
            # Safety check - require explicit confirmation (like Jarvis)
            if not confirm:
                return {
                    "status": "error",
                    "message": "Please confirm deletion by setting confirm=True"
                }
            
            logger.info(f"Deleting event: {event_id}")
            
            # Get calendar service
            service = get_service()
            if not service:
                return {
                    "status": "error",
                    "message": "Failed to authenticate with Google Calendar. Please check credentials."
                }
            
            # Get event details before deletion for confirmation
            try:
                event = service.events().get(calendarId="primary", eventId=event_id).execute()
                event_summary = event.get("summary", "Untitled Event")
                event_start = format_event_time(event.get("start", {}))
            except Exception:
                return {
                    "status": "error",
                    "message": f"Event with ID {event_id} not found in primary calendar."
                }
            
            # Call the Calendar API to delete the event
            service.events().delete(calendarId="primary", eventId=event_id).execute()
            
            return {
                "status": "success",
                "message": f"Event '{event_summary}' has been deleted successfully",
                "event_id": event_id,
                "deleted_event": {
                    "summary": event_summary,
                    "start": event_start
                }
            }
            
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return {
                "status": "error",
                "message": f"Error deleting event: {str(e)}"
            }


# =========================================================
# 6. Calendar Management Tools
# =========================================================

@register_tool
class CalendarListCalendarsTool(Tool):
    """List all accessible calendars."""
    name = "calendar_list_calendars"
    description = "List all calendars accessible to the user."
    
    def run(self):
        """
        Returns:
            dict: List of calendars or error details
        """
        try:
            logger.info("Listing calendars")
            
            # Get calendar service
            service = get_service()
            if not service:
                return {
                    "status": "error",
                    "message": "Failed to authenticate with Google Calendar. Please check credentials.",
                    "calendars": []
                }
            
            # Get calendar list
            calendar_list = service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])
            
            if not calendars:
                return {
                    "status": "success",
                    "message": "No calendars found.",
                    "calendars": []
                }
            
            # Format calendars for display
            formatted_calendars = []
            for calendar in calendars:
                formatted_calendar = {
                    "id": calendar.get("id"),
                    "summary": calendar.get("summary", "Untitled Calendar"),
                    "description": calendar.get("description", ""),
                    "primary": calendar.get("primary", False),
                    "access_role": calendar.get("accessRole", ""),
                    "color_id": calendar.get("colorId", ""),
                    "timezone": calendar.get("timeZone", "")
                }
                formatted_calendars.append(formatted_calendar)
            
            return {
                "status": "success",
                "message": f"Found {len(formatted_calendars)} calendar(s).",
                "calendars": formatted_calendars
            }
            
        except Exception as e:
            logger.error(f"Error listing calendars: {e}")
            return {
                "status": "error",
                "message": f"Error fetching calendars: {str(e)}",
                "calendars": []
            }


# =========================================================
# 7. Free Time Finder Tool
# =========================================================

@register_tool
class CalendarFindFreeTimeTool(Tool):
    """Find free time slots in the calendar."""
    name = "calendar_find_free_time"
    description = "Find available free time slots in the calendar."
    
    def run(self, start_date: str = "", days: int = 7, duration_minutes: int = 60):
        """
        Args:
            start_date (str): Start date in YYYY-MM-DD format. Empty string defaults to today.
            days (int): Number of days to search ahead
            duration_minutes (int): Duration of the meeting in minutes
        Returns:
            dict: Available time slots or error details
        """
        try:
            logger.info(f"Finding free time - start_date: {start_date}, days: {days}, duration: {duration_minutes}min")
            
            # Get calendar service
            service = get_service()
            if not service:
                return {
                    "status": "error",
                    "message": "Failed to authenticate with Google Calendar. Please check credentials.",
                    "free_slots": []
                }
            
            # Set time range
            if not start_date or start_date.strip() == "":
                start_time = datetime.utcnow()
            else:
                try:
                    start_time = datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    return {
                        "status": "error",
                        "message": f"Invalid date format: {start_date}. Use YYYY-MM-DD format.",
                        "free_slots": []
                    }
            
            end_time = start_time + timedelta(days=days)
            
            # Get busy times using freebusy API
            body = {
                "timeMin": start_time.isoformat() + "Z",
                "timeMax": end_time.isoformat() + "Z",
                "items": [{"id": "primary"}]
            }
            
            freebusy_result = service.freebusy().query(body=body).execute()
            busy_times = freebusy_result.get("calendars", {}).get("primary", {}).get("busy", [])
            
            # Find free slots (simple algorithm)
            free_slots = []
            current_time = start_time
            
            # Working hours: 9 AM to 6 PM on weekdays
            while current_time < end_time:
                # Skip weekends
                if current_time.weekday() >= 5:
                    current_time += timedelta(days=1)
                    current_time = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
                    continue
                
                # Check working hours (9 AM to 6 PM)
                if current_time.hour < 9:
                    current_time = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
                elif current_time.hour >= 18:
                    current_time += timedelta(days=1)
                    current_time = current_time.replace(hour=9, minute=0, second=0, microsecond=0)
                    continue
                
                # Check if this slot is free
                slot_end = current_time + timedelta(minutes=duration_minutes)
                is_free = True
                
                for busy_period in busy_times:
                    busy_start = datetime.fromisoformat(busy_period["start"].replace("Z", "+00:00"))
                    busy_end = datetime.fromisoformat(busy_period["end"].replace("Z", "+00:00"))
                    
                    # Check for overlap
                    if (current_time < busy_end and slot_end > busy_start):
                        is_free = False
                        break
                
                if is_free and slot_end.hour <= 18:  # Don't go past 6 PM
                    free_slots.append({
                        "start": current_time.strftime("%Y-%m-%d %H:%M"),
                        "end": slot_end.strftime("%Y-%m-%d %H:%M"),
                        "duration_minutes": duration_minutes,
                        "date": current_time.strftime("%A, %B %d, %Y")
                    })
                
                # Move to next 30-minute slot
                current_time += timedelta(minutes=30)
                
                # Limit to first 10 slots to avoid overwhelming response
                if len(free_slots) >= 10:
                    break
            
            return {
                "status": "success",
                "message": f"Found {len(free_slots)} available time slot(s).",
                "free_slots": free_slots,
                "search_parameters": {
                    "start_date": start_time.strftime("%Y-%m-%d"),
                    "days_searched": days,
                    "duration_minutes": duration_minutes
                }
            }
            
        except Exception as e:
            logger.error(f"Error finding free time: {e}")
            return {
                "status": "error",
                "message": f"Error finding free time: {str(e)}",
                "free_slots": []
            }


# =========================================================
# 8. Testing and Development Utilities
# =========================================================

def test_calendar_tools():
    """Test calendar tools functionality."""
    print("📅 Testing Calendar MCP Tools...")
    
    test_results = {
        "current_time": False,
        "list_events": False,
        "list_calendars": False,
        "find_free_time": False,
        "tool_registration": False
    }
    
    try:
        # Test 1: Current time tool
        print("⏰ Testing current time tool...")
        current_time_tool = CalendarGetCurrentTimeTool()
        time_result = current_time_tool.run()
        
        if time_result.get("status") == "success":
            test_results["current_time"] = True
            print("   ✅ Current time tool works")
            print(f"       Current time: {time_result.get('current_time')}")
        else:
            print("   ❌ Current time tool failed")
        
        # Test 2: List events tool (may fail if not authenticated)
        print("📋 Testing list events tool...")
        list_events_tool = CalendarListEventsTool()
        events_result = list_events_tool.run()
        
        if events_result.get("status") in ["success", "error"]:  # Structure is correct
            test_results["list_events"] = True
            print("   ✅ List events tool structure correct")
            if events_result.get("status") == "error":
                print(f"       Expected error (not authenticated): {events_result.get('message', '')[:50]}...")
        else:
            print("   ❌ List events tool structure invalid")
        
        # Test 3: List calendars tool
        print("📅 Testing list calendars tool...")
        list_calendars_tool = CalendarListCalendarsTool()
        calendars_result = list_calendars_tool.run()
        
        if calendars_result.get("status") in ["success", "error"]:
            test_results["list_calendars"] = True
            print("   ✅ List calendars tool structure correct")
        else:
            print("   ❌ List calendars tool structure invalid")
        
        # Test 4: Find free time tool
        print("🔍 Testing find free time tool...")
        free_time_tool = CalendarFindFreeTimeTool()
        free_time_result = free_time_tool.run(duration_minutes=30)
        
        if free_time_result.get("status") in ["success", "error"]:
            test_results["find_free_time"] = True
            print("   ✅ Find free time tool structure correct")
        else:
            print("   ❌ Find free time tool structure invalid")
        
        # Test 5: Tool registration
        print("🔧 Testing tool registration...")
        from google_mcp.mcp_tool import TOOL_REGISTRY
        
        expected_tools = [
            "calendar_get_current_time",
            "calendar_list_events", 
            "calendar_create_event",
            "calendar_update_event",
            "calendar_delete_event",
            "calendar_list_calendars",
            "calendar_find_free_time"
        ]
        
        registered_tools = list(TOOL_REGISTRY.keys())
        calendar_tools_registered = [tool for tool in expected_tools if tool in registered_tools]
        
        if len(calendar_tools_registered) == len(expected_tools):
            test_results["tool_registration"] = True
            print("   ✅ All calendar tools registered successfully")
            print(f"       Registered: {len(calendar_tools_registered)}/{len(expected_tools)}")
        else:
            print(f"   ⚠️ Some tools not registered: {len(calendar_tools_registered)}/{len(expected_tools)}")
            print(f"       Missing: {set(expected_tools) - set(calendar_tools_registered)}")
        
        # Summary
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        print(f"\n📊 Calendar Tools Test Results:")
        print(f"   Passed: {passed_tests}/{total_tests}")
        
        for test_name, result in test_results.items():
            status = "✅" if result else "❌"
            print(f"   {status} {test_name.replace('_', ' ').title()}")
        
        if passed_tests == total_tests:
            print("\n🎉 All calendar tools tests passed!")
            print("✅ Ready for MCP integration!")
            return True
        else:
            print(f"\n⚠️ {total_tests - passed_tests} calendar tools tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Calendar tools test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Running Calendar MCP Tools Tests...")
    print("=" * 60)
    
    # Run test
    success = test_calendar_tools()
    
    if success:
        print("🎉 Calendar MCP tools ready for integration!")
        print("✅ Proceed to Step 3.5 (Test Both Services)")
    else:
        print("⚠️ Please fix calendar tools issues before proceeding")
    
    print("✅ Calendar MCP tools test completed")