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
    layout="wide",  # Use wide layout for better sidebar control
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme and styling
st.markdown("""
 
""", unsafe_allow_html=True)

# Session state will be initialized in main() function

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
        st.session_state.current_session_id = session_id
        st.session_state.chat_history = []
        
        return session_id
    except Exception as e:
        st.error(f"Error in create_new_chat_session: {str(e)}")
        raise e

def load_chat_session(session_id):
    """Load a specific chat session"""
    if session_id in st.session_state.chat_sessions:
        st.session_state.current_session_id = session_id
        st.session_state.chat_history = st.session_state.chat_sessions[session_id]['messages']
        return True
    return False

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

def delete_chat_session(session_id):
    """Delete a chat session"""
    if session_id in st.session_state.chat_sessions:
        del st.session_state.chat_sessions[session_id]
        if st.session_state.current_session_id == session_id:
            st.session_state.current_session_id = None
            st.session_state.chat_history = []

def rename_chat_session(session_id, new_name):
    """Rename a chat session"""
    if session_id in st.session_state.chat_sessions:
        st.session_state.chat_sessions[session_id]['name'] = new_name

def archive_chat_session(session_id):
    """Archive a chat session"""
    if session_id in st.session_state.chat_sessions:
        st.session_state.chat_sessions[session_id]['archived'] = True
        if st.session_state.current_session_id == session_id:
            st.session_state.current_session_id = None
            st.session_state.chat_history = []

def share_chat_session(session_id):
    """Share a chat session (placeholder for future implementation)"""
    if session_id in st.session_state.chat_sessions:
        # For now, just show a success message
        st.success("📤 Chat session copied to clipboard!")
        # In a real implementation, this would copy a shareable link or export the chat

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
            return {key: convert_datetime(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_datetime(item) for item in obj]
        else:
            return obj
    
    session_data = {
        'api_key_entered': st.session_state.get('api_key_entered', False),
        'data_loaded': st.session_state.get('data_loaded', False),
        'chat_sessions': convert_datetime(st.session_state.get('chat_sessions', {})),
        'current_session_id': st.session_state.get('current_session_id', None),
        'auto_loaded': st.session_state.get('auto_loaded', False)
    }
    
    try:
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
                def convert_datetime_strings(obj):
                    if isinstance(obj, dict):
                        result = {}
                        for key, value in obj.items():
                            if key == 'timestamp' and isinstance(value, str):
                                try:
                                    result[key] = datetime.fromisoformat(value)
                                except:
                                    result[key] = value
                            elif key == 'created_at' and isinstance(value, str):
                                try:
                                    result[key] = datetime.fromisoformat(value)
                                except:
                                    result[key] = value
                            else:
                                result[key] = convert_datetime_strings(value)
                        return result
                    elif isinstance(obj, list):
                        return [convert_datetime_strings(item) for item in obj]
                    else:
                        return obj
                
                session_data = convert_datetime_strings(session_data)
                
                # Clean up any malformed chat sessions
                if 'chat_sessions' in session_data:
                    cleaned_sessions = {}
                    for session_id, session_info in session_data['chat_sessions'].items():
                        if isinstance(session_info, dict) and 'messages' in session_info:
                            cleaned_sessions[session_id] = session_info
                        else:
                            # Skip malformed sessions
                            continue
                    session_data['chat_sessions'] = cleaned_sessions
                
                return session_data
        except json.JSONDecodeError as e:
            st.warning(f"Corrupted session data file. Creating new session. Error: {str(e)}")
            # Backup the corrupted file and create a new one
            try:
                os.rename('session_data.json', 'session_data.json.backup')
            except:
                pass
            return {}
        except Exception as e:
            st.warning(f"Error loading session data: {str(e)}. Starting fresh.")
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
    
    # Initialize chat history session state
    if 'chat_sessions' not in st.session_state:
        st.session_state.chat_sessions = persistent_data.get('chat_sessions', {})
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = persistent_data.get('current_session_id', None)
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Load current session chat history if exists
    if st.session_state.current_session_id and st.session_state.current_session_id in st.session_state.chat_sessions:
        session_data = st.session_state.chat_sessions[st.session_state.current_session_id]
        if isinstance(session_data, dict) and 'messages' in session_data:
            # Clean up any malformed messages
            cleaned_messages = []
            for msg in session_data['messages']:
                if isinstance(msg, dict) and 'content' in msg and 'role' in msg:
                    cleaned_messages.append(msg)
                elif isinstance(msg, str):
                    # Convert string messages to proper format
                    cleaned_messages.append({
                        'role': 'user',
                        'content': msg,
                        'timestamp': datetime.now()
                    })
            st.session_state.chat_history = cleaned_messages
        else:
            # Handle legacy format or malformed data
            st.session_state.chat_history = []
    
    # Mark as initialized
    if 'session_initialized' not in st.session_state:
        st.session_state.session_initialized = True

def find_data_file():
    """Find the data file in various possible locations"""
    import os
    import glob
    
    # Possible file names and locations
    possible_files = [
        "FetiiAI_Data_Austin.xlsx",
        "FetiiAI_Data_Austin.xls",
        "FetiiAI_Data.xlsx",
        "FetiiAI_Data.xls",
        "data.xlsx",
        "data.xls"
    ]
    
    # Search in current directory and subdirectories
    for pattern in ["*.xlsx", "*.xls"]:
        files = glob.glob(pattern, recursive=True)
        for file in files:
            if any(name.lower() in file.lower() for name in ["fetii", "austin", "data"]):
                return file
    
    # Check specific file names
    for filename in possible_files:
        if os.path.exists(filename):
            return filename
    
    return None

def restore_chatbot_state():
    """Restore chatbot state from persistent data"""
    if st.session_state.api_key_entered and not st.session_state.chatbot:
        # Try to restore API key from environment or config
        api_key = None
        
        # Check environment variable first
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        
        # If not found, try to load from a config file
        if not api_key:
            try:
                with open('config.txt', 'r') as f:
                    api_key = f.read().strip()
            except FileNotFoundError:
                pass
        
        if api_key:
            try:
                st.session_state.chatbot = FetiiChatbot(api_key)
                
                # Restore data if it was loaded
                if st.session_state.data_loaded:
                    data_file = find_data_file()
                    if data_file:
                        success = st.session_state.chatbot.load_data(data_file=data_file)
                    if success:
                        pass  # Data restored successfully
                    else:
                        st.warning("⚠️ Data restoration failed. Please reload data.")
            except Exception as e:
                st.error(f"❌ Error restoring chatbot state: {str(e)}")

def auto_load_app():
    """Auto-load API key and data on app startup"""
    if not st.session_state.auto_loaded:
        st.session_state.auto_loaded = True
        
        # Try to load API key from environment or config
        api_key = None
        
        # Check environment variable first
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
                save_session_data()  # Save session data
                
                # Try to find and load data file
                data_file = find_data_file()
                if data_file:
                    success = st.session_state.chatbot.load_data(data_file=data_file)
                    if success:
                        st.session_state.data_loaded = True
                        save_session_data()  # Save session data
                        st.success("🚀 App auto-loaded successfully! API key and data are ready.")
                    else:
                        st.warning("⚠️ API key loaded, but data loading failed. Please use the file uploader.")
                else:
                    st.warning("⚠️ API key loaded, but no data file found. Please upload the data file.")
            except Exception as e:
                st.error(f"❌ Error during auto-load: {str(e)}")
        else:
            # Restore chatbot state if already loaded
            restore_chatbot_state()

def main():
    """Main application function"""
    # Initialize session state
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = None
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Header
    st.title("🚗 FetiiAI - GPT-Powered Rideshare Analytics")
    st.markdown("Ask questions about Austin rideshare data and get intelligent insights")
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        api_key = st.text_input("OpenAI API Key", type="password")
        
        if api_key and st.session_state.chatbot is None:
            try:
                from chatbot import FetiiChatbot
                st.session_state.chatbot = FetiiChatbot(api_key)
                st.success("✅ Chatbot initialized!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        st.header("📊 Data Upload")
        data_file = st.file_uploader("Upload Fetii Data", type=['xlsx', 'xls'])
        
        if st.button("Load Sample Data"):
            if st.session_state.chatbot:
                try:
                    success = st.session_state.chatbot.load_data(data_file="sample_fetii_data.xlsx")
                    if success:
                        st.session_state.data_loaded = True
                        st.success("✅ Sample data loaded!")
                    else:
                        st.error("❌ Failed to load sample data")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.error("❌ Please configure API key first")
    
    # Main content
    st.header("💬 Chat Interface")
    
    # Navigation
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

def render_sidebar():
    """Render the sidebar with chat history and configuration"""
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
                st.exception(e)
        
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
                            "Edit chat name:",
                            value=full_chat_name,
                            key=f"edit_input_{session_id}",
                            label_visibility="collapsed",
                            placeholder="Enter new chat name..."
                        )
                    
                    with col2:
                        if st.button("✓", key=f"save_{session_id}", help="Save changes"):
                            if new_name.strip() and new_name.strip() != full_chat_name:
                                # Update the session name
                                st.session_state.chat_sessions[session_id]['name'] = new_name.strip()
                                save_session_data()
                                st.success(f"✅ Renamed to: {new_name.strip()}")
                                st.session_state[f"edit_{session_id}"] = False
                        st.rerun()
                    
                    with col3:
                        if st.button("✗", key=f"cancel_{session_id}", help="Cancel editing"):
                            st.session_state[f"edit_{session_id}"] = False
                        st.rerun()
                else:
                    # Normal display mode with hover actions
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        # Create enhanced tooltip with full information
                        tooltip_text = f"{full_chat_name}\nCreated: {time_str}\n\nClick to open this chat"
                        
                        # Add message count if available
                        if 'messages' in session_data and session_data['messages']:
                            msg_count = len(session_data['messages'])
                            tooltip_text = f"{full_chat_name}\nCreated: {time_str}\n{msg_count} messages\n\nClick to open this chat"
                        
                        if st.button(f"{chat_display_name}", key=f"chat_{session_id}", help=tooltip_text):
                            load_chat_session(session_id)
                        st.rerun()
                    
                    with col2:
                        if st.button("✏️", key=f"edit_btn_{session_id}", help="Edit chat name"):
                            st.session_state[f"edit_{session_id}"] = True
                        st.rerun()
                    
                    with col3:
                        if st.button("🗑️", key=f"delete_btn_{session_id}", help="Delete this chat"):
                            # Confirm deletion
                            st.session_state[f"confirm_delete_{session_id}"] = True
                        st.rerun()
                
                # Show confirmation dialog if delete was clicked
                if st.session_state.get(f"confirm_delete_{session_id}", False):
                    st.warning(f"⚠️ Are you sure you want to delete '{full_chat_name}'?")
                    col_confirm1, col_confirm2 = st.columns(2)
                    
                    with col_confirm1:
                        if st.button("✅ Yes, Delete", key=f"confirm_delete_yes_{session_id}", type="primary"):
                            # Delete the chat session
                            try:
                                # Remove from session state
                                if session_id in st.session_state.chat_sessions:
                                    del st.session_state.chat_sessions[session_id]
                                
                                # Clear the current session if it's the one being deleted
                                if st.session_state.get('current_session_id') == session_id:
                                    st.session_state.current_session_id = None
                                    st.session_state.chat_history = []
                                
                                # Save the updated session data
                                save_session_data()
                                
                                # Clear confirmation state
                                st.session_state[f"confirm_delete_{session_id}"] = False
                                
                                st.success(f"✅ Chat '{full_chat_name}' deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error deleting chat: {str(e)}")
                    
                    with col_confirm2:
                        if st.button("❌ Cancel", key=f"confirm_delete_no_{session_id}"):
                            st.session_state[f"confirm_delete_{session_id}"] = False
                            st.rerun()
        
        st.divider()
        
        # Configuration Section
        st.header("⚙️ Configuration")
        
        # Auto-setup section
        with st.expander("🔧 Auto-Setup (Recommended)", expanded=not st.session_state.api_key_entered):
            st.markdown("**Option 1: Environment Variable**")
            st.code("set OPENAI_API_KEY=your_api_key_here")
            st.markdown("**Option 2: Config File**")
            st.markdown("1. Create a file named `config.txt`")
            st.markdown("2. Add your API key on the first line")
            st.markdown("3. Save the file in the same directory as app.py")
            
            if st.button("🔄 Reload App"):
                st.session_state.auto_loaded = False
                st.rerun()
            
            if st.button("🗑️ Clear Session Data"):
                try:
                    if os.path.exists('session_data.json'):
                        os.remove('session_data.json')
                    if os.path.exists('session_data.json.backup'):
                        os.remove('session_data.json.backup')
                    st.session_state.clear()
                    st.success("✅ Session data cleared successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error clearing session data: {str(e)}")
            
            if st.button("🔧 Fix Sidebar Issues", help="Clean up corrupted sidebar data"):
                try:
                    # Clean up any corrupted sessions
                    if 'chat_sessions' in st.session_state:
                        cleaned_sessions = {}
                        for session_id, session_data in st.session_state.chat_sessions.items():
                            if isinstance(session_data, dict) and 'name' in session_data and 'created_at' in session_data:
                                # Clean the name of any HTML
                                import re
                                clean_name = re.sub(r'<[^>]+>', '', str(session_data['name'])).strip()
                                if clean_name:
                                    session_data['name'] = clean_name
                                    cleaned_sessions[session_id] = session_data
                        st.session_state.chat_sessions = cleaned_sessions
                        save_session_data()
                        st.success("✅ Sidebar data cleaned! Please refresh the page.")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error fixing sidebar: {str(e)}")
        
        # Manual API Key input (fallback)
        if not st.session_state.api_key_entered:
            st.markdown("---")
            st.subheader("🔑 Manual API Key Entry")
        api_key = st.text_input(
            "OpenAI API Key", 
            type="password",
            help="Enter your OpenAI API key to enable GPT-powered responses"
        )
        
        if api_key:
            try:
                st.session_state.chatbot = FetiiChatbot(api_key)
                st.session_state.api_key_entered = True
                save_session_data()  # Save session data
                st.success("✅ API Key configured successfully!")
            except Exception as e:
                st.error(f"❌ Error configuring API key: {str(e)}")
        else:
            st.success("✅ API Key: Connected")
            if st.button("Change API Key"):
                st.session_state.api_key_entered = False
                st.session_state.chatbot = None
                st.session_state.data_loaded = False
                st.rerun()
        
        st.divider()
        
        # Data upload section
        st.header("📊 Data Status")
        
        if st.session_state.data_loaded:
            st.success("✅ Data: Loaded")
            if st.button("🔄 Reload Data"):
                st.session_state.data_loaded = False
                st.rerun()
        else:
            st.warning("⚠️ Data: Not loaded")
            
            # Auto-load button
            if st.button("🚀 Auto-Load Data"):
                if st.session_state.chatbot:
                    data_file = find_data_file()
                    if data_file:
                        success = st.session_state.chatbot.load_data(data_file=data_file)
                        if success:
                            st.session_state.data_loaded = True
                            st.success("✅ Data loaded successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to load data. Try file upload below.")
                    else:
                        st.error("❌ No data file found. Please upload the file.")
                else:
                    st.error("Please configure API key first")
        
            # Fix permission button
            if st.button("🔧 Fix Permission Issues"):
                st.info("**Troubleshooting Steps:**")
                st.markdown("1. **Close Excel** - Make sure the Excel file is not open")
                st.markdown("2. **Check File Properties** - Right-click the file → Properties → Security")
                st.markdown("3. **Run as Administrator** - Try running the app as administrator")
                st.markdown("4. **Copy File** - Copy the file to a different location")
                st.markdown("5. **Use Upload** - Use the file uploader below as alternative")
                
                # Try to create a copy
                import os
                import shutil
                import tempfile
                
                if os.path.exists("FetiiAI_Data_Austin.xlsx"):
                    try:
                        st.info("🔄 Creating a working copy...")
                        temp_dir = tempfile.mkdtemp()
                        temp_file = os.path.join(temp_dir, "FetiiAI_Data_Austin.xlsx")
                        shutil.copy2("FetiiAI_Data_Austin.xlsx", temp_file)
                        
                        if st.session_state.chatbot:
                            success = st.session_state.chatbot.load_data(data_file=temp_file)
                            if success:
                                st.session_state.data_loaded = True
                                st.success("✅ Data loaded from working copy!")
                                st.rerun()
                            else:
                                st.error("❌ Still having issues. Please use file uploader.")
                    except Exception as e:
                        st.error(f"❌ Could not create working copy: {str(e)}")
                else:
                    st.error("❌ Data file not found. Please upload the file.")
            
            st.markdown("---")
            st.subheader("📁 Manual Upload")
        
        # Single file upload for the Fetii Excel file with multiple tabs
        data_file = st.file_uploader(
            "Upload Fetii Data (Excel with multiple tabs)",
            type=['xlsx', 'xls'],
            help="Upload your FetiiAI_Data_Austin.xlsx file with Trip data, Rider data, and Ride Demo tabs"
        )
        
        # Legacy option for separate files (collapsed by default)
        with st.expander("📁 Upload Separate Files (Legacy)", expanded=False):
            st.markdown("*Use this option if you have separate files for trips and users data*")
            
            trips_file = st.file_uploader(
                "Upload Trips Data (Excel)",
                type=['xlsx', 'xls'],
                help="Upload your Fetii trips data in Excel format",
                key="trips_file_legacy"
            )
            
            users_file = st.file_uploader(
                "Upload Users Data (Excel)",
                type=['xlsx', 'xls'],
                help="Upload your Fetii users data in Excel format",
                key="users_file_legacy"
            )
        
        # Load data button
        if st.button("Load Data", disabled=not (data_file or trips_file or users_file)):
            if st.session_state.chatbot:
                if data_file:
                    # New method: single file with tabs
                    success = st.session_state.chatbot.load_data(data_file=data_file)
                else:
                    # Legacy method: separate files
                    success = st.session_state.chatbot.load_data(
                        trips_file=trips_file.name if trips_file else None,
                        users_file=users_file.name if users_file else None
                    )
                
                if success:
                    st.session_state.data_loaded = True
                    st.success("✅ Data loaded successfully!")
                else:
                    st.error("❌ Failed to load data")
            else:
                st.error("❌ Please configure API key first")
        
        # Load real data button
        st.markdown("---")
        st.subheader("📊 Load Real Fetii Data")
        if st.button("Load FetiiAI Data", help="Load the real FetiiAI_Data_Austin.xlsx file"):
            if st.session_state.chatbot:
                try:
                    st.info("🔍 Loading FetiiAI data...")
                    st.info(f"🔍 Chatbot data processor before load: {st.session_state.chatbot.data_processor.trips_data is None}")
                    # Load the real Excel file
                    success = st.session_state.chatbot.load_data(data_file="FetiiAI_Data_Austin.xlsx")
                    st.info(f"🔍 Load result: {success}")
                    st.info(f"🔍 Chatbot data processor after load: {st.session_state.chatbot.data_processor.trips_data is None}")
                    if success:
                        st.session_state.data_loaded = True
                        st.success("✅ FetiiAI data loaded successfully!")
                        st.info("📊 Real data includes Austin rideshare trips, user demographics, and rider data")
                    else:
                        st.error("❌ Failed to load FetiiAI data")
                except Exception as e:
                    st.error(f"❌ Error loading FetiiAI data: {str(e)}")
                    st.exception(e)
            else:
                st.error("❌ Please configure API key first")
        
        st.divider()
        
        # Quick actions - Stacked button layout
        st.header("🚀 Quick Actions")
        
        # Stack of action buttons
        action_buttons = [
            ("📊", "Load Data", "Load FetiiAI data", "load_data"),
            ("📈", "Data Summary", "View data summary", "data_summary"),
            ("❓", "Help", "Get help", "help"),
            ("🗑️", "Clear Chat", "Clear current chat history", "clear_chat"),
            ("🔄", "Refresh", "Refresh data", "refresh"),
            ("⚙️", "Settings", "Open settings", "settings")
        ]
        
        for icon, label, tooltip, key in action_buttons:
            if st.button(f"{icon} {label}", key=f"action_{key}", help=tooltip):
                if key == "load_data":
                    if st.session_state.chatbot:
                        data_file = find_data_file()
                        if data_file:
                            success = st.session_state.chatbot.load_data(data_file=data_file)
                            if success:
                                st.session_state.data_loaded = True
                                st.success("✅ Data loaded successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to load data")
                        else:
                            st.error("❌ No data file found")
                    else:
                        st.error("❌ Please configure API key first")
                
                elif key == "data_summary":
                    if st.session_state.data_loaded and st.session_state.chatbot:
                        summary = st.session_state.chatbot.data_processor.get_data_summary()
                        st.json(summary)
                    else:
                        st.warning("⚠️ Please load data first")
                
                elif key == "help":
                    st.info("❓ Help: Check the Help tab for detailed instructions")
                
                elif key == "clear_chat":
                    if st.session_state.chatbot and st.session_state.current_session_id:
                        st.session_state.chatbot.clear_memory()
                        st.session_state.chat_history = []
                        st.session_state.chat_sessions[st.session_state.current_session_id]['messages'] = []
                        st.success("✅ Current chat cleared!")
                
                elif key == "refresh":
                    st.rerun()
                
                elif key == "settings":
                    st.info("⚙️ Settings panel coming soon!")
    
    # Main content area
    
    
    if not st.session_state.api_key_entered:
        st.warning("⚠️ Please enter your OpenAI API key in the sidebar to get started.")
        st.info("""
        **Getting Started:**
        1. Enter your OpenAI API key in the sidebar
        2. Load the FetiiAI data using the "Load FetiiAI Data" button
        3. Start asking questions about the data!
        """)
        return
    
    if not st.session_state.data_loaded:
        st.warning("⚠️ Please load the FetiiAI data to start analyzing.")
        
        # Add file uploader as alternative
        st.subheader("📁 Upload FetiiAI Data File")
        uploaded_file = st.file_uploader(
            "Choose an Excel file (.xlsx)",
            type=['xlsx'],
            help="Upload the FetiiAI_Data_Austin.xlsx file if the local file cannot be accessed"
        )
        
        if uploaded_file is not None:
            try:
                # Save uploaded file temporarily
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                # Load data from uploaded file
                if st.session_state.chatbot:
                    success = st.session_state.chatbot.load_data(data_file=tmp_file_path)
                    if success:
                        st.session_state.data_loaded = True
                        st.success("✅ FetiiAI data loaded successfully from uploaded file!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to load data from uploaded file")
                
                # Clean up temporary file
                os.unlink(tmp_file_path)
                
            except Exception as e:
                st.error(f"❌ Error processing uploaded file: {str(e)}")
        
        return

def render_main_content():
    """Render the main content area with navigation and interfaces"""
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
                st.session_state.user_input = question
                st.rerun()
    
    # Chat container
    
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
    
    # Use a simple form without sticky positioning
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            user_input = st.text_input(
                "Ask a question about the rideshare data:",
                key="user_input",
                placeholder="Ask a question about the rideshare data...",
                label_visibility="collapsed"
            )
        
    with col2:
        submitted = st.form_submit_button("Send", type="primary", use_container_width=True)
    
    # Initialize processing flag
    if 'question_processed' not in st.session_state:
        st.session_state.question_processed = False
    
    # Handle the form submission
    if submitted and user_input and not st.session_state.question_processed:
        st.session_state.question_processed = True
        if st.session_state.chatbot:
            # Create new chat session if none exists
            if not st.session_state.current_session_id:
                create_new_chat_session()
            
            with st.spinner("🤔 Thinking..."):
                response = st.session_state.chatbot.process_question(user_input)
                
                # Save messages to current session
                save_message_to_session("user", user_input)
                save_message_to_session("assistant", response["answer"])
                
                # Rerun to show the new message
                st.rerun()
    
    # Handle sample question clicks (only if not from form submission)
    elif st.session_state.get('user_input') and not submitted and not st.session_state.question_processed:
        st.session_state.question_processed = True
        if st.session_state.chatbot:
            # Create new chat session if none exists
            if not st.session_state.current_session_id:
                create_new_chat_session()
            
            with st.spinner("🤔 Thinking..."):
                response = st.session_state.chatbot.process_question(st.session_state.user_input)
                
                # Save messages to current session
                save_message_to_session("user", st.session_state.user_input)
                save_message_to_session("assistant", response["answer"])
                
                # Clear the user input to prevent re-processing
                if 'user_input' in st.session_state:
                    del st.session_state.user_input
                
                # Rerun to show the new message
                st.rerun()
    
    # Reset processing flag when form is submitted (new question)
    if submitted:
        st.session_state.question_processed = False
    

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
    
    1. **Get OpenAI API Key**: Sign up at [OpenAI](https://platform.openai.com/) and get your API key
    2. **Load Data**: Use the "Load FetiiAI Data" button to load the FetiiAI_Data_Austin.xlsx file with all 3 tabs (Trip data, Rider data, Ride Demo)
    3. **Start Chatting**: Ask questions about your data!
    
    ### 💡 Sample Questions
    
    Here are some example questions you can ask:
    
    - **Destination Analysis**: "How many groups went to the Moody Center last month?"
    - **Demographics**: "What are the top destinations for 18-24 year-olds on Saturday nights?"
    - **Group Size**: "What time do large groups (6+) usually ride in Austin on Fridays?"
    - **Popular Spots**: "Show me the most popular destinations in Austin"
    - **Patterns**: "When is the busiest time for rideshares?"
    - **Statistics**: "What's the average group size for trips?"
    
    ### 📊 Features
    
    - **Interactive Chat**: Natural language questions with AI-powered responses
    - **Data Visualization**: Charts and graphs for better insights
    - **Real-time Analysis**: Instant answers based on your data
    - **Multiple Views**: Chat, Analytics, and Data Explorer interfaces
    
    ### 🔧 Data Format
    
    Your FetiiAI_Data_Austin.xlsx file should contain 3 tabs:
    
    **Trip data tab:**
    - `Trip ID`, `User ID of booker`, `pickup/drop off longitude and latitude`
    - `pickup/drop off address`, `timestamps`, `how many users rode in the fetii`
    
    **Rider data tab:**
    - `Trip ID`, `associated User ID who was a passenger in that trip`
    
    **Ride Demo tab:**
    - `User ID`, `their age`
    
    ### 🆘 Troubleshooting
    
    - **API Key Issues**: Make sure your OpenAI API key is valid and has credits
    - **Data Loading**: Ensure your Excel files are in the correct format
    - **No Response**: Try rephrasing your question or check if the data contains relevant information
    
    ### 📞 Support
    
    For technical support or questions about the hackathon, contact:
    - Email: matthewiommi@fetii.com
    - Check the hackathon instructions for more details
    """)
    
    # Technical details
    with st.expander("🔧 Technical Details"):
        st.markdown("""
        **Built with:**
        - Streamlit for the web interface
        - LangChain for AI integration
        - OpenAI GPT-3.5-turbo for natural language processing
        - Pandas for data manipulation
        - Plotly for visualizations
        
        **Architecture:**
        - Modular design with separate components
        - Real-time data processing
        - Conversation memory for context
        - Interactive visualizations
        """)

if __name__ == "__main__":
    main()
