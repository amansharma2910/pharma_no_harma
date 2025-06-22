import logging
import requests
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class SarvamTranslationService:
    """Service for translating medical content using Sarvam AI APIs"""
    
    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.base_url = "https://api.sarvam.ai/translate"
        self.max_chars = 1000  # Sarvam API limit
        self.supported_languages = {
            "bn-IN": "Bengali",
            "en-IN": "English", 
            "gu-IN": "Gujarati",
            "hi-IN": "Hindi",
            "kn-IN": "Kannada",
            "ml-IN": "Malayalam",
            "mr-IN": "Marathi",
            "od-IN": "Odia",
            "pa-IN": "Punjabi",
            "ta-IN": "Tamil",
            "te-IN": "Telugu"
        }
    
    def summarize_for_translation(self, text: str) -> str:
        """
        Further summarize text to fit within translation API limits
        Preserves essential medical information while reducing length
        
        Args:
            text: Original text to summarize
            
        Returns:
            Summarized text under 1000 characters
        """
        if not text or len(text) <= self.max_chars:
            return text
        
        logger.info(f"Summarizing text from {len(text)} to under {self.max_chars} characters")
        
        # Remove markdown formatting and extra whitespace
        import re
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Remove italic
        text = re.sub(r'#+\s*', '', text)               # Remove headers
        text = re.sub(r'---\s*', '', text)              # Remove separators
        text = re.sub(r'\n\s*\n', '\n', text)           # Remove extra newlines
        text = re.sub(r'\s+', ' ', text)                # Normalize whitespace
        
        # If still too long, truncate intelligently
        if len(text) > self.max_chars:
            # Try to find a good breaking point
            words = text.split()
            truncated = ""
            
            for word in words:
                if len(truncated + " " + word) <= self.max_chars - 50:  # Leave some buffer
                    truncated += (" " + word) if truncated else word
                else:
                    break
            
            if truncated:
                text = truncated + "..."
            else:
                # Fallback: just truncate
                text = text[:self.max_chars - 3] + "..."
        
        logger.info(f"Summarized text length: {len(text)} characters")
        return text
    
    def translate_text(self, text: str, target_language: str, source_language: str = "auto") -> Dict[str, Any]:
        """
        Translate text using Sarvam AI API
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'hi-IN', 'bn-IN')
            source_language: Source language code (default: 'auto' for auto-detection)
            
        Returns:
            Dict containing translation result or error
        """
        try:
            if not self.api_key:
                logger.error("Sarvam API key not configured")
                return {
                    "success": False,
                    "error": "Translation service not configured",
                    "original_text": text
                }
            
            if target_language not in self.supported_languages:
                logger.error(f"Unsupported target language: {target_language}")
                return {
                    "success": False,
                    "error": f"Unsupported language: {target_language}",
                    "original_text": text,
                    "supported_languages": list(self.supported_languages.keys())
                }
            
            # Clean and validate text
            if not text or not text.strip():
                logger.error("Empty or invalid text provided for translation")
                return {
                    "success": False,
                    "error": "Empty or invalid text provided",
                    "original_text": text
                }
            
            # Summarize text if too long for translation API
            original_text = text
            text = self.summarize_for_translation(text)
            
            payload = {
                "input": text,
                "source_language_code": source_language,
                "target_language_code": target_language
            }
            
            headers = {
                "api-subscription-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            logger.info(f"Translating text to {target_language} ({self.supported_languages[target_language]})")
            logger.debug(f"Text length: {len(text)} chars")
            logger.debug(f"Text preview: {text[:100]}...")
            
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            
            # Log response details for debugging
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                logger.error(f"Translation API request failed: {response.status_code} {response.reason}")
                logger.error(f"Response body: {response.text}")
                logger.error(f"Request payload: {payload}")
                
                # Try to parse error response
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_data.get('message', response.text))
                except:
                    error_msg = response.text
                
                return {
                    "success": False,
                    "error": f"Translation API error ({response.status_code}): {error_msg}",
                    "original_text": original_text
                }
            
            result = response.json()
            logger.debug(f"API response: {result}")
            
            # Handle different response formats from Sarvam API
            if "translated_text" in result:
                translated_text = result["translated_text"]
            elif "translation" in result:
                translated_text = result["translation"]
            elif "output" in result:
                translated_text = result["output"]
            else:
                # If response structure is unknown, return the full response
                logger.warning(f"Unknown response format from Sarvam API: {result}")
                translated_text = str(result)
            
            return {
                "success": True,
                "translated_text": translated_text,
                "original_text": original_text,
                "summarized_text": text if text != original_text else None,
                "source_language": source_language,
                "target_language": target_language,
                "target_language_name": self.supported_languages[target_language]
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Translation API request failed: {e}")
            logger.error(f"Request details - URL: {self.base_url}, Headers: {headers}")
            return {
                "success": False,
                "error": f"Translation request failed: {str(e)}",
                "original_text": text
            }
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {
                "success": False,
                "error": f"Translation error: {str(e)}",
                "original_text": text
            }
    
    def translate_medical_summary(self, summary: str, target_language: str, summary_type: str = "LAYMAN") -> Dict[str, Any]:
        """
        Translate medical summary with special handling for medical terms
        
        Args:
            summary: Medical summary text
            target_language: Target language code
            summary_type: Type of summary ("LAYMAN" or "DOCTOR")
            
        Returns:
            Dict containing translated summary
        """
        try:
            # Only translate layman summaries, not doctor summaries
            if summary_type == "DOCTOR":
                logger.info("Skipping translation for doctor summary (only layman summaries are translated)")
                return {
                    "success": False,
                    "error": "Doctor summaries are not translated to preserve medical accuracy",
                    "original_text": summary,
                    "summary_type": summary_type
                }
            
            # Clean the summary text
            if not summary or not summary.strip():
                logger.error("Empty medical summary provided")
                return {
                    "success": False,
                    "error": "Empty medical summary provided",
                    "original_text": summary
                }
            
            # Add context for medical translation
            enhanced_text = f"Medical Summary: {summary}"
            
            result = self.translate_text(enhanced_text, target_language)
            
            if result["success"]:
                # Clean up the translated text (remove "Medical Summary:" prefix if present)
                translated_text = result["translated_text"]
                if translated_text.startswith("Medical Summary:"):
                    translated_text = translated_text.replace("Medical Summary:", "").strip()
                
                result["translated_text"] = translated_text
                result["summary_type"] = summary_type
                
                logger.info(f"Successfully translated {summary_type.lower()} summary to {target_language}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error translating medical summary: {e}")
            return {
                "success": False,
                "error": f"Medical summary translation failed: {str(e)}",
                "original_text": summary,
                "summary_type": summary_type
            }
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages"""
        return self.supported_languages.copy()
    
    def is_language_supported(self, language_code: str) -> bool:
        """Check if a language code is supported"""
        return language_code in self.supported_languages
    
    def get_language_name(self, language_code: str) -> Optional[str]:
        """Get language name from language code"""
        return self.supported_languages.get(language_code)

# Global instance
sarvam_translation_service = SarvamTranslationService() 