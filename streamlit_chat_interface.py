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

# Page configuration
st.set_page_config(
    page_title="AI Medical Assistant - Chat Interface",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for chat interface
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        max-height: 600px;
        overflow-y: auto;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 10px 15px;
        border-radius: 15px 15px 0 15px;
        margin: 10px 0;
        max-width: 80%;
        margin-left: auto;
        word-wrap: break-word;
    }
    .assistant-message {
        background-color: #e9ecef;
        color: #212529;
        padding: 10px 15px;
        border-radius: 15px 15px 15px 0;
        margin: 10px 0;
        max-width: 80%;
        margin-right: auto;
        word-wrap: break-word;
    }
    .example-query {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .example-query:hover {
        background-color: #bee5eb;
    }
    .confidence-badge {
        background-color: #28a745;
        color: white;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.8em;
        margin-left: 10px;
    }
    .suggested-action {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 8px;
        margin: 5px 5px 5px 0;
        display: inline-block;
        font-size: 0.9em;
    }
    .loading-spinner {
        text-align: center;
        padding: 20px;
    }
    .sidebar-section {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

class OrchestratorAPI:
    """API client for orchestrator agent operations"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def query_orchestrator(self, query: str, user_id: str, user_type: str, health_record_id: str = None) -> Dict[str, Any]:
        """Send query to orchestrator agent"""
        payload = {
            "query": query,
            "user_id": user_id,
            "user_type": user_type,
            "health_record_id": health_record_id
        }
        return self._make_request("POST", "/api/v1/orchestrator/query", json=payload)
    
    def get_available_tools(self) -> Dict[str, Any]:
        """Get list of available tools"""
        return self._make_request("GET", "/api/v1/orchestrator/tools")
    
    def get_example_queries(self) -> Dict[str, Any]:
        """Get example queries"""
        return self._make_request("POST", "/api/v1/orchestrator/examples")
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return self._make_request("GET", "/api/v1/orchestrator/status")

def initialize_session_state():
    """Initialize session state variables"""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "current_user" not in st.session_state:
        st.session_state.current_user = FIXED_PATIENT
    if "orchestrator_api" not in st.session_state:
        st.session_state.orchestrator_api = OrchestratorAPI(API_BASE_URL)

def display_chat_message(message: str, is_user: bool = False, confidence: float = None, suggested_actions: List[str] = None):
    """Display a chat message with styling"""
    if is_user:
        st.markdown(f'<div class="user-message">👤 {message}</div>', unsafe_allow_html=True)
    else:
        # Add confidence badge if available
        confidence_html = ""
        if confidence is not None:
            confidence_color = "#28a745" if confidence > 0.7 else "#ffc107" if confidence > 0.4 else "#dc3545"
            confidence_html = f'<span class="confidence-badge" style="background-color: {confidence_color};">Confidence: {confidence:.1%}</span>'
        
        # Add suggested actions if available
        actions_html = ""
        if suggested_actions:
            actions_html = '<div style="margin-top: 10px;"><strong>Suggested Actions:</strong><br>'
            for action in suggested_actions:
                actions_html += f'<span class="suggested-action">🔧 {action}</span>'
            actions_html += '</div>'
        
        st.markdown(f'<div class="assistant-message">🤖 {message}{confidence_html}{actions_html}</div>', unsafe_allow_html=True)

def display_example_queries():
    """Display example queries in the sidebar"""
    st.sidebar.markdown("### 💡 Example Queries")
    
    example_queries = {
        "Medical History": [
            "Give me my complete medical history report",
            "Show me all my health records",
            "Generate a comprehensive medical history"
        ],
        "Prescriptions": [
            "What's my latest prescription?",
            "Show me my current medications",
            "Get my most recent medicine prescription"
        ],
        "Search": [
            "Search for diabetes-related records",
            "Find all records about my heart condition",
            "Look for blood test results"
        ],
        "Summaries": [
            "Generate a summary of my health record",
            "Give me an overview of my medical condition",
            "Summarize my latest health checkup"
        ],
        "Specific Queries": [
            "What were my blood pressure readings?",
            "Show me my vaccination records",
            "When was my last appointment?"
        ]
    }
    
    for category, queries in example_queries.items():
        st.sidebar.markdown(f"**{category}**")
        for query in queries:
            if st.sidebar.button(query, key=f"example_{category}_{query[:20]}"):
                st.session_state.user_input = query
                st.rerun()

def display_user_info():
    """Display current user information"""
    user = st.session_state.current_user
    st.sidebar.markdown("### 👤 Current User")
    st.sidebar.markdown(f"""
    **Name:** {user['name']}  
    **Type:** {user['user_type']}  
    **Email:** {user['email']}
    """)

def display_orchestrator_status():
    """Display orchestrator agent status"""
    try:
        status = st.session_state.orchestrator_api.get_orchestrator_status()
        if status.get("status") == "healthy":
            st.sidebar.markdown("### 🤖 Agent Status")
            st.sidebar.success("🟢 Orchestrator Agent: Online")
            st.sidebar.info(f"Available Tools: {status.get('available_tools', 0)}")
        else:
            st.sidebar.error("🔴 Orchestrator Agent: Offline")
    except:
        st.sidebar.error("🔴 Orchestrator Agent: Connection Error")

def process_user_query(query: str):
    """Process user query through orchestrator agent"""
    user = st.session_state.current_user
    
    # Add user message to chat history
    st.session_state.chat_history.append({
        "message": query,
        "is_user": True,
        "timestamp": datetime.now()
    })
    
    # Show loading spinner
    with st.spinner("🤖 AI Assistant is thinking..."):
        try:
            # Send query to orchestrator
            response = st.session_state.orchestrator_api.query_orchestrator(
                query=query,
                user_id=user["id"],
                user_type=user["user_type"],
                health_record_id=None
            )
            
            if response.get("success", True):  # Default to True for orchestrator responses
                # Add assistant response to chat history
                st.session_state.chat_history.append({
                    "message": response.get("response", "No response generated"),
                    "is_user": False,
                    "confidence": response.get("confidence"),
                    "suggested_actions": response.get("suggested_actions", []),
                    "timestamp": datetime.now()
                })
            else:
                # Handle error response
                error_msg = response.get("error", "An unknown error occurred")
                st.session_state.chat_history.append({
                    "message": f"❌ Error: {error_msg}",
                    "is_user": False,
                    "confidence": 0.0,
                    "suggested_actions": [],
                    "timestamp": datetime.now()
                })
                
        except Exception as e:
            # Handle exception
            st.session_state.chat_history.append({
                "message": f"❌ Connection Error: {str(e)}",
                "is_user": False,
                "confidence": 0.0,
                "suggested_actions": [],
                "timestamp": datetime.now()
            })

def main():
    """Main application function"""
    st.markdown('<h1 class="main-header">🤖 AI Medical Assistant</h1>', unsafe_allow_html=True)
    st.markdown("### Chat with your intelligent medical records assistant")
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        display_user_info()
        display_orchestrator_status()
        st.markdown("---")
        display_example_queries()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Chat container
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Display chat history
        for chat_item in st.session_state.chat_history:
            display_chat_message(
                message=chat_item["message"],
                is_user=chat_item["is_user"],
                confidence=chat_item.get("confidence"),
                suggested_actions=chat_item.get("suggested_actions", [])
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Input area
        st.markdown("### 💬 Ask me anything about your medical records")
        
        # User input
        user_input = st.text_area(
            "Type your question here...",
            key="user_input",
            height=100,
            placeholder="e.g., Give me my complete medical history report"
        )
        
        # Send button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 Send", use_container_width=True):
                if user_input.strip():
                    process_user_query(user_input.strip())
                    st.rerun()
                else:
                    st.warning("Please enter a question.")
    
    with col2:
        # Quick actions panel
        st.markdown("### ⚡ Quick Actions")
        
        quick_actions = [
            ("📋 Medical History", "Give me my complete medical history report"),
            ("💊 Latest Prescription", "What's my latest prescription?"),
            ("🔍 Search Records", "Search for diabetes-related records"),
            ("📝 Health Summary", "Generate a summary of my health record"),
            ("🏥 Appointments", "Show me my recent appointments"),
            ("💉 Vaccinations", "Show me my vaccination records")
        ]
        
        for action_name, action_query in quick_actions:
            if st.button(action_name, key=f"quick_{action_name}"):
                st.session_state.user_input = action_query
                st.rerun()
        
        # Information panel
        st.markdown("### ℹ️ About the AI Assistant")
        st.info("""
        This AI assistant can help you with:
        
        • 📋 **Medical History Reports**
        • 💊 **Prescription Information**
        • 🔍 **Record Searches**
        • 📝 **Health Summaries**
        • 🏥 **Appointment Details**
        • 💉 **Vaccination Records**
        
        Just ask in natural language!
        """)

if __name__ == "__main__":
    main() 