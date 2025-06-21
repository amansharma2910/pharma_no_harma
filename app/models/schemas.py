# FastAPI Health Records Schema for Agentic Application

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
import uuid
import json

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

# =============================================================================
# ENUMS
# =============================================================================

class UserType(str, Enum):
    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"

class HealthRecordStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"

class FileType(str, Enum):
    TXT = "TXT"
    PDF = "PDF"
    JPG = "JPG"
    JPEG = "JPEG"
    APPOINTMENT = "APPOINTMENT"

class FileCategory(str, Enum):
    LAB_REPORT = "LAB_REPORT"
    PRESCRIPTION = "PRESCRIPTION"
    IMAGING = "IMAGING"
    NOTES = "NOTES"
    APPOINTMENT = "APPOINTMENT"
    OTHER = "OTHER"

class MedicationStatus(str, Enum):
    PRESCRIBED = "PRESCRIBED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"

class ShareType(str, Enum):
    SHORT = "SHORT"
    DETAILED = "DETAILED"

class RelationshipType(str, Enum):
    FOLLOW_UP = "FOLLOW_UP"
    COMPLICATION = "COMPLICATION"
    REFERRED = "REFERRED"

class SummaryType(str, Enum):
    LAYMAN = "LAYMAN"
    DOCTOR = "DOCTOR"
    BOTH = "BOTH"

class FileStatus(str, Enum):
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"

# =============================================================================
# BASE MODELS
# =============================================================================

class BaseResponse(BaseModel):
    success: bool
    message: str
    timestamp: datetime = datetime.now()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 20

# =============================================================================
# USER MODELS
# =============================================================================

class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None

class UserCreate(UserBase):
    user_type: UserType
    specialization: Optional[str] = None  # For doctors
    license_number: Optional[str] = None  # For doctors

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None

class UserResponse(UserBase):
    id: str
    user_type: UserType
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

# =============================================================================
# MEDICATION MODELS
# =============================================================================

class Medication(BaseModel):
    id: str = str(uuid.uuid4())
    medication_name: str
    dosage: str
    frequency: str
    duration_days: int
    instructions: Optional[str] = None
    start_date: date
    end_date: date
    status: MedicationStatus = MedicationStatus.PRESCRIBED
    prescribed_by: str
    approved_by: Optional[str] = None
    side_effects: Optional[str] = None
    created_at: datetime = datetime.now()
    approved_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class MedicationCreate(BaseModel):
    medication_name: str
    dosage: str
    frequency: str
    duration_days: int
    instructions: Optional[str] = None
    start_date: date
    end_date: date
    side_effects: Optional[str] = None

class MedicationApproval(BaseModel):
    medication_id: str
    approved_by: str

class MedicationResponse(BaseModel):
    medication_id: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

# =============================================================================
# HEALTH RECORD MODELS
# =============================================================================

class HealthRecordCreate(BaseModel):
    title: str
    ailment: str
    patient_id: str
    doctor_id: str
    layman_summary: Optional[str] = None
    medical_summary: Optional[str] = None
    overall_report: Optional[str] = None

class HealthRecordUpdate(BaseModel):
    title: Optional[str] = None
    ailment: Optional[str] = None
    status: Optional[HealthRecordStatus] = None
    layman_summary: Optional[str] = None
    medical_summary: Optional[str] = None
    overall_report: Optional[str] = None

class HealthRecordResponse(BaseModel):
    id: str
    title: str
    ailment: str
    status: HealthRecordStatus
    created_by: str
    layman_summary: Optional[str] = None
    medical_summary: Optional[str] = None
    overall_report: Optional[str] = None
    share_token: Optional[str] = None
    share_type: Optional[ShareType] = None
    created_at: datetime
    updated_at: datetime
    last_activity: datetime
    medications: List[Medication] = []
    patient: UserResponse
    doctor: UserResponse
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class HealthRecordRelation(BaseModel):
    source_record_id: str
    target_record_id: str
    relationship_type: RelationshipType
    notes: Optional[str] = None

class ShareHealthRecord(BaseModel):
    share_type: ShareType

# =============================================================================
# FILE MODELS
# =============================================================================

class FileCreate(BaseModel):
    filename: str
    description: Optional[str] = None
    category: FileCategory
    layman_summary: Optional[str] = None
    doctor_summary: Optional[str] = None

class AppointmentCreate(BaseModel):
    appointment_title: str
    appointment_date: datetime
    duration_minutes: int
    chief_complaint: str
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    next_appointment: Optional[datetime] = None
    appointment_notes: Optional[str] = None
    layman_summary: Optional[str] = None
    doctor_summary: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class FileResponse(BaseModel):
    id: str
    filename: str
    file_type: FileType
    file_size: Optional[int] = None
    storage_path: Optional[str] = None
    description: Optional[str] = None
    category: FileCategory
    uploaded_by: str
    file_status: FileStatus
    layman_summary: Optional[str] = None
    doctor_summary: Optional[str] = None
    # Appointment-specific fields
    appointment_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    next_appointment: Optional[datetime] = None
    created_at: datetime
    file_hash: Optional[str] = None
    uploaded_by_name: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class FileUpdate(BaseModel):
    layman_summary: Optional[str] = None
    doctor_summary: Optional[str] = None
    description: Optional[str] = None

# =============================================================================
# AGENT INTERACTION MODELS
# =============================================================================

class AgentQuery(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None
    health_record_id: Optional[str] = None
    user_id: str
    user_type: UserType

class AgentResponse(BaseModel):
    response: str
    confidence: Optional[float] = None
    sources: Optional[List[str]] = None
    suggested_actions: Optional[List[str]] = None
    cypher_queries_executed: Optional[List[str]] = None

class CypherQueryRequest(BaseModel):
    natural_language_query: str
    health_record_id: Optional[str] = None
    user_id: str

class CypherQueryResponse(BaseModel):
    cypher_query: str
    results: List[Dict[str, Any]]
    interpretation: str

class SummaryRequest(BaseModel):
    content: str
    summary_type: SummaryType
    context: Optional[str] = None  # Medical context for better summaries

class SummaryResponse(BaseModel):
    layman_summary: Optional[str] = None
    doctor_summary: Optional[str] = None

class MedicationScheduleRequest(BaseModel):
    health_record_id: str
    patient_symptoms: Optional[str] = None
    current_medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None

# =============================================================================
# SEARCH AND FILTER MODELS
# =============================================================================

class HealthRecordFilter(BaseModel):
    patient_id: Optional[str] = None
    doctor_id: Optional[str] = None
    status: Optional[HealthRecordStatus] = None
    ailment: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None

class FileFilter(BaseModel):
    file_type: Optional[FileType] = None
    category: Optional[FileCategory] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    uploaded_by: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    search_in: List[str] = ["health_records", "files", "medications"]
    user_id: str
    user_type: UserType

class SearchResult(BaseModel):
    type: str  # "health_record", "file", "medication"
    id: str
    title: str
    snippet: str
    relevance_score: Optional[float] = None

# =============================================================================
# TIMELINE AND DASHBOARD MODELS
# =============================================================================

class TimelineEvent(BaseModel):
    event_type: str  # "appointment", "file_upload", "medication", "diagnosis"
    event_date: datetime
    title: str
    description: str
    health_record_id: str
    related_id: Optional[str] = None  # File ID, medication ID, etc.
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class PatientTimeline(BaseModel):
    patient: UserResponse
    events: List[TimelineEvent]
    total_events: int

class DoctorDashboardItem(BaseModel):
    patient: UserResponse
    health_record: HealthRecordResponse
    last_visit: Optional[datetime] = None
    last_diagnosis: Optional[str] = None
    clinical_notes: Optional[str] = None
    medication_count: int
    pending_approvals: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class DoctorDashboard(BaseModel):
    doctor: UserResponse
    patients: List[DoctorDashboardItem]
    total_patients: int

# =============================================================================
# EXPORT MODELS
# =============================================================================

class ExportRequest(BaseModel):
    health_record_id: str
    export_type: SummaryType  # LAYMAN or DOCTOR
    include_files: bool = True
    include_medications: bool = True
    include_timeline: bool = True

class ExportResponse(BaseModel):
    pdf_url: str
    export_id: str
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

# =============================================================================
# AUDIT LOG MODELS
# =============================================================================

class AuditAction(str, Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SHARE = "SHARE"
    EXPORT = "EXPORT"
    APPROVE = "APPROVE"

class AuditLog(BaseModel):
    id: str
    user_id: str
    user_name: str
    action: AuditAction
    resource_type: str  # "health_record", "file", "medication"
    resource_id: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

# =============================================================================
# API ENDPOINT RESPONSES
# =============================================================================

class UserListResponse(BaseResponse):
    data: List[UserResponse]
    total: int
    pagination: PaginationParams

class HealthRecordListResponse(BaseResponse):
    data: List[HealthRecordResponse]
    total: int
    pagination: PaginationParams

class FileListResponse(BaseResponse):
    data: List[FileResponse]
    total: int
    pagination: PaginationParams

class SingleResourceResponse(BaseResponse):
    data: Union[UserResponse, HealthRecordResponse, FileResponse, AgentResponse, MedicationResponse]

class SearchResponse(BaseResponse):
    data: List[SearchResult]
    total: int
    query: str

# =============================================================================
# ERROR MODELS
# =============================================================================

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str
    code: Optional[str] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: Optional[List[ErrorDetail]] = None
    timestamp: datetime = datetime.now()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

# =============================================================================
# UTILITY MODELS
# =============================================================================

class HealthStatus(BaseModel):
    status: str
    database_connected: bool
    agent_service_available: bool
    file_processing_available: bool
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class BulkOperation(BaseModel):
    operation: str  # "create", "update", "delete"
    resource_type: str
    items: List[Dict[str, Any]]
    
class BulkOperationResponse(BaseModel):
    success: bool
    processed: int
    failed: int
    errors: List[str] = [] 