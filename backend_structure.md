# FastAPI Health Records Implementation Instructions for Cursor

This document provides complete instructions for implementing a FastAPI-based agentic health records management system for elderly care.

## Project Structure

Create the following file structure:

```
health_records_api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── users.py
│   │   │   ├── health_records.py
│   │   │   ├── files.py
│   │   │   ├── medications.py
│   │   │   ├── agent.py
│   │   │   ├── search.py
│   │   │   ├── dashboard.py
│   │   │   ├── export.py
│   │   │   └── audit.py
│   │   └── deps.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── database.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── neo4j_service.py
│   │   ├── agent_service.py
│   │   ├── file_service.py
│   │   └── audit_service.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── requirements.txt
└── README.md
```

## File 1: schemas.py (app/models/schemas.py)

Create a comprehensive Pydantic models file with the following content:

```python
# FastAPI Health Records Schema for Agentic Application

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
import uuid

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

# =============================================================================
# BASE MODELS
# =============================================================================

class BaseResponse(BaseModel):
    success: bool
    message: str
    timestamp: datetime = datetime.now()

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

class FileResponse(BaseModel):
    id: str
    filename: str
    file_type: FileType
    file_size: Optional[int] = None
    storage_path: Optional[str] = None
    description: Optional[str] = None
    category: FileCategory
    uploaded_by: str
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
    data: Union[UserResponse, HealthRecordResponse, FileResponse, AgentResponse]

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

# =============================================================================
# UTILITY MODELS
# =============================================================================

class HealthStatus(BaseModel):
    status: str
    database_connected: bool
    agent_service_available: bool
    file_processing_available: bool
    timestamp: datetime

class BulkOperation(BaseModel):
    operation: str  # "create", "update", "delete"
    resource_type: str
    items: List[Dict[str, Any]]
    
class BulkOperationResponse(BaseModel):
    success: bool
    processed: int
    failed: int
    errors: List[str] = []
```

## File 2: main.py (app/main.py)

Create the main FastAPI application file with all endpoints:

```python
# FastAPI Endpoints for Health Records Application

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uuid

# Import all the models from the schema file
from app.models.schemas import *

app = FastAPI(
    title="Health Records API",
    description="Agentic Health Records Management System for Elderly Care",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# USER ENDPOINTS
# =============================================================================

@app.post("/users", response_model=SingleResourceResponse, status_code=201)
async def create_user(user: UserCreate):
    """Create a new user (patient or doctor)"""
    # TODO: Implement user creation logic
    # - Generate unique user ID
    # - Create user node in Neo4j
    # - Log audit entry
    pass

@app.get("/users/{user_id}", response_model=SingleResourceResponse)
async def get_user(user_id: str):
    """Get user by ID"""
    # TODO: Implement user retrieval logic
    # - Query Neo4j for user by ID
    # - Log audit entry for READ action
    pass

@app.put("/users/{user_id}", response_model=SingleResourceResponse)
async def update_user(user_id: str, user_update: UserUpdate):
    """Update user information"""
    # TODO: Implement user update logic
    # - Update user node in Neo4j
    # - Log audit entry for UPDATE action
    pass

@app.delete("/users/{user_id}", response_model=BaseResponse)
async def delete_user(user_id: str):
    """Delete user account"""
    # TODO: Implement user deletion logic
    # - Delete user and all relationships from Neo4j
    # - Log audit entry for DELETE action
    pass

@app.get("/users", response_model=UserListResponse)
async def list_users(
    user_type: Optional[UserType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """List users with optional filtering"""
    # TODO: Implement user listing logic
    # - Query Neo4j with filters and pagination
    # - Return paginated results
    pass

# =============================================================================
# HEALTH RECORD ENDPOINTS
# =============================================================================

@app.post("/health-records", response_model=SingleResourceResponse, status_code=201)
async def create_health_record(health_record: HealthRecordCreate):
    """Create a new health record"""
    # TODO: Implement health record creation logic
    # - Generate unique health record ID and share token
    # - Create health record node in Neo4j
    # - Create relationships with patient and doctor
    # - Log audit entry
    pass

@app.get("/health-records/{health_record_id}", response_model=SingleResourceResponse)
async def get_health_record(health_record_id: str):
    """Get health record by ID with all associated data"""
    # TODO: Implement health record retrieval logic
    # - Query Neo4j for health record with all relationships
    # - Include files, medications, patient, and doctor info
    # - Log audit entry for READ action
    pass

@app.put("/health-records/{health_record_id}", response_model=SingleResourceResponse)
async def update_health_record(health_record_id: str, health_record_update: HealthRecordUpdate):
    """Update health record information"""
    # TODO: Implement health record update logic
    # - Update health record node in Neo4j
    # - Update last_activity timestamp
    # - Log audit entry for UPDATE action
    pass

@app.delete("/health-records/{health_record_id}", response_model=BaseResponse)
async def delete_health_record(health_record_id: str):
    """Delete health record"""
    # TODO: Implement health record deletion logic
    # - Delete health record and all relationships from Neo4j
    # - Log audit entry for DELETE action
    pass

@app.get("/health-records", response_model=HealthRecordListResponse)
async def list_health_records(
    filters: HealthRecordFilter = Depends(),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """List health records with filtering"""
    # TODO: Implement health record listing logic
    # - Build Cypher query with filters
    # - Apply pagination
    # - Return structured results
    pass

@app.post("/health-records/{health_record_id}/relate", response_model=BaseResponse)
async def relate_health_records(health_record_id: str, relation: HealthRecordRelation):
    """Create relationship between health records"""
    # TODO: Implement health record relationship creation
    # - Create RELATED_TO relationship in Neo4j
    # - Log audit entry
    pass

@app.get("/health-records/{health_record_id}/related", response_model=HealthRecordListResponse)
async def get_related_health_records(health_record_id: str):
    """Get all related health records"""
    # TODO: Implement related health records retrieval
    # - Query Neo4j for RELATED_TO relationships
    # - Return related health records with relationship info
    pass

# =============================================================================
# SHARING ENDPOINTS
# =============================================================================

@app.post("/health-records/{health_record_id}/share", response_model=dict)
async def create_share_link(health_record_id: str, share_config: ShareHealthRecord):
    """Generate shareable link for health record"""
    # TODO: Implement share link creation
    # - Generate unique share token
    # - Update health record with share configuration
    # - Log audit entry for SHARE action
    pass

@app.get("/shared/{share_token}", response_model=dict)
async def get_shared_health_record(share_token: str):
    """Access shared health record via token"""
    # TODO: Implement shared health record access
    # - Query Neo4j for health record by share token
    # - Return appropriate data based on share_type (SHORT/DETAILED)
    # - Log audit entry for READ action
    pass

@app.delete("/health-records/{health_record_id}/share", response_model=BaseResponse)
async def revoke_share_link(health_record_id: str):
    """Revoke existing share link"""
    # TODO: Implement share link revocation
    # - Clear share_token from health record
    # - Log audit entry
    pass

# =============================================================================
# FILE MANAGEMENT ENDPOINTS
# =============================================================================

@app.post("/health-records/{health_record_id}/files", response_model=SingleResourceResponse, status_code=201)
async def upload_file(
    health_record_id: str,
    file: UploadFile = File(...),
    file_data: FileCreate = Depends(),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Upload and process a file (triggers AI processing pipeline)"""
    # TODO: Implement file upload logic
    # - Save file to storage
    # - Create file node in Neo4j
    # - Trigger background AI processing for summaries
    # - Log audit entry for CREATE action
    pass

@app.post("/health-records/{health_record_id}/appointments", response_model=SingleResourceResponse, status_code=201)
async def create_appointment(health_record_id: str, appointment: AppointmentCreate):
    """Create appointment record"""
    # TODO: Implement appointment creation logic
    # - Create file node with file_type: "APPOINTMENT"
    # - Set appointment-specific fields
    # - Create relationships (CONDUCTED, ATTENDED)
    # - Log audit entry
    pass

@app.get("/health-records/{health_record_id}/files", response_model=FileListResponse)
async def list_files(
    health_record_id: str,
    filters: FileFilter = Depends(),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """List files for health record"""
    # TODO: Implement file listing logic
    # - Query Neo4j for files with filters
    # - Apply pagination
    # - Include uploader information
    pass

@app.get("/files/{file_id}", response_model=SingleResourceResponse)
async def get_file(file_id: str, summary_type: Optional[SummaryType] = None):
    """Get file details with appropriate summary based on user type"""
    # TODO: Implement file retrieval logic
    # - Query Neo4j for file by ID
    # - Return appropriate summary based on summary_type
    # - Log audit entry for READ action
    pass

@app.put("/files/{file_id}", response_model=SingleResourceResponse)
async def update_file(file_id: str, file_update: FileUpdate):
    """Update file summaries and metadata"""
    # TODO: Implement file update logic
    # - Update file node in Neo4j
    # - Log audit entry for UPDATE action
    pass

@app.delete("/files/{file_id}", response_model=BaseResponse)
async def delete_file(file_id: str):
    """Delete file"""
    # TODO: Implement file deletion logic
    # - Delete file from storage and Neo4j
    # - Log audit entry for DELETE action
    pass

@app.get("/files/{file_id}/download")
async def download_file(file_id: str):
    """Download original file"""
    # TODO: Implement file download logic
    # - Return file from storage
    # - Log audit entry for READ action
    pass

@app.get("/health-records/{health_record_id}/appointments", response_model=FileListResponse)
async def list_appointments(
    health_record_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """List appointments for health record"""
    # TODO: Implement appointment listing logic
    # - Query Neo4j for files with file_type: "APPOINTMENT"
    # - Include doctor and patient information
    pass

# =============================================================================
# MEDICATION ENDPOINTS
# =============================================================================

@app.post("/health-records/{health_record_id}/medications", response_model=SingleResourceResponse, status_code=201)
async def add_medication(health_record_id: str, medication: MedicationCreate):
    """Add medication to health record"""
    # TODO: Implement medication addition logic
    # - Add medication to health record's medications array
    # - Update last_activity timestamp
    # - Log audit entry for CREATE action
    pass

@app.put("/health-records/{health_record_id}/medications/{medication_id}/approve", response_model=BaseResponse)
async def approve_medication(
    health_record_id: str, 
    medication_id: str, 
    approval: MedicationApproval
):
    """Approve medication (doctor only)"""
    # TODO: Implement medication approval logic
    # - Update medication status to APPROVED
    # - Set approved_by and approved_at fields
    # - Log audit entry for APPROVE action
    pass

@app.get("/health-records/{health_record_id}/medications", response_model=List[Medication])
async def list_medications(
    health_record_id: str,
    status: Optional[MedicationStatus] = None
):
    """List medications for health record"""
    # TODO: Implement medication listing logic
    # - Query health record's medications array
    # - Filter by status if provided
    pass

@app.delete("/health-records/{health_record_id}/medications/{medication_id}", response_model=BaseResponse)
async def remove_medication(health_record_id: str, medication_id: str):
    """Remove medication from health record"""
    # TODO: Implement medication removal logic
    # - Remove medication from medications array
    # - Log audit entry for DELETE action
    pass

@app.get("/medications/active", response_model=List[Medication])
async def get_active_medications(user_id: str):
    """Get all active medications for a patient across all health records"""
    # TODO: Implement active medications retrieval
    # - Query all health records for patient
    # - Filter for active/approved medications
    pass

# =============================================================================
# AGENT INTERACTION ENDPOINTS
# =============================================================================

@app.post("/agent/query", response_model=AgentResponse)
async def query_agent(query: AgentQuery):
    """Send natural language query to the health agent"""
    # TODO: Implement agent query logic
    # - Process natural language query
    # - Query Neo4j based on intent
    # - Generate response with context
    # - Log interaction
    pass

@app.post("/agent/cypher", response_model=CypherQueryResponse)
async def generate_cypher_query(request: CypherQueryRequest):
    """Generate and execute Cypher query from natural language"""
    # TODO: Implement Cypher generation logic
    # - Convert natural language to Cypher query
    # - Execute query on Neo4j
    # - Interpret results for user
    pass

@app.post("/agent/summarize", response_model=SummaryResponse)
async def generate_summary(request: SummaryRequest, background_tasks: BackgroundTasks):
    """Generate layman and/or doctor summaries using AI"""
    # TODO: Implement AI summary generation
    # - Process content through AI service
    # - Generate appropriate summaries
    # - Return structured response
    pass

@app.post("/agent/medication-schedule", response_model=List[MedicationCreate])
async def suggest_medication_schedule(request: MedicationScheduleRequest):
    """AI-suggested medication schedule based on health record"""
    # TODO: Implement medication schedule suggestion
    # - Analyze health record context
    # - Generate AI-powered medication suggestions
    # - Return structured medication list
    pass

@app.post("/agent/interpret-record", response_model=AgentResponse)
async def interpret_health_record(health_record_id: str, user_type: UserType):
    """AI interpretation of complete health record"""
    # TODO: Implement health record interpretation
    # - Analyze complete health record
    # - Generate interpretation based on user_type
    # - Provide insights and recommendations
    pass

@app.post("/files/{file_id}/reprocess", response_model=SingleResourceResponse)
async def reprocess_file(file_id: str, background_tasks: BackgroundTasks):
    """Reprocess file through AI pipeline for updated summaries"""
    # TODO: Implement file reprocessing
    # - Trigger AI processing pipeline
    # - Update summaries in background
    # - Log audit entry
    pass

# =============================================================================
# SEARCH ENDPOINTS
# =============================================================================

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Search across health records, files, and medications"""
    # TODO: Implement comprehensive search
    # - Search in health records, files, medications
    # - Rank results by relevance
    # - Return structured search results
    pass

@app.get("/search/suggestions")
async def get_search_suggestions(q: str, user_id: str, limit: int = 10):
    """Get search suggestions as user types"""
    # TODO: Implement search suggestions
    # - Generate suggestions based on partial query
    # - Use user's data for personalized suggestions
    pass

# =============================================================================
# TIMELINE AND DASHBOARD ENDPOINTS
# =============================================================================

@app.get("/patients/{patient_id}/timeline", response_model=PatientTimeline)
async def get_patient_timeline(
    patient_id: str,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
):
    """Get patient's complete health timeline"""
    # TODO: Implement timeline generation
    # - Query all events for patient
    # - Sort chronologically
    # - Format for timeline display
    pass

@app.get("/doctors/{doctor_id}/dashboard", response_model=DoctorDashboard)
async def get_doctor_dashboard(doctor_id: str):
    """Get doctor's patient dashboard"""
    # TODO: Implement doctor dashboard
    # - Query all patients for doctor
    # - Get latest activity and status
    # - Calculate pending approvals
    pass

@app.get("/patients/{patient_id}/summary", response_model=AgentResponse)
async def get_patient_summary(patient_id: str, summary_type: SummaryType):
    """Get AI-generated patient health summary"""
    # TODO: Implement patient summary generation
    # - Analyze all health records for patient
    # - Generate comprehensive health summary
    # - Tailor summary based on summary_type
    pass

# =============================================================================
# EXPORT ENDPOINTS
# =============================================================================

@app.post("/health-records/{health_record_id}/export", response_model=ExportResponse)
async def export_health_record(
    health_record_id: str, 
    export_request: ExportRequest,
    background_tasks: BackgroundTasks
):
    """Export health record as PDF"""
    # TODO: Implement PDF export logic
    # - Generate PDF based on export_request configuration
    # - Include appropriate summaries (layman/doctor)
    # - Store PDF and return download URL
    # - Log audit entry for EXPORT action
    pass

@app.get("/exports/{export_id}/download")
async def download_export(export_id: str):
    """Download exported PDF"""
    # TODO: Implement export download
    # - Return PDF file from storage
    # - Log audit entry for READ action
    pass

@app.get("/files/{file_id}/export")
async def export_file_summary(file_id: str, summary_type: SummaryType):
    """Export file summary as PDF"""
    # TODO: Implement file summary export
    # - Generate PDF of file summary
    # - Include appropriate summary type
    # - Return PDF response
    pass

# =============================================================================
# AUDIT AND LOGGING ENDPOINTS
# =============================================================================

@app.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(
    resource_id: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[AuditAction] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    """Get audit logs with filtering"""
    # TODO: Implement audit log retrieval
    # - Query audit logs with filters
    # - Apply pagination
    # - Return structured audit data
    pass

@app.get("/health-records/{health_record_id}/audit", response_model=List[AuditLog])
async def get_health_record_audit(health_record_id: str):
    """Get audit logs for specific health record"""
    # TODO: Implement health record audit retrieval
    # - Query audit logs for specific health record
    # - Include all related resources (files, medications)
    pass

# =============================================================================
# NOTIFICATION ENDPOINTS (for future medication reminders)
# =============================================================================

@app.get("/patients/{patient_id}/medication-reminders")
async def get_medication_reminders(patient_id: str, date: Optional[date] = None):
    """Get medication reminders for patient"""
    # TODO: Implement medication reminder retrieval
    # - Query active medications for patient
    # - Calculate reminder schedule for date
    # - Return structured reminder data
    pass

@app.post("/patients/{patient_id}/medication-reminders/call", response_model=BaseResponse)
async def trigger_medication_reminder_call(patient_id: str, medication_id: str):
    """Trigger automated phone call reminder"""
    # TODO: Implement phone call trigger
    # - Integrate with phone service API
    # - Generate medication reminder message
    # - Log call attempt and result
    pass

# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """System health check"""
    # TODO: Implement health check logic
    # - Check database connectivity
    # - Check AI service availability
    # - Check file processing service
    # - Return system status
    pass

@app.post("/bulk-operations", response_model=BulkOperationResponse)
async def bulk_operation(operation: BulkOperation, background_tasks: BackgroundTasks):
    """Perform bulk operations"""
    # TODO: Implement bulk operations
    # - Process bulk create/update/delete operations
    # - Handle errors gracefully
    # - Return operation summary
    pass

@app.get("/stats/dashboard")
async def get_dashboard_stats(user_id: str, user_type: UserType):
    """Get dashboard statistics for user"""
    # TODO: Implement dashboard statistics
    # - Calculate relevant stats based on user_type
    # - Return structured dashboard data
    pass

# =============================================================================
# FILE PROCESSING WEBHOOKS (for LlamaCloud integration)
# =============================================================================

@app.post("/webhooks/file-processed")
async def file_processing_complete(
    file_id: str,
    processing_results: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Webhook endpoint for completed file processing"""
    # TODO: Implement file processing webhook
    # - Update file with processed data
    # - Trigger AI summary generation
    # - Update health record last_activity
    pass

@app.post("/webhooks/ai-summary-ready")
async def ai_summary_ready(
    file_id: str,
    summaries: SummaryResponse,
    background_tasks: BackgroundTasks
):
    """Webhook endpoint for completed AI summary generation"""
    # TODO: Implement AI summary webhook
    # - Update file with generated summaries
    # - Notify relevant users if needed
    pass

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return ErrorResponse(
        message=exc.detail,
        errors=[ErrorDetail(message=exc.detail, code=str(exc.status_code))]
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return ErrorResponse(
        message="Internal server error",
        errors=[ErrorDetail(message=str(exc), code="500")]
    )

# =============================================================================
# STARTUP/SHUTDOWN EVENTS
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database connections, AI services, etc."""
    # TODO: Implement startup logic
    # - Initialize Neo4j connection
    # - Initialize AI service clients
    # - Setup file storage
    # - Initialize audit logging
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources"""
    # TODO: Implement shutdown logic
    # - Close database connections
    # - Cleanup temporary files
    # - Flush audit logs
    pass
```

## File 3: requirements.txt

Create a requirements.txt file with necessary dependencies:

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic[email]==2.5.0
python-multipart==0.0.6
neo4j==5.15.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
aiofiles==23.2.1
httpx==0.25.2
celery==5.3.4
redis==5.0.1
reportlab==4.0.7
weasyprint==60.2
pillow==10.1.0
pypdf2==3.0.1
```

## File 4: config.py (app/core/config.py)

Create configuration management:

```python
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Neo4j Configuration
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "healthrecords"
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Health Records API"
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: list = ["TXT", "PDF", "JPG", "JPEG"]
    
    # AI Service Configuration
    OPENAI_API_KEY: Optional[str] = None
    LLAMA_CLOUD_API_KEY: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Background Tasks
    CELERY_BROKER_URL: str = "redis://localhost:6379"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379"
    
    # Export Configuration
    PDF_EXPORT_DIR: str = "./exports"
    EXPORT_URL_PREFIX: str = "http://localhost:8000/exports"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## File 5: Neo4j Service (app/services/neo4j_service.py)

Create Neo4j database service:

```python
from neo4j import GraphDatabase, Driver
from typing import Dict, List, Optional, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Neo4jService:
    def __init__(self):
        self.driver: Optional[Driver] = None
    
    async def connect(self):
        """Initialize Neo4j connection"""
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
            )
            # Test connection
            await self.driver.verify_connectivity()
            logger.info("Connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    async def close(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()
    
    async def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict]:
        """Execute Cypher query and return results"""
        if not self.driver:
            raise Exception("Database connection not initialized")
        
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def execute_write_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict]:
        """Execute write query in a transaction"""
        if not self.driver:
            raise Exception("Database connection not initialized")
        
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.write_transaction(self._execute_query, query, parameters or {})
                return result
        except Exception as e:
            logger.error(f"Write query execution failed: {e}")
            raise
    
    @staticmethod
    def _execute_query(tx, query: str, parameters: Dict[str, Any]):
        result = tx.run(query, parameters)
        return [record.data() for record in result]

# Global instance
neo4j_service = Neo4jService()
```

## Implementation Instructions

### Step 1: Project Setup
1. Create the project directory structure as shown above
2. Install dependencies: `pip install -r requirements.txt`
3. Create `.env` file with your configuration values

### Step 2: Database Setup
1. Install and start Neo4j database
2. Run the Neo4j setup queries from the previous Neo4j guide
3. Configure connection settings in `.env`

### Step 3: Core Implementation
1. Implement the `neo4j_service.py` for database operations
2. Create additional service files for:
   - `agent_service.py` - AI/LLM interactions
   - `file_service.py` - File upload/processing
   - `audit_service.py` - Audit logging

### Step 4: Endpoint Implementation
Fill in the TODO sections in `main.py` with actual implementation:

#### User Endpoints
- Implement CRUD operations using Neo4j Cypher queries
- Add validation and error handling
- Log all operations for audit trail

#### Health Record Endpoints
- Create health records with patient-doctor relationships
- Implement health record relationships (RELATED_TO)
- Add sharing functionality with token generation

#### File Management
- Implement file upload with storage
- Trigger background AI processing
- Handle appointment creation as special file type
- Have status PROCESSING or PROCESSED on files. Once the file is processed, the status changes to PROCESSED. 

#### Agent Integration
- Connect to AI service for natural language processing
- Implement summary generation
- Add Cypher query generation from natural language

### Step 5: Background Processing
1. Set up Celery for background tasks
2. Implement file processing pipeline
3. Add AI summary generation workers

### Step 6: Testing and Validation
1. Create test files for each endpoint
2. Test with sample data
3. Validate Neo4j integration

### Step 7: Streamlit Frontend Integration
The API is designed to work seamlessly with Streamlit:
- Use structured responses for easy data display
- Implement file upload endpoints for Streamlit file widgets
- Provide dashboard endpoints for Streamlit dashboards

## Key Implementation Notes

1. **Authentication**: Authentication is excluded for POC but can be added later
2. **Error Handling**: Comprehensive error responses for debugging
3. **Audit Logging**: Every operation should log user activity
4. **Background Tasks**: File processing and AI operations run asynchronously
5. **Pagination**: All list endpoints support pagination
6. **Filtering**: Flexible filtering options for data retrieval
7. **Export**: PDF generation for sharing medical records

This structure provides a complete foundation for your agentic health records application that integrates with Neo4j and supports AI-powered features.