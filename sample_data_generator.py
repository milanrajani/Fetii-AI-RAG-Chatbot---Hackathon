"""
Sample data generator for testing FetiiAI application
Generates realistic rideshare data for Austin, TX
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_sample_data(num_trips=1000, num_users=200):
    """Generate sample Fetii rideshare data"""
    
    # Austin destinations
    destinations = [
        "Moody Center", "Downtown Austin", "South by Southwest", 
        "University of Texas", "Zilker Park", "Barton Springs", 
        "6th Street", "Rainey Street", "Domain", "South Austin",
        "East Austin", "West Campus", "Hyde Park", "Clarksville",
        "South Lamar", "North Austin", "Cedar Park", "Round Rock"
    ]
    
    pickup_locations = [
        "Downtown Austin", "University of Texas", "South Austin",
        "East Austin", "West Campus", "Domain", "North Austin",
        "South Lamar", "Hyde Park", "Clarksville"
    ]
    
    age_groups = ["18-24", "25-34", "35-44", "45-54", "55+"]
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Generate trips data
    trips_data = []
    
    for i in range(num_trips):
        # Random date in the last 6 months
        start_date = datetime.now() - timedelta(days=random.randint(1, 180))
        
        # Random time (more trips in evening and weekend)
        if random.random() < 0.3:  # Weekend
            hour = random.choices(range(24), weights=[1]*6 + [2]*4 + [3]*6 + [2]*4 + [1]*4)[0]
        else:  # Weekday
            hour = random.choices(range(24), weights=[1]*7 + [3]*2 + [1]*2 + [2]*3 + [1]*10)[0]
        
        pickup_time = start_date.replace(hour=hour, minute=random.randint(0, 59))
        
        # Trip duration (10-60 minutes)
        duration_minutes = random.randint(10, 60)
        dropoff_time = pickup_time + timedelta(minutes=duration_minutes)
        
        # Group size (1-8 people, weighted towards smaller groups)
        group_size = random.choices(range(1, 9), weights=[3, 2, 2, 1, 1, 0.5, 0.3, 0.2])[0]
        
        # Age group (weighted towards younger users)
        age_group = random.choices(age_groups, weights=[4, 3, 2, 1, 0.5])[0]
        
        # Destinations (some more popular than others)
        destination = random.choices(destinations, weights=[
            2, 3, 1, 4, 2, 2, 3, 2, 1, 2, 2, 3, 1, 1, 2, 1, 1, 1
        ])[0]
        
        pickup_location = random.choice(pickup_locations)
        
        trip = {
            'trip_id': f"TRIP_{i+1:06d}",
            'user_id': f"USER_{random.randint(1, num_users):06d}",
            'group_size': group_size,
            'pickup_location': pickup_location,
            'dropoff_location': destination,
            'pickup_time': pickup_time,
            'dropoff_time': dropoff_time,
            'date': pickup_time.date(),
            'day_of_week': pickup_time.strftime('%A'),
            'age_group': age_group,
            'destination_category': categorize_destination(destination)
        }
        
        trips_data.append(trip)
    
    trips_df = pd.DataFrame(trips_data)
    
    # Generate users data
    users_data = []
    unique_users = trips_df['user_id'].unique()
    
    for user_id in unique_users:
        user_trips = trips_df[trips_df['user_id'] == user_id]
        age_group = user_trips['age_group'].iloc[0]
        
        # Generate age based on age group
        if age_group == "18-24":
            age = random.randint(18, 24)
        elif age_group == "25-34":
            age = random.randint(25, 34)
        elif age_group == "35-44":
            age = random.randint(35, 44)
        elif age_group == "45-54":
            age = random.randint(45, 54)
        else:
            age = random.randint(55, 70)
        
        # Registration date (before first trip)
        first_trip = user_trips['date'].min()
        reg_date = first_trip - timedelta(days=random.randint(1, 365))
        
        # Preferred destinations
        top_destinations = user_trips['dropoff_location'].value_counts().head(3)
        preferred_destinations = ", ".join(top_destinations.index.tolist())
        
        user = {
            'user_id': user_id,
            'age': age,
            'age_group': age_group,
            'registration_date': reg_date,
            'total_trips': len(user_trips),
            'preferred_destinations': preferred_destinations
        }
        
        users_data.append(user)
    
    users_df = pd.DataFrame(users_data)
    
    return trips_df, users_df

def categorize_destination(destination):
    """Categorize destinations into groups"""
    entertainment = ["Moody Center", "6th Street", "Rainey Street", "South by Southwest"]
    education = ["University of Texas", "West Campus"]
    recreation = ["Zilker Park", "Barton Springs"]
    shopping = ["Domain", "South Lamar"]
    residential = ["South Austin", "East Austin", "North Austin", "Hyde Park", "Clarksville", "Cedar Park", "Round Rock"]
    business = ["Downtown Austin"]
    
    if destination in entertainment:
        return "Entertainment"
    elif destination in education:
        return "Education"
    elif destination in recreation:
        return "Recreation"
    elif destination in shopping:
        return "Shopping"
    elif destination in residential:
        return "Residential"
    elif destination in business:
        return "Business"
    else:
        return "Other"

def save_sample_data():
    """Generate and save sample data to Excel files"""
    print("Generating sample data...")
    
    trips_df, users_df = generate_sample_data(num_trips=2000, num_users=300)
    
    # Save to Excel files
    trips_df.to_excel("sample_trips_data.xlsx", index=False)
    users_df.to_excel("sample_users_data.xlsx", index=False)
    
    print(f"✅ Generated {len(trips_df)} trips and {len(users_df)} users")
    print("📁 Files saved:")
    print("   - sample_trips_data.xlsx")
    print("   - sample_users_data.xlsx")
    
    # Print summary
    print("\n📊 Data Summary:")
    print(f"   - Date range: {trips_df['date'].min()} to {trips_df['date'].max()}")
    print(f"   - Average group size: {trips_df['group_size'].mean():.2f}")
    print(f"   - Most popular destination: {trips_df['dropoff_location'].mode().iloc[0]}")
    print(f"   - Peak hour: {trips_df['pickup_time'].dt.hour.mode().iloc[0]}:00")

if __name__ == "__main__":
    save_sample_data()
