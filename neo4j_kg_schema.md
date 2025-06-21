# Neo4j Health Records Knowledge Graph Implementation Guide

This guide provides everything needed to implement a health records management system using Neo4j with a simplified 3-node schema.

## Schema Overview

### Node Types
- **User**: Patients and doctors
- **HealthRecord**: Treatment episodes between patient and doctor
- **File**: Documents, images, notes, and appointments

### Key Relationships
- `(:User)-[:OWNS]->(:HealthRecord)` - Patient owns records
- `(:User)-[:MANAGES]->(:HealthRecord)` - Doctor manages records  
- `(:HealthRecord)-[:HAS_FILE]->(:File)` - Records contain files/appointments
- `(:HealthRecord)-[:RELATED_TO]->(:HealthRecord)` - Connected health records

## Database Setup

### 1. Create Constraints and Indexes

```cypher
// Unique constraints
CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT health_record_id_unique IF NOT EXISTS FOR (hr:HealthRecord) REQUIRE hr.id IS UNIQUE;
CREATE CONSTRAINT file_id_unique IF NOT EXISTS FOR (f:File) REQUIRE f.id IS UNIQUE;

// Indexes for performance
CREATE INDEX user_email_index IF NOT EXISTS FOR (u:User) ON (u.email);
CREATE INDEX user_type_index IF NOT EXISTS FOR (u:User) ON (u.user_type);
CREATE INDEX health_record_status_index IF NOT EXISTS FOR (hr:HealthRecord) ON (hr.status);
CREATE INDEX file_type_index IF NOT EXISTS FOR (f:File) ON (f.file_type);
CREATE INDEX file_category_index IF NOT EXISTS FOR (f:File) ON (f.category);
CREATE INDEX appointment_date_index IF NOT EXISTS FOR (f:File) ON (f.appointment_date);
```

### 2. Sample Data Creation

```cypher
// Create sample patients
CREATE (p1:User {
  id: "patient_001",
  email: "john.doe@email.com",
  name: "John Doe",
  phone: "+1-555-0123",
  date_of_birth: date("1985-03-15"),
  gender: "Male",
  address: "123 Main St, City, State",
  user_type: "PATIENT",
  created_at: datetime(),
  updated_at: datetime()
});

CREATE (p2:User {
  id: "patient_002", 
  email: "jane.smith@email.com",
  name: "Jane Smith",
  phone: "+1-555-0124",
  date_of_birth: date("1990-07-22"),
  gender: "Female", 
  address: "456 Oak Ave, City, State",
  user_type: "PATIENT",
  created_at: datetime(),
  updated_at: datetime()
});

// Create sample doctors
CREATE (d1:User {
  id: "doctor_001",
  email: "dr.wilson@hospital.com",
  name: "Dr. Sarah Wilson",
  phone: "+1-555-0200",
  date_of_birth: date("1975-12-10"),
  gender: "Female",
  address: "789 Medical Center Dr, City, State", 
  user_type: "DOCTOR",
  specialization: "Internal Medicine",
  license_number: "MD12345",
  created_at: datetime(),
  updated_at: datetime()
});

CREATE (d2:User {
  id: "doctor_002",
  email: "dr.brown@clinic.com", 
  name: "Dr. Michael Brown",
  phone: "+1-555-0201",
  date_of_birth: date("1968-09-05"),
  gender: "Male",
  address: "321 Health Plaza, City, State",
  user_type: "DOCTOR", 
  specialization: "Orthopedics",
  license_number: "MD67890",
  created_at: datetime(),
  updated_at: datetime()
});
```

## Core CRUD Operations

### User Management

#### Create New User
```cypher
// Create patient
CREATE (u:User {
  id: $user_id,
  email: $email,
  name: $name,
  phone: $phone,
  date_of_birth: date($date_of_birth),
  gender: $gender,
  address: $address,
  user_type: "PATIENT",
  created_at: datetime(),
  updated_at: datetime()
})
RETURN u;

// Create doctor
CREATE (u:User {
  id: $user_id,
  email: $email, 
  name: $name,
  phone: $phone,
  date_of_birth: date($date_of_birth),
  gender: $gender,
  address: $address,
  user_type: "DOCTOR",
  specialization: $specialization,
  license_number: $license_number,
  created_at: datetime(),
  updated_at: datetime()
})
RETURN u;
```

#### Get User by ID
```cypher
MATCH (u:User {id: $user_id})
RETURN u;
```

#### Update User
```cypher
MATCH (u:User {id: $user_id})
SET u.name = $name,
    u.phone = $phone,
    u.address = $address,
    u.updated_at = datetime()
RETURN u;
```

#### Delete User
```cypher
MATCH (u:User {id: $user_id})
DETACH DELETE u;
```

### Health Record Management

#### Create Health Record
```cypher
// Create health record with patient and doctor relationships
MATCH (patient:User {id: $patient_id, user_type: "PATIENT"})
MATCH (doctor:User {id: $doctor_id, user_type: "DOCTOR"})
CREATE (hr:HealthRecord {
  id: $health_record_id,
  title: $title,
  ailment: $ailment,
  status: "ACTIVE",
  created_by: $created_by_user_id,
  layman_summary: $layman_summary,
  medical_summary: $medical_summary,
  overall_report: $overall_report,
  share_token: $share_token,
  share_type: $share_type,
  medications: [],
  created_at: datetime(),
  updated_at: datetime(),
  last_activity: datetime()
})
CREATE (patient)-[:OWNS]->(hr)
CREATE (doctor)-[:MANAGES]->(hr)
CREATE (doctor)-[:TREATS]->(patient)
RETURN hr, patient, doctor;
```

#### Get Health Records for Patient
```cypher
MATCH (patient:User {id: $patient_id})-[:OWNS]->(hr:HealthRecord)
OPTIONAL MATCH (doctor:User)-[:MANAGES]->(hr)
RETURN hr, doctor
ORDER BY hr.created_at DESC;
```

#### Get Health Records for Doctor
```cypher
MATCH (doctor:User {id: $doctor_id})-[:MANAGES]->(hr:HealthRecord)
OPTIONAL MATCH (patient:User)-[:OWNS]->(hr)
RETURN hr, patient
ORDER BY hr.last_activity DESC;
```

#### Update Health Record
```cypher
MATCH (hr:HealthRecord {id: $health_record_id})
SET hr.title = $title,
    hr.ailment = $ailment,
    hr.status = $status,
    hr.layman_summary = $layman_summary,
    hr.medical_summary = $medical_summary,
    hr.overall_report = $overall_report,
    hr.updated_at = datetime(),
    hr.last_activity = datetime()
RETURN hr;
```

#### Link Related Health Records
```cypher
MATCH (hr1:HealthRecord {id: $health_record_1_id})
MATCH (hr2:HealthRecord {id: $health_record_2_id})
CREATE (hr1)-[:RELATED_TO {
  relationship_type: $relationship_type,
  created_at: datetime(),
  notes: $notes
}]->(hr2)
RETURN hr1, hr2;
```

### File and Appointment Management

#### Add Document File
```cypher
MATCH (hr:HealthRecord {id: $health_record_id})
MATCH (uploader:User {id: $uploaded_by})
CREATE (f:File {
  id: $file_id,
  filename: $filename,
  file_type: $file_type,
  file_size: $file_size,
  storage_path: $storage_path,
  description: $description,
  category: $category,
  uploaded_by: $uploaded_by,
  file_status: $file_status #can be PROCESSING or PROCESSED
  layman_summary: $layman_summary,
  doctor_summary: $doctor_summary,
  created_at: datetime(),
  file_hash: $file_hash
})
CREATE (hr)-[:HAS_FILE]->(f)
CREATE (uploader)-[:UPLOADED]->(f)
SET hr.last_activity = datetime()
RETURN f;
```

#### Add Appointment Record
```cypher
MATCH (hr:HealthRecord {id: $health_record_id})
MATCH (doctor:User {id: $doctor_id, user_type: "DOCTOR"})
MATCH (patient:User)-[:OWNS]->(hr)
CREATE (apt:File {
  id: $appointment_id,
  filename: $appointment_title,
  file_type: "APPOINTMENT",
  category: "APPOINTMENT",
  description: $appointment_notes,
  layman_summary: $layman_summary,
  doctor_summary: $doctor_summary,
  appointment_date: datetime($appointment_date),
  duration_minutes: $duration_minutes,
  chief_complaint: $chief_complaint,
  diagnosis: $diagnosis,
  treatment_plan: $treatment_plan,
  next_appointment: datetime($next_appointment),
  uploaded_by: $doctor_id,
  created_at: datetime()
})
CREATE (hr)-[:HAS_FILE]->(apt)
CREATE (doctor)-[:UPLOADED]->(apt)
CREATE (doctor)-[:CONDUCTED]->(apt)
CREATE (patient)-[:ATTENDED]->(apt)
SET hr.last_activity = datetime()
RETURN apt;
```

#### Get All Files for Health Record
```cypher
MATCH (hr:HealthRecord {id: $health_record_id})-[:HAS_FILE]->(f:File)
OPTIONAL MATCH (uploader:User)-[:UPLOADED]->(f)
RETURN f, uploader.name as uploaded_by_name
ORDER BY f.created_at DESC;
```

#### Get Files with Patient-Friendly Summaries
```cypher
MATCH (hr:HealthRecord {id: $health_record_id})-[:HAS_FILE]->(f:File)
OPTIONAL MATCH (uploader:User)-[:UPLOADED]->(f)
RETURN f.id, f.filename, f.file_type, f.category, 
       f.layman_summary, f.created_at,
       uploader.name as uploaded_by_name
ORDER BY f.created_at DESC;
```

#### Get Files with Medical Summaries (for doctors)
```cypher
MATCH (hr:HealthRecord {id: $health_record_id})-[:HAS_FILE]->(f:File)
OPTIONAL MATCH (uploader:User)-[:UPLOADED]->(f)
RETURN f.id, f.filename, f.file_type, f.category,
       f.doctor_summary, f.layman_summary, f.created_at,
       uploader.name as uploaded_by_name
ORDER BY f.created_at DESC;
```

#### Get Appointments for Health Record
```cypher
MATCH (hr:HealthRecord {id: $health_record_id})-[:HAS_FILE]->(f:File {file_type: "APPOINTMENT"})
OPTIONAL MATCH (doctor:User)-[:CONDUCTED]->(f)
OPTIONAL MATCH (patient:User)-[:ATTENDED]->(f)
RETURN f, doctor.name as doctor_name, patient.name as patient_name
ORDER BY f.appointment_date DESC;
```

#### Update File Summaries
```cypher
MATCH (f:File {id: $file_id})
SET f.layman_summary = $layman_summary,
    f.doctor_summary = $doctor_summary
RETURN f;
```

#### Get File by Summary Type
```cypher
// Get patient-friendly view
MATCH (f:File {id: $file_id})
RETURN f.id, f.filename, f.file_type, f.category,
       f.layman_summary as summary, f.created_at;

// Get medical professional view  
MATCH (f:File {id: $file_id})
RETURN f.id, f.filename, f.file_type, f.category,
       f.doctor_summary as summary, f.layman_summary, f.created_at;
```

### Medication Management

#### Add Medication to Health Record
```cypher
MATCH (hr:HealthRecord {id: $health_record_id})
SET hr.medications = hr.medications + [{
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
  created_at: toString(datetime()),
  approved_at: null
}],
hr.updated_at = datetime(),
hr.last_activity = datetime()
RETURN hr;
```

#### Approve Medication
```cypher
MATCH (hr:HealthRecord {id: $health_record_id})
SET hr.medications = [med IN hr.medications | 
  CASE WHEN med.id = $medication_id 
  THEN apoc.map.setKey(apoc.map.setKey(med, 'status', 'APPROVED'), 'approved_by', $doctor_id)
  ELSE med END
],
hr.updated_at = datetime()
RETURN hr;
```

#### Get Active Medications
```cypher
MATCH (hr:HealthRecord {id: $health_record_id})
UNWIND hr.medications as med
WHERE med.status IN ['APPROVED', 'ACTIVE']
RETURN med;
```

## Advanced Queries

### Patient Health Timeline
```cypher
MATCH (patient:User {id: $patient_id})-[:OWNS]->(hr:HealthRecord)
OPTIONAL MATCH (hr)-[:HAS_FILE]->(f:File)
OPTIONAL MATCH (doctor:User)-[:MANAGES]->(hr)
WITH hr, doctor, 
     collect(CASE WHEN f.file_type = "APPOINTMENT" THEN f ELSE null END) as appointments,
     collect(CASE WHEN f.file_type <> "APPOINTMENT" THEN f ELSE null END) as files
RETURN hr.title, hr.ailment, hr.status, hr.created_at,
       doctor.name as doctor_name,
       [apt IN appointments WHERE apt IS NOT NULL | {
         date: apt.appointment_date,
         diagnosis: apt.diagnosis,
         treatment: apt.treatment_plan,
         layman_summary: apt.layman_summary
       }] as appointment_history,
       [file IN files WHERE file IS NOT NULL | {
         filename: file.filename,
         category: file.category,
         created: file.created_at,
         layman_summary: file.layman_summary
       }] as document_files,
       hr.medications
ORDER BY hr.created_at DESC;
```

### Doctor's Patient Dashboard
```cypher
MATCH (doctor:User {id: $doctor_id})-[:MANAGES]->(hr:HealthRecord)
MATCH (patient:User)-[:OWNS]->(hr)
OPTIONAL MATCH (hr)-[:HAS_FILE]->(recent_apt:File {file_type: "APPOINTMENT"})
WITH hr, patient, recent_apt
ORDER BY recent_apt.appointment_date DESC
WITH hr, patient, collect(recent_apt)[0] as last_appointment
RETURN patient.name, patient.email,
       hr.title, hr.ailment, hr.status,
       last_appointment.appointment_date as last_visit,
       last_appointment.diagnosis as last_diagnosis,
       last_appointment.doctor_summary as clinical_notes,
       size(hr.medications) as medication_count
ORDER BY last_appointment.appointment_date DESC;
```

### Search Health Records
```cypher
// Search by ailment or title
MATCH (hr:HealthRecord)
WHERE toLower(hr.title) CONTAINS toLower($search_term) 
   OR toLower(hr.ailment) CONTAINS toLower($search_term)
OPTIONAL MATCH (patient:User)-[:OWNS]->(hr)
OPTIONAL MATCH (doctor:User)-[:MANAGES]->(hr)
RETURN hr, patient.name as patient_name, doctor.name as doctor_name
LIMIT 20;
```

### Search Files by Summary Content
```cypher
// Search in layman summaries for patients
MATCH (hr:HealthRecord)-[:HAS_FILE]->(f:File)
WHERE toLower(f.layman_summary) CONTAINS toLower($search_term)
   OR toLower(f.filename) CONTAINS toLower($search_term)
OPTIONAL MATCH (patient:User)-[:OWNS]->(hr)
RETURN f.filename, f.category, f.layman_summary, f.created_at,
       hr.title as health_record, patient.name as patient_name
LIMIT 20;

// Search in doctor summaries for medical professionals
MATCH (hr:HealthRecord)-[:HAS_FILE]->(f:File)
WHERE toLower(f.doctor_summary) CONTAINS toLower($search_term)
   OR toLower(f.layman_summary) CONTAINS toLower($search_term)
   OR toLower(f.filename) CONTAINS toLower($search_term)
OPTIONAL MATCH (patient:User)-[:OWNS]->(hr)
RETURN f.filename, f.category, f.doctor_summary, f.layman_summary, f.created_at,
       hr.title as health_record, patient.name as patient_name
LIMIT 20;
```

### Get Shared Health Record
```cypher
MATCH (hr:HealthRecord {share_token: $share_token})
MATCH (patient:User)-[:OWNS]->(hr)
MATCH (doctor:User)-[:MANAGES]->(hr)
OPTIONAL MATCH (hr)-[:HAS_FILE]->(f:File)
RETURN 
  CASE hr.share_type
    WHEN "SHORT" THEN {
      title: hr.title,
      ailment: hr.ailment,
      patient_name: patient.name,
      doctor_name: doctor.name,
      summary: hr.layman_summary,
      files: collect({
        filename: f.filename,
        category: f.category,
        summary: f.layman_summary,
        created: f.created_at
      })
    }
    ELSE {
      title: hr.title,
      ailment: hr.ailment,
      patient_name: patient.name,
      doctor_name: doctor.name,
      summary: hr.layman_summary,
      medical_summary: hr.medical_summary,
      overall_report: hr.overall_report,
      medications: hr.medications,
      files: collect({
        filename: f.filename,
        category: f.category,
        layman_summary: f.layman_summary,
        doctor_summary: f.doctor_summary,
        created: f.created_at
      })
    }
  END as shared_data;
```

## Performance Optimization

### Recommended Indexes
```cypher
// Additional performance indexes
CREATE INDEX health_record_created_at IF NOT EXISTS FOR (hr:HealthRecord) ON (hr.created_at);
CREATE INDEX health_record_last_activity IF NOT EXISTS FOR (hr:HealthRecord) ON (hr.last_activity);
CREATE INDEX file_created_at IF NOT EXISTS FOR (f:File) ON (f.created_at);
CREATE INDEX health_record_share_token IF NOT EXISTS FOR (hr:HealthRecord) ON (hr.share_token);
```

### Pagination Pattern
```cypher
// Get paginated health records
MATCH (patient:User {id: $patient_id})-[:OWNS]->(hr:HealthRecord)
OPTIONAL MATCH (doctor:User)-[:MANAGES]->(hr)
RETURN hr, doctor
ORDER BY hr.created_at DESC
SKIP $skip
LIMIT $limit;
```

## Testing Queries

### Data Validation
```cypher
// Check data integrity
MATCH (hr:HealthRecord)
OPTIONAL MATCH (patient:User)-[:OWNS]->(hr)
OPTIONAL MATCH (doctor:User)-[:MANAGES]->(hr)
WHERE patient IS NULL OR doctor IS NULL
RETURN hr.id, patient, doctor;

// Find orphaned files
MATCH (f:File)
WHERE NOT EXISTS((:HealthRecord)-[:HAS_FILE]->(f))
RETURN f;
```

### Sample Data Cleanup
```cypher
// Remove all sample data
MATCH (n) WHERE n.id STARTS WITH "patient_" OR n.id STARTS WITH "doctor_" OR n.id STARTS WITH "hr_"
DETACH DELETE n;
```

## Environment Variables for Application

```bash
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Application Settings
HEALTH_RECORDS_DB_NAME=neo4j
DEFAULT_PAGE_SIZE=20
MAX_FILE_SIZE_MB=50
ALLOWED_FILE_TYPES=TXT,PDF,JPG,JPEG
```

This comprehensive guide provides all the Cypher queries and patterns needed to implement the health records knowledge graph system.