from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, Optional, List
from app.services.bedrock_service import bedrock_service
from app.services.bedrock_neo4j_service import bedrock_neo4j_service
from app.models.schemas import AgentQuery, AgentResponse, SummaryRequest, SummaryResponse
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/bedrock/query", response_model=AgentResponse)
async def bedrock_query(query: AgentQuery):
    """Process query using AWS Bedrock"""
    try:
        if not settings.AWS_ACCESS_KEY_ID:
            raise HTTPException(status_code=400, detail="AWS Bedrock not configured")
        
        response = await bedrock_service.process_query_with_bedrock(query)
        return response
    except Exception as e:
        logger.error(f"Bedrock query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@router.post("/bedrock/query-with-neo4j", response_model=AgentResponse)
async def bedrock_query_with_neo4j(query: AgentQuery):
    """Process query using AWS Bedrock with Neo4j knowledge graph context"""
    try:
        if not settings.AWS_ACCESS_KEY_ID:
            raise HTTPException(status_code=400, detail="AWS Bedrock not configured")
        response = await bedrock_neo4j_service.process_query_with_neo4j_context(query)
        return response
    except Exception as e:
        logger.error(f"Bedrock + Neo4j query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@router.get("/bedrock/patient-context/{patient_id}")
async def get_patient_context(patient_id: str):
    """Get comprehensive patient context from Neo4j"""
    try:
        if not settings.AWS_ACCESS_KEY_ID:
            raise HTTPException(status_code=400, detail="AWS Bedrock not configured")
        
        context = await bedrock_neo4j_service.get_patient_context(patient_id)
        return {
            "patient_id": patient_id,
            "context": context
        }
    except Exception as e:
        logger.error(f"Patient context error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get patient context: {str(e)}")

@router.get("/bedrock/search-records")
async def search_health_records(
    search_term: str,
    patient_id: Optional[str] = None
):
    """Search health records using Neo4j and enhance with Bedrock"""
    try:
        if not settings.AWS_ACCESS_KEY_ID:
            raise HTTPException(status_code=400, detail="AWS Bedrock not configured")
        
        results = await bedrock_neo4j_service.search_health_records(search_term, patient_id)
        return {
            "search_term": search_term,
            "patient_id": patient_id,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Health records search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/bedrock/health")
async def bedrock_health_check():
    """Health check for AWS Bedrock services"""
    try:
        health_status = {
            "bedrock_configured": settings.AWS_ACCESS_KEY_ID is not None,
            "bedrock_model_id": "amazon.nova-pro-v1:0",
            "supported_model": "amazon.nova-pro-v1:0",
            "aws_region": settings.AWS_REGION,
            "neo4j_integration": True
        }
        
        return health_status
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}") 