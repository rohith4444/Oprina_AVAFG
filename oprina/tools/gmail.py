"""
Simplified Gmail Tools for ADK - Direct Service Access

Simple ADK-compatible tools that use Gmail API directly through auth_utils.
No complex connection state management - each tool checks service availability directly.
"""

import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(3):
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk.tools import FunctionTool
from oprina.services.logging.logger import setup_logger
from google import genai

# Import simplified auth utils
from oprina.tools.auth_utils import get_gmail_service

# Import ADK utility functions
from oprina.common.utils import (
    validate_tool_context, update_agent_activity, log_tool_execution
)

# Import session state constants
from oprina.common.session_keys import (
    USER_EMAIL,
    EMAIL_CURRENT_RESULTS, EMAIL_LAST_FETCH, EMAIL_LAST_QUERY, 
    EMAIL_RESULTS_COUNT, EMAIL_LAST_SENT_TO, EMAIL_LAST_SENT,
    EMAIL_LAST_MESSAGE_VIEWED, EMAIL_LAST_MESSAGE_VIEWED_AT,
    EMAIL_LAST_SENT_SUBJECT, EMAIL_LAST_SENT_ID,
    EMAIL_LAST_REPLY_SENT, EMAIL_LAST_REPLY_TO, EMAIL_LAST_REPLY_ID, EMAIL_LAST_REPLY_THREAD,
    EMAIL_LAST_MARKED_READ, EMAIL_LAST_MARKED_READ_AT,
    EMAIL_LAST_ARCHIVED, EMAIL_LAST_ARCHIVED_AT,
    EMAIL_LAST_DELETED, EMAIL_LAST_DELETED_AT,
    # AI keys
    EMAIL_LAST_AI_SUMMARY, EMAIL_LAST_AI_SUMMARY_AT,
    EMAIL_LAST_SENTIMENT_ANALYSIS, EMAIL_LAST_SENTIMENT_ANALYSIS_AT,
    EMAIL_LAST_EXTRACTED_TASKS, EMAIL_LAST_TASK_EXTRACTION_AT,
    EMAIL_LAST_GENERATED_REPLY, EMAIL_LAST_REPLY_GENERATION_AT,
    EMAIL_PENDING_SEND, EMAIL_PENDING_REPLY,
    EMAIL_LAST_GENERATED_EMAIL, EMAIL_LAST_EMAIL_GENERATION_AT, EMAIL_LAST_GENERATED_EMAIL_TO,
    EMAIL_LAST_LISTED_MESSAGES, EMAIL_MESSAGE_INDEX_MAP,
    EMAIL_LAST_SINGLE_RESULT
)

logger = setup_logger("gmail_tools", console_output=True)

# =============================================================================
# Gmail Email Reading Tools
# =============================================================================

def gmail_list_messages(query: str = "", max_results: int = 10, tool_context=None) -> str:
    """List Gmail messages with optional search query."""
    validate_tool_context(tool_context, "gmail_list_message")
    
    try:
        # Log operation start
        log_tool_execution(tool_context, "gmail_list_messages", "list_messages", True, 
                         f"Query: '{query}', Max results: {max_results}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "listing_messages")
        
        # Get Gmail service
        service = get_gmail_service()
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        # List messages
        result = service.users().messages().list(
            userId='me', 
            q=query, 
            maxResults=max_results
        ).execute()
        
        messages = result.get('messages', [])
        
        if not messages:
            response = f"No messages found{' for query: ' + query if query else ''}"
            
            # Update session state even for empty results
            tool_context.state[EMAIL_LAST_FETCH] = datetime.utcnow().isoformat()
            tool_context.state[EMAIL_LAST_QUERY] = query
            tool_context.state[EMAIL_RESULTS_COUNT] = 0
            tool_context.state[EMAIL_CURRENT_RESULTS] = []
            tool_context.state[EMAIL_MESSAGE_INDEX_MAP] = {}
            tool_context.state[EMAIL_LAST_LISTED_MESSAGES] = []
            
            return response
        
        # Get basic info for each message
        message_summaries = []
        for msg in messages[:max_results]:
            try:
                msg_data = service.users().messages().get(
                    userId='me', 
                    id=msg['id'], 
                    format='metadata'
                ).execute()
                
                headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
                
                summary = {
                    "id": msg['id'],
                    "from": headers.get('From', 'Unknown'),
                    "subject": headers.get('Subject', 'No Subject'),
                    "date": headers.get('Date', 'Unknown')
                }
                message_summaries.append(summary)
                
            except Exception as e:
                logger.warning(f"Error getting message {msg['id']}: {e}")
                continue
        
        # Update session state with results including message ID mapping
        tool_context.state[EMAIL_LAST_FETCH] = datetime.utcnow().isoformat()
        tool_context.state[EMAIL_LAST_QUERY] = query
        tool_context.state[EMAIL_RESULTS_COUNT] = len(message_summaries)
        tool_context.state[EMAIL_CURRENT_RESULTS] = message_summaries
        
        # Store message ID mapping for easy reference by agents
        message_index_map = {}
        detailed_messages = []
        
        for i, msg in enumerate(message_summaries, 1):
            message_index_map[str(i)] = msg['id']
            # Store more complete message data including position
            detailed_msg = msg.copy()
            detailed_msg['position'] = i
            detailed_messages.append(detailed_msg)
        
        tool_context.state[EMAIL_MESSAGE_INDEX_MAP] = message_index_map
        tool_context.state[EMAIL_LAST_LISTED_MESSAGES] = detailed_messages
        
        # Store single result for confirmatory responses, clear for multiple
        if len(message_summaries) == 1:
            stored_id = message_summaries[0]['id']
            tool_context.state[EMAIL_LAST_SINGLE_RESULT] = stored_id
            logger.info(f"Stored single result ID for 'yes' responses: {stored_id}")
            logger.debug(f"Single result details - From: {message_summaries[0]['from']}, Subject: {message_summaries[0]['subject']}")
            
            # Immediately test if this message ID can be retrieved
            try:
                test_retrieval = service.users().messages().get(
                    userId='me', 
                    id=stored_id, 
                    format='minimal'
                ).execute()
                logger.info(f"Verification successful - message ID {stored_id} is accessible")
            except Exception as e:
                logger.error(f"Verification FAILED - message ID {stored_id} cannot be retrieved: {e}")
                # Store None to prevent issues later
                tool_context.state[EMAIL_LAST_SINGLE_RESULT] = None
                logger.warning(f"Cleared single result due to verification failure")
        else:
            # Clear single result if multiple results
            tool_context.state[EMAIL_LAST_SINGLE_RESULT] = None
            logger.debug(f"Cleared single result (found {len(message_summaries)} messages)")
        
        # Debug log to ensure data is stored
        logger.debug(f"Stored {len(message_index_map)} messages in index map")
        logger.debug(f"First message ID: {message_index_map.get('1', 'None')}")
        
        # Format response with clean, voice-optimized display
        if len(message_summaries) == 1:
            response_lines = ["Here is your most recent email:"]
        else:
            response_lines = [f"Here are the {min(len(message_summaries), 5)} most recent emails in your inbox:"]
        
        response_lines.append("")  # Add blank line for readability
        
        for i, msg in enumerate(message_summaries[:5], 1):  # Show first 5
            # Clean up sender name for better voice readability
            from_sender = msg['from']
            if '<' in from_sender and '>' in from_sender:
                # Extract just the name part if email is in "Name <email>" format
                name_part = from_sender.split('<')[0].strip().strip('"')
                email_part = from_sender.split('<')[1].split('>')[0]
                if name_part:
                    from_display = name_part
                else:
                    from_display = email_part
            else:
                from_display = from_sender
            
            # Truncate for voice readability
            from_display = from_display[:35] + "..." if len(from_display) > 35 else from_display
            subject_display = msg['subject'][:50] + "..." if len(msg['subject']) > 50 else msg['subject']
            
            response_lines.append(f"From: {from_display} | Subject: {subject_display}")
        
        if len(message_summaries) > 5:
            response_lines.append(f"... and {len(message_summaries) - 5} more messages")
        
        # Provide context-specific guidance based on results
        if len(message_summaries) == 1:
            response_lines.append(f"\nWould you like to read it?")
        else:
            response_lines.append(f"\nJust let me know which one you'd like to read!")
        
        log_tool_execution(tool_context, "gmail_list_messages", "list_messages", True, 
                         f"Retrieved {len(message_summaries)} messages")
        
        return "\n".join(response_lines)
        
    except Exception as e:
        logger.error(f"Error listing Gmail messages: {e}")
        log_tool_execution(tool_context, "gmail_list_messages", "list_messages", False, str(e))
        return f"Error retrieving emails: {str(e)}"


def gmail_get_message(message_id: str, tool_context=None) -> str:
    """Get detailed content of a specific Gmail message."""
    validate_tool_context(tool_context, "gmail_get_message")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_get_message", "get_message", True, f"Message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "getting_message")
        
        # Get Gmail service
        service = get_gmail_service()
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        # Use helper function to resolve message reference
        logger.info(f"GET_MESSAGE: Starting resolution for '{message_id}'")
        logger.debug(f"GET_MESSAGE: Session state available: {hasattr(tool_context, 'state') and tool_context.state is not None}")
        
        if tool_context and hasattr(tool_context, 'state'):
            single_result_id = tool_context.state.get(EMAIL_LAST_SINGLE_RESULT)
            message_index_map = tool_context.state.get(EMAIL_MESSAGE_INDEX_MAP, {})
            last_listed_messages = tool_context.state.get(EMAIL_LAST_LISTED_MESSAGES, [])
            
            logger.info(f"GET_MESSAGE: Single result ID in session: {single_result_id}")
            logger.info(f"GET_MESSAGE: Message index map has {len(message_index_map)} entries: {message_index_map}")
            logger.info(f"GET_MESSAGE: Last listed messages: {len(last_listed_messages)} entries")
            
            if last_listed_messages:
                logger.debug(f"GET_MESSAGE: First listed message: ID={last_listed_messages[0].get('id')}, From={last_listed_messages[0].get('from')}")
        
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        logger.info(f"GET_MESSAGE: Helper resolved '{message_id}' to '{actual_message_id}'")
        logger.info(f"GET_MESSAGE: About to retrieve message ID: {actual_message_id}")
        
        try:
            message = service.users().messages().get(
                userId='me', 
                id=actual_message_id, 
                format='full'
            ).execute()
        except Exception as e:
            logger.error(f"Error getting Gmail message {actual_message_id}: {e}")
            if message_id.lower() in ['yes', 'yeah', 'yep', 'sure', 'okay', 'ok', 'that one', 'it']:
                return f"I'm having trouble accessing that email right now. Let me show you your recent emails so you can pick another one to read."
            else:
                return f"I couldn't find an email matching '{message_id}'. Let me show you your recent emails so you can pick which one you'd like to read."
        
        # Extract headers
        headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}
        
        # Extract body
        body = _extract_message_body(message.get('payload', {}))
        
        # Update session state
        tool_context.state[EMAIL_LAST_MESSAGE_VIEWED] = actual_message_id
        tool_context.state[EMAIL_LAST_MESSAGE_VIEWED_AT] = datetime.utcnow().isoformat()
        
        # Clean up sender name for more natural display
        from_sender = headers.get('From', 'Unknown')
        if '<' in from_sender and '>' in from_sender:
            name_part = from_sender.split('<')[0].strip().strip('"')
            if name_part:
                from_display = name_part
            else:
                from_display = from_sender.split('<')[1].split('>')[0]
        else:
            from_display = from_sender
        
        # Make response more conversational
        subject = headers.get('Subject', 'No Subject')
        
        # Format response based on available content
        if body and len(body.strip()) > 0:
            response = f"""Here's the email from {from_display}:

Subject: {subject}

{body[:600]}{'...' if len(body) > 600 else ''}

Would you like me to reply to this, archive it, or do something else with it?"""
        else:
            response = f"""Here's the email from {from_display}:

Subject: {subject}

I was able to retrieve the email headers but had trouble accessing the full content. This sometimes happens with certain email formats.

Would you like me to try replying to this email based on the subject line?"""
        
        log_tool_execution(tool_context, "gmail_get_message", "get_message", True, "Message retrieved successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error getting Gmail message {message_id}: {e}")
        log_tool_execution(tool_context, "gmail_get_message", "get_message", False, str(e))
        return f"Error retrieving email: {str(e)}"

def gmail_search_messages(search_query: str, max_results: int = 10, tool_context=None) -> str:
    """Search Gmail messages using Gmail search syntax."""
    validate_tool_context(tool_context, "gmail_search_message")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_search_messages", "search_messages", True, f"Search: '{search_query}'")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "searching_messages")
        
        # Get Gmail service for direct search handling
        service = get_gmail_service()
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        # Perform search and get message IDs
        result = service.users().messages().list(
            userId='me', 
            q=search_query, 
            maxResults=max_results
        ).execute()
        
        messages = result.get('messages', [])
        
        if not messages:
            # Create user-friendly response instead of showing raw search query
            if 'from:' in search_query.lower():
                # Extract sender name from search query for friendlier response
                sender_part = search_query.lower().replace('from:', '').strip().strip('"')
                response = f"I couldn't find any emails from {sender_part}. You might want to check if the name is spelled correctly, or try searching for just part of the name."
            elif 'subject:' in search_query.lower():
                # Extract subject from search query for friendlier response  
                subject_part = search_query.lower().replace('subject:', '').strip().strip('"')
                response = f"I couldn't find any emails with '{subject_part}' in the subject line. Try searching for just a few key words from the subject instead."
            elif any(term in search_query.lower() for term in ['newer_than:', 'older_than:', 'after:', 'before:']):
                response = f"I couldn't find any emails matching your date criteria. You might want to try expanding the date range or checking a different time period."
            else:
                # General search
                response = f"I couldn't find any emails matching '{search_query}'. Try using different keywords, checking the sender's name, or looking for specific words from the subject line."
            
            # Clear search results in session
            tool_context.state[EMAIL_LAST_FETCH] = datetime.utcnow().isoformat()
            tool_context.state[EMAIL_LAST_QUERY] = search_query
            tool_context.state[EMAIL_RESULTS_COUNT] = 0
            tool_context.state[EMAIL_CURRENT_RESULTS] = []
            tool_context.state[EMAIL_MESSAGE_INDEX_MAP] = {}
            tool_context.state[EMAIL_LAST_LISTED_MESSAGES] = []
            
            return response
        
        # Get detailed info for search results and ensure IDs are captured
        message_summaries = []
        for msg in messages[:max_results]:
            try:
                logger.debug(f"Processing search result message with ID: {msg['id']}")
                
                # Validate the message ID before trying to get metadata
                if not msg['id'] or len(msg['id'].strip()) < 10:
                    logger.warning(f"Skipping message with invalid ID: {msg['id']}")
                    continue
                
                msg_data = service.users().messages().get(
                    userId='me', 
                    id=msg['id'], 
                    format='metadata'
                ).execute()
                
                # Verify the returned message ID matches what we requested
                returned_id = msg_data.get('id', '')
                if returned_id != msg['id']:
                    logger.warning(f"Message ID mismatch: requested {msg['id']}, got {returned_id}")
                
                headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
                
                summary = {
                    "id": msg['id'],  # Use original ID from search, not from metadata response
                    "from": headers.get('From', 'Unknown'),
                    "subject": headers.get('Subject', 'No Subject'),
                    "date": headers.get('Date', 'Unknown')
                }
                message_summaries.append(summary)
                
                logger.debug(f"Successfully processed message: ID={msg['id']}, From={summary['from']}, Subject={summary['subject']}")
                
            except Exception as e:
                logger.error(f"Error getting search result message {msg['id']}: {e}")
                # If we can't get metadata, let's still try to store the basic info
                summary = {
                    "id": msg['id'],
                    "from": "Unknown (metadata failed)",
                    "subject": "Unknown (metadata failed)",
                    "date": "Unknown"
                }
                message_summaries.append(summary)
                logger.warning(f"Stored basic info for message {msg['id']} despite metadata failure")
                continue
        
        # Store search results in session with proper ID mapping
        tool_context.state[EMAIL_LAST_FETCH] = datetime.utcnow().isoformat()
        tool_context.state[EMAIL_LAST_QUERY] = search_query
        tool_context.state[EMAIL_RESULTS_COUNT] = len(message_summaries)
        tool_context.state[EMAIL_CURRENT_RESULTS] = message_summaries
        
        # Create message ID mapping for easy reference resolution
        message_index_map = {}
        detailed_messages = []
        
        for i, msg in enumerate(message_summaries, 1):
            message_index_map[str(i)] = msg['id']  # Map position to message ID
            detailed_msg = msg.copy()
            detailed_msg['position'] = i
            detailed_messages.append(detailed_msg)
        
        tool_context.state[EMAIL_MESSAGE_INDEX_MAP] = message_index_map
        tool_context.state[EMAIL_LAST_LISTED_MESSAGES] = detailed_messages
        
        # Store single result for confirmatory responses, clear for multiple
        if len(message_summaries) == 1:
            stored_id = message_summaries[0]['id']
            tool_context.state[EMAIL_LAST_SINGLE_RESULT] = stored_id
            logger.info(f"SEARCH: Stored single result ID for 'yes' responses: {stored_id}")
            logger.debug(f"SEARCH: Single result details - From: {message_summaries[0]['from']}, Subject: {message_summaries[0]['subject']}")
        else:
            # Clear single result if multiple results
            tool_context.state[EMAIL_LAST_SINGLE_RESULT] = None
            logger.debug(f"SEARCH: Cleared single result (found {len(message_summaries)} messages)")
        
        # Debug logging to verify ID storage
        logger.debug(f"Search results stored: {len(message_index_map)} messages")
        logger.debug(f"First message ID from search: {message_index_map.get('1', 'None')}")
        
        # Format search results with voice-optimized display
        if len(message_summaries) == 1:
            # Create user-friendly response instead of showing raw search query
            if 'from:' in search_query.lower():
                # Extract sender name from search query for friendlier response
                sender_part = search_query.lower().replace('from:', '').strip().strip('"')
                response_lines = [f"I found an email from {sender_part}:"]
            elif 'subject:' in search_query.lower():
                # Extract subject from search query for friendlier response  
                subject_part = search_query.lower().replace('subject:', '').strip().strip('"')
                response_lines = [f"I found an email with '{subject_part}' in the subject:"]
            elif any(term in search_query.lower() for term in ['newer_than:', 'older_than:', 'after:', 'before:']):
                response_lines = [f"I found an email from your search:"]
            else:
                # General search
                response_lines = [f"I found an email matching your search:"]
        else:
            # Create user-friendly response for multiple results
            if 'from:' in search_query.lower():
                sender_part = search_query.lower().replace('from:', '').strip().strip('"')
                response_lines = [f"I found {len(message_summaries)} emails from {sender_part}:"]
            elif 'subject:' in search_query.lower():
                subject_part = search_query.lower().replace('subject:', '').strip().strip('"')
                response_lines = [f"I found {len(message_summaries)} emails with '{subject_part}' in the subject:"]
            elif any(term in search_query.lower() for term in ['newer_than:', 'older_than:', 'after:', 'before:']):
                response_lines = [f"I found {len(message_summaries)} emails from your search:"]
            else:
                response_lines = [f"I found {len(message_summaries)} emails matching your search:"]
        
        response_lines.append("")  # Add blank line for readability
        
        for i, msg in enumerate(message_summaries[:5], 1):  # Show first 5
            # Clean up sender name for better voice readability
            from_sender = msg['from']
            if '<' in from_sender and '>' in from_sender:
                name_part = from_sender.split('<')[0].strip().strip('"')
                email_part = from_sender.split('<')[1].split('>')[0]
                if name_part:
                    from_display = name_part
                else:
                    from_display = email_part
            else:
                from_display = from_sender
            
            # Truncate for voice readability
            from_display = from_display[:35] + "..." if len(from_display) > 35 else from_display
            subject_display = msg['subject'][:50] + "..." if len(msg['subject']) > 50 else msg['subject']
            
            response_lines.append(f"From: {from_display} | Subject: {subject_display}")
        
        if len(message_summaries) > 5:
            response_lines.append(f"... and {len(message_summaries) - 5} more messages")
        
        # Provide context-specific guidance for search results
        if len(message_summaries) == 1:
            response_lines.append(f"\nWould you like to read it?")
        else:
            response_lines.append(f"\nWhich one would you like to read?")
        
        log_tool_execution(tool_context, "gmail_search_messages", "search_messages", True, 
                         f"Found {len(message_summaries)} messages matching '{search_query}'")
        
        return "\n".join(response_lines)
        
    except Exception as e:
        logger.error(f"Error searching Gmail: {e}")
        log_tool_execution(tool_context, "gmail_search_messages", "search_messages", False, str(e))
        return f"Error searching emails: {str(e)}"


# =============================================================================
# Gmail Sending Tools
# =============================================================================

def gmail_send_message(to: str, subject: str, body: str, cc: str = "", bcc: str = "", 
                      style_check: bool = True, tool_context=None) -> str:
    """Send a Gmail message with optional style checking."""
    validate_tool_context(tool_context, "gmail_send_message")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_send_message", "send_message", True, 
                         f"To: {to}, Subject: '{subject}', CC: {cc}, BCC: {bcc}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "sending_message")
        
        # Style checking - if content seems casual and style_check is enabled
        if style_check and _is_casual_content(body, subject):
            return f"""I notice this email content seems casual:

Subject: {subject}
To: {to}
Message: {body}

Would you like me to:
1. Send it as-is 
2. Make it more professional
3. Cancel and let you revise it

Please let me know how you'd like to proceed."""
        
        # Get Gmail service
        service = get_gmail_service()
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        # Get sender email from session or profile
        sender_email = tool_context.state.get(USER_EMAIL, "")
        if not sender_email:
            try:
                profile = service.users().getProfile(userId='me').execute()
                sender_email = profile.get('emailAddress', '')
                tool_context.state[USER_EMAIL] = sender_email
            except:
                sender_email = "me"
        
        # Create message
        from email.mime.text import MIMEText
        import base64
        
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        message['from'] = sender_email
        
        if cc:
            message['cc'] = cc
        if bcc:
            message['bcc'] = bcc
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Send message
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        # Update session state after successful send
        tool_context.state[EMAIL_LAST_SENT] = datetime.utcnow().isoformat()
        tool_context.state[EMAIL_LAST_SENT_TO] = to
        tool_context.state[EMAIL_LAST_SENT_SUBJECT] = subject
        tool_context.state[EMAIL_LAST_SENT_ID] = sent_message.get('id', '')
        
        log_tool_execution(tool_context, "gmail_send_message", "send_message", True, "Email sent successfully")
        return f"Email sent successfully to {to}. Subject: {subject}"
        
    except Exception as e:
        logger.error(f"Error sending Gmail message: {e}")
        log_tool_execution(tool_context, "gmail_send_message", "send_message", False, str(e))
        return f"Error sending email: {str(e)}"


def gmail_reply_to_message(message_id: str, reply_body: str, tool_context=None) -> str:
    """Reply to a specific Gmail message."""
    validate_tool_context(tool_context, "gmail_reply_message")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_reply_to_message", "reply_message", True, 
                         f"Reply to message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "replying_to_message")
        
        # Get Gmail service
        service = get_gmail_service()
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        # Try to resolve message reference, fallback to direct ID
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            original = service.users().messages().get(
                userId='me', 
                id=actual_message_id, 
                format='full'
            ).execute()
        except Exception as e:
            if message_id.isdigit():
                return f"I couldn't find email number {message_id}. Let me check your recent emails first, then you can try replying again."
            else:
                return f"I couldn't find an email matching '{message_id}'. Let me show you your recent emails so you can pick which one to reply to."
        
        # Extract reply information
        headers = {h['name']: h['value'] for h in original.get('payload', {}).get('headers', [])}
        thread_id = original.get('threadId')
        
        from_email = headers.get('From', '')
        subject = headers.get('Subject', '')
        if not subject.lower().startswith('re:'):
            subject = 'Re: ' + subject
        
        # Create reply
        from email.mime.text import MIMEText
        import base64
        
        message = MIMEText(reply_body)
        message['to'] = from_email
        message['subject'] = subject
        message['In-Reply-To'] = headers.get('Message-ID', '')
        message['References'] = headers.get('Message-ID', '')
        
        # Send reply
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent_reply = service.users().messages().send(
            userId='me',
            body={'raw': raw_message, 'threadId': thread_id}
        ).execute()
        
        # Update session state
        tool_context.state[EMAIL_LAST_REPLY_SENT] = datetime.utcnow().isoformat()
        tool_context.state[EMAIL_LAST_REPLY_TO] = from_email
        tool_context.state[EMAIL_LAST_REPLY_ID] = sent_reply.get('id', '')
        tool_context.state[EMAIL_LAST_REPLY_THREAD] = thread_id
        
        log_tool_execution(tool_context, "gmail_reply_to_message", "reply_message", True, f"Reply sent to {from_email}")
        return f"Reply sent to {from_email}"
        
    except Exception as e:
        logger.error(f"Error replying to message {message_id}: {e}")
        log_tool_execution(tool_context, "gmail_reply_to_message", "reply_message", False, str(e))
        return f"Error sending reply: {str(e)}"

def gmail_confirm_and_send(to: str, subject: str, body: str, cc: str = "", bcc: str = "", 
                          tool_context=None) -> str:
    """Prepare email for confirmation before sending."""
    validate_tool_context(tool_context, "gmail_confirm_and_send")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_confirm_and_send", "prepare_send", True, f"To: {to}")
        
        # Store pending email in session state for agent to handle confirmation
        pending_email = {
            'to': to,
            'subject': subject, 
            'body': body,
            'cc': cc,
            'bcc': bcc,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        tool_context.state[EMAIL_PENDING_SEND] = pending_email
        
        # Format confirmation message for agent
        confirmation_text = f"""Ready to send email:
To: {to}
{f'CC: {cc}' if cc else ''}
{f'BCC: {bcc}' if bcc else ''}
Subject: {subject}

Body:
{body}

[Agent should ask user for confirmation before calling gmail_send_message]"""
        
        log_tool_execution(tool_context, "gmail_confirm_and_send", "prepare_send", True, "Email prepared for confirmation")
        return confirmation_text
        
    except Exception as e:
        logger.error(f"Error preparing email for confirmation: {e}")
        log_tool_execution(tool_context, "gmail_confirm_and_send", "prepare_send", False, str(e))
        return f"Error preparing email: {str(e)}"


def gmail_confirm_and_reply(message_id: str, reply_body: str, tool_context=None) -> str:
    """Prepare reply for confirmation before sending."""
    validate_tool_context(tool_context, "gmail_confirm_and_reply")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_confirm_and_reply", "prepare_reply", True, f"Message: {message_id}")
        
        # Get original message info for context
        service = get_gmail_service()
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        # Resolve message ID using the helper function    
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            original = service.users().messages().get(userId='me', id=actual_message_id, format='metadata').execute()
        except Exception as e:
            if message_id.isdigit():
                return f"Could not find email at position '{message_id}'. Please use 'list emails' first to see available emails, then try preparing reply to email {message_id} again."
            else:
                return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
            
        headers = {h['name']: h['value'] for h in original.get('payload', {}).get('headers', [])}
        
        # Store pending reply in session state
        pending_reply = {
            'message_id': actual_message_id,
            'reply_body': reply_body,
            'original_from': headers.get('From', 'Unknown'),
            'original_subject': headers.get('Subject', 'No Subject'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        tool_context.state[EMAIL_PENDING_REPLY] = pending_reply
        
        # Format confirmation message for agent
        confirmation_text = f"""Ready to send reply:
To: {headers.get('From', 'Unknown')}
Subject: Re: {headers.get('Subject', 'No Subject')}

Reply:
{reply_body}

[Agent should ask user for confirmation before calling gmail_reply_to_message]"""
        
        log_tool_execution(tool_context, "gmail_confirm_and_reply", "prepare_reply", True, "Reply prepared for confirmation")
        return confirmation_text
        
    except Exception as e:
        logger.error(f"Error preparing reply for confirmation: {e}")
        log_tool_execution(tool_context, "gmail_confirm_and_reply", "prepare_reply", False, str(e))
        return f"Error preparing reply: {str(e)}"

# =============================================================================
# Gmail Organization Tools
# =============================================================================

def gmail_mark_as_read(message_id: str, tool_context=None) -> str:
    """Mark a Gmail message as read."""
    validate_tool_context(tool_context, "gmail_markread_message")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_mark_as_read", "mark_read", True, f"Message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "marking_read")
        
        # Get Gmail service
        service = get_gmail_service()
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        # Try to resolve message reference, fallback to direct ID
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            service.users().messages().modify(
                userId='me',
                id=actual_message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except Exception as e:
            if message_id.isdigit():
                return f"Could not find email at position '{message_id}'. Please use 'list emails' first to see available emails, then try marking email {message_id} as read again."
            else:
                return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
        
        # Update session state
        tool_context.state[EMAIL_LAST_MARKED_READ] = actual_message_id
        tool_context.state[EMAIL_LAST_MARKED_READ_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_mark_as_read", "mark_read", True, "Message marked as read")
        return f"Message marked as read"
        
    except Exception as e:
        logger.error(f"Error marking message as read: {e}")
        log_tool_execution(tool_context, "gmail_mark_as_read", "mark_read", False, str(e))
        return f"Error marking as read: {str(e)}"


def gmail_archive_message(message_id: str, tool_context=None) -> str:
    """Archive a Gmail message."""
    validate_tool_context(tool_context, "gmail_archive_message")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_archive_message", "archive", True, f"Message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "archiving_message")
        
        # Get Gmail service
        service = get_gmail_service()
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        # Try to resolve message reference, fallback to direct ID
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            service.users().messages().modify(
                userId='me',
                id=actual_message_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
        except Exception as e:
            if message_id.isdigit():
                return f"Could not find email at position '{message_id}'. Please use 'list emails' first to see available emails, then try archiving email {message_id} again."
            else:
                return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
        
        # Update session state
        tool_context.state[EMAIL_LAST_ARCHIVED] = actual_message_id
        tool_context.state[EMAIL_LAST_ARCHIVED_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_archive_message", "archive", True, "Message archived")
        return f"Message archived successfully"
        
    except Exception as e:
        logger.error(f"Error archiving message: {e}")
        log_tool_execution(tool_context, "gmail_archive_message", "archive", False, str(e))
        return f"Error archiving message: {str(e)}"

def gmail_delete_message(message_id: str, tool_context=None) -> str:
    """Delete a Gmail message."""
    validate_tool_context(tool_context, "gmail_delete_message")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_delete_message", "delete", True, f"Message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "deleting_message")
        
        # Get Gmail service
        service = get_gmail_service()
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        # Try to resolve message reference, fallback to direct ID
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            service.users().messages().trash(
                userId='me',
                id=actual_message_id
            ).execute()
        except Exception as e:
            if message_id.isdigit():
                return f"Could not find email at position '{message_id}'. Please use 'list emails' first to see available emails, then try deleting email {message_id} again."
            else:
                return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
        
        # Update session state
        tool_context.state[EMAIL_LAST_DELETED] = actual_message_id
        tool_context.state[EMAIL_LAST_DELETED_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_delete_message", "delete", True, "Message moved to trash")
        return f"Message moved to trash"
        
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        log_tool_execution(tool_context, "gmail_delete_message", "delete", False, str(e))
        return f"Error deleting message: {str(e)}"

# =============================================================================
# AI Shared tools Functions
# =============================================================================

def _process_with_ai(content: str, task_type: str, **kwargs) -> str:
    """Shared AI processing function for all email content tasks"""
    try:
        # Initialize Gemini client
        client = genai.Client(
            vertexai=True,
            project=os.getenv('GOOGLE_CLOUD_PROJECT'),
            location=os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        )
        
        # Build prompt based on task type
        prompts = {
            "summarize": f"Summarize this email content in a clear, concise way:\n\n{content}",
            "sentiment": f"Analyze the sentiment and tone of this email. Identify if it's positive, negative, or neutral, and note the formality level:\n\n{content}",
            "tasks": f"Extract any action items, tasks, or follow-ups mentioned in this email. List them clearly:\n\n{content}",
            "reply": f"Generate a {kwargs.get('style', 'professional')} email reply to this message. Reply intent: {kwargs.get('intent', '')}\n\nOriginal email:\n{content}",
            "compose": f"Generate a {kwargs.get('style', 'professional')} email with the following requirements:\n\n{content}\n\nPlease provide both a subject line and email body. Format as:\nSubject: [subject line]\n\n[email body]"
        }
        
        # Call Gemini API
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompts.get(task_type, f"Process this email content:\n{content}")
        )
        
        return response.text
        
    except Exception as e:
        logger.error(f"AI processing failed for task {task_type}: {e}")
        return f"AI processing temporarily unavailable. Error: {str(e)}"


def gmail_generate_email(to: str, subject_intent: str, email_intent: str, 
                        style: str = "professional", context: str = "", tool_context=None) -> str:
    """Generate a complete email using AI for composition (not replies)."""
    validate_tool_context(tool_context, "gmail_generate_email")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_generate_email", "ai_compose_email", True, 
                         f"To: {to}, Intent: {email_intent}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "ai_composing_email")
        
        # Build composition requirements for AI
        composition_requirements = f"""
        Recipient: {to}
        Subject intent: {subject_intent}
        Email purpose: {email_intent}
        {f'Additional context: {context}' if context else ''}
        
        Create an appropriate email for this communication.
        """
        
        # Use AI to generate email with "compose" task type
        email_content = _process_with_ai(composition_requirements, "compose", style=style)
        
        # Update session state
        tool_context.state[EMAIL_LAST_GENERATED_EMAIL] = email_content
        tool_context.state[EMAIL_LAST_EMAIL_GENERATION_AT] = datetime.utcnow().isoformat()
        tool_context.state[EMAIL_LAST_GENERATED_EMAIL_TO] = to
        
        log_tool_execution(tool_context, "gmail_generate_email", "ai_compose_email", True, "Email composition completed")
        return email_content
        
    except Exception as e:
        logger.error(f"Error generating email: {e}")
        log_tool_execution(tool_context, "gmail_generate_email", "ai_compose_email", False, str(e))
        return f"Error generating email: {str(e)}"

def gmail_summarize_message(message_id: str, detail_level: str = "moderate", tool_context=None) -> str:
    """Summarize a specific Gmail message using AI."""
    validate_tool_context(tool_context, "gmail_summarize_message")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_summarize_message", "ai_summarize", True, f"Message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "ai_summarizing_message")
        
        # Get Gmail service
        service = get_gmail_service()
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            message = service.users().messages().get(userId='me', id=actual_message_id, format='full').execute()
        except Exception as e:
            if message_id.isdigit():
                return f"Could not find email at position '{message_id}'. Please use 'list emails' first to see available emails, then try summarizing email {message_id} again."
            else:
                return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
        
        body = _extract_message_body(message.get('payload', {}))
        
        if not body:
            return "Could not extract message content for summarization"
        
        # Use AI to summarize
        summary = _process_with_ai(body, "summarize")
        
        # Update session state using proper keys
        tool_context.state[EMAIL_LAST_AI_SUMMARY] = summary
        tool_context.state[EMAIL_LAST_AI_SUMMARY_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_summarize_message", "ai_summarize", True, "AI summary completed")
        return summary
        
    except Exception as e:
        logger.error(f"Error summarizing message {message_id}: {e}")
        log_tool_execution(tool_context, "gmail_summarize_message", "ai_summarize", False, str(e))
        return f"Error summarizing message: {str(e)}"


def gmail_analyze_sentiment(message_id: str, tool_context=None) -> str:
    """Analyze sentiment of a Gmail message using AI."""
    validate_tool_context(tool_context, "gmail_analyze_sentiment")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_analyze_sentiment", "ai_sentiment", True, f"Message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "ai_analyzing_sentiment")
        
        # Get Gmail service
        service = get_gmail_service()
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        # Try to resolve message reference, fallback to direct ID
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            message = service.users().messages().get(userId='me', id=actual_message_id, format='full').execute()
        except Exception as e:
            if message_id.isdigit():
                return f"Could not find email at position '{message_id}'. Please use 'list emails' first to see available emails, then try analyzing email {message_id} again."
            else:
                return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
        
        body = _extract_message_body(message.get('payload', {}))
        
        if not body:
            return "Could not extract message content for sentiment analysis"
        
        # Use AI to analyze sentiment
        analysis = _process_with_ai(body, "sentiment")
        
        # Update session state using proper keys
        tool_context.state[EMAIL_LAST_SENTIMENT_ANALYSIS] = analysis
        tool_context.state[EMAIL_LAST_SENTIMENT_ANALYSIS_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_analyze_sentiment", "ai_sentiment", True, "AI sentiment analysis completed")
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment for message {message_id}: {e}")
        log_tool_execution(tool_context, "gmail_analyze_sentiment", "ai_sentiment", False, str(e))
        return f"Error analyzing sentiment: {str(e)}"


def gmail_extract_action_items(message_id: str, tool_context=None) -> str:
    """Extract action items from a Gmail message using AI."""
    validate_tool_context(tool_context, "gmail_extract_action_items")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_extract_action_items", "ai_extract_tasks", True, f"Message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "ai_extracting_tasks")
        
        # Get Gmail service
        service = get_gmail_service()
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            message = service.users().messages().get(userId='me', id=actual_message_id, format='full').execute()
        except Exception as e:
            if message_id.isdigit():
                return f"Could not find email at position '{message_id}'. Please use 'list emails' first to see available emails, then try extracting action items from email {message_id} again."
            else:
                return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
        
        body = _extract_message_body(message.get('payload', {}))
        
        if not body:
            return "Could not extract message content for task extraction"
        
        # Use AI to extract tasks
        tasks = _process_with_ai(body, "tasks")
        
        # Update session state using proper keys
        tool_context.state[EMAIL_LAST_EXTRACTED_TASKS] = tasks
        tool_context.state[EMAIL_LAST_TASK_EXTRACTION_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_extract_action_items", "ai_extract_tasks", True, "AI task extraction completed")
        return tasks
        
    except Exception as e:
        logger.error(f"Error extracting tasks from message {message_id}: {e}")
        log_tool_execution(tool_context, "gmail_extract_action_items", "ai_extract_tasks", False, str(e))
        return f"Error extracting action items: {str(e)}"


def gmail_generate_reply(message_id: str, reply_intent: str, style: str = "professional", tool_context=None) -> str:
    """Generate AI reply to a Gmail message."""
    validate_tool_context(tool_context, "gmail_generate_reply")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_generate_reply", "ai_generate_reply", True, f"Message ID/Reference: {message_id}")
        
        # Update agent activity
        update_agent_activity(tool_context, "email_agent", "ai_generating_reply")
        
        # Get Gmail service
        service = get_gmail_service()
        if not service:
            return "Gmail not set up. Please run: python setup_gmail.py"
        
        actual_message_id = _get_message_id_by_reference(message_id, tool_context) or message_id
        
        try:
            message = service.users().messages().get(userId='me', id=actual_message_id, format='full').execute()
        except Exception as e:
            if message_id.isdigit():
                return f"Could not find email at position '{message_id}'. Please use 'list emails' first to see available emails, then try generating reply for email {message_id} again."
            else:
                return f"Could not find email with reference '{message_id}'. Please use 'list emails' first, then refer to emails by position (e.g., '1', '2') or sender name."
        
        body = _extract_message_body(message.get('payload', {}))
        
        if not body:
            return "Could not extract message content for reply generation"
        
        # Use AI to generate reply
        reply = _process_with_ai(body, "reply", intent=reply_intent, style=style)
        
        # Update session state using proper keys
        tool_context.state[EMAIL_LAST_GENERATED_REPLY] = reply
        tool_context.state[EMAIL_LAST_REPLY_GENERATION_AT] = datetime.utcnow().isoformat()
        
        log_tool_execution(tool_context, "gmail_generate_reply", "ai_generate_reply", True, "AI reply generation completed")
        return reply
        
    except Exception as e:
        logger.error(f"Error generating reply for message {message_id}: {e}")
        log_tool_execution(tool_context, "gmail_generate_reply", "ai_generate_reply", False, str(e))
        return f"Error generating reply: {str(e)}"
    
# =============================================================================
# Helper Functions
# =============================================================================

def _is_casual_content(body: str, subject: str) -> bool:
    """Detect if email content appears casual and might benefit from professionalization."""
    casual_indicators = [
        # Informal greetings
        'hey', 'hi there', 'sup', 'yo', 'hiya',
        # Casual phrases
        'just wanted to', 'real quick', 'btw', 'fyi', 'asap',
        # Informal closings  
        'thanks!', 'thx', 'cheers', 'later', 'talk soon',
        # Casual punctuation patterns
        '!!', '...', 'lol', 'haha',
        # Informal contractions (more than normal business use)
        "won't", "can't", "don't", "haven't", "we'll",
    ]
    
    content_lower = (body + " " + subject).lower()
    
    # Count casual indicators
    casual_count = sum(1 for indicator in casual_indicators if indicator in content_lower)
    
    # Also check for very short messages (likely casual)
    is_very_short = len(body.strip()) < 50
    
    # Consider casual if multiple indicators or very short informal message
    return casual_count >= 2 or (casual_count >= 1 and is_very_short)

def _get_message_id_by_reference(reference: str, tool_context=None) -> Optional[str]:
    """Get message ID by user reference (position, sender, subject partial match)."""
    try:
        # Log operation start
        if tool_context:
            log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True, 
                             f"Reference: '{reference}'")
        
        # Check if tool_context and state are available - but don't fail if they're not
        if not tool_context or not hasattr(tool_context, 'state'):
            logger.debug("No tool context or state available for message ID lookup - will return None for fallback")
            if tool_context:
                log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", False, 
                                 "No tool context or state available")
            return None
            
        # Get stored message data from session state (using your session key constants)
        message_index_map = tool_context.state.get(EMAIL_MESSAGE_INDEX_MAP, {})
        last_listed_messages = tool_context.state.get(EMAIL_LAST_LISTED_MESSAGES, [])
        
        # If no session data, try to build it with fresh email fetch
        if not message_index_map or not last_listed_messages:
            try:
                # Get Gmail service for fresh fetch
                service = get_gmail_service()
                if service:
                    logger.info(f"RESOLVE: No session data found, attempting fresh email fetch for reference '{reference}'")
                    recent_result = service.users().messages().list(userId='me', maxResults=10).execute()
                    recent_messages = recent_result.get('messages', [])
                    
                    # Build session index
                    message_index_map = {}
                    last_listed_messages = []
                    for i, msg in enumerate(recent_messages, 1):
                        message_index_map[str(i)] = msg['id']
                        try:
                            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
                            headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
                            detailed_msg = {
                                "id": msg['id'],
                                "from": headers.get('From', 'Unknown'),
                                "subject": headers.get('Subject', 'No Subject'),
                                "date": headers.get('Date', 'Unknown'),
                                "position": i
                            }
                            last_listed_messages.append(detailed_msg)
                        except Exception:
                            # If metadata fails, store basic info
                            detailed_msg = {
                                "id": msg['id'],
                                "from": "Unknown",
                                "subject": "Unknown", 
                                "date": "Unknown",
                                "position": i
                            }
                            last_listed_messages.append(detailed_msg)
                            continue
                    
                    # Store in session for future use
                    if tool_context and hasattr(tool_context, 'state'):
                        tool_context.state[EMAIL_MESSAGE_INDEX_MAP] = message_index_map
                        tool_context.state[EMAIL_LAST_LISTED_MESSAGES] = last_listed_messages
                        logger.info(f"RESOLVE: Built fresh index with {len(message_index_map)} messages and updated session state")
                    else:
                        logger.debug(f"RESOLVE: Built fresh index with {len(message_index_map)} messages but couldn't update session state")
                
            except Exception as e:
                logger.warning(f"RESOLVE: Failed to fetch fresh emails for reference resolution: {e}")
                # Continue with empty data - will return None
        
        # If still no data, return None
        if not message_index_map or not last_listed_messages:
            logger.debug("No message data available for reference resolution")
            if tool_context:
                log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", False,
                                 "No message data available")
            return None
        
        # Define reference_lower at the start to avoid NameError
        reference_lower = reference.lower().strip()
        
        logger.debug(f"Processing reference: '{reference}' -> normalized: '{reference_lower}'")
        logger.debug(f"Available positions in message_index_map: {list(message_index_map.keys())}")
        logger.debug(f"Number of messages in last_listed_messages: {len(last_listed_messages)}")
        
        # Special debug for position-based requests
        if any(char.isdigit() for char in reference_lower):
            logger.debug(f"Reference contains digits, checking position lookup")
        if any(word in reference_lower for word in ['fifth', 'fifth one', 'the fifth']):
            logger.debug(f"Reference contains 'fifth', should map to position '5'")
            logger.debug(f"Is position '5' in message_index_map? {'5' in message_index_map}")
            if '5' in message_index_map:
                logger.debug(f"Position '5' maps to message ID: {message_index_map['5']}")
            logger.debug(f"Does last_listed_messages have 5+ emails? {len(last_listed_messages) >= 5}")
            if len(last_listed_messages) >= 5:
                logger.debug(f"Fifth message ID from list: {last_listed_messages[4].get('id', 'None')}")
        
        # Handle confirmatory responses that refer to the most recent/first email
        confirmatory_responses = ['yes', 'yeah', 'yep', 'sure', 'okay', 'ok', 'that one', 'it', 'that email', 'this one']
        if any(phrase == reference_lower for phrase in confirmatory_responses):
            logger.debug(f"Detected confirmatory response: '{reference_lower}'")
            
            # First check if there's a specific single result stored
            single_result_id = tool_context.state.get(EMAIL_LAST_SINGLE_RESULT)
            if single_result_id:
                logger.info(f"RESOLVE: Found single result ID for confirmatory response: {single_result_id}")
                log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True,
                                 f"Resolved confirmatory '{reference}' to single result ID {single_result_id}")
                return single_result_id
            else:
                logger.warning(f"RESOLVE: No single result ID found in session state for confirmatory response '{reference_lower}'")
            
            # Fallback to first message in the list
            if last_listed_messages and len(last_listed_messages) > 0:
                resolved_id = last_listed_messages[0].get('id')
                logger.debug(f"RESOLVE: Found message ID by confirmatory response '{reference}' from messages list: {resolved_id}")
                log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True,
                                 f"Resolved confirmatory '{reference}' to first message ID {resolved_id}")
                return resolved_id
            # If no stored messages, try to use position 1 from index map
            elif message_index_map and '1' in message_index_map:
                resolved_id = message_index_map['1']
                logger.debug(f"RESOLVE: Found message ID by confirmatory response '{reference}' from index: {resolved_id}")
                log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True,
                                 f"Resolved confirmatory '{reference}' to position 1 ID {resolved_id}")
                return resolved_id
            else:
                logger.debug(f"RESOLVE: Confirmatory response '{reference_lower}' detected but no messages available")
        
        # Handle natural language expressions for "first", "first one", etc.
        first_indicators = ['most recent', 'latest', 'newest', 'first', 'first one', 'top', 'first email', '1st', 'number 1', 'the first', 'the first one', 'the first email']
        if any(phrase in reference_lower for phrase in first_indicators):
            # Return the first message in the list (most recent)
            if last_listed_messages and len(last_listed_messages) > 0:
                resolved_id = last_listed_messages[0].get('id')
                logger.debug(f"Found message ID by natural language request '{reference}': {resolved_id}")
                log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True,
                                 f"Resolved '{reference}' to first message ID {resolved_id}")
                return resolved_id
            # If no stored messages, try to use position 1 from index map
            elif message_index_map and '1' in message_index_map:
                resolved_id = message_index_map['1']
                logger.debug(f"Found message ID by natural language request '{reference}' from index: {resolved_id}")
                log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True,
                                 f"Resolved '{reference}' to position 1 ID {resolved_id}")
                return resolved_id
        
        # Handle second, third, etc.
        number_words = {
            'second': '2', 'third': '3', 'fourth': '4', 'fifth': '5', 'sixth': '6', 'seventh': '7', 'eighth': '8', 'ninth': '9', 'tenth': '10',
            '2nd': '2', '3rd': '3', '4th': '4', '5th': '5', '6th': '6', '7th': '7', '8th': '8', '9th': '9', '10th': '10',
            'second email': '2', 'third email': '3', 'fourth email': '4', 'fifth email': '5', 'sixth email': '6',
            'second one': '2', 'third one': '3', 'fourth one': '4', 'fifth one': '5', 'sixth one': '6',
            'the second': '2', 'the third': '3', 'the fourth': '4', 'the fifth': '5', 'the sixth': '6',
            'the second one': '2', 'the third one': '3', 'the fourth one': '4', 'the fifth one': '5', 'the sixth one': '6'
        }
        for word, position in number_words.items():
            if word in reference_lower:
                if position in message_index_map:
                    resolved_id = message_index_map[position]
                    logger.debug(f"Found message ID by number word '{word}': {resolved_id}")
                    log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True,
                                     f"Resolved '{reference}' to position {position} ID {resolved_id}")
                    return resolved_id
                else:
                    # Fallback: try to get from last_listed_messages array directly
                    position_int = int(position)
                    if last_listed_messages and len(last_listed_messages) >= position_int and position_int > 0:
                        resolved_id = last_listed_messages[position_int - 1].get('id')  # Convert to 0-based index
                        logger.debug(f"Found message ID by number word '{word}' from messages list: {resolved_id}")
                        log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True,
                                         f"Resolved '{reference}' to position {position} ID {resolved_id} via messages list")
                        return resolved_id
                    else:
                        logger.debug(f"Number word '{word}' mapped to position {position} but no email at that position in messages list")
                        break  # Found the pattern but no email at that position
        
        # Try to parse as position number (1, 2, 3, etc.)
        try:
            position = int(reference)
            if str(position) in message_index_map:
                resolved_id = message_index_map[str(position)]
                logger.debug(f"Found message ID by position {position}: {resolved_id}")
                log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True,
                                 f"Resolved position {position} to ID {resolved_id}")
                return resolved_id
            else:
                # Fallback: try to get from last_listed_messages array directly
                if last_listed_messages and len(last_listed_messages) >= position and position > 0:
                    resolved_id = last_listed_messages[position - 1].get('id')  # Convert to 0-based index
                    logger.debug(f"Found message ID by position {position} from messages list: {resolved_id}")
                    log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True,
                                     f"Resolved position {position} to ID {resolved_id} via messages list")
                    return resolved_id
                else:
                    logger.debug(f"Position {position} not found in index map and not enough messages in list")
        except ValueError:
            pass  # Not a number, continue with other methods
        
        # Try to match by sender (partial match, case insensitive)
        for msg in last_listed_messages:
            sender = msg.get('from', '').lower()
            if reference_lower in sender:
                resolved_id = msg.get('id')
                logger.debug(f"Found message ID by sender match: {reference} -> {resolved_id}")
                log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True,
                                 f"Resolved sender '{reference}' to ID {resolved_id}")
                return resolved_id
        
        # Try to match by subject (smart partial matching, case insensitive)
        for msg in last_listed_messages:
            subject = msg.get('subject', '').lower()
            
            # Smart subject matching - handle common user expressions
            if any(keyword in reference_lower for keyword in ['welcome', 'oprina']) and any(keyword in subject for keyword in ['welcome', 'oprina']):
                resolved_id = msg.get('id')
                logger.debug(f"Found message ID by smart subject match: {reference} -> {resolved_id}")
                log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True,
                                 f"Resolved subject '{reference}' to ID {resolved_id}")
                return resolved_id
            
            # Standard partial matching
            elif reference_lower in subject:
                resolved_id = msg.get('id')
                logger.debug(f"Found message ID by subject match: {reference} -> {resolved_id}")
                log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", True,
                                 f"Resolved subject '{reference}' to ID {resolved_id}")
                return resolved_id
        
        # No match found
        logger.debug(f"Could not resolve message reference: {reference} - returning None for fallback")
        if tool_context:
            log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", False,
                             f"Could not resolve reference: {reference}")
        return None
        
    except Exception as e:
        logger.error(f"Error resolving message reference '{reference}': {e}")
        if tool_context:
            log_tool_execution(tool_context, "_get_message_id_by_reference", "resolve_reference", False, str(e))
        return None

def gmail_parse_subject_and_body(ai_generated_content: str, tool_context=None) -> str:
    """Parse AI-generated email content into subject and body components and return formatted result."""
    validate_tool_context(tool_context, "gmail_parse_email_content")
    
    try:
        # Log operation
        log_tool_execution(tool_context, "gmail_parse_subject_and_body", "parse_content", True, "Parsing AI content")
        
        lines = ai_generated_content.strip().split('\n')
        subject = ""
        body = ""
        
        # Look for subject line
        for i, line in enumerate(lines):
            if line.lower().startswith('subject:'):
                subject = line[8:].strip()  # Remove "Subject:" prefix
                # Body starts after subject line (skip empty lines)
                for j in range(i + 1, len(lines)):
                    if lines[j].strip():  # First non-empty line after subject
                        body = '\n'.join(lines[j:]).strip()
                        break
                break
        
        # Fallback if no "Subject:" found - treat first line as subject
        if not subject and lines:
            subject = lines[0].strip()
            if len(lines) > 1:
                body = '\n'.join(lines[1:]).strip()
        
        # Clean up subject and body
        subject = subject.strip('"\'')  # Remove quotes if present
        
        # Return parsed content as formatted string instead of tuple
        parsed_result = f"PARSED_SUBJECT: {subject}\nPARSED_BODY: {body}"
        
        log_tool_execution(tool_context, "gmail_parse_subject_and_body", "parse_content", True, 
                         f"Parsed - Subject: '{subject[:50]}...', Body length: {len(body)}")
        
        return parsed_result
        
    except Exception as e:
        logger.error(f"Error parsing AI content: {e}")
        log_tool_execution(tool_context, "gmail_parse_subject_and_body", "parse_content", False, str(e))
        return f"PARSED_SUBJECT: Email Subject\nPARSED_BODY: {ai_generated_content}"  # Fallback


def _extract_message_body(payload: Dict[str, Any]) -> str:
    """Extract text body from Gmail message payload."""
    try:
        # Handle multipart messages
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':  # Added .get() for safety
                    data = part.get('body', {}).get('data', '')
                    if data:
                        import base64
                        return base64.urlsafe_b64decode(data).decode('utf-8')
        
        # Handle single part messages
        elif payload.get('mimeType') == 'text/plain':  # Added .get() for safety
            data = payload.get('body', {}).get('data', '')
            if data:
                import base64
                return base64.urlsafe_b64decode(data).decode('utf-8')
        
        return "Unable to extract message content"
        
    except Exception as e:
        logger.warning(f"Error extracting message body: {e}")
        return "Error reading message content"


# =============================================================================
# Create ADK Function Tools
# =============================================================================

# Reading tools
gmail_list_messages_tool = FunctionTool(func=gmail_list_messages)
gmail_get_message_tool = FunctionTool(func=gmail_get_message)
gmail_search_messages_tool = FunctionTool(func=gmail_search_messages)

# Sending tools
gmail_send_message_tool = FunctionTool(func=gmail_send_message)
gmail_reply_to_message_tool = FunctionTool(func=gmail_reply_to_message)

# Organization tools
gmail_mark_as_read_tool = FunctionTool(func=gmail_mark_as_read)
gmail_archive_message_tool = FunctionTool(func=gmail_archive_message)
gmail_delete_message_tool = FunctionTool(func=gmail_delete_message)

# AI-powered content tools
gmail_summarize_message_tool = FunctionTool(func=gmail_summarize_message)
gmail_analyze_sentiment_tool = FunctionTool(func=gmail_analyze_sentiment)
gmail_extract_action_items_tool = FunctionTool(func=gmail_extract_action_items)
gmail_generate_reply_tool = FunctionTool(func=gmail_generate_reply)

# NEW AI composition and workflow tools
gmail_generate_email_tool = FunctionTool(func=gmail_generate_email)
gmail_parse_subject_and_body_tool = FunctionTool(func=gmail_parse_subject_and_body)
gmail_confirm_and_send_tool = FunctionTool(func=gmail_confirm_and_send)
gmail_confirm_and_reply_tool = FunctionTool(func=gmail_confirm_and_reply)

# Gmail tools collection
GMAIL_TOOLS = [
    # Reading tools
    gmail_list_messages_tool,
    gmail_get_message_tool,
    gmail_search_messages_tool,
    
    # Sending tools
    gmail_send_message_tool,
    gmail_reply_to_message_tool,
    
    # Organization tools
    gmail_mark_as_read_tool,
    gmail_archive_message_tool,
    gmail_delete_message_tool,
    
    # AI-powered content tools
    gmail_summarize_message_tool,
    gmail_analyze_sentiment_tool,
    gmail_extract_action_items_tool,
    gmail_generate_reply_tool,
    
    # NEW AI composition and workflow tools
    gmail_generate_email_tool,
    gmail_parse_subject_and_body_tool,
    gmail_confirm_and_send_tool,
    gmail_confirm_and_reply_tool
]

# Export for easy access
__all__ = [
    # Reading functions
    "gmail_list_messages",
    "gmail_get_message",
    "gmail_search_messages",
    
    # Sending functions
    "gmail_send_message",
    "gmail_reply_to_message",
    
    # Organization functions
    "gmail_mark_as_read",
    "gmail_archive_message",
    "gmail_delete_message",
    
    # AI content processing functions
    "gmail_summarize_message",
    "gmail_analyze_sentiment", 
    "gmail_extract_action_items",
    "gmail_generate_reply",
    
    # NEW AI composition and workflow functions
    "gmail_generate_email",
    "gmail_parse_subject_and_body",
    "gmail_confirm_and_send",
    "gmail_confirm_and_reply",
    
    # Tools collection
    "GMAIL_TOOLS"
]