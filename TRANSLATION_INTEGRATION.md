# Sarvam Translation Integration

## Overview

This document outlines the integration of Sarvam AI's translation APIs into the Pharma No Harma application to provide medical summaries and information in regional Indian languages. This feature is particularly beneficial for elderly patients who may prefer to read medical information in their native language.

## Supported Languages

The application supports the following regional Indian languages:

| Language Code | Language Name | Region |
|---------------|---------------|---------|
| bn-IN | Bengali | West Bengal, Tripura |
| en-IN | English | All India |
| gu-IN | Gujarati | Gujarat |
| hi-IN | Hindi | North India |
| kn-IN | Kannada | Karnataka |
| ml-IN | Malayalam | Kerala |
| mr-IN | Marathi | Maharashtra |
| od-IN | Odia | Odisha |
| pa-IN | Punjabi | Punjab |
| ta-IN | Tamil | Tamil Nadu |
| te-IN | Telugu | Telangana, Andhra Pradesh |

## Features

### 1. Language Selection
- **Sidebar Language Selector**: Users can select their preferred language from the sidebar
- **Per-Section Language Control**: Different sections can have different language preferences
- **Session Persistence**: Language preference is maintained throughout the session

### 2. Translation Services
- **Medical Summaries**: Translate health record summaries to regional languages
- **File Summaries**: Translate file analysis summaries
- **Medicine Information**: Translate medicine descriptions and instructions
- **Real-time Translation**: On-demand translation without page refresh

### 3. User Experience Enhancements
- **Translation Status Indicators**: Shows when content has been translated
- **Refresh Translation**: Allows users to regenerate translations
- **Copy to Clipboard**: Easy copying of translated text
- **Fallback Handling**: Graceful handling when translation fails

## Implementation Details

### Backend Services

#### 1. Sarvam Translation Service (`app/services/sarvam_translation_service.py`)
```python
class SarvamTranslationService:
    def translate_text(self, text: str, target_language: str, source_language: str = "auto")
    def translate_medical_summary(self, summary: str, target_language: str)
    def get_supported_languages(self)
    def is_language_supported(self, language_code: str)
```

#### 2. API Endpoints (`app/main.py`)
- `GET /translation/languages` - Get supported languages
- `POST /translation/translate` - Translate general text
- `POST /translation/translate-summary` - Translate medical summaries
- `POST /files/{file_id}/translate-summary` - Translate file summaries
- `POST /health-records/{health_record_id}/translate-summary` - Translate health record summaries

### Frontend Integration

#### 1. Streamlit Application (`streamlit_app.py`)
- **Language Selector**: Sidebar widget for language preference
- **Translation Functions**: Helper functions for translation
- **UI Components**: Translation controls and status indicators

#### 2. Key Functions
```python
def show_language_selector()  # Language selection widget
def translate_summary_if_needed()  # Translation helper
def get_language_options()  # Get available languages
```

## Configuration

### Environment Variables
Add the following to your `.env` file:
```bash
SARVAM_API_KEY=your_sarvam_api_key_here
```

### API Configuration
The Sarvam API is configured with:
- **Base URL**: `https://api.sarvam.ai/translate`
- **Authentication**: API subscription key in headers
- **Timeout**: 30 seconds for requests
- **Error Handling**: Comprehensive error handling and fallbacks

## Usage Examples

### 1. Selecting Language
1. Open the Streamlit application
2. In the sidebar, find the "Language Preferences" section
3. Select your preferred language from the dropdown
4. The language preference will be applied to all summaries

### 2. Viewing Translated Summaries
1. Navigate to "View Records" or "File Management"
2. Select a medical record or file
3. Choose your preferred language for summaries
4. View the translated content with translation status indicators

### 3. Medicine Information in Regional Language
1. Go to "Medicine Search"
2. Enter a medicine name
3. Select your preferred language
4. View medicine information in your chosen language

## API Integration Details

### Sarvam API Request Format
```python
payload = {
    "input": "text_to_translate",
    "source_language_code": "auto",
    "target_language_code": "hi-IN"
}

headers = {
    "api-subscription-key": "your_api_key",
    "Content-Type": "application/json"
}
```

### Response Handling
The service handles multiple response formats from Sarvam API:
- `translated_text` field
- `translation` field
- `output` field
- Fallback to string representation

## Error Handling

### Translation Failures
- **API Unavailable**: Shows original text with warning
- **Invalid Language**: Displays error message with supported languages
- **Network Issues**: Graceful fallback to original content
- **Rate Limiting**: User-friendly error messages

### Fallback Mechanisms
1. **Original Text**: Always shows original English text if translation fails
2. **Default Languages**: Hardcoded language list if API is unavailable
3. **User Feedback**: Clear error messages explaining what went wrong

## Security Considerations

### API Key Management
- **Environment Variables**: API keys stored in environment variables
- **No Hardcoding**: Keys are never hardcoded in source code
- **Access Control**: API keys are not exposed in client-side code

### Data Privacy
- **No Storage**: Translated content is not permanently stored
- **Temporary Translation**: Translations are generated on-demand
- **Audit Logging**: Translation requests are logged for monitoring

## Performance Optimization

### Caching Strategy
- **Language Options**: Cached in session state
- **Translation Results**: Not cached (always fresh)
- **API Calls**: Minimized through smart request handling

### Request Optimization
- **Batch Translation**: Not implemented (individual requests)
- **Timeout Handling**: 30-second timeout for API calls
- **Error Recovery**: Automatic retry with fallback

## Testing

### Manual Testing
1. **Language Selection**: Test all supported languages
2. **Translation Quality**: Verify medical terminology accuracy
3. **Error Scenarios**: Test with invalid API keys, network issues
4. **UI Responsiveness**: Test translation controls and status indicators

### API Testing
```python
# Test translation service
from app.services.sarvam_translation_service import sarvam_translation_service

result = sarvam_translation_service.translate_text(
    "Your blood pressure is high", 
    "hi-IN"
)
print(result)
```

## Future Enhancements

### Planned Features
1. **Translation Memory**: Cache common medical terms
2. **Batch Translation**: Translate multiple summaries at once
3. **Quality Feedback**: User feedback on translation quality
4. **Custom Dictionaries**: Medical terminology dictionaries
5. **Offline Support**: Basic offline translation capabilities

### Potential Improvements
1. **Multilingual UI**: Complete UI translation
2. **Voice Integration**: Text-to-speech for translated content
3. **Regional Dialects**: Support for regional variations
4. **Medical Glossary**: Standardized medical term translations

## Troubleshooting

### Common Issues

#### 1. Translation Not Working
- **Check API Key**: Verify SARVAM_API_KEY is set correctly
- **Network Connection**: Ensure internet connectivity
- **API Limits**: Check if API quota is exceeded

#### 2. Language Not Available
- **Supported Languages**: Verify language code is in supported list
- **API Response**: Check API response for error details
- **Fallback**: Application should show original text

#### 3. Poor Translation Quality
- **Medical Terms**: Some medical terms may not translate perfectly
- **Context**: Medical context helps improve translation
- **Feedback**: Report issues for improvement

### Debug Information
- **API Logs**: Check application logs for API errors
- **Response Data**: Raw API responses logged for debugging
- **User Feedback**: Collect user feedback on translation quality

## Support and Maintenance

### Monitoring
- **API Usage**: Monitor API call frequency and success rates
- **Error Rates**: Track translation failure rates
- **User Feedback**: Collect feedback on translation quality

### Maintenance
- **API Updates**: Keep up with Sarvam API changes
- **Language Support**: Add new languages as needed
- **Performance**: Monitor and optimize translation performance

## Conclusion

The Sarvam translation integration significantly enhances the user experience for patients who prefer regional languages. The implementation provides:

- **Accessibility**: Medical information in native languages
- **User Control**: Flexible language selection
- **Reliability**: Robust error handling and fallbacks
- **Performance**: Optimized for real-time translation
- **Security**: Secure API key management

This feature is particularly valuable for elderly patients who may have difficulty understanding medical information in English, making healthcare more accessible and inclusive. 