import logging
from openai import OpenAI
from typing import Dict, Any, Optional
from app.core.config import settings
from prompts import medicine_summary_prompt

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
            
            # Use the improved medicine summary prompt
            prompt = f"{medicine_summary_prompt}\n\nMedicine: {medicine_name}"
            
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
        """Fallback summary when API is not available - patient-friendly version"""
        return f"""
**{medicine_name.upper()}**

**What you need to know:**
• This is a medicine your doctor prescribed
• Always take exactly as your doctor told you
• Keep all your medicine appointments

**IMPORTANT SAFETY:**
• **Call your doctor if you feel worse**
• **Call 911 if you have trouble breathing**
• Tell your doctor about all other medicines you take
• Keep this medicine away from children

**What to do next:**
• Talk to your pharmacist about this medicine
• Ask your doctor any questions you have
• Write down when you take your medicine

**Storage:** Keep in a cool, dry place. Keep away from children.

**Remember:** This is basic information. Your doctor and pharmacist know your specific situation best.
"""
    
    async def close(self):
        """Close the client (no cleanup needed for OpenAI client)"""
        self.client = None

# Global instance
perplexity_service = PerplexityService() 