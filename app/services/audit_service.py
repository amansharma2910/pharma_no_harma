import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.models.schemas import AuditAction, AuditLog
from app.services.neo4j_service import neo4j_service

logger = logging.getLogger(__name__)

class AuditService:
    def __init__(self):
        self.enabled = True
    
    async def log_action(
        self,
        user_id: str,
        user_name: str,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Log an audit action"""
        try:
            if not self.enabled:
                return True
            
            audit_data = {
                "user_id": user_id,
                "user_name": user_name,
                "action": action.value,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details,
                "ip_address": ip_address,
                "user_agent": user_agent
            }
            
            success = await neo4j_service.create_audit_log(audit_data)
            
            if success:
                logger.info(f"Audit logged: {action.value} on {resource_type} {resource_id} by {user_name}")
            else:
                logger.error(f"Failed to log audit: {action.value} on {resource_type} {resource_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error logging audit action: {e}")
            return False
    
    async def get_audit_logs(
        self,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[AuditLog]:
        """Get audit logs with filtering"""
        try:
            filters = {}
            
            if resource_id:
                filters["resource_id"] = resource_id
            if user_id:
                filters["user_id"] = user_id
            if action:
                filters["action"] = action.value
            if date_from:
                filters["date_from"] = date_from.isoformat()
            if date_to:
                filters["date_to"] = date_to.isoformat()
            
            result = await neo4j_service.get_audit_logs(filters, skip, limit)
            
            audit_logs = []
            for log_data in result["logs"]:
                audit_logs.append(AuditLog(**log_data))
            
            return audit_logs
            
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}")
            return []
    
    async def get_health_record_audit(self, health_record_id: str) -> List[AuditLog]:
        """Get audit logs for specific health record"""
        try:
            # Get direct health record actions
            health_record_logs = await self.get_audit_logs(resource_id=health_record_id)
            
            # Get related file actions
            file_logs = await self._get_related_file_audit_logs(health_record_id)
            
            # Get related medication actions
            medication_logs = await self._get_related_medication_audit_logs(health_record_id)
            
            # Combine and sort by timestamp
            all_logs = health_record_logs + file_logs + medication_logs
            all_logs.sort(key=lambda x: x.timestamp, reverse=True)
            
            return all_logs
            
        except Exception as e:
            logger.error(f"Error retrieving health record audit: {e}")
            return []
    
    async def _get_related_file_audit_logs(self, health_record_id: str) -> List[AuditLog]:
        """Get audit logs for files related to a health record"""
        try:
            # This would query for files related to the health record
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting related file audit logs: {e}")
            return []
    
    async def _get_related_medication_audit_logs(self, health_record_id: str) -> List[AuditLog]:
        """Get audit logs for medications related to a health record"""
        try:
            # This would query for medications related to the health record
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting related medication audit logs: {e}")
            return []
    
    async def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get summary of user activity"""
        try:
            # This would aggregate audit logs for user activity summary
            # For now, return placeholder data
            return {
                "user_id": user_id,
                "period_days": days,
                "total_actions": 0,
                "action_breakdown": {},
                "most_active_day": None,
                "most_common_action": None
            }
        except Exception as e:
            logger.error(f"Error getting user activity summary: {e}")
            return {}
    
    async def export_audit_logs(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        format: str = "csv"
    ) -> str:
        """Export audit logs to file"""
        try:
            # This would export audit logs to CSV or other format
            # For now, return placeholder
            return "audit_export.csv"
        except Exception as e:
            logger.error(f"Error exporting audit logs: {e}")
            return ""
    
    async def cleanup_old_audit_logs(self, days_to_keep: int = 365) -> int:
        """Clean up old audit logs"""
        try:
            # This would delete audit logs older than specified days
            # For now, return 0
            return 0
        except Exception as e:
            logger.error(f"Error cleaning up old audit logs: {e}")
            return 0
    
    def enable_auditing(self):
        """Enable audit logging"""
        self.enabled = True
        logger.info("Audit logging enabled")
    
    def disable_auditing(self):
        """Disable audit logging"""
        self.enabled = False
        logger.info("Audit logging disabled")
    
    async def log_system_event(
        self,
        event_type: str,
        description: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log system-level events"""
        try:
            return await self.log_action(
                user_id="system",
                user_name="System",
                action=AuditAction.CREATE,
                resource_type="system_event",
                resource_id=event_type,
                details={
                    "description": description,
                    "event_type": event_type,
                    **(details or {})
                }
            )
        except Exception as e:
            logger.error(f"Error logging system event: {e}")
            return False
    
    async def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log security-related events"""
        try:
            return await self.log_action(
                user_id=user_id or "unknown",
                user_name="Security Event",
                action=AuditAction.CREATE,
                resource_type="security_event",
                resource_id=event_type,
                details={
                    "event_type": event_type,
                    "ip_address": ip_address,
                    **(details or {})
                },
                ip_address=ip_address
            )
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
            return False

# Global instance
audit_service = AuditService() 