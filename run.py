#!/usr/bin/env python3
"""
FetiiAI Application Runner
Simple script to run the Streamlit application
"""

import subprocess
import sys
import os

def main():
    """Run the FetiiAI application"""
    print("🚗 Starting FetiiAI - GPT-Powered Rideshare Analytics")
    print("=" * 60)
    
    # Check if streamlit is installed
    try:
        import streamlit
        print("✅ Streamlit is installed")
    except ImportError:
        print("❌ Streamlit not found. Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("⚠️  No .env file found. Creating template...")
        with open(".env", "w") as f:
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
        print("📝 Please edit .env file and add your OpenAI API key")
    
    # Run the application
    print("🚀 Launching application...")
    print("📱 Open your browser to http://localhost:8501")
    print("=" * 60)
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {e}")

if __name__ == "__main__":
    main()
