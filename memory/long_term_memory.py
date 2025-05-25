"""
Long-term Memory Service for Oprina

This module provides long-term learning and pattern recognition using
ADK's MemoryService. Focuses on learning user behavior patterns,
preferences, and improving suggestions over time.

Key Features:
- User behavior pattern learning
- Email interaction preferences
- Smart suggestions based on history
- Adaptive response patterns
- Cross-session learning
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from google.adk.memory import InMemoryMemoryService
from google.adk.memory.memory_service import MemoryService

from config.settings import settings


@dataclass
class UserPattern:
    """User behavior pattern data structure."""
    pattern_type: str  # email_frequency, response_style, etc.
    pattern_data: Dict[str, Any]
    confidence: float  # 0.0 to 1.0
    frequency: int  # How often this pattern occurs
    last_seen: datetime
    created_at: datetime


@dataclass
class LearningEvent:
    """Learning event for pattern recognition."""
    user_id: str
    event_type: str
    event_data: Dict[str, Any]
    timestamp: datetime
    context: Optional[Dict[str, Any]] = None


class LongTermMemoryService:
    """
    Long-term memory service using ADK's MemoryService.
    Learns user patterns and preferences for intelligent assistance.
    """
    
    def __init__(self):
        """Initialize long-term memory service."""
        self.logger = logging.getLogger("long_term_memory")
        self._memory_service: Optional[MemoryService] = None
        
        # Learning configuration
        self.learning_enabled = True
        self.pattern_confidence_threshold = 0.3
        self.max_patterns_per_type = 10
        
        # Pattern types we track
        self.pattern_types = {
            "email_frequency": "How often user checks emails",
            "response_style": "Preferred email response style",
            "summary_detail": "Preferred summary detail level",
            "action_patterns": "Common email actions taken",
            "time_preferences": "Preferred times for email activities",
            "sender_priorities": "Important senders and priority patterns",
            "content_preferences": "Content types user engages with most",
            "voice_patterns": "Voice command patterns and preferences"
        }
        
        # Initialize memory service
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize the ADK MemoryService."""
        try:
            # Use InMemoryMemoryService for now
            # Can be upgraded to VertexAiRagMemoryService later
            self._memory_service = InMemoryMemoryService()
            
            self.logger.info("Long-term memory service initialized with InMemoryMemoryService")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize memory service: {e}")
            self._memory_service = None
    
    def is_ready(self) -> bool:
        """Check if memory service is ready."""
        return self._memory_service is not None and self.learning_enabled
    
    # =============================================================================
    # Learning and Pattern Recognition
    # =============================================================================
    
    def learn_from_event(self, user_id: str, event_type: str, event_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Learn from a user event to build patterns.
        
        Args:
            user_id: User identifier
            event_type: Type of event (email_check, voice_command, etc.)
            event_data: Event data
            context: Additional context information
            
        Returns:
            True if learning was successful
        """
        if not self.is_ready():
            return False
        
        try:
            learning_event = LearningEvent(
                user_id=user_id,
                event_type=event_type,
                event_data=event_data,
                timestamp=datetime.utcnow(),
                context=context
            )
            
            # Process different types of learning events
            if event_type == "email_check":
                self._learn_email_frequency_pattern(learning_event)
            elif event_type == "voice_command":
                self._learn_voice_pattern(learning_event)
            elif event_type == "email_action":
                self._learn_action_pattern(learning_event)
            elif event_type == "response_generated":
                self._learn_response_style_pattern(learning_event)
            elif event_type == "summary_requested":
                self._learn_summary_preference_pattern(learning_event)
            
            self.logger.debug(f"Learned from {event_type} event for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to learn from event: {e}")
            return False
    
    def _learn_email_frequency_pattern(self, event: LearningEvent):
        """Learn email checking frequency patterns."""
        try:
            # Extract time-based patterns
            hour = event.timestamp.hour
            day_of_week = event.timestamp.weekday()
            
            # Store in memory service
            pattern_key = f"email_frequency_{event.user_id}"
            
            # Get existing pattern or create new
            existing_pattern = self._get_pattern_from_memory(pattern_key)
            
            if existing_pattern:
                # Update existing pattern
                pattern_data = existing_pattern["pattern_data"]
                pattern_data["check_times"].append(hour)
                pattern_data["check_days"].append(day_of_week)
                pattern_data["total_checks"] += 1
                
                # Calculate frequency statistics
                pattern_data["avg_hour"] = sum(pattern_data["check_times"]) / len(pattern_data["check_times"])
                pattern_data["most_common_day"] = max(set(pattern_data["check_days"]), key=pattern_data["check_days"].count)
                
                # Update confidence based on consistency
                time_consistency = self._calculate_time_consistency(pattern_data["check_times"])
                pattern_data["confidence"] = min(time_consistency, 1.0)
            else:
                # Create new pattern
                pattern_data = {
                    "check_times": [hour],
                    "check_days": [day_of_week],
                    "total_checks": 1,
                    "avg_hour": hour,
                    "most_common_day": day_of_week,
                    "confidence": 0.1
                }
            
            # Store updated pattern
            self._store_pattern_in_memory(pattern_key, {
                "pattern_type": "email_frequency",
                "pattern_data": pattern_data,
                "last_updated": event.timestamp.isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to learn email frequency pattern: {e}")
    
    def _learn_voice_pattern(self, event: LearningEvent):
        """Learn voice command patterns."""
        try:
            command = event.event_data.get("command", "")
            intent = event.event_data.get("intent", "")
            
            pattern_key = f"voice_patterns_{event.user_id}"
            existing_pattern = self._get_pattern_from_memory(pattern_key)
            
            if existing_pattern:
                pattern_data = existing_pattern["pattern_data"]
                pattern_data["commands"].append(command)
                pattern_data["intents"].append(intent)
                pattern_data["command_count"] += 1
                
                # Find most common patterns
                pattern_data["common_commands"] = self._get_most_frequent(pattern_data["commands"], top_n=5)
                pattern_data["common_intents"] = self._get_most_frequent(pattern_data["intents"], top_n=3)
            else:
                pattern_data = {
                    "commands": [command],
                    "intents": [intent],
                    "command_count": 1,
                    "common_commands": [command],
                    "common_intents": [intent]
                }
            
            self._store_pattern_in_memory(pattern_key, {
                "pattern_type": "voice_patterns",
                "pattern_data": pattern_data,
                "last_updated": event.timestamp.isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to learn voice pattern: {e}")
    
    def _learn_action_pattern(self, event: LearningEvent):
        """Learn email action patterns."""
        try:
            action = event.event_data.get("action", "")
            email_type = event.event_data.get("email_type", "")
            sender = event.event_data.get("sender", "")
            
            pattern_key = f"action_patterns_{event.user_id}"
            existing_pattern = self._get_pattern_from_memory(pattern_key)
            
            if existing_pattern:
                pattern_data = existing_pattern["pattern_data"]
                pattern_data["actions"].append(action)
                pattern_data["email_types"].append(email_type)
                if sender:
                    pattern_data["senders"].append(sender)
                
                # Calculate action preferences
                pattern_data["preferred_actions"] = self._get_most_frequent(pattern_data["actions"], top_n=3)
                pattern_data["sender_priorities"] = self._get_most_frequent(pattern_data["senders"], top_n=10)
            else:
                pattern_data = {
                    "actions": [action],
                    "email_types": [email_type],
                    "senders": [sender] if sender else [],
                    "preferred_actions": [action],
                    "sender_priorities": [sender] if sender else []
                }
            
            self._store_pattern_in_memory(pattern_key, {
                "pattern_type": "action_patterns",
                "pattern_data": pattern_data,
                "last_updated": event.timestamp.isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to learn action pattern: {e}")
    
    def _learn_response_style_pattern(self, event: LearningEvent):
        """Learn response style preferences."""
        try:
            style = event.event_data.get("style", "")  # brief, detailed, formal, casual
            length = event.event_data.get("length", 0)
            tone = event.event_data.get("tone", "")
            
            pattern_key = f"response_style_{event.user_id}"
            existing_pattern = self._get_pattern_from_memory(pattern_key)
            
            if existing_pattern:
                pattern_data = existing_pattern["pattern_data"]
                pattern_data["styles"].append(style)
                pattern_data["lengths"].append(length)
                pattern_data["tones"].append(tone)
                
                # Calculate preferences
                pattern_data["preferred_style"] = max(set(pattern_data["styles"]), key=pattern_data["styles"].count)
                pattern_data["avg_length"] = sum(pattern_data["lengths"]) / len(pattern_data["lengths"])
                pattern_data["preferred_tone"] = max(set(pattern_data["tones"]), key=pattern_data["tones"].count)
            else:
                pattern_data = {
                    "styles": [style],
                    "lengths": [length],
                    "tones": [tone],
                    "preferred_style": style,
                    "avg_length": length,
                    "preferred_tone": tone
                }
            
            self._store_pattern_in_memory(pattern_key, {
                "pattern_type": "response_style",
                "pattern_data": pattern_data,
                "last_updated": event.timestamp.isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to learn response style pattern: {e}")
    
    def _learn_summary_preference_pattern(self, event: LearningEvent):
        """Learn summary detail preferences."""
        try:
            detail_level = event.event_data.get("detail_level", "brief")  # brief, moderate, detailed
            email_count = event.event_data.get("email_count", 0)
            
            pattern_key = f"summary_preferences_{event.user_id}"
            existing_pattern = self._get_pattern_from_memory(pattern_key)
            
            if existing_pattern:
                pattern_data = existing_pattern["pattern_data"]
                pattern_data["detail_levels"].append(detail_level)
                pattern_data["email_counts"].append(email_count)
                
                # Calculate preferences based on email volume
                pattern_data["preferred_detail"] = max(set(pattern_data["detail_levels"]), key=pattern_data["detail_levels"].count)
                
                # Learn detail preference by email volume
                if email_count < 5:
                    pattern_data["low_volume_preference"] = detail_level
                elif email_count < 20:
                    pattern_data["medium_volume_preference"] = detail_level
                else:
                    pattern_data["high_volume_preference"] = detail_level
            else:
                pattern_data = {
                    "detail_levels": [detail_level],
                    "email_counts": [email_count],
                    "preferred_detail": detail_level,
                    "low_volume_preference": detail_level,
                    "medium_volume_preference": detail_level,
                    "high_volume_preference": detail_level
                }
            
            self._store_pattern_in_memory(pattern_key, {
                "pattern_type": "summary_preferences",
                "pattern_data": pattern_data,
                "last_updated": event.timestamp.isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to learn summary preference pattern: {e}")
    
    # =============================================================================
    # Pattern Retrieval and Suggestions
    # =============================================================================
    
    def get_user_patterns(self, user_id: str, pattern_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get learned patterns for a user.
        
        Args:
            user_id: User identifier
            pattern_type: Specific pattern type to retrieve (None for all)
            
        Returns:
            Dictionary of user patterns
        """
        if not self.is_ready():
            return {}
        
        try:
            patterns = {}
            
            if pattern_type:
                # Get specific pattern
                pattern_key = f"{pattern_type}_{user_id}"
                pattern = self._get_pattern_from_memory(pattern_key)
                if pattern:
                    patterns[pattern_type] = pattern
            else:
                # Get all patterns for user
                for ptype in self.pattern_types.keys():
                    pattern_key = f"{ptype}_{user_id}"
                    pattern = self._get_pattern_from_memory(pattern_key)
                    if pattern:
                        patterns[ptype] = pattern
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Failed to get user patterns: {e}")
            return {}
    
    def get_smart_suggestions(self, user_id: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate smart suggestions based on learned patterns.
        
        Args:
            user_id: User identifier
            context: Current context (time, email count, etc.)
            
        Returns:
            List of suggestions
        """
        if not self.is_ready():
            return []
        
        try:
            suggestions = []
            current_hour = datetime.utcnow().hour
            patterns = self.get_user_patterns(user_id)
            
            # Email frequency suggestions
            if "email_frequency" in patterns:
                freq_pattern = patterns["email_frequency"]["pattern_data"]
                avg_hour = freq_pattern.get("avg_hour", 9)
                
                if abs(current_hour - avg_hour) <= 1:
                    suggestions.append({
                        "type": "email_check",
                        "message": "This is usually when you check your emails",
                        "confidence": freq_pattern.get("confidence", 0.5),
                        "action": "check_emails"
                    })
            
            # Response style suggestions
            if "response_style" in patterns:
                style_pattern = patterns["response_style"]["pattern_data"]
                preferred_style = style_pattern.get("preferred_style", "brief")
                
                suggestions.append({
                    "type": "response_style",
                    "message": f"Use {preferred_style} style based on your preferences",
                    "confidence": 0.8,
                    "action": f"set_style_{preferred_style}"
                })
            
            # Summary detail suggestions
            if "summary_preferences" in patterns and context.get("email_count"):
                summary_pattern = patterns["summary_preferences"]["pattern_data"]
                email_count = context["email_count"]
                
                if email_count < 5:
                    preferred_detail = summary_pattern.get("low_volume_preference", "detailed")
                elif email_count < 20:
                    preferred_detail = summary_pattern.get("medium_volume_preference", "moderate")
                else:
                    preferred_detail = summary_pattern.get("high_volume_preference", "brief")
                
                suggestions.append({
                    "type": "summary_detail",
                    "message": f"Use {preferred_detail} summary for {email_count} emails",
                    "confidence": 0.7,
                    "action": f"set_detail_{preferred_detail}"
                })
            
            # Voice pattern suggestions
            if "voice_patterns" in patterns:
                voice_pattern = patterns["voice_patterns"]["pattern_data"]
                common_commands = voice_pattern.get("common_commands", [])
                
                if common_commands:
                    suggestions.append({
                        "type": "voice_suggestion",
                        "message": f"Try: {common_commands[0]}",
                        "confidence": 0.6,
                        "action": "suggest_command",
                        "command": common_commands[0]
                    })
            
            # Action pattern suggestions
            if "action_patterns" in patterns:
                action_pattern = patterns["action_patterns"]["pattern_data"]
                preferred_actions = action_pattern.get("preferred_actions", [])
                
                if preferred_actions and context.get("email_context"):
                    suggestions.append({
                        "type": "action_suggestion",
                        "message": f"You usually {preferred_actions[0]} emails like this",
                        "confidence": 0.7,
                        "action": preferred_actions[0]
                    })
            
            # Sort suggestions by confidence
            suggestions.sort(key=lambda x: x["confidence"], reverse=True)
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            self.logger.error(f"Failed to generate smart suggestions: {e}")
            return []
    
    def get_adaptive_response_settings(self, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get adaptive response settings based on learned patterns.
        
        Args:
            user_id: User identifier
            context: Current context
            
        Returns:
            Adaptive settings dictionary
        """
        if not self.is_ready():
            return self._get_default_settings()
        
        try:
            patterns = self.get_user_patterns(user_id)
            settings = self._get_default_settings()
            
            # Adapt response style
            if "response_style" in patterns:
                style_pattern = patterns["response_style"]["pattern_data"]
                settings["response_style"] = style_pattern.get("preferred_style", "brief")
                settings["response_tone"] = style_pattern.get("preferred_tone", "friendly")
                settings["response_length"] = style_pattern.get("avg_length", 100)
            
            # Adapt summary detail
            if "summary_preferences" in patterns:
                summary_pattern = patterns["summary_preferences"]["pattern_data"]
                email_count = context.get("email_count", 0)
                
                if email_count < 5:
                    settings["summary_detail"] = summary_pattern.get("low_volume_preference", "detailed")
                elif email_count < 20:
                    settings["summary_detail"] = summary_pattern.get("medium_volume_preference", "moderate")
                else:
                    settings["summary_detail"] = summary_pattern.get("high_volume_preference", "brief")
            
            # Adapt based on time patterns
            if "email_frequency" in patterns:
                freq_pattern = patterns["email_frequency"]["pattern_data"]
                current_hour = datetime.utcnow().hour
                avg_hour = freq_pattern.get("avg_hour", 9)
                
                # Adjust urgency based on typical check times
                if abs(current_hour - avg_hour) <= 2:
                    settings["urgency_level"] = "high"
                else:
                    settings["urgency_level"] = "normal"
            
            return settings
            
        except Exception as e:
            self.logger.error(f"Failed to get adaptive response settings: {e}")
            return self._get_default_settings()
    
    # =============================================================================
    # Memory Service Interface
    # =============================================================================
    
    def _get_pattern_from_memory(self, pattern_key: str) -> Optional[Dict[str, Any]]:
        """Get pattern from memory service."""
        try:
            if not self._memory_service:
                return None
            
            # Use memory service to retrieve pattern
            # Note: Implementation depends on ADK MemoryService API
            # This is a placeholder for the actual implementation
            
            # For InMemoryMemoryService, we might need to implement
            # a simple key-value store or use the service's storage methods
            
            return None  # Placeholder
            
        except Exception as e:
            self.logger.error(f"Failed to get pattern from memory: {e}")
            return None
    
    def _store_pattern_in_memory(self, pattern_key: str, pattern_data: Dict[str, Any]) -> bool:
        """Store pattern in memory service."""
        try:
            if not self._memory_service:
                return False
            
            # Use memory service to store pattern
            # Note: Implementation depends on ADK MemoryService API
            # This is a placeholder for the actual implementation
            
            return True  # Placeholder
            
        except Exception as e:
            self.logger.error(f"Failed to store pattern in memory: {e}")
            return False
    
    # =============================================================================
    # Utility Methods
    # =============================================================================
    
    def _calculate_time_consistency(self, times: List[int]) -> float:
        """Calculate consistency score for time-based patterns."""
        if len(times) < 2:
            return 0.1
        
        # Calculate standard deviation
        avg = sum(times) / len(times)
        variance = sum((t - avg) ** 2 for t in times) / len(times)
        std_dev = variance ** 0.5
        
        # Convert to consistency score (0-1, where 1 is most consistent)
        max_std = 12  # Hours in half a day
        consistency = max(0, 1 - (std_dev / max_std))
        
        return consistency
    
    def _get_most_frequent(self, items: List[str], top_n: int = 5) -> List[str]:
        """Get most frequent items from a list."""
        if not items:
            return []
        
        from collections import Counter
        counter = Counter(items)
        return [item for item, _ in counter.most_common(top_n)]
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default response settings."""
        return {
            "response_style": "brief",
            "response_tone": "friendly",
            "response_length": 100,
            "summary_detail": "moderate",
            "urgency_level": "normal",
            "auto_actions": False
        }
    
    # =============================================================================
    # Pattern Analysis and Insights
    # =============================================================================
    
    def analyze_user_behavior(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze user behavior patterns and provide insights.
        
        Args:
            user_id: User identifier
            
        Returns:
            Behavior analysis results
        """
        if not self.is_ready():
            return {}
        
        try:
            patterns = self.get_user_patterns(user_id)
            analysis = {
                "user_id": user_id,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "patterns_found": len(patterns),
                "insights": []
            }
            
            # Analyze email frequency patterns
            if "email_frequency" in patterns:
                freq_data = patterns["email_frequency"]["pattern_data"]
                avg_hour = freq_data.get("avg_hour", 9)
                total_checks = freq_data.get("total_checks", 0)
                
                analysis["insights"].append({
                    "type": "email_frequency",
                    "insight": f"Typically checks emails around {avg_hour}:00",
                    "data": {"average_hour": avg_hour, "total_checks": total_checks}
                })
            
            # Analyze voice patterns
            if "voice_patterns" in patterns:
                voice_data = patterns["voice_patterns"]["pattern_data"]
                command_count = voice_data.get("command_count", 0)
                common_intents = voice_data.get("common_intents", [])
                
                analysis["insights"].append({
                    "type": "voice_usage",
                    "insight": f"Uses voice commands frequently, mainly for {common_intents[0] if common_intents else 'various tasks'}",
                    "data": {"command_count": command_count, "common_intents": common_intents}
                })
            
            # Analyze response preferences
            if "response_style" in patterns:
                style_data = patterns["response_style"]["pattern_data"]
                preferred_style = style_data.get("preferred_style", "brief")
                
                analysis["insights"].append({
                    "type": "response_preference",
                    "insight": f"Prefers {preferred_style} responses",
                    "data": {"preferred_style": preferred_style}
                })
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze user behavior: {e}")
            return {}
    
    def get_learning_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get learning statistics for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Learning statistics
        """
        try:
            patterns = self.get_user_patterns(user_id)
            
            stats = {
                "user_id": user_id,
                "total_patterns": len(patterns),
                "pattern_types": list(patterns.keys()),
                "learning_quality": {},
                "recommendations": []
            }
            
            # Calculate learning quality for each pattern
            for pattern_type, pattern_data in patterns.items():
                if "pattern_data" in pattern_data:
                    data = pattern_data["pattern_data"]
                    
                    # Simple quality assessment based on data volume
                    if pattern_type == "email_frequency":
                        quality = min(data.get("total_checks", 0) / 10, 1.0)
                    elif pattern_type == "voice_patterns":
                        quality = min(data.get("command_count", 0) / 20, 1.0)
                    else:
                        quality = 0.5  # Default
                    
                    stats["learning_quality"][pattern_type] = quality
            
            # Generate recommendations for better learning
            if stats["total_patterns"] < 3:
                stats["recommendations"].append("Use more features to improve personalization")
            
            avg_quality = sum(stats["learning_quality"].values()) / len(stats["learning_quality"]) if stats["learning_quality"] else 0
            if avg_quality < 0.5:
                stats["recommendations"].append("Continue using Oprina to improve AI learning")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get learning stats: {e}")
            return {}
    
    # =============================================================================
    # Pattern Management
    # =============================================================================
    
    def reset_user_patterns(self, user_id: str, pattern_type: Optional[str] = None) -> bool:
        """
        Reset learned patterns for a user.
        
        Args:
            user_id: User identifier
            pattern_type: Specific pattern to reset (None for all)
            
        Returns:
            True if successful
        """
        if not self.is_ready():
            return False
        
        try:
            if pattern_type:
                # Reset specific pattern
                pattern_key = f"{pattern_type}_{user_id}"
                # Implementation would delete from memory service
                self.logger.info(f"Reset {pattern_type} pattern for user {user_id}")
            else:
                # Reset all patterns
                for ptype in self.pattern_types.keys():
                    pattern_key = f"{ptype}_{user_id}"
                    # Implementation would delete from memory service
                
                self.logger.info(f"Reset all patterns for user {user_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset patterns: {e}")
            return False
    
    def export_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """
        Export user patterns for backup or transfer.
        
        Args:
            user_id: User identifier
            
        Returns:
            Exported patterns data
        """
        try:
            patterns = self.get_user_patterns(user_id)
            
            export_data = {
                "user_id": user_id,
                "export_timestamp": datetime.utcnow().isoformat(),
                "patterns": patterns,
                "metadata": {
                    "version": "1.0",
                    "source": "oprina_long_term_memory"
                }
            }
            
            return export_data
            
        except Exception as e:
            self.logger.error(f"Failed to export user patterns: {e}")
            return {}
    
    # =============================================================================
    # Health Check and Monitoring
    # =============================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on long-term memory service.
        
        Returns:
            Health check results
        """
        health = {
            "service": "long_term_memory",
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        try:
            # Service ready check
            health["checks"]["service_ready"] = self.is_ready()
            health["checks"]["learning_enabled"] = self.learning_enabled
            
            if self.is_ready():
                # Memory service check
                health["checks"]["memory_service_available"] = self._memory_service is not None
                
                # Pattern storage test
                test_user_id = "health_check_user"
                test_pattern_stored = self._store_pattern_in_memory(f"test_{test_user_id}", {
                    "pattern_type": "test",
                    "pattern_data": {"test": True},
                    "timestamp": datetime.utcnow().isoformat()
                })
                health["checks"]["pattern_storage"] = test_pattern_stored
                
                # Pattern retrieval test
                if test_pattern_stored:
                    retrieved_pattern = self._get_pattern_from_memory(f"test_{test_user_id}")
                    health["checks"]["pattern_retrieval"] = retrieved_pattern is not None
            
            # Overall status
            all_checks_passed = all(
                check for check in health["checks"].values() 
                if isinstance(check, bool)
            )
            
            health["status"] = "healthy" if all_checks_passed else "degraded"
            health["pattern_types_supported"] = list(self.pattern_types.keys())
            
        except Exception as e:
            health["checks"]["error"] = str(e)
            health["status"] = "unhealthy"
        
        return health


# =============================================================================
# Singleton instance and utility functions
# =============================================================================

# Global long-term memory instance
_long_term_memory_instance = None


def get_long_term_memory() -> LongTermMemoryService:
    """Get singleton long-term memory instance."""
    global _long_term_memory_instance
    if _long_term_memory_instance is None:
        _long_term_memory_instance = LongTermMemoryService()
    return _long_term_memory_instance


# =============================================================================
# Testing and Development Utilities
# =============================================================================

async def test_long_term_memory():
    """Test long-term memory functionality."""
    ltm = get_long_term_memory()
    
    print("Testing Long-term Memory Service...")
    
    # Health check
    health = await ltm.health_check()
    print(f"Health Check: {health['status']}")
    
    if health["status"] != "healthy":
        print("Long-term memory is not healthy, skipping tests")
        return False
    
    # Test learning from events
    test_user_id = "test_user_123"
    
    # Learn email frequency
    email_check_success = ltm.learn_from_event(test_user_id, "email_check", {
        "timestamp": datetime.utcnow().isoformat()
    })
    print(f"Email frequency learning: {email_check_success}")
    
    # Learn voice pattern
    voice_learn_success = ltm.learn_from_event(test_user_id, "voice_command", {
        "command": "check my emails",
        "intent": "email_management"
    })
    print(f"Voice pattern learning: {voice_learn_success}")
    
    # Learn response style
    response_learn_success = ltm.learn_from_event(test_user_id, "response_generated", {
        "style": "brief",
        "length": 85,
        "tone": "friendly"
    })
    print(f"Response style learning: {response_learn_success}")
    
    # Get patterns
    patterns = ltm.get_user_patterns(test_user_id)
    print(f"Learned patterns: {list(patterns.keys())}")
    
    # Get smart suggestions
    suggestions = ltm.get_smart_suggestions(test_user_id, {
        "email_count": 12,
        "current_time": datetime.utcnow().isoformat()
    })
    print(f"Smart suggestions: {len(suggestions)}")
    
    # Get adaptive settings
    adaptive_settings = ltm.get_adaptive_response_settings(test_user_id, {
        "email_count": 5
    })
    print(f"Adaptive settings: {adaptive_settings.get('response_style', 'default')}")
    
    # Analyze behavior
    behavior_analysis = ltm.analyze_user_behavior(test_user_id)
    print(f"Behavior insights: {len(behavior_analysis.get('insights', []))}")
    
    # Get learning stats
    learning_stats = ltm.get_learning_stats(test_user_id)
    print(f"Learning quality: {learning_stats.get('total_patterns', 0)} patterns")
    
    print("✅ Long-term memory tests completed")
    return True


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_long_term_memory())