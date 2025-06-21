import logging
from openai import OpenAI
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class PerplexityService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.client = None
        
    def _get_client(self) -> OpenAI:
        """Get or create OpenAI client for OpenRouter"""
        if self.client is None:
            extra_headers = {}
                
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                default_headers=extra_headers
            )
        return self.client
    
    async def generate_summary(self, medicine_name: str) -> str:
        """Generate a comprehensive summary of a medicine using OpenRouter (Perplexity model)"""
        try:
            if not self.api_key:
                logger.warning("OpenRouter API key not configured")
                return self._fallback_summary(medicine_name)
            
            client = self._get_client()
            
            # Create a comprehensive prompt for medicine information
            prompt = f"""
            The following is the medicine name: {medicine_name}
            Provide a super-simplified, easy to understand layman's summary of the medicine '{medicine_name}' for patients to understand. 
            Include the following information:
            1. Generic name and common brand names
            2. What it's used for (indications)
            3. How it works (mechanism of action)
            4. Common side effects
            5. Important warnings and precautions
            6. Drug interactions to be aware of
            7. Dosage information (general guidance)
            8. Storage instructions
            
            Format the response in a clear, structured manner suitable for patients. Keep it short and concise for non-medical people.
            """
            
            response = client.chat.completions.create(
                model="perplexity/llama-3.1-sonar-small-128k-online",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.3,
                top_p=0.9
            )
            
            if response.choices and len(response.choices) > 0:
                summary = response.choices[0].message.content
                return summary
            else:
                logger.error("Unexpected response format from OpenRouter API")
                return self._fallback_summary(medicine_name)
                
        except Exception as e:
            logger.error(f"Error with OpenRouter API: {e}")
            return self._fallback_summary(medicine_name)
    
    async def search_medicine_info(self, medicine_name: str) -> Dict[str, Any]:
        """Search for detailed medicine information using OpenRouter"""
        try:
            if not self.api_key:
                return {"error": "OpenRouter API key not configured"}
            
            client = self._get_client()
            
            prompt = f"""
            Search for detailed information about the medicine '{medicine_name}'.
            Return the information in JSON format with the following structure:
            {{
                "generic_name": "string",
                "brand_names": ["list", "of", "brands"],
                "indications": ["list", "of", "uses"],
                "mechanism": "how it works",
                "side_effects": ["list", "of", "side effects"],
                "warnings": ["list", "of", "warnings"],
                "interactions": ["list", "of", "interactions"],
                "dosage": "general dosage info",
                "storage": "storage instructions"
            }}
            """
            
            response = client.chat.completions.create(
                model="perplexity/llama-3.1-sonar-small-128k-online",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                # Try to parse JSON from the response
                try:
                    import json
                    return json.loads(content)
                except json.JSONDecodeError:
                    # If JSON parsing fails, return as text
                    return {"summary": content}
            else:
                return {"error": "No response from OpenRouter API"}
                
        except Exception as e:
            logger.error(f"Error searching medicine info: {e}")
            return {"error": f"Failed to search medicine info: {str(e)}"}
    
    def _fallback_summary(self, medicine_name: str) -> str:
        """Fallback summary when API is not available"""
        return f"""
        Medicine: {medicine_name}
        
        This is a fallback summary as the OpenRouter API is not available.
        Please consult with your healthcare provider or pharmacist for accurate information about {medicine_name}.
        
        Important: Always consult with a healthcare professional before taking any medication.
        """
    
    async def close(self):
        """Close the client (no cleanup needed for OpenAI client)"""
        self.client = None

# Global instance
perplexity_service = PerplexityService() 