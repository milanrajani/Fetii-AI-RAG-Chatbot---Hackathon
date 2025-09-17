import streamlit as st

st.set_page_config(
    page_title="FetiiAI - Test Deployment",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 FetiiAI - Test Deployment")
st.write("This is a test to verify the deployment is working correctly.")

# Test imports
try:
    import pandas as pd
    st.success("✅ Pandas imported successfully")
except Exception as e:
    st.error(f"❌ Pandas import failed: {e}")

try:
    import plotly.express as px
    st.success("✅ Plotly imported successfully")
except Exception as e:
    st.error(f"❌ Plotly import failed: {e}")

try:
    from streamlit_chat import message
    st.success("✅ streamlit-chat imported successfully")
except Exception as e:
    st.error(f"❌ streamlit-chat import failed: {e}")

try:
    from streamlit_option_menu import option_menu
    st.success("✅ streamlit-option-menu imported successfully")
except Exception as e:
    st.error(f"❌ streamlit-option-menu import failed: {e}")

# Test custom imports
try:
    from chatbot import FetiiChatbot
    st.success("✅ FetiiChatbot imported successfully")
except Exception as e:
    st.error(f"❌ FetiiChatbot import failed: {e}")

try:
    from data_processor import FetiiDataProcessor
    st.success("✅ FetiiDataProcessor imported successfully")
except Exception as e:
    st.error(f"❌ FetiiDataProcessor import failed: {e}")

# Test file existence
import os
if os.path.exists('FetiiAI_Data_Austin.xlsx'):
    st.success("✅ FetiiAI_Data_Austin.xlsx found")
else:
    st.error("❌ FetiiAI_Data_Austin.xlsx not found")

# Test environment variables
import os
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    st.success("✅ OPENAI_API_KEY environment variable found")
else:
    st.warning("⚠️ OPENAI_API_KEY environment variable not found")

st.write("---")
st.write("If all tests pass, the deployment environment is working correctly.")
st.write("If any tests fail, that's likely the cause of the deployment issues.")
