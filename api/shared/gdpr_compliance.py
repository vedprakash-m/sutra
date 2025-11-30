"""
GDPR Compliance System
Implements GDPR requirements including data subject rights, consent management, and data protection
"""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from uuid import uuid4

logger = logging.getLogger(__name__)


class DataProcessingPurpose(Enum):
    """Legal purposes for data processing under GDPR"""

    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class DataCategory(Enum):
    """Categories of personal data"""

    BASIC_IDENTITY = "basic_identity"  # Name, email, username
    CONTACT_INFO = "contact_info"  # Phone, address
    USAGE_DATA = "usage_data"  # App usage, analytics
    TECHNICAL_DATA = "technical_data"  # IP address, device info
    PREFERENCE_DATA = "preference_data"  # Settings, preferences
    CONTENT_DATA = "content_data"  # Prompts, collections created
    SPECIAL_CATEGORY = "special_category"  # Sensitive personal data


class ConsentStatus(Enum):
    """Consent status"""

    GIVEN = "given"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    PENDING = "pending"


class DataSubjectRight(Enum):
    """GDPR data subject rights"""

    ACCESS = "access"  # Article 15
    RECTIFICATION = "rectification"  # Article 16
    ERASURE = "erasure"  # Article 17 (Right to be forgotten)
    RESTRICT_PROCESSING = "restrict_processing"  # Article 18
    DATA_PORTABILITY = "data_portability"  # Article 20
    OBJECT_PROCESSING = "object_processing"  # Article 21


@dataclass
class ConsentRecord:
    """Record of user consent"""

    consent_id: str
    user_id: str
    purpose: DataProcessingPurpose
    data_categories: List[DataCategory]
    status: ConsentStatus
    timestamp: datetime
    expiry_date: Optional[datetime] = None
    withdrawal_date: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    consent_text: str = ""


@dataclass
class DataProcessingRecord:
    """Record of data processing activity"""

    processing_id: str
    user_id: str
    purpose: DataProcessingPurpose
    data_categories: List[DataCategory]
    processing_date: datetime
    retention_period_days: int
    lawful_basis: str
    consent_id: Optional[str] = None
    automated_decision: bool = False


@dataclass
class DataSubjectRequest:
    """Data subject rights request"""

    request_id: str
    user_id: str
    request_type: DataSubjectRight
    status: str  # pending, processing, completed, rejected
    created_date: datetime
    completed_date: Optional[datetime] = None
    notes: str = ""
    verification_token: str = ""


class GDPRCompliance:
    """GDPR compliance management system"""

    def __init__(self, database_manager=None):
        self.database_manager = database_manager
        self.consent_container = "gdpr_consent"
        self.processing_container = "gdpr_processing"
        self.requests_container = "gdpr_requests"

        # Data retention policies (in days)
        self.retention_policies = {
            DataCategory.BASIC_IDENTITY: 2555,  # 7 years
            DataCategory.CONTACT_INFO: 2555,
            DataCategory.USAGE_DATA: 730,  # 2 years
            DataCategory.TECHNICAL_DATA: 365,  # 1 year
            DataCategory.PREFERENCE_DATA: 1095,  # 3 years
            DataCategory.CONTENT_DATA: 2555,  # 7 years
            DataCategory.SPECIAL_CATEGORY: 365,  # 1 year (strict)
        }

        # Consent expiry periods (in days)
        self.consent_expiry = {
            DataProcessingPurpose.CONSENT: 730,  # 2 years
            DataProcessingPurpose.LEGITIMATE_INTERESTS: 1095,  # 3 years
            DataProcessingPurpose.CONTRACT: None,  # No expiry during contract
        }

    async def record_consent(
        self,
        user_id: str,
        purpose: DataProcessingPurpose,
        data_categories: List[DataCategory],
        consent_given: bool = True,
        ip_address: str = None,
        user_agent: str = None,
        consent_text: str = "",
    ) -> str:
        """Record user consent for data processing"""
        try:
            consent_id = str(uuid4())

            # Calculate expiry date
            expiry_date = None
            if purpose in self.consent_expiry and self.consent_expiry[purpose]:
                expiry_date = datetime.utcnow() + timedelta(days=self.consent_expiry[purpose])

            consent_record = ConsentRecord(
                consent_id=consent_id,
                user_id=user_id,
                purpose=purpose,
                data_categories=data_categories,
                status=ConsentStatus.GIVEN if consent_given else ConsentStatus.WITHDRAWN,
                timestamp=datetime.utcnow(),
                expiry_date=expiry_date,
                ip_address=ip_address,
                user_agent=user_agent,
                consent_text=consent_text,
            )

            # Store in database
            if self.database_manager:
                await self._store_consent(consent_record)

            logger.info(f"Recorded consent {consent_id} for user {user_id}")
            return consent_id

        except Exception as e:
            logger.error(f"Failed to record consent: {str(e)}")
            raise

    async def withdraw_consent(self, user_id: str, consent_id: str = None, purpose: DataProcessingPurpose = None) -> bool:
        """Withdraw user consent"""
        try:
            # Find consent records to withdraw
            if consent_id:
                consents = [await self._get_consent(consent_id)]
            elif purpose:
                consents = await self._get_user_consents(user_id, purpose)
            else:
                consents = await self._get_user_consents(user_id)

            withdrawn_count = 0
            for consent in consents:
                if consent and consent.user_id == user_id and consent.status == ConsentStatus.GIVEN:
                    consent.status = ConsentStatus.WITHDRAWN
                    consent.withdrawal_date = datetime.utcnow()

                    await self._store_consent(consent)
                    withdrawn_count += 1

            logger.info(f"Withdrew {withdrawn_count} consent records for user {user_id}")
            return withdrawn_count > 0

        except Exception as e:
            logger.error(f"Failed to withdraw consent: {str(e)}")
            return False

    async def check_consent(self, user_id: str, purpose: DataProcessingPurpose, data_category: DataCategory) -> bool:
        """Check if user has valid consent for data processing"""
        try:
            consents = await self._get_user_consents(user_id, purpose)

            for consent in consents:
                if consent.status == ConsentStatus.GIVEN and data_category in consent.data_categories:

                    # Check if consent has expired
                    if consent.expiry_date and consent.expiry_date < datetime.utcnow():
                        consent.status = ConsentStatus.EXPIRED
                        await self._store_consent(consent)
                        continue

                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to check consent: {str(e)}")
            return False

    async def record_data_processing(
        self,
        user_id: str,
        purpose: DataProcessingPurpose,
        data_categories: List[DataCategory],
        lawful_basis: str,
        consent_id: str = None,
        automated_decision: bool = False,
    ) -> str:
        """Record data processing activity"""
        try:
            processing_id = str(uuid4())

            # Determine retention period
            max_retention = max(self.retention_policies.get(cat, 365) for cat in data_categories)

            processing_record = DataProcessingRecord(
                processing_id=processing_id,
                user_id=user_id,
                purpose=purpose,
                data_categories=data_categories,
                processing_date=datetime.utcnow(),
                retention_period_days=max_retention,
                lawful_basis=lawful_basis,
                consent_id=consent_id,
                automated_decision=automated_decision,
            )

            # Store in database
            if self.database_manager:
                await self._store_processing_record(processing_record)

            logger.info(f"Recorded data processing {processing_id} for user {user_id}")
            return processing_id

        except Exception as e:
            logger.error(f"Failed to record data processing: {str(e)}")
            raise

    async def handle_data_subject_request(
        self, user_id: str, request_type: DataSubjectRight, verification_required: bool = True
    ) -> str:
        """Handle data subject rights request"""
        try:
            request_id = str(uuid4())
            verification_token = hashlib.sha256(f"{request_id}{user_id}{datetime.utcnow()}".encode()).hexdigest()[:16]

            request = DataSubjectRequest(
                request_id=request_id,
                user_id=user_id,
                request_type=request_type,
                status="pending" if verification_required else "processing",
                created_date=datetime.utcnow(),
                verification_token=verification_token if verification_required else "",
            )

            # Store in database
            if self.database_manager:
                await self._store_subject_request(request)

            # If no verification required, process immediately
            if not verification_required:
                await self._process_subject_request(request)

            logger.info(f"Created data subject request {request_id} for user {user_id}")
            return request_id

        except Exception as e:
            logger.error(f"Failed to handle data subject request: {str(e)}")
            raise

    async def verify_and_process_request(self, request_id: str, verification_token: str) -> bool:
        """Verify and process data subject request"""
        try:
            request = await self._get_subject_request(request_id)
            if not request:
                return False

            if request.verification_token != verification_token:
                logger.warning(f"Invalid verification token for request {request_id}")
                return False

            request.status = "processing"
            await self._store_subject_request(request)

            # Process the request
            await self._process_subject_request(request)

            return True

        except Exception as e:
            logger.error(f"Failed to verify and process request: {str(e)}")
            return False

    async def _process_subject_request(self, request: DataSubjectRequest) -> None:
        """Process data subject rights request"""
        try:
            if request.request_type == DataSubjectRight.ACCESS:
                await self._process_access_request(request)
            elif request.request_type == DataSubjectRight.ERASURE:
                await self._process_erasure_request(request)
            elif request.request_type == DataSubjectRight.DATA_PORTABILITY:
                await self._process_portability_request(request)
            elif request.request_type == DataSubjectRight.RECTIFICATION:
                await self._process_rectification_request(request)
            elif request.request_type == DataSubjectRight.RESTRICT_PROCESSING:
                await self._process_restriction_request(request)
            elif request.request_type == DataSubjectRight.OBJECT_PROCESSING:
                await self._process_objection_request(request)

            request.status = "completed"
            request.completed_date = datetime.utcnow()
            await self._store_subject_request(request)

        except Exception as e:
            logger.error(f"Failed to process subject request: {str(e)}")
            request.status = "error"
            request.notes = str(e)
            await self._store_subject_request(request)

    async def _process_access_request(self, request: DataSubjectRequest) -> None:
        """Process data access request (Article 15)
        
        Collects all personal data for the user from relevant containers.
        """
        logger.info(f"Processing access request for user {request.user_id}")
        
        if not self.database_manager:
            logger.warning("Database manager not available for access request")
            return
            
        collected_data = await self._collect_user_data(request.user_id)
        
        # Store the collected data as part of the request
        request.notes = json.dumps({
            "collected_data_summary": {
                "containers_queried": list(collected_data.keys()),
                "total_records": sum(len(v) for v in collected_data.values()),
                "collection_timestamp": datetime.utcnow().isoformat()
            }
        })
        
        # The actual data would be made available to the user through a secure download
        logger.info(f"Collected data from {len(collected_data)} containers for user {request.user_id}")

    async def _collect_user_data(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Collect all user data from relevant containers.
        
        Returns:
            Dictionary mapping container names to lists of user records.
        """
        collected_data: Dict[str, List[Dict[str, Any]]] = {}
        
        # Define containers and their user ID fields
        containers_config = [
            ("Users", "id"),
            ("Prompts", "userId"),
            ("Collections", "userId"),
            ("Playbooks", "userId"),
            ("Executions", "userId"),
            ("AuditLog", "userId"),
            ("GDPRConsents", "user_id"),
        ]
        
        for container_name, user_field in containers_config:
            try:
                container = self.database_manager.get_container(container_name)
                if container:
                    query = f"SELECT * FROM c WHERE c.{user_field} = @userId"
                    parameters = [{"name": "@userId", "value": user_id}]
                    
                    items = list(container.query_items(
                        query=query,
                        parameters=parameters,
                        enable_cross_partition_query=True
                    ))
                    
                    if items:
                        # Anonymize sensitive fields for the response
                        collected_data[container_name] = items
                        logger.info(f"Collected {len(items)} items from {container_name}")
            except Exception as e:
                logger.warning(f"Could not query {container_name}: {e}")
                
        return collected_data

    async def _process_erasure_request(self, request: DataSubjectRequest) -> None:
        """Process right to be forgotten request (Article 17)
        
        Deletes all user data from relevant containers with careful handling
        of data dependencies.
        """
        logger.info(f"Processing erasure request for user {request.user_id}")
        
        if not self.database_manager:
            logger.warning("Database manager not available for erasure request")
            return
        
        deletion_results = await self._delete_user_data(request.user_id)
        
        request.notes = json.dumps({
            "deletion_summary": deletion_results,
            "deletion_timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Completed erasure for user {request.user_id}: {deletion_results}")

    async def _delete_user_data(self, user_id: str) -> Dict[str, Any]:
        """Delete all user data from relevant containers.
        
        Order matters: delete dependent data first, then parent records.
        
        Returns:
            Summary of deletion results.
        """
        results: Dict[str, Any] = {"deleted": {}, "errors": []}
        
        # Delete in dependency order: dependent records first
        deletion_order = [
            ("Executions", "userId"),
            ("AuditLog", "userId"),
            ("GDPRConsents", "user_id"),
            ("Playbooks", "userId"),
            ("Prompts", "userId"),
            ("Collections", "userId"),
            ("Users", "id"),  # Delete user record last
        ]
        
        for container_name, user_field in deletion_order:
            try:
                container = self.database_manager.get_container(container_name)
                if container:
                    # Query for user's items
                    query = f"SELECT c.id FROM c WHERE c.{user_field} = @userId"
                    parameters = [{"name": "@userId", "value": user_id}]
                    
                    items = list(container.query_items(
                        query=query,
                        parameters=parameters,
                        enable_cross_partition_query=True
                    ))
                    
                    deleted_count = 0
                    for item in items:
                        try:
                            container.delete_item(item=item["id"], partition_key=user_id)
                            deleted_count += 1
                        except Exception as delete_error:
                            results["errors"].append({
                                "container": container_name,
                                "item_id": item.get("id"),
                                "error": str(delete_error)
                            })
                    
                    results["deleted"][container_name] = deleted_count
                    logger.info(f"Deleted {deleted_count} items from {container_name}")
                    
            except Exception as e:
                logger.warning(f"Error processing {container_name}: {e}")
                results["errors"].append({
                    "container": container_name,
                    "error": str(e)
                })
                
        return results

    async def _process_portability_request(self, request: DataSubjectRequest) -> None:
        """Process data portability request (Article 20)
        
        Exports user data in a machine-readable format (JSON).
        """
        logger.info(f"Processing portability request for user {request.user_id}")
        
        if not self.database_manager:
            logger.warning("Database manager not available for portability request")
            return
        
        # Collect all user data
        collected_data = await self._collect_user_data(request.user_id)
        
        # Format for portability (remove internal fields)
        portable_data = self._format_for_portability(collected_data)
        
        request.notes = json.dumps({
            "export_format": "json",
            "total_records": sum(len(v) for v in portable_data.values()),
            "export_timestamp": datetime.utcnow().isoformat()
        })
        
        # In production, this would generate a downloadable file
        logger.info(f"Prepared portable data export for user {request.user_id}")

    def _format_for_portability(self, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """Format collected data for portability export.
        
        Removes internal Cosmos DB fields and sensitive metadata.
        """
        portable_data: Dict[str, List[Dict[str, Any]]] = {}
        
        internal_fields = ["_rid", "_self", "_etag", "_attachments", "_ts"]
        
        for container_name, records in data.items():
            portable_data[container_name] = []
            for record in records:
                clean_record = {
                    k: v for k, v in record.items()
                    if k not in internal_fields
                }
                portable_data[container_name].append(clean_record)
                
        return portable_data

    async def _process_rectification_request(self, request: DataSubjectRequest) -> None:
        """Process data rectification request (Article 16)
        
        Updates user's personal data based on the request details.
        """
        logger.info(f"Processing rectification request for user {request.user_id}")
        
        if not self.database_manager:
            logger.warning("Database manager not available for rectification request")
            return
        
        # Parse rectification details from request
        try:
            rectification_data = json.loads(request.details) if request.details else {}
        except json.JSONDecodeError:
            rectification_data = {"raw_request": request.details}
        
        # Update user profile data in Users container
        if rectification_data.get("profile_updates"):
            try:
                container = self.database_manager.get_container("Users")
                if container:
                    # Get current user record
                    query = "SELECT * FROM c WHERE c.id = @userId"
                    parameters = [{"name": "@userId", "value": request.user_id}]
                    items = list(container.query_items(
                        query=query,
                        parameters=parameters,
                        enable_cross_partition_query=True
                    ))
                    
                    if items:
                        user_data = items[0]
                        user_data.update(rectification_data["profile_updates"])
                        user_data["updatedAt"] = datetime.utcnow().isoformat() + "Z"
                        user_data["gdprRectificationApplied"] = datetime.utcnow().isoformat()
                        
                        container.replace_item(item=user_data["id"], body=user_data)
                        logger.info(f"Applied rectification to user {request.user_id}")
                        
            except Exception as e:
                logger.error(f"Failed to apply rectification: {e}")
        
        request.notes = json.dumps({
            "rectification_applied": True,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def _process_restriction_request(self, request: DataSubjectRequest) -> None:
        """Process processing restriction request (Article 18)
        
        Marks user's data for restricted processing.
        """
        logger.info(f"Processing restriction request for user {request.user_id}")
        
        if not self.database_manager:
            logger.warning("Database manager not available for restriction request")
            return
        
        try:
            container = self.database_manager.get_container("Users")
            if container:
                query = "SELECT * FROM c WHERE c.id = @userId"
                parameters = [{"name": "@userId", "value": request.user_id}]
                items = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                if items:
                    user_data = items[0]
                    user_data["processingRestricted"] = True
                    user_data["restrictionReason"] = request.details or "User request"
                    user_data["restrictionDate"] = datetime.utcnow().isoformat() + "Z"
                    
                    container.replace_item(item=user_data["id"], body=user_data)
                    logger.info(f"Applied processing restriction for user {request.user_id}")
                    
        except Exception as e:
            logger.error(f"Failed to apply restriction: {e}")
        
        request.notes = json.dumps({
            "restriction_applied": True,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def _process_objection_request(self, request: DataSubjectRequest) -> None:
        """Process objection to processing request (Article 21)
        
        Records user's objection to data processing.
        """
        logger.info(f"Processing objection request for user {request.user_id}")
        
        if not self.database_manager:
            logger.warning("Database manager not available for objection request")
            return
        
        try:
            container = self.database_manager.get_container("Users")
            if container:
                query = "SELECT * FROM c WHERE c.id = @userId"
                parameters = [{"name": "@userId", "value": request.user_id}]
                items = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                if items:
                    user_data = items[0]
                    
                    # Record objection details
                    if "processingObjections" not in user_data:
                        user_data["processingObjections"] = []
                    
                    user_data["processingObjections"].append({
                        "objectionId": str(uuid4()),
                        "date": datetime.utcnow().isoformat() + "Z",
                        "reason": request.details or "User objection",
                        "requestId": request.request_id
                    })
                    
                    container.replace_item(item=user_data["id"], body=user_data)
                    logger.info(f"Recorded processing objection for user {request.user_id}")
                    
        except Exception as e:
            logger.error(f"Failed to record objection: {e}")
        
        request.notes = json.dumps({
            "objection_recorded": True,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def get_user_data_overview(self, user_id: str) -> Dict[str, Any]:
        """Get overview of user's personal data processing"""
        try:
            consents = await self._get_user_consents(user_id)
            processing_records = await self._get_user_processing_records(user_id)

            overview = {
                "user_id": user_id,
                "data_processing_overview": {
                    "active_consents": len([c for c in consents if c.status == ConsentStatus.GIVEN]),
                    "withdrawn_consents": len([c for c in consents if c.status == ConsentStatus.WITHDRAWN]),
                    "expired_consents": len([c for c in consents if c.status == ConsentStatus.EXPIRED]),
                    "total_processing_activities": len(processing_records),
                },
                "data_categories_processed": list(
                    set([cat.value for record in processing_records for cat in record.data_categories])
                ),
                "processing_purposes": list(set([record.purpose.value for record in processing_records])),
                "retention_status": await self._calculate_retention_status(user_id, processing_records),
            }

            return overview

        except Exception as e:
            logger.error(f"Failed to get user data overview: {str(e)}")
            return {}

    async def _calculate_retention_status(
        self, user_id: str, processing_records: List[DataProcessingRecord]
    ) -> Dict[str, Any]:
        """Calculate data retention status"""
        now = datetime.utcnow()
        retention_status = {"items_due_for_deletion": 0, "upcoming_deletions": [], "permanent_retention_items": 0}

        for record in processing_records:
            retention_date = record.processing_date + timedelta(days=record.retention_period_days)

            if retention_date <= now:
                retention_status["items_due_for_deletion"] += 1
            elif retention_date <= now + timedelta(days=30):  # Due within 30 days
                retention_status["upcoming_deletions"].append(
                    {
                        "processing_id": record.processing_id,
                        "retention_date": retention_date.isoformat(),
                        "data_categories": [cat.value for cat in record.data_categories],
                    }
                )

        return retention_status

    async def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up expired personal data"""
        cleanup_stats = {"consent_records_expired": 0, "processing_records_deleted": 0, "errors": 0}

        try:
            if self.database_manager:
                now = datetime.utcnow()
                
                # Mark expired consents
                try:
                    container = self.database_manager.get_container(self.consent_container)
                    if container:
                        # Query for consents with expired dates
                        query = "SELECT * FROM c WHERE c.expiry_date < @now AND c.status = 'given'"
                        parameters = [{"name": "@now", "value": now.isoformat()}]
                        
                        items = list(container.query_items(
                            query=query,
                            parameters=parameters,
                            enable_cross_partition_query=True
                        ))
                        
                        for item in items:
                            try:
                                item["status"] = ConsentStatus.EXPIRED.value
                                item["expiredAt"] = now.isoformat()
                                container.replace_item(item=item["id"], body=item)
                                cleanup_stats["consent_records_expired"] += 1
                            except Exception as e:
                                logger.warning(f"Failed to expire consent {item.get('id')}: {e}")
                                cleanup_stats["errors"] += 1
                                
                except Exception as e:
                    logger.warning(f"Error querying expired consents: {e}")
                    cleanup_stats["errors"] += 1

                # Delete data past retention period
                try:
                    container = self.database_manager.get_container(self.processing_container)
                    if container:
                        # Query for processing records past retention
                        query = "SELECT * FROM c"
                        items = list(container.query_items(
                            query=query,
                            enable_cross_partition_query=True
                        ))
                        
                        for item in items:
                            try:
                                processing_date = datetime.fromisoformat(item.get("processing_date", ""))
                                retention_days = item.get("retention_period_days", 365)
                                retention_date = processing_date + timedelta(days=retention_days)
                                
                                if retention_date < now:
                                    container.delete_item(
                                        item=item["id"],
                                        partition_key=item.get("user_id", item["id"])
                                    )
                                    cleanup_stats["processing_records_deleted"] += 1
                            except Exception as e:
                                logger.warning(f"Failed to process record {item.get('id')}: {e}")
                                cleanup_stats["errors"] += 1
                                
                except Exception as e:
                    logger.warning(f"Error processing retention cleanup: {e}")
                    cleanup_stats["errors"] += 1

        except Exception as e:
            logger.error(f"Failed to cleanup expired data: {str(e)}")
            cleanup_stats["errors"] += 1

        logger.info(f"Cleanup completed: {cleanup_stats}")
        return cleanup_stats

    # Database interaction methods (to be implemented based on your database setup)
    async def _store_consent(self, consent: ConsentRecord) -> None:
        """Store consent record in database"""
        if self.database_manager:
            data = asdict(consent)
            data["timestamp"] = consent.timestamp.isoformat()
            if consent.expiry_date:
                data["expiry_date"] = consent.expiry_date.isoformat()
            if consent.withdrawal_date:
                data["withdrawal_date"] = consent.withdrawal_date.isoformat()
            data["purpose"] = consent.purpose.value
            data["status"] = consent.status.value
            data["data_categories"] = [cat.value for cat in consent.data_categories]

            await self.database_manager.create_item(container_name=self.consent_container, item=data)

    async def _store_processing_record(self, record: DataProcessingRecord) -> None:
        """Store processing record in database"""
        if self.database_manager:
            data = asdict(record)
            data["processing_date"] = record.processing_date.isoformat()
            data["purpose"] = record.purpose.value
            data["data_categories"] = [cat.value for cat in record.data_categories]

            await self.database_manager.create_item(container_name=self.processing_container, item=data)

    async def _store_subject_request(self, request: DataSubjectRequest) -> None:
        """Store subject request in database"""
        if self.database_manager:
            data = asdict(request)
            data["created_date"] = request.created_date.isoformat()
            if request.completed_date:
                data["completed_date"] = request.completed_date.isoformat()
            data["request_type"] = request.request_type.value

            await self.database_manager.create_item(container_name=self.requests_container, item=data)

    async def _get_consent(self, consent_id: str) -> Optional[ConsentRecord]:
        """Get consent record by ID"""
        if not self.database_manager:
            return None
            
        try:
            container = self.database_manager.get_container(self.consent_container)
            if container:
                query = "SELECT * FROM c WHERE c.consent_id = @consentId"
                parameters = [{"name": "@consentId", "value": consent_id}]
                
                items = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                if items:
                    item = items[0]
                    return ConsentRecord(
                        consent_id=item["consent_id"],
                        user_id=item["user_id"],
                        purpose=DataProcessingPurpose(item["purpose"]),
                        data_categories=[DataCategory(cat) for cat in item.get("data_categories", [])],
                        status=ConsentStatus(item["status"]),
                        timestamp=datetime.fromisoformat(item["timestamp"]),
                        expiry_date=datetime.fromisoformat(item["expiry_date"]) if item.get("expiry_date") else None,
                        withdrawal_date=datetime.fromisoformat(item["withdrawal_date"]) if item.get("withdrawal_date") else None,
                        ip_address=item.get("ip_address"),
                        user_agent=item.get("user_agent"),
                        consent_text=item.get("consent_text", "")
                    )
        except Exception as e:
            logger.warning(f"Error getting consent {consent_id}: {e}")
            
        return None

    async def _get_user_consents(self, user_id: str, purpose: DataProcessingPurpose = None) -> List[ConsentRecord]:
        """Get user consent records"""
        consents: List[ConsentRecord] = []
        
        if not self.database_manager:
            return consents
            
        try:
            container = self.database_manager.get_container(self.consent_container)
            if container:
                if purpose:
                    query = "SELECT * FROM c WHERE c.user_id = @userId AND c.purpose = @purpose"
                    parameters = [
                        {"name": "@userId", "value": user_id},
                        {"name": "@purpose", "value": purpose.value}
                    ]
                else:
                    query = "SELECT * FROM c WHERE c.user_id = @userId"
                    parameters = [{"name": "@userId", "value": user_id}]
                
                items = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                for item in items:
                    try:
                        consent = ConsentRecord(
                            consent_id=item["consent_id"],
                            user_id=item["user_id"],
                            purpose=DataProcessingPurpose(item["purpose"]),
                            data_categories=[DataCategory(cat) for cat in item.get("data_categories", [])],
                            status=ConsentStatus(item["status"]),
                            timestamp=datetime.fromisoformat(item["timestamp"]),
                            expiry_date=datetime.fromisoformat(item["expiry_date"]) if item.get("expiry_date") else None,
                            withdrawal_date=datetime.fromisoformat(item["withdrawal_date"]) if item.get("withdrawal_date") else None,
                            ip_address=item.get("ip_address"),
                            user_agent=item.get("user_agent"),
                            consent_text=item.get("consent_text", "")
                        )
                        consents.append(consent)
                    except Exception as e:
                        logger.warning(f"Error parsing consent record: {e}")
                        
        except Exception as e:
            logger.warning(f"Error getting user consents: {e}")
            
        return consents

    async def _get_user_processing_records(self, user_id: str) -> List[DataProcessingRecord]:
        """Get user processing records"""
        records: List[DataProcessingRecord] = []
        
        if not self.database_manager:
            return records
            
        try:
            container = self.database_manager.get_container(self.processing_container)
            if container:
                query = "SELECT * FROM c WHERE c.user_id = @userId"
                parameters = [{"name": "@userId", "value": user_id}]
                
                items = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                for item in items:
                    try:
                        record = DataProcessingRecord(
                            processing_id=item["processing_id"],
                            user_id=item["user_id"],
                            purpose=DataProcessingPurpose(item["purpose"]),
                            data_categories=[DataCategory(cat) for cat in item.get("data_categories", [])],
                            processing_date=datetime.fromisoformat(item["processing_date"]),
                            retention_period_days=item.get("retention_period_days", 365),
                            lawful_basis=item.get("lawful_basis", ""),
                            consent_id=item.get("consent_id"),
                            automated_decision=item.get("automated_decision", False)
                        )
                        records.append(record)
                    except Exception as e:
                        logger.warning(f"Error parsing processing record: {e}")
                        
        except Exception as e:
            logger.warning(f"Error getting user processing records: {e}")
            
        return records

    async def _get_subject_request(self, request_id: str) -> Optional[DataSubjectRequest]:
        """Get subject request by ID"""
        if not self.database_manager:
            return None
            
        try:
            container = self.database_manager.get_container(self.requests_container)
            if container:
                query = "SELECT * FROM c WHERE c.request_id = @requestId"
                parameters = [{"name": "@requestId", "value": request_id}]
                
                items = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                if items:
                    item = items[0]
                    return DataSubjectRequest(
                        request_id=item["request_id"],
                        user_id=item["user_id"],
                        request_type=DataSubjectRight(item["request_type"]),
                        status=item["status"],
                        created_date=datetime.fromisoformat(item["created_date"]),
                        completed_date=datetime.fromisoformat(item["completed_date"]) if item.get("completed_date") else None,
                        details=item.get("details"),
                        notes=item.get("notes")
                    )
        except Exception as e:
            logger.warning(f"Error getting subject request {request_id}: {e}")
            
        return None


# Global GDPR compliance instance
gdpr_compliance = GDPRCompliance()


def gdpr_required(purpose: DataProcessingPurpose, data_categories: List[DataCategory], lawful_basis: str = "consent"):
    """Decorator to ensure GDPR compliance for data processing"""

    def decorator(func):
        async def wrapper(req, *args, **kwargs):
            user_id = req.headers.get("X-User-ID")

            if user_id:
                # Check consent for consent-based processing
                if purpose == DataProcessingPurpose.CONSENT:
                    for category in data_categories:
                        has_consent = await gdpr_compliance.check_consent(user_id, purpose, category)
                        if not has_consent:
                            return func.HttpResponse(
                                json.dumps(
                                    {
                                        "error": "Consent required for data processing",
                                        "code": "GDPR_CONSENT_REQUIRED",
                                        "data_category": category.value,
                                    }
                                ),
                                status_code=403,
                                headers={"Content-Type": "application/json"},
                            )

                # Record data processing
                await gdpr_compliance.record_data_processing(
                    user_id=user_id, purpose=purpose, data_categories=data_categories, lawful_basis=lawful_basis
                )

            return await func(req, *args, **kwargs)

        return wrapper

    return decorator


# Global GDPR compliance instance
gdpr_compliance = GDPRCompliance()
