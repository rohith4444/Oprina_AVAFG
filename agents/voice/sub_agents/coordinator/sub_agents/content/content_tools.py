"""
Direct Content Tools for ADK - Replaces Complex Content Processing

Simple ADK-compatible tools for content processing operations.
No MCP bridge complexity - just direct function tools following Gmail/Calendar pattern.
"""

import os
import sys
import re
import html
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
current_file = os.path.abspath(__file__)
project_root = current_file
for _ in range(7):
    project_root = os.path.dirname(project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from google.adk.tools import FunctionTool
from agents.voice.sub_agents.common import (
    USER_PREFERENCES, USER_EMAIL, USER_NAME
)
from services.logging.logger import setup_logger

logger = setup_logger("content_tools", console_output=True)


# =============================================================================
# Email Content Summarization Tools
# =============================================================================

def summarize_email_content(
    content: str, 
    detail_level: str = "moderate", 
    tool_context=None
) -> str:
    """Summarize email content with specified detail level."""
    try:
        if not content or not content.strip():
            return "No content provided to summarize"
        
        # Get user preferences from session
        user_prefs = tool_context.session.state.get(USER_PREFERENCES, {}) if tool_context else {}
        preferred_detail = user_prefs.get("summary_detail", detail_level)
        
        # Clean the email content
        content_clean = _clean_email_content(content)
        
        if not content_clean or len(content_clean) < 10:
            return "Email content is too short to summarize effectively"
        
        # Generate summary based on detail level
        if preferred_detail == "brief":
            # Brief: Key points only (50-100 chars)
            summary = _extract_key_points(content_clean, max_length=100)
            return f"Brief summary: {summary}"
            
        elif preferred_detail == "detailed":
            # Detailed: Comprehensive summary (200-400 chars)
            summary = _extract_detailed_summary(content_clean, max_length=400)
            return f"Detailed summary: {summary}"
            
        else:
            # Moderate: Balanced summary (100-250 chars)
            summary = _extract_moderate_summary(content_clean, max_length=250)
            return f"Summary: {summary}"
            
    except Exception as e:
        logger.error(f"Error summarizing email content: {e}")
        return f"Error creating summary: {str(e)}"


def summarize_email_list(
    emails: str, 
    max_emails: int = 5,
    tool_context=None
) -> str:
    """Summarize a list of emails for quick overview."""
    try:
        if not emails or not emails.strip():
            return "No emails provided to summarize"
        
        # Parse email list (assuming simple format)
        email_lines = emails.split('\n')
        email_summaries = []
        
        count = 0
        for line in email_lines:
            if line.strip() and count < max_emails:
                # Extract sender and subject if formatted properly
                if 'From:' in line or 'Subject:' in line:
                    email_summaries.append(line.strip())
                    count += 1
        
        if not email_summaries:
            return "No valid email format found to summarize"
        
        result = f"Email overview ({len(email_summaries)} emails):\n"
        for i, summary in enumerate(email_summaries, 1):
            result += f"{i}. {summary[:60]}...\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error summarizing email list: {e}")
        return f"Error summarizing emails: {str(e)}"


# =============================================================================
# Email Reply Generation Tools
# =============================================================================

def generate_email_reply(
    original_email: str,
    reply_intent: str,
    style: str = "professional",
    tool_context=None
) -> str:
    """Generate email reply based on original email and user intent."""
    try:
        if not reply_intent or not reply_intent.strip():
            return "Please provide what you want to communicate in the reply"
        
        # Get user info from session
        user_prefs = tool_context.session.state.get(USER_PREFERENCES, {}) if tool_context else {}
        user_name = tool_context.session.state.get(USER_NAME, "") if tool_context else ""
        
        preferred_style = user_prefs.get("reply_style", style)
        
        # Extract sender info from original email
        sender_info = _extract_sender_info(original_email)
        
        # Generate reply based on style
        if preferred_style == "brief":
            reply = f"{reply_intent.strip()}"
            if user_name:
                reply += f"\n\n{user_name}"
                
        elif preferred_style == "formal":
            greeting = f"Dear {sender_info}," if sender_info else "Dear Sir/Madam,"
            reply = f"{greeting}\n\n{reply_intent.strip()}\n\n"
            if user_name:
                reply += f"Best regards,\n{user_name}"
            else:
                reply += "Best regards"
                
        elif preferred_style == "friendly":
            greeting = f"Hi {sender_info}!" if sender_info else "Hi!"
            reply = f"{greeting}\n\n{reply_intent.strip()}\n\n"
            if user_name:
                reply += f"Thanks,\n{user_name}"
            else:
                reply += "Thanks!"
                
        else:  # professional (default)
            greeting = f"Hello {sender_info}," if sender_info else "Hello,"
            reply = f"{greeting}\n\n{reply_intent.strip()}\n\n"
            if user_name:
                reply += f"Best regards,\n{user_name}"
            else:
                reply += "Best regards"
        
        return reply
        
    except Exception as e:
        logger.error(f"Error generating email reply: {e}")
        return f"Error generating reply: {str(e)}"


def suggest_reply_templates(
    email_content: str,
    tool_context=None
) -> str:
    """Suggest appropriate reply templates based on email content."""
    try:
        if not email_content:
            return "No email content provided for template suggestions"
        
        content_lower = email_content.lower()
        suggestions = []
        
        # Meeting-related emails
        if any(word in content_lower for word in ["meeting", "schedule", "appointment", "calendar"]):
            suggestions.append("Meeting response: 'I'm available [time] or [alternative time]. Please let me know what works best.'")
        
        # Information requests
        if any(word in content_lower for word in ["information", "details", "clarification", "question"]):
            suggestions.append("Info response: 'Here's the information you requested: [details]. Let me know if you need anything else.'")
        
        # Thank you emails
        if any(word in content_lower for word in ["thank", "thanks", "appreciate", "grateful"]):
            suggestions.append("Acknowledgment: 'You're welcome! Happy to help. Please don't hesitate to reach out if you need anything else.'")
        
        # Urgent requests
        if any(word in content_lower for word in ["urgent", "asap", "immediately", "deadline"]):
            suggestions.append("Urgent response: 'I understand this is urgent. I'll [action] and get back to you by [time].'")
        
        # Default suggestions
        if not suggestions:
            suggestions = [
                "Acknowledgment: 'Thank you for your email. I'll review this and get back to you shortly.'",
                "Confirmation: 'I can confirm [specific point]. Please let me know if you need any additional information.'",
                "Follow-up: 'I'll take care of this and follow up with you by [date/time].'"
            ]
        
        result = "Suggested reply templates:\n"
        for i, suggestion in enumerate(suggestions, 1):
            result += f"{i}. {suggestion}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error suggesting reply templates: {e}")
        return f"Error generating suggestions: {str(e)}"


# =============================================================================
# Content Analysis Tools
# =============================================================================

def analyze_email_sentiment(content: str, tool_context=None) -> str:
    """Analyze email sentiment and tone."""
    try:
        if not content or not content.strip():
            return "No content provided for sentiment analysis"
        
        content_clean = _clean_email_content(content)
        content_lower = content_clean.lower()
        
        # Analyze different sentiment indicators
        analysis_parts = []
        
        # Urgency detection
        urgent_words = ["urgent", "asap", "immediately", "emergency", "critical", "deadline"]
        if any(word in content_lower for word in urgent_words):
            analysis_parts.append("⚡ Urgent tone detected")
        
        # Positive sentiment
        positive_words = ["thank", "great", "excellent", "pleased", "happy", "congratulations", "wonderful"]
        positive_count = sum(1 for word in positive_words if word in content_lower)
        
        # Negative sentiment
        negative_words = ["problem", "issue", "concern", "complaint", "error", "failed", "wrong", "disappointed"]
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        # Determine overall sentiment
        if positive_count > negative_count:
            analysis_parts.append("😊 Positive sentiment")
        elif negative_count > positive_count:
            analysis_parts.append("😟 Concerned/negative sentiment")
        else:
            analysis_parts.append("😐 Neutral sentiment")
        
        # Formality level
        formal_indicators = ["dear", "sincerely", "regards", "respectfully", "kindly"]
        casual_indicators = ["hi", "hey", "thanks", "cheers", "talk soon"]
        
        formal_count = sum(1 for word in formal_indicators if word in content_lower)
        casual_count = sum(1 for word in casual_indicators if word in content_lower)
        
        if formal_count > casual_count:
            analysis_parts.append("🎩 Formal tone")
        elif casual_count > formal_count:
            analysis_parts.append("👋 Casual tone")
        else:
            analysis_parts.append("💼 Professional tone")
        
        return " | ".join(analysis_parts)
        
    except Exception as e:
        logger.error(f"Error analyzing email sentiment: {e}")
        return f"Error analyzing sentiment: {str(e)}"


def extract_action_items(content: str, tool_context=None) -> str:
    """Extract action items and tasks from email content."""
    try:
        if not content or not content.strip():
            return "No content provided for action item extraction"
        
        content_clean = _clean_email_content(content)
        action_items = []
        
        # Action keywords and patterns
        action_patterns = [
            r"please\s+(\w+[^.]*)",
            r"can you\s+(\w+[^.]*)",
            r"could you\s+(\w+[^.]*)",
            r"need to\s+(\w+[^.]*)",
            r"should\s+(\w+[^.]*)",
            r"must\s+(\w+[^.]*)",
            r"deadline[:\s]+([^.]*)",
            r"by\s+(\w+day[^.]*)",
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, content_clean, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 3:  # Avoid very short matches
                    action_items.append(match.strip())
        
        # Remove duplicates and limit
        action_items = list(dict.fromkeys(action_items))[:5]
        
        if not action_items:
            return "No clear action items found in this email"
        
        result = "Action items identified:\n"
        for i, item in enumerate(action_items, 1):
            result += f"{i}. {item[:60]}...\n" if len(item) > 60 else f"{i}. {item}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting action items: {e}")
        return f"Error extracting action items: {str(e)}"


# =============================================================================
# Voice Optimization Tools
# =============================================================================

def optimize_for_voice(content: str, max_length: int = 200, tool_context=None) -> str:
    """Optimize content for voice delivery."""
    try:
        if not content or not content.strip():
            return "No content provided for voice optimization"
        
        # Start with cleaned content
        voice_content = _clean_email_content(content)
        
        # Remove/replace elements that don't work well with voice
        voice_content = voice_content.replace("\n", " ").replace("\t", " ")
        voice_content = re.sub(r'\s+', ' ', voice_content)  # Multiple spaces to single
        
        # Replace abbreviations and symbols
        replacements = {
            "&": " and ",
            "e.g.": "for example",
            "i.e.": "that is",
            "etc.": "and so on",
            "vs.": "versus",
            "w/": "with",
            "@": " at ",
            "#": " number ",
            "%": " percent",
            "$": " dollars",
        }
        
        for old, new in replacements.items():
            voice_content = voice_content.replace(old, new)
        
        # Break long sentences at natural pause points
        voice_content = voice_content.replace(", and ", ". And ")
        voice_content = voice_content.replace(", but ", ". But ")
        voice_content = voice_content.replace(", however ", ". However ")
        
        # Remove URLs and email addresses (not voice-friendly)
        voice_content = re.sub(r'http[s]?://[^\s]+', '[link]', voice_content)
        voice_content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[email address]', voice_content)
        
        # Truncate if too long, but try to end at sentence boundary
        if len(voice_content) > max_length:
            truncated = voice_content[:max_length-3]
            last_sentence = truncated.rfind('.')
            if last_sentence > max_length * 0.7:  # If we can end at a reasonable sentence
                voice_content = truncated[:last_sentence + 1]
            else:
                voice_content = truncated + "..."
        
        return voice_content.strip()
        
    except Exception as e:
        logger.error(f"Error optimizing content for voice: {e}")
        return content[:max_length] if len(content) > max_length else content


def create_voice_summary(content: str, tool_context=None) -> str:
    """Create a summary specifically optimized for voice delivery."""
    try:
        if not content:
            return "No content to create voice summary"
        
        # First summarize, then optimize for voice
        summary = summarize_email_content(content, "moderate", tool_context)
        
        # Remove the "Summary:" prefix for voice
        if summary.startswith("Summary: "):
            summary = summary[9:]
        
        # Optimize for voice
        voice_summary = optimize_for_voice(summary, max_length=150, tool_context=tool_context)
        
        return voice_summary
        
    except Exception as e:
        logger.error(f"Error creating voice summary: {e}")
        return f"Error creating voice summary: {str(e)}"


# =============================================================================
# Helper Functions
# =============================================================================

def _clean_email_content(content: str) -> str:
    """Clean email content for processing."""
    try:
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Decode HTML entities
        content = html.unescape(content)
        
        # Remove email signatures (common patterns)
        signature_patterns = [
            r'\n--\s*\n.*$',  # Standard signature delimiter
            r'\nSent from my.*$',  # Mobile signatures
            r'\nBest regards,.*$',  # Common closings (keep the phrase, remove what follows)
            r'\nBest,.*$',
            r'\nSincerely,.*$',
            r'\nThanks,.*$'
        ]
        
        for pattern in signature_patterns:
            content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        content = content.strip()
        
        return content
        
    except Exception as e:
        logger.warning(f"Error cleaning email content: {e}")
        return content


def _extract_key_points(content: str, max_length: int = 100) -> str:
    """Extract key points for brief summary."""
    # Simple key point extraction - first sentence or key phrases
    sentences = content.split('.')
    if sentences:
        first_sentence = sentences[0].strip()
        if len(first_sentence) <= max_length:
            return first_sentence
        else:
            return first_sentence[:max_length-3] + "..."
    return content[:max_length-3] + "..."


def _extract_moderate_summary(content: str, max_length: int = 250) -> str:
    """Extract moderate summary."""
    # Take first 2-3 sentences or key content
    sentences = content.split('.')
    summary_parts = []
    current_length = 0
    
    for sentence in sentences[:3]:
        sentence = sentence.strip()
        if sentence and current_length + len(sentence) < max_length:
            summary_parts.append(sentence)
            current_length += len(sentence)
        else:
            break
    
    summary = '. '.join(summary_parts)
    if len(summary) < max_length and summary:
        summary += '.'
    
    return summary if summary else content[:max_length-3] + "..."


def _extract_detailed_summary(content: str, max_length: int = 400) -> str:
    """Extract detailed summary."""
    # More comprehensive summary with key details
    if len(content) <= max_length:
        return content
    
    # Take more content but still truncate intelligently
    sentences = content.split('.')
    summary_parts = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and current_length + len(sentence) < max_length - 20:
            summary_parts.append(sentence)
            current_length += len(sentence)
        else:
            break
    
    summary = '. '.join(summary_parts)
    if summary and not summary.endswith('.'):
        summary += '.'
    
    return summary if summary else content[:max_length-3] + "..."


def _extract_sender_info(email_content: str) -> str:
    """Extract sender name from email content."""
    try:
        # Look for "From:" line
        from_match = re.search(r'From:\s*([^<\n]+)', email_content, re.IGNORECASE)
        if from_match:
            sender = from_match.group(1).strip()
            # Clean up common email formats
            sender = re.sub(r'[<>"]', '', sender)
            # Take first name only
            first_name = sender.split()[0] if sender.split() else sender
            return first_name
        return ""
    except:
        return ""


# =============================================================================
# Create ADK Function Tools
# =============================================================================

# Summarization tools
summarize_email_content_tool = FunctionTool(func=summarize_email_content)
summarize_email_list_tool = FunctionTool(func=summarize_email_list)

# Reply generation tools
generate_email_reply_tool = FunctionTool(func=generate_email_reply)
suggest_reply_templates_tool = FunctionTool(func=suggest_reply_templates)

# Analysis tools
analyze_email_sentiment_tool = FunctionTool(func=analyze_email_sentiment)
extract_action_items_tool = FunctionTool(func=extract_action_items)

# Voice optimization tools
optimize_for_voice_tool = FunctionTool(func=optimize_for_voice)
create_voice_summary_tool = FunctionTool(func=create_voice_summary)

# Content tools collection
CONTENT_TOOLS = [
    summarize_email_content_tool,
    summarize_email_list_tool,
    generate_email_reply_tool,
    suggest_reply_templates_tool,
    analyze_email_sentiment_tool,
    extract_action_items_tool,
    optimize_for_voice_tool,
    create_voice_summary_tool
]

# Export for easy access
__all__ = [
    "summarize_email_content",
    "summarize_email_list",
    "generate_email_reply",
    "suggest_reply_templates",
    "analyze_email_sentiment",
    "extract_action_items",
    "optimize_for_voice",
    "create_voice_summary",
    "CONTENT_TOOLS"
]


# =============================================================================
# Testing
# =============================================================================

if __name__ == "__main__":
    print("🧪 Testing Direct Content Tools...")
    
    # Mock tool context for testing
    class MockSession:
        def __init__(self):
            self.state = {
                USER_PREFERENCES: {
                    "summary_detail": "moderate",
                    "reply_style": "professional"
                },
                USER_NAME: "Test User"
            }
    
    class MockToolContext:
        def __init__(self):
            self.session = MockSession()
    
    mock_context = MockToolContext()
    
    # Test content summarization
    test_email = """
    Hi John,
    
    I hope this email finds you well. I wanted to follow up on our meeting yesterday about the Q3 marketing campaign. 
    We discussed several key points including budget allocation, target demographics, and timeline for execution.
    
    Can you please send me the revised budget proposal by Friday? We need to finalize this before the board meeting next week.
    
    Thanks!
    Sarah
    """
    
    summary_result = summarize_email_content(test_email, "brief", mock_context)
    print(f"Summary test: {summary_result}")
    
    # Test reply generation
    reply_result = generate_email_reply(test_email, "I'll send the budget by Thursday", "professional", mock_context)
    print(f"Reply test: {reply_result[:100]}...")
    
    # Test sentiment analysis
    sentiment_result = analyze_email_sentiment(test_email, mock_context)
    print(f"Sentiment test: {sentiment_result}")
    
    # Test voice optimization
    voice_result = optimize_for_voice(test_email, 150, mock_context)
    print(f"Voice optimization test: {voice_result}")
    
    print("✅ Direct Content tools created successfully!")