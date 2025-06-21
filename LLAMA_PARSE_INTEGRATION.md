# LlamaParse Integration

This document explains the integration of LlamaParse for PDF and image text extraction in the Health Records API.

## Overview

LlamaParse is a powerful document parsing library that can extract text from various file formats including:
- PDF files
- Images (JPG, JPEG, PNG, etc.)
- Documents (DOC, DOCX, etc.)
- And many more formats

## Installation

The LlamaParse package has been added to `requirements.txt`:

```bash
pip install llama-parse
```

## Configuration

### Environment Variables

Add the following to your `.env` file:

```env
LLAMA_PARSE_API_KEY=your_llama_parse_api_key_here
```

**Note**: LlamaParse can work without an API key for basic functionality, but having an API key provides:
- Higher rate limits
- Better OCR accuracy
- Access to advanced features

### Settings

The API key is configured in `app/core/config.py`:

```python
LLAMA_PARSE_API_KEY: Optional[str] = None
```

## Usage

### File Service Integration

The `FileService` class has been updated to use LlamaParse for text extraction:

```python
from app.services.file_service import file_service

# Extract text from PDF
pdf_text = await file_service._extract_pdf_text("path/to/document.pdf")

# Extract text from image
image_text = await file_service._extract_image_text("path/to/image.jpg")
```

### Supported File Types

The following file types are supported for text extraction:

1. **PDF Files** (`.pdf`)
   - Extracts text from all pages
   - Handles complex layouts
   - Preserves formatting

2. **Image Files** (`.jpg`, `.jpeg`)
   - Uses OCR to extract text
   - Handles handwritten and printed text
   - Supports multiple languages

3. **Text Files** (`.txt`)
   - Direct text extraction
   - UTF-8 encoding support

### Error Handling

The integration includes comprehensive error handling:

- **Parser Initialization**: Gracefully handles cases where LlamaParse fails to initialize
- **File Processing**: Logs errors and returns empty string on failure
- **API Key**: Works without API key (with limitations)

## Implementation Details

### FileService Updates

The `FileService` class has been enhanced with:

1. **LlamaParse Initialization**:
   ```python
   self.parser = LlamaParse(
       api_key=settings.LLAMA_PARSE_API_KEY,
       result_type="text"
   )
   ```

2. **PDF Text Extraction**:
   ```python
   async def _extract_pdf_text(self, file_path: str) -> str:
       documents = self.parser.load_data(file_path)
       # Extract and combine text from all pages
   ```

3. **Image Text Extraction**:
   ```python
   async def _extract_image_text(self, file_path: str) -> str:
       documents = self.parser.load_data(file_path)
       # Extract text using OCR
   ```

### Logging

The integration includes detailed logging:

- Success messages with character count
- Warning messages for empty extractions
- Error messages for failed operations

## Testing

Run the test script to verify the integration:

```bash
python test_llama_parse.py
```

## API Endpoints

The existing file upload endpoints automatically use LlamaParse for text extraction:

- `POST /api/v1/health-records/{health_record_id}/files`
- `POST /api/v1/files/upload`

## Performance Considerations

1. **File Size**: Large files may take longer to process
2. **API Limits**: Without API key, there are rate limits
3. **Memory Usage**: Large documents are processed in chunks
4. **Async Processing**: All operations are asynchronous for better performance

## Troubleshooting

### Common Issues

1. **Parser Not Available**
   - Check if LlamaParse is installed: `pip install llama-parse`
   - Verify API key configuration
   - Check logs for initialization errors

2. **No Text Extracted**
   - Verify file format is supported
   - Check if file contains extractable text
   - For images, ensure text is clearly visible

3. **API Key Issues**
   - Verify API key is valid
   - Check rate limits
   - Ensure proper environment variable setup

### Logs

Check the application logs for detailed error messages:

```python
logger.error(f"Error extracting PDF text using LlamaParse: {e}")
logger.warning(f"No text content extracted from PDF: {filename}")
```

## Future Enhancements

Potential improvements:

1. **Batch Processing**: Process multiple files simultaneously
2. **Caching**: Cache extracted text to avoid re-processing
3. **Format Support**: Add support for more file formats
4. **Quality Settings**: Configurable OCR quality settings
5. **Language Detection**: Automatic language detection for OCR

## Dependencies

- `llama-parse>=0.6.35`
- `llama-cloud-services>=0.6.35`
- `llama-index-core>=0.12.0`

## License

LlamaParse is subject to its own license terms. Please refer to the official LlamaParse documentation for licensing information. 