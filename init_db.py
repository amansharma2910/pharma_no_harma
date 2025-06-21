"""
Database Initialization Script for Health Records API
"""

import asyncio
import logging
from app.services.neo4j_service import neo4j_service
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_database():
    """Initialize Neo4j database with constraints and indexes"""
    try:
        # Connect to database
        await neo4j_service.connect()
        logger.info("Connected to Neo4j database")
        
        # Create constraints
        constraints = [
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
            "CREATE CONSTRAINT health_record_id_unique IF NOT EXISTS FOR (hr:HealthRecord) REQUIRE hr.id IS UNIQUE",
            "CREATE CONSTRAINT file_id_unique IF NOT EXISTS FOR (f:File) REQUIRE f.id IS UNIQUE"
        ]
        
        for constraint in constraints:
            await neo4j_service.execute_write_query(constraint)
            logger.info(f"Created constraint: {constraint}")
        
        # Create indexes
        indexes = [
            "CREATE INDEX user_email_index IF NOT EXISTS FOR (u:User) ON (u.email)",
            "CREATE INDEX user_type_index IF NOT EXISTS FOR (u:User) ON (u.user_type)",
            "CREATE INDEX health_record_status_index IF NOT EXISTS FOR (hr:HealthRecord) ON (hr.status)",
            "CREATE INDEX health_record_created_at IF NOT EXISTS FOR (hr:HealthRecord) ON (hr.created_at)",
            "CREATE INDEX health_record_last_activity IF NOT EXISTS FOR (hr:HealthRecord) ON (hr.last_activity)",
            "CREATE INDEX health_record_share_token IF NOT EXISTS FOR (hr:HealthRecord) ON (hr.share_token)",
            "CREATE INDEX file_type_index IF NOT EXISTS FOR (f:File) ON (f.file_type)",
            "CREATE INDEX file_category_index IF NOT EXISTS FOR (f:File) ON (f.category)",
            "CREATE INDEX file_created_at IF NOT EXISTS FOR (f:File) ON (f.created_at)",
            "CREATE INDEX appointment_date_index IF NOT EXISTS FOR (f:File) ON (f.appointment_date)"
        ]
        
        for index in indexes:
            await neo4j_service.execute_write_query(index)
            logger.info(f"Created index: {index}")
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        await neo4j_service.close()

async def create_sample_data():
    """Create sample data for testing"""
    try:
        await neo4j_service.connect()
        logger.info("Creating sample data...")
        
        # Create sample patients
        patients = [
            {
                "email": "john.doe@email.com",
                "name": "John Doe",
                "phone": "+1-555-0123",
                "date_of_birth": "1985-03-15",
                "gender": "Male",
                "address": "123 Main St, City, State",
                "user_type": "PATIENT"
            },
            {
                "email": "jane.smith@email.com",
                "name": "Jane Smith",
                "phone": "+1-555-0124",
                "date_of_birth": "1990-07-22",
                "gender": "Female",
                "address": "456 Oak Ave, City, State",
                "user_type": "PATIENT"
            }
        ]
        
        # Create sample doctors
        doctors = [
            {
                "email": "dr.wilson@hospital.com",
                "name": "Dr. Sarah Wilson",
                "phone": "+1-555-0200",
                "date_of_birth": "1975-12-10",
                "gender": "Female",
                "address": "789 Medical Center Dr, City, State",
                "user_type": "DOCTOR",
                "specialization": "Internal Medicine",
                "license_number": "MD12345"
            },
            {
                "email": "dr.brown@clinic.com",
                "name": "Dr. Michael Brown",
                "phone": "+1-555-0201",
                "date_of_birth": "1968-09-05",
                "gender": "Male",
                "address": "321 Health Plaza, City, State",
                "user_type": "DOCTOR",
                "specialization": "Orthopedics",
                "license_number": "MD67890"
            }
        ]
        
        # Create users
        created_users = []
        for user_data in patients + doctors:
            user = await neo4j_service.create_user(user_data)
            created_users.append(user)
            logger.info(f"Created user: {user['name']}")
        
        # Create sample health record
        if len(created_users) >= 2:
            patient = next(u for u in created_users if u["user_type"] == "PATIENT")
            doctor = next(u for u in created_users if u["user_type"] == "DOCTOR")
            
            health_record_data = {
                "title": "Annual Checkup 2024",
                "ailment": "Routine health examination",
                "patient_id": patient["id"],
                "doctor_id": doctor["id"],
                "created_by": doctor["id"],
                "layman_summary": "Patient had a routine annual checkup with normal results.",
                "medical_summary": "Annual physical examination completed. Vital signs within normal limits. No significant findings.",
                "overall_report": "Patient is in good health with no immediate concerns."
            }
            
            result = await neo4j_service.create_health_record(health_record_data)
            logger.info(f"Created health record: {result['hr']['title']}")
        
        logger.info("Sample data creation completed")
        
    except Exception as e:
        logger.error(f"Sample data creation failed: {e}")
        raise
    finally:
        await neo4j_service.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--sample-data":
        asyncio.run(create_sample_data())
    else:
        asyncio.run(init_database()) 