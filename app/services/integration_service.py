"""
Integration service for ATS, calendar, and communication integrations
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.models.integration import Integration, SyncLog, EmailTemplate, Campaign, CalendarEvent
from app.models.company import Company
from app.schemas.integration import (
    ATSType, ATSCredentials, ATSCandidate, ATSJob, SyncResult, ATSCandidateUpdate,
    CalendarProvider, CalendarEvent as CalendarEventSchema, TimeSlot,
    EmailTemplate as EmailTemplateSchema, CampaignRequest, CampaignResult,
    IntegrationConfig, IntegrationStatus
)

logger = logging.getLogger(__name__)


class BaseIntegrationConnector(ABC):
    """Base class for all integration connectors"""
    
    def __init__(self, credentials: Dict[str, Any], settings: Dict[str, Any] = None):
        self.credentials = credentials
        self.settings = settings or {}
        self.is_authenticated = False
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the external service"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the connection to the external service"""
        pass
    
    @abstractmethod
    async def get_rate_limits(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        pass


class ATSConnector(BaseIntegrationConnector):
    """Base class for ATS connectors"""
    
    @abstractmethod
    async def get_candidates(self, filters: Dict[str, Any] = None) -> List[ATSCandidate]:
        """Get candidates from ATS"""
        pass
    
    @abstractmethod
    async def get_jobs(self, filters: Dict[str, Any] = None) -> List[ATSJob]:
        """Get jobs from ATS"""
        pass
    
    @abstractmethod
    async def update_candidate(self, external_id: str, updates: ATSCandidateUpdate) -> bool:
        """Update candidate in ATS"""
        pass
    
    @abstractmethod
    async def create_candidate(self, candidate_data: Dict[str, Any]) -> str:
        """Create candidate in ATS, return external ID"""
        pass


class CalendarConnector(BaseIntegrationConnector):
    """Base class for calendar connectors"""
    
    @abstractmethod
    async def create_event(self, event: CalendarEventSchema) -> str:
        """Create calendar event, return event ID"""
        pass
    
    @abstractmethod
    async def update_event(self, event_id: str, updates: Dict[str, Any]) -> bool:
        """Update calendar event"""
        pass
    
    @abstractmethod
    async def delete_event(self, event_id: str) -> bool:
        """Delete calendar event"""
        pass
    
    @abstractmethod
    async def get_availability(self, email: str, start_time: datetime, end_time: datetime) -> List[TimeSlot]:
        """Get available time slots for a user"""
        pass


class CommunicationConnector(BaseIntegrationConnector):
    """Base class for communication connectors"""
    
    @abstractmethod
    async def send_email(self, to: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send email"""
        pass
    
    @abstractmethod
    async def send_sms(self, to: str, message: str) -> bool:
        """Send SMS"""
        pass
    
    @abstractmethod
    async def send_bulk_email(self, recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send bulk email campaign"""
        pass


class IntegrationService:
    """Main integration service for managing all integrations"""
    
    def __init__(self, db: Session):
        self.db = db
        self._connectors: Dict[str, Type[BaseIntegrationConnector]] = {}
        self._active_connections: Dict[str, BaseIntegrationConnector] = {}
    
    def register_connector(self, integration_type: str, connector_class: Type[BaseIntegrationConnector]):
        """Register a connector class for an integration type"""
        self._connectors[integration_type] = connector_class
    
    async def get_connector(self, integration_id: str) -> Optional[BaseIntegrationConnector]:
        """Get an active connector for an integration"""
        if integration_id in self._active_connections:
            return self._active_connections[integration_id]
        
        integration = self.db.query(Integration).filter(Integration.id == integration_id).first()
        if not integration or not integration.enabled:
            return None
        
        connector_key = f"{integration.type}_{integration.provider}"
        if connector_key not in self._connectors:
            logger.error(f"No connector registered for {connector_key}")
            return None
        
        connector_class = self._connectors[connector_key]
        connector = connector_class(integration.credentials, integration.settings)
        
        try:
            if await connector.authenticate():
                self._active_connections[integration_id] = connector
                return connector
        except Exception as e:
            logger.error(f"Failed to authenticate connector {integration_id}: {e}")
            await self._update_integration_status(integration_id, IntegrationStatus.ERROR, str(e))
        
        return None
    
    async def create_integration(self, company_id: str, config: IntegrationConfig) -> Integration:
        """Create a new integration"""
        integration = Integration(
            company_id=company_id,
            name=config.name,
            type=config.type,
            provider=config.type,  # Will be overridden by specific implementations
            enabled=config.enabled,
            credentials=config.credentials,
            settings=config.settings,
            field_mappings=config.field_mappings
        )
        
        self.db.add(integration)
        self.db.commit()
        self.db.refresh(integration)
        
        # Test the connection
        connector = await self.get_connector(str(integration.id))
        if connector:
            await self._update_integration_status(str(integration.id), IntegrationStatus.CONNECTED)
        else:
            await self._update_integration_status(str(integration.id), IntegrationStatus.ERROR, "Failed to connect")
        
        return integration
    
    async def update_integration(self, integration_id: str, updates: Dict[str, Any]) -> Integration:
        """Update an integration"""
        integration = self.db.query(Integration).filter(Integration.id == integration_id).first()
        if not integration:
            raise ValueError(f"Integration {integration_id} not found")
        
        for key, value in updates.items():
            if hasattr(integration, key):
                setattr(integration, key, value)
        
        integration.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(integration)
        
        # Remove from active connections to force re-authentication
        if integration_id in self._active_connections:
            del self._active_connections[integration_id]
        
        return integration
    
    async def delete_integration(self, integration_id: str) -> bool:
        """Delete an integration"""
        integration = self.db.query(Integration).filter(Integration.id == integration_id).first()
        if not integration:
            return False
        
        # Remove from active connections
        if integration_id in self._active_connections:
            del self._active_connections[integration_id]
        
        self.db.delete(integration)
        self.db.commit()
        return True
    
    async def get_integrations(self, company_id: str, integration_type: str = None) -> List[Integration]:
        """Get integrations for a company"""
        query = self.db.query(Integration).filter(Integration.company_id == company_id)
        if integration_type:
            query = query.filter(Integration.type == integration_type)
        return query.all()
    
    async def sync_integration(self, integration_id: str, operation_type: str = "full_sync") -> SyncResult:
        """Perform sync operation for an integration"""
        integration = self.db.query(Integration).filter(Integration.id == integration_id).first()
        if not integration:
            raise ValueError(f"Integration {integration_id} not found")
        
        # Create sync log
        sync_log = SyncLog(
            integration_id=integration_id,
            operation_type=operation_type,
            status="in_progress"
        )
        self.db.add(sync_log)
        self.db.commit()
        
        try:
            connector = await self.get_connector(integration_id)
            if not connector:
                raise Exception("Failed to get connector")
            
            result = SyncResult(
                success=False,
                candidates_synced=0,
                jobs_synced=0,
                errors=[],
                sync_timestamp=datetime.utcnow()
            )
            
            if integration.type == "ats":
                result = await self._sync_ats(connector, integration, sync_log)
            elif integration.type == "calendar":
                result = await self._sync_calendar(connector, integration, sync_log)
            elif integration.type == "communication":
                result = await self._sync_communication(connector, integration, sync_log)
            
            # Update sync log
            sync_log.status = "success" if result.success else "error"
            sync_log.records_success = result.candidates_synced + result.jobs_synced
            sync_log.error_details = result.errors
            sync_log.completed_at = datetime.utcnow()
            
            # Update integration last sync
            integration.last_sync = datetime.utcnow()
            if result.success:
                await self._update_integration_status(integration_id, IntegrationStatus.CONNECTED)
            
            self.db.commit()
            return result
            
        except Exception as e:
            logger.error(f"Sync failed for integration {integration_id}: {e}")
            sync_log.status = "error"
            sync_log.error_details = [str(e)]
            sync_log.completed_at = datetime.utcnow()
            self.db.commit()
            
            await self._update_integration_status(integration_id, IntegrationStatus.ERROR, str(e))
            
            return SyncResult(
                success=False,
                candidates_synced=0,
                jobs_synced=0,
                errors=[str(e)],
                sync_timestamp=datetime.utcnow()
            )
    
    async def _sync_ats(self, connector: ATSConnector, integration: Integration, sync_log: SyncLog) -> SyncResult:
        """Sync ATS data"""
        candidates_synced = 0
        jobs_synced = 0
        errors = []
        
        try:
            # Sync candidates
            if integration.settings.get("sync_candidates", True):
                candidates = await connector.get_candidates()
                for candidate in candidates:
                    try:
                        await self._process_ats_candidate(candidate, integration.company_id)
                        candidates_synced += 1
                    except Exception as e:
                        errors.append(f"Failed to process candidate {candidate.external_id}: {e}")
            
            # Sync jobs
            if integration.settings.get("sync_jobs", True):
                jobs = await connector.get_jobs()
                for job in jobs:
                    try:
                        await self._process_ats_job(job, integration.company_id)
                        jobs_synced += 1
                    except Exception as e:
                        errors.append(f"Failed to process job {job.external_id}: {e}")
            
        except Exception as e:
            errors.append(f"ATS sync error: {e}")
        
        return SyncResult(
            success=len(errors) == 0,
            candidates_synced=candidates_synced,
            jobs_synced=jobs_synced,
            errors=errors,
            sync_timestamp=datetime.utcnow()
        )
    
    async def _sync_calendar(self, connector: CalendarConnector, integration: Integration, sync_log: SyncLog) -> SyncResult:
        """Sync calendar data"""
        # Calendar sync implementation would go here
        return SyncResult(
            success=True,
            candidates_synced=0,
            jobs_synced=0,
            errors=[],
            sync_timestamp=datetime.utcnow()
        )
    
    async def _sync_communication(self, connector: CommunicationConnector, integration: Integration, sync_log: SyncLog) -> SyncResult:
        """Sync communication data"""
        # Communication sync implementation would go here
        return SyncResult(
            success=True,
            candidates_synced=0,
            jobs_synced=0,
            errors=[],
            sync_timestamp=datetime.utcnow()
        )
    
    async def _process_ats_candidate(self, candidate: ATSCandidate, company_id: str):
        """Process ATS candidate data"""
        # Implementation would sync candidate data to PRIME database
        pass
    
    async def _process_ats_job(self, job: ATSJob, company_id: str):
        """Process ATS job data"""
        # Implementation would sync job data to PRIME database
        pass
    
    async def _update_integration_status(self, integration_id: str, status: IntegrationStatus, error_message: str = None):
        """Update integration status"""
        integration = self.db.query(Integration).filter(Integration.id == integration_id).first()
        if integration:
            integration.status = status.value
            integration.error_message = error_message
            integration.updated_at = datetime.utcnow()
            self.db.commit()


# Global integration service instance
integration_service = None

def get_integration_service(db: Session = None) -> IntegrationService:
    """Get integration service instance"""
    global integration_service
    if integration_service is None or db is not None:
        integration_service = IntegrationService(db or next(get_db()))
    return integration_service