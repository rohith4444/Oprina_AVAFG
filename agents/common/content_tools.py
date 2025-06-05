"""
Content Tools for ADK Integration

This module provides content processing tools that follow the ADK FunctionTool pattern.
These tools replace the MCP client approach with direct API calls.
"""

import os
import sys
import re
from typing import Optional, List, Dict, Any
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import project modules
from config.settings import settings
from services.logging.logger import setup_logger

# Configure logging
logger = setup_logger("content_tools", console_output=True)

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

def summarize_email_content(content: str = "", detail_level: str = "moderate", tool_context=None) -> Dict[str, Any]:
    """
    Summarize email content.
    
    Args:
        content: Email content to summarize
        detail_level: Detail level (brief, moderate, detailed)
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Summary
    """
    logger.info(f"Summarizing email content with detail level: {detail_level}")
    
    try:
        # Simple summarization logic
        # In a real implementation, this would use a language model
        
        # Split content into sentences
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        # Filter out empty sentences
        sentences = [s for s in sentences if s.strip()]
        
        # Determine how many sentences to include based on detail level
        if detail_level == "brief":
            num_sentences = min(1, len(sentences))
        elif detail_level == "moderate":
            num_sentences = min(3, len(sentences))
        else:  # detailed
            num_sentences = min(5, len(sentences))
        
        # Select sentences
        summary_sentences = sentences[:num_sentences]
        
        # Join sentences
        summary = " ".join(summary_sentences)
        
        return {
            "summary": summary,
            "detail_level": detail_level,
            "original_length": len(content),
            "summary_length": len(summary)
        }
        
    except Exception as e:
        logger.error(f"Error summarizing email content: {e}")
        return {"error": f"Failed to summarize email content: {str(e)}"}

def summarize_email_list(emails: str = "", max_emails: int = 5, tool_context=None) -> Dict[str, Any]:
    """
    Summarize a list of emails.
    
    Args:
        emails: List of emails to summarize
        max_emails: Maximum number of emails to include in summary
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Summary
    """
    logger.info(f"Summarizing email list with max_emails: {max_emails}")
    
    try:
        # Parse emails
        # In a real implementation, this would parse a structured list of emails
        
        # Simple parsing logic
        email_list = []
        for line in emails.split('\n'):
            if line.strip():
                email_list.append(line.strip())
        
        # Limit to max_emails
        email_list = email_list[:max_emails]
        
        # Create summary
        summary = f"Found {len(email_list)} emails. "
        
        if email_list:
            summary += "Top emails:\n"
            for i, email in enumerate(email_list[:3]):
                summary += f"{i+1}. {email}\n"
        
        return {
            "summary": summary,
            "email_count": len(email_list),
            "emails_included": min(len(email_list), max_emails)
        }
        
    except Exception as e:
        logger.error(f"Error summarizing email list: {e}")
        return {"error": f"Failed to summarize email list: {str(e)}"}

def generate_email_reply(original_email: str = "", reply_intent: str = "", style: str = "professional", tool_context=None) -> Dict[str, Any]:
    """
    Generate an email reply.
    
    Args:
        original_email: Original email content
        reply_intent: Intent of the reply (e.g., "accept", "decline", "clarify")
        style: Reply style (e.g., "professional", "casual", "formal")
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Generated reply
    """
    logger.info(f"Generating email reply with intent: {reply_intent}, style: {style}")
    
    try:
        # Simple reply generation logic
        # In a real implementation, this would use a language model
        
        # Extract subject from original email
        subject_match = re.search(r'Subject: (.*)', original_email)
        subject = subject_match.group(1) if subject_match else "Re: Your email"
        
        # Generate reply based on intent and style
        if reply_intent == "accept":
            if style == "professional":
                reply = f"I'm pleased to accept your proposal regarding {subject}. I look forward to working with you on this."
            elif style == "casual":
                reply = f"Great! I'm in for {subject}. Let's make it happen!"
            else:  # formal
                reply = f"I hereby confirm my acceptance of your proposal regarding {subject}. I appreciate the opportunity to collaborate on this matter."
        
        elif reply_intent == "decline":
            if style == "professional":
                reply = f"Thank you for your proposal regarding {subject}. Unfortunately, I must decline at this time."
            elif style == "casual":
                reply = f"Thanks for the offer about {subject}, but I'll have to pass this time."
            else:  # formal
                reply = f"I regret to inform you that I must decline your proposal regarding {subject}. I appreciate your consideration."
        
        elif reply_intent == "clarify":
            if style == "professional":
                reply = f"Thank you for your email regarding {subject}. I'd like to clarify a few points to ensure we're on the same page."
            elif style == "casual":
                reply = f"Hey, about {subject} - I just wanted to make sure I understand everything correctly."
            else:  # formal
                reply = f"I am writing in response to your correspondence regarding {subject}. I seek clarification on several points to ensure mutual understanding."
        
        else:  # general
            if style == "professional":
                reply = f"Thank you for your email regarding {subject}. I appreciate your message and will respond in more detail soon."
            elif style == "casual":
                reply = f"Thanks for your note about {subject}! I'll get back to you with more details soon."
            else:  # formal
                reply = f"I acknowledge receipt of your correspondence regarding {subject}. I shall respond in greater detail at the earliest opportunity."
        
        return {
            "reply": reply,
            "intent": reply_intent,
            "style": style,
            "subject": subject
        }
        
    except Exception as e:
        logger.error(f"Error generating email reply: {e}")
        return {"error": f"Failed to generate email reply: {str(e)}"}

def analyze_email_sentiment(content: str = "", tool_context=None) -> Dict[str, Any]:
    """
    Analyze email sentiment.
    
    Args:
        content: Email content to analyze
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Sentiment analysis
    """
    logger.info("Analyzing email sentiment")
    
    try:
        # Simple sentiment analysis logic
        # In a real implementation, this would use a language model
        
        # Count positive and negative words
        positive_words = ["good", "great", "excellent", "wonderful", "fantastic", "amazing", "happy", "pleased", "thank", "thanks", "appreciate"]
        negative_words = ["bad", "terrible", "awful", "horrible", "disappointed", "unhappy", "angry", "upset", "sorry", "regret", "unfortunately"]
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        # Determine sentiment
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "positive_score": positive_count,
            "negative_score": negative_count,
            "neutral_score": len(content.split()) - positive_count - negative_count
        }
        
    except Exception as e:
        logger.error(f"Error analyzing email sentiment: {e}")
        return {"error": f"Failed to analyze email sentiment: {str(e)}"}

def extract_action_items(content: str = "", tool_context=None) -> Dict[str, Any]:
    """
    Extract action items from email content.
    
    Args:
        content: Email content to analyze
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Action items
    """
    logger.info("Extracting action items from email content")
    
    try:
        # Simple action item extraction logic
        # In a real implementation, this would use a language model
        
        # Look for action item patterns
        action_patterns = [
            r"please\s+(\w+.*?)[\.\?]",
            r"can you\s+(\w+.*?)[\.\?]",
            r"could you\s+(\w+.*?)[\.\?]",
            r"would you\s+(\w+.*?)[\.\?]",
            r"need you to\s+(\w+.*?)[\.\?]",
            r"action required:\s+(.*?)[\.\?]",
            r"todo:\s+(.*?)[\.\?]",
            r"task:\s+(.*?)[\.\?]"
        ]
        
        action_items = []
        
        for pattern in action_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                action_items.append(match.group(1).strip())
        
        return {
            "action_items": action_items,
            "count": len(action_items)
        }
        
    except Exception as e:
        logger.error(f"Error extracting action items: {e}")
        return {"error": f"Failed to extract action items: {str(e)}"}

def optimize_for_voice(content: str = "", max_length: int = 200, tool_context=None) -> Dict[str, Any]:
    """
    Optimize content for voice.
    
    Args:
        content: Content to optimize
        max_length: Maximum length of optimized content
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Optimized content
    """
    logger.info(f"Optimizing content for voice with max_length: {max_length}")
    
    try:
        # Simple optimization logic
        # In a real implementation, this would use a language model
        
        # Remove URLs
        content = re.sub(r'https?://\S+', '[URL]', content)
        
        # Remove email addresses
        content = re.sub(r'\S+@\S+', '[EMAIL]', content)
        
        # Remove special characters
        content = re.sub(r'[^\w\s.,!?]', '', content)
        
        # Truncate to max_length
        if len(content) > max_length:
            content = content[:max_length] + "..."
        
        return {
            "optimized_content": content,
            "original_length": len(content),
            "optimized_length": len(content)
        }
        
    except Exception as e:
        logger.error(f"Error optimizing content for voice: {e}")
        return {"error": f"Failed to optimize content for voice: {str(e)}"}

def create_voice_summary(content: str = "", tool_context=None) -> Dict[str, Any]:
    """
    Create a voice summary of content.
    
    Args:
        content: Content to summarize
        tool_context: The tool context containing session information
        
    Returns:
        Dict[str, Any]: Voice summary
    """
    logger.info("Creating voice summary")
    
    try:
        # Simple voice summary logic
        # In a real implementation, this would use a language model
        
        # First summarize the content
        summary_result = summarize_email_content(content, "brief", tool_context)
        
        if "error" in summary_result:
            return summary_result
        
        summary = summary_result["summary"]
        
        # Then optimize for voice
        voice_result = optimize_for_voice(summary, 150, tool_context)
        
        if "error" in voice_result:
            return voice_result
        
        voice_summary = voice_result["optimized_content"]
        
        return {
            "voice_summary": voice_summary,
            "original_length": len(content),
            "summary_length": len(summary),
            "voice_length": len(voice_summary)
        }
        
    except Exception as e:
        logger.error(f"Error creating voice summary: {e}")
        return {"error": f"Failed to create voice summary: {str(e)}"}

# Create ADK FunctionTools
if ADK_AVAILABLE:
    summarize_email_content_tool = FunctionTool(
        func=summarize_email_content,
        name="summarize_email_content",
        description="Summarize email content.",
        parameters={
            "content": {"type": "string", "description": "Email content to summarize"},
            "detail_level": {"type": "string", "description": "Detail level (brief, moderate, detailed)"}
        }
    )
    
    summarize_email_list_tool = FunctionTool(
        func=summarize_email_list,
        name="summarize_email_list",
        description="Summarize a list of emails.",
        parameters={
            "emails": {"type": "string", "description": "List of emails to summarize"},
            "max_emails": {"type": "integer", "description": "Maximum number of emails to include in summary"}
        }
    )
    
    generate_email_reply_tool = FunctionTool(
        func=generate_email_reply,
        name="generate_email_reply",
        description="Generate an email reply.",
        parameters={
            "original_email": {"type": "string", "description": "Original email content"},
            "reply_intent": {"type": "string", "description": "Intent of the reply (e.g., 'accept', 'decline', 'clarify')"},
            "style": {"type": "string", "description": "Reply style (e.g., 'professional', 'casual', 'formal')"}
        }
    )
    
    analyze_email_sentiment_tool = FunctionTool(
        func=analyze_email_sentiment,
        name="analyze_email_sentiment",
        description="Analyze email sentiment.",
        parameters={
            "content": {"type": "string", "description": "Email content to analyze"}
        }
    )
    
    extract_action_items_tool = FunctionTool(
        func=extract_action_items,
        name="extract_action_items",
        description="Extract action items from email content.",
        parameters={
            "content": {"type": "string", "description": "Email content to analyze"}
        }
    )
    
    optimize_for_voice_tool = FunctionTool(
        func=optimize_for_voice,
        name="optimize_for_voice",
        description="Optimize content for voice reading.",
        parameters={
            "content": {"type": "string", "description": "Content to optimize"},
            "max_length": {"type": "integer", "description": "Maximum length of optimized content"}
        }
    )
    
    create_voice_summary_tool = FunctionTool(
        func=create_voice_summary,
        name="create_voice_summary",
        description="Create a voice-friendly summary of content.",
        parameters={
            "content": {"type": "string", "description": "Content to summarize"}
        }
    )
    
    # List of all content tools
    content_tools = [
        summarize_email_content_tool,
        summarize_email_list_tool,
        generate_email_reply_tool,
        analyze_email_sentiment_tool,
        extract_action_items_tool,
        optimize_for_voice_tool,
        create_voice_summary_tool
    ]
else:
    # Fallback tools
    content_tools = [
        summarize_email_content,
        summarize_email_list,
        generate_email_reply,
        analyze_email_sentiment,
        extract_action_items,
        optimize_for_voice,
        create_voice_summary
    ] 