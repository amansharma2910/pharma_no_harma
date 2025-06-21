import logging
import os
import aiofiles
import hashlib
from typing import Optional, Dict, Any
from fastapi import UploadFile
from llama_parse import LlamaParse
from app.core.config import settings
from app.services.neo4j_service import neo4j_service
from app.services.agent_service import agent_service
from app.models.schemas import FileStatus, SummaryRequest, SummaryType

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_types = settings.ALLOWED_FILE_TYPES
        # Initialize LlamaParse parser
        try:
            self.parser = LlamaParse(
                api_key=settings.LLAMA_PARSE_API_KEY if hasattr(settings, 'LLAMA_PARSE_API_KEY') and settings.LLAMA_PARSE_API_KEY else None,
                result_type="text"
            )
            logger.info("LlamaParse initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize LlamaParse: {e}")
            self.parser = None
    
    async def save_file(self, file: UploadFile, health_record_id: str) -> str:
        """Save uploaded file to storage"""
        try:
            # Validate file size
            if file.size > self.max_file_size:
                raise ValueError(f"File size {file.size} exceeds maximum {self.max_file_size}")
            
            # Validate file type
            file_extension = file.filename.split('.')[-1].upper() if '.' in file.filename else ''
            if file_extension not in self.allowed_types:
                raise ValueError(f"File type {file_extension} not allowed")
            
            # Create directory structure
            record_dir = os.path.join(self.upload_dir, health_record_id)
            os.makedirs(record_dir, exist_ok=True)
            
            # Generate unique filename
            file_hash = hashlib.md5(f"{file.filename}{health_record_id}".encode()).hexdigest()
            safe_filename = f"{file_hash}_{file.filename}"
            file_path = os.path.join(record_dir, safe_filename)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            logger.info(f"File saved: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    async def process_file_async(self, file_id: str, file_path: str, health_record_id: str):
        """Process file asynchronously for AI analysis"""
        try:
            logger.info(f"Starting async processing for file: {file_id}")
            
            # Update file status to PROCESSING
            await neo4j_service.update_file(file_id, {"file_status": FileStatus.PROCESSING})
            
            # Extract text content from file
            content = await self._extract_text_content(file_path)
            
            if content:
                # Store the parsed content in the database
                await neo4j_service.update_file(file_id, {"parsed_content": content})
                
                # Generate AI summaries
                summary_request = SummaryRequest(
                    content=content,
                    summary_type=SummaryType.BOTH,
                    context=f"Health record: {health_record_id}"
                )
                
                summaries = await agent_service.generate_summary(summary_request)
                
                # Update file with summaries and status
                update_data = {
                    "layman_summary": summaries.layman_summary,
                    "doctor_summary": summaries.doctor_summary,
                    "file_status": FileStatus.PROCESSED
                }
                
                await neo4j_service.update_file(file_id, update_data)
                
                # Update health record last activity
                await neo4j_service.update_health_record(health_record_id, {})
                
                logger.info(f"File processing completed: {file_id}")
            else:
                # If no content extracted, mark as processed anyway
                await neo4j_service.update_file(file_id, {"file_status": FileStatus.PROCESSED})
                logger.warning(f"No content extracted from file: {file_id}")
                
        except Exception as e:
            logger.error(f"Error processing file {file_id}: {e}")
            # Mark as processed even if there's an error to avoid infinite retries
            await neo4j_service.update_file(file_id, {"file_status": FileStatus.PROCESSED})
    
    async def _extract_text_content(self, file_path: str) -> Optional[str]:
        """Extract text content from various file types"""
        try:
            file_extension = file_path.split('.')[-1].lower()
            
            if file_extension in ['txt']:
                return await self._extract_text(file_path)
            elif file_extension in ['pdf']:
                return await self._extract_pdf_text(file_path)
            elif file_extension in ['jpg', 'jpeg']:
                return await self._extract_image_text(file_path)
            else:
                logger.warning(f"Unsupported file type for text extraction: {file_extension}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
            return None
    
    async def _extract_text(self, file_path: str) -> str:
        """Extract text from plain text file"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            return content
        except Exception as e:
            logger.error(f"Error reading text file: {e}")
            return ""
    
    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file using LlamaParse"""
        try:
            if not self.parser:
                logger.error("LlamaParse parser not available")
                return ""
            
            # Use LlamaParse to extract text from PDF
            documents = self.parser.load_data(file_path)
            
            if documents and len(documents) > 0:
                # Extract text from all pages
                text_content = ""
                for doc in documents:
                    if hasattr(doc, 'text') and doc.text:
                        text_content += doc.text + "\n"
                
                if text_content.strip():
                    logger.info(f"Successfully extracted {len(text_content)} characters from PDF: {os.path.basename(file_path)}")
                    return text_content.strip()
                else:
                    logger.warning(f"No text content extracted from PDF: {os.path.basename(file_path)}")
                    return ""
            else:
                logger.warning(f"No documents parsed from PDF: {os.path.basename(file_path)}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting PDF text using LlamaParse: {e}")
            return ""
    
    async def _extract_image_text(self, file_path: str) -> str:
        """Extract text from image using LlamaParse OCR"""
        try:
            if not self.parser:
                logger.error("LlamaParse parser not available")
                return ""
            
            # Use LlamaParse to extract text from image using OCR
            documents = self.parser.load_data(file_path)
            
            if documents and len(documents) > 0:
                # Extract text from the image
                text_content = ""
                for doc in documents:
                    if hasattr(doc, 'text') and doc.text:
                        text_content += doc.text + "\n"
                
                if text_content.strip():
                    logger.info(f"Successfully extracted {len(text_content)} characters from image: {os.path.basename(file_path)}")
                    return text_content.strip()
                else:
                    logger.warning(f"No text content extracted from image: {os.path.basename(file_path)}")
                    return ""
            else:
                logger.warning(f"No documents parsed from image: {os.path.basename(file_path)}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting image text using LlamaParse: {e}")
            return ""
    
    async def get_parsed_content(self, file_id: str) -> Optional[str]:
        """Get parsed content from database to avoid re-parsing"""
        try:
            file_info = await neo4j_service.get_file_by_id(file_id)
            if file_info and file_info.get("f", {}).get("parsed_content"):
                return file_info["f"]["parsed_content"]
            return None
        except Exception as e:
            logger.error(f"Error getting parsed content for file {file_id}: {e}")
            return None

    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information"""
        try:
            if not os.path.exists(file_path):
                return {}
            
            stat = os.stat(file_path)
            return {
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "exists": True
            }
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {}
    
    async def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded file"""
        errors = []
        
        # Check file size
        if file.size > self.max_file_size:
            errors.append(f"File size {file.size} exceeds maximum {self.max_file_size}")
        
        # Check file type
        if file.filename:
            file_extension = file.filename.split('.')[-1].upper() if '.' in file.filename else ''
            if file_extension not in self.allowed_types:
                errors.append(f"File type {file_extension} not allowed. Allowed types: {', '.join(self.allowed_types)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "size": file.size,
            "filename": file.filename,
            "content_type": file.content_type
        }
    
    async def cleanup_orphaned_files(self) -> int:
        """Clean up files that don't have database records"""
        try:
            # This would find files in storage that don't have corresponding database records
            # For now, return 0
            return 0
        except Exception as e:
            logger.error(f"Error cleaning up orphaned files: {e}")
            return 0

    async def is_file_parsed(self, file_id: str) -> bool:
        """Check if a file has been parsed and has content available"""
        try:
            content = await self.get_parsed_content(file_id)
            return content is not None and len(content.strip()) > 0
        except Exception as e:
            logger.error(f"Error checking if file {file_id} is parsed: {e}")
            return False

# Global instance
file_service = FileService() 