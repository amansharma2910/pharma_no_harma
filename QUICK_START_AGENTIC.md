# Quick Start Guide: Agentic Architecture

## 🚀 Getting Started

This guide will help you quickly understand and use the new agentic architecture for the Health Records Management System.

## 📋 Prerequisites

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Setup**
   ```bash
   cp env.example .env
   # Configure your .env file with necessary API keys and database settings
   ```

3. **Database Setup**
   - Ensure Neo4j is running
   - Run database initialization: `python init_db.py`

## 🏗️ Architecture Overview

```
User Query → Orchestrator Agent → Tool Selection → Tool Execution → Response
```

### Key Components:
- **Orchestrator Agent**: Central coordinator using LangGraph
- **Tools**: Specialized functions for different tasks
- **Workflow**: Stateful processing with memory

## 🔧 Available Tools

The system includes these tools that can be called automatically:

1. **`get_medical_history_report`** - Complete medical history
2. **`get_latest_prescription`** - Latest medication prescription
3. **`search_health_records`** - Search across records and files
4. **`query_medical_record`** - Query specific records
5. **`generate_health_summary`** - Generate health summaries

## 🧪 Testing the System

### 1. Run the Test Script
```bash
python test_orchestrator.py
```

### 2. Test via API
Start the server:
```bash
python run.py
```

Then test with curl:
```bash
# Test orchestrator query
curl -X POST "http://localhost:8000/api/v1/orchestrator/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Give me my complete medical history report",
    "user_id": "test_user_123",
    "user_type": "PATIENT"
  }'

# Get available tools
curl "http://localhost:8000/api/v1/orchestrator/tools"

# Get example queries
curl "http://localhost:8000/api/v1/orchestrator/examples"
```

## 📝 Example Queries

### Medical History
```json
{
  "query": "Give me my complete medical history report",
  "user_id": "user123",
  "user_type": "PATIENT"
}
```

### Latest Prescription
```json
{
  "query": "What's my latest prescription?",
  "user_id": "user123",
  "user_type": "PATIENT"
}
```

### Search Records
```json
{
  "query": "Search for diabetes-related records",
  "user_id": "user123",
  "user_type": "PATIENT"
}
```

### Health Summary
```json
{
  "query": "Generate a summary of my health record",
  "user_id": "user123",
  "user_type": "PATIENT"
}
```

## 🔍 Understanding the Workflow

### 1. Intent Analysis
The system analyzes your query to understand what you want:
- "history", "report" → `get_medical_history`
- "prescription", "medication" → `get_latest_prescription`
- "search", "find" → `search_records`
- "summary" → `generate_summary`

### 2. Tool Selection
Based on intent, appropriate tools are selected:
```python
tool_mapping = {
    "get_medical_history": ["get_medical_history_report"],
    "get_latest_prescription": ["get_latest_prescription"],
    "search_records": ["search_health_records"],
    "generate_summary": ["generate_health_summary"]
}
```

### 3. Tool Execution
Selected tools are executed with proper parameters and context.

### 4. Response Generation
Results are compiled into a comprehensive, user-friendly response.

## 🛠️ Adding New Tools

To add a new tool:

1. **Define the Tool**
   ```python
   @tool
   async def your_new_tool(param1: str, param2: int) -> Dict[str, Any]:
       """Description of what this tool does"""
       try:
           # Your tool logic here
           return {"success": True, "data": result}
       except Exception as e:
           return {"success": False, "error": str(e)}
   ```

2. **Add to Orchestrator**
   ```python
   class OrchestratorAgent:
       def __init__(self):
           self.tools = [
               # ... existing tools
               your_new_tool
           ]
   ```

3. **Update Intent Mapping**
   ```python
   tool_mapping = {
       # ... existing mappings
       "your_intent": ["your_new_tool"]
   }
   ```

## 🔧 Configuration

### Environment Variables
```bash
# AI Services
OPENAI_API_KEY=your_openai_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret

# Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Other Services
PERPLEXITY_API_KEY=your_perplexity_key
```

### LangGraph Configuration
The system uses LangGraph with:
- **Memory**: Conversation memory for context
- **State Management**: Tracks workflow state
- **Tool Integration**: Seamless tool calling

## 📊 Monitoring

### Health Check
```bash
curl "http://localhost:8000/api/v1/orchestrator/status"
```

### Audit Logs
All interactions are logged for:
- Compliance
- Debugging
- Performance monitoring

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install langgraph==0.2.28
   ```

2. **Database Connection**
   - Check Neo4j is running
   - Verify connection settings in `.env`

3. **Tool Execution Errors**
   - Check tool parameters
   - Verify user permissions
   - Review audit logs

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance Tips

1. **Caching**: Implement caching for frequent queries
2. **Async Operations**: All tools are async for better performance
3. **Error Handling**: Robust error handling with fallbacks
4. **Monitoring**: Track tool execution times

## 🔮 Next Steps

1. **Explore the Code**: Review `app/services/orchestrator_agent.py`
2. **Test Different Queries**: Try various natural language inputs
3. **Add Custom Tools**: Extend functionality with new tools
4. **Monitor Performance**: Track response times and accuracy

## 📚 Additional Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Tools](https://python.langchain.com/docs/modules/tools/)
- [Agentic Architecture Guide](./AGENTIC_ARCHITECTURE.md)

---

**Happy Building! 🚀**

The agentic architecture provides a powerful foundation for intelligent health records management. Start with simple queries and gradually explore more complex workflows. 