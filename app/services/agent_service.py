import logging
from typing import Dict, Any, Optional
from app.models.schemas import AgentQuery, AgentResponse, SummaryRequest, SummaryResponse, SummaryType
from app.core.config import settings
from app.services.perplexity_service import perplexity_service
from openai import AsyncOpenAI
import json

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self):
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def process_query(self, query: AgentQuery) -> AgentResponse:
        """Process natural language query and return response"""
        try:
            # For now, return a simple response
            # In a real implementation, this would:
            # 1. Analyze the query intent
            # 2. Generate appropriate Cypher queries
            # 3. Execute queries against Neo4j
            # 4. Format response based on user type
            
            response_text = f"I understand you're asking about: {query.query}. "
            
            if query.user_type.value == "PATIENT":
                response_text += "Here's a patient-friendly explanation..."
            else:
                response_text += "Here's the medical information..."
            
            return AgentResponse(
                response=response_text,
                confidence=0.8,
                sources=["health_records", "medical_database"],
                suggested_actions=["view_health_record", "schedule_appointment"],
                cypher_queries_executed=["MATCH (hr:HealthRecord) WHERE..."])
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return AgentResponse(
                response="I'm sorry, I couldn't process your query at the moment.",
                confidence=0.0
            )
    
    async def generate_summary(self, request: SummaryRequest) -> SummaryResponse:
        """Generate AI-powered summaries"""
        try:
            if not self.openai_client:
                # Fallback to simple summarization
                return self._simple_summarize(request.content, request.summary_type)
            
            # Use OpenAI for advanced summarization
            return await self._openai_summarize(request)
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return self._simple_summarize(request.content, request.summary_type)
    
    async def _openai_summarize(self, request: SummaryRequest) -> SummaryResponse:
        """Generate summary using OpenAI with comprehensive error handling"""
        try:
            system_prompt = self._get_summary_prompt(request.summary_type, request.context)
            
            # Truncate content if it's too long for the model context
            max_content_length = 120000  # Conservative limit for GPT-4o (128k tokens)
            content = request.content
            if len(content) > max_content_length:
                logger.warning(f"Content too long ({len(content)} chars), truncating to {max_content_length} chars")
                content = content[:max_content_length] + "\n\n[Content truncated due to length]"
            
            # Try with GPT-4o first (better performance, larger context)
            try:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content}
                    ],
                    max_tokens=1000,  # Increased for better summaries
                    temperature=0.3
                )
                
                summary = response.choices[0].message.content
                
            except Exception as gpt4_error:
                logger.warning(f"GPT-4o failed, falling back to GPT-3.5-turbo: {gpt4_error}")
                
                # Fallback to GPT-3.5-turbo with further content truncation
                fallback_max_length = 8000  # Conservative limit for GPT-3.5-turbo
                if len(content) > fallback_max_length:
                    content = content[:fallback_max_length] + "\n\n[Content truncated for fallback model]"
                
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                
                summary = response.choices[0].message.content
            
            if request.summary_type.value == "BOTH":
                # Split the response into layman and doctor summaries
                parts = summary.split("---")
                layman_summary = parts[0].strip() if len(parts) > 0 else summary
                doctor_summary = parts[1].strip() if len(parts) > 1 else summary
                
                return SummaryResponse(
                    layman_summary=layman_summary,
                    doctor_summary=doctor_summary
                )
            elif request.summary_type.value == "LAYMAN":
                return SummaryResponse(layman_summary=summary)
            else:
                return SummaryResponse(doctor_summary=summary)
                
        except Exception as e:
            logger.error(f"OpenAI summarization failed: {e}")
            # Provide more specific error handling
            if "context_length_exceeded" in str(e):
                logger.error("Context length exceeded - document too large for AI processing")
                return SummaryResponse(
                    layman_summary="Document too large for AI processing. Please contact support for manual review.",
                    doctor_summary="Document exceeds AI processing limits. Manual review required."
                )
            elif "rate_limit" in str(e).lower():
                logger.error("OpenAI rate limit exceeded")
                return SummaryResponse(
                    layman_summary="AI service temporarily unavailable due to high demand. Please try again later.",
                    doctor_summary="Rate limit exceeded. Retry after cooling period."
                )
            elif "invalid_request" in str(e).lower():
                logger.error(f"Invalid request to OpenAI: {e}")
                return self._simple_summarize(request.content, request.summary_type)
            else:
                logger.error(f"Unexpected OpenAI error: {e}")
                return self._simple_summarize(request.content, request.summary_type)
    
    def _get_summary_prompt(self, summary_type: str, context: Optional[str] = None) -> str:
        """Get appropriate prompt for summary type"""
        base_prompt = "You are a medical AI assistant. Summarize the following content appropriately."
        
        if summary_type.value == "LAYMAN":
            prompt = f"{base_prompt} Provide a simple, easy-to-understand summary for patients. Avoid medical jargon and explain concepts in plain language."
        elif summary_type.value == "DOCTOR":
            prompt = f"{base_prompt} Provide a detailed medical summary for healthcare professionals. Include relevant medical terminology and clinical details."
        else:  # BOTH
            prompt = f"{base_prompt} Provide two summaries separated by '---': 1) A simple patient-friendly summary, 2) A detailed medical summary for professionals."
        
        if context:
            prompt += f"\n\nContext: {context}"
        
        return prompt
    
    def _simple_summarize(self, content: str, summary_type: str) -> SummaryResponse:
        """Simple fallback summarization with better handling of large documents"""
        try:
            # Truncate content if it's extremely long
            max_content_length = 50000  # Reasonable limit for simple processing
            if len(content) > max_content_length:
                content = content[:max_content_length] + "\n\n[Content truncated]"
            
            # Basic summarization logic - take first, middle, and last portions
            words = content.split()
            total_words = len(words)
            
            if total_words <= 100:
                # Short content - use as is
                simple_summary = content
            else:
                # Long content - take samples from beginning, middle, and end
                sample_size = min(50, total_words // 6)  # Take ~1/6 from each section
                
                beginning = " ".join(words[:sample_size])
                middle_start = total_words // 3
                middle = " ".join(words[middle_start:middle_start + sample_size])
                end_start = max(total_words - sample_size, middle_start + sample_size)
                end = " ".join(words[end_start:])
                
                simple_summary = f"{beginning}... [middle content] ... {end}"
            
            # Limit final summary length
            if len(simple_summary) > 2000:
                simple_summary = simple_summary[:2000] + "... [summary truncated]"
            
            if summary_type.value == "BOTH":
                return SummaryResponse(
                    layman_summary=f"Document Summary: {simple_summary}",
                    doctor_summary=f"Medical Document Summary: {simple_summary}"
                )
            elif summary_type.value == "LAYMAN":
                return SummaryResponse(layman_summary=f"Document Summary: {simple_summary}")
            else:
                return SummaryResponse(doctor_summary=f"Medical Document Summary: {simple_summary}")
                
        except Exception as e:
            logger.error(f"Error in simple summarization: {e}")
            # Ultimate fallback
            fallback_msg = "Unable to generate summary. Document processing failed."
            if summary_type.value == "BOTH":
                return SummaryResponse(
                    layman_summary=fallback_msg,
                    doctor_summary=fallback_msg
                )
            elif summary_type.value == "LAYMAN":
                return SummaryResponse(layman_summary=fallback_msg)
            else:
                return SummaryResponse(doctor_summary=fallback_msg)
    
    async def generate_cypher_query(self, natural_language: str, context: Dict[str, Any] = None) -> str:
        """Generate Cypher query from natural language"""
        try:
            # This would use AI to convert natural language to Cypher
            # For now, return a simple template
            return f"MATCH (n) WHERE n.title CONTAINS '{natural_language}' RETURN n LIMIT 10"
        except Exception as e:
            logger.error(f"Error generating Cypher query: {e}")
            return "MATCH (n) RETURN n LIMIT 5"
    
    async def interpret_health_record(self, health_record_data: Dict[str, Any], user_type: str) -> AgentResponse:
        """Provide AI interpretation of health record"""
        try:
            interpretation = f"Based on the health record '{health_record_data.get('title', 'Unknown')}', "
            
            if user_type == "PATIENT":
                interpretation += "here's what this means for you in simple terms..."
            else:
                interpretation += "here's the clinical interpretation and recommendations..."
            
            return AgentResponse(
                response=interpretation,
                confidence=0.9,
                suggested_actions=["schedule_follow_up", "review_medications"],
                sources=["health_record_analysis"]
            )
        except Exception as e:
            logger.error(f"Error interpreting health record: {e}")
            return AgentResponse(
                response="Unable to provide interpretation at this time.",
                confidence=0.0
            )
        
    async def generate_medicine_summary_via_perplexity(self, medicine_name: str) -> str:
        """Generate summary of a medicine using Perplexity"""
        try:
            # Use Perplexity API to generate summary
            response = await perplexity_service.generate_summary(medicine_name)
            return response
        except Exception as e:
            logger.error(f"Error generating medicine summary via Perplexity: {e}")
            return f"Unable to generate summary for {medicine_name} at this time. Please consult with your healthcare provider."

    async def generate_summary_from_file_id(self, file_id: str, summary_type: SummaryType, context: Optional[str] = None) -> SummaryResponse:
        """Generate summary using stored parsed content from file ID"""
        try:
            from app.services.file_service import file_service
            
            # Get parsed content from database
            content = await file_service.get_parsed_content(file_id)
            
            if not content:
                return SummaryResponse(
                    layman_summary="No parsed content available for this file.",
                    doctor_summary="File content not available for processing."
                )
            
            # Generate summary using the stored content
            summary_request = SummaryRequest(
                content=content,
                summary_type=summary_type,
                context=context
            )
            
            return await self.generate_summary(summary_request)
            
        except Exception as e:
            logger.error(f"Error generating summary from file ID {file_id}: {e}")
            return SummaryResponse(
                layman_summary="Unable to generate summary at this time.",
                doctor_summary="Summary generation failed."
            )

# Global instance
agent_service = AgentService() 