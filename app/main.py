from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query, BackgroundTasks, Request
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
import uuid
import os
import aiofiles
import hashlib
import logging
from datetime import datetime, date

# Import all the models from the schema file
from app.models.schemas import (
    ShareType, UserCreate, UserUpdate, UserResponse, UserType, UserListResponse,
    HealthRecordCreate, HealthRecordUpdate, HealthRecordResponse, HealthRecordStatus, HealthRecordListResponse,
    FileResponse as FileResponseSchema, FileUpdate, FileListResponse, FileType, FileCategory, FileStatus,
    AppointmentCreate, Medication, MedicationCreate, MedicationApproval, MedicationStatus,
    AgentQuery, AgentResponse, SummaryRequest, SummaryResponse, SummaryType,
    SearchRequest, SearchResponse, SearchResult,
    BaseResponse, SingleResourceResponse, PaginationParams,
    AuditAction, AuditLog,
    ErrorResponse, ErrorDetail, HealthStatus,
    MedicationResponse
)
from app.services.neo4j_service import neo4j_service
from app.services.agent_service import agent_service
from app.services.file_service import file_service
from app.services.audit_service import audit_service
from app.core.config import settings

# Import Bedrock router
from app.api.endpoints.bedrock import router as bedrock_router

logger = logging.getLogger(__name__)

def convert_neo4j_dates(data: Any) -> Any:
    """Convert Neo4j date/time objects to Python native types"""
    if hasattr(data, '__dict__'):
        # Handle Neo4j objects
        if hasattr(data, 'year') and hasattr(data, 'month') and hasattr(data, 'day'):
            # Neo4j Date object
            return date(data.year, data.month, data.day)
        elif hasattr(data, 'year') and hasattr(data, 'month') and hasattr(data, 'day') and hasattr(data, 'hour'):
            # Neo4j DateTime object
            return datetime(
                data.year, data.month, data.day, 
                data.hour, data.minute, data.second, 
                data.nanosecond // 1000000 if hasattr(data, 'nanosecond') else 0,
                tzinfo=getattr(data, 'tzinfo', None)
            )
    
    if isinstance(data, dict):
        return {key: convert_neo4j_dates(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_neo4j_dates(item) for item in data]
    else:
        return data

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    try:
        await neo4j_service.connect()
        logger.info("Application startup completed")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        await neo4j_service.close()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

app = FastAPI(
    title="Health Records API",
    description="Agentic Health Records Management System for Elderly Care",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Bedrock router
app.include_router(bedrock_router, prefix="/api/v1", tags=["AWS Bedrock"])

# =============================================================================
# USER ENDPOINTS
# =============================================================================

@app.post("/users", response_model=SingleResourceResponse, status_code=201)
async def create_user(user: UserCreate, request: Request):
    """Create a new user (patient or doctor)"""
    try:
        user_data = user.model_dump()
        user_data["date_of_birth"] = user_data.get("date_of_birth")
        
        created_user = await neo4j_service.create_user(user_data)
        
        if not created_user:
            raise HTTPException(status_code=400, detail="Failed to create user")
        
        # Convert Neo4j date/time objects to Python native types
        created_user = convert_neo4j_dates(created_user)
        
        # Log audit entry
        await audit_service.log_action(
            user_id=created_user["id"],
            user_name=created_user["name"],
            action=AuditAction.CREATE,
            resource_type="user",
            resource_id=created_user["id"],
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return SingleResourceResponse(
            success=True,
            message="User created successfully",
            data=UserResponse(**created_user)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}", response_model=SingleResourceResponse)
async def get_user(user_id: str, request: Request):
    """Get user by ID"""
    try:
        user = await neo4j_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Convert Neo4j date/time objects to Python native types
        user = convert_neo4j_dates(user)
        
        # Log audit entry
        await audit_service.log_action(
            user_id=user_id,
            user_name=user["name"],
            action=AuditAction.READ,
            resource_type="user",
            resource_id=user_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return SingleResourceResponse(
            success=True,
            message="User retrieved successfully",
            data=UserResponse(**user)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/users/{user_id}", response_model=SingleResourceResponse)
async def update_user(user_id: str, user_update: UserUpdate, request: Request):
    """Update user information"""
    try:
        update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updated_user = await neo4j_service.update_user(user_id, update_data)
        
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Convert Neo4j date/time objects to Python native types
        updated_user = convert_neo4j_dates(updated_user)
        
        # Log audit entry
        await audit_service.log_action(
            user_id=user_id,
            user_name=updated_user["name"],
            action=AuditAction.UPDATE,
            resource_type="user",
            resource_id=user_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details=update_data
        )
        
        return SingleResourceResponse(
            success=True,
            message="User updated successfully",
            data=UserResponse(**updated_user)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/users/{user_id}", response_model=BaseResponse)
async def delete_user(user_id: str, request: Request):
    """Delete user account"""
    try:
        user = await neo4j_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        await neo4j_service.delete_user(user_id)
        
        # Log audit entry
        await audit_service.log_action(
            user_id=user_id,
            user_name=user["name"],
            action=AuditAction.DELETE,
            resource_type="user",
            resource_id=user_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return BaseResponse(
            success=True,
            message="User deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users", response_model=UserListResponse)
async def list_users(
    user_type: Optional[UserType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """List users with optional filtering"""
    try:
        result = await neo4j_service.list_users(
            user_type=user_type.value if user_type else None,
            skip=skip,
            limit=limit
        )
        
        # Convert Neo4j date/time objects to Python native types
        users = [convert_neo4j_dates(user) for user in result["users"]]
        users = [UserResponse(**user) for user in users]
        
        return UserListResponse(
            success=True,
            message="Users retrieved successfully",
            data=users,
            total=result["total"],
            pagination=PaginationParams(skip=skip, limit=limit)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# HEALTH RECORD ENDPOINTS
# =============================================================================

@app.post("/health-records", response_model=SingleResourceResponse, status_code=201)
async def create_health_record(health_record: HealthRecordCreate, request: Request):
    """Create a new health record"""
    try:
        health_record_data = health_record.model_dump()
        health_record_data["created_by"] = health_record_data["doctor_id"]
        health_record_data["share_type"] = ShareType.SHORT
        
        result = await neo4j_service.create_health_record(health_record_data)
        
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create health record")
        
        # Convert Neo4j date/time objects to Python native types
        result = convert_neo4j_dates(result)
        
        # Log audit entry
        await audit_service.log_action(
            user_id=health_record_data["created_by"],
            user_name="System",  # Could be enhanced to get actual user name
            action=AuditAction.CREATE,
            resource_type="health_record",
            resource_id=result["hr"]["id"],
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return SingleResourceResponse(
            success=True,
            message="Health record created successfully",
            data=HealthRecordResponse(
                **result["hr"],
                patient=UserResponse(**result["patient"]),
                doctor=UserResponse(**result["doctor"])
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health-records/{health_record_id}", response_model=SingleResourceResponse)
async def get_health_record(health_record_id: str, request: Request):
    """Get health record by ID with all associated data"""
    try:
        result = await neo4j_service.get_health_record_by_id(health_record_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Health record not found")
        
        # Convert Neo4j date/time objects to Python native types
        result = convert_neo4j_dates(result)
        
        # Process medications from the new structure
        medications = []
        if result.get("medications"):
            for med_data in result["medications"]:
                if med_data.get("medication"):
                    med = med_data["medication"]
                    medications.append(Medication(**med))
        
        # Log audit entry
        await audit_service.log_action(
            user_id="system",  # Could be enhanced to get actual user
            user_name="System",
            action=AuditAction.READ,
            resource_type="health_record",
            resource_id=health_record_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return SingleResourceResponse(
            success=True,
            message="Health record retrieved successfully",
            data=HealthRecordResponse(
                **result["hr"],
                patient=UserResponse(**result["patient"]),
                doctor=UserResponse(**result["doctor"]),
                medications=medications
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/health-records/{health_record_id}", response_model=SingleResourceResponse)
async def update_health_record(health_record_id: str, health_record_update: HealthRecordUpdate, request: Request):
    """Update health record information"""
    try:
        update_data = {k: v for k, v in health_record_update.model_dump().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updated_record = await neo4j_service.update_health_record(health_record_id, update_data)
        
        if not updated_record:
            raise HTTPException(status_code=404, detail="Health record not found")
        
        # Convert Neo4j date/time objects to Python native types
        updated_record = convert_neo4j_dates(updated_record)
        
        # Log audit entry
        await audit_service.log_action(
            user_id="system",
            user_name="System",
            action=AuditAction.UPDATE,
            resource_type="health_record",
            resource_id=health_record_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details=update_data
        )
        
        return SingleResourceResponse(
            success=True,
            message="Health record updated successfully",
            data=HealthRecordResponse(
                **updated_record["hr"],
                patient=UserResponse(**updated_record["patient"]),
                doctor=UserResponse(**updated_record["doctor"])
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/health-records/{health_record_id}", response_model=BaseResponse)
async def delete_health_record(health_record_id: str, request: Request):
    """Delete health record"""
    try:
        record = await neo4j_service.get_health_record_by_id(health_record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Health record not found")
        
        await neo4j_service.delete_health_record(health_record_id)
        
        # Log audit entry
        await audit_service.log_action(
            user_id="system",
            user_name="System",
            action=AuditAction.DELETE,
            resource_type="health_record",
            resource_id=health_record_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return BaseResponse(
            success=True,
            message="Health record deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health-records", response_model=HealthRecordListResponse)
async def list_health_records(
    patient_id: Optional[str] = None,
    doctor_id: Optional[str] = None,
    status: Optional[HealthRecordStatus] = None,
    ailment: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """List health records with filtering"""
    try:
        filters = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "status": status.value if status else None,
            "ailment": ailment,
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None
        }
        
        result = await neo4j_service.list_health_records(filters, skip, limit)
        
        # Convert Neo4j date/time objects to Python native types
        records = []
        for record_data in result["records"]:
            record_data = convert_neo4j_dates(record_data)
            records.append(HealthRecordResponse(
                **record_data["hr"],
                patient=UserResponse(**record_data["patient"]),
                doctor=UserResponse(**record_data["doctor"])
            ))
        
        return HealthRecordListResponse(
            success=True,
            message="Health records retrieved successfully",
            data=records,
            total=result["total"],
            pagination=PaginationParams(skip=skip, limit=limit)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# FILE MANAGEMENT ENDPOINTS
# =============================================================================

@app.post("/health-records/{health_record_id}/files", response_model=SingleResourceResponse, status_code=201)
async def upload_file(
    health_record_id: str,
    file: UploadFile = File(...),
    uploaded_by: str = Query(..., description="User ID of the person uploading the file"),
    description: Optional[str] = None,
    category: FileCategory = FileCategory.OTHER,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Upload and process a file (triggers AI processing pipeline)"""
    try:
        # Validate file type
        file_extension = file.filename.split('.')[-1].upper() if '.' in file.filename else ''
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(status_code=400, detail=f"File type {file_extension} not allowed")
        
        # Validate that the uploader exists
        uploader = await neo4j_service.get_user_by_id(uploaded_by)
        if not uploader:
            raise HTTPException(status_code=400, detail="Uploader user not found")
        
        # Save file
        file_path = await file_service.save_file(file, health_record_id)
        
        # Create file record
        file_data = {
            "filename": file.filename,
            "file_type": file_extension,
            "file_size": file.size,
            "storage_path": file_path,
            "description": description,
            "category": category,
            "uploaded_by": uploaded_by,
            "file_status": FileStatus.PROCESSING,
            "layman_summary": None,
            "doctor_summary": None,
            "parsed_content": None,  # Will be populated during processing
            "file_hash": hashlib.md5(file.filename.encode()).hexdigest()
        }
        
        created_file = await neo4j_service.create_file(health_record_id, file_data)
        
        if not created_file:
            raise HTTPException(status_code=400, detail="Failed to create file record")
        
        # Convert Neo4j date/time objects to Python native types
        created_file = convert_neo4j_dates(created_file)
        
        # Trigger background processing
        background_tasks.add_task(
            file_service.process_file_async,
            created_file["id"],
            file_path,
            health_record_id
        )
        
        return SingleResourceResponse(
            success=True,
            message="File uploaded successfully and processing started",
            data=FileResponseSchema(**created_file)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/health-records/{health_record_id}/appointments", response_model=SingleResourceResponse, status_code=201)
async def create_appointment(
    health_record_id: str, 
    appointment: AppointmentCreate, 
    uploaded_by: str = Query(..., description="User ID of the doctor creating the appointment"),
    request: Request = None
):
    """Create appointment record"""
    try:
        # Validate that the uploader exists and is a doctor
        uploader = await neo4j_service.get_user_by_id(uploaded_by)
        if not uploader:
            raise HTTPException(status_code=400, detail="Uploader user not found")
        if uploader.get("user_type") != "DOCTOR":
            raise HTTPException(status_code=400, detail="Only doctors can create appointments")
        
        appointment_data = appointment.model_dump()
        appointment_data.update({
            "filename": appointment_data["appointment_title"],
            "file_type": FileType.APPOINTMENT,
            "file_size": None,
            "storage_path": None,
            "category": FileCategory.APPOINTMENT,
            "uploaded_by": uploaded_by,
            "file_status": FileStatus.PROCESSED,
            "parsed_content": None,  # Appointments don't have parsed content
            "file_hash": None
        })
        
        created_appointment = await neo4j_service.create_file(health_record_id, appointment_data)
        
        if not created_appointment:
            raise HTTPException(status_code=400, detail="Failed to create appointment")
        
        # Convert Neo4j date/time objects to Python native types
        created_appointment = convert_neo4j_dates(created_appointment)
        
        # Log audit entry
        if request:
            await audit_service.log_action(
                user_id=uploaded_by,
                user_name=uploader["name"],
                action=AuditAction.CREATE,
                resource_type="appointment",
                resource_id=created_appointment["id"],
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent")
            )
        
        return SingleResourceResponse(
            success=True,
            message="Appointment created successfully",
            data=FileResponseSchema(**created_appointment)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health-records/{health_record_id}/files", response_model=FileListResponse)
async def list_files(
    health_record_id: str,
    file_type: Optional[FileType] = None,
    category: Optional[FileCategory] = None,
    uploaded_by: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """List files for health record"""
    try:
        filters = {
            "file_type": file_type.value if file_type else None,
            "category": category.value if category else None,
            "uploaded_by": uploaded_by
        }
        
        result = await neo4j_service.list_files(health_record_id, filters, skip, limit)
        
        # Convert Neo4j date/time objects to Python native types
        files = []
        for file_data in result["files"]:
            file_data = convert_neo4j_dates(file_data)
            file_info = file_data["f"]
            uploader = file_data.get("uploader", {})
            file_info["uploaded_by_name"] = uploader.get("name") if uploader else None
            files.append(FileResponseSchema(**file_info))
        
        return FileListResponse(
            success=True,
            message="Files retrieved successfully",
            data=files,
            total=result["total"],
            pagination=PaginationParams(skip=skip, limit=limit)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{file_id}", response_model=SingleResourceResponse)
async def get_file(file_id: str, summary_type: Optional[SummaryType] = None, request: Request = None):
    """Get file details with appropriate summary based on user type"""
    try:
        result = await neo4j_service.get_file_by_id(file_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Convert Neo4j date/time objects to Python native types
        result = convert_neo4j_dates(result)
        
        file_info = result["f"]
        uploader = result.get("uploader", {})
        file_info["uploaded_by_name"] = uploader.get("name") if uploader else None
        
        # Log audit entry
        if request:
            await audit_service.log_action(
                user_id="system",
                user_name="System",
                action=AuditAction.READ,
                resource_type="file",
                resource_id=file_id,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent")
            )
        
        return SingleResourceResponse(
            success=True,
            message="File retrieved successfully",
            data=FileResponseSchema(**file_info)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/files/{file_id}", response_model=SingleResourceResponse)
async def update_file(file_id: str, file_update: FileUpdate, request: Request):
    """Update file summaries and metadata"""
    try:
        update_data = {k: v for k, v in file_update.model_dump().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updated_file = await neo4j_service.update_file(file_id, update_data)
        
        if not updated_file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Convert Neo4j date/time objects to Python native types
        updated_file = convert_neo4j_dates(updated_file)
        
        # Log audit entry
        await audit_service.log_action(
            user_id="system",
            user_name="System",
            action=AuditAction.UPDATE,
            resource_type="file",
            resource_id=file_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details=update_data
        )
        
        return SingleResourceResponse(
            success=True,
            message="File updated successfully",
            data=FileResponseSchema(**updated_file)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/files/{file_id}", response_model=BaseResponse)
async def delete_file(file_id: str, request: Request):
    """Delete file"""
    try:
        file_info = await neo4j_service.get_file_by_id(file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete from storage
        if file_info["f"]["storage_path"]:
            await file_service.delete_file(file_info["f"]["storage_path"])
        
        # Delete from database
        await neo4j_service.delete_file(file_id)
        
        # Log audit entry
        await audit_service.log_action(
            user_id="system",
            user_name="System",
            action=AuditAction.DELETE,
            resource_type="file",
            resource_id=file_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return BaseResponse(
            success=True,
            message="File deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{file_id}/download")
async def download_file(file_id: str, request: Request):
    """Download original file"""
    try:
        result = await neo4j_service.get_file_by_id(file_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = result["f"]
        
        if not file_info["storage_path"] or not os.path.exists(file_info["storage_path"]):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        # Log audit entry
        await audit_service.log_action(
            user_id="system",
            user_name="System",
            action=AuditAction.READ,
            resource_type="file",
            resource_id=file_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details={"action": "download"}
        )
        
        # Return file as a stream using FastAPI's FileResponse
        return FileResponse(
            path=file_info["storage_path"],
            filename=file_info["filename"],
            media_type="application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{file_id}/status")
async def get_file_status(file_id: str, request: Request):
    """Get file processing status and statistics"""
    try:
        result = await neo4j_service.get_file_by_id(file_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = result["f"]
        parsed_content = file_info.get("parsed_content", "")
        has_content = bool(parsed_content and len(parsed_content.strip()) > 0)
        
        # Log audit entry
        await audit_service.log_action(
            user_id="system",
            user_name="System",
            action=AuditAction.READ,
            resource_type="file_status",
            resource_id=file_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return {
            "success": True,
            "file_id": file_id,
            "filename": file_info["filename"],
            "file_status": file_info["file_status"],
            "has_parsed_content": has_content,
            "content_length": len(parsed_content) if parsed_content else 0,
            "has_layman_summary": bool(file_info.get("layman_summary")),
            "has_doctor_summary": bool(file_info.get("doctor_summary")),
            "created_at": file_info["created_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/files/{file_id}/regenerate-summary", response_model=SummaryResponse)
async def regenerate_file_summary(
    file_id: str, 
    summary_type: SummaryType = SummaryType.BOTH,
    context: Optional[str] = None,
    request: Request = None
):
    """Regenerate summaries using stored parsed content"""
    try:
        # Check if file exists
        result = await neo4j_service.get_file_by_id(file_id)
        if not result:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Generate new summaries using stored content
        summaries = await agent_service.generate_summary_from_file_id(file_id, summary_type, context)
        
        # Update file with new summaries
        update_data = {}
        if summaries.layman_summary:
            update_data["layman_summary"] = summaries.layman_summary
        if summaries.doctor_summary:
            update_data["doctor_summary"] = summaries.doctor_summary
        
        if update_data:
            await neo4j_service.update_file(file_id, update_data)
        
        # Log audit entry
        if request:
            await audit_service.log_action(
                user_id="system",
                user_name="System",
                action=AuditAction.UPDATE,
                resource_type="file_summary",
                resource_id=file_id,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent")
            )
        
        return summaries
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# MEDICATION ENDPOINTS
# =============================================================================

@app.post("/health-records/{health_record_id}/medications", response_model=SingleResourceResponse, status_code=201)
async def add_medication(
    health_record_id: str, 
    medication: MedicationCreate, 
    prescribed_by: str = Query(..., description="User ID of the doctor prescribing the medication"),
    request: Request = None
):
    """Add medication to health record"""
    try:
        # Validate that the prescriber exists and is a doctor
        prescriber = await neo4j_service.get_user_by_id(prescribed_by)
        if not prescriber:
            raise HTTPException(status_code=400, detail="Prescriber user not found")
        if prescriber.get("user_type") != "DOCTOR":
            raise HTTPException(status_code=400, detail="Only doctors can prescribe medications")
        
        medication_data = medication.model_dump()
        medication_data["prescribed_by"] = prescribed_by
        
        medication_id = await neo4j_service.add_medication(health_record_id, medication_data)
        
        if not medication_id:
            raise HTTPException(status_code=400, detail="Failed to add medication")
        
        # Log audit entry
        if request:
            await audit_service.log_action(
                user_id=prescribed_by,
                user_name=prescriber["name"],
                action=AuditAction.CREATE,
                resource_type="medication",
                resource_id=medication_id,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent")
            )
        
        return SingleResourceResponse(
            success=True,
            message="Medication added successfully",
            data=MedicationResponse(medication_id=medication_id)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/health-records/{health_record_id}/medications/{medication_id}/approve", response_model=BaseResponse)
async def approve_medication(
    health_record_id: str, 
    medication_id: str, 
    approval: MedicationApproval,
    request: Request
):
    """Approve medication (doctor only)"""
    try:
        success = await neo4j_service.approve_medication(
            health_record_id, 
            medication_id, 
            approval.approved_by
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to approve medication")
        
        # Log audit entry
        await audit_service.log_action(
            user_id=approval.approved_by,
            user_name="System",
            action=AuditAction.APPROVE,
            resource_type="medication",
            resource_id=medication_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return BaseResponse(
            success=True,
            message="Medication approved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health-records/{health_record_id}/medications", response_model=List[Medication])
async def list_medications(
    health_record_id: str,
    status: Optional[MedicationStatus] = None
):
    """List medications for health record"""
    try:
        medications = await neo4j_service.get_medications(
            health_record_id, 
            status.value if status else None
        )
        
        # Convert Neo4j date/time objects to Python native types
        medications = [convert_neo4j_dates(med) for med in medications]
        
        return [Medication(**med) for med in medications]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# AGENT INTERACTION ENDPOINTS
# =============================================================================

# @app.post("/agent/query", response_model=AgentResponse)
# async def query_agent(query: AgentQuery):
#     """Send natural language query to the health agent"""
#     try:
#         response = await agent_service.process_query(query)
#         return response
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/agent/summarize", response_model=SummaryResponse)
# async def generate_summary(request: SummaryRequest, background_tasks: BackgroundTasks):
#     """Generate layman and/or doctor summaries using AI"""
#     try:
#         response = await agent_service.generate_summary(request)
#         return response
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.get("/medicines/{medicine_name}/summary")
async def get_medicine_summary(medicine_name: str):
    """Get comprehensive medicine summary using Perplexity AI"""
    try:
        summary = await agent_service.generate_medicine_summary_via_perplexity(medicine_name)
        return {
            "success": True,
            "medicine_name": medicine_name,
            "summary": summary,
            "source": "openrouter_perplexity"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/medicines/{medicine_name}/info")
async def get_medicine_info(medicine_name: str):
    """Get detailed structured medicine information using Perplexity AI"""
    try:
        from app.services.perplexity_service import perplexity_service
        info = await perplexity_service.search_medicine_info(medicine_name)
        return {
            "success": True,
            "medicine_name": medicine_name,
            "info": info,
            "source": "openrouter_perplexity"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/files/{file_id}/reprocess", response_model=SingleResourceResponse)
async def reprocess_file(file_id: str, background_tasks: BackgroundTasks):
    """Reprocess file through AI pipeline for updated summaries"""
    try:
        result = await neo4j_service.get_file_by_id(file_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = result["f"]
        
        # Trigger background reprocessing
        background_tasks.add_task(
            file_service.process_file_async,
            file_id,
            file_info["storage_path"],
            "system"  # Could be enhanced to get health record ID
        )
        
        return SingleResourceResponse(
            success=True,
            message="File reprocessing started",
            data={"file_id": file_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# SEARCH ENDPOINTS
# =============================================================================

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Search across health records, files, and medications"""
    try:
        results = []
        
        if "health_records" in request.search_in:
            health_records = await neo4j_service.search_health_records(
                request.query, request.user_id, request.user_type.value
            )
            for record in health_records:
                results.append(SearchResult(
                    type="health_record",
                    id=record["hr"]["id"],
                    title=record["hr"]["title"],
                    snippet=record["hr"]["ailment"],
                    relevance_score=0.8  # Placeholder
                ))
        
        if "files" in request.search_in:
            files = await neo4j_service.search_files(
                request.query, request.user_id, request.user_type.value
            )
            for file in files:
                results.append(SearchResult(
                    type="file",
                    id=file["filename"],  # Placeholder ID
                    title=file["filename"],
                    snippet=file["summary"] or file["filename"],
                    relevance_score=0.7  # Placeholder
                ))
        
        return SearchResponse(
            success=True,
            message="Search completed successfully",
            data=results,
            total=len(results),
            query=request.query
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """System health check"""
    try:
        # Check database connectivity
        db_connected = False
        try:
            await neo4j_service.execute_query("RETURN 1")
            db_connected = True
        except:
            pass
        
        return HealthStatus(
            status="healthy" if db_connected else "unhealthy",
            database_connected=db_connected,
            agent_service_available=True,  # Placeholder
            file_processing_available=True,  # Placeholder
            timestamp=datetime.now()
        )
    except Exception as e:
        return HealthStatus(
            status="unhealthy",
            database_connected=False,
            agent_service_available=False,
            file_processing_available=False,
            timestamp=datetime.now()
        )

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    error_response = ErrorResponse(
        message=exc.detail,
        errors=[ErrorDetail(message=exc.detail, code=str(exc.status_code))]
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    error_response = ErrorResponse(
        message="Internal server error",
        errors=[ErrorDetail(message=str(exc), code="500")]
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode='json')
    )

@app.get("/files/{file_id}/content")
async def get_file_content(file_id: str, request: Request):
    """Get parsed content of a file"""
    try:
        result = await neo4j_service.get_file_by_id(file_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = result["f"]
        
        # Check if parsed content exists
        if not file_info.get("parsed_content"):
            raise HTTPException(status_code=404, detail="File content not available")
        
        # Log audit entry
        await audit_service.log_action(
            user_id="system",
            user_name="System",
            action=AuditAction.READ,
            resource_type="file_content",
            resource_id=file_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return {
            "success": True,
            "file_id": file_id,
            "filename": file_info["filename"],
            "content": file_info["parsed_content"],
            "content_length": len(file_info["parsed_content"])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 