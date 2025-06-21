import uuid
import hashlib
import re
from typing import Optional, Dict, Any, List
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

def generate_uuid() -> str:
    """Generate a unique identifier"""
    return str(uuid.uuid4())

def generate_share_token() -> str:
    """Generate a unique share token for health records"""
    return str(uuid.uuid4())

def generate_file_hash(content: bytes) -> str:
    """Generate MD5 hash for file content"""
    return hashlib.md5(content).hexdigest()

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        sanitized = name[:255-len(ext)-1] + ('.' + ext if ext else '')
    return sanitized

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    # Check if it's a reasonable length (7-15 digits)
    return 7 <= len(digits_only) <= 15

def format_phone(phone: str) -> str:
    """Format phone number for display"""
    digits_only = re.sub(r'\D', '', phone)
    if len(digits_only) == 10:
        return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
    elif len(digits_only) == 11 and digits_only[0] == '1':
        return f"+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
    else:
        return phone

def calculate_age(birth_date: date) -> int:
    """Calculate age from birth date"""
    today = date.today()
    age = today.year - birth_date.year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    return age

def format_duration_minutes(minutes: int) -> str:
    """Format duration in minutes to human readable string"""
    if minutes < 60:
        return f"{minutes} minutes"
    else:
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            return f"{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text"""
    # Simple keyword extraction - in production, use NLP libraries
    words = re.findall(r'\b\w+\b', text.lower())
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'}
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Count frequency and return most common
    from collections import Counter
    keyword_counts = Counter(keywords)
    return [keyword for keyword, count in keyword_counts.most_common(max_keywords)]

def calculate_relevance_score(query: str, content: str) -> float:
    """Calculate relevance score between query and content"""
    query_keywords = set(extract_keywords(query.lower()))
    content_keywords = set(extract_keywords(content.lower()))
    
    if not query_keywords:
        return 0.0
    
    intersection = query_keywords.intersection(content_keywords)
    union = query_keywords.union(content_keywords)
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return filename.split('.')[-1].lower() if '.' in filename else ''

def is_safe_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Check if file type is allowed"""
    extension = get_file_extension(filename).upper()
    return extension in allowed_types

def generate_search_snippet(text: str, query: str, max_length: int = 200) -> str:
    """Generate search snippet highlighting query terms"""
    if not query or not text:
        return truncate_text(text, max_length)
    
    # Find the first occurrence of any query word
    query_words = query.lower().split()
    text_lower = text.lower()
    
    best_position = -1
    for word in query_words:
        pos = text_lower.find(word)
        if pos != -1 and (best_position == -1 or pos < best_position):
            best_position = pos
    
    if best_position == -1:
        return truncate_text(text, max_length)
    
    # Extract snippet around the found position
    start = max(0, best_position - max_length // 2)
    end = min(len(text), start + max_length)
    
    snippet = text[start:end]
    
    # Add ellipsis if needed
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    
    return snippet

def validate_date_range(start_date: date, end_date: date) -> bool:
    """Validate that start date is before end date"""
    return start_date <= end_date

def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string"""
    return dt.strftime(format_str)

def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """Parse datetime from string"""
    try:
        return datetime.strptime(date_str, format_str)
    except ValueError:
        return None

def mask_sensitive_data(text: str, data_type: str = "email") -> str:
    """Mask sensitive data for logging"""
    if data_type == "email":
        # Mask email: john.doe@example.com -> j***.d***@example.com
        if '@' in text:
            username, domain = text.split('@', 1)
            masked_username = username[0] + '*' * (len(username) - 1)
            return f"{masked_username}@{domain}"
    elif data_type == "phone":
        # Mask phone: (555) 123-4567 -> (555) ***-****
        digits = re.sub(r'\D', '', text)
        if len(digits) >= 10:
            return f"({digits[:3]}) ***-****"
    elif data_type == "ssn":
        # Mask SSN: 123-45-6789 -> ***-**-6789
        digits = re.sub(r'\D', '', text)
        if len(digits) == 9:
            return f"***-**-{digits[-4:]}"
    
    return text

def create_pagination_metadata(total: int, skip: int, limit: int) -> Dict[str, Any]:
    """Create pagination metadata"""
    total_pages = (total + limit - 1) // limit
    current_page = (skip // limit) + 1
    
    return {
        "total": total,
        "page": current_page,
        "pages": total_pages,
        "skip": skip,
        "limit": limit,
        "has_next": skip + limit < total,
        "has_prev": skip > 0
    }

def validate_uuid(uuid_str: str) -> bool:
    """Validate UUID format"""
    try:
        uuid.UUID(uuid_str)
        return True
    except ValueError:
        return False

def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    import secrets
    return secrets.token_urlsafe(length)

def clean_html_tags(text: str) -> str:
    """Remove HTML tags from text"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def normalize_text(text: str) -> str:
    """Normalize text for consistent processing"""
    # Convert to lowercase
    text = text.lower()
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep alphanumeric and spaces
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()

def calculate_medication_compliance(medications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate medication compliance statistics"""
    if not medications:
        return {
            "total_medications": 0,
            "active_medications": 0,
            "compliance_rate": 0.0,
            "overdue_medications": 0
        }
    
    total = len(medications)
    active = sum(1 for med in medications if med.get("status") in ["ACTIVE", "APPROVED"])
    
    # Calculate compliance rate (placeholder logic)
    compliance_rate = 0.85  # This would be calculated based on actual compliance data
    
    # Count overdue medications
    today = date.today()
    overdue = sum(1 for med in medications 
                  if med.get("end_date") and parse_datetime(med["end_date"], "%Y-%m-%d") and 
                  parse_datetime(med["end_date"], "%Y-%m-%d").date() < today)
    
    return {
        "total_medications": total,
        "active_medications": active,
        "compliance_rate": compliance_rate,
        "overdue_medications": overdue
    } 