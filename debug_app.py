import streamlit as st

st.title("🚗 FetiiAI - GPT-Powered Rideshare Analytics")
st.markdown("Ask questions about Austin rideshare data and get intelligent insights")

st.info("This is a debug version to test rendering")

# Test sidebar
with st.sidebar:
    st.header("Debug Sidebar")
    st.write("Sidebar is working!")

# Test main content
st.header("Debug Main Content")
st.write("Main content is working!")

# Test columns
col1, col2 = st.columns(2)
with col1:
    st.write("Column 1")
with col2:
    st.write("Column 2")

st.success("Debug app is working!")

