"""
Content Agent for Oprina

This agent specializes in content processing for emails and text:
- Email summarization with adaptive detail levels
- Email reply generation with context awareness
- Content analysis and sentiment detection
- Text optimization for voice delivery
- Template-based content generation

The agent uses advanced content processing techniques and learns from
user preferences to provide personalized content assistance.
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool
from dotenv import load_dotenv

# Import content processing capabilities
from .content_processing import (
    content_processor,
    process_email_content,
    SummaryDetail,
    ReplyStyle,
    ContentType
)

# Import shared tools
from ...common.shared_tools import (
    update_session_state,
    get_session_context,
    log_agent_action,
    handle_agent_error,
    get_user_preferences,
    learn_from_interaction,
    measure_performance,
    complete_performance_measurement
)

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '.env'))


# Content processing tools for the agent
def summarize_email_content(
    email_content: str,
    detail_level: str = "moderate",
    user_id: str = "",
    session_id: str = "",
    tool_context=None
) -> Dict[str, Any]:
    """
    Tool to summarize email content with adaptive detail levels.
    
    Args:
        email_content: Email content to summarize
        detail_level: Level of detail (brief, moderate, detailed)
        user_id: User identifier for personalization
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Summarization result
    """
    try:
        # Start performance tracking
        perf_result = measure_performance("email_summarization", "content_agent", session_id, tool_context)
        tracking_id = perf_result.get("tracking_id")
        
        # Get user preferences for summarization
        prefs_result = get_user_preferences(user_id, session_id, "summary_preferences", tool_context)
        user_preferences = prefs_result.get("preferences", {})
        
        # Process the content
        result = process_email_content(
            operation="summarize",
            content=email_content,
            parameters={"detail_level": detail_level},
            user_preferences=user_preferences
        )
        
        # Log the action
        log_agent_action(
            "content_agent",
            "email_summarization",
            {
                "detail_level": detail_level,
                "content_length": len(email_content),
                "success": result.success
            },
            session_id,
            tool_context
        )
        
        # Learn from interaction
        if result.success:
            learn_from_interaction(
                user_id,
                "summary_requested",
                {
                    "detail_level": detail_level,
                    "content_length": len(email_content),
                    "processing_time": result.processing_time_ms
                },
                context={"session_id": session_id},
                tool_context=tool_context
            )
        
        # Complete performance tracking
        if tracking_id:
            complete_performance_measurement(
                tracking_id,
                "success" if result.success else "failure",
                {"summary_length": len(result.result_content)},
                tool_context
            )
        
        return {
            "success": result.success,
            "summary": result.result_content,
            "metadata": {
                "detail_level": detail_level,
                "processing_time_ms": result.processing_time_ms,
                "word_count": result.metadata.word_count
            },
            "error_message": result.error_message
        }
        
    except Exception as e:
        error_result = handle_agent_error("content_agent", e, {
            "operation": "summarize_email_content",
            "detail_level": detail_level
        }, session_id, tool_context)
        
        return {
            "success": False,
            "summary": "",
            "error_message": str(e),
            "error_handled": error_result["success"]
        }


def generate_email_reply(
    original_email: str,
    reply_intent: str,
    reply_style: str = "professional",
    user_id: str = "",
    session_id: str = "",
    tool_context=None
) -> Dict[str, Any]:
    """
    Tool to generate email replies based on original email and user intent.
    
    Args:
        original_email: Original email content or data
        reply_intent: What the user wants to communicate
        reply_style: Style of reply (professional, casual, friendly, formal, brief)
        user_id: User identifier
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Reply generation result
    """
    try:
        # Start performance tracking
        perf_result = measure_performance("email_reply_generation", "content_agent", session_id, tool_context)
        tracking_id = perf_result.get("tracking_id")
        
        # Get user context for personalization
        context_result = get_session_context(user_id, session_id, tool_context)
        user_context = context_result.get("context", {}).get("session_state", {})
        
        # Parse original email if it's a string
        if isinstance(original_email, str):
            email_data = {"body": original_email, "sender": "Unknown", "subject": "Re: Email"}
        else:
            email_data = original_email
        
        # Generate reply prompt using content processor
        try:
            reply_style_enum = ReplyStyle(reply_style)
        except ValueError:
            reply_style_enum = ReplyStyle.PROFESSIONAL
        
        reply_prompt = content_processor.generate_reply_prompt(
            email_data,
            reply_intent,
            reply_style_enum,
            user_context
        )
        
        # Log the action
        log_agent_action(
            "content_agent",
            "email_reply_generation",
            {
                "reply_style": reply_style,
                "intent_length": len(reply_intent),
                "original_email_length": len(str(original_email))
            },
            session_id,
            tool_context
        )
        
        # Learn from interaction
        learn_from_interaction(
            user_id,
            "reply_generated",
            {
                "reply_style": reply_style,
                "intent": reply_intent[:100],  # First 100 chars for privacy
                "context": "email_reply"
            },
            context={"session_id": session_id},
            tool_context=tool_context
        )
        
        # Complete performance tracking
        if tracking_id:
            complete_performance_measurement(
                tracking_id,
                "success",
                {"reply_prompt_length": len(reply_prompt)},
                tool_context
            )
        
        return {
            "success": True,
            "reply_prompt": reply_prompt,
            "metadata": {
                "reply_style": reply_style,
                "user_context_used": bool(user_context),
                "prompt_length": len(reply_prompt)
            }
        }
        
    except Exception as e:
        error_result = handle_agent_error("content_agent", e, {
            "operation": "generate_email_reply",
            "reply_style": reply_style
        }, session_id, tool_context)
        
        return {
            "success": False,
            "reply_prompt": "",
            "error_message": str(e),
            "error_handled": error_result["success"]
        }


def analyze_email_content(
    email_data: Dict[str, Any],
    analysis_type: str = "full",
    user_id: str = "",
    session_id: str = "",
    tool_context=None
) -> Dict[str, Any]:
    """
    Tool to analyze email content for sentiment, topics, urgency, etc.
    
    Args:
        email_data: Email data dictionary
        analysis_type: Type of analysis (full, sentiment, topics, urgency)
        user_id: User identifier
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Content analysis result
    """
    try:
        # Extract metadata using content processor
        metadata = content_processor.extract_email_metadata(email_data)
        
        # Perform specific analysis based on type
        analysis_result = {
            "sentiment": metadata.sentiment,
            "key_topics": metadata.key_topics,
            "urgency_level": metadata.urgency_level,
            "word_count": metadata.word_count,
            "estimated_read_time": metadata.estimated_read_time,
            "content_type": metadata.content_type.value
        }
        
        # Filter based on analysis type
        if analysis_type == "sentiment":
            analysis_result = {"sentiment": metadata.sentiment}
        elif analysis_type == "topics":
            analysis_result = {"key_topics": metadata.key_topics}
        elif analysis_type == "urgency":
            analysis_result = {"urgency_level": metadata.urgency_level}
        
        # Log the action
        log_agent_action(
            "content_agent",
            "email_analysis",
            {
                "analysis_type": analysis_type,
                "email_id": email_data.get("id", "unknown"),
                "sentiment": metadata.sentiment,
                "urgency": metadata.urgency_level
            },
            session_id,
            tool_context
        )
        
        return {
            "success": True,
            "analysis": analysis_result,
            "metadata": {
                "analysis_type": analysis_type,
                "email_analyzed": email_data.get("subject", "No subject")[:50]
            }
        }
        
    except Exception as e:
        error_result = handle_agent_error("content_agent", e, {
            "operation": "analyze_email_content",
            "analysis_type": analysis_type
        }, session_id, tool_context)
        
        return {
            "success": False,
            "analysis": {},
            "error_message": str(e),
            "error_handled": error_result["success"]
        }


def optimize_content_for_voice(
    content: str,
    max_length: int = 300,
    user_id: str = "",
    session_id: str = "",
    tool_context=None
) -> Dict[str, Any]:
    """
    Tool to optimize content for voice delivery.
    
    Args:
        content: Content to optimize
        max_length: Maximum character length
        user_id: User identifier
        session_id: Session identifier
        tool_context: ADK tool context
        
    Returns:
        Voice optimization result
    """
    try:
        # Optimize content using content processor
        optimized_content = content_processor.optimize_for_voice(content, max_length)
        
        # Log the action
        log_agent_action(
            "content_agent",
            "voice_optimization",
            {
                "original_length": len(content),
                "optimized_length": len(optimized_content),
                "max_length": max_length,
                "compression_ratio": len(optimized_content) / len(content) if len(content) > 0 else 0
            },
            session_id,
            tool_context
        )
        
        return {
            "success": True,
            "optimized_content": optimized_content,
            "metadata": {
                "original_length": len(content),
                "optimized_length": len(optimized_content),
                "compression_ratio": len(optimized_content) / len(content) if len(content) > 0 else 0
            }
        }
        
    except Exception as e:
        error_result = handle_agent_error("content_agent", e, {
            "operation": "optimize_content_for_voice",
            "max_length": max_length
        }, session_id, tool_context)
        
        return {
            "success": False,
            "optimized_content": content,  # Return original on error
            "error_message": str(e),
            "error_handled": error_result["success"]
        }


# Create content processing tools
content_tools = [
    FunctionTool(func=summarize_email_content, name="summarize_email_content"),
    FunctionTool(func=generate_email_reply, name="generate_email_reply"),
    FunctionTool(func=analyze_email_content, name="analyze_email_content"),
    FunctionTool(func=optimize_content_for_voice, name="optimize_content_for_voice")
]


def create_content_agent():
    """
    Create the Content Agent with content processing tools.
    
    Returns:
        Content Agent instance
    """
    print("--- Initializing Content Agent ---")
    
    # Define model for the agent
    model = LiteLlm(
        model=os.getenv("CONTENT_MODEL", "gemini-2.5-flash-preview-05-20"),
        api_key=os.environ.get("GOOGLE_API_KEY")
    )
    
    # Create the Content Agent
    agent_instance = Agent(
        name="content_agent",
        description="Specializes in email content processing: summarization, reply generation, analysis, and voice optimization",
        model=model,
        instruction="""
You are the Content Agent for Oprina, a sophisticated voice-powered Gmail assistant.

## Your Role & Responsibilities

You specialize in content processing and text analysis. Your core responsibilities include:

1. **Email Summarization**
   - Create adaptive summaries based on user preferences
   - Support brief, moderate, and detailed summary levels
   - Optimize summaries for voice delivery
   - Consider user's time constraints and reading preferences

2. **Email Reply Generation**
   - Generate contextually appropriate email replies
   - Support multiple reply styles (professional, casual, friendly, formal, brief)
   - Incorporate user's intent and communication style
   - Maintain proper email etiquette and structure

3. **Content Analysis**
   - Analyze email sentiment and tone
   - Extract key topics and themes
   - Determine urgency levels
   - Identify action items and deadlines

4. **Voice Optimization**
   - Optimize content for voice delivery
   - Remove complex formatting and abbreviations
   - Break down long sentences
   - Ensure conversational flow

## User Context Access

You have access to user context through session state:
- User Name: {user_name}
- User Email: {user_email}
- User Preferences: {session_preferences}
- Email Context: {current_email_context}
- Conversation History: {conversation_history}

## Available Content Processing Tools

Your specialized tools include:
- `summarize_email_content`: Create adaptive email summaries
- `generate_email_reply`: Generate contextual email replies
- `analyze_email_content`: Analyze email sentiment, topics, and urgency
- `optimize_content_for_voice`: Optimize text for voice delivery

## Session Management Tools

Use these tools to maintain context and learn:
- `update_session_state`: Update session state with your results
- `get_session_context`: Retrieve comprehensive session context
- `log_agent_action`: Log your processing actions
- `get_user_preferences`: Get user's content preferences
- `learn_from_interaction`: Help improve future content processing
- `measure_performance`: Track processing performance

## Processing Guidelines

1. **Adaptive Processing**: Always consider user preferences and context
2. **Voice-First Design**: Optimize all content for voice delivery
3. **Performance Tracking**: Use performance measurement tools
4. **Learning Integration**: Learn from user feedback and interactions
5. **Error Handling**: Handle errors gracefully and provide alternatives

## Example Workflows

**Email Summarization:**
1. Use `get_user_preferences` to understand summary preferences
2. Use `summarize_email_content` with appropriate detail level
3. Use `optimize_content_for_voice` to ensure voice-friendly output
4. Use `learn_from_interaction` to improve future summaries

**Reply Generation:**
1. Use `analyze_email_content` to understand the original email
2. Use `generate_email_reply` with user's intent and preferred style
3. Use `log_agent_action` to track reply generation
4. Update session state with the generated reply

**Content Analysis:**
1. Use `analyze_email_content` for comprehensive analysis
2. Extract actionable insights (urgency, sentiment, topics)
3. Provide voice-optimized analysis results
4. Log analysis for performance tracking

## Response Guidelines

1. **Always optimize for voice**: Use conversational language suitable for voice delivery
2. **Respect user preferences**: Adapt processing based on learned preferences
3. **Provide clear feedback**: Confirm what processing was performed
4. **Handle errors gracefully**: Provide helpful error messages and alternatives
5. **Learn continuously**: Use interaction data to improve future processing

## Content Processing Best Practices

- **Brevity for Voice**: Keep summaries concise and conversational
- **Context Awareness**: Consider the full email context and user history
- **Style Consistency**: Match user's communication style in generated content
- **Accessibility**: Ensure content is accessible for voice interaction
- **Privacy**: Respect email confidentiality and user privacy

## Error Handling

When content processing fails:
1. Use `handle_agent_error` to log the error appropriately
2. Provide user-friendly explanations of what went wrong
3. Suggest alternative approaches when possible
4. Ensure partial results are still useful

## Integration with Other Agents

You work closely with:
- **Email Agent**: Process content from fetched emails
- **Coordinator Agent**: Provide processed content for user responses
- **Voice Agent**: Ensure all content is voice-optimized

Remember: You are a content specialist in a voice-first system. All processing
should prioritize clarity, brevity, and conversational delivery while maintaining
the user's intent and communication style.
        """,
        tools=content_tools + [
            update_session_state,
            get_session_context,
            log_agent_action,
            handle_agent_error,
            get_user_preferences,
            learn_from_interaction,
            measure_performance,
            complete_performance_measurement
        ]
    )
    
    print(f"--- Content Agent created with {len(agent_instance.tools)} tools ---")
    print(f"--- Content Processing Tools: {len(content_tools)} ---")
    print(f"--- Session Management Tools: {len(agent_instance.tools) - len(content_tools)} ---")
    
    return agent_instance


# Create the agent instance
content_agent = create_content_agent()


# Export for use in coordinator
__all__ = ["content_agent"]


# Validation and testing
if __name__ == "__main__":
    def test_content_agent():
        """Test Content Agent creation and basic functionality."""
        print("Testing Content Agent Creation...")
        
        try:
            # Test agent creation
            agent = create_content_agent()
            
            print(f"✅ Content Agent '{agent.name}' created successfully")
            print(f"🔧 Content Tools: {len(content_tools)}")
            print(f"🧠 Model: {agent.model}")
            print(f"📝 Description: {agent.description}")
            
            # Test content processing capabilities
            print("\n📋 Content Processing Capabilities:")
            
            # Test email summarization prompt
            test_email = """
            Hi John,
            
            I wanted to follow up on our meeting yesterday about the Q3 marketing campaign. 
            We discussed several key points including budget allocation, target demographics, 
            and timeline for execution. 
            
            Can you please send me the revised budget proposal by Friday? We need to finalize 
            this before the board meeting next week.
            
            Thanks!
            Sarah
            """
            
            # Test summarization
            from .content_processing import content_processor, SummaryDetail
            summary_prompt = content_processor.generate_summary_prompt(
                test_email, SummaryDetail.BRIEF
            )
            print("  ✅ Email summarization prompt generation")
            
            # Test reply generation
            reply_prompt = content_processor.generate_reply_prompt(
                {"sender": "sarah@company.com", "subject": "Q3 Campaign Follow-up", "body": test_email},
                "I'll send the revised budget by Thursday",
                content_processor.ReplyStyle.PROFESSIONAL
            )
            print("  ✅ Email reply prompt generation")
            
            # Test content analysis
            metadata = content_processor.extract_email_metadata({
                "body": test_email,
                "subject": "Q3 Campaign Follow-up",
                "sender": "sarah@company.com"
            })
            print(f"  ✅ Content analysis: {metadata.sentiment} sentiment, {metadata.urgency_level} urgency")
            
            # Test voice optimization
            optimized = content_processor.optimize_for_voice(test_email, max_length=200)
            print(f"  ✅ Voice optimization: {len(optimized)} characters")
            
            # List all available tools
            print(f"\n📋 Available Tools ({len(agent.tools)}):")
            content_tool_names = [tool.name for tool in content_tools]
            
            for i, tool in enumerate(agent.tools, 1):
                tool_name = getattr(tool, 'name', str(tool))
                tool_type = "Content" if tool_name in content_tool_names else "Session"
                print(f"  {i}. {tool_name} ({tool_type})")
            
            print("\n✅ Content Agent validation completed successfully!")
            
        except Exception as e:
            print(f"❌ Error creating Content Agent: {e}")
            import traceback
            traceback.print_exc()
    
    # Run the test
    test_content_agent()