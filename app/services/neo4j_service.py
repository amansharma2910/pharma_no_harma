from neo4j import GraphDatabase, Driver
from typing import Dict, List, Optional, Any
from app.core.config import settings
import logging
from datetime import datetime, date
import uuid
import json

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
            self.driver.verify_connectivity()
            logger.info("Connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    async def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
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
                result = session.execute_write(self._execute_query, query, parameters or {})
                return result
        except Exception as e:
            logger.error(f"Write query execution failed: {e}")
            raise
    
    @staticmethod
    def _execute_query(tx, query: str, parameters: Dict[str, Any]):
        result = tx.run(query, parameters)
        return [record.data() for record in result]

    # =============================================================================
    # USER OPERATIONS
    # =============================================================================

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        query = """
        CREATE (u:User {
            id: $user_id,
            email: $email,
            name: $name,
            phone: $phone,
            date_of_birth: date($date_of_birth),
            gender: $gender,
            address: $address,
            user_type: $user_type,
            specialization: $specialization,
            license_number: $license_number,
            created_at: datetime(),
            updated_at: datetime()
        })
        RETURN u
        """
        
        parameters = {
            "user_id": user_id,
            **user_data
        }
        
        result = await self.execute_write_query(query, parameters)
        return result[0]["u"] if result else None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        query = "MATCH (u:User {id: $user_id}) RETURN u"
        result = await self.execute_query(query, {"user_id": user_id})
        return result[0]["u"] if result else None

    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user information"""
        set_clauses = []
        parameters = {"user_id": user_id}
        
        for key, value in update_data.items():
            if value is not None:
                if key == "date_of_birth":
                    set_clauses.append(f"u.{key} = date(${key})")
                else:
                    set_clauses.append(f"u.{key} = ${key}")
                parameters[key] = value
        
        if not set_clauses:
            return await self.get_user_by_id(user_id)
        
        set_clauses.append("u.updated_at = datetime()")
        
        query = f"""
        MATCH (u:User {{id: $user_id}})
        SET {', '.join(set_clauses)}
        RETURN u
        """
        
        result = await self.execute_write_query(query, parameters)
        return result[0]["u"] if result else None

    async def delete_user(self, user_id: str) -> bool:
        """Delete user and all relationships"""
        query = "MATCH (u:User {id: $user_id}) DETACH DELETE u"
        await self.execute_write_query(query, {"user_id": user_id})
        return True

    async def list_users(self, user_type: Optional[str] = None, skip: int = 0, limit: int = 20) -> Dict[str, Any]:
        """List users with optional filtering"""
        where_clause = ""
        parameters = {"skip": skip, "limit": limit}
        
        if user_type:
            where_clause = "WHERE u.user_type = $user_type"
            parameters["user_type"] = user_type
        
        query = f"""
        MATCH (u:User)
        {where_clause}
        RETURN u
        ORDER BY u.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        
        count_query = f"""
        MATCH (u:User)
        {where_clause}
        RETURN count(u) as total
        """
        
        users = await self.execute_query(query, parameters)
        total_result = await self.execute_query(count_query, parameters)
        total = total_result[0]["total"] if total_result else 0
        
        return {
            "users": [user["u"] for user in users],
            "total": total
        }

    # =============================================================================
    # HEALTH RECORD OPERATIONS
    # =============================================================================

    async def create_health_record(self, health_record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new health record with relationships"""
        health_record_id = str(uuid.uuid4())
        share_token = str(uuid.uuid4())
        
        query = """
        MATCH (patient:User {id: $patient_id, user_type: "PATIENT"})
        MATCH (doctor:User {id: $doctor_id, user_type: "DOCTOR"})
        CREATE (hr:HealthRecord {
            id: $health_record_id,
            title: $title,
            ailment: $ailment,
            status: "ACTIVE",
            created_by: $created_by,
            layman_summary: $layman_summary,
            medical_summary: $medical_summary,
            overall_report: $overall_report,
            share_token: $share_token,
            share_type: $share_type,
            created_at: datetime(),
            updated_at: datetime(),
            last_activity: datetime()
        })
        CREATE (patient)-[:OWNS]->(hr)
        CREATE (doctor)-[:MANAGES]->(hr)
        CREATE (doctor)-[:TREATS]->(patient)
        RETURN hr, patient, doctor
        """
        
        parameters = {
            "health_record_id": health_record_id,
            "share_token": share_token,
            **health_record_data
        }
        
        result = await self.execute_write_query(query, parameters)
        return result[0] if result else None

    async def get_health_record_by_id(self, health_record_id: str) -> Optional[Dict[str, Any]]:
        """Get health record with all relationships"""
        query = """
        MATCH (hr:HealthRecord {id: $health_record_id})
        OPTIONAL MATCH (patient:User)-[:OWNS]->(hr)
        OPTIONAL MATCH (doctor:User)-[:MANAGES]->(hr)
        OPTIONAL MATCH (hr)-[:HAS_FILE]->(f:File)
        OPTIONAL MATCH (uploader:User)-[:UPLOADED]->(f)
        OPTIONAL MATCH (hr)-[:HAS_MEDICATION]->(m:Medication)
        OPTIONAL MATCH (prescriber:User)-[:PRESCRIBED]->(m)
        OPTIONAL MATCH (approver:User)-[:APPROVED]->(m)
        RETURN hr, patient, doctor,
               collect(DISTINCT {file: f, uploader: uploader}) as files,
               collect(DISTINCT {medication: m, prescriber: prescriber, approver: approver}) as medications
        """
        
        result = await self.execute_query(query, {"health_record_id": health_record_id})
        return result[0] if result else None

    async def update_health_record(self, health_record_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update health record"""
        set_clauses = []
        parameters = {"health_record_id": health_record_id}
        
        for key, value in update_data.items():
            if value is not None:
                set_clauses.append(f"hr.{key} = ${key}")
                parameters[key] = value
        
        if not set_clauses:
            return await self.get_health_record_by_id(health_record_id)
        
        set_clauses.extend([
            "hr.updated_at = datetime()",
            "hr.last_activity = datetime()"
        ])
        
        query = f"""
        MATCH (hr:HealthRecord {{id: $health_record_id}})
        OPTIONAL MATCH (patient:User)-[:OWNS]->(hr)
        OPTIONAL MATCH (doctor:User)-[:MANAGES]->(hr)
        SET {', '.join(set_clauses)}
        RETURN hr, patient, doctor
        """
        
        result = await self.execute_write_query(query, parameters)
        if result:
            return {
                "hr": result[0]["hr"],
                "patient": result[0]["patient"],
                "doctor": result[0]["doctor"]
            }
        return None

    async def delete_health_record(self, health_record_id: str) -> bool:
        """Delete health record and all relationships"""
        query = "MATCH (hr:HealthRecord {id: $health_record_id}) DETACH DELETE hr"
        await self.execute_write_query(query, {"health_record_id": health_record_id})
        return True

    async def list_health_records(self, filters: Dict[str, Any], skip: int = 0, limit: int = 20) -> Dict[str, Any]:
        """List health records with filtering"""
        match_clauses = []
        where_clauses = []
        parameters = {"skip": skip, "limit": limit}
        
        # Build MATCH clauses for relationships
        if filters.get("patient_id"):
            match_clauses.append("(patient:User {id: $patient_id})-[:OWNS]->(hr:HealthRecord)")
            parameters["patient_id"] = filters["patient_id"]
        else:
            match_clauses.append("(patient:User)-[:OWNS]->(hr:HealthRecord)")
        
        if filters.get("doctor_id"):
            match_clauses.append("(doctor:User {id: $doctor_id})-[:MANAGES]->(hr)")
            parameters["doctor_id"] = filters["doctor_id"]
        else:
            match_clauses.append("(doctor:User)-[:MANAGES]->(hr)")
        
        # Build WHERE clauses for properties
        if filters.get("status"):
            where_clauses.append("hr.status = $status")
            parameters["status"] = filters["status"]
        
        if filters.get("ailment"):
            where_clauses.append("toLower(hr.ailment) CONTAINS toLower($ailment)")
            parameters["ailment"] = filters["ailment"]
        
        if filters.get("date_from"):
            where_clauses.append("hr.created_at >= datetime($date_from)")
            parameters["date_from"] = filters["date_from"]
        
        if filters.get("date_to"):
            where_clauses.append("hr.created_at <= datetime($date_to)")
            parameters["date_to"] = filters["date_to"]
        
        # Construct the query
        match_clause = ", ".join(match_clauses)
        where_clause = " AND ".join(where_clauses) if where_clauses else ""
        
        query = f"""
        MATCH {match_clause}
        """
        
        if where_clause:
            query += f"WHERE {where_clause}\n"
        
        query += """
        RETURN hr, patient, doctor
        ORDER BY hr.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        
        count_query = f"""
        MATCH {match_clause}
        """
        
        if where_clause:
            count_query += f"WHERE {where_clause}\n"
        
        count_query += "RETURN count(hr) as total"
        
        records = await self.execute_query(query, parameters)
        total_result = await self.execute_query(count_query, parameters)
        total = total_result[0]["total"] if total_result else 0
        
        return {
            "records": records,
            "total": total
        }

    # =============================================================================
    # FILE OPERATIONS
    # =============================================================================

    async def create_file(self, health_record_id: str, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new file"""
        file_id = str(uuid.uuid4())
        
        # Base properties that all files have
        base_properties = [
            "id: $file_id",
            "filename: $filename",
            "file_type: $file_type",
            "file_size: $file_size",
            "storage_path: $storage_path",
            "description: $description",
            "category: $category",
            "uploaded_by: $uploaded_by",
            "file_status: $file_status",
            "layman_summary: $layman_summary",
            "doctor_summary: $doctor_summary",
            "parsed_content: $parsed_content",
            "created_at: datetime()",
            "file_hash: $file_hash"
        ]
        
        # Add appointment-specific properties only if it's an appointment
        if file_data.get("file_type") == "APPOINTMENT":
            appointment_properties = [
                "appointment_date: $appointment_date",
                "duration_minutes: $duration_minutes",
                "chief_complaint: $chief_complaint",
                "diagnosis: $diagnosis",
                "treatment_plan: $treatment_plan",
                "next_appointment: $next_appointment"
            ]
            base_properties.extend(appointment_properties)
        
        properties_str = ", ".join(base_properties)
        
        query = f"""
        MATCH (hr:HealthRecord {{id: $health_record_id}})
        MATCH (uploader:User {{id: $uploaded_by}})
        CREATE (f:File {{
            {properties_str}
        }})
        CREATE (hr)-[:HAS_FILE]->(f)
        CREATE (uploader)-[:UPLOADED]->(f)
        SET hr.last_activity = datetime()
        RETURN f
        """
        
        parameters = {
            "file_id": file_id,
            "health_record_id": health_record_id,
            **file_data
        }
        
        result = await self.execute_write_query(query, parameters)
        return result[0]["f"] if result else None

    async def get_file_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file by ID"""
        query = """
        MATCH (f:File {id: $file_id})
        OPTIONAL MATCH (uploader:User)-[:UPLOADED]->(f)
        RETURN f, uploader
        """
        
        result = await self.execute_query(query, {"file_id": file_id})
        return result[0] if result else None

    async def update_file(self, file_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update file"""
        set_clauses = []
        parameters = {"file_id": file_id}
        
        for key, value in update_data.items():
            if value is not None:
                set_clauses.append(f"f.{key} = ${key}")
                parameters[key] = value
        
        if not set_clauses:
            return await self.get_file_by_id(file_id)
        
        query = f"""
        MATCH (f:File {{id: $file_id}})
        SET {', '.join(set_clauses)}
        RETURN f
        """
        
        result = await self.execute_write_query(query, parameters)
        return result[0]["f"] if result else None

    async def delete_file(self, file_id: str) -> bool:
        """Delete file"""
        query = "MATCH (f:File {id: $file_id}) DETACH DELETE f"
        await self.execute_write_query(query, {"file_id": file_id})
        return True

    async def list_files(self, health_record_id: str, filters: Dict[str, Any], skip: int = 0, limit: int = 20) -> Dict[str, Any]:
        """List files for health record"""
        match_clauses = ["(hr:HealthRecord {id: $health_record_id})-[:HAS_FILE]->(f:File)"]
        where_clauses = []
        parameters = {"health_record_id": health_record_id, "skip": skip, "limit": limit}
        
        # Build WHERE clauses for properties
        if filters.get("file_type"):
            where_clauses.append("f.file_type = $file_type")
            parameters["file_type"] = filters["file_type"]
        
        if filters.get("category"):
            where_clauses.append("f.category = $category")
            parameters["category"] = filters["category"]
        
        # Build additional MATCH clauses for relationships
        if filters.get("uploaded_by"):
            match_clauses.append("(uploader:User {id: $uploaded_by})-[:UPLOADED]->(f)")
            parameters["uploaded_by"] = filters["uploaded_by"]
        
        # Construct the query
        match_clause = ", ".join(match_clauses)
        where_clause = " AND ".join(where_clauses) if where_clauses else ""
        
        query = f"""
        MATCH {match_clause}
        """
        
        if where_clause:
            query += f"WHERE {where_clause}\n"
        
        query += """
        OPTIONAL MATCH (uploader:User)-[:UPLOADED]->(f)
        RETURN f, uploader
        ORDER BY f.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        
        count_query = f"""
        MATCH {match_clause}
        """
        
        if where_clause:
            count_query += f"WHERE {where_clause}\n"
        
        count_query += "RETURN count(f) as total"
        
        files = await self.execute_query(query, parameters)
        total_result = await self.execute_query(count_query, parameters)
        total = total_result[0]["total"] if total_result else 0
        
        return {
            "files": files,
            "total": total
        }

    # =============================================================================
    # MEDICATION OPERATIONS
    # =============================================================================

    async def add_medication(self, health_record_id: str, medication_data: Dict[str, Any]) -> str:
        """Add medication to health record"""
        medication_id = str(uuid.uuid4())
        
        # Convert date objects to strings for Neo4j compatibility
        processed_data = {}
        for key, value in medication_data.items():
            if isinstance(value, date):
                processed_data[key] = value.isoformat()
            else:
                processed_data[key] = value
        
        query = """
        MATCH (hr:HealthRecord {id: $health_record_id})
        MATCH (prescriber:User {id: $prescribed_by})
        CREATE (m:Medication {
            id: $medication_id,
            medication_name: $medication_name,
            dosage: $dosage,
            frequency: $frequency,
            duration_days: $duration_days,
            instructions: $instructions,
            start_date: $start_date,
            end_date: $end_date,
            status: "PRESCRIBED",
            prescribed_by: $prescribed_by,
            approved_by: null,
            side_effects: $side_effects,
            created_at: datetime(),
            approved_at: null
        })
        CREATE (hr)-[:HAS_MEDICATION]->(m)
        CREATE (prescriber)-[:PRESCRIBED]->(m)
        SET hr.updated_at = datetime(),
            hr.last_activity = datetime()
        RETURN m
        """
        
        parameters = {
            "medication_id": medication_id,
            "health_record_id": health_record_id,
            **processed_data
        }
        
        await self.execute_write_query(query, parameters)
        return medication_id

    async def approve_medication(self, health_record_id: str, medication_id: str, approved_by: str) -> bool:
        """Approve medication"""
        query = """
        MATCH (hr:HealthRecord {id: $health_record_id})-[:HAS_MEDICATION]->(m:Medication {id: $medication_id})
        MATCH (approver:User {id: $approved_by})
        SET m.status = "APPROVED",
            m.approved_by = $approved_by,
            m.approved_at = datetime(),
            hr.updated_at = datetime()
        CREATE (approver)-[:APPROVED]->(m)
        RETURN m
        """
        
        await self.execute_write_query(query, {
            "health_record_id": health_record_id,
            "medication_id": medication_id,
            "approved_by": approved_by
        })
        return True

    async def get_medications(self, health_record_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get medications for health record"""
        where_clause = ""
        parameters = {"health_record_id": health_record_id}
        
        if status:
            where_clause = "AND m.status = $status"
            parameters["status"] = status
        
        query = f"""
        MATCH (hr:HealthRecord {{id: $health_record_id}})-[:HAS_MEDICATION]->(m:Medication)
        WHERE true {where_clause}
        OPTIONAL MATCH (prescriber:User)-[:PRESCRIBED]->(m)
        OPTIONAL MATCH (approver:User)-[:APPROVED]->(m)
        RETURN m, prescriber.name as prescriber_name, approver.name as approver_name
        ORDER BY m.created_at DESC
        """
        
        result = await self.execute_query(query, parameters)
        return [record["m"] for record in result]

    # =============================================================================
    # SEARCH OPERATIONS
    # =============================================================================

    async def search_health_records(self, query: str, user_id: str, user_type: str) -> List[Dict[str, Any]]:
        """Search health records"""
        if user_type == "PATIENT":
            base_query = """
            MATCH (patient:User {id: $user_id})-[:OWNS]->(hr:HealthRecord)
            """
        else:
            base_query = """
            MATCH (doctor:User {id: $user_id})-[:MANAGES]->(hr:HealthRecord)
            """
        
        search_query = f"""
        {base_query}
        WHERE toLower(hr.title) CONTAINS toLower($query) 
           OR toLower(hr.ailment) CONTAINS toLower($query)
        OPTIONAL MATCH (patient:User)-[:OWNS]->(hr)
        OPTIONAL MATCH (doctor:User)-[:MANAGES]->(hr)
        RETURN hr, patient.name as patient_name, doctor.name as doctor_name
        LIMIT 20
        """
        
        result = await self.execute_query(search_query, {
            "user_id": user_id,
            "query": query
        })
        
        return result

    async def search_files(self, query: str, user_id: str, user_type: str) -> List[Dict[str, Any]]:
        """Search files including parsed content"""
        if user_type == "PATIENT":
            base_query = """
            MATCH (patient:User {id: $user_id})-[:OWNS]->(hr:HealthRecord)-[:HAS_FILE]->(f:File)
            """
            summary_field = "f.layman_summary"
        else:
            base_query = """
            MATCH (doctor:User {id: $user_id})-[:MANAGES]->(hr:HealthRecord)-[:HAS_FILE]->(f:File)
            """
            summary_field = "f.doctor_summary"
        
        search_query = f"""
        {base_query}
        WHERE toLower({summary_field}) CONTAINS toLower($query)
           OR toLower(f.filename) CONTAINS toLower($query)
           OR toLower(f.parsed_content) CONTAINS toLower($query)
        OPTIONAL MATCH (patient:User)-[:OWNS]->(hr)
        RETURN f.filename, f.category, {summary_field} as summary, f.created_at,
               hr.title as health_record, patient.name as patient_name,
               f.parsed_content as content_preview
        LIMIT 20
        """
        
        result = await self.execute_query(search_query, {
            "user_id": user_id,
            "query": query
        })
        
        return result

    # =============================================================================
    # AUDIT OPERATIONS
    # =============================================================================

    async def create_audit_log(self, audit_data: Dict[str, Any]) -> bool:
        """Create audit log entry"""
        audit_id = str(uuid.uuid4())
        
        # Convert details to JSON string if it's a dictionary
        if audit_data.get("details") and isinstance(audit_data["details"], dict):
            audit_data["details"] = json.dumps(audit_data["details"])
        
        query = """
        CREATE (a:AuditLog {
            id: $audit_id,
            user_id: $user_id,
            user_name: $user_name,
            action: $action,
            resource_type: $resource_type,
            resource_id: $resource_id,
            details: $details,
            ip_address: $ip_address,
            user_agent: $user_agent,
            timestamp: datetime()
        })
        """
        
        await self.execute_write_query(query, {
            "audit_id": audit_id,
            **audit_data
        })
        return True

    async def get_audit_logs(self, filters: Dict[str, Any], skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        """Get audit logs with filtering"""
        where_clauses = []
        parameters = {"skip": skip, "limit": limit}
        
        for key, value in filters.items():
            if value is not None:
                where_clauses.append(f"a.{key} = ${key}")
                parameters[key] = value
        
        where_clause = " AND ".join(where_clauses) if where_clauses else ""
        
        query = f"""
        MATCH (a:AuditLog)
        {f"WHERE {where_clause}" if where_clause else ""}
        RETURN a
        ORDER BY a.timestamp DESC
        SKIP $skip
        LIMIT $limit
        """
        
        count_query = f"""
        MATCH (a:AuditLog)
        {f"WHERE {where_clause}" if where_clause else ""}
        RETURN count(a) as total
        """
        
        logs = await self.execute_query(query, parameters)
        total_result = await self.execute_query(count_query, parameters)
        total = total_result[0]["total"] if total_result else 0
        
        return {
            "logs": [log["a"] for log in logs],
            "total": total
        }

# Global instance
neo4j_service = Neo4jService() 