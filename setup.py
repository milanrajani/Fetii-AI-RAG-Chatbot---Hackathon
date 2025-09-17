#!/usr/bin/env python3
"""
FetiiAI Setup Script
This script helps you configure the FetiiAI app for auto-loading.
"""

import os

def create_config_file():
    """Create a config.txt file with API key"""
    print("🔧 FetiiAI Setup")
    print("=" * 50)
    
    # Get API key from user
    api_key = input("Enter your OpenAI API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Exiting.")
        return False
    
    # Create config.txt file
    try:
        with open('config.txt', 'w') as f:
            f.write(api_key)
        print("✅ Config file created successfully!")
        print("📁 File: config.txt")
        print("🔑 API key saved securely")
        return True
    except Exception as e:
        print(f"❌ Error creating config file: {e}")
        return False

def check_data_file():
    """Check if data file exists"""
    data_file = "FetiiAI_Data_Austin.xlsx"
    if os.path.exists(data_file):
        print(f"✅ Data file found: {data_file}")
        return True
    else:
        print(f"⚠️  Data file not found: {data_file}")
        print("💡 Make sure the Excel file is in the same directory as this script")
        return False

def main():
    """Main setup function"""
    print("🚀 Welcome to FetiiAI Setup!")
    print()
    
    # Check data file
    data_exists = check_data_file()
    
    # Create config file
    config_created = create_config_file()
    
    print()
    print("📋 Setup Summary:")
    print(f"   Data file: {'✅ Found' if data_exists else '❌ Not found'}")
    print(f"   Config file: {'✅ Created' if config_created else '❌ Failed'}")
    
    if config_created and data_exists:
        print()
        print("🎉 Setup complete! You can now run the app with:")
        print("   streamlit run app.py")
        print()
        print("The app will automatically load your API key and data!")
    else:
        print()
        print("⚠️  Setup incomplete. Please:")
        if not data_exists:
            print("   - Place FetiiAI_Data_Austin.xlsx in the app directory")
        if not config_created:
            print("   - Run this script again to create config.txt")
        print("   - Or use manual setup in the app sidebar")

if __name__ == "__main__":
    main()
