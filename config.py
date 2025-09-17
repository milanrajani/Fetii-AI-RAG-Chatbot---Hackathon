import os

# Load environment variables (with fallback to config.txt)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Fallback to config.txt if environment variable not found
if not OPENAI_API_KEY:
    try:
        with open('config.txt', 'r') as f:
            OPENAI_API_KEY = f.read().strip()
    except FileNotFoundError:
        pass

# Streamlit configuration
STREAMLIT_CONFIG = {
    "page_title": "FetiiAI - GPT-Powered Rideshare Analytics",
    "page_icon": "🚗",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Sample data structure for Fetii rideshare data
SAMPLE_DATA_STRUCTURE = {
    "trips": {
        "columns": [
            "trip_id", "user_id", "group_size", "pickup_location", 
            "dropoff_location", "pickup_time", "dropoff_time", 
            "date", "day_of_week", "age_group", "destination_category"
        ]
    },
    "users": {
        "columns": [
            "user_id", "age", "age_group", "registration_date", 
            "total_trips", "preferred_destinations"
        ]
    }
}

# Common destinations in Austin
AUSTIN_DESTINATIONS = [
    "Moody Center", "Downtown Austin", "South by Southwest", 
    "University of Texas", "Zilker Park", "Barton Springs", 
    "6th Street", "Rainey Street", "Domain", "South Austin",
    "East Austin", "West Campus", "Hyde Park", "Clarksville"
]
