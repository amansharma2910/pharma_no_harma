# OpenRouter Integration (Perplexity via OpenRouter)

This document describes the integration of Perplexity AI for medicine information and summaries in the Pharma No Harma application via OpenRouter.

## Overview

The OpenRouter integration provides AI-powered medicine information and summaries using Perplexity models through the OpenRouter API. This service can generate comprehensive medicine summaries and structured information for both patients and healthcare professionals.

## Features

- **Medicine Summaries**: Generate comprehensive summaries of medicines including indications, side effects, warnings, and usage information
- **Structured Medicine Info**: Get detailed medicine information in JSON format
- **Fallback Support**: Graceful degradation when API is not available
- **Error Handling**: Robust error handling with logging
- **OpenAI SDK Compatible**: Uses the standard OpenAI SDK for easy integration

## Setup

### 1. Environment Configuration

Add the following environment variables to your `.env` file:

```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_SITE_URL=https://your-site-url.com
OPENROUTER_SITE_NAME=Your Site Name
```

### 2. API Key

To get an OpenRouter API key:

1. Visit [OpenRouter](https://openrouter.ai/)
2. Sign up for an account
3. Navigate to API settings
4. Generate an API key
5. Add the key to your environment variables

### 3. Site Information (Optional)

The `OPENROUTER_SITE_URL` and `OPENROUTER_SITE_NAME` are optional but recommended for:
- Better rankings on OpenRouter
- Analytics and usage tracking
- Rate limit management

## Usage

### Service Usage

```python
from app.services.perplexity_service import perplexity_service

# Generate medicine summary
summary = await perplexity_service.generate_summary("Aspirin")

# Get structured medicine information
info = await perplexity_service.search_medicine_info("Aspirin")
```

### API Endpoints

#### Get Medicine Summary
```
GET /medicines/{medicine_name}/summary
```

**Response:**
```json
{
  "success": true,
  "medicine_name": "Aspirin",
  "summary": "Comprehensive medicine summary...",
  "source": "openrouter_perplexity"
}
```

#### Get Medicine Information
```
GET /medicines/{medicine_name}/info
```

**Response:**
```json
{
  "success": true,
  "medicine_name": "Aspirin",
  "info": {
    "generic_name": "Acetylsalicylic acid",
    "brand_names": ["Bayer", "Ecotrin", "Bufferin"],
    "indications": ["Pain relief", "Fever reduction", "Blood thinning"],
    "mechanism": "Inhibits cyclooxygenase enzymes...",
    "side_effects": ["Stomach upset", "Bleeding risk"],
    "warnings": ["Not for children with viral infections"],
    "interactions": ["Blood thinners", "NSAIDs"],
    "dosage": "325-650mg every 4-6 hours",
    "storage": "Store at room temperature"
  },
  "source": "openrouter_perplexity"
}
```

## Integration with Agent Service

The OpenRouter service is integrated with the Agent Service for medicine-related queries:

```python
from app.services.agent_service import agent_service

# Generate medicine summary via agent service
summary = await agent_service.generate_medicine_summary_via_perplexity("Aspirin")
```

## Error Handling

The service includes comprehensive error handling:

- **API Key Missing**: Returns fallback summary
- **Network Errors**: Logs error and returns fallback
- **API Errors**: Handles HTTP errors gracefully
- **JSON Parsing Errors**: Falls back to text response

## Testing

Run the test script to verify the integration:

```bash
python test_openrouter.py
```

## Configuration Options

### Model Selection

The service uses the `perplexity/llama-3.1-sonar-small-128k-online` model by default. You can modify this in `app/services/perplexity_service.py`.

### Token Limits

- Summary generation: 1000 tokens
- Info search: 1500 tokens

### Temperature Settings

- Summary generation: 0.3 (balanced creativity)
- Info search: 0.1 (more factual)

## Security Considerations

1. **API Key Protection**: Never commit API keys to version control
2. **Rate Limiting**: Be aware of OpenRouter API rate limits
3. **Data Privacy**: Medicine queries are sent to OpenRouter servers
4. **Fallback Mode**: Service works without API key for testing

## Troubleshooting

### Common Issues

1. **"OpenRouter API key not configured"**
   - Check your `.env` file
   - Verify the environment variable name

2. **HTTP 401 Unauthorized**
   - Verify your API key is correct
   - Check if your account has API access

3. **Network Timeout**
   - Check your internet connection
   - Verify the API endpoint is accessible

### Logging

The service logs all errors and warnings. Check your application logs for detailed error information.

## Future Enhancements

- Caching of medicine information
- Batch processing for multiple medicines
- Integration with medication scheduling
- Patient-specific medicine recommendations
- Drug interaction checking 