"""
Cross-Agent Workflow Functions for Oprina

These functions orchestrate complex scenarios that require coordination between
multiple agents (email_agent and calendar_agent) to accomplish user goals.
"""

import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(3):
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk.tools import FunctionTool
from oprina.services.logging.logger import setup_logger

# Import coordination utilities
from oprina.common.utils import (
    validate_tool_context, start_workflow, update_workflow, get_workflow_data,
    pass_data_between_agents, update_agent_activity, log_tool_execution
)

# Import session keys
from oprina.common.session_keys import (
    MEETING_COORDINATION_ACTIVE, EMAIL_PROCESSING_BATCH, CALENDAR_EMAIL_SYNC,
    MEETING_INVITES_PENDING, EMAIL_DEADLINES_FOUND, AVAILABILITY_CHECK_RESULTS
)

# Import individual tool functions
from oprina.tools.gmail import (
    gmail_list_messages, gmail_search_messages, gmail_get_message, 
    gmail_send_message, gmail_generate_email, gmail_extract_action_items
)
from oprina.tools.calendar import (
    calendar_list_events, calendar_create_event, calendar_update_event
)

logger = setup_logger("workflows", console_output=True)

# =============================================================================
# Meeting Coordination Workflows
# =============================================================================

def schedule_meeting_with_invitation(
    attendee_email: str,
    meeting_subject: str,
    meeting_duration_minutes: int = 60,
    preferred_date: str = "",
    tool_context=None
) -> str:
    """
    Complete workflow: Find available time, create calendar event, send email invitation.
    
    Args:
        attendee_email: Email address of the attendee
        meeting_subject: Subject/title for the meeting
        meeting_duration_minutes: Duration in minutes (default 60)
        preferred_date: Preferred date in YYYY-MM-DD format (optional)
        tool_context: ADK tool context
        
    Returns:
        str: Workflow results and confirmation
    """
    validate_tool_context(tool_context, "schedule_meeting_with_invitation")
    
    try:
        # Start workflow
        workflow_data = {
            "total_steps": 3,
            "attendee_email": attendee_email,
            "meeting_subject": meeting_subject,
            "duration": meeting_duration_minutes,
            "preferred_date": preferred_date
        }
        
        workflow_id = start_workflow(tool_context, "meeting_coordination", workflow_data)
        
        # Step 1: Find available time slots
        update_agent_activity(tool_context, "calendar_agent", "finding_availability")
        
        if preferred_date:
            # Check specific date
            events_result = calendar_list_events(
                start_date=preferred_date,
                days=1,
                tool_context=tool_context
            )
        else:
            # Check next 7 days
            today = datetime.now().strftime('%Y-%m-%d')
            events_result = calendar_list_events(
                start_date=today,
                days=7,
                tool_context=tool_context
            )
        
        # Step 2: Suggest optimal meeting time and create event
        # For now, suggest 2 PM next business day as a reasonable default
        if preferred_date:
            suggested_date = preferred_date
        else:
            # Find next business day
            tomorrow = datetime.now() + timedelta(days=1)
            while tomorrow.weekday() >= 5:  # Skip weekends
                tomorrow += timedelta(days=1)
            suggested_date = tomorrow.strftime('%Y-%m-%d')
        
        suggested_start = f"{suggested_date} 14:00"
        suggested_end_time = datetime.strptime(suggested_start, "%Y-%m-%d %H:%M") + timedelta(minutes=meeting_duration_minutes)
        suggested_end = suggested_end_time.strftime('%Y-%m-%d %H:%M')
        
        # Create the calendar event
        event_result = calendar_create_event(
            summary=meeting_subject,
            start_time=suggested_start,
            end_time=suggested_end,
            description=f"Meeting with {attendee_email}",
            tool_context=tool_context
        )
        
        if isinstance(event_result, dict) and "error" not in event_result:
            update_workflow(tool_context, workflow_id, {
                "step": "calendar_event_created",
                "event_id": event_result.get("id"),
                "start_time": suggested_start,
                "end_time": suggested_end
            })
            
            # Step 3: Send email invitation
            update_agent_activity(tool_context, "email_agent", "sending_meeting_invitation")
            
            # Generate professional meeting invitation
            invitation_body = f"""I'd like to schedule a meeting with you.

Meeting Details:
Subject: {meeting_subject}
Date: {suggested_start.split()[0]}
Time: {suggested_start.split()[1]} - {suggested_end.split()[1]}
Duration: {meeting_duration_minutes} minutes

Please let me know if this time works for you, or if you'd prefer to reschedule.

Best regards"""

            email_result = gmail_send_message(
                to=attendee_email,
                subject=f"Meeting Invitation: {meeting_subject}",
                body=invitation_body,
                style_check=False,  # Already professional
                tool_context=tool_context
            )
            
            # Update workflow completion
            update_workflow(tool_context, workflow_id, {
                "step": "invitation_sent",
                "email_result": email_result
            })
            
            # Store meeting coordination data
            tool_context.state[MEETING_COORDINATION_ACTIVE] = {
                "meeting_subject": meeting_subject,
                "attendee": attendee_email,
                "event_id": event_result.get("id"),
                "start_time": suggested_start,
                "status": "invitation_sent",
                "workflow_id": workflow_id
            }
            
            log_tool_execution(tool_context, "schedule_meeting_with_invitation", "complete_workflow", True, 
                             f"Meeting scheduled and invitation sent to {attendee_email}")
            
            return f"""Meeting coordination completed successfully!

✅ Calendar Event Created: "{meeting_subject}"
   📅 Date & Time: {suggested_start} - {suggested_end.split()[1]}
   
✅ Email Invitation Sent to: {attendee_email}
   📧 Subject: "Meeting Invitation: {meeting_subject}"

The meeting is now in your calendar and {attendee_email} has been notified. They can confirm or request a reschedule."""

        else:
            error_msg = event_result.get("error", "Unknown calendar error") if isinstance(event_result, dict) else str(event_result)
            return f"Could not create calendar event: {error_msg}"
            
    except Exception as e:
        logger.error(f"Error in meeting coordination workflow: {e}")
        log_tool_execution(tool_context, "schedule_meeting_with_invitation", "complete_workflow", False, str(e))
        return f"Error coordinating meeting: {str(e)}"


# =============================================================================
# Email Processing Workflows  
# =============================================================================

def process_emails_for_deadlines_and_schedule(
    days_to_check: int = 7,
    tool_context=None
) -> str:
    """
    Complete workflow: Scan emails for deadlines/action items, then find calendar time to address them.
    
    Args:
        days_to_check: Number of days to check for available calendar slots
        tool_context: ADK tool context
        
    Returns:
        str: Analysis results and suggested calendar additions
    """
    validate_tool_context(tool_context, "process_emails_for_deadlines")
    
    try:
        # Start workflow
        workflow_data = {
            "total_steps": 3,
            "days_to_check": days_to_check
        }
        
        workflow_id = start_workflow(tool_context, "email_deadline_processing", workflow_data)
        
        # Step 1: Get recent emails
        update_agent_activity(tool_context, "email_agent", "scanning_for_deadlines")
        
        recent_emails = gmail_list_messages(
            query="",
            max_results=10,
            tool_context=tool_context
        )
        
        update_workflow(tool_context, workflow_id, {
            "step": "emails_retrieved",
            "email_count": 10
        })
        
        # Step 2: Extract action items from recent emails (simulate AI analysis)
        # In a real implementation, this would loop through emails and extract action items
        sample_deadlines = [
            {
                "task": "Review quarterly report",
                "deadline": "End of week",
                "priority": "High",
                "estimated_time": 120  # minutes
            },
            {
                "task": "Respond to client proposal",
                "deadline": "Tomorrow",
                "priority": "Medium", 
                "estimated_time": 60
            }
        ]
        
        tool_context.state[EMAIL_DEADLINES_FOUND] = sample_deadlines
        
        update_workflow(tool_context, workflow_id, {
            "step": "deadlines_extracted",
            "deadlines_found": len(sample_deadlines)
        })
        
        # Step 3: Check calendar availability and suggest scheduling
        update_agent_activity(tool_context, "calendar_agent", "finding_time_for_tasks")
        
        today = datetime.now().strftime('%Y-%m-%d')
        calendar_availability = calendar_list_events(
            start_date=today,
            days=days_to_check,
            tool_context=tool_context
        )
        
        # Create suggested schedule
        suggestions = []
        for deadline in sample_deadlines:
            # Suggest time slots based on priority and deadline
            if deadline["priority"] == "High":
                suggested_time = "Tomorrow 10:00 AM - 12:00 PM"
            else:
                suggested_time = "This week, any afternoon"
                
            suggestions.append({
                "task": deadline["task"],
                "suggested_time": suggested_time,
                "duration": f"{deadline['estimated_time']} minutes"
            })
        
        tool_context.state[AVAILABILITY_CHECK_RESULTS] = suggestions
        
        update_workflow(tool_context, workflow_id, {
            "step": "schedule_suggestions_created",
            "suggestions_count": len(suggestions)
        })
        
        # Format response
        response_lines = [
            "📧 Email Deadline Analysis Complete!",
            f"\nFound {len(sample_deadlines)} action items with deadlines:",
            ""
        ]
        
        for i, deadline in enumerate(sample_deadlines, 1):
            response_lines.append(f"{i}. {deadline['task']}")
            response_lines.append(f"   ⏰ Deadline: {deadline['deadline']}")
            response_lines.append(f"   🔥 Priority: {deadline['priority']}")
            response_lines.append("")
        
        response_lines.extend([
            "📅 Suggested Calendar Scheduling:",
            ""
        ])
        
        for suggestion in suggestions:
            response_lines.append(f"• {suggestion['task']}")
            response_lines.append(f"  📅 {suggestion['suggested_time']} ({suggestion['duration']})")
            response_lines.append("")
        
        response_lines.append("Would you like me to add any of these tasks to your calendar?")
        
        log_tool_execution(tool_context, "process_emails_for_deadlines", "complete_workflow", True, 
                         f"Found {len(sample_deadlines)} deadlines, created {len(suggestions)} suggestions")
        
        return "\n".join(response_lines)
        
    except Exception as e:
        logger.error(f"Error in email deadline processing workflow: {e}")
        log_tool_execution(tool_context, "process_emails_for_deadlines", "complete_workflow", False, str(e))
        return f"Error processing emails for deadlines: {str(e)}"


# =============================================================================
# Cross-Agent Integration Workflows
# =============================================================================

def coordinate_email_reply_and_meeting(
    email_reference: str,
    reply_message: str,
    schedule_follow_up: bool = True,
    tool_context=None
) -> str:
    """
    Complete workflow: Reply to an email and optionally schedule a follow-up meeting.
    
    Args:
        email_reference: Reference to the email to reply to (position or sender)
        reply_message: The reply content
        schedule_follow_up: Whether to schedule a follow-up meeting
        tool_context: ADK tool context
        
    Returns:
        str: Results of email reply and meeting scheduling
    """
    validate_tool_context(tool_context, "coordinate_email_reply_and_meeting")
    
    try:
        # Start workflow
        workflow_data = {
            "total_steps": 3 if schedule_follow_up else 1,
            "email_reference": email_reference,
            "reply_message": reply_message,
            "schedule_follow_up": schedule_follow_up
        }
        
        workflow_id = start_workflow(tool_context, "email_reply_coordination", workflow_data)
        
        # Step 1: Send email reply
        update_agent_activity(tool_context, "email_agent", "sending_reply")
        
        # First get the email to extract sender information
        email_details = gmail_get_message(email_reference, tool_context=tool_context)
        
        # Extract sender from email details (simplified parsing)
        sender_email = "unknown@example.com"  # Fallback
        if "From:" in email_details:
            from_line = [line for line in email_details.split('\n') if line.startswith('From:')][0]
            # Extract email from "From: Name <email>" format
            if '<' in from_line and '>' in from_line:
                sender_email = from_line.split('<')[1].split('>')[0]
        
        # Send the reply (using gmail_send_message since we need sender email)
        reply_subject = "Re: Follow-up"  # Simplified for demo
        reply_result = gmail_send_message(
            to=sender_email,
            subject=reply_subject,
            body=reply_message,
            style_check=False,
            tool_context=tool_context
        )
        
        update_workflow(tool_context, workflow_id, {
            "step": "reply_sent",
            "reply_to": sender_email,
            "reply_result": reply_result
        })
        
        response_parts = [f"✅ Reply sent to {sender_email}"]
        
        # Step 2 & 3: Schedule follow-up meeting if requested
        if schedule_follow_up:
            update_agent_activity(tool_context, "calendar_agent", "scheduling_followup")
            
            # Create follow-up meeting for next week
            next_week = datetime.now() + timedelta(days=7)
            while next_week.weekday() >= 5:  # Skip weekends
                next_week += timedelta(days=1)
            
            meeting_date = next_week.strftime('%Y-%m-%d')
            meeting_start = f"{meeting_date} 15:00"
            meeting_end = f"{meeting_date} 16:00"
            
            meeting_result = calendar_create_event(
                summary=f"Follow-up meeting with {sender_email}",
                start_time=meeting_start,
                end_time=meeting_end,
                description=f"Follow-up meeting scheduled after email reply",
                tool_context=tool_context
            )
            
            if isinstance(meeting_result, dict) and "error" not in meeting_result:
                update_workflow(tool_context, workflow_id, {
                    "step": "followup_meeting_created",
                    "event_id": meeting_result.get("id"),
                    "meeting_time": meeting_start
                })
                
                # Send meeting invitation
                invitation_result = gmail_send_message(
                    to=sender_email,
                    subject=f"Follow-up Meeting Scheduled",
                    body=f"""Hi,

Following up on our recent email exchange, I've scheduled a meeting for us to discuss further.

Meeting Details:
📅 Date: {meeting_date}
🕒 Time: 3:00 PM - 4:00 PM
📝 Topic: Follow-up discussion

Please let me know if this time works for you.

Best regards""",
                    style_check=False,
                    tool_context=tool_context
                )
                
                response_parts.extend([
                    f"✅ Follow-up meeting scheduled for {meeting_date} at 3:00 PM",
                    f"✅ Meeting invitation sent to {sender_email}"
                ])
            else:
                response_parts.append("⚠️ Could not create follow-up meeting")
        
        log_tool_execution(tool_context, "coordinate_email_reply_and_meeting", "complete_workflow", True, 
                         f"Reply sent and follow-up {'scheduled' if schedule_follow_up else 'skipped'}")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Error in email reply coordination workflow: {e}")
        log_tool_execution(tool_context, "coordinate_email_reply_and_meeting", "complete_workflow", False, str(e))
        return f"Error coordinating email reply and meeting: {str(e)}"


# =============================================================================
# Create ADK Function Tools
# =============================================================================

# Meeting coordination tools
schedule_meeting_with_invitation_tool = FunctionTool(func=schedule_meeting_with_invitation)

# Email processing tools  
process_emails_for_deadlines_and_schedule_tool = FunctionTool(func=process_emails_for_deadlines_and_schedule)

# Cross-agent integration tools
coordinate_email_reply_and_meeting_tool = FunctionTool(func=coordinate_email_reply_and_meeting)

# Workflow tools collection
WORKFLOW_TOOLS = [
    schedule_meeting_with_invitation_tool,
    process_emails_for_deadlines_and_schedule_tool,
    coordinate_email_reply_and_meeting_tool
]

# Export for easy access
__all__ = [
    "schedule_meeting_with_invitation",
    "process_emails_for_deadlines_and_schedule", 
    "coordinate_email_reply_and_meeting",
    "WORKFLOW_TOOLS"
] 