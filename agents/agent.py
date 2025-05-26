import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv
from mcp import mcp_discovery
from google.oauth2.credentials import Credentials

# Load environment variables from .env file
load_dotenv()

def is_authenticated():
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email',
        'openid'
    ]
    token_file = 'token.json'
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            if creds and creds.valid:
                return True
        except Exception:
            pass
    return False

class LlmAgent:
    def __init__(self, name, model):
        self.name = name
        self.model = model
        self.conversation_history = []
        self.tools = mcp_discovery.list_tools()
        
        # Configure the Gemini API
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel(model_name=model)
        
        # Best-practice system prompt for Gmail assistant
        self.system_prompt = f"""
You are Oprina, the Gmail management assistant chatbot.

Your identity:
- You are a helpful, friendly, and privacy-respecting AI assistant named Oprina.
- You help users manage their Gmail inbox efficiently and securely.
- You are not a human, but an AI developed to assist with Gmail tasks.

Your introduction:
- When a user interacts with you for the first time, always introduce yourself as Oprina, the Gmail Chatbot.
- Briefly explain your main capabilities (listing, searching, reading, sending emails, etc.).
- If the user asks "what can you do" or similar, provide a concise summary of your features.

Your task is to help users manage their Gmail inbox efficiently. You have access to Gmail tools including:
- Listing emails (by sender, subject, date, labels)
- Fetching full email details
- Searching emails with complex filters (e.g., from:John, newer_than:7d)
- Reading email threads
- Downloading attachments
- Sending and drafting emails (if authorized)

When responding:
✅ Always explain actions clearly.
✅ Provide context where needed (e.g., number of emails found, sender details).
✅ Warn users if an operation might fail or exceed limits (e.g., rate limits, missing tokens).
✅ Keep explanations concise, actionable, and user-friendly.
✅ Respect Gmail's security and privacy protocols.

If you encounter errors (e.g., authentication failure, token expiry):
🔒 Prompt the user to reauthorize using OAuth.
🔒 Do not attempt unauthorized actions.
🔒 Notify the user immediately with a clear message.

Remember:
- Your goal is to streamline Gmail management.
- Focus on accuracy, clarity, and efficiency.
- Avoid long-winded or irrelevant details.

When you see a 'Tool result' section, it contains real data from the user's Gmail account. Always use this data as the source of truth to answer the user's question directly. Do not say you lack access to Gmail or need simulated data. If the tool result is empty or no emails are found, politely inform the user.

Let's deliver an exceptional Gmail assistant experience!
"""

    async def run(self, user_input):
        self.conversation_history.append({"role": "user", "content": user_input})
        if not is_authenticated():
            response_text = (
                "I need to access your Gmail account to help you. "
                "Please make sure you have a valid token.json file in your project root. "
                "If you don't have one, you'll need to authenticate with Gmail first."
            )
            self.conversation_history.append({"role": "assistant", "content": response_text})
            return {
                "response": response_text,
                "tools_used": None,
                "tool_result": None
            }
        user_lower = user_input.lower().strip()
        tool_to_use = None
        tool_args = {}
        search_query = None
        # Special: What can you do?
        if any(kw in user_lower for kw in ["what can you do", "help", "abilities", "features"]):
            response_text = (
                "I can help you manage your Gmail inbox. Here's what I can do:\n\n"
                "- **List your emails:** Show a summary of your emails, optionally filtered by sender, subject, or date.\n"
                "- **Get a specific email:** Retrieve a single email given its ID.\n"
                "- **Search for emails:** Find emails matching specific keywords or criteria.\n"
                "- **Get an email thread:** Retrieve all emails in a conversation.\n"
                "- **Get email attachments:** Download an attachment from a specific email.\n\n"
                "Just tell me what you'd like to do! For example:\n"
                "- `List my emails from John`\n"
                "- `Get email with ID 12345`\n"
                "- `Search for emails about vacation`\n"
                "- `Get the thread for email ID 67890`"
            )
            self.conversation_history.append({"role": "assistant", "content": response_text})
            return {
                "response": response_text,
                "tools_used": None,
                "tool_result": None
            }
        # Special: What is my email?
        if "what is my email" in user_lower or "my email address" in user_lower:
            # Fetch the user's own email address using the tool
            profile = mcp_discovery.run_tool("gmail_get_user_profile")
            email_addr = profile.get("emailAddress", "(unknown)")
            response_text = f"Your authenticated Gmail address is: {email_addr}"
            self.conversation_history.append({"role": "assistant", "content": response_text})
            return {
                "response": response_text,
                "tools_used": "gmail_get_user_profile",
                "tool_result": profile
            }
        # Special: Send email flow
        if any(kw in user_lower for kw in ["send an email", "send email", "compose email", "email to"]):
            # Improved extraction for recipient, subject, and body
            to_match = re.search(r"to ([\w.\-+]+@[\w.\-]+)", user_input, re.IGNORECASE)
            subject_match = re.search(r"subject (?:is |:|=)?([\w .@\-\"']+)", user_input, re.IGNORECASE)
            body_match = re.search(r"message (?:is |:|=)?([\w .@\-\"']+)", user_input, re.IGNORECASE)
            # Fallback: try to extract subject/body from phrasing like 'with subject ... and message ...'
            if not subject_match:
                subject_match = re.search(r"with subject ([^,]+)", user_input, re.IGNORECASE)
            if not body_match:
                body_match = re.search(r"message (?:is |:|=)?(.+)$", user_input, re.IGNORECASE)
            to = to_match.group(1) if to_match else None
            subject = subject_match.group(1).strip(' "') if subject_match else None
            body = body_match.group(1).strip(' "') if body_match else None
            # Prompt for missing fields
            missing = []
            if not to:
                missing.append("recipient email address")
            if not subject:
                missing.append("subject")
            if not body:
                missing.append("message body")
            if missing:
                prompt = (
                    f"To send an email, I need the following missing information: {', '.join(missing)}. "
                    f"Please provide the complete command, e.g., 'Send an email to someone@example.com with subject Hello and message How are you?'"
                )
                self.conversation_history.append({"role": "assistant", "content": prompt})
                return {
                    "response": prompt,
                    "tools_used": None,
                    "tool_result": None
                }
            # Fetch the user's own email address for confirmation
            profile = mcp_discovery.run_tool("gmail_get_user_profile")
            sender_email = profile.get("emailAddress", "(unknown)")
            # Ask for confirmation before sending
            confirm_msg = (
                f"You are about to send an email from **{sender_email}** to **{to}** with subject "
                f"'{subject}' and message '{body}'.\n\nType 'confirm send' to proceed or 'cancel' to abort."
            )
            self.conversation_history.append({"role": "assistant", "content": confirm_msg})
            # Store pending send info in the agent's state
            self.pending_send = {"to": to, "subject": subject, "body": body}
            return {
                "response": confirm_msg,
                "tools_used": "gmail_get_user_profile",
                "tool_result": profile
            }
        # Handle confirmation for sending email
        if hasattr(self, "pending_send") and user_lower.strip() == "confirm send":
            send_info = self.pending_send
            # Double-check all fields are present
            if not send_info.get("to") or not send_info.get("subject") or not send_info.get("body"):
                response_text = "Cannot send email: missing recipient, subject, or message body. Please start over."
                del self.pending_send
                self.conversation_history.append({"role": "assistant", "content": response_text})
                return {
                    "response": response_text,
                    "tools_used": None,
                    "tool_result": None
                }
            try:
                result = mcp_discovery.run_tool(
                    "gmail_send_message",
                    to=send_info["to"],
                    subject=send_info["subject"],
                    body=send_info["body"]
                )
                response_text = f"Email sent successfully to {send_info['to']}!"
            except Exception as e:
                response_text = f"Failed to send email: {e}"
            del self.pending_send
            self.conversation_history.append({"role": "assistant", "content": response_text})
            return {
                "response": response_text,
                "tools_used": "gmail_send_message",
                "tool_result": result if 'result' in locals() else None
            }
        if hasattr(self, "pending_send") and user_lower.strip() == "cancel":
            del self.pending_send
            response_text = "Email sending cancelled."
            self.conversation_history.append({"role": "assistant", "content": response_text})
            return {
                "response": response_text,
                "tools_used": None,
                "tool_result": None
            }
        # Improved intent detection for search queries
        from_match = re.search(r'(?:from|sent by|sender is) ([\w .<>@\-\"]+)', user_input, re.IGNORECASE)
        if from_match:
            sender = from_match.group(1).strip(' "')
            search_query = f'from:"{sender}"'
        subject_match = re.search(r'subject (?:is |equals |:)?([\w .@\-\"]+)', user_input, re.IGNORECASE)
        if subject_match:
            subject = subject_match.group(1).strip(' "')
            search_query = f'subject:"{subject}"'
        if not search_query:
            search_patterns = [
                r"search for (?:an )?email(?: called| named| titled)? ['\"]?([^'\"]+)['\"]?",
                r"find (?:an )?email(?: called| named| titled)? ['\"]?([^'\"]+)['\"]?",
                r"email (?:called|named|titled) ['\"]?([^'\"]+)['\"]?",
                r"subject:? ['\"]?([^'\"]+)['\"]?",
            ]
            for pattern in search_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    search_query = match.group(1).strip()
                    break
        if not search_query and (
            'search' in user_lower or 'find' in user_lower or 'subject' in user_lower or 'title' in user_lower
        ):
            cleaned = re.sub(r'(search for|find|subject|title|email|called|named|titled|the|an|a|of|with|about|on|in|to|for|by|from|please|show|me|\s+)', ' ', user_lower, flags=re.IGNORECASE).strip()
            if cleaned:
                search_query = cleaned
        if not search_query and len(self.conversation_history) > 1:
            prev = self.conversation_history[-2]["content"].lower()
            if any(word in prev for word in ["search", "find", "subject", "title"]):
                search_query = user_input.strip()
        
        # Map to new tool names
        if search_query:
            tool_to_use = "gmail_search"
            tool_args["query"] = search_query
        # Fix: Better detection for listing emails
        elif "list" in user_lower or "show" in user_lower or "display" in user_lower:
            tool_to_use = "gmail_list_messages"
            if "unread" in user_lower:
                tool_args["query"] = "is:unread"
            elif "from" in user_lower:
                # Extract sender if present
                from_match = re.search(r'from ([\w .<>@\-\"]+)', user_input, re.IGNORECASE)
                if from_match:
                    sender = from_match.group(1).strip(' "')
                    tool_args["query"] = f'from:"{sender}"'
        elif "get" in user_lower and "email" in user_lower:
            # Check if there's an ID in the request
            id_match = re.search(r'id (\w+)', user_input, re.IGNORECASE)
            if id_match:
                msg_id = id_match.group(1)
                tool_to_use = "gmail_get_message"
                tool_args["msg_id"] = msg_id
            else:
                tool_to_use = "gmail_list_messages"
        
        # If no specific intent was detected but the user mentioned emails, default to listing
        if not tool_to_use and ("email" in user_lower or "inbox" in user_lower or "mail" in user_lower):
            tool_to_use = "gmail_list_messages"
            
        tool_result = None
        if tool_to_use:
            try:
                tool_result = mcp_discovery.run_tool(tool_to_use, **tool_args)
            except Exception as e:
                tool_result = f"Error running tool '{tool_to_use}': {e}"
        # Format list_emails and search_emails results
        if tool_to_use in ["gmail_list_messages", "gmail_search"]:
            if isinstance(tool_result, str):
                # tool_result is an error string
                tool_result = f"There was an error processing your request: {tool_result}"
            elif tool_result and "messages" in tool_result:
                messages = tool_result["messages"]
                if not messages:
                    tool_result = (
                        "I couldn't find any emails matching your request. "
                        "Try a different search term or check your inbox."
                    )
                else:
                    summary_lines = []
                    for msg in messages[:5]:
                        email = mcp_discovery.run_tool("gmail_get_message", msg_id=msg["id"])
                        headers = {h["name"]: h["value"] for h in email.get("payload", {}).get("headers", [])}
                        subject = headers.get("Subject", "(No Subject)")
                        sender = headers.get("From", "(Unknown Sender)")
                        date = headers.get("Date", "(Unknown Date)")
                        summary_lines.append(f"- **Subject:** {subject}\n  **From:** {sender}\n  **Date:** {date}\n  **ID:** `{msg['id']}`")
                    more = f"\n...and {len(messages)-5} more." if len(messages) > 5 else ""
                    tool_result = (
                        f"Here are the top {min(5, len(messages))} email(s):\n\n" + "\n\n".join(summary_lines) + more
                    )
        elif not tool_to_use:
            tool_result = (
                "I'm here to help you manage your Gmail. "
                "You can ask me to list, search, or get details about your emails. "
                "Try something like: `List my emails`, `Search for emails from John`, or `Get email with ID 12345`."
            )
        prompt = f"{self.system_prompt}\n\n"
        for message in self.conversation_history:
            prompt += f"{message['role']}: {message['content']}\n"
        if tool_result:
            prompt += f"\nTool result: {tool_result}\n"
        prompt += "\nassistant: "
        response = self.gemini_model.generate_content(prompt)
        self.conversation_history.append({"role": "assistant", "content": response.text})
        return {
            "response": response.text,
            "tools_used": tool_to_use if tool_to_use else None,
            "tool_result": tool_result if tool_result else None
        }

async def run_agent(user_input: str):
    agent = LlmAgent(
        name="gmail_agent",
        model="gemini-1.5-flash"
    )
    return await agent.run(user_input)