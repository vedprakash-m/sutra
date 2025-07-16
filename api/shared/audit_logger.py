"""
Comprehensive Audit Logging System
Tracks all user actions, API calls, and security events for compliance
"""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional, Union

import azure.functions as func

# Set up logging
logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    BULK_OPERATION = "bulk_operation"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"
    API_CALL = "api_call"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    ERROR = "error"
    WARNING = "warning"


class AuditLevel(Enum):
    """Audit logging levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ComplianceStandard(Enum):
    """Compliance standards"""

    GDPR = "gdpr"
    SOC2 = "soc2"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"


@dataclass
class AuditEvent:
    """Individual audit event"""

    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    level: AuditLevel
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource_type: str
    resource_id: Optional[str]
    action: str
    status: str  # success, failure, error
    details: Dict[str, Any]
    compliance_flags: List[ComplianceStandard]
    risk_score: int  # 0-100

    # Security context
    authentication_method: Optional[str] = None
    authorization_context: Optional[Dict[str, Any]] = None

    # Data context
    data_classification: str = "unclassified"  # public, internal, confidential, restricted
    data_size: Optional[int] = None
    affected_records: Optional[int] = None

    # Performance context
    execution_time_ms: Optional[float] = None
    api_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    response_code: Optional[int] = None

    # Compliance context
    retention_period_days: int = 2555  # 7 years default
    gdpr_lawful_basis: Optional[str] = None
    data_subject_id: Optional[str] = None


@dataclass
class AuditQuery:
    """Query parameters for audit log search"""

    user_id: Optional[str] = None
    resource_type: Optional[str] = None
    event_type: Optional[AuditEventType] = None
    level: Optional[AuditLevel] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    compliance_standard: Optional[ComplianceStandard] = None
    risk_score_min: Optional[int] = None
    risk_score_max: Optional[int] = None
    ip_address: Optional[str] = None
    status: Optional[str] = None
    limit: int = 100
    offset: int = 0


class AuditLogger:
    """Comprehensive audit logging system"""

    def __init__(self, database_manager=None):
        self.database_manager = database_manager
        self.container_name = "audit_logs"
        self.session_store = {}  # In production, use Redis or similar

        # Compliance configurations
        self.compliance_config = {
            ComplianceStandard.GDPR: {
                "retention_days": 2555,  # 7 years
                "anonymization_required": True,
                "right_to_erasure": True,
                "data_portability": True,
            },
            ComplianceStandard.SOC2: {
                "retention_days": 2555,  # 7 years
                "access_logging": True,
                "change_management": True,
                "incident_response": True,
            },
            ComplianceStandard.HIPAA: {
                "retention_days": 2190,  # 6 years
                "access_controls": True,
                "audit_controls": True,
                "data_integrity": True,
            },
        }

        # Risk scoring weights
        self.risk_weights = {
            "admin_action": 30,
            "data_export": 25,
            "authentication_failure": 20,
            "privilege_escalation": 40,
            "data_modification": 15,
            "bulk_operation": 20,
            "after_hours": 10,
            "suspicious_ip": 25,
            "rapid_requests": 15,
        }

    async def log_event(self, event: AuditEvent) -> str:
        """Log an audit event"""
        try:
            # Generate unique event ID if not provided
            if not event.event_id:
                event.event_id = self._generate_event_id(event)

            # Calculate risk score
            event.risk_score = self._calculate_risk_score(event)

            # Add compliance flags
            event.compliance_flags = self._determine_compliance_flags(event)

            # Store in database
            if self.database_manager:
                await self._store_event(event)

            # Log to application log
            self._log_to_application(event)

            # Trigger alerts for high-risk events
            if event.risk_score >= 70:
                await self._trigger_security_alert(event)

            return event.event_id

        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            # Fallback logging to ensure audit trail continuity
            logger.critical(f"AUDIT_FAILURE: {json.dumps(asdict(event), default=str)}")
            raise

    async def _store_event(self, event: AuditEvent) -> None:
        """Store audit event in database"""
        try:
            event_data = asdict(event)
            # Convert datetime to string for JSON serialization
            event_data["timestamp"] = event.timestamp.isoformat()
            event_data["event_type"] = event.event_type.value
            event_data["level"] = event.level.value
            event_data["compliance_flags"] = [flag.value for flag in event.compliance_flags]

            await self.database_manager.create_item(container_name=self.container_name, item=event_data)

        except Exception as e:
            logger.error(f"Failed to store audit event in database: {str(e)}")
            # Continue with other logging mechanisms
            raise

    def _log_to_application(self, event: AuditEvent) -> None:
        """Log audit event to application logger"""
        log_message = (
            f"AUDIT [{event.level.value.upper()}] "
            f"User:{event.user_id} "
            f"Action:{event.action} "
            f"Resource:{event.resource_type}:{event.resource_id} "
            f"Status:{event.status} "
            f"Risk:{event.risk_score}"
        )

        if event.level == AuditLevel.CRITICAL:
            logger.critical(log_message)
        elif event.level == AuditLevel.ERROR:
            logger.error(log_message)
        elif event.level == AuditLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)

    def _generate_event_id(self, event: AuditEvent) -> str:
        """Generate unique event ID"""
        content = f"{event.timestamp.isoformat()}{event.user_id}{event.action}{event.resource_type}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _calculate_risk_score(self, event: AuditEvent) -> int:
        """Calculate risk score for event"""
        score = 0

        # Base score by event type
        base_scores = {
            AuditEventType.AUTHENTICATION: 10,
            AuditEventType.AUTHORIZATION: 15,
            AuditEventType.CREATE: 20,
            AuditEventType.READ: 5,
            AuditEventType.UPDATE: 25,
            AuditEventType.DELETE: 35,
            AuditEventType.BULK_OPERATION: 40,
            AuditEventType.CONFIGURATION_CHANGE: 45,
            AuditEventType.SECURITY_EVENT: 60,
            AuditEventType.DATA_EXPORT: 30,
            AuditEventType.ERROR: 20,
        }

        score += base_scores.get(event.event_type, 10)

        # Adjust for status
        if event.status == "failure":
            score += 20
        elif event.status == "error":
            score += 30

        # Adjust for data classification
        classification_scores = {"public": 0, "internal": 5, "confidential": 15, "restricted": 25}
        score += classification_scores.get(event.data_classification, 0)

        # Adjust for time of day (after hours = higher risk)
        if event.timestamp.hour < 6 or event.timestamp.hour > 22:
            score += self.risk_weights["after_hours"]

        # Adjust for admin actions
        if event.user_id and "admin" in event.user_id.lower():
            score += self.risk_weights["admin_action"]

        # Adjust for bulk operations
        if event.affected_records and event.affected_records > 100:
            score += self.risk_weights["bulk_operation"]

        # Cap at 100
        return min(score, 100)

    def _determine_compliance_flags(self, event: AuditEvent) -> List[ComplianceStandard]:
        """Determine which compliance standards apply to this event"""
        flags = []

        # GDPR applies to all personal data processing
        if self._involves_personal_data(event):
            flags.append(ComplianceStandard.GDPR)

        # SOC2 applies to system access and changes
        if event.event_type in [
            AuditEventType.AUTHENTICATION,
            AuditEventType.AUTHORIZATION,
            AuditEventType.CONFIGURATION_CHANGE,
            AuditEventType.SECURITY_EVENT,
        ]:
            flags.append(ComplianceStandard.SOC2)

        # Add other standards based on data classification and context
        if event.data_classification in ["confidential", "restricted"]:
            flags.append(ComplianceStandard.ISO27001)

        return flags

    def _involves_personal_data(self, event: AuditEvent) -> bool:
        """Check if event involves personal data processing"""
        # Check resource types that typically contain personal data
        personal_data_resources = ["user", "profile", "contact", "analytics", "prompt", "collection"]

        return any(resource in event.resource_type.lower() for resource in personal_data_resources)

    async def _trigger_security_alert(self, event: AuditEvent) -> None:
        """Trigger security alert for high-risk events"""
        alert_data = {
            "event_id": event.event_id,
            "risk_score": event.risk_score,
            "event_type": event.event_type.value,
            "user_id": event.user_id,
            "action": event.action,
            "timestamp": event.timestamp.isoformat(),
            "ip_address": event.ip_address,
        }

        # In production, send to SIEM, security team, etc.
        logger.critical(f"HIGH_RISK_SECURITY_EVENT: {json.dumps(alert_data)}")

    async def query_events(self, query: AuditQuery) -> List[AuditEvent]:
        """Query audit events with filters"""
        try:
            if not self.database_manager:
                return []

            # Build query conditions
            conditions = []
            parameters = {}

            if query.user_id:
                conditions.append("c.user_id = @user_id")
                parameters["@user_id"] = query.user_id

            if query.resource_type:
                conditions.append("c.resource_type = @resource_type")
                parameters["@resource_type"] = query.resource_type

            if query.event_type:
                conditions.append("c.event_type = @event_type")
                parameters["@event_type"] = query.event_type.value

            if query.start_date:
                conditions.append("c.timestamp >= @start_date")
                parameters["@start_date"] = query.start_date.isoformat()

            if query.end_date:
                conditions.append("c.timestamp <= @end_date")
                parameters["@end_date"] = query.end_date.isoformat()

            if query.risk_score_min:
                conditions.append("c.risk_score >= @risk_min")
                parameters["@risk_min"] = query.risk_score_min

            if query.risk_score_max:
                conditions.append("c.risk_score <= @risk_max")
                parameters["@risk_max"] = query.risk_score_max

            # Build SQL query
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            sql_query = f"""
                SELECT * FROM c
                WHERE {where_clause}
                ORDER BY c.timestamp DESC
                OFFSET {query.offset} LIMIT {query.limit}
            """

            # Execute query
            results = await self.database_manager.query_items(
                container_name=self.container_name, query=sql_query, parameters=parameters
            )

            # Convert back to AuditEvent objects
            events = []
            for item in results:
                # Convert string back to datetime
                item["timestamp"] = datetime.fromisoformat(item["timestamp"])
                item["event_type"] = AuditEventType(item["event_type"])
                item["level"] = AuditLevel(item["level"])
                item["compliance_flags"] = [ComplianceStandard(flag) for flag in item["compliance_flags"]]

                events.append(AuditEvent(**item))

            return events

        except Exception as e:
            logger.error(f"Failed to query audit events: {str(e)}")
            return []

    async def generate_compliance_report(
        self, standard: ComplianceStandard, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Generate compliance report for specific standard"""
        try:
            query = AuditQuery(
                compliance_standard=standard,
                start_date=start_date,
                end_date=end_date,
                limit=10000,  # Get all events for report
            )

            events = await self.query_events(query)

            report = {
                "standard": standard.value,
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "total_events": len(events),
                "summary": self._generate_compliance_summary(events, standard),
                "risk_analysis": self._analyze_risk_patterns(events),
                "recommendations": self._generate_compliance_recommendations(events, standard),
            }

            return report

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {str(e)}")
            return {}

    def _generate_compliance_summary(self, events: List[AuditEvent], standard: ComplianceStandard) -> Dict[str, Any]:
        """Generate summary for compliance report"""
        if not events:
            return {}

        summary = {
            "event_types": {},
            "user_activity": {},
            "high_risk_events": 0,
            "failed_operations": 0,
            "data_access_events": 0,
        }

        for event in events:
            # Count by event type
            event_type = event.event_type.value
            summary["event_types"][event_type] = summary["event_types"].get(event_type, 0) + 1

            # Count by user
            if event.user_id:
                summary["user_activity"][event.user_id] = summary["user_activity"].get(event.user_id, 0) + 1

            # Count high risk events
            if event.risk_score >= 70:
                summary["high_risk_events"] += 1

            # Count failed operations
            if event.status in ["failure", "error"]:
                summary["failed_operations"] += 1

            # Count data access events
            if event.event_type in [AuditEventType.READ, AuditEventType.DATA_EXPORT]:
                summary["data_access_events"] += 1

        return summary

    def _analyze_risk_patterns(self, events: List[AuditEvent]) -> Dict[str, Any]:
        """Analyze risk patterns in audit events"""
        if not events:
            return {}

        risk_analysis = {
            "average_risk_score": sum(event.risk_score for event in events) / len(events),
            "high_risk_users": [],
            "risk_trends": {},
            "security_incidents": 0,
        }

        # Analyze high-risk users
        user_risks = {}
        for event in events:
            if event.user_id:
                if event.user_id not in user_risks:
                    user_risks[event.user_id] = []
                user_risks[event.user_id].append(event.risk_score)

        for user_id, scores in user_risks.items():
            avg_risk = sum(scores) / len(scores)
            if avg_risk >= 50:
                risk_analysis["high_risk_users"].append(
                    {"user_id": user_id, "average_risk": avg_risk, "event_count": len(scores)}
                )

        # Count security incidents
        risk_analysis["security_incidents"] = sum(1 for event in events if event.event_type == AuditEventType.SECURITY_EVENT)

        return risk_analysis

    def _generate_compliance_recommendations(self, events: List[AuditEvent], standard: ComplianceStandard) -> List[str]:
        """Generate compliance recommendations based on audit data"""
        recommendations = []

        if not events:
            return ["No audit data available for analysis"]

        # Calculate metrics
        high_risk_events = sum(1 for event in events if event.risk_score >= 70)
        failed_events = sum(1 for event in events if event.status in ["failure", "error"])

        # Generate recommendations based on patterns
        if high_risk_events > len(events) * 0.05:  # More than 5% high-risk
            recommendations.append("Consider implementing additional access controls for high-risk operations")

        if failed_events > len(events) * 0.1:  # More than 10% failures
            recommendations.append("Review and improve error handling and user training")

        # Standard-specific recommendations
        if standard == ComplianceStandard.GDPR:
            personal_data_events = sum(1 for event in events if self._involves_personal_data(event))
            if personal_data_events > 0:
                recommendations.append("Ensure proper consent management for all personal data processing")
                recommendations.append("Implement data retention policies according to GDPR requirements")

        elif standard == ComplianceStandard.SOC2:
            admin_events = sum(1 for event in events if event.user_id and "admin" in event.user_id.lower())
            if admin_events > len(events) * 0.2:  # More than 20% admin events
                recommendations.append("Review administrator access patterns and implement least privilege principle")

        return recommendations


# Global audit logger instance
audit_logger = AuditLogger()


def audit_log(
    event_type: AuditEventType,
    action: str,
    resource_type: str,
    level: AuditLevel = AuditLevel.INFO,
    data_classification: str = "internal",
):
    """Decorator for automatic audit logging"""

    def decorator(func):
        @wraps(func)
        async def wrapper(req: func.HttpRequest, *args, **kwargs):
            start_time = datetime.now(timezone.utc)
            event = None

            try:
                # Extract request context
                user_id = req.headers.get("X-User-ID")
                session_id = req.headers.get("X-Session-ID")
                ip_address = req.headers.get("X-Forwarded-For", req.headers.get("X-Real-IP"))
                user_agent = req.headers.get("User-Agent")

                # Call the function
                result = await func(req, *args, **kwargs)

                # Determine status and resource ID from result
                status = "success"
                resource_id = None

                if hasattr(result, "status_code"):
                    if result.status_code >= 400:
                        status = "error"
                    elif result.status_code >= 300:
                        status = "warning"

                # Try to extract resource ID from result or request
                if hasattr(result, "get_body"):
                    try:
                        body = json.loads(result.get_body())
                        resource_id = body.get("id") or body.get("resource_id")
                    except:
                        pass

                # Calculate execution time
                execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

                # Create audit event
                event = AuditEvent(
                    event_id="",  # Will be generated
                    timestamp=start_time,
                    event_type=event_type,
                    level=level,
                    user_id=user_id,
                    session_id=session_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=action,
                    status=status,
                    details={
                        "method": req.method,
                        "url": req.url,
                        "headers": dict(req.headers) if hasattr(req, "headers") else {},
                    },
                    compliance_flags=[],  # Will be determined by logger
                    risk_score=0,  # Will be calculated by logger
                    execution_time_ms=execution_time,
                    api_endpoint=req.url,
                    http_method=req.method,
                    response_code=getattr(result, "status_code", 200),
                    data_classification=data_classification,
                )

                # Log the event
                await audit_logger.log_event(event)

                return result

            except Exception as e:
                # Log the error
                if not event:
                    event = AuditEvent(
                        event_id="",
                        timestamp=start_time,
                        event_type=AuditEventType.ERROR,
                        level=AuditLevel.ERROR,
                        user_id=req.headers.get("X-User-ID"),
                        session_id=req.headers.get("X-Session-ID"),
                        ip_address=req.headers.get("X-Forwarded-For"),
                        user_agent=req.headers.get("User-Agent"),
                        resource_type=resource_type,
                        resource_id=None,
                        action=action,
                        status="error",
                        details={"error": str(e)},
                        compliance_flags=[],
                        risk_score=0,
                        data_classification=data_classification,
                    )
                else:
                    event.status = "error"
                    event.level = AuditLevel.ERROR
                    event.details["error"] = str(e)

                await audit_logger.log_event(event)
                raise

        return wrapper

    return decorator
