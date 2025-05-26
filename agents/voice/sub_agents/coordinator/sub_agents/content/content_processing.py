"""
Content Processing Module for Content Agent

This module provides specialized content processing functions for:
- Email summarization with different detail levels
- Email reply generation with context awareness
- Content analysis and sentiment detection
- Text formatting and enhancement
- Template management for common email types

Key Features:
- Adaptive summarization based on user preferences
- Context-aware reply generation
- Sentiment analysis for appropriate response tone
- Template-based content generation
- Content length optimization for voice delivery
"""

import re
import html, os, sys
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from contextlib import AsyncExitStack

# Calculate project root more reliably
current_file = os.path.abspath(__file__)
# From: agents/voice/sub_agents/coordinator/sub_agents/email/mcp_integration.py
# Need to go up 6 levels to reach project root
project_root = current_file
for _ in range(7):  # 6 levels + 1 for the file itself
    project_root = os.path.dirname(project_root)

# Add to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from services.logging.logger import setup_logger

# Configure logging
logger = setup_logger("content_processing", console_output=True)


class SummaryDetail(Enum):
    """Summary detail levels."""
    BRIEF = "brief"
    MODERATE = "moderate"
    DETAILED = "detailed"


class ContentType(Enum):
    """Content types for processing."""
    EMAIL = "email"
    EMAIL_THREAD = "email_thread"
    EMAIL_LIST = "email_list"
    PLAIN_TEXT = "plain_text"
    HTML = "html"


class ReplyStyle(Enum):
    """Email reply styles."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    BRIEF = "brief"


@dataclass
class ContentMetadata:
    """Metadata for content processing."""
    content_type: ContentType
    word_count: int
    estimated_read_time: float  # in seconds
    sentiment: Optional[str] = None
    key_topics: Optional[List[str]] = None
    urgency_level: Optional[str] = None
    language: str = "en"


@dataclass
class ProcessingRequest:
    """Content processing request structure."""
    operation: str  # summarize, generate_reply, analyze, etc.
    content: str
    content_type: ContentType = ContentType.PLAIN_TEXT
    parameters: Dict[str, Any] = None
    user_preferences: Dict[str, Any] = None
    context: Dict[str, Any] = None


@dataclass
class ProcessingResult:
    """Content processing result structure."""
    success: bool
    result_content: str
    metadata: ContentMetadata
    processing_time_ms: float
    parameters_used: Dict[str, Any]
    error_message: str = ""


class ContentProcessor:
    """
    Advanced content processing for email and text content.
    Handles summarization, reply generation, and content analysis.
    """
    
    def __init__(self):
        """Initialize content processor."""
        self.logger = logger
        
        # Processing configuration
        self.max_summary_lengths = {
            SummaryDetail.BRIEF: 100,
            SummaryDetail.MODERATE: 250,
            SummaryDetail.DETAILED: 500
        }
        
        # Common email templates
        self.reply_templates = {
            "acknowledgment": "Thank you for your email about {subject}. I'll {action} and get back to you {timeframe}.",
            "meeting_request": "I'd be happy to meet about {topic}. I'm available {availability}. Please let me know what works best for you.",
            "information_request": "Here's the information you requested about {topic}: {details}",
            "follow_up": "Following up on our previous discussion about {topic}. {update_or_question}",
            "decline_politely": "Thank you for thinking of me for {request}. Unfortunately, I won't be able to {reason}, but I appreciate the opportunity."
        }
    
    def clean_email_content(self, content: str) -> str:
        """
        Clean email content by removing HTML, signatures, and formatting.
        
        Args:
            content: Raw email content
            
        Returns:
            Cleaned text content
        """
        try:
            # Remove HTML tags
            content = re.sub(r'<[^>]+>', '', content)
            
            # Decode HTML entities
            content = html.unescape(content)
            
            # Remove email signatures (common patterns)
            signature_patterns = [
                r'\n--\s*\n.*$',  # Standard signature delimiter
                r'\nSent from my.*$',  # Mobile signatures
                r'\nBest regards,.*$',  # Common closings
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
            self.logger.error(f"Error cleaning email content: {e}")
            return content
    
    def extract_email_metadata(self, email_data: Dict[str, Any]) -> ContentMetadata:
        """
        Extract metadata from email data.
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            Content metadata
        """
        try:
            content = email_data.get("body", email_data.get("snippet", ""))
            cleaned_content = self.clean_email_content(content)
            
            word_count = len(cleaned_content.split())
            estimated_read_time = max(word_count / 200 * 60, 5)  # 200 WPM, min 5 seconds
            
            # Simple sentiment analysis (can be enhanced)
            sentiment = self._analyze_sentiment(cleaned_content)
            
            # Extract key topics (simple keyword extraction)
            key_topics = self._extract_key_topics(cleaned_content)
            
            # Determine urgency level
            urgency_level = self._determine_urgency(email_data, cleaned_content)
            
            return ContentMetadata(
                content_type=ContentType.EMAIL,
                word_count=word_count,
                estimated_read_time=estimated_read_time,
                sentiment=sentiment,
                key_topics=key_topics,
                urgency_level=urgency_level
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting email metadata: {e}")
            return ContentMetadata(
                content_type=ContentType.EMAIL,
                word_count=0,
                estimated_read_time=0
            )
    
    def _analyze_sentiment(self, content: str) -> str:
        """
        Simple sentiment analysis.
        
        Args:
            content: Text content
            
        Returns:
            Sentiment category (positive, negative, neutral, urgent)
        """
        content_lower = content.lower()
        
        # Urgent indicators
        urgent_words = ["urgent", "asap", "immediately", "emergency", "critical", "deadline"]
        if any(word in content_lower for word in urgent_words):
            return "urgent"
        
        # Positive indicators
        positive_words = ["thank", "great", "excellent", "pleased", "happy", "congratulations"]
        positive_count = sum(1 for word in positive_words if word in content_lower)
        
        # Negative indicators
        negative_words = ["problem", "issue", "concern", "complaint", "error", "failed", "wrong"]
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _extract_key_topics(self, content: str, max_topics: int = 5) -> List[str]:
        """
        Extract key topics from content.
        
        Args:
            content: Text content
            max_topics: Maximum number of topics to extract
            
        Returns:
            List of key topics
        """
        try:
            # Simple keyword extraction based on word frequency
            words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
            
            # Filter out common words
            stop_words = {
                "this", "that", "with", "have", "will", "from", "they", "been", 
                "were", "said", "each", "which", "their", "time", "would", "about",
                "email", "message", "send", "please", "thank", "thanks", "regards"
            }
            
            filtered_words = [word for word in words if word not in stop_words]
            
            # Count word frequency
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get most frequent words as topics
            topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [topic[0] for topic in topics[:max_topics]]
            
        except Exception as e:
            self.logger.error(f"Error extracting key topics: {e}")
            return []
    
    def _determine_urgency(self, email_data: Dict[str, Any], content: str) -> str:
        """
        Determine urgency level of email.
        
        Args:
            email_data: Email metadata
            content: Email content
            
        Returns:
            Urgency level (low, normal, high, urgent)
        """
        try:
            urgency_score = 0
            
            # Check importance flag
            if email_data.get("important", False):
                urgency_score += 2
            
            # Check subject line
            subject = email_data.get("subject", "").lower()
            if any(word in subject for word in ["urgent", "asap", "immediate"]):
                urgency_score += 3
            elif any(word in subject for word in ["fyi", "info", "update"]):
                urgency_score -= 1
            
            # Check sender importance (would be enhanced with user's contact prioritization)
            sender = email_data.get("sender", "")
            if "noreply" in sender.lower() or "no-reply" in sender.lower():
                urgency_score -= 2
            
            # Check content for urgency indicators
            content_lower = content.lower()
            urgent_indicators = ["deadline", "urgent", "asap", "emergency", "critical"]
            urgency_score += sum(1 for indicator in urgent_indicators if indicator in content_lower)
            
            # Determine final urgency level
            if urgency_score >= 4:
                return "urgent"
            elif urgency_score >= 2:
                return "high"
            elif urgency_score <= -2:
                return "low"
            else:
                return "normal"
                
        except Exception as e:
            self.logger.error(f"Error determining urgency: {e}")
            return "normal"
    
    def generate_summary_prompt(
        self,
        content: str,
        detail_level: SummaryDetail,
        user_preferences: Dict[str, Any] = None
    ) -> str:
        """
        Generate a specialized prompt for email summarization.
        
        Args:
            content: Content to summarize
            detail_level: Level of detail for summary
            user_preferences: User's summarization preferences
            
        Returns:
            Tailored summarization prompt
        """
        try:
            max_length = self.max_summary_lengths[detail_level]
            preferences = user_preferences or {}
            
            # Base prompt based on detail level
            if detail_level == SummaryDetail.BRIEF:
                prompt = f"""
                Summarize this email content in {max_length} characters or less.
                Focus on: main action items, key decisions, and immediate next steps.
                Format: Single paragraph, conversational tone suitable for voice delivery.
                Prioritize: Actionable information over background details.
                
                Email content:
                {content}
                
                Summary:"""
                
            elif detail_level == SummaryDetail.MODERATE:
                prompt = f"""
                Provide a moderate summary of this email in {max_length} characters or less.
                Include: main points, context, action items, and key details.
                Format: 2-3 sentences, clear and structured.
                Balance: Important details with conciseness.
                
                Email content:
                {content}
                
                Summary:"""
                
            else:  # DETAILED
                prompt = f"""
                Create a detailed summary of this email in {max_length} characters or less.
                Include: full context, all action items, key details, timeline, and participants.
                Format: Multiple sentences with clear structure.
                Preserve: Important nuances and specific information.
                
                Email content:
                {content}
                
                Detailed summary:"""
            
            # Add user preference modifications
            if preferences.get("include_sentiment", False):
                prompt += "\nAlso mention the overall tone/sentiment of the email."
                
            if preferences.get("highlight_urgency", True):
                prompt += "\nIndicate if this email requires urgent attention."
                
            if preferences.get("voice_optimized", True):
                prompt += "\nOptimize the summary for voice delivery - use conversational language."
            
            return prompt
            
        except Exception as e:
            self.logger.error(f"Error generating summary prompt: {e}")
            return f"Summarize this email briefly:\n{content}"
    
    def generate_reply_prompt(
        self,
        original_email: Dict[str, Any],
        reply_intent: str,
        reply_style: ReplyStyle = ReplyStyle.PROFESSIONAL,
        user_context: Dict[str, Any] = None
    ) -> str:
        """
        Generate a prompt for email reply generation.
        
        Args:
            original_email: Original email data
            reply_intent: What the user wants to communicate
            reply_style: Style of the reply
            user_context: User's context and preferences
            
        Returns:
            Reply generation prompt
        """
        try:
            sender = original_email.get("sender", "")
            subject = original_email.get("subject", "")
            content = original_email.get("body", original_email.get("snippet", ""))
            
            user_name = user_context.get("user_name", "") if user_context else ""
            user_email = user_context.get("user_email", "") if user_context else ""
            
            # Style-specific instructions
            style_instructions = {
                ReplyStyle.PROFESSIONAL: "Use professional, business-appropriate language. Be courteous and clear.",
                ReplyStyle.CASUAL: "Use casual, friendly language. Keep it conversational but respectful.",
                ReplyStyle.FRIENDLY: "Use warm, friendly tone. Show enthusiasm and personal connection.",
                ReplyStyle.FORMAL: "Use formal language with proper business etiquette. Be respectful and structured.",
                ReplyStyle.BRIEF: "Keep the response very concise. Get straight to the point."
            }
            
            prompt = f"""
            Generate a {reply_style.value} email reply based on the following:
            
            ORIGINAL EMAIL:
            From: {sender}
            Subject: {subject}
            Content: {content}
            
            USER'S INTENT: {reply_intent}
            
            STYLE GUIDELINES: {style_instructions[reply_style]}
            
            REQUIREMENTS:
            - Address the sender appropriately
            - Respond to their main points
            - Incorporate the user's intent naturally
            - Use proper email structure (greeting, body, closing)
            - Keep it suitable for voice-generated content
            {"- Sign as " + user_name if user_name else "- Use appropriate closing"}
            
            Generate the email reply:"""
            
            return prompt
            
        except Exception as e:
            self.logger.error(f"Error generating reply prompt: {e}")
            return f"Generate a reply to this email expressing: {reply_intent}"
    
    def analyze_email_thread(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a thread of emails for conversation flow and context.
        
        Args:
            emails: List of emails in chronological order
            
        Returns:
            Thread analysis results
        """
        try:
            if not emails:
                return {"error": "No emails provided"}
            
            analysis = {
                "thread_length": len(emails),
                "participants": set(),
                "date_range": {},
                "key_topics": [],
                "action_items": [],
                "sentiment_flow": [],
                "summary": ""
            }
            
            # Extract participants
            for email in emails:
                sender = email.get("sender", "")
                if sender:
                    analysis["participants"].add(sender)
            
            analysis["participants"] = list(analysis["participants"])
            
            # Date range
            if emails:
                dates = [email.get("date") for email in emails if email.get("date")]
                if dates:
                    analysis["date_range"] = {
                        "start": min(dates),
                        "end": max(dates)
                    }
            
            # Combine all content for topic extraction
            all_content = " ".join([
                self.clean_email_content(email.get("body", email.get("snippet", "")))
                for email in emails
            ])
            
            analysis["key_topics"] = self._extract_key_topics(all_content, max_topics=8)
            
            # Analyze sentiment flow
            for email in emails:
                content = self.clean_email_content(email.get("body", email.get("snippet", "")))
                sentiment = self._analyze_sentiment(content)
                analysis["sentiment_flow"].append({
                    "sender": email.get("sender", ""),
                    "sentiment": sentiment,
                    "date": email.get("date")
                })
            
            # Generate thread summary
            thread_summary = self._generate_thread_summary(emails, analysis)
            analysis["summary"] = thread_summary
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing email thread: {e}")
            return {"error": str(e)}
    
    def _generate_thread_summary(self, emails: List[Dict[str, Any]], analysis: Dict[str, Any]) -> str:
        """Generate a summary of the email thread."""
        try:
            participants = analysis["participants"]
            key_topics = analysis["key_topics"]
            thread_length = analysis["thread_length"]
            
            if thread_length == 1:
                return f"Single email from {participants[0] if participants else 'unknown sender'} about {', '.join(key_topics[:3]) if key_topics else 'general topic'}."
            
            summary = f"Email thread with {thread_length} messages between {len(participants)} participants"
            
            if len(participants) <= 3:
                summary += f" ({', '.join(participants)})"
            
            if key_topics:
                summary += f" discussing {', '.join(key_topics[:3])}"
            
            # Add sentiment insight
            sentiments = [item["sentiment"] for item in analysis["sentiment_flow"]]
            if "urgent" in sentiments:
                summary += ". Contains urgent items."
            elif sentiments.count("positive") > sentiments.count("negative"):
                summary += ". Generally positive tone."
            elif sentiments.count("negative") > sentiments.count("positive"):
                summary += ". Contains concerns or issues."
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating thread summary: {e}")
            return "Email thread analysis summary unavailable."
    
    def optimize_for_voice(self, content: str, max_length: int = 300) -> str:
        """
        Optimize content for voice delivery.
        
        Args:
            content: Text content to optimize
            max_length: Maximum character length
            
        Returns:
            Voice-optimized content
        """
        try:
            # Remove complex punctuation
            content = re.sub(r'[(){}[\]]', '', content)
            
            # Replace abbreviations with full words
            abbreviations = {
                "e.g.": "for example",
                "i.e.": "that is",
                "etc.": "and so on",
                "vs.": "versus",
                "w/": "with",
                "&": "and"
            }
            
            for abbrev, full in abbreviations.items():
                content = content.replace(abbrev, full)
            
            # Break long sentences
            sentences = content.split('. ')
            optimized_sentences = []
            
            for sentence in sentences:
                if len(sentence) > 100:  # Long sentence
                    # Try to break at conjunctions
                    for conjunction in [' and ', ' but ', ' however ', ' although ']:
                        if conjunction in sentence:
                            parts = sentence.split(conjunction, 1)
                            optimized_sentences.append(parts[0].strip())
                            optimized_sentences.append(conjunction.strip() + ' ' + parts[1].strip())
                            break
                    else:
                        optimized_sentences.append(sentence)
                else:
                    optimized_sentences.append(sentence)
            
            result = '. '.join(optimized_sentences)
            
            # Truncate if too long
            if len(result) > max_length:
                result = result[:max_length - 3] + "..."
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error optimizing content for voice: {e}")
            return content[:max_length] if len(content) > max_length else content


# Global content processor instance
content_processor = ContentProcessor()


# Helper functions for use in agent tools
def process_email_content(
    operation: str,
    content: str,
    parameters: Dict[str, Any] = None,
    user_preferences: Dict[str, Any] = None,
    context: Dict[str, Any] = None
) -> ProcessingResult:
    """
    Process email content with specified operation.
    
    Args:
        operation: Processing operation (summarize, analyze, etc.)
        content: Content to process
        parameters: Operation-specific parameters
        user_preferences: User preferences for processing
        context: Additional context
        
    Returns:
        Processing result
    """
    start_time = datetime.utcnow()
    
    try:
        parameters = parameters or {}
        user_preferences = user_preferences or {}
        context = context or {}
        
        if operation == "summarize":
            detail_level = SummaryDetail(parameters.get("detail_level", "moderate"))
            prompt = content_processor.generate_summary_prompt(content, detail_level, user_preferences)
            
            # For now, return the prompt - actual LLM processing happens in agent
            result_content = prompt
            
        elif operation == "analyze":
            # Extract metadata and return analysis
            email_data = context.get("email_data", {"body": content})
            metadata = content_processor.extract_email_metadata(email_data)
            result_content = f"Analysis: {metadata.word_count} words, {metadata.sentiment} sentiment, topics: {', '.join(metadata.key_topics or [])}"
            
        elif operation == "optimize_voice":
            max_length = parameters.get("max_length", 300)
            result_content = content_processor.optimize_for_voice(content, max_length)
            
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        # Create metadata
        metadata = ContentMetadata(
            content_type=ContentType.EMAIL,
            word_count=len(result_content.split()),
            estimated_read_time=len(result_content) / 200 * 60  # Rough estimate
        )
        
        return ProcessingResult(
            success=True,
            result_content=result_content,
            metadata=metadata,
            processing_time_ms=processing_time,
            parameters_used=parameters
        )
        
    except Exception as e:
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        logger.error(f"Error in process_email_content: {e}")
        
        return ProcessingResult(
            success=False,
            result_content="",
            metadata=ContentMetadata(ContentType.EMAIL, 0, 0),
            processing_time_ms=processing_time,
            parameters_used=parameters,
            error_message=str(e)
        )


# Export key functions
__all__ = [
    "ContentProcessor",
    "SummaryDetail",
    "ContentType", 
    "ReplyStyle",
    "ProcessingRequest",
    "ProcessingResult",
    "content_processor",
    "process_email_content"
]


if __name__ == "__main__":
    # Test content processing
    def test_content_processing():
        print("Testing Content Processing Module...")
        
        # Test email content
        test_email = {
            "sender": "john@company.com",
            "subject": "Urgent: Project Update Required",
            "body": """
            Hi there,
            
            I hope this email finds you well. I wanted to follow up on our project discussion 
            from last week. We have an urgent deadline approaching on Friday, and I need your 
            input on the marketing strategy for our new product launch.
            
            Could you please review the attached documents and provide feedback by Thursday?
            This is critical for our timeline.
            
            Thank you for your attention to this matter.
            
            Best regards,
            John Smith
            Marketing Director
            """,
            "important": True
        }
        
        # Test metadata extraction
        metadata = content_processor.extract_email_metadata(test_email)
        print(f"✅ Metadata: {metadata.word_count} words, {metadata.sentiment} sentiment")
        print(f"   Topics: {metadata.key_topics}")
        print(f"   Urgency: {metadata.urgency_level}")
        
        # Test summarization prompt generation
        summary_prompt = content_processor.generate_summary_prompt(
            test_email["body"], 
            SummaryDetail.BRIEF
        )
        print(f"✅ Brief summary prompt generated")
        
        # Test reply prompt generation
        reply_prompt = content_processor.generate_reply_prompt(
            test_email,
            "I'll review the documents and send feedback by Wednesday",
            ReplyStyle.PROFESSIONAL
        )
        print(f"✅ Reply prompt generated")
        
        # Test voice optimization
        optimized = content_processor.optimize_for_voice(test_email["body"])
        print(f"✅ Voice optimization: {len(optimized)} characters")
        
        # Test processing function
        result = process_email_content(
            "analyze",
            test_email["body"],
            context={"email_data": test_email}
        )
        print(f"✅ Processing result: {result.success}")
        
        print("✅ Content processing tests completed!")
    
    test_content_processing()