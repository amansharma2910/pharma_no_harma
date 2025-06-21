# Health Records Management System

A comprehensive FastAPI-based health records management system with AI-powered features using AWS Bedrock and Neo4j graph database.

## Features

- **Health Records Management**: Complete CRUD operations for patient records
- **AI-Powered Queries**: Natural language processing with AWS Bedrock
- **Neo4j Integration**: Graph database for complex health data relationships
- **Document Processing**: AI-powered document parsing and summarization
- **Export Functionality**: PDF generation and data export
- **Background Tasks**: Asynchronous processing with Celery
- **RESTful API**: Comprehensive API with automatic documentation

## Tech Stack

- **Backend**: FastAPI, Python 3.8+
- **Database**: Neo4j (Graph Database)
- **AI Services**: AWS Bedrock (Claude, Titan, Llama)
- **Task Queue**: Celery with Redis
- **Document Processing**: LlamaParse
- **Export**: ReportLab for PDF generation

## Quick Start

### Prerequisites

- Python 3.8+
- Neo4j Database
- AWS Account with Bedrock access
- Redis (for background tasks)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd pharma_no_harma
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Configure Neo4j**:
   - Start Neo4j database
   - Update connection details in `.env`

5. **Configure AWS Bedrock**:
   ```bash
   python setup_bedrock.py
   ```

6. **Start the application**:
   ```bash
   python run.py
   ```

The API will be available at `http://localhost:8000`

## AWS Bedrock Integration

The system integrates AWS Bedrock with your existing Neo4j knowledge graph for intelligent, context-aware health record queries.

### Key Benefits

- **Leverages Existing Data**: Uses your current Neo4j knowledge graph
- **Complex Relationships**: Exploits graph relationships for better context
- **Real-time Access**: Always up-to-date with latest data
- **No Data Duplication**: No need for separate knowledge base

### Setup

1. **Configure AWS Credentials**:
   ```bash
   aws configure
   # Or set environment variables
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   export AWS_REGION=us-east-1
   ```

2. **Enable Bedrock Models**:
   - Go to AWS Bedrock Console
   - Request access to desired models (Claude, Titan, Llama)

3. **Run Setup Script**:
   ```bash
   python setup_bedrock.py
   ```

### Usage Examples

```bash
# Basic query with Bedrock
curl -X POST "http://localhost:8000/api/v1/bedrock/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are my recent blood pressure readings?", "user_type": "PATIENT"}'

# Neo4j-enhanced query
curl -X POST "http://localhost:8000/api/v1/bedrock/query-with-neo4j" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me patients with diabetes and their medications", "user_type": "DOCTOR"}'

# Health check
curl http://localhost:8000/api/v1/bedrock/health
```

For detailed Bedrock integration documentation, see [AWS_BEDROCK_INTEGRATION.md](AWS_BEDROCK_INTEGRATION.md).

## API Documentation

Once the application is running, you can access:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Core Endpoints

### Health Records
- `GET /api/v1/health-records` - List all health records
- `POST /api/v1/health-records` - Create new health record
- `GET /api/v1/health-records/{record_id}` - Get specific record
- `PUT /api/v1/health-records/{record_id}` - Update record
- `DELETE /api/v1/health-records/{record_id}` - Delete record

### AI Services
- `POST /api/v1/bedrock/query` - Process query with Bedrock
- `POST /api/v1/bedrock/query-with-neo4j` - Neo4j-enhanced query
- `POST /api/v1/bedrock/summary` - Generate AI summaries
- `POST /api/v1/bedrock/generate-cypher` - Generate Cypher queries

### Document Processing
- `POST /api/v1/documents/upload` - Upload and process documents
- `POST /api/v1/documents/summarize` - Generate document summaries
- `GET /api/v1/documents/{document_id}` - Get document details

### Export
- `POST /api/v1/export/pdf` - Generate PDF reports
- `GET /api/v1/export/health-records` - Export health records

## Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# AWS Bedrock Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# AI Services
OPENAI_API_KEY=your_openai_key  # Optional fallback
LLAMA_CLOUD_API_KEY=your_llama_key  # For document parsing

# Background Tasks
CELERY_BROKER_URL=redis://localhost:6379
```

### Available Bedrock Models

| Model ID | Description | Use Case | On-Demand Support |
|----------|-------------|----------|-------------------|
| `anthropic.claude-3-sonnet-20240229-v1:0` | Claude 3 Sonnet | General queries, balanced performance | ✅ Yes |
| `anthropic.claude-3-haiku-20240307-v1:0` | Claude 3 Haiku | Fast responses, simple queries | ✅ Yes |
| `anthropic.claude-3-opus-20240229-v1:0` | Claude 3 Opus | Complex reasoning, detailed analysis | ✅ Yes |
| `amazon.titan-text-express-v1` | Amazon Titan | Cost-effective, good performance | ✅ Yes |
| `meta.llama2-13b-chat-v1` | Llama 2 13B | Open source alternative | ✅ Yes |
| `amazon.nova-pro-v1:0` | Amazon Nova Pro | Advanced reasoning | ❌ Requires inference profile |

## Troubleshooting

### Bedrock Model Configuration Issues

If you encounter errors like:
```
ValidationException: Model amazon.nova-pro-v1:0 does not support on-demand throughput. 
Please use an inference profile for this model.
```

**Solution**: Use a model that supports on-demand usage or configure an inference profile.

**Quick Fix**:
```bash
# Run the model configuration fixer
python fix_bedrock_model.py

# Or manually update your .env file
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

**Why this happens**: Some Bedrock models (like Nova Pro) require inference profile configuration and cannot be used with on-demand throughput. This is common in development environments where inference profiles aren't set up.

**For Production**: If you need to use Nova Pro models, configure an inference profile in the AWS Bedrock console.

## Development

### Project Structure

```
pharma_no_harma/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── health_records.py
│   │   │   ├── bedrock.py
│   │   │   ├── documents.py
│   │   │   └── export.py
│   │   └── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   ├── schemas.py
│   │   └── database.py
│   ├── services/
│   │   ├── bedrock_service.py
│   │   ├── bedrock_neo4j_service.py
│   │   ├── document_service.py
│   │   └── export_service.py
│   └── utils/
├── tests/
├── requirements.txt
├── run.py
└── setup_bedrock.py
```

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=app
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## Deployment

### Docker

```bash
# Build image
docker build -t health-records-api .

# Run container
docker run -p 8000:8000 health-records-api
```

### Production Considerations

1. **Environment Variables**: Use proper secrets management
2. **Database**: Use production Neo4j instance
3. **Redis**: Use production Redis instance
4. **AWS**: Configure proper IAM roles and permissions
5. **Monitoring**: Set up logging and monitoring
6. **Security**: Enable HTTPS, authentication, rate limiting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
1. Check the documentation
2. Review the API docs at `/docs`
3. Check the logs for error details
4. Open an issue on GitHub

## Roadmap

- [ ] Real-time notifications
- [ ] Advanced analytics dashboard
- [ ] Multi-tenant support
- [ ] Mobile app integration
- [ ] Advanced AI features
- [ ] Performance optimizations 