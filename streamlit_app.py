import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, date
import io
import base64
from typing import Dict, List, Optional, Any
import time

# Configuration
API_BASE_URL = "http://localhost:8000"

# Fixed user data
FIXED_PATIENT = {
    "email": "amansharma2910@gmail.com",
    "name": "Aman",
    "phone": "7023119860",
    "date_of_birth": "2000-10-29",
    "gender": "MALE",
    "address": "test",
    "id": "c0c78cb4-ae6f-4569-b1fd-78875e394b7c",
    "user_type": "PATIENT",
    "specialization": None,
    "license_number": None,
    "created_at": "2025-06-21T00:00:00",
    "updated_at": "2025-06-21T00:00:00"
}

FIXED_DOCTORS = [
    {
        "email": "john_doe@gmail.com",
        "name": "John Doe",
        "phone": "7023319862",
        "date_of_birth": "1971-10-29",
        "gender": "MALE",
        "address": "104, Utopia",
        "id": "ca3e0154-ae8b-435e-90d7-548ed56137ce",
        "user_type": "DOCTOR",
        "specialization": "Neurosurgeon",
        "license_number": "K32D23",
        "created_at": "2025-06-21T00:00:00",
        "updated_at": "2025-06-21T00:00:00"
    },
    {
        "email": "jane_jonah@gmail.com",
        "name": "Jane Jonah",
        "phone": "9023314362",
        "date_of_birth": "1993-04-12",
        "gender": "FEMALE",
        "address": "103, Utopia",
        "id": "bc9515fc-e35c-45f3-b40e-087f59ab2a46",
        "user_type": "DOCTOR",
        "specialization": "ENT",
        "license_number": "F52K13",
        "created_at": "2025-06-21T00:00:00",
        "updated_at": "2025-06-21T00:00:00"
    },
    {
        "email": "bruce_wayne@wayneenterprise.com",
        "name": "Bruce Wayne",
        "phone": "6023314362",
        "date_of_birth": "1986-01-23",
        "gender": "MALE",
        "address": "102, Utopia",
        "id": "dd72c738-b74f-4221-b60b-0028c82f16e9",
        "user_type": "DOCTOR",
        "specialization": "Cardiologist",
        "license_number": "FK8008",
        "created_at": "2025-06-21T00:00:00",
        "updated_at": "2025-06-21T00:00:00"
    }
]

# Page configuration
st.set_page_config(
    page_title="Medical Records Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
    .user-info {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class MedicalRecordsAPI:
    """API client for medical records operations"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        try:
            # Handle params separately for query parameters
            params = kwargs.pop('params', None)
            response = requests.request(method, url, params=params, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def create_health_record(self, health_record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new health record"""
        return self._make_request("POST", "/health-records", json=health_record_data)
    
    def get_health_record(self, health_record_id: str) -> Dict[str, Any]:
        """Get health record by ID"""
        return self._make_request("GET", f"/health-records/{health_record_id}")
    
    def list_health_records(self, **params) -> Dict[str, Any]:
        """List health records with optional filters"""
        query_params = "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
        endpoint = f"/health-records?{query_params}" if query_params else "/health-records"
        return self._make_request("GET", endpoint)
    
    def upload_file(self, health_record_id: str, file_data: bytes, filename: str, 
                   uploaded_by: str, description: str = None, category: str = "OTHER") -> Dict[str, Any]:
        """Upload file to health record"""
        files = {"file": (filename, file_data)}
        params = {
            "uploaded_by": uploaded_by,
            "description": description or "",
            "category": category
        }
        return self._make_request("POST", f"/health-records/{health_record_id}/files", 
                                files=files, params=params)
    
    def list_files(self, health_record_id: str, **params) -> Dict[str, Any]:
        """List files for health record"""
        query_params = "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
        endpoint = f"/health-records/{health_record_id}/files?{query_params}" if query_params else f"/health-records/{health_record_id}/files"
        return self._make_request("GET", endpoint)
    
    def get_file(self, file_id: str) -> Dict[str, Any]:
        """Get file details"""
        return self._make_request("GET", f"/files/{file_id}")
    
    def regenerate_file_summary(self, file_id: str, summary_type: str = "BOTH") -> Dict[str, Any]:
        """Regenerate file summary"""
        params = {"summary_type": summary_type}
        return self._make_request("POST", f"/files/{file_id}/regenerate-summary", params=params)
    
    def generate_health_record_summary(self, health_record_id: str, summary_type: str = "BOTH") -> Dict[str, Any]:
        """Generate comprehensive health record summary"""
        params = {"summary_type": summary_type}
        return self._make_request("POST", f"/health-records/{health_record_id}/generate-summary", params=params)
    
    def get_medicine_summary(self, medicine_name: str) -> Dict[str, Any]:
        """Get medicine summary"""
        return self._make_request("GET", f"/medicines/{medicine_name}/summary")
    
    def get_medicine_info(self, medicine_name: str) -> Dict[str, Any]:
        """Get detailed medicine information"""
        return self._make_request("GET", f"/medicines/{medicine_name}/info")
    
    def get_supported_languages(self) -> Dict[str, Any]:
        """Get list of supported languages for translation"""
        return self._make_request("GET", "/translation/languages")
    
    def translate_text(self, text: str, target_language: str, source_language: str = "auto") -> Dict[str, Any]:
        """Translate text to target language"""
        payload = {
            "text": text,
            "target_language": target_language,
            "source_language": source_language
        }
        return self._make_request("POST", "/translation/translate", json=payload)
    
    def translate_medical_summary(self, summary: str, target_language: str, summary_type: str = "LAYMAN") -> Dict[str, Any]:
        """Translate medical summary to target language"""
        payload = {
            "summary": summary,
            "target_language": target_language,
            "summary_type": summary_type
        }
        return self._make_request("POST", "/translation/translate-summary", json=payload)
    
    def translate_file_summary(self, file_id: str, target_language: str, summary_type: str = "LAYMAN") -> Dict[str, Any]:
        """Translate file summary to target language"""
        params = {
            "target_language": target_language,
            "summary_type": summary_type
        }
        return self._make_request("POST", f"/files/{file_id}/translate-summary", params=params)
    
    def translate_health_record_summary(self, health_record_id: str, target_language: str, summary_type: str = "LAYMAN") -> Dict[str, Any]:
        """Translate health record summary to target language"""
        params = {
            "target_language": target_language,
            "summary_type": summary_type
        }
        return self._make_request("POST", f"/health-records/{health_record_id}/translate-summary", params=params)

def initialize_session_state():
    """Initialize session state variables"""
    if "api_client" not in st.session_state:
        st.session_state.api_client = MedicalRecordsAPI(API_BASE_URL)
    
    if "selected_user" not in st.session_state:
        st.session_state.selected_user = FIXED_PATIENT
    
    if "selected_doctor" not in st.session_state:
        st.session_state.selected_doctor = FIXED_DOCTORS[0]
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"
    
    if "preferred_language" not in st.session_state:
        st.session_state.preferred_language = "en-IN"
    
    if "available_languages" not in st.session_state:
        st.session_state.available_languages = {}

def get_language_options():
    """Get language options for selection"""
    if not st.session_state.available_languages:
        try:
            result = st.session_state.api_client.get_supported_languages()
            if result.get("success"):
                st.session_state.available_languages = result.get("languages", {})
            else:
                # Fallback to default languages if API fails
                st.session_state.available_languages = {
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
        except Exception as e:
            st.error(f"Failed to load languages: {e}")
            # Fallback to default languages
            st.session_state.available_languages = {
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
    
    return st.session_state.available_languages

def show_language_selector():
    """Show language selection widget in sidebar"""
    st.sidebar.markdown("### 🌐 Language Preferences")
    
    languages = get_language_options()
    
    # Create options for selectbox
    language_options = [f"{name} ({code})" for code, name in languages.items()]
    language_codes = list(languages.keys())
    
    # Find current selection index
    current_index = language_codes.index(st.session_state.preferred_language) if st.session_state.preferred_language in language_codes else 0
    
    selected_option = st.sidebar.selectbox(
        "Select your preferred language:",
        language_options,
        index=current_index,
        help="Choose your preferred language for medical summaries and information"
    )
    
    # Extract language code from selection
    selected_code = language_codes[language_options.index(selected_option)]
    
    if selected_code != st.session_state.preferred_language:
        st.session_state.preferred_language = selected_code
        st.sidebar.success(f"Language changed to {languages[selected_code]}")

def translate_summary_if_needed(summary: str, target_language: str = None, summary_type: str = "LAYMAN") -> str:
    """Translate summary if target language is different from English"""
    if not summary:
        return summary
    
    if target_language is None:
        target_language = st.session_state.preferred_language
    
    # If target language is English, return original
    if target_language == "en-IN":
        return summary
    
    # Only translate layman summaries, not doctor summaries
    if summary_type == "DOCTOR":
        st.info("📋 Doctor summaries are shown in English to preserve medical accuracy")
        return summary
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/translation/translate-summary",
            json={
                "summary": summary,
                "target_language": target_language,
                "summary_type": summary_type
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                translated_text = result.get("translated_summary", summary)
                
                # Show info if text was summarized for translation
                if result.get("summarized_text"):
                    st.info("📝 Summary was condensed for translation to fit API limits")
                
                return translated_text
            else:
                error_msg = result.get('error', 'Unknown error')
                if "not translated" in error_msg.lower():
                    st.info("📋 " + error_msg)
                else:
                    st.warning(f"Translation failed: {error_msg}")
                return summary
        else:
            st.warning(f"Translation API error: {response.status_code}")
            return summary
            
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return summary

def display_user_info(user_data: Dict[str, Any], user_type: str):
    """Display user information in a formatted way"""
    st.markdown(f"<div class='user-info'>", unsafe_allow_html=True)
    st.markdown(f"**{user_type}:** {user_data['name']}")
    st.markdown(f"**Email:** {user_data['email']}")
    st.markdown(f"**Phone:** {user_data['phone']}")
    if user_data.get('specialization'):
        st.markdown(f"**Specialization:** {user_data['specialization']}")
    if user_data.get('license_number'):
        st.markdown(f"**License:** {user_data['license_number']}")
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    """Main application"""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🏥 Medical Records Management System</h1>', unsafe_allow_html=True)
    
    # Display current patient info in sidebar
    st.sidebar.markdown("### 👤 Current Patient")
    st.sidebar.markdown(f"**Name:** {FIXED_PATIENT['name']}")
    st.sidebar.markdown(f"**Email:** {FIXED_PATIENT['email']}")
    st.sidebar.markdown(f"**Phone:** {FIXED_PATIENT['phone']}")
    
    # Language selector
    show_language_selector()
    
    # Show current language preference
    languages = get_language_options()
    current_language_name = languages.get(st.session_state.preferred_language, "English")
    st.sidebar.markdown(f"**Current Language:** {current_language_name}")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Dashboard", "Create Medical Record", "Upload Files", "View Records", "Medicine Search", "File Management"]
    )
    
    # Page routing
    if page == "Dashboard":
        show_dashboard()
    elif page == "Create Medical Record":
        show_create_medical_record()
    elif page == "Upload Files":
        show_upload_files()
    elif page == "View Records":
        show_view_records()
    elif page == "Medicine Search":
        show_medicine_search()
    elif page == "File Management":
        show_file_management()

def show_dashboard():
    """AI Chat Dashboard"""
    st.markdown('<h2 class="section-header">🤖 AI Medical Assistant Chat</h2>', unsafe_allow_html=True)
    
    # Initialize chat history if not exists
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat interface layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Chat display area
        st.markdown("### 💬 Chat with AI Assistant")
        
        # Create chat container with custom styling
        chat_container = st.container()
        
        with chat_container:
            if not st.session_state.chat_history:
                st.markdown("""
                <div style="background-color: #fff3cd; color: #856404; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;">
                    👋 <strong>Welcome to your AI Medical Assistant!</strong><br><br>
                    I can help you with:<br>
                    • Viewing your medical history and records<br>
                    • Finding specific health information<br>
                    • Getting medication details<br>
                    • Generating health summaries<br>
                    • Answering questions about your health data<br><br>
                    Choose an example query from the sidebar or type your own question below!
                </div>
                """, unsafe_allow_html=True)
            
            # Display chat messages
            for i, entry in enumerate(st.session_state.chat_history):
                timestamp_str = entry["timestamp"].strftime("%H:%M")
                
                if entry["is_user"]:
                    st.markdown(f"""
                    <div style="background-color: #007bff; color: white; padding: 0.8rem 1rem; 
                         border-radius: 18px 18px 4px 18px; margin: 0.5rem 0 0.5rem auto; 
                         max-width: 70%; word-wrap: break-word;">
                        {entry["message"]}
                        <div style="font-size: 0.7rem; color: #e0e0e0; margin-top: 0.3rem;">
                            You • {timestamp_str}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Format assistant response with metadata
                    response_text = entry["message"]
                    metadata = entry.get("metadata", {})
                    
                    # Add confidence and sources if available
                    if metadata.get("confidence") is not None:
                        confidence_percent = int(metadata["confidence"] * 100)
                        confidence_emoji = "🟢" if confidence_percent >= 80 else "🟡" if confidence_percent >= 60 else "🔴"
                        response_text += f"<br><br>{confidence_emoji} <strong>Confidence:</strong> {confidence_percent}%"
                    
                    if metadata.get("sources"):
                        sources_text = ", ".join(metadata["sources"])
                        response_text += f"<br>📚 <strong>Sources:</strong> {sources_text}"
                    
                    if metadata.get("suggested_actions"):
                        actions_text = " • ".join(metadata["suggested_actions"])
                        response_text += f"<br>💡 <strong>Suggested:</strong> {actions_text}"
                    
                    # Add language indicator if not English
                    if st.session_state.get("preferred_language", "en-IN") != "en-IN":
                        languages = get_language_options()
                        lang_name = languages.get(st.session_state.preferred_language, "Unknown")
                        response_text += f"<br>🌐 <strong>Language:</strong> {lang_name}"
                    
                    st.markdown(f"""
                    <div style="background-color: #e9ecef; color: #333; padding: 0.8rem 1rem; 
                         border-radius: 18px 18px 18px 4px; margin: 0.5rem auto 0.5rem 0; 
                         max-width: 85%; word-wrap: break-word;">
                        {response_text}
                        <div style="font-size: 0.7rem; color: #6c757d; margin-top: 0.3rem;">
                            AI Assistant • {timestamp_str}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Chat input form
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Ask me anything about your medical records:",
                placeholder="Type your question here... (e.g., 'What's my latest prescription?' or 'Show me my blood test results')",
                height=100,
                key="user_input"
            )
            
            col_submit, col_clear = st.columns([3, 1])
            with col_submit:
                submitted = st.form_submit_button("Send Message", use_container_width=True)
            with col_clear:
                if st.form_submit_button("🗑️ Clear Chat"):
                    st.session_state.chat_history = []
                    st.rerun()
        
        # Handle form submission
        if submitted and user_input.strip():
            # Add user message to chat
            add_message_to_chat(user_input.strip(), is_user=True)
            
            # Show loading indicator
            with st.spinner("🤖 AI is analyzing your request..."):
                # Query the orchestrator
                result = query_orchestrator(user_input.strip())
                
                # Add assistant response to chat
                metadata = {
                    "confidence": result.get("confidence"),
                    "sources": result.get("sources"),
                    "suggested_actions": result.get("suggested_actions")
                }
                add_message_to_chat(result.get("response", "I couldn't process your request right now."), 
                                  is_user=False, metadata=metadata)
            
            st.rerun()
    
    with col2:
        # Example queries sidebar
        st.markdown("### 💡 Example Queries")
        
        example_queries = get_dashboard_example_queries()
        
        for category, queries in example_queries.items():
            with st.expander(category, expanded=False):
                for query in queries:
                    if st.button(query, key=f"example_{hash(query)}", help="Click to use this query"):
                        # Add user message
                        add_message_to_chat(query, is_user=True)
                        
                        # Show loading message
                        with st.spinner("AI is thinking..."):
                            # Query orchestrator
                            result = query_orchestrator(query)
                            
                            # Add assistant response
                            metadata = {
                                "confidence": result.get("confidence"),
                                "sources": result.get("sources"),
                                "suggested_actions": result.get("suggested_actions")
                            }
                            add_message_to_chat(result.get("response", "No response received"), 
                                              is_user=False, metadata=metadata)
                        
                        st.rerun()
        
        # Quick stats
        st.markdown("### 📊 Quick Stats")
        try:
            # Get health records count
            health_records_response = requests.get(
                f"{API_BASE_URL}/health-records",
                params={"patient_id": FIXED_PATIENT["id"], "limit": 1}
            )
            if health_records_response.status_code == 200:
                total_records = health_records_response.json().get("total", 0)
                st.metric("Health Records", total_records)
            else:
                st.metric("Health Records", "N/A")
        except:
            st.metric("Health Records", "Error")
        
        # Chat stats
        total_messages = len(st.session_state.chat_history)
        user_messages = len([msg for msg in st.session_state.chat_history if msg["is_user"]])
        st.metric("Chat Messages", f"{user_messages}/{total_messages}")
        
        # System status
        st.markdown("### 🚀 System Status")
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=3)
            if response.status_code == 200:
                st.success("✅ Backend Connected")
            else:
                st.error("❌ Backend Issues")
        except:
            st.error("❌ Backend Offline")
        
        try:
            response = requests.get(f"{API_BASE_URL}/api/v1/orchestrator/status", timeout=3)
            if response.status_code == 200:
                status_data = response.json()
                if status_data.get("status") == "healthy":
                    st.success("🤖 AI Assistant Ready")
                    st.caption(f"Tools: {status_data.get('available_tools', 'N/A')}")
                else:
                    st.warning("⚠️ AI Assistant Issues")
            else:
                st.error("❌ AI Assistant Offline")
        except:
            st.error("❌ AI Assistant Unreachable")
        
        # Language Settings
        st.markdown("### 🌐 Language Settings")
        languages = get_language_options()
        current_language_name = languages.get(st.session_state.preferred_language, "English")
        
        st.info(f"**Current Language:** {current_language_name}")
        st.caption("ℹ️ Summaries will be generated in your preferred language. Change language in the sidebar.")
        
        # Pro tips
        st.markdown("### 💡 Pro Tips")
        st.info("""
        **Get better responses:**
        • Be specific about what you want to know
        • Mention time periods (e.g., "last month")
        • Ask follow-up questions for details
        • Use medical terms if you know them
        • Summaries are automatically translated to your preferred language
        """)

def add_message_to_chat(message: str, is_user: bool, metadata: dict = None):
    """Add a message to chat history"""
    chat_entry = {
        "message": message,
        "is_user": is_user,
        "timestamp": datetime.now(),
        "metadata": metadata or {}
    }
    st.session_state.chat_history.append(chat_entry)

def query_orchestrator(user_query: str) -> dict:
    """Send query to orchestrator agent"""
    try:
        # Get user's preferred language from session state
        preferred_language = st.session_state.get("preferred_language", "en-IN")
        
        payload = {
            "query": user_query,
            "user_id": FIXED_PATIENT["id"],
            "user_type": FIXED_PATIENT["user_type"],
            "health_record_id": None,  # Optional
            "preferred_language": preferred_language
        }
        
        response = requests.post(f"{API_BASE_URL}/api/v1/orchestrator/query", json=payload)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        return {
            "response": f"❌ **Connection Error**\n\nCouldn't connect to the AI assistant. Please make sure the backend server is running.\n\nError: {str(e)}",
            "confidence": 0.0,
            "sources": [],
            "suggested_actions": ["Check server connection", "Try again later"],
            "cypher_queries_executed": []
        }

def get_dashboard_example_queries() -> dict:
    """Get example queries organized by category"""
    return {
        "📋 Medical History": [
            "Give me my complete medical history report",
            "Show me all my health records",
            "Generate a comprehensive medical timeline",
            "What's my medical background summary?"
        ],
        "💊 Medications & Prescriptions": [
            "What's my latest prescription?",
            "Show me my current medications",
            "What medications am I taking?",
            "Get my most recent medicine prescription"
        ],
        "🔍 Search & Find": [
            "Search for diabetes-related records",
            "Find all records about my heart condition",
            "Look for my blood test results",
            "Search for appointment records from last month"
        ],
        "📝 Summaries & Reports": [
            "Generate a summary of my health record",
            "Give me an overview of my medical condition",
            "Summarize my latest health checkup",
            "Create a summary of my treatment plan"
        ],
        "🩺 Specific Health Questions": [
            "What were my blood pressure readings?",
            "Show me my vaccination records",
            "What was my last diagnosis?",
            "When was my last appointment?",
            "What are my allergies?",
            "Show me my lab test results"
        ]
    }

def show_create_medical_record():
    """Create medical record page"""
    st.markdown('<h2 class="section-header">📝 Create Medical Record</h2>', unsafe_allow_html=True)
    
    # Display patient info (read-only)
    st.subheader("Patient Information")
    display_user_info(FIXED_PATIENT, "Patient")
    
    with st.form("create_health_record"):
        st.subheader("Select Doctor")
        doctor_options = {f"{doc['name']} - {doc['specialization']}": doc for doc in FIXED_DOCTORS}
        selected_doctor_name = st.selectbox("Choose a doctor:", list(doctor_options.keys()))
        selected_doctor = doctor_options[selected_doctor_name]
        
        # Display selected doctor info
        st.markdown("**Selected Doctor:**")
        display_user_info(selected_doctor, "Doctor")
        
        st.subheader("Medical Record Details")
        title = st.text_input("Record Title")
        ailment = st.text_area("Ailment/Diagnosis")
        layman_summary = st.text_area("Initial Layman Summary (Optional)")
        medical_summary = st.text_area("Initial Medical Summary (Optional)")
        
        submitted = st.form_submit_button("Create Medical Record")
        
        if submitted:
            if not all([title, ailment]):
                st.error("Please fill in all required fields")
                return
            
            # Create health record with fixed patient and selected doctor
            health_record_data = {
                "title": title,
                "ailment": ailment,
                "patient_id": FIXED_PATIENT["id"],
                "doctor_id": selected_doctor["id"],
                "layman_summary": layman_summary or None,
                "medical_summary": medical_summary or None
            }
            
            result = st.session_state.api_client.create_health_record(health_record_data)
            
            if result.get("success"):
                st.success("Medical record created successfully!")
                st.json(result["data"])
            else:
                st.error(f"Failed to create medical record: {result.get('error', 'Unknown error')}")

def show_upload_files():
    """Upload files page"""
    st.markdown('<h2 class="section-header">📁 Upload Files</h2>', unsafe_allow_html=True)
    
    # Display patient info
    st.subheader("Patient Information")
    display_user_info(FIXED_PATIENT, "Patient")
    
    # Select health record
    st.subheader("Select Medical Record")
    
    # Get list of health records for the fixed patient
    records_result = st.session_state.api_client.list_health_records(patient_id=FIXED_PATIENT["id"])
    
    if not records_result.get("success"):
        st.error("Failed to load health records")
        return
    
    records = records_result.get("data", [])
    
    if not records:
        st.warning("No medical records found for this patient. Please create a medical record first.")
        return
    
    # Display records with summaries in a more user-friendly format
    st.markdown("**Available Medical Records:**")
    
    # Create tabs for each record
    if len(records) == 1:
        # If only one record, show it directly
        selected_record = records[0]
        selected_record_id = selected_record["id"]
        
        # Display record details
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Record:** {selected_record['title']}")
            st.markdown(f"**Ailment:** {selected_record['ailment']}")
            st.markdown(f"**Status:** {selected_record['status']}")
            st.markdown(f"**Created:** {selected_record['created_at'][:10] if selected_record['created_at'] else 'N/A'}")
        
        with col2:
            if selected_record.get("doctor"):
                st.markdown(f"**Doctor:** {selected_record['doctor']['name']}")
                st.markdown(f"**Specialization:** {selected_record['doctor']['specialization']}")
        
        # Show layman summary if available
        if selected_record.get("layman_summary"):
            st.markdown("**Layman Summary:**")
            translated_summary = translate_summary_if_needed(selected_record["layman_summary"])
            st.info(translated_summary)
        else:
            st.info("No layman summary available for this record.")
        
    else:
        # If multiple records, create tabs
        tab_names = [f"{r['title']} - {r['ailment']}" for r in records]
        tabs = st.tabs(tab_names)
        
        selected_record_id = None
        
        for i, (tab, record) in enumerate(zip(tabs, records)):
            with tab:
                # Display record details
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Record:** {record['title']}")
                    st.markdown(f"**Ailment:** {record['ailment']}")
                    st.markdown(f"**Status:** {record['status']}")
                    st.markdown(f"**Created:** {record['created_at'][:10] if record['created_at'] else 'N/A'}")
                
                with col2:
                    if record.get("doctor"):
                        st.markdown(f"**Doctor:** {record['doctor']['name']}")
                        st.markdown(f"**Specialization:** {record['doctor']['specialization']}")
                
                                # Show layman summary if available
                if record.get("layman_summary"):
                    st.markdown("**Layman Summary:**")
                    translated_summary = translate_summary_if_needed(record["layman_summary"])
                    st.info(translated_summary)
                else:
                    st.info("No layman summary available for this record.")
                
                # Add a select button for this record
                if st.button(f"Select this record", key=f"select_{i}"):
                    selected_record_id = record["id"]
                    st.session_state.selected_health_record = selected_record_id
                    st.success(f"Selected: {record['title']}")
        
        # If no record selected yet, show a dropdown as fallback
        if not selected_record_id:
            st.markdown("**Or select from dropdown:**")
            record_options = {f"{r['title']} - {r['ailment']}": r['id'] for r in records}
            selected_record_name = st.selectbox("Choose a medical record:", list(record_options.keys()))
            selected_record_id = record_options[selected_record_name]
    
    st.session_state.selected_health_record = selected_record_id
    
    # File upload section
    st.subheader("Upload File")
    
    uploaded_file = st.file_uploader(
        "Choose a file to upload",
        type=['pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png'],
        help="Supported formats: PDF, DOCX, TXT, JPG, JPEG, PNG"
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            description = st.text_input("File Description (Optional)")
            category = st.selectbox(
                "File Category",
                ["OTHER", "LAB_REPORT", "IMAGING", "PRESCRIPTION", "APPOINTMENT", "MEDICAL_NOTE"]
            )
        
        with col2:
            # Pre-fill with patient ID
            uploaded_by = st.text_input("Uploaded By (User ID)", value=FIXED_PATIENT["id"], disabled=True)
        
        if st.button("Upload File"):
            with st.spinner("Uploading file..."):
                file_data = uploaded_file.read()
                
                result = st.session_state.api_client.upload_file(
                    health_record_id=selected_record_id,
                    file_data=file_data,
                    filename=uploaded_file.name,
                    uploaded_by=FIXED_PATIENT["id"],
                    description=description,
                    category=category
                )
                
                if result.get("success"):
                    st.success("File uploaded successfully! AI processing has started.")
                    st.json(result["data"])
                else:
                    st.error(f"Failed to upload file: {result.get('error', 'Unknown error')}")

def show_view_records():
    """View records page"""
    st.markdown('<h2 class="section-header">📋 View Medical Records</h2>', unsafe_allow_html=True)
    
    # Display patient info
    st.subheader("Patient Information")
    display_user_info(FIXED_PATIENT, "Patient")
    
    # Get list of health records for the fixed patient
    records_result = st.session_state.api_client.list_health_records(patient_id=FIXED_PATIENT["id"])
    
    if not records_result.get("success"):
        st.error("Failed to load health records")
        return
    
    records = records_result.get("data", [])
    
    if not records:
        st.warning("No medical records found for this patient.")
        return
    
    # Display records in a table
    st.subheader("Medical Records")
    
    # Create a DataFrame for better display
    records_data = []
    for record in records:
        records_data.append({
            "ID": record["id"],
            "Title": record["title"],
            "Ailment": record["ailment"],
            "Status": record["status"],
            "Created": record["created_at"][:10] if record["created_at"] else "N/A",
            "Patient": record["patient"]["name"] if record.get("patient") else "N/A",
            "Doctor": record["doctor"]["name"] if record.get("doctor") else "N/A"
        })
    
    df = pd.DataFrame(records_data)
    st.dataframe(df, use_container_width=True)
    
    # Select a record to view details
    st.subheader("View Record Details")
    
    # Create dropdown with record names instead of IDs
    record_options = {f"{r['title']} - {r['ailment']}": r for r in records}
    selected_record_name = st.selectbox("Select a record to view:", list(record_options.keys()))
    selected_record = record_options[selected_record_name]
    selected_record_id = selected_record["id"]
    
    if selected_record_id:
        record_result = st.session_state.api_client.get_health_record(selected_record_id)
        
        if record_result.get("success"):
            record = record_result["data"]
            
            # Display record details
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Record Information**")
                st.write(f"**Title:** {record['title']}")
                st.write(f"**Ailment:** {record['ailment']}")
                st.write(f"**Status:** {record['status']}")
                st.write(f"**Created:** {record['created_at']}")
                st.write(f"**Last Updated:** {record['updated_at']}")
            
            with col2:
                st.markdown("**Patient Information**")
                if record.get("patient"):
                    display_user_info(record["patient"], "Patient")
                
                st.markdown("**Doctor Information**")
                if record.get("doctor"):
                    display_user_info(record["doctor"], "Doctor")
            
            # Summaries section
            st.subheader("Summaries")
            
            # Language selection for summaries
            languages = get_language_options()
            summary_language = st.selectbox(
                "Select language for summaries:",
                options=list(languages.keys()),
                format_func=lambda x: languages[x],
                index=list(languages.keys()).index(st.session_state.preferred_language)
            )
            
            # Summary type selector
            summary_type = st.selectbox(
                "Select summary type to view:",
                options=["LAYMAN", "DOCTOR"],
                format_func=lambda x: "Patient-Friendly Summary" if x == "LAYMAN" else "Medical Summary",
                key="record_summary_type"
            )
            
            # Display selected summary
            st.markdown(f"**{summary_type.title()} Summary**")
            
            if summary_type == "LAYMAN":
                if record.get("layman_summary"):
                    # Translate if needed
                    translated_summary = translate_summary_if_needed(
                        record["layman_summary"], 
                        summary_language, 
                        "LAYMAN"
                    )
                    st.markdown(translated_summary)
                    
                    # Show translation status
                    if summary_language != "en-IN":
                        st.info(f"Translated to {languages[summary_language]}")
                else:
                    st.info("No layman summary available")
            else:  # DOCTOR
                if record.get("medical_summary"):
                    # Translate if needed (will show English for doctor summaries)
                    translated_summary = translate_summary_if_needed(
                        record["medical_summary"], 
                        summary_language, 
                        "DOCTOR"
                    )
                    st.markdown(translated_summary)
                    
                    # Show translation status
                    if summary_language != "en-IN":
                        st.info(f"Translated to {languages[summary_language]}")
                else:
                    st.info("No doctor summary available")
            
            # Translation controls
            if summary_language != "en-IN":
                st.markdown("**Translation Controls**")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔄 Refresh Translation"):
                        with st.spinner("Refreshing translation..."):
                            st.rerun()
                
                with col2:
                    if st.button("📋 Copy Translated Text"):
                        # This would copy the translated text to clipboard
                        st.success("Translation copied to clipboard!")
            
            # Generate/Update summaries
            st.subheader("Generate/Update Summaries")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Generate Layman Summary"):
                    with st.spinner("Generating layman summary..."):
                        result = st.session_state.api_client.generate_health_record_summary(
                            selected_record_id, "LAYMAN"
                        )
                        if result.get("layman_summary"):
                            st.success("Layman summary generated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to generate summary")
            
            with col2:
                if st.button("Generate Medical Summary"):
                    with st.spinner("Generating medical summary..."):
                        result = st.session_state.api_client.generate_health_record_summary(
                            selected_record_id, "DOCTOR"
                        )
                        if result.get("doctor_summary"):
                            st.success("Medical summary generated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to generate summary")
            
            with col3:
                if st.button("Generate Both Summaries"):
                    with st.spinner("Generating both summaries..."):
                        result = st.session_state.api_client.generate_health_record_summary(
                            selected_record_id, "BOTH"
                        )
                        if result.get("layman_summary") or result.get("doctor_summary"):
                            st.success("Both summaries generated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to generate summaries")
            
            # Files section
            st.subheader("Files")
            
            files_result = st.session_state.api_client.list_files(selected_record_id)
            
            if files_result.get("success"):
                files = files_result.get("data", [])
                
                if files:
                    # Create a DataFrame for files
                    files_data = []
                    for file in files:
                        files_data.append({
                            "ID": file["id"],
                            "Filename": file["filename"],
                            "Category": file["category"],
                            "Status": file["file_status"],
                            "Uploaded": file["created_at"][:10] if file["created_at"] else "N/A",
                            "Size": f"{file['file_size']} bytes" if file.get("file_size") else "N/A"
                        })
                    
                    files_df = pd.DataFrame(files_data)
                    st.dataframe(files_df, use_container_width=True)
                else:
                    st.info("No files uploaded for this record yet.")
            else:
                st.error("Failed to load files")
        else:
            st.error(f"Failed to get record details: {record_result.get('error', 'Unknown error')}")

def show_medicine_search():
    """Medicine search page"""
    st.markdown('<h2 class="section-header">💊 Medicine Information Search</h2>', unsafe_allow_html=True)
    
    # Display patient info
    st.subheader("Patient Information")
    display_user_info(FIXED_PATIENT, "Patient")
    
    # Search interface
    st.subheader("Search Medicine Information")
    
    medicine_name = st.text_input("Enter medicine name:", placeholder="e.g., Aspirin, Paracetamol, Ibuprofen")
    
    # Language selection for medicine information
    languages = get_language_options()
    medicine_language = st.selectbox(
        "Select language for medicine information:",
        options=list(languages.keys()),
        format_func=lambda x: languages[x],
        index=list(languages.keys()).index(st.session_state.preferred_language)
    )
    
    if st.button("Get Summary"):
        if medicine_name:
            with st.spinner("Searching for medicine information..."):
                result = st.session_state.api_client.get_medicine_summary(medicine_name)
                
                if result.get("success"):
                    st.success("Medicine information retrieved successfully!")
                    
                    st.markdown("**Summary**")
                    # Translate medicine summary if needed
                    translated_summary = translate_summary_if_needed(result["summary"], medicine_language)
                    st.markdown(translated_summary)
                    
                    # Show translation status
                    if medicine_language != "en-IN":
                        st.info(f"Translated to {languages[medicine_language]}")
                    
                    st.markdown(f"**Source:** {result.get('source', 'Unknown')}")
                    
                    # Translation controls
                    if medicine_language != "en-IN":
                        st.markdown("**Translation Controls**")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("🔄 Refresh Translation", key="refresh_medicine"):
                                with st.spinner("Refreshing translation..."):
                                    st.rerun()
                        
                        with col2:
                            if st.button("📋 Copy Translated Text", key="copy_medicine"):
                                st.success("Translation copied to clipboard!")
                else:
                    st.error(f"Failed to get medicine information: {result.get('error', 'Unknown error')}")
        else:
            st.warning("Please enter a medicine name")
    
    # Example searches
    st.subheader("Example Searches")
    st.markdown("""
    Try searching for these common medicines:
    - **Aspirin** - Pain relief and blood thinning
    - **Paracetamol** - Fever and pain relief
    - **Ibuprofen** - Anti-inflammatory pain relief
    - **Omeprazole** - Acid reflux medication
    - **Metformin** - Diabetes medication
    """)

def show_file_management():
    """File management page"""
    st.markdown('<h2 class="section-header">📄 File Management</h2>', unsafe_allow_html=True)
    
    # Display patient info
    st.subheader("Patient Information")
    display_user_info(FIXED_PATIENT, "Patient")
    
    # Select health record
    st.subheader("Select Medical Record")
    
    records_result = st.session_state.api_client.list_health_records(patient_id=FIXED_PATIENT["id"])
    
    if not records_result.get("success"):
        st.error("Failed to load health records")
        return
    
    records = records_result.get("data", [])
    
    if not records:
        st.warning("No medical records found for this patient.")
        return
    
    record_options = {f"{r['title']} - {r['ailment']}": r['id'] for r in records}
    selected_record_name = st.selectbox("Choose a medical record:", list(record_options.keys()))
    selected_record_id = record_options[selected_record_name]
    
    # Get files for selected record
    files_result = st.session_state.api_client.list_files(selected_record_id)
    
    if not files_result.get("success"):
        st.error("Failed to load files")
        return
    
    files = files_result.get("data", [])
    
    if not files:
        st.warning("No files found for this record.")
        return
    
    # Display files
    st.subheader("Files")
    
    # Create a DataFrame for files
    files_data = []
    for file in files:
        files_data.append({
            "ID": file["id"],
            "Filename": file["filename"],
            "Category": file["category"],
            "Status": file["file_status"],
            "Uploaded": file["created_at"][:10] if file["created_at"] else "N/A",
            "Size": f"{file['file_size']} bytes" if file.get("file_size") else "N/A"
        })
    
    files_df = pd.DataFrame(files_data)
    st.dataframe(files_df, use_container_width=True)
    
    # Select file to view details
    st.subheader("File Details")
    selected_file_id = st.selectbox("Select a file to view:", [f["id"] for f in files])
    
    if selected_file_id:
        file_result = st.session_state.api_client.get_file(selected_file_id)
        
        if file_result.get("success"):
            file = file_result["data"]
            
            # Display file details
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**File Information**")
                st.write(f"**Filename:** {file['filename']}")
                st.write(f"**Category:** {file['category']}")
                st.write(f"**Status:** {file['file_status']}")
                st.write(f"**Uploaded:** {file['created_at']}")
                st.write(f"**Size:** {file.get('file_size', 'N/A')} bytes")
                
                if file.get("description"):
                    st.write(f"**Description:** {file['description']}")
            
            with col2:
                st.markdown("**Uploader Information**")
                if file.get("uploaded_by_name"):
                    st.write(f"**Uploaded by:** {file['uploaded_by_name']}")
                else:
                    st.write(f"**Uploaded by:** {file.get('uploaded_by', 'Unknown')}")
            
            # File summaries
            st.subheader("File Summaries")
            
            # Language selection for file summaries
            languages = get_language_options()
            file_summary_language = st.selectbox(
                "Select language for file summaries:",
                options=list(languages.keys()),
                format_func=lambda x: languages[x],
                index=list(languages.keys()).index(st.session_state.preferred_language),
                key="file_summary_language"
            )
            
            # Summary type selector
            summary_type = st.selectbox(
                "Select summary type to view:",
                options=["LAYMAN", "DOCTOR"],
                format_func=lambda x: "Patient-Friendly Summary" if x == "LAYMAN" else "Medical Summary",
                key="file_summary_type"
            )
            
            # Display selected summary
            st.markdown(f"**{summary_type.title()} Summary**")
            
            if summary_type == "LAYMAN":
                if file.get("layman_summary"):
                    # Translate if needed
                    translated_summary = translate_summary_if_needed(
                        file["layman_summary"], 
                        file_summary_language, 
                        "LAYMAN"
                    )
                    st.markdown(translated_summary)
                    
                    # Show translation status
                    if file_summary_language != "en-IN":
                        st.info(f"Translated to {languages[file_summary_language]}")
                else:
                    st.info("No layman summary available")
            else:  # DOCTOR
                if file.get("doctor_summary"):
                    # Translate if needed (will show English for doctor summaries)
                    translated_summary = translate_summary_if_needed(
                        file["doctor_summary"], 
                        file_summary_language, 
                        "DOCTOR"
                    )
                    st.markdown(translated_summary)
                    
                    # Show translation status
                    if file_summary_language != "en-IN":
                        st.info(f"Translated to {languages[file_summary_language]}")
                else:
                    st.info("No doctor summary available")
            
            # Translation controls for file summaries
            if file_summary_language != "en-IN":
                st.markdown("**Translation Controls**")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔄 Refresh Translation", key="refresh_file"):
                        with st.spinner("Refreshing translation..."):
                            st.rerun()
                
                with col2:
                    if st.button("📋 Copy Translated Text", key="copy_file"):
                        st.success("Translation copied to clipboard!")
            
            # Regenerate summaries
            st.subheader("Regenerate File Summaries")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Regenerate Layman Summary"):
                    with st.spinner("Regenerating layman summary..."):
                        result = st.session_state.api_client.regenerate_file_summary(
                            selected_file_id, "LAYMAN"
                        )
                        st.write("Raw API response:", result)  # Debug output
                        if result.get("success") or result.get("layman_summary"):
                            st.success("Layman summary regenerated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to regenerate summary")
            
            with col2:
                if st.button("Regenerate Doctor Summary"):
                    with st.spinner("Regenerating doctor summary..."):
                        result = st.session_state.api_client.regenerate_file_summary(
                            selected_file_id, "DOCTOR"
                        )
                        st.write("Raw API response:", result)  # Debug output
                        if result.get("success") or result.get("doctor_summary"):
                            st.success("Doctor summary regenerated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to regenerate summary")
            
            with col3:
                if st.button("Regenerate Both Summaries"):
                    with st.spinner("Regenerating both summaries..."):
                        result = st.session_state.api_client.regenerate_file_summary(
                            selected_file_id, "BOTH"
                        )
                        st.write("Raw API response:", result)  # Debug output
                        if result.get("success") or (result.get("layman_summary") or result.get("doctor_summary")):
                            st.success("Both summaries regenerated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to regenerate summaries")

if __name__ == "__main__":
    main() 