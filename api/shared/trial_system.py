"""
Anonymous Trial System for Sutra - Task 3.1
Implements guest access with conversion optimization, usage tracking, and seamless trial-to-paid conversion.
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)


@dataclass
class TrialSession:
    """Anonymous trial session data"""
    session_id: str
    created_at: datetime
    last_activity: datetime
    features_used: List[str]
    prompts_executed: int
    llm_calls_made: int
    cost_incurred: float
    conversion_events: List[Dict[str, Any]]
    trial_status: str  # "active", "expired", "converted", "churned"
    limitations_hit: List[str]
    user_agent: str
    source: str  # "direct", "referral", "search", etc.


@dataclass
class TrialLimitations:
    """Trial account limitations"""
    max_prompts_per_session: int = 10
    max_llm_calls_per_session: int = 25
    max_cost_per_session: float = 1.0
    max_session_duration_hours: int = 24
    allowed_features: List[str] = None
    blocked_features: List[str] = None
    
    def __post_init__(self):
        if self.allowed_features is None:
            self.allowed_features = [
                "basic_prompts",
                "simple_collections", 
                "limited_llm_access",
                "basic_analytics",
                "forge_idea_refinement"  # Limited Forge access
            ]
        if self.blocked_features is None:
            self.blocked_features = [
                "advanced_prompts",
                "premium_collections",
                "unlimited_llm_access", 
                "advanced_analytics",
                "full_forge_workflow",
                "team_collaboration",
                "api_access",
                "custom_integrations"
            ]


@dataclass
class ConversionEvent:
    """Conversion tracking event"""
    event_type: str  # "page_view", "feature_attempt", "limitation_hit", "signup_prompt", "conversion"
    timestamp: datetime
    data: Dict[str, Any]
    value_score: float  # Conversion likelihood impact


class AnonymousTrialSystem:
    """Manages anonymous trial sessions with conversion optimization"""
    
    def __init__(self):
        self.active_sessions: Dict[str, TrialSession] = {}
        self.trial_limitations = TrialLimitations()
        self.conversion_optimization = ConversionOptimizer()
    
    def create_trial_session(
        self, 
        user_agent: str = "", 
        source: str = "direct",
        referrer: str = ""
    ) -> TrialSession:
        """Create a new anonymous trial session"""
        try:
            session_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            session = TrialSession(
                session_id=session_id,
                created_at=now,
                last_activity=now,
                features_used=[],
                prompts_executed=0,
                llm_calls_made=0,
                cost_incurred=0.0,
                conversion_events=[],
                trial_status="active",
                limitations_hit=[],
                user_agent=user_agent,
                source=source
            )
            
            self.active_sessions[session_id] = session
            
            # Track session creation event
            self.track_conversion_event(
                session_id,
                "session_created",
                {"source": source, "referrer": referrer}
            )
            
            logger.info(f"Created trial session: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating trial session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[TrialSession]:
        """Get trial session by ID"""
        return self.active_sessions.get(session_id)
    
    def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity timestamp"""
        try:
            if session_id in self.active_sessions:
                self.active_sessions[session_id].last_activity = datetime.now(timezone.utc)
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
            return False
    
    def check_feature_access(self, session_id: str, feature: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a trial user can access a specific feature.
        Returns (allowed, limitation_reason)
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return False, "Invalid session"
            
            # Check if session is still active
            if session.trial_status != "active":
                return False, f"Session is {session.trial_status}"
            
            # Check session expiration
            if self._is_session_expired(session):
                session.trial_status = "expired"
                return False, "Trial session expired"
            
            # Check feature-specific limitations
            if feature in self.trial_limitations.blocked_features:
                self.track_conversion_event(
                    session_id,
                    "limitation_hit",
                    {"feature": feature, "reason": "premium_feature"}
                )
                return False, "Premium feature - upgrade required"
            
            # Check usage limitations
            limitation_reason = self._check_usage_limitations(session, feature)
            if limitation_reason:
                session.limitations_hit.append(limitation_reason)
                self.track_conversion_event(
                    session_id,
                    "limitation_hit", 
                    {"feature": feature, "reason": limitation_reason}
                )
                return False, limitation_reason
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking feature access: {e}")
            return False, "System error"
    
    def track_feature_usage(
        self, 
        session_id: str, 
        feature: str, 
        cost: float = 0.0,
        llm_calls: int = 0
    ) -> bool:
        """Track feature usage for trial analytics"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            # Update usage statistics
            if feature not in session.features_used:
                session.features_used.append(feature)
            
            if feature in ["prompt_execution", "llm_query"]:
                session.prompts_executed += 1
            
            session.llm_calls_made += llm_calls
            session.cost_incurred += cost
            session.last_activity = datetime.now(timezone.utc)
            
            # Track usage event for conversion optimization
            self.track_conversion_event(
                session_id,
                "feature_used",
                {
                    "feature": feature,
                    "cost": cost,
                    "llm_calls": llm_calls,
                    "total_usage": {
                        "prompts": session.prompts_executed,
                        "llm_calls": session.llm_calls_made,
                        "cost": session.cost_incurred
                    }
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking feature usage: {e}")
            return False
    
    def track_conversion_event(
        self, 
        session_id: str, 
        event_type: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Track conversion events for analytics"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            event = ConversionEvent(
                event_type=event_type,
                timestamp=datetime.now(timezone.utc),
                data=data,
                value_score=self.conversion_optimization.calculate_event_value(event_type, data)
            )
            
            session.conversion_events.append(asdict(event))
            
            # Trigger conversion optimization
            conversion_score = self.conversion_optimization.calculate_conversion_likelihood(session)
            if conversion_score > 0.7:  # High conversion likelihood
                self._trigger_conversion_optimization(session_id, conversion_score)
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking conversion event: {e}")
            return False
    
    def get_trial_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive trial session analytics"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {"error": "Session not found"}
            
            # Calculate session metrics
            session_duration = (datetime.now(timezone.utc) - session.created_at).total_seconds() / 3600
            conversion_score = self.conversion_optimization.calculate_conversion_likelihood(session)
            
            analytics = {
                "session_info": {
                    "session_id": session.session_id,
                    "created_at": session.created_at.isoformat(),
                    "duration_hours": round(session_duration, 2),
                    "status": session.trial_status,
                    "source": session.source
                },
                "usage_stats": {
                    "features_used": session.features_used,
                    "prompts_executed": session.prompts_executed,
                    "llm_calls_made": session.llm_calls_made,
                    "cost_incurred": round(session.cost_incurred, 4),
                    "limitations_hit": session.limitations_hit
                },
                "limitations": {
                    "prompts_remaining": max(0, self.trial_limitations.max_prompts_per_session - session.prompts_executed),
                    "llm_calls_remaining": max(0, self.trial_limitations.max_llm_calls_per_session - session.llm_calls_made),
                    "cost_remaining": max(0, self.trial_limitations.max_cost_per_session - session.cost_incurred)
                },
                "conversion": {
                    "likelihood_score": round(conversion_score, 3),
                    "events_tracked": len(session.conversion_events),
                    "optimization_triggers": len([e for e in session.conversion_events if e.get("event_type") == "conversion_prompt"])
                }
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting trial analytics: {e}")
            return {"error": str(e)}
    
    def _is_session_expired(self, session: TrialSession) -> bool:
        """Check if trial session has expired"""
        expiry_time = session.created_at + timedelta(hours=self.trial_limitations.max_session_duration_hours)
        return datetime.now(timezone.utc) > expiry_time
    
    def _check_usage_limitations(self, session: TrialSession, feature: str) -> Optional[str]:
        """Check if usage limitations are exceeded"""
        if session.prompts_executed >= self.trial_limitations.max_prompts_per_session:
            return f"Maximum prompts limit reached ({self.trial_limitations.max_prompts_per_session})"
        
        if session.llm_calls_made >= self.trial_limitations.max_llm_calls_per_session:
            return f"Maximum LLM calls limit reached ({self.trial_limitations.max_llm_calls_per_session})"
        
        if session.cost_incurred >= self.trial_limitations.max_cost_per_session:
            return f"Maximum cost limit reached (${self.trial_limitations.max_cost_per_session})"
        
        return None
    
    def _trigger_conversion_optimization(self, session_id: str, conversion_score: float):
        """Trigger conversion optimization for high-likelihood sessions"""
        try:
            # This would integrate with frontend to show conversion prompts
            self.track_conversion_event(
                session_id,
                "conversion_prompt",
                {
                    "trigger_score": conversion_score,
                    "message": "Your trial session shows high engagement! Consider upgrading for unlimited access."
                }
            )
            
            logger.info(f"Triggered conversion optimization for session {session_id} (score: {conversion_score})")
            
        except Exception as e:
            logger.error(f"Error triggering conversion optimization: {e}")


class ConversionOptimizer:
    """Optimizes trial-to-paid conversion using behavioral analytics"""
    
    def __init__(self):
        self.event_weights = {
            "session_created": 0.1,
            "feature_used": 0.3,
            "limitation_hit": 0.5,  # High value - user wants more
            "premium_feature_attempt": 0.7,
            "multiple_sessions": 0.6,
            "deep_engagement": 0.8
        }
    
    def calculate_event_value(self, event_type: str, data: Dict[str, Any]) -> float:
        """Calculate the conversion value of an event"""
        base_weight = self.event_weights.get(event_type, 0.1)
        
        # Adjust based on event data
        if event_type == "feature_used":
            # More valuable if using advanced features
            feature = data.get("feature", "")
            if "forge" in feature.lower():
                base_weight *= 1.5
            if "llm" in feature.lower():
                base_weight *= 1.3
        
        elif event_type == "limitation_hit":
            # Very valuable - user wants more than trial offers
            base_weight = 0.8
        
        return min(base_weight, 1.0)
    
    def calculate_conversion_likelihood(self, session: TrialSession) -> float:
        """Calculate the likelihood of conversion based on session data"""
        try:
            if not session.conversion_events:
                return 0.1
            
            # Base score from events
            event_score = sum(
                event.get("value_score", 0.1) 
                for event in session.conversion_events
            ) / len(session.conversion_events)
            
            # Engagement factors
            engagement_score = 0.0
            
            # Feature diversity (using multiple features indicates engagement)
            if len(session.features_used) > 3:
                engagement_score += 0.2
            
            # Usage intensity
            if session.prompts_executed > 5:
                engagement_score += 0.2
            
            # Time spent (longer sessions = higher engagement)
            session_duration = (datetime.now(timezone.utc) - session.created_at).total_seconds() / 3600
            if session_duration > 0.5:  # More than 30 minutes
                engagement_score += 0.1
            
            # Limitations hit (want more than trial offers)
            if session.limitations_hit:
                engagement_score += 0.3
            
            # Combine scores
            total_score = (event_score * 0.7) + (engagement_score * 0.3)
            
            return min(total_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating conversion likelihood: {e}")
            return 0.1


# Global trial system instance
trial_system = AnonymousTrialSystem()


def get_trial_system() -> AnonymousTrialSystem:
    """Get the global trial system instance"""
    return trial_system


def create_trial_session(user_agent: str = "", source: str = "direct") -> TrialSession:
    """Convenience function to create a trial session"""
    return trial_system.create_trial_session(user_agent, source)


def check_trial_access(session_id: str, feature: str) -> Tuple[bool, Optional[str]]:
    """Convenience function to check trial access"""
    return trial_system.check_feature_access(session_id, feature)


def track_trial_usage(session_id: str, feature: str, cost: float = 0.0, llm_calls: int = 0) -> bool:
    """Convenience function to track trial usage"""
    return trial_system.track_feature_usage(session_id, feature, cost, llm_calls)
