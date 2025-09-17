# FetiiAI - GPT-Powered Rideshare Analytics

A comprehensive Streamlit application for analyzing rideshare data with AI-powered insights.

## Features

- 🤖 **AI-Powered Chat Interface** - Ask questions about your data
- 📊 **Interactive Analytics** - Visualize trip patterns, destinations, and user behavior
- 🔍 **Data Explorer** - Explore and filter your data with advanced tools
- 📈 **Automated Reports** - Generate executive summaries and performance reports
- 🚗 **Rideshare-Specific Metrics** - Group size analysis, destination patterns, time-based insights

## Quick Start

1. **Set up your API key:**
   - Create a `config.txt` file
   - Add your OpenAI API key: `OPENAI_API_KEY=your_key_here`
   - Or set the environment variable: `OPENAI_API_KEY`

2. **Prepare your data:**
   - Place your Excel file as `FetiiAI_Data_Austin.xlsx` in the project directory
   - The app will automatically load this file on startup

3. **Run the app:**
   ```bash
   streamlit run working_app.py
   ```

## Data Format

The app expects Excel files with the following structure:
- **Trip Data**: Trip ID, User ID, Group Size, Pickup/Dropoff Locations, Times, etc.
- **User Data**: User ID, Age, Registration Date, Trip History, etc.

## Deployment

This app is ready for deployment on:
- Streamlit Community Cloud
- Heroku
- Railway
- AWS/GCP/Azure

## Requirements

See `requirements.txt` for all dependencies.

## Support

For issues or questions, please check the documentation or create an issue.