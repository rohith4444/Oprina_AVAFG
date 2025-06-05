"""
Calendar Service Module

This module provides services for interacting with the Google Calendar API.
It handles authentication, event retrieval, and event operations.
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add the parent directory to the path to import from mcp_server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_server.auth_manager import AuthManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CalendarService:
    """Service for interacting with the Google Calendar API."""
    
    def __init__(self, auth_manager: Optional[AuthManager] = None):
        """Initialize the Calendar service.
        
        Args:
            auth_manager: Optional AuthManager instance. If not provided, a new one will be created.
        """
        self.auth_manager = auth_manager or AuthManager()
        self.service = None
        
    def _get_service(self) -> Any:
        """Get the Google Calendar API service.
        
        Returns:
            The Google Calendar API service.
        """
        if self.service is None:
            credentials = self.auth_manager.get_credentials()
            self.service = build('calendar', 'v3', credentials=credentials)
        return self.service
    
    def list_events(self, max_results: int = 10, time_min: Optional[str] = None, time_max: Optional[str] = None) -> List[Dict[str, Any]]:
        """List Google Calendar events.
        
        Args:
            max_results: The maximum number of events to return.
            time_min: The start time for the events (ISO 8601 format).
            time_max: The end time for the events (ISO 8601 format).
            
        Returns:
            A list of event metadata.
        """
        try:
            service = self._get_service()
            
            # Set default time range if not provided
            if time_min is None:
                time_min = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            if time_max is None:
                time_max = (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                logger.info('No upcoming events found.')
                return []
                
            # Format events for response
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                formatted_events.append({
                    'id': event['id'],
                    'summary': event.get('summary', 'No Title'),
                    'description': event.get('description', 'No Description'),
                    'start': start,
                    'end': end,
                    'location': event.get('location', 'No Location'),
                    'attendees': [attendee.get('email') for attendee in event.get('attendees', [])],
                    'creator': event.get('creator', {}).get('email', 'Unknown'),
                    'status': event.get('status', 'confirmed')
                })
                
            return formatted_events
            
        except HttpError as error:
            logger.error(f'An error occurred: {error}')
            raise
    
    def get_event(self, event_id: str) -> Dict[str, Any]:
        """Get a Google Calendar event by ID.
        
        Args:
            event_id: The ID of the event to retrieve.
            
        Returns:
            The event details.
        """
        try:
            service = self._get_service()
            event = service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            return {
                'id': event['id'],
                'summary': event.get('summary', 'No Title'),
                'description': event.get('description', 'No Description'),
                'start': start,
                'end': end,
                'location': event.get('location', 'No Location'),
                'attendees': [attendee.get('email') for attendee in event.get('attendees', [])],
                'creator': event.get('creator', {}).get('email', 'Unknown'),
                'status': event.get('status', 'confirmed')
            }
            
        except HttpError as error:
            logger.error(f'An error occurred: {error}')
            raise
    
    def create_event(self, summary: str, start_time: str, end_time: str, description: Optional[str] = None, 
                    location: Optional[str] = None, attendees: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a Google Calendar event.
        
        Args:
            summary: The event summary (title).
            start_time: The event start time (ISO 8601 format).
            end_time: The event end time (ISO 8601 format).
            description: Optional event description.
            location: Optional event location.
            attendees: Optional list of attendee email addresses.
            
        Returns:
            The created event details.
        """
        try:
            service = self._get_service()
            
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
                },
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
                body=event,
                sendUpdates='all'
            ).execute()
            
            logger.info(f'Event created: {created_event.get("htmlLink")}')
            return created_event
            
        except HttpError as error:
            logger.error(f'An error occurred: {error}')
            raise
    
    def update_event(self, event_id: str, summary: Optional[str] = None, start_time: Optional[str] = None, 
                    end_time: Optional[str] = None, description: Optional[str] = None, 
                    location: Optional[str] = None, attendees: Optional[List[str]] = None) -> Dict[str, Any]:
        """Update a Google Calendar event.
        
        Args:
            event_id: The ID of the event to update.
            summary: Optional new event summary (title).
            start_time: Optional new event start time (ISO 8601 format).
            end_time: Optional new event end time (ISO 8601 format).
            description: Optional new event description.
            location: Optional new event location.
            attendees: Optional new list of attendee email addresses.
            
        Returns:
            The updated event details.
        """
        try:
            service = self._get_service()
            
            # Get existing event
            event = service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Update fields if provided
            if summary:
                event['summary'] = summary
                
            if start_time:
                event['start']['dateTime'] = start_time
                
            if end_time:
                event['end']['dateTime'] = end_time
                
            if description:
                event['description'] = description
                
            if location:
                event['location'] = location
                
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            # Update event
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            logger.info(f'Event updated: {updated_event.get("htmlLink")}')
            return updated_event
            
        except HttpError as error:
            logger.error(f'An error occurred: {error}')
            raise
    
    def delete_event(self, event_id: str) -> None:
        """Delete a Google Calendar event.
        
        Args:
            event_id: The ID of the event to delete.
        """
        try:
            service = self._get_service()
            service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            
            logger.info(f'Event {event_id} deleted.')
            
        except HttpError as error:
            logger.error(f'An error occurred: {error}')
            raise 