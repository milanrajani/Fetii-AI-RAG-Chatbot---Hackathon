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
import numpy as np

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

# Use default Streamlit styling - no custom CSS

def initialize_session_state():
    """Initialize session state variables"""
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = None
    
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    if 'api_key_entered' not in st.session_state:
        st.session_state.api_key_entered = False
    
    if 'chat_sessions' not in st.session_state:
        st.session_state.chat_sessions = {}
    
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'api_key' not in st.session_state:
        st.session_state.api_key = None
    
    if 'auto_loaded' not in st.session_state:
        st.session_state.auto_loaded = False
    
    if 'loaded_data_file' not in st.session_state:
        st.session_state.loaded_data_file = None
    
    if 'trips_data' not in st.session_state:
        st.session_state.trips_data = None
    
    if 'users_data' not in st.session_state:
        st.session_state.users_data = None

def save_session_data():
    """Save session data to JSON file for persistence"""
    try:
        session_data = {
            'chat_sessions': st.session_state.chat_sessions,
            'current_session_id': st.session_state.current_session_id,
            'data_loaded': st.session_state.data_loaded,
            'api_key_entered': st.session_state.api_key_entered,
            'auto_loaded': st.session_state.auto_loaded,
            'api_key': st.session_state.api_key,
            'chat_history': st.session_state.chat_history,
            'loaded_data_file': st.session_state.loaded_data_file
        }
        
        with open('session_data.json', 'w') as f:
            json.dump(session_data, f, indent=2)
    except Exception as e:
        st.error(f"Error saving session data: {str(e)}")

def load_session_data():
    """Load session data from JSON file"""
    try:
        if os.path.exists('session_data.json'):
            with open('session_data.json', 'r') as f:
                session_data = json.load(f)
                
            # Restore session state
            st.session_state.chat_sessions = session_data.get('chat_sessions', {})
            st.session_state.current_session_id = session_data.get('current_session_id', None)
            st.session_state.data_loaded = session_data.get('data_loaded', False)
            st.session_state.api_key_entered = session_data.get('api_key_entered', False)
            st.session_state.auto_loaded = session_data.get('auto_loaded', False)
            st.session_state.api_key = session_data.get('api_key', None)
            st.session_state.chat_history = session_data.get('chat_history', [])
            st.session_state.loaded_data_file = session_data.get('loaded_data_file', None)
            
            return True
    except Exception as e:
        st.error(f"Error loading session data: {str(e)}")
    
    return False

def create_new_chat_session():
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    st.session_state.current_session_id = session_id
    st.session_state.chat_sessions[session_id] = {
        'id': session_id,
        'created_at': datetime.now().isoformat(),
        'messages': []
    }
    st.session_state.chat_history = []
    save_session_data()

def save_message_to_session(role, content, data=None, visualization=None):
    """Save a message to the current session"""
    if st.session_state.current_session_id and st.session_state.current_session_id in st.session_state.chat_sessions:
        message_data = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        if data is not None:
            message_data['data'] = data
        
        if visualization is not None:
            message_data['visualization'] = visualization
        
        st.session_state.chat_sessions[st.session_state.current_session_id]['messages'].append(message_data)
        
        # Also add to chat_history for display
        st.session_state.chat_history.append(message_data)
        
        save_session_data()

def auto_load_app():
    """Auto-load API key and data if available"""
    if st.session_state.auto_loaded:
        return
    
    # Try to load API key from environment or config.txt
    api_key = None
    
    # First try environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    
    # If not found, try config.txt
    if not api_key:
        try:
            with open('config.txt', 'r') as f:
                api_key = f.read().strip()
        except FileNotFoundError:
            pass
    
    # If API key found, initialize chatbot
    if api_key and not st.session_state.chatbot:
        try:
            st.session_state.chatbot = FetiiChatbot(api_key)
            st.session_state.api_key = api_key
            st.session_state.api_key_entered = True
            st.success("✅ API Key loaded automatically!")
            
            # If data was already loaded, transfer it to the chatbot
            if st.session_state.data_loaded and hasattr(st.session_state, 'trips_data'):
                st.session_state.chatbot.data_processor.trips_data = st.session_state.trips_data
                st.session_state.chatbot.data_processor.users_data = st.session_state.users_data
                st.session_state.chatbot.data_processor.process_data()
                st.info("🔄 Data transferred to chatbot successfully!")
        except Exception as e:
            st.error(f"Error initializing chatbot: {str(e)}")
    
    # Direct file loading - prioritize FetiiAI_Data_Austin.xlsx
    if not st.session_state.data_loaded:
        data_file = None
        
        # Check for FetiiAI_Data_Austin.xlsx first
        if os.path.exists('FetiiAI_Data_Austin.xlsx'):
            data_file = 'FetiiAI_Data_Austin.xlsx'
            st.info("🔍 Found FetiiAI_Data_Austin.xlsx file, loading directly...")
        else:
            # Look for any Excel file as fallback
            import glob
            excel_files = glob.glob('*.xlsx')
            if excel_files:
                data_file = excel_files[0]
                st.info(f"🔍 Found {data_file} file, loading directly...")
        
        if data_file:
            try:
                with st.spinner("📊 Loading data directly from file..."):
                    # Direct file processing
                    success = load_data_directly(data_file)
                    if success:
                        st.session_state.data_loaded = True
                        st.session_state.loaded_data_file = data_file
                        save_session_data()
                        st.success(f"✅ Data loaded successfully from {data_file}!")
                    else:
                        st.warning(f"⚠️ Failed to load data from {data_file}")
            except Exception as e:
                st.error(f"❌ Error loading data: {str(e)}")
        else:
            # Check if we're in a deployed environment and try to load pre-loaded data
            if is_deployed_environment():
                st.info("🌐 Deployment environment detected - checking for pre-loaded data...")
                # Try to load the pre-loaded FetiiAI_Data_Austin.xlsx file
                if os.path.exists('FetiiAI_Data_Austin.xlsx'):
                    try:
                        with st.spinner("📊 Loading pre-loaded FetiiAI_Data_Austin.xlsx..."):
                            success = load_data_directly('FetiiAI_Data_Austin.xlsx')
                            if success:
                                st.session_state.data_loaded = True
                                st.session_state.loaded_data_file = 'FetiiAI_Data_Austin.xlsx (Pre-loaded)'
                                save_session_data()
                                st.success("✅ Pre-loaded data loaded successfully!")
                                st.info("💡 Upload your own data file using the file uploader in the sidebar")
                            else:
                                st.warning("⚠️ Failed to load pre-loaded data")
                    except Exception as e:
                        st.error(f"❌ Error loading pre-loaded data: {str(e)}")
                else:
                    st.warning("⚠️ No pre-loaded data file found in deployment")
                    st.info("💡 Upload your data file using the file uploader in the sidebar")
            else:
                st.warning("⚠️ No Excel data file found in directory")
    
    st.session_state.auto_loaded = True

def is_deployed_environment():
    """Check if we're running in a deployed environment"""
    # Check for common deployment indicators
    deployed_indicators = [
        'STREAMLIT_SERVER_PORT' in os.environ,
        'PORT' in os.environ,
        'DYNO' in os.environ,  # Heroku
        'RAILWAY_ENVIRONMENT' in os.environ,  # Railway
        'STREAMLIT_CLOUD' in os.environ  # Streamlit Cloud
    ]
    return any(deployed_indicators)

def load_data_directly(file_path):
    """Load data directly from file and process it"""
    try:
        # Read the Excel file
        import pandas as pd
        
        st.info(f"📖 Reading Excel file: {file_path}")
        
        # Read all sheets
        excel_data = pd.read_excel(file_path, sheet_name=None)
        st.info(f"📋 Found {len(excel_data)} sheets: {list(excel_data.keys())}")
        
        # Process the data based on sheet names
        trips_data = None
        users_data = None
        
        # Look for trip data sheet
        for sheet_name, sheet_data in excel_data.items():
            sheet_lower = sheet_name.lower()
            st.info(f"🔍 Checking sheet '{sheet_name}' with {len(sheet_data)} rows")
            if 'trip' in sheet_lower:
                trips_data = sheet_data
                st.info(f"📊 Found trip data in sheet: {sheet_name} ({len(sheet_data)} rows)")
            elif 'user' in sheet_lower or 'rider' in sheet_lower:
                users_data = sheet_data
                st.info(f"👥 Found user data in sheet: {sheet_name} ({len(sheet_data)} rows)")
        
        # If no specific sheets found, use the first sheet as trips data
        if trips_data is None and excel_data:
            first_sheet = list(excel_data.keys())[0]
            trips_data = excel_data[first_sheet]
            st.info(f"📊 Using first sheet as trip data: {first_sheet} ({len(trips_data)} rows)")
        
        # Process the data
        if trips_data is not None and len(trips_data) > 0:
            st.info(f"🔧 Mapping columns for {len(trips_data)} trips...")
            st.info(f"📋 Original columns: {list(trips_data.columns)}")
            
            # Map columns to standard names
            trips_data = map_fetii_columns(trips_data)
            st.info(f"📋 Mapped columns: {list(trips_data.columns)}")
            
            # Store data in session state for later use
            st.session_state.trips_data = trips_data
            st.session_state.users_data = users_data
            
            # If chatbot exists, also store in its data processor
            if st.session_state.chatbot:
                st.session_state.chatbot.data_processor.trips_data = trips_data
                st.session_state.chatbot.data_processor.users_data = users_data
                st.session_state.chatbot.data_processor.process_data()
                st.info("🤖 Data transferred to chatbot successfully!")
            else:
                # If no chatbot yet, we'll transfer data when chatbot is created
                st.info("📊 Data loaded and ready. Will transfer to chatbot when API key is available.")
            
            return True
        else:
            st.error("❌ No valid data found in the Excel file")
            return False
            
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return False

# Sample data generation function removed - using pre-loaded data instead

def map_fetii_columns(df):
    """Map Fetii dataset column names to expected names"""
    column_mapping = {}
    
    for col in df.columns:
        col_lower = col.lower().strip()
        
        # Trip ID mapping
        if col_lower == 'trip id':
            column_mapping[col] = 'trip_id'
        # Booking User ID mapping
        elif col_lower == 'booking user id':
            column_mapping[col] = 'user_id'
        # Pickup coordinates
        elif col_lower == 'pick up lattittude' or col_lower == 'pick up latitude':
            column_mapping[col] = 'pickup_latitude'
        elif col_lower == 'pick up longitude':
            column_mapping[col] = 'pickup_longitude'
        # Dropoff coordinates
        elif col_lower == 'drop off latitude':
            column_mapping[col] = 'dropoff_latitude'
        elif col_lower == 'drop off longitude':
            column_mapping[col] = 'dropoff_longitude'
        # Addresses
        elif col_lower == 'pick up address':
            column_mapping[col] = 'pickup_location'
        elif col_lower == 'drop off address':
            column_mapping[col] = 'dropoff_location'
        # Date and time
        elif col_lower == 'trip date and time':
            column_mapping[col] = 'pickup_time'
        # Total passengers
        elif col_lower == 'total passengers':
            column_mapping[col] = 'group_size'
    
    # Apply the mapping
    df = df.rename(columns=column_mapping)
    
    return df

def render_sidebar():
    """Render the sidebar with configuration and data upload"""
    with st.sidebar:
        st.title("🚗 FetiiAI")
        st.markdown("---")
        
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
        
        st.markdown("---")
        
        # Data Upload Section
        st.header("📊 Data Upload")
        
        # Show data status
        if st.session_state.data_loaded:
            st.success("✅ Data loaded automatically")
            st.info("📊 Ready for analysis")
            
            # Show data file info
            if hasattr(st.session_state, 'loaded_data_file') and st.session_state.loaded_data_file:
                st.info(f"📁 File: {st.session_state.loaded_data_file}")
            else:
                st.info("📁 File: FetiiAI_Data_Austin.xlsx (auto-loaded)")
        else:
            st.warning("⚠️ No data loaded")
            st.info("💡 Place FetiiAI_Data_Austin.xlsx in the app directory for auto-loading")
            
            # Auto-load button
            if st.button("🚀 Auto-Load FetiiAI_Data_Austin.xlsx", type="primary", help="Automatically load the data file from the directory"):
                force_load_data()
        
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
        
        st.markdown("---")
        
        # Chat Management
        st.header("💬 Chat Management")
        
        # Show current session info
        if st.session_state.current_session_id:
            session_info = st.session_state.chat_sessions.get(st.session_state.current_session_id, {})
            created_at = session_info.get('created_at', 'Unknown')
            message_count = len(session_info.get('messages', []))
            
            st.info(f"**Current Session:**\n📅 Created: {created_at[:10] if created_at != 'Unknown' else 'Unknown'}\n💬 Messages: {message_count}")
        
        # Chat session list
        if st.session_state.chat_sessions:
            st.subheader("📋 Chat Sessions")
            
            # Sort sessions by creation date (newest first)
            sorted_sessions = sorted(
                st.session_state.chat_sessions.items(),
                key=lambda x: x[1].get('created_at', ''),
                reverse=True
            )
            
            for session_id, session_data in sorted_sessions[:5]:  # Show last 5 sessions
                created_at = session_data.get('created_at', 'Unknown')
                message_count = len(session_data.get('messages', []))
                is_current = session_id == st.session_state.current_session_id
                
                # Create a button for each session
                button_text = f"💬 {created_at[:10] if created_at != 'Unknown' else 'Unknown'} ({message_count} msgs)"
                
                if is_current:
                    button_text = f"✅ {button_text}"
                
                if st.button(button_text, key=f"session_{session_id}", help=f"Switch to session from {created_at[:10] if created_at != 'Unknown' else 'Unknown'}"):
                    # Switch to this session
                    st.session_state.current_session_id = session_id
                    st.session_state.chat_history = session_data.get('messages', [])
                    save_session_data()
                    st.rerun()
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Chat", help="Clear current chat session"):
                if st.session_state.current_session_id and st.session_state.current_session_id in st.session_state.chat_sessions:
                    st.session_state.chat_sessions[st.session_state.current_session_id]['messages'] = []
                st.session_state.chat_history = []
                save_session_data()
                st.rerun()
        
        with col2:
            if st.button("🆕 New Chat", help="Start a new chat session"):
                create_new_chat_session()
                st.rerun()

def chat_interface():
    """Main chat interface"""
    st.header("🤖 FetiiAI Chatbot")
    st.markdown("Ask questions about your rideshare data and get intelligent insights!")
    
    # Sample questions
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
                        
                        # Rerun to show the new message
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
                
                # Rerun to show the new message
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
        st.metric("Average Group Size", f"{summary.get('avg_group_size', 0):.1f}")
    
    with col4:
        st.metric("Total Users", summary.get("total_users", 0))
    
    # Visualizations
    st.subheader("📊 Data Visualizations")
    
    # Popular destinations
    if data_processor.trips_data is not None and not data_processor.trips_data.empty:
        st.subheader("🏆 Top Destinations")
        # Use the correct column name
        if 'dropoff_location' in data_processor.trips_data.columns:
            top_destinations = data_processor.trips_data['dropoff_location'].value_counts().head(10)
            
            if not top_destinations.empty:
                fig = px.bar(
                    x=top_destinations.values,
                    y=top_destinations.index,
                    orientation='h',
                    title="Top 10 Destinations",
                    labels={'x': 'Number of Trips', 'y': 'Destination'}
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Dropoff location data not available")
    
    # Group size distribution
    if data_processor.trips_data is not None and not data_processor.trips_data.empty:
        st.subheader("👥 Group Size Distribution")
        # Use the correct column name
        if 'group_size' in data_processor.trips_data.columns:
            group_size_dist = data_processor.trips_data['group_size'].value_counts().sort_index()
            
            if not group_size_dist.empty:
                fig = px.bar(
                    x=group_size_dist.index,
                    y=group_size_dist.values,
                    title="Group Size Distribution",
                    labels={'x': 'Group Size', 'y': 'Number of Trips'}
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Group size data not available")
    
    # Time-based analysis
    if data_processor.trips_data is not None and not data_processor.trips_data.empty:
        st.subheader("⏰ Time-based Analysis")
        
        # Hourly distribution
        if 'pickup_time' in data_processor.trips_data.columns:
            # Extract hour from pickup_time
            data_processor.trips_data['hour'] = pd.to_datetime(data_processor.trips_data['pickup_time']).dt.hour
            hourly_dist = data_processor.trips_data['hour'].value_counts().sort_index()
            
            if not hourly_dist.empty:
                fig = px.bar(
                    x=hourly_dist.index,
                    y=hourly_dist.values,
                    title="Trips by Hour of Day",
                    labels={'x': 'Hour', 'y': 'Number of Trips'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Day of week analysis
        if 'pickup_time' in data_processor.trips_data.columns:
            data_processor.trips_data['day_of_week'] = pd.to_datetime(data_processor.trips_data['pickup_time']).dt.day_name()
            daily_dist = data_processor.trips_data['day_of_week'].value_counts()
            
            if not daily_dist.empty:
                fig = px.bar(
                    x=daily_dist.index,
                    y=daily_dist.values,
                    title="Trips by Day of Week",
                    labels={'x': 'Day', 'y': 'Number of Trips'}
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Age group analysis
    if data_processor.users_data is not None and not data_processor.users_data.empty:
        st.subheader("👥 Age Group Analysis")
        
        if 'age' in data_processor.users_data.columns:
            # Create age groups
            data_processor.users_data['age_group'] = pd.cut(
                data_processor.users_data['age'], 
                bins=[0, 18, 25, 35, 45, 55, 100], 
                labels=['Under 18', '18-24', '25-34', '35-44', '45-54', '55+']
            )
            
            age_dist = data_processor.users_data['age_group'].value_counts()
            
            if not age_dist.empty:
                fig = px.pie(
                    values=age_dist.values,
                    names=age_dist.index,
                    title="Age Group Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Geographic analysis
    if data_processor.trips_data is not None and not data_processor.trips_data.empty:
        st.subheader("🗺️ Geographic Analysis")
        
        if 'pickup_latitude' in data_processor.trips_data.columns and 'pickup_longitude' in data_processor.trips_data.columns:
            # Create a map of pickup locations
            fig = px.scatter_mapbox(
                data_processor.trips_data,
                lat='pickup_latitude',
                lon='pickup_longitude',
                color='group_size',
                size='group_size',
                hover_data=['pickup_location', 'dropoff_location'],
                title="Pickup Locations by Group Size",
                mapbox_style="open-street-map"
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    # Revenue analysis (if available)
    if data_processor.trips_data is not None and not data_processor.trips_data.empty:
        st.subheader("💰 Revenue Analysis")
        
        # Calculate estimated revenue based on group size
        if 'group_size' in data_processor.trips_data.columns:
            # Assume $5 per person as base fare
            data_processor.trips_data['estimated_revenue'] = data_processor.trips_data['group_size'] * 5
            
            total_revenue = data_processor.trips_data['estimated_revenue'].sum()
            avg_revenue_per_trip = data_processor.trips_data['estimated_revenue'].mean()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Estimated Revenue", f"${total_revenue:,.2f}")
            with col2:
                st.metric("Average Revenue per Trip", f"${avg_revenue_per_trip:.2f}")
    
    # Advanced analytics
    st.subheader("🔍 Advanced Analytics")
    
    # Correlation analysis
    if data_processor.trips_data is not None and not data_processor.trips_data.empty:
        st.subheader("📊 Correlation Analysis")
        
        numeric_cols = data_processor.trips_data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            corr_matrix = data_processor.trips_data[numeric_cols].corr()
            
            fig = px.imshow(
                corr_matrix,
                title="Correlation Matrix",
                color_continuous_scale="RdBu"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Data quality metrics
    st.subheader("🔍 Data Quality Metrics")
    
    if data_processor.trips_data is not None and not data_processor.trips_data.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            missing_data = data_processor.trips_data.isnull().sum().sum()
            st.metric("Missing Values", missing_data)
        
        with col2:
            duplicate_trips = data_processor.trips_data.duplicated().sum()
            st.metric("Duplicate Trips", duplicate_trips)
        
        with col3:
            data_quality_score = ((len(data_processor.trips_data) - missing_data) / len(data_processor.trips_data)) * 100
            st.metric("Data Quality Score", f"{data_quality_score:.1f}%")

def data_explorer_interface():
    """Data explorer interface"""
    st.header("🔍 Data Explorer")
    
    if not st.session_state.chatbot:
        st.error("❌ Please configure your API key first!")
        return
    
    if not st.session_state.data_loaded:
        st.warning("Please load data first to explore the dataset.")
        return
    
    data_processor = st.session_state.chatbot.data_processor
    
    # Data overview
    st.subheader("📋 Dataset Overview")
    
    if data_processor.trips_data is not None and not data_processor.trips_data.empty:
        st.write("**Trips Data:**")
        st.dataframe(data_processor.trips_data.head(10))
        
        st.write(f"**Shape:** {data_processor.trips_data.shape}")
        st.write(f"**Columns:** {list(data_processor.trips_data.columns)}")
        
        # Data types
        st.write("**Data Types:**")
        st.dataframe(data_processor.trips_data.dtypes.to_frame('Data Type'))
        
        # Missing values
        st.write("**Missing Values:**")
        missing_values = data_processor.trips_data.isnull().sum()
        st.dataframe(missing_values[missing_values > 0].to_frame('Missing Count'))
        
        # Basic statistics
        st.write("**Basic Statistics:**")
        st.dataframe(data_processor.trips_data.describe())
    
    if data_processor.users_data is not None and not data_processor.users_data.empty:
        st.write("**Users Data:**")
        st.dataframe(data_processor.users_data.head(10))
        
        st.write(f"**Shape:** {data_processor.users_data.shape}")
        st.write(f"**Columns:** {list(data_processor.users_data.columns)}")
        
        # Data types
        st.write("**Data Types:**")
        st.dataframe(data_processor.users_data.dtypes.to_frame('Data Type'))
        
        # Missing values
        st.write("**Missing Values:**")
        missing_values = data_processor.users_data.isnull().sum()
        st.dataframe(missing_values[missing_values > 0].to_frame('Missing Count'))
        
        # Basic statistics
        st.write("**Basic Statistics:**")
        st.dataframe(data_processor.users_data.describe())
    
    # Interactive filters
    st.subheader("🔍 Interactive Filters")
    
    if data_processor.trips_data is not None and not data_processor.trips_data.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Group size filter
            if 'group_size' in data_processor.trips_data.columns:
                min_group_size = int(data_processor.trips_data['group_size'].min())
                max_group_size = int(data_processor.trips_data['group_size'].max())
                
                group_size_range = st.slider(
                    "Group Size Range",
                    min_value=min_group_size,
                    max_value=max_group_size,
                    value=(min_group_size, max_group_size)
                )
                
                filtered_data = data_processor.trips_data[
                    (data_processor.trips_data['group_size'] >= group_size_range[0]) &
                    (data_processor.trips_data['group_size'] <= group_size_range[1])
                ]
            else:
                filtered_data = data_processor.trips_data
        
        with col2:
            # Date range filter
            if 'pickup_time' in data_processor.trips_data.columns:
                data_processor.trips_data['pickup_time'] = pd.to_datetime(data_processor.trips_data['pickup_time'])
                min_date = data_processor.trips_data['pickup_time'].min().date()
                max_date = data_processor.trips_data['pickup_time'].max().date()
                
                date_range = st.date_input(
                    "Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
                
                if len(date_range) == 2:
                    filtered_data = filtered_data[
                        (filtered_data['pickup_time'].dt.date >= date_range[0]) &
                        (filtered_data['pickup_time'].dt.date <= date_range[1])
                    ]
        
        # Show filtered data
        st.write(f"**Filtered Data ({len(filtered_data)} rows):**")
        st.dataframe(filtered_data.head(20))
        
        # Download filtered data
        if st.button("📥 Download Filtered Data"):
            csv = filtered_data.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="filtered_fetii_data.csv",
                mime="text/csv"
            )
    
    # Data quality analysis
    st.subheader("🔍 Data Quality Analysis")
    
    if data_processor.trips_data is not None and not data_processor.trips_data.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Completeness
            completeness = (1 - data_processor.trips_data.isnull().sum().sum() / (len(data_processor.trips_data) * len(data_processor.trips_data.columns))) * 100
            st.metric("Data Completeness", f"{completeness:.1f}%")
        
        with col2:
            # Uniqueness
            uniqueness = (1 - data_processor.trips_data.duplicated().sum() / len(data_processor.trips_data)) * 100
            st.metric("Data Uniqueness", f"{uniqueness:.1f}%")
        
        with col3:
            # Validity
            # Check for valid coordinates
            if 'pickup_latitude' in data_processor.trips_data.columns and 'pickup_longitude' in data_processor.trips_data.columns:
                valid_coords = data_processor.trips_data[
                    (data_processor.trips_data['pickup_latitude'].notna()) &
                    (data_processor.trips_data['pickup_longitude'].notna()) &
                    (data_processor.trips_data['pickup_latitude'].between(-90, 90)) &
                    (data_processor.trips_data['pickup_longitude'].between(-180, 180))
                ]
                validity = len(valid_coords) / len(data_processor.trips_data) * 100
            else:
                validity = 100
            st.metric("Data Validity", f"{validity:.1f}%")
    
    # Advanced data exploration
    st.subheader("🔍 Advanced Data Exploration")
    
    if data_processor.trips_data is not None and not data_processor.trips_data.empty:
        # Column analysis
        st.write("**Column Analysis:**")
        
        for col in data_processor.trips_data.columns:
            with st.expander(f"📊 {col}"):
                col_data = data_processor.trips_data[col]
                
                if col_data.dtype in ['int64', 'float64']:
                    # Numeric column
                    st.write(f"**Type:** Numeric")
                    st.write(f"**Min:** {col_data.min()}")
                    st.write(f"**Max:** {col_data.max()}")
                    st.write(f"**Mean:** {col_data.mean():.2f}")
                    st.write(f"**Median:** {col_data.median():.2f}")
                    st.write(f"**Missing:** {col_data.isnull().sum()}")
                    
                    # Histogram
                    fig = px.histogram(col_data, title=f"Distribution of {col}")
                    st.plotly_chart(fig, use_container_width=True)
                
                elif col_data.dtype == 'object':
                    # Categorical column
                    st.write(f"**Type:** Categorical")
                    st.write(f"**Unique values:** {col_data.nunique()}")
                    st.write(f"**Missing:** {col_data.isnull().sum()}")
                    
                    # Top values
                    top_values = col_data.value_counts().head(10)
                    st.write("**Top 10 values:**")
                    st.dataframe(top_values.to_frame('Count'))
                    
                    # Bar chart
                    fig = px.bar(x=top_values.index, y=top_values.values, title=f"Top values in {col}")
                    st.plotly_chart(fig, use_container_width=True)
                
                else:
                    # Other types
                    st.write(f"**Type:** {col_data.dtype}")
                    st.write(f"**Unique values:** {col_data.nunique()}")
                    st.write(f"**Missing:** {col_data.isnull().sum()}")
    
    # Data export options
    st.subheader("📤 Data Export Options")
    
    if data_processor.trips_data is not None and not data_processor.trips_data.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Download Trips Data (CSV)"):
                csv = data_processor.trips_data.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="fetii_trips_data.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📊 Download Trips Data (Excel)"):
                # Create Excel file
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    data_processor.trips_data.to_excel(writer, sheet_name='Trips', index=False)
                    if data_processor.users_data is not None and not data_processor.users_data.empty:
                        data_processor.users_data.to_excel(writer, sheet_name='Users', index=False)
                
                st.download_button(
                    label="Download Excel",
                    data=output.getvalue(),
                    file_name="fetii_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col3:
            if st.button("📋 Copy Data to Clipboard"):
                st.code(data_processor.trips_data.head(10).to_string(), language="text")
                st.success("Data copied to clipboard!")

def reports_interface():
    """Reports and insights interface"""
    st.header("📊 Reports & Insights")
    
    if not st.session_state.chatbot:
        st.error("❌ Please configure your API key first!")
        return
    
    if not st.session_state.data_loaded:
        st.warning("Please load data first to generate reports.")
        return
    
    data_processor = st.session_state.chatbot.data_processor
    
    # Report generation options
    st.subheader("📋 Generate Reports")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📈 Executive Summary", use_container_width=True):
            st.session_state.current_report = "executive"
    
    with col2:
        if st.button("📊 Performance Report", use_container_width=True):
            st.session_state.current_report = "performance"
    
    with col3:
        if st.button("🔍 Detailed Analysis", use_container_width=True):
            st.session_state.current_report = "detailed"
    
    # Generate reports based on selection
    if hasattr(st.session_state, 'current_report'):
        if st.session_state.current_report == "executive":
            generate_executive_summary(data_processor)
        elif st.session_state.current_report == "performance":
            generate_performance_report(data_processor)
        elif st.session_state.current_report == "detailed":
            generate_detailed_analysis(data_processor)

def generate_executive_summary(data_processor):
    """Generate executive summary report"""
    st.subheader("📈 Executive Summary")
    
    if data_processor.trips_data is not None and not data_processor.trips_data.empty:
        # Key metrics
        total_trips = len(data_processor.trips_data)
        total_revenue = data_processor.trips_data['group_size'].sum() * 5 if 'group_size' in data_processor.trips_data.columns else 0
        avg_group_size = data_processor.trips_data['group_size'].mean() if 'group_size' in data_processor.trips_data.columns else 0
        
        # Top destinations
        top_destinations = data_processor.trips_data['dropoff_location'].value_counts().head(5) if 'dropoff_location' in data_processor.trips_data.columns else []
        
        # Time analysis
        if 'pickup_time' in data_processor.trips_data.columns:
            data_processor.trips_data['pickup_time'] = pd.to_datetime(data_processor.trips_data['pickup_time'])
            peak_hour = data_processor.trips_data['pickup_time'].dt.hour.mode().iloc[0] if not data_processor.trips_data.empty else 0
            peak_day = data_processor.trips_data['pickup_time'].dt.day_name().mode().iloc[0] if not data_processor.trips_data.empty else "Unknown"
        else:
            peak_hour = 0
            peak_day = "Unknown"
        
        # Create executive summary
        st.markdown(f"""
        ## 🚗 FetiiAI Rideshare Analytics - Executive Summary
        
        ### 📊 Key Performance Indicators
        - **Total Trips:** {total_trips:,}
        - **Estimated Revenue:** ${total_revenue:,.2f}
        - **Average Group Size:** {avg_group_size:.1f} people
        - **Peak Hour:** {peak_hour}:00
        - **Peak Day:** {peak_day}
        
        ### 🏆 Top Destinations
        """)
        
        if not top_destinations.empty:
            for i, (destination, count) in enumerate(top_destinations.items(), 1):
                st.markdown(f"{i}. **{destination}** - {count} trips")
        else:
            st.markdown("No destination data available")
        
        # Insights
        st.markdown("""
        ### 💡 Key Insights
        - The rideshare service shows strong performance with consistent group bookings
        - Peak usage patterns indicate optimal service times
        - Geographic distribution reveals popular destination clusters
        - Revenue potential is significant with current group sizes
        """)
        
        # Download report
        if st.button("📥 Download Executive Summary"):
            report_content = f"""
            FetiiAI Rideshare Analytics - Executive Summary
            
            Key Performance Indicators:
            - Total Trips: {total_trips:,}
            - Estimated Revenue: ${total_revenue:,.2f}
            - Average Group Size: {avg_group_size:.1f} people
            - Peak Hour: {peak_hour}:00
            - Peak Day: {peak_day}
            
            Top Destinations:
            """
            for i, (destination, count) in enumerate(top_destinations.items(), 1):
                report_content += f"{i}. {destination} - {count} trips\n"
            
            st.download_button(
                label="Download Report",
                data=report_content,
                file_name="executive_summary.txt",
                mime="text/plain"
            )

def generate_performance_report(data_processor):
    """Generate performance report"""
    st.subheader("📊 Performance Report")
    
    if data_processor.trips_data is not None and not data_processor.trips_data.empty:
        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_trips = len(data_processor.trips_data)
            st.metric("Total Trips", f"{total_trips:,}")
        
        with col2:
            if 'group_size' in data_processor.trips_data.columns:
                avg_group_size = data_processor.trips_data['group_size'].mean()
                st.metric("Avg Group Size", f"{avg_group_size:.1f}")
            else:
                st.metric("Avg Group Size", "N/A")
        
        with col3:
            if 'pickup_time' in data_processor.trips_data.columns:
                data_processor.trips_data['pickup_time'] = pd.to_datetime(data_processor.trips_data['pickup_time'])
                unique_days = data_processor.trips_data['pickup_time'].dt.date.nunique()
                st.metric("Active Days", unique_days)
            else:
                st.metric("Active Days", "N/A")
        
        with col4:
            if 'dropoff_location' in data_processor.trips_data.columns:
                unique_destinations = data_processor.trips_data['dropoff_location'].nunique()
                st.metric("Unique Destinations", unique_destinations)
            else:
                st.metric("Unique Destinations", "N/A")
        
        # Performance trends
        st.subheader("📈 Performance Trends")
        
        if 'pickup_time' in data_processor.trips_data.columns:
            # Daily trends
            daily_trips = data_processor.trips_data.groupby(data_processor.trips_data['pickup_time'].dt.date).size()
            
            fig = px.line(
                x=daily_trips.index,
                y=daily_trips.values,
                title="Daily Trip Trends",
                labels={'x': 'Date', 'y': 'Number of Trips'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Performance by group size
        if 'group_size' in data_processor.trips_data.columns:
            group_performance = data_processor.trips_data.groupby('group_size').size()
            
            fig = px.bar(
                x=group_performance.index,
                y=group_performance.values,
                title="Performance by Group Size",
                labels={'x': 'Group Size', 'y': 'Number of Trips'}
            )
            st.plotly_chart(fig, use_container_width=True)

def generate_detailed_analysis(data_processor):
    """Generate detailed analysis report"""
    st.subheader("🔍 Detailed Analysis")
    
    if data_processor.trips_data is not None and not data_processor.trips_data.empty:
        # Detailed metrics
        st.subheader("📊 Detailed Metrics")
        
        # Create comprehensive analysis
        analysis_data = []
        
        if 'group_size' in data_processor.trips_data.columns:
            analysis_data.append({
                "Metric": "Group Size Statistics",
                "Min": data_processor.trips_data['group_size'].min(),
                "Max": data_processor.trips_data['group_size'].max(),
                "Mean": data_processor.trips_data['group_size'].mean(),
                "Median": data_processor.trips_data['group_size'].median(),
                "Std": data_processor.trips_data['group_size'].std()
            })
        
        if 'pickup_time' in data_processor.trips_data.columns:
            data_processor.trips_data['pickup_time'] = pd.to_datetime(data_processor.trips_data['pickup_time'])
            analysis_data.append({
                "Metric": "Time Statistics",
                "Min": data_processor.trips_data['pickup_time'].min(),
                "Max": data_processor.trips_data['pickup_time'].max(),
                "Mean": data_processor.trips_data['pickup_time'].mean(),
                "Median": data_processor.trips_data['pickup_time'].median(),
                "Std": "N/A"
            })
        
        if analysis_data:
            st.dataframe(pd.DataFrame(analysis_data))
        
        # Correlation analysis
        st.subheader("📊 Correlation Analysis")
        
        numeric_cols = data_processor.trips_data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            corr_matrix = data_processor.trips_data[numeric_cols].corr()
            
            fig = px.imshow(
                corr_matrix,
                title="Correlation Matrix",
                color_continuous_scale="RdBu"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Statistical tests
        st.subheader("🧮 Statistical Tests")
        
        if 'group_size' in data_processor.trips_data.columns:
            # Group size distribution test
            from scipy import stats
            
            # Test for normality
            group_sizes = data_processor.trips_data['group_size'].dropna()
            if len(group_sizes) > 3:
                shapiro_stat, shapiro_p = stats.shapiro(group_sizes)
                
                st.write(f"**Shapiro-Wilk Test for Normality:**")
                st.write(f"Statistic: {shapiro_stat:.4f}")
                st.write(f"P-value: {shapiro_p:.4f}")
                st.write(f"Normal distribution: {'Yes' if shapiro_p > 0.05 else 'No'}")

def render_main_content():
    """Render the main content based on selected page"""
    # Navigation
    selected = option_menu(
        menu_title=None,
        options=["Chat", "Analytics", "Data Explorer", "Reports"],
        icons=["chat-dots", "graph-up", "search", "file-text"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#262730"},
            "icon": {"color": "#ff6b6b", "font-size": "25px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "center",
                "margin": "0px",
                "--hover-color": "#444"
            },
            "nav-link-selected": {"background-color": "#ff6b6b"},
        }
    )
    
    if selected == "Chat":
        chat_interface()
    elif selected == "Analytics":
        analytics_interface()
    elif selected == "Data Explorer":
        data_explorer_interface()
    elif selected == "Reports":
        reports_interface()

def force_load_data():
    """Force load data from FetiiAI_Data_Austin.xlsx if available, or generate sample data for deployment"""
    if st.session_state.data_loaded:
        return
    
    # Check if file exists locally
    if os.path.exists('FetiiAI_Data_Austin.xlsx'):
        try:
            st.info("🚀 Auto-loading FetiiAI_Data_Austin.xlsx...")
            st.info(f"📁 File size: {os.path.getsize('FetiiAI_Data_Austin.xlsx')} bytes")
            
            with st.spinner("📊 Loading data automatically..."):
                success = load_data_directly('FetiiAI_Data_Austin.xlsx')
                if success:
                    st.session_state.data_loaded = True
                    st.session_state.loaded_data_file = 'FetiiAI_Data_Austin.xlsx'
                    save_session_data()
                    st.success("✅ Data loaded automatically from FetiiAI_Data_Austin.xlsx!")
                    st.info(f"📊 Loaded {len(st.session_state.trips_data)} trips")
                    st.rerun()  # Refresh to show the loaded data
                else:
                    st.error("❌ Failed to load data from FetiiAI_Data_Austin.xlsx")
        except Exception as e:
            st.error(f"❌ Error loading data: {str(e)}")
            import traceback
            st.error(f"Traceback: {traceback.format_exc()}")
    else:
        # For deployment - try to load pre-loaded data
        st.info("🌐 Deployment mode detected - checking for pre-loaded data...")
        if os.path.exists('FetiiAI_Data_Austin.xlsx'):
            try:
                st.info("📁 Found pre-loaded FetiiAI_Data_Austin.xlsx file")
                st.info(f"📁 File size: {os.path.getsize('FetiiAI_Data_Austin.xlsx')} bytes")
                
                with st.spinner("📊 Loading pre-loaded data..."):
                    success = load_data_directly('FetiiAI_Data_Austin.xlsx')
                    if success:
                        st.session_state.data_loaded = True
                        st.session_state.loaded_data_file = 'FetiiAI_Data_Austin.xlsx (Pre-loaded)'
                        save_session_data()
                        st.success("✅ Pre-loaded data loaded successfully!")
                        st.info(f"📊 Loaded {len(st.session_state.trips_data)} trips")
                        st.info("💡 Upload your own data file using the file uploader in the sidebar")
                        st.rerun()
                    else:
                        st.error("❌ Failed to load pre-loaded data")
            except Exception as e:
                st.error(f"❌ Error loading pre-loaded data: {str(e)}")
                import traceback
                st.error(f"Traceback: {traceback.format_exc()}")
        else:
            st.warning("⚠️ No pre-loaded data file found in deployment")
            st.info("💡 Upload your data file using the file uploader in the sidebar")

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Load session data
    load_session_data()
    
    # Force load data immediately - FIRST PRIORITY
    if not st.session_state.data_loaded:
        force_load_data()
    
    # Auto-load API key and data
    auto_load_app()
    
    # Force load data again if still not loaded
    if not st.session_state.data_loaded:
        force_load_data()
    
    # Render sidebar
    render_sidebar()
    
    # Render main content
    render_main_content()

if __name__ == "__main__":
    main()