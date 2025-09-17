import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_chat import message
from streamlit_option_menu import option_menu
import os
from datetime import datetime, timedelta
import io
import json
import uuid

# Import our custom modules
from chatbot import FetiiChatbot
from data_processor import FetiiDataProcessor
from config import STREAMLIT_CONFIG, AUSTIN_DESTINATIONS

# Page configuration
st.set_page_config(
    page_title=STREAMLIT_CONFIG["page_title"],
    page_icon=STREAMLIT_CONFIG["page_icon"],
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme and styling
st.markdown("""
<style>
    /* Main theme - Dark mode */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #262730;
    }
    
    /* Headers */
    .main .block-container h1 {
        color: #ffffff;
    }
    
    .main .block-container h2 {
        color: #ffffff;
    }
    
    .main .block-container h3 {
        color: #ffffff;
    }
    
    /* Text */
    .main .block-container p {
        color: #ffffff;
    }
    
    /* Success messages */
    .stSuccess {
        background-color: #1e3a1e;
        border: 1px solid #4caf50;
    }
    
    /* Error messages */
    .stError {
        background-color: #3a1e1e;
        border: 1px solid #f44336;
    }
    
    /* Warning messages */
    .stWarning {
        background-color: #3a2e1e;
        border: 1px solid #ff9800;
    }
    
    /* Info messages */
    .stInfo {
        background-color: #1e2a3a;
        border: 1px solid #2196f3;
    }
</style>
""", unsafe_allow_html=True)

# Chat History Management Functions
def create_new_chat_session():
    """Create a new chat session"""
    try:
        session_id = str(uuid.uuid4())
        session_name = f"New Chat {len(st.session_state.chat_sessions) + 1}"
        
        # Ensure session state is properly initialized
        if 'chat_sessions' not in st.session_state:
            st.session_state.chat_sessions = {}
        
        st.session_state.chat_sessions[session_id] = {
            'name': session_name,
            'created_at': datetime.now(),
            'messages': []
        }
        
        # Save session data for persistence
        save_session_data()
        
        return session_id
    except Exception as e:
        st.error(f"Error creating chat session: {str(e)}")
        return None

def save_message_to_session(role, content):
    """Save a message to the current session"""
    if st.session_state.current_session_id:
        message_data = {
            'role': role,
            'content': content,
            'timestamp': datetime.now()
        }
        st.session_state.chat_sessions[st.session_state.current_session_id]['messages'].append(message_data)
        st.session_state.chat_history.append(message_data)
        
        # Save session data for persistence
        save_session_data()

def save_session_data():
    """Save session data to file for persistence"""
    import json
    import os
    from datetime import datetime
    
    # Convert datetime objects to strings for JSON serialization
    def convert_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: convert_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_datetime(item) for item in obj]
        else:
            return obj
    
    try:
        session_data = {
            'chat_sessions': convert_datetime(st.session_state.get('chat_sessions', {})),
            'current_session_id': st.session_state.get('current_session_id'),
            'data_loaded': st.session_state.get('data_loaded', False),
            'api_key_entered': st.session_state.get('api_key_entered', False),
            'auto_loaded': st.session_state.get('auto_loaded', False),
            'api_key': st.session_state.get('api_key', ''),
            'chat_history': convert_datetime(st.session_state.get('chat_history', []))
        }
        
        with open('session_data.json', 'w') as f:
            json.dump(session_data, f, indent=2)
    except Exception as e:
        st.error(f"Error saving session data: {str(e)}")

def load_session_data():
    """Load session data from file"""
    import json
    import os
    from datetime import datetime
    
    if os.path.exists('session_data.json'):
        try:
            with open('session_data.json', 'r') as f:
                session_data = json.load(f)
            
            # Convert datetime strings back to datetime objects
            def convert_datetime_back(obj):
                if isinstance(obj, dict):
                    if 'created_at' in obj and isinstance(obj['created_at'], str):
                        try:
                            obj['created_at'] = datetime.fromisoformat(obj['created_at'])
                        except:
                            pass
                    if 'timestamp' in obj and isinstance(obj['timestamp'], str):
                        try:
                            obj['timestamp'] = datetime.fromisoformat(obj['timestamp'])
                        except:
                            pass
                    for key, value in obj.items():
                        convert_datetime_back(value)
                elif isinstance(obj, list):
                    for item in obj:
                        convert_datetime_back(item)
            
            convert_datetime_back(session_data)
            return session_data
        except Exception as e:
            st.error(f"Error loading session data: {str(e)}")
            return {}
    return {}

def initialize_session_state():
    """Initialize session state variables with persistence"""
    # Load persistent data first
    persistent_data = load_session_data()
    
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = None
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = persistent_data.get('data_loaded', False)
    if 'api_key_entered' not in st.session_state:
        st.session_state.api_key_entered = persistent_data.get('api_key_entered', False)
    if 'auto_loaded' not in st.session_state:
        st.session_state.auto_loaded = persistent_data.get('auto_loaded', False)
    
    # Initialize API key from persistent data
    if 'api_key' not in st.session_state:
        st.session_state.api_key = persistent_data.get('api_key', '')
    
    # Initialize chat history session state
    if 'chat_sessions' not in st.session_state:
        st.session_state.chat_sessions = persistent_data.get('chat_sessions', {})
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = persistent_data.get('current_session_id', None)
    
    # Initialize chat history for backward compatibility
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = persistent_data.get('chat_history', [])
    
    # Restore chatbot if API key is available
    if st.session_state.api_key and not st.session_state.chatbot and st.session_state.api_key_entered:
        try:
            st.session_state.chatbot = FetiiChatbot(st.session_state.api_key)
        except Exception as e:
            st.warning(f"Could not restore chatbot: {str(e)}")
            st.session_state.chatbot = None

def auto_load_app():
    """Try to auto-load API key and data on app startup"""
    if not st.session_state.auto_loaded:
        st.session_state.auto_loaded = True
        
        # Try to load API key from environment or config
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        
        # If not found, try to load from a config file
        if not api_key:
            try:
                with open('config.txt', 'r') as f:
                    api_key = f.read().strip()
            except FileNotFoundError:
                pass
        
        # If we found an API key, initialize the chatbot
        if api_key:
            try:
                st.session_state.chatbot = FetiiChatbot(api_key)
                st.session_state.api_key_entered = True
                st.session_state.api_key = api_key  # Store API key in session state
                save_session_data()
                
                # Try to find and load the data file
                data_file = find_data_file()
                
                if data_file:
                    success = st.session_state.chatbot.load_data(data_file=data_file)
                    if success:
                        st.session_state.data_loaded = True
                        save_session_data()
                        st.success("🚀 App auto-loaded successfully! API key and data are ready.")
                    else:
                        st.warning("⚠️ API key loaded, but data loading failed. Please upload data manually.")
                else:
                    st.warning("⚠️ API key loaded, but no data file found. Please upload data manually.")
            except Exception as e:
                st.warning(f"⚠️ Auto-load failed: {str(e)}. Please configure manually.")
        else:
            # Restore chatbot state if already loaded
            restore_chatbot_state()

def find_data_file():
    """Find data file in current directory"""
    import os
    import glob
    
    # Look for the actual Fetii data file first
    if os.path.exists("FetiiAI_Data_Austin.xlsx"):
        return "FetiiAI_Data_Austin.xlsx"
    
    # Then look for other Excel files
    patterns = [
        "*.xlsx",
        "*.xls"
    ]
    
    for pattern in patterns:
        files = glob.glob(pattern)
        if files:
            return files[0]
    return None

def restore_chatbot_state():
    """Restore chatbot state from session data"""
    try:
        if st.session_state.api_key_entered and st.session_state.chatbot is None:
            # Try to get API key from session data
            api_key = st.session_state.get('api_key')
            if not api_key:
                # Try to get from config.txt as fallback
                try:
                    with open('config.txt', 'r') as f:
                        api_key = f.read().strip()
                except:
                    pass
            
            if api_key:
                st.session_state.chatbot = FetiiChatbot(api_key)
                st.session_state.api_key = api_key  # Store it in session state
    except Exception as e:
        st.error(f"Error restoring chatbot state: {str(e)}")

def main():
    """Main application function"""
    initialize_session_state()
    auto_load_app()
    
    # Header
    st.title("🚗 FetiiAI - GPT-Powered Rideshare Analytics")
    st.markdown("Ask questions about Austin rideshare data and get intelligent insights")
    
    # Sidebar
    with st.sidebar:
        # Fetii Logo Section
        try:
            # Try to load and display the logo image
            import base64
            with open("logo.png", "rb") as f:
                logo_data = f.read()
                logo_base64 = base64.b64encode(logo_data).decode()
            
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="data:image/png;base64,{logo_base64}" alt="Fetii Logo" style="max-width: 120px; height: auto; margin-bottom: 10px;">
            </div>
            """, unsafe_allow_html=True)
        except FileNotFoundError:
            # Fallback if logo file is not found
            st.markdown("""
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #1f77b4; margin: 0; font-size: 24px; font-weight: bold;">🚗 Fetii</h2>
                <p style="color: #666; margin: 5px 0 0 0; font-size: 12px;">AI-Powered Analytics</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Chat History Section
        st.header("💬 Chat History")
        
        # New chat button
        if st.button("➕ New Chat", key="new_chat_btn"):
            try:
                create_new_chat_session()
                st.success("✅ New chat session created!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error creating new chat: {str(e)}")
        
        st.divider()
        
        # Display chat sessions
        if st.session_state.chat_sessions:
            st.subheader("Recent Chats")
            
            # Clean up any corrupted sessions first
            cleaned_sessions = {}
            for session_id, session_data in st.session_state.chat_sessions.items():
                if isinstance(session_data, dict) and 'name' in session_data and 'created_at' in session_data:
                    cleaned_sessions[session_id] = session_data
                else:
                    # Skip malformed sessions
                    continue
            
            # Update session state with cleaned sessions
            st.session_state.chat_sessions = cleaned_sessions
            
            # Sort sessions by creation time (newest first), exclude archived
            sorted_sessions = sorted(
                [(sid, data) for sid, data in cleaned_sessions.items() 
                 if not data.get('archived', False)],
                key=lambda x: x[1]['created_at'],
                reverse=True
            )
            
            for session_id, session_data in sorted_sessions:
                # Clean session name of any HTML
                import re
                clean_name = re.sub(r'<[^>]+>', '', str(session_data['name'])).strip()
                chat_display_name = clean_name[:30] + ('...' if len(clean_name) > 30 else '')
                
                # Format timestamp
                created_at = session_data.get('created_at', datetime.now())
                if isinstance(created_at, datetime):
                    time_str = created_at.strftime('%m/%d %H:%M')
                else:
                    time_str = str(created_at)[:10] if created_at else 'Unknown'
                
                # Chat item with inline editing capability
                full_chat_name = clean_name  # Use the full clean name for tooltip
                
                # Initialize states for this session
                if f"edit_{session_id}" not in st.session_state:
                    st.session_state[f"edit_{session_id}"] = False
                if f"show_dropdown_{session_id}" not in st.session_state:
                    st.session_state[f"show_dropdown_{session_id}"] = False
                
                # Check if we're in edit mode for this session
                if st.session_state[f"edit_{session_id}"]:
                    # Inline editing mode
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        new_name = st.text_input(
                            "Edit name:",
                            value=clean_name,
                            key=f"edit_input_{session_id}",
                            label_visibility="collapsed"
                        )
                    
                    with col2:
                        if st.button("✓", key=f"save_{session_id}", help="Save changes"):
                            if new_name and new_name.strip():
                                st.session_state.chat_sessions[session_id]['name'] = new_name.strip()
                                save_session_data()
                                st.session_state[f"edit_{session_id}"] = False
                                st.rerun()
                            else:
                                st.error("Name cannot be empty")
                    
                    with col3:
                        if st.button("✗", key=f"cancel_{session_id}", help="Cancel editing"):
                            st.session_state[f"edit_{session_id}"] = False
                            st.rerun()
                else:
                    # Normal display mode
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        if st.button(f"{chat_display_name}", key=f"chat_{session_id}", help=full_chat_name):
                            st.session_state.current_session_id = session_id
                            # Load messages for this session
                            if session_id in st.session_state.chat_sessions:
                                messages = st.session_state.chat_sessions[session_id].get('messages', [])
                                st.session_state.chat_history = messages
                            st.rerun()
                    
                    with col2:
                        if st.button("✏️", key=f"edit_btn_{session_id}", help="Edit chat name"):
                            st.session_state[f"edit_{session_id}"] = True
                            st.rerun()
                    
                    with col3:
                        if st.button("🗑️", key=f"delete_btn_{session_id}", help="Delete this chat"):
                            st.session_state[f"show_dropdown_{session_id}"] = True
                            st.rerun()
                    
                    # Delete confirmation dropdown
                    if st.session_state[f"show_dropdown_{session_id}"]:
                        st.warning("⚠️ Are you sure you want to delete this chat?")
                        col_confirm1, col_confirm2 = st.columns(2)
                        
                        with col_confirm1:
                            if st.button("✅ Yes, Delete", key=f"confirm_delete_yes_{session_id}", type="primary"):
                                # Delete the session
                                if session_id in st.session_state.chat_sessions:
                                    del st.session_state.chat_sessions[session_id]
                                
                                # If this was the current session, clear it
                                if st.session_state.current_session_id == session_id:
                                    st.session_state.current_session_id = None
                                    st.session_state.chat_history = []
                                
                                # Save session data
                                save_session_data()
                                
                                # Reset the dropdown state
                                st.session_state[f"show_dropdown_{session_id}"] = False
                                st.rerun()
                        
                        with col_confirm2:
                            if st.button("❌ Cancel", key=f"confirm_delete_no_{session_id}"):
                                st.session_state[f"show_dropdown_{session_id}"] = False
                                st.rerun()
        
        st.divider()
        
        # Configuration Section
        st.header("🔧 Configuration")
        
        # Show API key status
        if st.session_state.api_key_entered and st.session_state.chatbot:
            st.success("✅ API Key configured")
            st.info("🔑 Ready for AI responses")
        else:
            st.warning("⚠️ API key not configured")
            
            # Manual API Key input
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                help="Enter your OpenAI API key to enable AI responses",
                value=st.session_state.get('api_key', '')
            )
            
            if api_key:
                st.session_state.api_key = api_key
                try:
                    st.session_state.chatbot = FetiiChatbot(api_key)
                    st.session_state.api_key_entered = True
                    save_session_data()
                    st.success("✅ API Key configured successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error configuring API key: {str(e)}")
        
        st.divider()
        
        # Data Upload Section
        st.header("📊 Data Upload")
        
        # Show data status
        if st.session_state.data_loaded:
            st.success("✅ Data loaded")
            st.info("📊 Ready for analysis")
        else:
            st.warning("⚠️ No data loaded")
        
        # Manual data upload
        data_file = st.file_uploader(
            "Upload Excel Data File",
            type=['xlsx', 'xls'],
            help="Upload your FetiiAI_Data_Austin.xlsx file or any Excel file with rideshare data"
        )
        
        # Load data button
        if st.button("Load Data", disabled=not data_file):
            if st.session_state.chatbot:
                if data_file:
                    try:
                        # Handle uploaded file - save to temporary location
                        import tempfile
                        import os
                        import time
                        
                        # Create temporary file with unique name
                        temp_dir = tempfile.gettempdir()
                        temp_filename = f"fetii_data_{int(time.time())}.xlsx"
                        temp_path = os.path.join(temp_dir, temp_filename)
                        
                        # Write file content
                        with open(temp_path, 'wb') as tmp_file:
                            tmp_file.write(data_file.getvalue())
                        
                        # Small delay to ensure file is written
                        time.sleep(0.1)
                        
                        # Load data using the temporary file path
                        success = st.session_state.chatbot.load_data(data_file=temp_path)
                        
                        # Clean up temporary file
                        try:
                            os.unlink(temp_path)
                        except:
                            pass  # Ignore cleanup errors
                        
                        if success:
                            st.session_state.data_loaded = True
                            save_session_data()
                            st.success("✅ Data loaded successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Error loading data. Please check the file format.")
                    except Exception as e:
                        st.error(f"❌ Error processing file: {str(e)}")
                        # Try to clean up temp file if it exists
                        try:
                            if 'temp_path' in locals():
                                os.unlink(temp_path)
                        except:
                            pass
                else:
                    st.warning("⚠️ Please select a file first.")
            else:
                st.error("❌ Please configure API key first.")
        
        # Load sample data button
        st.markdown("---")
        st.subheader("🧪 Test with Sample Data")
        if st.button("Load Sample Data", help="Load built-in sample data for testing"):
            if st.session_state.chatbot:
                try:
                    # Load the sample Excel file
                    success = st.session_state.chatbot.load_data(data_file="sample_fetii_data.xlsx")
                    if success:
                        st.session_state.data_loaded = True
                        save_session_data()
                        st.success("✅ Sample data loaded successfully!")
                        st.info("📊 Sample data includes 500 trips with Moody Center visits, user demographics, and rider data")
                    else:
                        st.error("❌ Failed to load sample data")
                except Exception as e:
                    st.error(f"❌ Error loading sample data: {str(e)}")
            else:
                st.error("❌ Please configure API key first")
    
    # Main content
    # Navigation menu
    selected = option_menu(
        menu_title=None,
        options=["💬 Chat", "📈 Analytics", "📊 Data Explorer", "❓ Help"],
        icons=["chat", "graph-up", "table", "question-circle"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )
    
    if selected == "💬 Chat":
        chat_interface()
    elif selected == "📈 Analytics":
        analytics_interface()
    elif selected == "📊 Data Explorer":
        data_explorer_interface()
    elif selected == "❓ Help":
        help_interface()

def chat_interface():
    """Chat interface for asking questions"""
    st.header("💬 Ask FetiiAI Anything")
    
    # Check if chatbot and data are ready
    if not st.session_state.chatbot:
        st.error("❌ Please configure your API key first!")
        return
    
    if not st.session_state.data_loaded:
        st.warning("⚠️ Please load the data first to start chatting!")
        return
    
    # Chat controls
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("💡 Try these sample questions:")
    with col2:
        if st.button("🗑️ Clear Chat", help="Clear current chat history"):
            st.session_state.chat_history = []
            if st.session_state.current_session_id and st.session_state.current_session_id in st.session_state.chat_sessions:
                st.session_state.chat_sessions[st.session_state.current_session_id]['messages'] = []
            save_session_data()
            st.rerun()
    
    sample_questions = [
        "How many groups went to the Moody Center last month?",
        "What are the top destinations for 18-24 year-olds on Saturday nights?",
        "What time do large groups (6+) usually ride in Austin on Fridays?",
        "Show me the most popular destinations in Austin",
        "What's the average group size for trips?",
        "When is the busiest time for rideshares?"
    ]
    
    cols = st.columns(2)
    for i, question in enumerate(sample_questions):
        with cols[i % 2]:
            if st.button(f"❓ {question}", key=f"sample_{i}"):
                # Process the question directly
                if st.session_state.chatbot:
                    # Create new chat session if none exists
                    if not st.session_state.current_session_id:
                        create_new_chat_session()
                    
                    with st.spinner("🤔 Thinking..."):
                        response = st.session_state.chatbot.process_question(question)
                        
                        # Save messages to current session
                        save_message_to_session("user", question)
                        save_message_to_session("assistant", response["answer"])
                        
                        # Clear any input and rerun to show the new message
                        st.rerun()
                else:
                    st.error("❌ Please configure your API key first!")
    
    # Display current chat history
    if st.session_state.chat_history:
        st.subheader("💬 Current Chat")
        
        for i, msg in enumerate(st.session_state.chat_history):
            try:
                # Handle both dictionary and string message formats
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    role = msg.get("role", "user")
                    
                    # Clean content of any HTML tags
                    if isinstance(content, str):
                        import re
                        content = re.sub(r'<[^>]+>', '', content)  # Remove HTML tags
                        content = content.strip()
                    
                    if role == "user":
                        message(content, is_user=True, key=f"user_{i}")
                    else:
                        message(content, is_user=False, key=f"assistant_{i}")
                        
                        # Show data if available (for assistant messages)
                        if "data" in msg and msg["data"] is not None and hasattr(msg["data"], 'empty') and not msg["data"].empty:
                            st.markdown("### 📊 Data:")
                            st.dataframe(msg["data"].head(10))
                        
                        if "visualization" in msg and msg["visualization"]:
                            st.markdown("### 📈 Visualization:")
                            st.plotly_chart(msg["visualization"], use_container_width=True)
                elif isinstance(msg, str):
                    # Handle legacy string format - assume it's a user message
                    import re
                    clean_msg = re.sub(r'<[^>]+>', '', msg)  # Remove HTML tags
                    message(clean_msg.strip(), is_user=True, key=f"user_{i}")
                else:
                    # Skip invalid message formats
                    continue
            except Exception as e:
                # Skip problematic messages
                st.warning(f"Skipping problematic message: {str(e)}")
                continue
    
    # Simple input area at bottom
    st.subheader("💬 Ask a Question")
    
    # Simple input without form to avoid conflicts
    user_input = st.text_input(
        "Ask a question about the rideshare data:",
        key="user_input",
        placeholder="Ask a question about the rideshare data...",
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        send_button = st.button("Send", type="primary", use_container_width=True)
    
    # Process question only when send button is clicked
    if send_button and user_input:
        if st.session_state.chatbot:
            # Create new chat session if none exists
            if not st.session_state.current_session_id:
                create_new_chat_session()
            
            with st.spinner("🤔 Thinking..."):
                response = st.session_state.chatbot.process_question(user_input)
                
                # Save messages to current session
                save_message_to_session("user", user_input)
                save_message_to_session("assistant", response["answer"])
                
                # Clear the input by rerunning
                st.rerun()
        else:
            st.error("❌ Please configure your API key first!")
    
    

def analytics_interface():
    """Analytics dashboard interface"""
    st.header("📈 Analytics Dashboard")
    
    if not st.session_state.chatbot:
        st.error("❌ Please configure your API key first!")
        return
    
    if not st.session_state.data_loaded:
        st.warning("Please load data first to view analytics.")
        return
    
    data_processor = st.session_state.chatbot.data_processor
    
    # Key metrics
    st.subheader("📊 Key Metrics")
    summary = data_processor.get_data_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Trips", summary.get("total_trips", 0))
    
    with col2:
        st.metric("Unique Destinations", summary.get("unique_destinations", 0))
    
    with col3:
        st.metric("Avg Group Size", summary.get("average_group_size", 0))
    
    with col4:
        st.metric("Peak Hour", f"{summary.get('most_common_hour', 0)}:00")
    
    # Charts section
    st.subheader("📈 Visualizations")
    
    # Top destinations
    if data_processor.trips_data is not None and 'dropoff_location' in data_processor.trips_data.columns:
        top_destinations = data_processor.get_top_destinations(10)
        if not top_destinations.empty:
            fig = data_processor.create_visualization(
                "bar", top_destinations,
                title="Top 10 Destinations",
                x_label="Destination",
                y_label="Number of Trips"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ No destination data found")
    else:
        pass
    
    # Hourly distribution
    if data_processor.trips_data is not None and 'hour' in data_processor.trips_data.columns:
        hourly_data = data_processor.get_hourly_distribution()
        if not hourly_data.empty:
            fig = data_processor.create_visualization(
                "line", hourly_data,
                title="Hourly Trip Distribution",
                x_label="Hour of Day",
                y_label="Number of Trips"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Group size distribution
    if data_processor.trips_data is not None and 'group_size' in data_processor.trips_data.columns:
        group_sizes = data_processor.trips_data['group_size'].value_counts().sort_index()
        fig = data_processor.create_visualization(
            "bar", group_sizes,
            title="Group Size Distribution",
            x_label="Group Size",
            y_label="Number of Trips"
        )
        st.plotly_chart(fig, use_container_width=True)

def data_explorer_interface():
    """Data explorer interface"""
    st.header("📊 Data Explorer")
    
    if not st.session_state.chatbot:
        st.error("❌ Please configure your API key first!")
        return
    
    if not st.session_state.data_loaded:
        st.warning("Please load data first to explore.")
        return
    
    data_processor = st.session_state.chatbot.data_processor
    
    # Data overview
    st.subheader("📋 Data Overview")
    
    if data_processor.trips_data is not None:
        st.write("**Trips Data:**")
        st.dataframe(data_processor.trips_data.head(20))
        
        st.write(f"**Shape:** {data_processor.trips_data.shape}")
        st.write("**Columns:**", list(data_processor.trips_data.columns))
    
    if data_processor.users_data is not None:
        st.write("**Users Data:**")
        st.dataframe(data_processor.users_data.head(20))
        
        st.write(f"**Shape:** {data_processor.users_data.shape}")
        st.write("**Columns:**", list(data_processor.users_data.columns))
    
    # Data filters
    st.subheader("🔍 Filter Data")
    
    if data_processor.trips_data is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            if 'dropoff_location' in data_processor.trips_data.columns:
                destinations = data_processor.trips_data['dropoff_location'].unique()
                selected_dest = st.selectbox("Filter by Destination", ["All"] + list(destinations))
                
                if selected_dest != "All":
                    filtered_data = data_processor.trips_data[
                        data_processor.trips_data['dropoff_location'] == selected_dest
                    ]
                    st.write(f"**Filtered Data ({len(filtered_data)} trips):**")
                    st.dataframe(filtered_data.head(10))
        
        with col2:
            if 'group_size' in data_processor.trips_data.columns:
                min_group_size = st.slider("Minimum Group Size", 1, 10, 1)
                large_groups = data_processor.trips_data[
                    data_processor.trips_data['group_size'] >= min_group_size
                ]
                st.write(f"**Large Groups ({min_group_size}+ people): {len(large_groups)} trips**")
                st.dataframe(large_groups.head(10))
    else:
        st.warning("No data available for filtering. Please load data first.")

def help_interface():
    """Help and documentation interface"""
    st.header("❓ Help & Documentation")
    
    st.markdown("""
    ## 🚀 Getting Started
    
    **FetiiAI** is a GPT-powered chatbot designed to analyze Fetii rideshare data and answer questions about trip patterns, user behavior, and popular destinations in Austin.
    
    ### 📋 Setup Instructions
    
    1. **Configure API Key**: Enter your OpenAI API key in the sidebar
    2. **Load Data**: Upload your Fetii data file or use sample data
    3. **Start Chatting**: Ask questions about your data
    
    ### 📊 Data Format
    
    Your Excel file should contain these tabs:
    - **Trip data**: Trip ID, Booking User ID, Pickup/Dropoff coordinates, Addresses, Timestamps, Total Passengers
    - **Checked in User ID's**: Trip ID, User ID
    - **Customer Demographics**: User ID, Age
    
    ### 💬 Example Questions
    
    - "How many groups went to Moody Center last month?"
    - "What are the top drop-off spots for 18–24 year-olds on Saturday nights?"
    - "When do large groups (6+ riders) typically ride downtown?"
    - "Show me the most popular destinations in Austin"
    - "What's the average group size for trips?"
    - "When is the busiest time for rideshares?"
    
    ### 🔧 Features
    
    - **Real-time Analysis**: Get instant insights from your data
    - **Interactive Visualizations**: Charts and graphs for better understanding
    - **Smart Query Processing**: Natural language questions about your data
    - **Data Explorer**: Browse and filter your data
    - **Chat History**: Save and manage multiple chat sessions
    - **Persistent Sessions**: Your data and chat history are saved between sessions
    
    ### 🆘 Troubleshooting
    
    If you encounter issues:
    1. Make sure your API key is valid
    2. Check that your data file has the correct format
    3. Try using the sample data first
    4. Check the terminal for error messages
    
    ### 📞 Support
    
    For technical support, check the terminal output for detailed error messages.
    """)

if __name__ == "__main__":
    main()