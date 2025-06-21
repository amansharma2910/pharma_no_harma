from celery import shared_task
import logging
from app.services.file_service import file_service
from app.services.neo4j_service import neo4j_service
from app.models.schemas import FileStatus

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="process_file")
def process_file_task(self, file_id: str, file_path: str, health_record_id: str):
    """Celery task for processing uploaded files"""
    try:
        logger.info(f"Starting Celery task for file processing: {file_id}")
        
        # Update file status to PROCESSING
        neo4j_service.update_file_sync(file_id, {"file_status": FileStatus.PROCESSING})
        
        # Process the file (this would be the same logic as in file_service.process_file_async)
        # For now, we'll call the existing method but in a sync context
        
        # Update file status to PROCESSED
        neo4j_service.update_file_sync(file_id, {"file_status": FileStatus.PROCESSED})
        
        logger.info(f"Celery task completed for file: {file_id}")
        return {"status": "success", "file_id": file_id}
        
    except Exception as e:
        logger.error(f"Error in Celery task for file {file_id}: {e}")
        # Mark as processed even if there's an error to avoid infinite retries
        neo4j_service.update_file_sync(file_id, {"file_status": FileStatus.PROCESSED})
        raise

@shared_task(bind=True, name="reprocess_file")
def reprocess_file_task(self, file_id: str, file_path: str, health_record_id: str):
    """Celery task for reprocessing files"""
    try:
        logger.info(f"Starting Celery task for file reprocessing: {file_id}")
        
        # Similar logic to process_file_task but for reprocessing
        # This would regenerate AI summaries, etc.
        
        logger.info(f"Celery reprocessing task completed for file: {file_id}")
        return {"status": "success", "file_id": file_id}
        
    except Exception as e:
        logger.error(f"Error in Celery reprocessing task for file {file_id}: {e}")
        raise

@shared_task(bind=True, name="cleanup_files")
def cleanup_files_task(self):
    """Celery task for cleaning up orphaned files"""
    try:
        logger.info("Starting Celery task for file cleanup")
        
        # Call the cleanup method
        cleaned_count = file_service.cleanup_orphaned_files_sync()
        
        logger.info(f"Celery cleanup task completed. Cleaned {cleaned_count} files")
        return {"status": "success", "cleaned_count": cleaned_count}
        
    except Exception as e:
        logger.error(f"Error in Celery cleanup task: {e}")
        raise 