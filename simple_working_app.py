import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu

# Page configuration
st.set_page_config(
    page_title="FetiiAI - GPT-Powered Rideshare Analytics",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .main .block-container h1 {
        color: #ffffff;
    }
    .main .block-container h2 {
        color: #ffffff;
    }
    .main .block-container p {
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function"""
    # Header
    st.title("🚗 FetiiAI - GPT-Powered Rideshare Analytics")
    st.markdown("Ask questions about Austin rideshare data and get intelligent insights")
    
    # Test that basic rendering works
    st.success("✅ App is working!")
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        api_key = st.text_input("OpenAI API Key", type="password")
        
        st.header("📊 Data Upload")
        data_file = st.file_uploader("Upload Fetii Data", type=['xlsx', 'xls'])
        
        if st.button("Load Sample Data"):
            st.success("Sample data loaded!")
    
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
        st.subheader("Ask FetiiAI Anything")
        user_input = st.text_input("Enter your question:")
        if st.button("Send"):
            st.write("You asked:", user_input)
            st.write("This is where the AI response would go!")
    
    elif selected == "📈 Analytics":
        st.subheader("Analytics Dashboard")
        st.write("Analytics content would go here!")
        
        # Sample chart
        data = pd.DataFrame({
            'Destination': ['Moody Center', 'Downtown', 'UT Campus', '6th Street'],
            'Trips': [45, 32, 28, 15]
        })
        fig = px.bar(data, x='Destination', y='Trips', title="Top Destinations")
        st.plotly_chart(fig, use_container_width=True)
    
    elif selected == "📊 Data Explorer":
        st.subheader("Data Explorer")
        st.write("Data explorer content would go here!")
        
        # Sample data table
        sample_data = pd.DataFrame({
            'Trip ID': ['TRIP_001', 'TRIP_002', 'TRIP_003'],
            'Destination': ['Moody Center', 'Downtown', 'UT Campus'],
            'Group Size': [4, 2, 6]
        })
        st.dataframe(sample_data)
    
    elif selected == "❓ Help":
        st.subheader("Help & Documentation")
        st.write("""
        ## 🚗 FetiiAI - GPT-Powered Rideshare Analytics
        
        Welcome to FetiiAI! This application helps you analyze Austin rideshare data.
        
        ### Getting Started:
        1. Enter your OpenAI API key in the sidebar
        2. Upload your data file or use sample data
        3. Start asking questions!
        
        ### Example Questions:
        - "How many groups went to Moody Center last month?"
        - "What are the top drop-off spots for 18–24 year-olds?"
        - "When do large groups typically ride downtown?"
        """)

if __name__ == "__main__":
    main()

