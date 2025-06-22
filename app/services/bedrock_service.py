import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
import boto3
import aioboto3
from botocore.exceptions import ClientError, NoCredentialsError
from app.core.config import settings
from app.models.schemas import AgentQuery, AgentResponse, SummaryRequest, SummaryResponse, SummaryType
from prompts import layman_summary_prompt, doctor_summary_prompt, combined_summary_prompt

logger = logging.getLogger(__name__)

class BedrockService:
    def __init__(self):
        self.session = None
        self.bedrock_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AWS Bedrock clients"""
        try:
            # Configure AWS credentials
            aws_config = {
                'region_name': settings.AWS_REGION,
            }
            
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                aws_config.update({
                    'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
                    'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
                })
                
                if settings.AWS_SESSION_TOKEN:
                    aws_config['aws_session_token'] = settings.AWS_SESSION_TOKEN
            
            # Initialize boto3 session
            self.session = boto3.Session(**aws_config)
            
            # Initialize Bedrock clients
            self.bedrock_client = self.session.client('bedrock-runtime')
                
            logger.info("AWS Bedrock clients initialized successfully")
            
            # Validate model configuration
            self._validate_model_configuration()
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS credentials.")
            self.bedrock_client = None
        except Exception as e:
            logger.error(f"Failed to initialize AWS Bedrock clients: {e}")
            self.bedrock_client = None
    
    def _validate_model_configuration(self):
        """Validate that the configured model is amazon.nova-pro-v1:0"""
        model_id = settings.BEDROCK_MODEL_ID
        
        if model_id != "amazon.nova-pro-v1:0":
            logger.warning(f"Model '{model_id}' is not supported. Only amazon.nova-pro-v1:0 is supported.")
            logger.info("The service will use amazon.nova-pro-v1:0 regardless of the configured model.")
        
        logger.info("Using Amazon Nova Pro v1:0 model for all requests.")
    
    async def invoke_model(self, prompt: str, model_id: Optional[str] = None, 
                          max_tokens: int = 1000, temperature: float = 0.3,
                          inference_profile_arn: Optional[str] = None) -> str:
        """Invoke AWS Bedrock model with prompt"""
        if not self.bedrock_client:
            raise Exception("Bedrock client not initialized")
        
        # Use inference profile ARN as modelId if provided, otherwise use amazon.nova-pro-v1:0
        if inference_profile_arn:
            model_id = inference_profile_arn
            logger.info(f"Using inference profile ARN as modelId: {inference_profile_arn}")
        else:
            model_id = "amazon.nova-pro-v1:0"
            logger.warning("No inference profile ARN provided. This may fail for Nova Pro models.")
        
        try:
            # Amazon Nova Pro v1:0 specific request format
            request_body = {
                "inferenceConfig": {
                    "max_new_tokens": max_tokens
                },
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            # Prepare invoke parameters - only valid parameters
            invoke_params = {
                "modelId": model_id,
                "contentType": "application/json",
                "accept": "application/json",
                "body": json.dumps(request_body)
            }
            
            # Invoke model
            response = self.bedrock_client.invoke_model(**invoke_params)
            
            response_body = json.loads(response['body'].read())
            
            # Log the complete response for debugging
            logger.info(f"Complete Bedrock API response: {json.dumps(response_body, indent=2)}")
            
            # Extract response for Amazon Nova Pro - handle different response structures
            try:
                # Try different possible response structures
                if 'output' in response_body and 'message' in response_body['output'] and 'content' in response_body['output']['message']:
                    # AWS Bedrock inference profile response structure
                    content = response_body['output']['message']['content']
                    if isinstance(content, list) and len(content) > 0:
                        return content[0]['text']
                    elif isinstance(content, dict):
                        return content['text']
                elif 'content' in response_body and isinstance(response_body['content'], list) and len(response_body['content']) > 0:
                    return response_body['content'][0]['text']
                elif 'content' in response_body and isinstance(response_body['content'], dict):
                    return response_body['content']['text']
                elif 'text' in response_body:
                    return response_body['text']
                elif 'generation' in response_body:
                    return response_body['generation']
                elif 'outputText' in response_body:
                    return response_body['outputText']
                elif 'results' in response_body and isinstance(response_body['results'], list) and len(response_body['results']) > 0:
                    return response_body['results'][0].get('outputText', '')
                else:
                    # If none of the expected structures match, return the response as string
                    logger.warning(f"Unexpected response structure, returning response as string: {response_body}")
                    return str(response_body)
            except (KeyError, IndexError, TypeError) as e:
                logger.error(f"Error parsing response: {e}")
                logger.error(f"Response body: {response_body}")
                return str(response_body)
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'ValidationException':
                logger.error(f"Invalid request to Bedrock: {e}")
                raise Exception("Invalid request format")
            elif error_code == 'ThrottlingException':
                logger.error(f"Bedrock rate limit exceeded: {e}")
                raise Exception("Rate limit exceeded. Please try again later.")
            elif error_code == 'ModelStreamErrorException':
                logger.error(f"Bedrock model stream error: {e}")
                raise Exception("Model processing error")
            else:
                logger.error(f"Bedrock client error: {e}")
                raise Exception(f"AWS Bedrock error: {error_code}")
        except Exception as e:
            logger.error(f"Unexpected error invoking Bedrock model: {e}")
            raise Exception(f"Failed to invoke AI model: {str(e)}")
    
    async def process_query_with_bedrock(self, query: AgentQuery) -> AgentResponse:
        """Process natural language query using AWS Bedrock"""
        try:
            # Create a comprehensive prompt for the AI
            system_prompt = self._create_query_prompt(query)
            
            # Invoke Bedrock model
            response_text = await self.invoke_model(system_prompt, inference_profile_arn=settings.BEDROCK_INFERENCE_PROFILE_ARN)
            
            # Parse and structure the response
            return self._parse_agent_response(response_text, query)
            
        except Exception as e:
            logger.error(f"Error processing query with Bedrock: {e}")
            return AgentResponse(
                response="I'm sorry, I couldn't process your query at the moment.",
                confidence=0.0
            )
    
    async def generate_summary_with_bedrock(self, request: SummaryRequest) -> SummaryResponse:
        """Generate AI-powered summaries using AWS Bedrock"""
        try:
            # Create appropriate prompt for summary type
            prompt = self._create_summary_prompt(request)
            
            # Invoke Bedrock model
            summary = await self.invoke_model(prompt, max_tokens=1500, inference_profile_arn=settings.BEDROCK_INFERENCE_PROFILE_ARN)
            
            # Parse response based on summary type
            return self._parse_summary_response(summary, request.summary_type)
            
        except Exception as e:
            logger.error(f"Error generating summary with Bedrock: {e}")
            return self._simple_summarize(request.content, request.summary_type)
    
    def _create_query_prompt(self, query: AgentQuery) -> str:
        """Create a comprehensive prompt for query processing"""
        base_prompt = """You are an AI assistant for a health records management system. 
        You help patients and healthcare professionals understand medical information.
        
        User Query: {query}
        User Type: {user_type}
        
        Please provide a helpful response that:
        1. Addresses the user's question clearly
        2. Uses appropriate language for the user type (patient-friendly vs medical terminology)
        3. Suggests relevant actions they can take
        4. Mentions potential data sources that could help answer their question
        
        Response should be structured and informative."""
        
        return base_prompt.format(
            query=query.query,
            user_type=query.user_type.value
        )
    
    def _create_summary_prompt(self, request: SummaryRequest) -> str:
        """Create appropriate prompt for summary generation using improved prompts"""
        if request.summary_type.value == "LAYMAN":
            prompt = layman_summary_prompt
        elif request.summary_type.value == "DOCTOR":
            prompt = doctor_summary_prompt
        else:  # BOTH
            prompt = combined_summary_prompt
        
        # Add content and context
        content = request.content[:8000]  # Limit content length
        context = request.context or "Medical document"
        
        return f"{prompt}\n\nContent to summarize:\n{content}\n\nContext: {context}"
    
    def _parse_agent_response(self, response_text: str, query: AgentQuery) -> AgentResponse:
        """Parse and structure the agent response"""
        # Simple parsing - in a real implementation, you might want more sophisticated parsing
        return AgentResponse(
            response=response_text,
            confidence=0.8,
            sources=["health_records", "medical_database"],
            suggested_actions=["view_health_record", "schedule_appointment"],
            cypher_queries_executed=[]
        )
    
    def _parse_summary_response(self, summary: str, summary_type: SummaryType) -> SummaryResponse:
        """Parse summary response based on type"""
        if summary_type.value == "BOTH":
            parts = summary.split("---")
            layman_summary = parts[0].strip() if len(parts) > 0 else summary
            doctor_summary = parts[1].strip() if len(parts) > 1 else summary
            
            return SummaryResponse(
                layman_summary=layman_summary,
                doctor_summary=doctor_summary
            )
        elif summary_type.value == "LAYMAN":
            return SummaryResponse(layman_summary=summary)
        else:
            return SummaryResponse(doctor_summary=summary)
    
    def _simple_summarize(self, content: str, summary_type: SummaryType) -> SummaryResponse:
        """Simple fallback summarization"""
        simple_summary = f"Document Summary: {content[:500]}..."
        
        if summary_type.value == "BOTH":
            return SummaryResponse(
                layman_summary=f"Document Summary: {simple_summary}",
                doctor_summary=f"Medical Document Summary: {simple_summary}"
            )
        elif summary_type.value == "LAYMAN":
            return SummaryResponse(layman_summary=f"Document Summary: {simple_summary}")
        else:
            return SummaryResponse(doctor_summary=f"Medical Document Summary: {simple_summary}")

# Global instance
bedrock_service = BedrockService() 