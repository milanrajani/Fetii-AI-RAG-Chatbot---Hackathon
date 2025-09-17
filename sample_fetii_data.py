"""
Sample Fetii data generator that creates realistic data matching the actual Fetii dataset structure
This will help test the RAG functionality with known data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def create_sample_fetii_data():
    """Create sample data that matches the actual Fetii dataset structure"""
    
    # Set random seed for reproducible data
    np.random.seed(42)
    random.seed(42)
    
    # Austin destinations
    destinations = [
        "Moody Center", "Downtown Austin", "University of Texas", 
        "6th Street", "Rainey Street", "Zilker Park", "Barton Springs",
        "South by Southwest", "Domain", "South Austin", "East Austin",
        "West Campus", "Hyde Park", "Clarksville", "South Lamar"
    ]
    
    pickup_locations = [
        "Downtown Austin", "University of Texas", "South Austin",
        "East Austin", "West Campus", "Domain", "North Austin",
        "South Lamar", "Hyde Park", "Clarksville"
    ]
    
    # Generate 500 trips
    num_trips = 500
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
        
        # Destinations (Moody Center gets more trips)
        destination_weights = [4, 3, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]  # Moody Center gets highest weight
        destination = random.choices(destinations, weights=destination_weights)[0]
        
        pickup_location = random.choice(pickup_locations)
        
        # Generate coordinates (Austin area)
        pickup_lat = 30.2672 + random.uniform(-0.1, 0.1)
        pickup_lon = -97.7431 + random.uniform(-0.1, 0.1)
        dropoff_lat = 30.2672 + random.uniform(-0.1, 0.1)
        dropoff_lon = -97.7431 + random.uniform(-0.1, 0.1)
        
        trip = {
            'Trip ID': f"TRIP_{i+1:06d}",
            'Booking User ID': f"USER_{random.randint(1, 100):06d}",
            'Pick Up Lattittude': pickup_lat,
            'Pick Up longitude': pickup_lon,
            'Drop off latitude': dropoff_lat,
            'Drop off longitude': dropoff_lon,
            'Pick Up Address': pickup_location,
            'Drop off Address': destination,
            'Trip Date and Time': pickup_time,
            'Total Passengers': group_size
        }
        
        trips_data.append(trip)
    
    trips_df = pd.DataFrame(trips_data)
    
    # Generate rider data (Checked in User ID's)
    rider_data = []
    for i, trip in enumerate(trips_data):
        trip_id = trip['Trip ID']
        booking_user = trip['Booking User ID']
        group_size = trip['Total Passengers']
        
        # Add the booking user
        rider_data.append({
            'Trip ID': trip_id,
            'User ID': booking_user
        })
        
        # Add additional riders if group size > 1
        for j in range(1, group_size):
            rider_data.append({
                'Trip ID': trip_id,
                'User ID': f"USER_{random.randint(1, 100):06d}"
            })
    
    riders_df = pd.DataFrame(rider_data)
    
    # Generate customer demographics
    unique_users = set()
    for trip in trips_data:
        unique_users.add(trip['Booking User ID'])
    for rider in rider_data:
        unique_users.add(rider['User ID'])
    
    demographics_data = []
    for user_id in unique_users:
        # Age distribution (more young people)
        age = random.choices(range(18, 70), weights=[4, 4, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])[0]
        
        demographics_data.append({
            'User ID': user_id,
            'Age': age
        })
    
    demographics_df = pd.DataFrame(demographics_data)
    
    return trips_df, riders_df, demographics_df

def save_sample_excel():
    """Create and save sample Excel file with multiple tabs"""
    print("Creating sample Fetii data...")
    
    trips_df, riders_df, demographics_df = create_sample_fetii_data()
    
    # Create Excel file with multiple tabs
    with pd.ExcelWriter('sample_fetii_data.xlsx', engine='openpyxl') as writer:
        trips_df.to_excel(writer, sheet_name='Trip data', index=False)
        riders_df.to_excel(writer, sheet_name='Checked in User ID\'s', index=False)
        demographics_df.to_excel(writer, sheet_name='Customer Demographics', index=False)
    
    print(f"✅ Created sample_fetii_data.xlsx with:")
    print(f"   - {len(trips_df)} trips")
    print(f"   - {len(riders_df)} rider records")
    print(f"   - {len(demographics_df)} user demographics")
    
    # Show some statistics
    print(f"\n📊 Sample Statistics:")
    print(f"   - Moody Center trips: {len(trips_df[trips_df['Drop off Address'] == 'Moody Center'])}")
    print(f"   - Average group size: {trips_df['Total Passengers'].mean():.2f}")
    print(f"   - Date range: {trips_df['Trip Date and Time'].min()} to {trips_df['Trip Date and Time'].max()}")
    print(f"   - Age range: {demographics_df['Age'].min()} to {demographics_df['Age'].max()}")
    
    return trips_df, riders_df, demographics_df

if __name__ == "__main__":
    save_sample_excel()
