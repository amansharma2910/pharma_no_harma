# AWS Bedrock Integration Guide

This guide explains how to integrate AWS Bedrock with your Health Records API using Neo4j as the knowledge graph.

## Overview

The integration uses AWS Bedrock models (Claude, Titan, Llama) combined with your existing Neo4j knowledge graph to provide intelligent, context-aware responses for health records queries.

## Architecture

```
User Query → Bedrock Model → Cypher Generation → Neo4j Query → Context Gathering → Bedrock Response
```

### Key Components

1. **AWS Bedrock Models**: Anthropic Claude, Amazon Titan, Meta Llama
2. **Neo4j Knowledge Graph**: Your existing health records data
3. **BedrockNeo4jService**: Orchestrates the integration
4. **API Endpoints**: RESTful endpoints for queries and operations

## Benefits of Neo4j + Bedrock Integration

- **Leverages Existing Data**: Uses your current Neo4j knowledge graph
- **Complex Relationships**: Exploits graph relationships for better context
- **Real-time Access**: Always up-to-date with latest data
- **Structured Queries**: Generates precise Cypher queries
- **No Data Duplication**: No need for separate knowledge base

## Setup Instructions

### 1. Prerequisites

- AWS Account with Bedrock access
- Neo4j database with health records data
- Python 3.8+ with required dependencies

### 2. AWS Configuration

#### 2.1 AWS Credentials

Configure your AWS credentials using one of these methods:

**Option A: AWS CLI (Recommended)**
```bash
aws configure
```

**Option B: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

#### 2.2 IAM Permissions

Ensure your AWS user/role has these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:ListFoundationModels"
            ],
            "Resource": "*"
        }
    ]
}
```

#### 2.3 Enable Bedrock Models

In AWS Console:
1. Go to Amazon Bedrock
2. Navigate to "Model access"
3. Request access to desired models:
   - Anthropic Claude 3 Sonnet
   - Amazon Titan Text
   - Meta Llama 2

### 3. Application Configuration

#### 3.1 Environment Variables

Update your `.env` file:

```env
# AWS Bedrock Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1
AWS_SESSION_TOKEN=your_aws_session_token  # Optional
AWS_ACCOUNT_ID=your_aws_account_id  # Optional

# AWS Bedrock Models
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

#### 3.2 Available Models

| Model ID | Description | Use Case |
|----------|-------------|----------|
| `anthropic.claude-3-sonnet-20240229-v1:0` | Claude 3 Sonnet | General queries, balanced performance |
| `anthropic.claude-3-haiku-20240307-v1:0` | Claude 3 Haiku | Fast responses, simple queries |
| `anthropic.claude-3-opus-20240229-v1:0` | Claude 3 Opus | Complex reasoning, detailed analysis |
| `amazon.titan-text-express-v1` | Amazon Titan | Cost-effective, good performance |
| `meta.llama2-13b-chat-v1` | Llama 2 13B | Open source alternative |

### 4. Automated Setup

Run the setup script for guided configuration:

```bash
python setup_bedrock.py
```

This script will:
- Check dependencies
- Configure AWS credentials
- Select Bedrock models
- Test connections
- Update configuration files

## API Endpoints

### Core Bedrock Endpoints

#### 1. Basic Query
```http
POST /api/v1/bedrock/query
Content-Type: application/json

{
    "query": "What are my recent blood pressure readings?",
    "user_type": "PATIENT"
}
```

#### 2. Neo4j-Enhanced Query
```http
POST /api/v1/bedrock/query-with-neo4j
Content-Type: application/json

{
    "query": "Show me patients with diabetes and their medications",
    "user_type": "DOCTOR"
}
```

#### 3. Direct Model Invocation
```http
POST /api/v1/bedrock/invoke-model
Content-Type: application/json

{
    "prompt": "Summarize this medical report",
    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
    "max_tokens": 1500,
    "temperature": 0.3
}
```

### Neo4j Integration Endpoints

#### 4. Cypher Generation
```http
POST /api/v1/bedrock/generate-cypher
Content-Type: application/json

{
    "natural_language": "Find all patients with diabetes",
    "context": {"patient_type": "diabetic"}
}
```

#### 5. Patient Context
```http
GET /api/v1/bedrock/patient-context/{patient_id}
```

#### 6. Health Records Search
```http
GET /api/v1/bedrock/search-records?search_term=diabetes&patient_id=123
```

#### 7. Health Check
```http
GET /api/v1/bedrock/health
```

## Usage Examples

### Example 1: Patient Query
```bash
curl -X POST "http://localhost:8000/api/v1/bedrock/query-with-neo4j" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What medications am I currently taking?",
    "user_type": "PATIENT"
  }'
```

### Example 2: Doctor Query
```bash
curl -X POST "http://localhost:8000/api/v1/bedrock/query-with-neo4j" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all patients with hypertension and their treatment history",
    "user_type": "DOCTOR"
  }'
```

### Example 3: Cypher Generation
```bash
curl -X POST "http://localhost:8000/api/v1/bedrock/generate-cypher" \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "Find patients with diabetes who are taking metformin",
    "context": {"condition": "diabetes", "medication": "metformin"}
  }'
```

## How It Works

### 1. Query Processing Flow

1. **User Query**: Natural language query received
2. **Intent Analysis**: Bedrock analyzes query intent and user type
3. **Cypher Generation**: Bedrock generates appropriate Cypher query
4. **Neo4j Execution**: Query executed against Neo4j database
5. **Context Gathering**: Results processed and contextualized
6. **Response Generation**: Bedrock generates final response with context

### 2. Cypher Query Generation

The system uses prompts like:
```
Given this natural language query: "{query}"
Generate a Cypher query for Neo4j health records database.
Consider the user type: {user_type}
Focus on: {context}
```

### 3. Context Enhancement

Retrieved data is formatted and enhanced:
- Patient demographics
- Medical history
- Current medications
- Lab results
- Treatment plans
- Related conditions

## Error Handling

### Common Issues

1. **AWS Credentials**
   ```
   Error: AWS credentials not found
   Solution: Configure AWS credentials via CLI or environment variables
   ```

2. **Model Access**
   ```
   Error: AccessDeniedException
   Solution: Request model access in AWS Bedrock console
   ```

3. **Neo4j Connection**
   ```
   Error: Neo4j connection failed
   Solution: Check Neo4j URI, credentials, and network connectivity
   ```

### Fallback Strategy

The system implements graceful fallbacks:
1. **Primary**: Bedrock + Neo4j integration
2. **Secondary**: Bedrock only (without Neo4j context)
3. **Tertiary**: OpenAI (if configured)
4. **Final**: Simple response with error message

## Monitoring and Logging

### Health Checks
```bash
curl http://localhost:8000/api/v1/bedrock/health
```

Response:
```json
{
    "bedrock_configured": true,
    "bedrock_model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
    "aws_region": "us-east-1",
    "neo4j_integration": true
}
```

### Logging
Check application logs for:
- Bedrock API calls
- Cypher query generation
- Neo4j query execution
- Response processing
- Error handling

## Performance Optimization

### 1. Model Selection
- **Claude 3 Haiku**: Fastest, good for simple queries
- **Claude 3 Sonnet**: Balanced, recommended for most use cases
- **Claude 3 Opus**: Most capable, for complex reasoning

### 2. Query Optimization
- Use specific Cypher queries
- Limit result sets
- Implement pagination
- Cache frequent queries

### 3. Cost Management
- Monitor API usage
- Use appropriate model sizes
- Implement rate limiting
- Cache responses when possible

## Security Considerations

### 1. Data Privacy
- All health data remains in your Neo4j database
- No data sent to AWS beyond query context
- HIPAA compliance maintained

### 2. Access Control
- Implement proper authentication
- Use role-based access control
- Audit all queries and responses

### 3. AWS Security
- Use IAM roles with minimal permissions
- Enable CloudTrail for audit logging
- Use VPC endpoints if needed

## Troubleshooting

### Setup Issues

1. **Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **AWS Configuration**
   ```bash
   aws configure list
   aws sts get-caller-identity
   ```

3. **Neo4j Connection**
   ```bash
   cypher-shell -u neo4j -p password
   ```

### Runtime Issues

1. **Check Logs**
   ```bash
   tail -f logs/app.log
   ```

2. **Test Connections**
   ```bash
   curl http://localhost:8000/api/v1/bedrock/health
   ```

3. **Verify Permissions**
   ```bash
   aws bedrock list-foundation-models
   ```

## Support

For issues and questions:
1. Check this documentation
2. Review application logs
3. Test with health check endpoint
4. Verify AWS and Neo4j configurations

## Next Steps

1. **Start the application**: `python run.py`
2. **Test basic queries**: Use the example endpoints
3. **Monitor performance**: Check logs and health endpoints
4. **Optimize queries**: Refine Cypher generation prompts
5. **Scale as needed**: Add caching, load balancing, etc. 