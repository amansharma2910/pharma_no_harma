# Health Records API

A comprehensive FastAPI-based health records management system with AI-powered features for elderly care.

## Features

- **User Management**: Patient and doctor accounts with role-based access
- **Health Records**: Complete medical record management with relationships
- **File Management**: Document upload, processing, and AI-powered summarization
- **Medication Tracking**: Prescription management with approval workflows
- **AI Agent**: Natural language queries and intelligent responses
- **Search**: Full-text search across all medical data
- **Audit Logging**: Complete activity tracking for compliance
- **Export**: PDF generation for medical records
- **Neo4j Integration**: Graph database for complex medical relationships

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: Neo4j (Graph Database)
- **AI/ML**: OpenAI GPT-3.5 for summarization and queries
- **File Storage**: Local filesystem (configurable)
- **Background Tasks**: Async processing for file analysis
- **Documentation**: Auto-generated OpenAPI/Swagger

## Project Structure

```
health_records_api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints/          # API route handlers
│   │       └── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Application configuration
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic models and schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── agent_service.py    # AI agent functionality
│   │   ├── audit_service.py    # Audit logging service
│   │   ├── file_service.py     # File management service
│   │   └── neo4j_service.py    # Neo4j database operations
│   └── utils/
│       ├── __init__.py
│       └── helpers.py          # Utility functions
├── uploads/                    # File upload directory
├── exports/                    # PDF export directory
├── requirements.txt            # Python dependencies
├── run.py                      # Application startup script
├── init_db.py                  # Database initialization
├── env.example                 # Environment variables template
├── .gitignore
└── README.md
```

## Prerequisites

- Python 3.8+
- Neo4j Database (4.4+)
- Redis (for background tasks)
- OpenAI API key (for AI features)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd health_records_api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Start Neo4j Database**
   ```bash
   # Using Docker
   docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
   
   # Or install Neo4j Desktop/Server locally
   ```

6. **Start Redis (for background tasks)**
   ```bash
   # Using Docker
   docker run -p 6379:6379 redis:latest
   
   # Or install Redis locally
   ```

7. **Initialize the database**
   ```bash
   python init_db.py
   ```

8. **Run the application**
   ```bash
   python run.py
   ```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

## Configuration

### Environment Variables

Copy `env.example` to `.env` and configure the following variables:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=Health Records API
DEBUG=true

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=52428800
ALLOWED_FILE_TYPES=["TXT", "PDF", "JPG", "JPEG"]

# AI Service Configuration
OPENAI_API_KEY=your_openai_api_key_here
LLAMA_CLOUD_API_KEY=your_llama_cloud_api_key_here

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Background Tasks
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379

# Export Configuration
PDF_EXPORT_DIR=./exports
EXPORT_URL_PREFIX=http://localhost:8000/exports

# Logging
LOG_LEVEL=INFO
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Refresh access token

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update user profile
- `GET /api/v1/users/{user_id}` - Get user by ID

### Health Records
- `GET /api/v1/records` - List health records
- `POST /api/v1/records` - Create new health record
- `GET /api/v1/records/{record_id}` - Get specific record
- `PUT /api/v1/records/{record_id}` - Update record
- `DELETE /api/v1/records/{record_id}` - Delete record

### File Management
- `POST /api/v1/files/upload` - Upload medical documents
- `GET /api/v1/files/{file_id}` - Get file information
- `DELETE /api/v1/files/{file_id}` - Delete file
- `GET /api/v1/files/{file_id}/summary` - Get AI-generated summary

### Medications
- `GET /api/v1/medications` - List medications
- `POST /api/v1/medications` - Create medication record
- `PUT /api/v1/medications/{med_id}/approve` - Approve medication
- `GET /api/v1/medications/pending` - Get pending approvals

### AI Agent
- `POST /api/v1/agent/query` - Natural language queries
- `GET /api/v1/agent/chat` - Chat with AI agent

### Search
- `GET /api/v1/search` - Full-text search across records
- `GET /api/v1/search/advanced` - Advanced search with filters

### Export
- `GET /api/v1/export/record/{record_id}` - Export record as PDF
- `GET /api/v1/export/patient/{patient_id}` - Export patient summary

### Audit
- `GET /api/v1/audit/logs` - View audit logs
- `GET /api/v1/audit/activity/{user_id}` - User activity history

## Usage Examples

### Creating a Health Record

```python
import requests

# Login
response = requests.post("http://localhost:8000/api/v1/auth/login", json={
    "username": "doctor@example.com",
    "password": "password123"
})
token = response.json()["access_token"]

# Create health record
headers = {"Authorization": f"Bearer {token}"}
record_data = {
    "patient_id": "patient123",
    "record_type": "consultation",
    "title": "Annual Checkup",
    "content": "Patient shows good health indicators...",
    "date": "2024-01-15"
}

response = requests.post(
    "http://localhost:8000/api/v1/records",
    json=record_data,
    headers=headers
)
```

### Uploading and Processing Documents

```python
# Upload medical document
with open("medical_report.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(
        "http://localhost:8000/api/v1/files/upload",
        files=files,
        headers=headers
    )

file_id = response.json()["file_id"]

# Get AI summary
summary_response = requests.get(
    f"http://localhost:8000/api/v1/files/{file_id}/summary",
    headers=headers
)
summary = summary_response.json()["summary"]
```

### AI Agent Query

```python
# Ask natural language question
query_data = {
    "question": "What medications is patient John Smith currently taking?",
    "context": "patient_id: john_smith_123"
}

response = requests.post(
    "http://localhost:8000/api/v1/agent/query",
    json=query_data,
    headers=headers
)

answer = response.json()["answer"]
```

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Formatting
```bash
# Install formatting tools
pip install black isort

# Format code
black app/
isort app/
```

### Database Schema

The application uses Neo4j graph database with the following main node types:
- **User**: Patients, doctors, and administrators
- **HealthRecord**: Medical records and consultations
- **Medication**: Prescriptions and drug information
- **File**: Uploaded documents and reports
- **AuditLog**: Activity tracking and compliance

See `neo4j_kg_schema.md` for detailed schema documentation.

## Deployment

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t health-records-api .
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

### Production Considerations

- Set `DEBUG=false` in production
- Use strong `SECRET_KEY`
- Configure proper Neo4j authentication
- Set up SSL/TLS certificates
- Configure proper logging
- Set up monitoring and health checks
- Use production-grade Redis instance
- Configure backup strategies for Neo4j

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the backend structure documentation in `backend_structure.md` 