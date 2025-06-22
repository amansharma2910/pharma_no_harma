# Agentic Architecture Implementation

## Overview

This document describes the implementation of an agentic architecture for the Health Records Management System, converting it from a traditional LLM-driven application to a multi-agent framework using **LangGraph**.

## Architecture Components

### 1. Orchestrator Agent (`app/services/orchestrator_agent.py`)

The orchestrator agent is the central coordinator that:
- Analyzes user intent from natural language queries
- Selects appropriate tools/agents based on intent
- Executes workflows using LangGraph
- Generates comprehensive responses

#### Key Features:
- **State Management**: Uses `AgentState` to maintain context throughout the workflow
- **Intent Analysis**: Classifies user queries into specific intents
- **Tool Selection**: Maps intents to appropriate tools
- **Response Generation**: Creates comprehensive responses from tool results

### 2. Tool Definitions

The system includes several specialized tools that can be called by the orchestrator:

#### `get_medical_history_report`
- **Purpose**: Generate complete medical history reports
- **Parameters**: `user_id`, `date_from`, `date_to`
- **Functionality**: 
  - Retrieves all health records for a patient
  - Gathers all associated files
  - Generates comprehensive summaries
  - Returns structured data with counts and summaries

#### `query_medical_record`
- **Purpose**: Query specific medical records for detailed information
- **Parameters**: `health_record_id`, `user_id`, `query`
- **Functionality**:
  - Retrieves specific health record and associated files
  - Uses existing agent service for query processing
  - Returns detailed context and responses

#### `get_latest_prescription`
- **Purpose**: Retrieve the most recent prescription for a patient
- **Parameters**: `user_id`
- **Functionality**:
  - Searches all health records for medications
  - Identifies the latest prescription by date
  - Includes medicine information from external sources
  - Returns prescription details and medicine info

#### `search_health_records`
- **Purpose**: Search across all health records and files
- **Parameters**: `query`, `user_id`, `user_type`
- **Functionality**:
  - Performs semantic search in health records
  - Searches file contents
  - Returns ranked results with counts

#### `generate_health_summary`
- **Purpose**: Generate comprehensive health summaries
- **Parameters**: `health_record_id`, `summary_type`
- **Functionality**:
  - Creates summaries for specific health records
  - Supports both layman and medical summaries
  - Includes file count and record information

### 3. LangGraph Workflow

The workflow follows this pattern:

```
User Query → Intent Analysis → Tool Selection → Tool Execution → Response Generation
```

#### Workflow Nodes:

1. **`analyze_intent`**: Classifies user intent using keyword matching
2. **`select_tools`**: Maps intents to appropriate tools
3. **`execute_tools`**: Runs the selected tools using LangGraph's ToolNode
4. **`generate_response`**: Creates final response from tool results

#### State Management:
- Uses `MemorySaver` for conversation memory
- Maintains context across multiple interactions
- Tracks tool results and confidence scores

## API Endpoints

### Orchestrator Endpoints (`/api/v1/orchestrator/`)

#### `POST /orchestrator/query`
Process natural language queries through the orchestrator agent.

**Request Body:**
```json
{
  "query": "Give me my complete medical history report",
  "user_id": "user123",
  "user_type": "PATIENT",
  "health_record_id": "optional_record_id"
}
```

**Response:**
```json
{
  "response": "📋 **Medical History Report Generated**\n\nFound 5 health records with 23 files.\n\n**Summary:** [Generated summary]",
  "confidence": 0.8,
  "sources": ["health_records", "medical_database"],
  "suggested_actions": ["view_health_record", "schedule_appointment"],
  "cypher_queries_executed": []
}
```

#### `GET /orchestrator/tools`
Get list of available tools and their descriptions.

#### `GET /orchestrator/status`
Get orchestrator agent status and health information.

#### `POST /orchestrator/examples`
Get example queries that users can ask.

## Example Use Cases

### 1. Complete Medical History Report
**User Query**: "Give me my complete medical history report"

**Workflow**:
1. Intent Analysis: `get_medical_history`
2. Tool Selection: `get_medical_history_report`
3. Tool Execution: Retrieves all records and files, generates summary
4. Response: Comprehensive report with counts and summaries

### 2. Latest Prescription
**User Query**: "What's my latest prescription?"

**Workflow**:
1. Intent Analysis: `get_latest_prescription`
2. Tool Selection: `get_latest_prescription`
3. Tool Execution: Finds latest medication, gets medicine info
4. Response: Prescription details with medicine information

### 3. Search Records
**User Query**: "Search for diabetes-related records"

**Workflow**:
1. Intent Analysis: `search_records`
2. Tool Selection: `search_health_records`
3. Tool Execution: Performs semantic search
4. Response: Search results with counts and relevance

### 4. Health Summary
**User Query**: "Generate a summary of my health record"

**Workflow**:
1. Intent Analysis: `generate_summary`
2. Tool Selection: `generate_health_summary`
3. Tool Execution: Creates comprehensive summary
4. Response: Layman and medical summaries

## Integration with Existing Services

The orchestrator agent integrates seamlessly with existing services:

### Neo4j Service
- Uses existing database operations
- Leverages existing search functionality
- Maintains data consistency

### Agent Service
- Utilizes existing AI processing capabilities
- Maintains fallback mechanisms
- Preserves existing error handling

### File Service
- Integrates with file processing pipeline
- Uses existing file operations
- Maintains file status tracking

### Audit Service
- Logs all orchestrator interactions
- Tracks tool usage and performance
- Maintains compliance requirements

## Benefits of Agentic Architecture

### 1. **Intelligent Routing**
- Automatically selects appropriate tools based on user intent
- Reduces manual intervention in query processing
- Improves response accuracy

### 2. **Scalability**
- Easy to add new tools and capabilities
- Modular architecture supports independent development
- Horizontal scaling of individual components

### 3. **User Experience**
- Natural language interface
- Context-aware responses
- Comprehensive information gathering

### 4. **Maintainability**
- Clear separation of concerns
- Modular tool definitions
- Easy testing and debugging

### 5. **Extensibility**
- Simple to add new tools
- Easy to modify workflows
- Support for complex multi-step processes

## Future Enhancements

### 1. **Advanced Intent Recognition**
- Implement ML-based intent classification
- Support for complex multi-intent queries
- Context-aware intent analysis

### 2. **Dynamic Tool Selection**
- AI-powered tool selection
- Tool performance optimization
- Adaptive workflow generation

### 3. **Conversation Memory**
- Long-term conversation context
- User preference learning
- Personalized responses

### 4. **Multi-Agent Collaboration**
- Specialized agents for different domains
- Agent-to-agent communication
- Distributed processing

### 5. **Advanced Workflows**
- Conditional workflows
- Parallel tool execution
- Error recovery mechanisms

## Deployment Considerations

### 1. **Performance**
- Monitor tool execution times
- Implement caching for frequent queries
- Optimize database queries

### 2. **Reliability**
- Implement retry mechanisms
- Add circuit breakers for external services
- Monitor and alert on failures

### 3. **Security**
- Validate all user inputs
- Implement rate limiting
- Audit all agent interactions

### 4. **Monitoring**
- Track tool usage patterns
- Monitor response quality
- Alert on performance degradation

## Conclusion

The agentic architecture provides a robust foundation for intelligent health records management. By leveraging LangGraph and existing services, the system can now handle complex natural language queries while maintaining the reliability and security required for healthcare applications.

The modular design ensures easy maintenance and extension, while the intelligent routing improves user experience and system efficiency. 