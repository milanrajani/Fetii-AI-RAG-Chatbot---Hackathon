import streamlit as st

st.set_page_config(
    page_title="FetiiAI Test",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 FetiiAI - GPT-Powered Rideshare Analytics")
st.markdown("Ask questions about Austin rideshare data and get intelligent insights")

st.success("✅ App is working! This is a test version.")

if st.button("Test Button"):
    st.write("Button clicked! The app is responsive.")

st.info("If you can see this, the basic Streamlit app is working.")



