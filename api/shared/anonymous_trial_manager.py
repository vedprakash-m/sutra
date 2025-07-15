"""
Enhanced Guest User Manager for Anonymous Trial System (Task 3.1)
Implements comprehensive anonymous session management with trial limitations,
conversion tracking, and usage analytics.
"""
import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TrialLimits:
    """Trial limitations for anonymous users"""
    max_prompts_per_day: int = 10
    max_collections: int = 3
    max_playbooks: int = 2
    max_forge_projects: int = 1
    max_session_duration_hours: int = 24
    allowed_llm_providers: List[str] = None
    max_tokens_per_request: int = 1000
    
    def __post_init__(self):
        if self.allowed_llm_providers is None:
            self.allowed_llm_providers = ['openai']  # Only allow OpenAI for trials


@dataclass
class TrialUsage:
    """Track trial usage for conversion optimization"""
    prompts_used: int = 0
    collections_created: int = 0
    playbooks_created: int = 0
    forge_projects_created: int = 0
    session_start_time: datetime = None
    last_activity: datetime = None
    feature_interactions: Dict[str, int] = None
    conversion_triggers: List[str] = None
    
    def __post_init__(self):
        if self.session_start_time is None:
            self.session_start_time = datetime.utcnow()
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()
        if self.feature_interactions is None:
            self.feature_interactions = {}
        if self.conversion_triggers is None:
            self.conversion_triggers = []


@dataclass
class ConversionEvent:
    """Track conversion events and opportunities"""
    event_type: str  # 'limit_reached', 'feature_request', 'time_spent', 'manual_upgrade'
    timestamp: datetime
    feature_context: str
    user_journey_stage: str
    conversion_value: float  # Estimated value of conversion
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AnonymousTrialManager:
    """
    Enhanced manager for anonymous trial system with conversion optimization.
    Implements Task 3.1 requirements for anonymous session management,
    limited feature access, conversion tracking, and trial usage analytics.
    """
    
    def __init__(self, database_manager=None):
        self.database_manager = database_manager
        self.trial_limits = TrialLimits()
        self.conversion_events = []
        self.active_sessions = {}  # In-memory session cache
    
    def create_anonymous_session(
        self, 
        source: str = 'web',
        referrer: str = None,
        utm_params: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Create new anonymous trial session with tracking.
        
        Args:
            source: Source of the session (web, mobile, api)
            referrer: HTTP referrer for tracking
            utm_params: UTM parameters for conversion tracking
        
        Returns:
            Dictionary containing session details and trial limits
        """
        try:
            session_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            session_data = {
                "session_id": session_id,
                "user_type": "anonymous_trial",
                "created_at": current_time.isoformat(),
                "expires_at": (current_time + timedelta(hours=self.trial_limits.max_session_duration_hours)).isoformat(),
                "source": source,
                "referrer": referrer,
                "utm_params": utm_params or {},
                "trial_limits": {
                    "max_prompts_per_day": self.trial_limits.max_prompts_per_day,
                    "max_collections": self.trial_limits.max_collections,
                    "max_playbooks": self.trial_limits.max_playbooks,
                    "max_forge_projects": self.trial_limits.max_forge_projects,
                    "allowed_llm_providers": self.trial_limits.allowed_llm_providers,
                    "max_tokens_per_request": self.trial_limits.max_tokens_per_request
                },
                "usage": {
                    "prompts_used": 0,
                    "collections_created": 0,
                    "playbooks_created": 0,
                    "forge_projects_created": 0,
                    "feature_interactions": {},
                    "conversion_triggers": []
                },
                "conversion_score": 0.0,
                "status": "active"
            }
            
            # Store in database if available
            if self.database_manager:
                container = self.database_manager.get_container("TrialSessions")
                container.upsert_item(session_data)
            
            # Cache in memory
            self.active_sessions[session_id] = session_data
            
            logger.info(f"Created anonymous trial session: {session_id}")
            return session_data
            
        except Exception as e:
            logger.error(f"Error creating anonymous session: {str(e)}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve and validate anonymous session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session data if valid, None if expired or invalid
        """
        try:
            # Check memory cache first
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
            else:
                # Query database
                if self.database_manager:
                    container = self.database_manager.get_container("TrialSessions")
                    try:
                        session = container.read_item(session_id, partition_key=session_id)
                    except:
                        return None
                else:
                    return None
            
            # Check if session is expired
            expires_at = datetime.fromisoformat(session['expires_at'])
            if datetime.utcnow() > expires_at:
                self._expire_session(session_id)
                return None
            
            # Update last activity
            session['last_activity'] = datetime.utcnow().isoformat()
            self._update_session(session_id, session)
            
            return session
            
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {str(e)}")
            return None
    
    def check_trial_limit(
        self, 
        session_id: str, 
        feature: str, 
        requested_amount: int = 1
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Check if trial user can perform an action within limits.
        
        Args:
            session_id: Session identifier
            feature: Feature being accessed (prompts, collections, playbooks, forge_projects)
            requested_amount: Amount being requested (default 1)
        
        Returns:
            Tuple of (allowed: bool, reason: str, conversion_opportunity: dict)
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return False, "Invalid or expired session", {}
            
            usage = session.get('usage', {})
            limits = session.get('trial_limits', {})
            
            # Check specific feature limits
            if feature == 'prompts':
                current_usage = usage.get('prompts_used', 0)
                limit = limits.get('max_prompts_per_day', self.trial_limits.max_prompts_per_day)
                
                if current_usage + requested_amount > limit:
                    conversion_opp = self._create_conversion_opportunity(
                        session_id, 'prompt_limit_reached', 
                        f"User attempted to use {current_usage + requested_amount} prompts (limit: {limit})"
                    )
                    return False, f"Daily prompt limit reached ({limit})", conversion_opp
            
            elif feature == 'collections':
                current_usage = usage.get('collections_created', 0)
                limit = limits.get('max_collections', self.trial_limits.max_collections)
                
                if current_usage + requested_amount > limit:
                    conversion_opp = self._create_conversion_opportunity(
                        session_id, 'collection_limit_reached',
                        f"User attempted to create collection #{current_usage + requested_amount} (limit: {limit})"
                    )
                    return False, f"Collection limit reached ({limit})", conversion_opp
            
            elif feature == 'playbooks':
                current_usage = usage.get('playbooks_created', 0)
                limit = limits.get('max_playbooks', self.trial_limits.max_playbooks)
                
                if current_usage + requested_amount > limit:
                    conversion_opp = self._create_conversion_opportunity(
                        session_id, 'playbook_limit_reached',
                        f"User attempted to create playbook #{current_usage + requested_amount} (limit: {limit})"
                    )
                    return False, f"Playbook limit reached ({limit})", conversion_opp
            
            elif feature == 'forge_projects':
                current_usage = usage.get('forge_projects_created', 0)
                limit = limits.get('max_forge_projects', self.trial_limits.max_forge_projects)
                
                if current_usage + requested_amount > limit:
                    conversion_opp = self._create_conversion_opportunity(
                        session_id, 'forge_limit_reached',
                        f"User attempted to create Forge project #{current_usage + requested_amount} (limit: {limit})"
                    )
                    return False, f"Forge project limit reached ({limit})", conversion_opp
            
            elif feature == 'llm_tokens':
                limit = limits.get('max_tokens_per_request', self.trial_limits.max_tokens_per_request)
                
                if requested_amount > limit:
                    conversion_opp = self._create_conversion_opportunity(
                        session_id, 'token_limit_reached',
                        f"User requested {requested_amount} tokens (limit: {limit})"
                    )
                    return False, f"Token limit per request exceeded ({limit})", conversion_opp
            
            return True, "Within limits", {}
            
        except Exception as e:
            logger.error(f"Error checking trial limit for {session_id}: {str(e)}")
            return False, "Error checking limits", {}
    
    def record_usage(
        self, 
        session_id: str, 
        feature: str, 
        amount: int = 1,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Record trial usage for analytics and limit tracking.
        
        Args:
            session_id: Session identifier
            feature: Feature used
            amount: Amount used
            metadata: Additional context
        
        Returns:
            Success status
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            usage = session.get('usage', {})
            
            # Update usage counters
            if feature == 'prompts':
                usage['prompts_used'] = usage.get('prompts_used', 0) + amount
            elif feature == 'collections':
                usage['collections_created'] = usage.get('collections_created', 0) + amount
            elif feature == 'playbooks':
                usage['playbooks_created'] = usage.get('playbooks_created', 0) + amount
            elif feature == 'forge_projects':
                usage['forge_projects_created'] = usage.get('forge_projects_created', 0) + amount
            
            # Track feature interactions
            interactions = usage.get('feature_interactions', {})
            interactions[feature] = interactions.get(feature, 0) + amount
            usage['feature_interactions'] = interactions
            
            # Update session
            session['usage'] = usage
            session['last_activity'] = datetime.utcnow().isoformat()
            
            # Calculate conversion score
            session['conversion_score'] = self._calculate_conversion_score(session)
            
            self._update_session(session_id, session)
            
            # Check for conversion triggers
            self._check_conversion_triggers(session_id, feature, usage)
            
            logger.info(f"Recorded usage for {session_id}: {feature} +{amount}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording usage for {session_id}: {str(e)}")
            return False
    
    def get_conversion_opportunities(self, session_id: str) -> List[ConversionEvent]:
        """
        Get conversion opportunities for a trial session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            List of conversion events/opportunities
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return []
            
            opportunities = []
            usage = session.get('usage', {})
            limits = session.get('trial_limits', {})
            
            # Check usage-based opportunities
            for feature, current_usage in usage.items():
                if feature.endswith('_created') or feature.endswith('_used'):
                    feature_name = feature.replace('_created', '').replace('_used', '')
                    limit_key = f'max_{feature_name}_per_day' if 'prompts' in feature else f'max_{feature_name}'
                    limit = limits.get(limit_key, 0)
                    
                    if current_usage >= limit * 0.8:  # 80% of limit reached
                        opportunity = ConversionEvent(
                            event_type='approaching_limit',
                            timestamp=datetime.utcnow(),
                            feature_context=feature_name,
                            user_journey_stage='engaged_user',
                            conversion_value=self._estimate_conversion_value(feature_name, current_usage),
                            metadata={'current_usage': current_usage, 'limit': limit}
                        )
                        opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error getting conversion opportunities for {session_id}: {str(e)}")
            return []
    
    def get_trial_analytics(self, session_id: str = None) -> Dict[str, Any]:
        """
        Get trial usage analytics for optimization.
        
        Args:
            session_id: Specific session ID, or None for aggregate analytics
        
        Returns:
            Analytics data
        """
        try:
            if session_id:
                # Session-specific analytics
                session = self.get_session(session_id)
                if not session:
                    return {}
                
                usage = session.get('usage', {})
                session_start = datetime.fromisoformat(session['created_at'])
                session_duration = (datetime.utcnow() - session_start).total_seconds() / 3600  # hours
                
                return {
                    "session_id": session_id,
                    "session_duration_hours": round(session_duration, 2),
                    "usage_summary": usage,
                    "conversion_score": session.get('conversion_score', 0),
                    "feature_engagement": self._calculate_feature_engagement(usage),
                    "conversion_opportunities": len(self.get_conversion_opportunities(session_id)),
                    "user_journey_stage": self._determine_user_journey_stage(session),
                    "estimated_conversion_value": self._estimate_total_conversion_value(session)
                }
            else:
                # Aggregate analytics
                if self.database_manager:
                    return self._get_aggregate_analytics()
                else:
                    return {"error": "Database not available for aggregate analytics"}
                    
        except Exception as e:
            logger.error(f"Error getting trial analytics: {str(e)}")
            return {"error": str(e)}
    
    def extend_trial(self, session_id: str, hours: int = 24) -> bool:
        """
        Extend trial session duration (for conversion optimization).
        
        Args:
            session_id: Session identifier
            hours: Hours to extend
        
        Returns:
            Success status
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            current_expires = datetime.fromisoformat(session['expires_at'])
            new_expires = current_expires + timedelta(hours=hours)
            session['expires_at'] = new_expires.isoformat()
            
            self._update_session(session_id, session)
            
            logger.info(f"Extended trial session {session_id} by {hours} hours")
            return True
            
        except Exception as e:
            logger.error(f"Error extending trial {session_id}: {str(e)}")
            return False
    
    def convert_to_paid(self, session_id: str, user_id: str, plan: str) -> Dict[str, Any]:
        """
        Convert trial session to paid user account.
        
        Args:
            session_id: Trial session ID
            user_id: New user account ID
            plan: Subscription plan
        
        Returns:
            Conversion result with analytics
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return {"success": False, "error": "Invalid session"}
            
            # Record conversion event
            conversion_event = ConversionEvent(
                event_type='trial_converted',
                timestamp=datetime.utcnow(),
                feature_context='subscription',
                user_journey_stage='converted',
                conversion_value=self._get_plan_value(plan),
                metadata={
                    'trial_session_id': session_id,
                    'user_id': user_id,
                    'plan': plan,
                    'trial_usage': session.get('usage', {}),
                    'conversion_score': session.get('conversion_score', 0)
                }
            )
            
            # Update session status
            session['status'] = 'converted'
            session['converted_at'] = datetime.utcnow().isoformat()
            session['converted_to_user'] = user_id
            session['subscription_plan'] = plan
            
            self._update_session(session_id, session)
            
            # Record conversion analytics
            if self.database_manager:
                container = self.database_manager.get_container("ConversionEvents")
                container.create_item(conversion_event.__dict__)
            
            logger.info(f"Converted trial session {session_id} to paid user {user_id}")
            
            return {
                "success": True,
                "conversion_event": conversion_event.__dict__,
                "trial_analytics": self.get_trial_analytics(session_id)
            }
            
        except Exception as e:
            logger.error(f"Error converting trial {session_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # Private helper methods
    
    def _update_session(self, session_id: str, session_data: Dict[str, Any]):
        """Update session in database and cache"""
        try:
            if self.database_manager:
                container = self.database_manager.get_container("TrialSessions")
                container.upsert_item(session_data)
            
            self.active_sessions[session_id] = session_data
            
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {str(e)}")
    
    def _expire_session(self, session_id: str):
        """Mark session as expired"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session['status'] = 'expired'
                self._update_session(session_id, session)
                del self.active_sessions[session_id]
                
        except Exception as e:
            logger.error(f"Error expiring session {session_id}: {str(e)}")
    
    def _create_conversion_opportunity(
        self, 
        session_id: str, 
        event_type: str, 
        context: str
    ) -> Dict[str, Any]:
        """Create conversion opportunity data"""
        return {
            "type": "conversion_opportunity",
            "event_type": event_type,
            "session_id": session_id,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
            "suggested_action": self._get_suggested_conversion_action(event_type),
            "estimated_value": self._estimate_conversion_value(event_type.split('_')[0], 1)
        }
    
    def _calculate_conversion_score(self, session: Dict[str, Any]) -> float:
        """Calculate conversion likelihood score (0-100)"""
        try:
            usage = session.get('usage', {})
            session_start = datetime.fromisoformat(session['created_at'])
            session_age_hours = (datetime.utcnow() - session_start).total_seconds() / 3600
            
            score = 0.0
            
            # Usage-based scoring
            prompts_used = usage.get('prompts_used', 0)
            collections_created = usage.get('collections_created', 0)
            playbooks_created = usage.get('playbooks_created', 0)
            forge_projects = usage.get('forge_projects_created', 0)
            
            # Heavy usage indicates higher conversion likelihood
            score += min(prompts_used * 2, 30)  # Max 30 points for prompts
            score += min(collections_created * 10, 25)  # Max 25 points for collections
            score += min(playbooks_created * 15, 25)  # Max 25 points for playbooks
            score += min(forge_projects * 20, 20)  # Max 20 points for Forge projects
            
            # Time spent indicates engagement
            if session_age_hours > 1:
                score += min(session_age_hours * 2, 20)  # Max 20 points for time
            
            # Feature diversity indicates serious usage
            unique_features = len([f for f in usage.get('feature_interactions', {}) if usage['feature_interactions'][f] > 0])
            score += unique_features * 5  # 5 points per unique feature used
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating conversion score: {str(e)}")
            return 0.0
    
    def _check_conversion_triggers(self, session_id: str, feature: str, usage: Dict[str, Any]):
        """Check for conversion trigger events"""
        try:
            # Example triggers:
            # - User hits 80% of any limit
            # - User spends more than 2 hours in session
            # - User creates multiple items of same type
            # - User tries to access premium features
            
            limits = self.trial_limits
            
            if feature == 'prompts' and usage.get('prompts_used', 0) >= limits.max_prompts_per_day * 0.8:
                self._trigger_conversion_event(session_id, 'prompt_usage_high')
            
            elif feature == 'forge_projects' and usage.get('forge_projects_created', 0) >= 1:
                self._trigger_conversion_event(session_id, 'forge_engagement')
                
        except Exception as e:
            logger.error(f"Error checking conversion triggers: {str(e)}")
    
    def _trigger_conversion_event(self, session_id: str, trigger_type: str):
        """Trigger a conversion event"""
        logger.info(f"Conversion trigger: {trigger_type} for session {session_id}")
        # This would integrate with marketing automation, email campaigns, etc.
    
    def _calculate_feature_engagement(self, usage: Dict[str, Any]) -> Dict[str, float]:
        """Calculate engagement level for each feature"""
        engagement = {}
        
        # Calculate engagement based on usage patterns
        total_actions = sum(usage.get('feature_interactions', {}).values())
        
        if total_actions > 0:
            for feature, count in usage.get('feature_interactions', {}).items():
                engagement[feature] = round((count / total_actions) * 100, 2)
        
        return engagement
    
    def _determine_user_journey_stage(self, session: Dict[str, Any]) -> str:
        """Determine what stage the user is at in their journey"""
        usage = session.get('usage', {})
        conversion_score = session.get('conversion_score', 0)
        
        if conversion_score >= 80:
            return 'ready_to_convert'
        elif conversion_score >= 50:
            return 'highly_engaged'
        elif sum(usage.get('feature_interactions', {}).values()) >= 5:
            return 'actively_exploring'
        elif sum(usage.get('feature_interactions', {}).values()) >= 1:
            return 'initial_trial'
        else:
            return 'just_started'
    
    def _estimate_conversion_value(self, feature: str, usage_count: int) -> float:
        """Estimate conversion value based on feature usage"""
        feature_values = {
            'prompts': 2.0,    # $2 value per prompt used
            'collections': 15.0,  # $15 value per collection
            'playbooks': 25.0,    # $25 value per playbook
            'forge_projects': 50.0  # $50 value per Forge project
        }
        
        return feature_values.get(feature, 1.0) * usage_count
    
    def _estimate_total_conversion_value(self, session: Dict[str, Any]) -> float:
        """Estimate total conversion value for session"""
        usage = session.get('usage', {})
        total_value = 0.0
        
        total_value += self._estimate_conversion_value('prompts', usage.get('prompts_used', 0))
        total_value += self._estimate_conversion_value('collections', usage.get('collections_created', 0))
        total_value += self._estimate_conversion_value('playbooks', usage.get('playbooks_created', 0))
        total_value += self._estimate_conversion_value('forge_projects', usage.get('forge_projects_created', 0))
        
        return round(total_value, 2)
    
    def _get_suggested_conversion_action(self, event_type: str) -> str:
        """Get suggested action for conversion opportunity"""
        actions = {
            'prompt_limit_reached': 'Upgrade to Pro for unlimited prompts',
            'collection_limit_reached': 'Upgrade to access unlimited collections',
            'playbook_limit_reached': 'Upgrade for unlimited playbook creation',
            'forge_limit_reached': 'Upgrade to access unlimited Forge projects',
            'token_limit_reached': 'Upgrade for higher token limits'
        }
        
        return actions.get(event_type, 'Upgrade for full access to all features')
    
    def _get_plan_value(self, plan: str) -> float:
        """Get monetary value of subscription plan"""
        plan_values = {
            'pro_monthly': 29.0,
            'pro_yearly': 290.0,
            'team_monthly': 99.0,
            'team_yearly': 990.0,
            'enterprise': 500.0
        }
        
        return plan_values.get(plan, 29.0)
    
    def _get_aggregate_analytics(self) -> Dict[str, Any]:
        """Get aggregate analytics from database"""
        try:
            # This would query the database for aggregate statistics
            # For now, return placeholder data
            return {
                "total_trial_sessions": 0,
                "active_trials": 0,
                "conversion_rate": 0.0,
                "average_session_duration": 0.0,
                "most_used_features": [],
                "conversion_triggers": [],
                "revenue_from_conversions": 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting aggregate analytics: {str(e)}")
            return {"error": str(e)}


# Convenience functions for easy integration

def create_trial_session(source: str = 'web', referrer: str = None) -> Dict[str, Any]:
    """Create a new anonymous trial session"""
    manager = AnonymousTrialManager()
    return manager.create_anonymous_session(source=source, referrer=referrer)


def check_trial_access(session_id: str, feature: str, amount: int = 1) -> Tuple[bool, str, Dict[str, Any]]:
    """Check if trial user can access a feature"""
    manager = AnonymousTrialManager()
    return manager.check_trial_limit(session_id, feature, amount)


def record_trial_usage(session_id: str, feature: str, amount: int = 1) -> bool:
    """Record trial feature usage"""
    manager = AnonymousTrialManager()
    return manager.record_usage(session_id, feature, amount)


def get_trial_conversion_opportunities(session_id: str) -> List[ConversionEvent]:
    """Get conversion opportunities for trial session"""
    manager = AnonymousTrialManager()
    return manager.get_conversion_opportunities(session_id)
