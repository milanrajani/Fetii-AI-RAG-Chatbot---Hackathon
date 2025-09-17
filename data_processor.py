import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional
import streamlit as st

class FetiiDataProcessor:
    """Process and analyze Fetii rideshare data"""
    
    def __init__(self):
        self.trips_data = None
        self.users_data = None
        self.processed_data = None
    
    def load_data(self, data_file: str = None, trips_file: str = None, users_file: str = None) -> bool:
        """Load data from Excel files - supports both single file with tabs or separate files"""
        try:
            # Check if file exists and is accessible
            if data_file:
                import os
                import shutil
                import tempfile
                
                if not os.path.exists(data_file):
                    st.error(f"❌ File not found: {data_file}")
                    return False
                
                # Check file permissions
                if not os.access(data_file, os.R_OK):
                    st.error(f"❌ Permission denied: Cannot read {data_file}")
                    st.info("💡 **Solutions:**")
                    st.info("1. Close Excel if the file is open")
                    st.info("2. Check file permissions (right-click → Properties → Security)")
                    st.info("3. Try copying the file to a different location")
                    st.info("4. Use the file uploader below as an alternative")
                    
                    # Try to create a copy in temp directory
                    try:
                        st.info("🔄 Attempting to create a temporary copy...")
                        temp_dir = tempfile.mkdtemp()
                        temp_file = os.path.join(temp_dir, "FetiiAI_Data_Austin.xlsx")
                        shutil.copy2(data_file, temp_file)
                        data_file = temp_file
                        st.success("✅ Created temporary copy successfully!")
                    except Exception as copy_error:
                        st.error(f"❌ Could not create temporary copy: {str(copy_error)}")
                        return False
                
                # Try to open the file
                try:
                    excel_file = pd.ExcelFile(data_file)
                except PermissionError as e:
                    st.error(f"❌ Permission denied: {str(e)}")
                    st.info("💡 Please close the Excel file if it's open and try again")
                    return False
                except Exception as e:
                    st.error(f"❌ Error opening file: {str(e)}")
                    return False
                
                # Load Trip data from 'Trip Data' tab (note the capital D)
                if 'Trip Data' in excel_file.sheet_names:
                    self.trips_data = pd.read_excel(data_file, sheet_name='Trip Data')
                elif 'Trip data' in excel_file.sheet_names:
                    self.trips_data = pd.read_excel(data_file, sheet_name='Trip data')
                elif 'trips' in [name.lower() for name in excel_file.sheet_names]:
                    # Fallback: look for any sheet with 'trips' in the name
                    trips_sheet = [name for name in excel_file.sheet_names if 'trip' in name.lower()][0]
                    self.trips_data = pd.read_excel(data_file, sheet_name=trips_sheet)
                
                # Load Rider data from 'Checked in User ID's' tab
                rider_data = None
                if 'Checked in User ID\'s' in excel_file.sheet_names:
                    rider_data = pd.read_excel(data_file, sheet_name='Checked in User ID\'s')
                elif 'rider' in [name.lower() for name in excel_file.sheet_names]:
                    # Fallback: look for any sheet with 'rider' in the name
                    rider_sheet = [name for name in excel_file.sheet_names if 'rider' in name.lower()][0]
                    rider_data = pd.read_excel(data_file, sheet_name=rider_sheet)
                
                # Load User demographics from 'Customer Demographics' tab
                if 'Customer Demographics' in excel_file.sheet_names:
                    self.users_data = pd.read_excel(data_file, sheet_name='Customer Demographics')
                elif 'demo' in [name.lower() for name in excel_file.sheet_names]:
                    # Fallback: look for any sheet with 'demo' in the name
                    demo_sheet = [name for name in excel_file.sheet_names if 'demo' in name.lower()][0]
                    self.users_data = pd.read_excel(data_file, sheet_name=demo_sheet)
                
                # Show available tabs
            
            # Legacy method: separate files (for backward compatibility)
            elif trips_file or users_file:
                if trips_file:
                    self.trips_data = pd.read_excel(trips_file)
                
                if users_file:
                    self.users_data = pd.read_excel(users_file)
            
            if self.trips_data is not None:
                self._preprocess_data()
                # Merge trips with user demographics for age-based analysis
                self._merge_trips_with_demographics()
            return True
        except Exception as e:
            st.error(f"❌ Error loading data: {str(e)}")
            return False
    
    def _preprocess_data(self):
        """Preprocess the loaded data"""
        if self.trips_data is not None:
            # Map actual Fetii column names to expected names
            self._map_fetii_columns()
            
            # Convert datetime columns
            if 'pickup_time' in self.trips_data.columns:
                self.trips_data['pickup_time'] = pd.to_datetime(self.trips_data['pickup_time'])
            if 'dropoff_time' in self.trips_data.columns:
                self.trips_data['dropoff_time'] = pd.to_datetime(self.trips_data['dropoff_time'])
            if 'date' in self.trips_data.columns:
                self.trips_data['date'] = pd.to_datetime(self.trips_data['date'])
            
            # Extract additional features
            if 'pickup_time' in self.trips_data.columns:
                self.trips_data['hour'] = self.trips_data['pickup_time'].dt.hour
                self.trips_data['day_of_week'] = self.trips_data['pickup_time'].dt.day_name()
                self.trips_data['month'] = self.trips_data['pickup_time'].dt.month
                self.trips_data['year'] = self.trips_data['pickup_time'].dt.year
            
            # Create trip duration
            if 'pickup_time' in self.trips_data.columns and 'dropoff_time' in self.trips_data.columns:
                self.trips_data['trip_duration'] = (
                    self.trips_data['dropoff_time'] - self.trips_data['pickup_time']
                ).dt.total_seconds() / 60  # in minutes
    
    def _map_fetii_columns(self):
        """Map Fetii dataset column names to expected names"""
        if self.trips_data is not None:
            # Create a mapping dictionary for the actual Fetii column names
            column_mapping = {}
            
            # Map Trip data columns based on your actual dataset
            for col in self.trips_data.columns:
                col_lower = col.lower().strip()
                
                # Trip ID mapping
                if col_lower == 'trip id':
                    column_mapping[col] = 'trip_id'
                # Booking User ID mapping
                elif col_lower == 'booking user id':
                    column_mapping[col] = 'user_id'
                # Pickup coordinates
                elif col_lower == 'pick up lattittude' or col_lower == 'pick up latitude':
                    column_mapping[col] = 'pickup_latitude'
                elif col_lower == 'pick up longitude':
                    column_mapping[col] = 'pickup_longitude'
                # Dropoff coordinates
                elif col_lower == 'drop off latitude':
                    column_mapping[col] = 'dropoff_latitude'
                elif col_lower == 'drop off longitude':
                    column_mapping[col] = 'dropoff_longitude'
                # Addresses
                elif col_lower == 'pick up address':
                    column_mapping[col] = 'pickup_location'
                elif col_lower == 'drop off address':
                    column_mapping[col] = 'dropoff_location'
                # Date and time
                elif col_lower == 'trip date and time':
                    column_mapping[col] = 'pickup_time'
                # Total passengers
                elif col_lower == 'total passengers':
                    column_mapping[col] = 'group_size'
            
            # Apply the mapping
            self.trips_data = self.trips_data.rename(columns=column_mapping)
            
        
        if self.users_data is not None:
            # Map user data columns based on Customer Demographics
            user_column_mapping = {}
            
            for col in self.users_data.columns:
                col_lower = col.lower().strip()
                
                if col_lower == 'user id':
                    user_column_mapping[col] = 'user_id'
                elif col_lower == 'age':
                    user_column_mapping[col] = 'age'
            
            # Apply the mapping
            self.users_data = self.users_data.rename(columns=user_column_mapping)
            
            # Create age_group from age if not present
            if 'age' in self.users_data.columns and 'age_group' not in self.users_data.columns:
                self.users_data['age_group'] = self.users_data['age'].apply(self._categorize_age)
            
            if user_column_mapping:
                self.users_data = self.users_data.rename(columns=user_column_mapping)
    
    def _categorize_age(self, age):
        """Categorize age into age groups"""
        if pd.isna(age):
            return "Unknown"
        elif age < 18:
            return "Under 18"
        elif 18 <= age <= 24:
            return "18-24"
        elif 25 <= age <= 34:
            return "25-34"
        elif 35 <= age <= 44:
            return "35-44"
        elif 45 <= age <= 54:
            return "45-54"
        else:
            return "55+"
    
    def _merge_trips_with_demographics(self):
        """Merge trips data with user demographics to enable age-based analysis"""
        if self.trips_data is not None and self.users_data is not None:
            # Merge trips with user demographics based on user_id
            self.trips_data = self.trips_data.merge(
                self.users_data[['user_id', 'age', 'age_group']], 
                on='user_id', 
                how='left'
            )
    
    def get_trips_by_destination(self, destination: str, month: int = None) -> pd.DataFrame:
        """Get trips to a specific destination"""
        if self.trips_data is None:
            return pd.DataFrame()
        
        filtered_data = self.trips_data.copy()
        
        # Filter by destination (case-insensitive)
        if 'dropoff_location' in filtered_data.columns:
            filtered_data = filtered_data[
                filtered_data['dropoff_location'].str.contains(destination, case=False, na=False)
            ]
        
        # Filter by month if specified
        if month and 'month' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['month'] == month]
        elif month and 'pickup_time' in filtered_data.columns:
            # Extract month from pickup_time if month column doesn't exist
            filtered_data['month'] = pd.to_datetime(filtered_data['pickup_time']).dt.month
            filtered_data = filtered_data[filtered_data['month'] == month]
        
        return filtered_data
    
    def get_trips_by_age_group(self, age_group: str, day_of_week: str = None) -> pd.DataFrame:
        """Get trips by age group"""
        if self.trips_data is None:
            return pd.DataFrame()
        
        filtered_data = self.trips_data.copy()
        
        # Filter by age group
        if 'age_group' in filtered_data.columns:
            filtered_data = filtered_data[
                filtered_data['age_group'].str.contains(age_group, case=False, na=False)
            ]
        
        # Filter by day of week if specified
        if day_of_week and 'day_of_week' in filtered_data.columns:
            filtered_data = filtered_data[
                filtered_data['day_of_week'].str.contains(day_of_week, case=False, na=False)
            ]
        
        return filtered_data
    
    def get_large_group_trips(self, min_group_size: int = 6, day_of_week: str = None) -> pd.DataFrame:
        """Get trips with large groups"""
        if self.trips_data is None:
            return pd.DataFrame()
        
        filtered_data = self.trips_data.copy()
        
        # Filter by group size
        if 'group_size' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['group_size'] >= min_group_size]
        
        # Filter by day of week if specified
        if day_of_week and 'day_of_week' in filtered_data.columns:
            filtered_data = filtered_data[
                filtered_data['day_of_week'].str.contains(day_of_week, case=False, na=False)
            ]
        
        return filtered_data
    
    def get_age_group_destinations(self, age_group: str, day_of_week: str = None) -> pd.DataFrame:
        """Get top destinations for a specific age group"""
        if self.trips_data is None:
            return pd.DataFrame()
        
        filtered_data = self.trips_data.copy()
        
        # Filter by age group
        if 'age_group' in filtered_data.columns:
            filtered_data = filtered_data[
                filtered_data['age_group'].str.contains(age_group, case=False, na=False)
            ]
        
        # Filter by day of week if specified
        if day_of_week and 'day_of_week' in filtered_data.columns:
            filtered_data = filtered_data[
                filtered_data['day_of_week'].str.contains(day_of_week, case=False, na=False)
            ]
        
        # Get top destinations for this age group
        if 'dropoff_location' in filtered_data.columns:
            return filtered_data['dropoff_location'].value_counts().head(10)
        else:
            return pd.DataFrame()
    
    def get_top_destinations(self, limit: int = 10) -> pd.DataFrame:
        """Get top destinations by trip count"""
        if self.trips_data is None or 'dropoff_location' not in self.trips_data.columns:
            return pd.DataFrame()
        
        result = self.trips_data['dropoff_location'].value_counts().head(limit)
        return result
    
    def get_hourly_distribution(self, day_of_week: str = None) -> pd.DataFrame:
        """Get hourly trip distribution"""
        if self.trips_data is None or 'hour' not in self.trips_data.columns:
            return pd.DataFrame()
        
        filtered_data = self.trips_data.copy()
        
        if day_of_week and 'day_of_week' in filtered_data.columns:
            filtered_data = filtered_data[
                filtered_data['day_of_week'].str.contains(day_of_week, case=False, na=False)
            ]
        
        return filtered_data['hour'].value_counts().sort_index()
    
    def create_visualization(self, chart_type: str, data: pd.DataFrame, **kwargs) -> go.Figure:
        """Create various types of visualizations"""
        if data.empty:
            return go.Figure()
        
        try:
            # Ensure data is properly formatted
            if isinstance(data, pd.Series):
                # Convert Series to DataFrame for consistent handling
                df = data.reset_index()
                df.columns = ['category', 'value']
            else:
                df = data.copy()
            
            # Remove any NaN values
            df = df.dropna()
            
            if df.empty:
                return go.Figure()
            
            if chart_type == "bar":
                fig = px.bar(
                    df, 
                    x='category' if 'category' in df.columns else df.index,
                    y='value' if 'value' in df.columns else df.iloc[:, 0],
                    title=kwargs.get('title', 'Chart'),
                    labels={'x': kwargs.get('x_label', 'Category'), 'y': kwargs.get('y_label', 'Count')}
                )
            elif chart_type == "line":
                fig = px.line(
                    df, 
                    x='category' if 'category' in df.columns else df.index,
                    y='value' if 'value' in df.columns else df.iloc[:, 0],
                    title=kwargs.get('title', 'Chart'),
                    labels={'x': kwargs.get('x_label', 'Category'), 'y': kwargs.get('y_label', 'Count')}
                )
            elif chart_type == "pie":
                fig = px.pie(
                    df,
                    values='value' if 'value' in df.columns else df.iloc[:, 0],
                    names='category' if 'category' in df.columns else df.index,
                    title=kwargs.get('title', 'Chart')
                )
            else:
                fig = go.Figure()
            
            fig.update_layout(
                showlegend=True,
                height=400,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            return fig
            
        except Exception as e:
            st.error(f"Visualization error: {str(e)}")
            # Return a simple text-based visualization instead
            fig = go.Figure()
            fig.add_annotation(
                text=f"Data: {len(data)} records<br>Error creating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the data"""
        if self.trips_data is None:
            return {}
        
        summary = {
            "total_trips": len(self.trips_data),
            "date_range": None,
            "unique_destinations": 0,
            "average_group_size": 0,
            "most_common_day": None,
            "most_common_hour": None
        }
        
        if 'Trip Date and Time' in self.trips_data.columns:
            summary["date_range"] = {
                "start": self.trips_data['Trip Date and Time'].min(),
                "end": self.trips_data['Trip Date and Time'].max()
            }
        elif 'date' in self.trips_data.columns:
            summary["date_range"] = {
                "start": self.trips_data['date'].min(),
                "end": self.trips_data['date'].max()
            }
        elif 'pickup_time' in self.trips_data.columns:
            summary["date_range"] = {
                "start": self.trips_data['pickup_time'].min(),
                "end": self.trips_data['pickup_time'].max()
            }
        else:
            st.warning(f"⚠️ No date column found. Available columns: {list(self.trips_data.columns)}")
        
        if 'Drop Off Address' in self.trips_data.columns:
            summary["unique_destinations"] = self.trips_data['Drop Off Address'].nunique()
        elif 'dropoff_location' in self.trips_data.columns:
            summary["unique_destinations"] = self.trips_data['dropoff_location'].nunique()
        
        if 'Total Passengers' in self.trips_data.columns:
            summary["average_group_size"] = round(self.trips_data['Total Passengers'].mean(), 2)
        elif 'group_size' in self.trips_data.columns:
            summary["average_group_size"] = round(self.trips_data['group_size'].mean(), 2)
        
        if 'day_of_week' in self.trips_data.columns:
            summary["most_common_day"] = self.trips_data['day_of_week'].mode().iloc[0] if not self.trips_data['day_of_week'].mode().empty else None
        
        if 'hour' in self.trips_data.columns:
            summary["most_common_hour"] = int(self.trips_data['hour'].mode().iloc[0]) if not self.trips_data['hour'].mode().empty else None
        
        return summary
    
    def get_trips_by_age_and_day(self, age_group: str = None, day_of_week: str = None) -> pd.DataFrame:
        """Get trips filtered by age group and day of week"""
        if self.trips_data is None:
            return pd.DataFrame()
        
        data = self.trips_data.copy()
        
        # Filter by age group if specified
        if age_group and 'age_group' in data.columns:
            if age_group == "18-24":
                data = data[data['age_group'] == '18-24']
            elif age_group == "25-34":
                data = data[data['age_group'] == '25-34']
            elif age_group == "35-44":
                data = data[data['age_group'] == '35-44']
            elif age_group == "45+":
                data = data[data['age_group'] == '45+']
        
        # Filter by day of week if specified
        if day_of_week and 'day_of_week' in data.columns:
            data = data[data['day_of_week'].str.lower() == day_of_week.lower()]
        
        return data
    
    def get_top_destinations_by_age_and_day(self, age_group: str = None, day_of_week: str = None, limit: int = 10) -> pd.DataFrame:
        """Get top destinations for specific age group and day of week"""
        filtered_data = self.get_trips_by_age_and_day(age_group, day_of_week)
        
        if filtered_data.empty:
            return pd.DataFrame()
        
        # Get destination column
        dest_col = None
        for col in ['Drop Off Address', 'dropoff_location', 'destination']:
            if col in filtered_data.columns:
                dest_col = col
                break
        
        if dest_col is None:
            return pd.DataFrame()
        
        # Count destinations
        dest_counts = filtered_data[dest_col].value_counts().head(limit)
        
        result = pd.DataFrame({
            'destination': dest_counts.index,
            'trip_count': dest_counts.values
        })
        
        return result
    
    def get_large_groups_by_time_and_location(self, min_size: int = 6, location_keyword: str = None, day_of_week: str = None) -> pd.DataFrame:
        """Get large group trips filtered by time and location"""
        if self.trips_data is None:
            return pd.DataFrame()
        
        data = self.trips_data.copy()
        
        # Filter by group size
        group_col = None
        for col in ['Total Passengers', 'group_size', 'passengers']:
            if col in data.columns:
                group_col = col
                break
        
        if group_col:
            data = data[data[group_col] >= min_size]
        
        # Filter by location keyword (e.g., "downtown")
        if location_keyword:
            location_col = None
            for col in ['Pick Up Address', 'pickup_location', 'Drop Off Address', 'dropoff_location']:
                if col in data.columns:
                    location_col = col
                    break
            
            if location_col:
                data = data[data[location_col].str.contains(location_keyword, case=False, na=False)]
        
        # Filter by day of week
        if day_of_week and 'day_of_week' in data.columns:
            data = data[data['day_of_week'].str.lower() == day_of_week.lower()]
        
        return data
    
    def get_hourly_patterns_by_demographics(self, age_group: str = None, day_of_week: str = None) -> pd.DataFrame:
        """Get hourly patterns for specific demographics"""
        filtered_data = self.get_trips_by_age_and_day(age_group, day_of_week)
        
        if filtered_data.empty or 'hour' not in filtered_data.columns:
            return pd.DataFrame()
        
        # Group by hour and count trips
        hourly_counts = filtered_data.groupby('hour').size().reset_index(name='trip_count')
        
        return hourly_counts
    
    def get_detailed_trip_analysis(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get detailed analysis of trips based on various filters"""
        if self.trips_data is None:
            return {}
        
        data = self.trips_data.copy()
        
        # Apply filters if provided
        if filters:
            if 'age_group' in filters and 'age_group' in data.columns:
                data = data[data['age_group'] == filters['age_group']]
            
            if 'day_of_week' in filters and 'day_of_week' in data.columns:
                data = data[data['day_of_week'].str.lower() == filters['day_of_week'].lower()]
            
            if 'min_group_size' in filters:
                group_col = None
                for col in ['Total Passengers', 'group_size', 'passengers']:
                    if col in data.columns:
                        group_col = col
                        break
                if group_col:
                    data = data[data[group_col] >= filters['min_group_size']]
            
            if 'location_keyword' in filters:
                location_col = None
                for col in ['Pick Up Address', 'pickup_location', 'Drop Off Address', 'dropoff_location']:
                    if col in data.columns:
                        location_col = col
                        break
                if location_col:
                    data = data[data[location_col].str.contains(filters['location_keyword'], case=False, na=False)]
        
        analysis = {
            'total_trips': len(data),
            'columns_available': list(data.columns),
            'sample_data': data.head(10).to_dict('records') if not data.empty else []
        }
        
        # Add time-based analysis
        if 'hour' in data.columns:
            analysis['hourly_distribution'] = data['hour'].value_counts().to_dict()
        
        if 'day_of_week' in data.columns:
            analysis['daily_distribution'] = data['day_of_week'].value_counts().to_dict()
        
        # Add destination analysis
        dest_col = None
        for col in ['Drop Off Address', 'dropoff_location', 'destination']:
            if col in data.columns:
                dest_col = col
                break
        
        if dest_col:
            analysis['top_destinations'] = data[dest_col].value_counts().head(10).to_dict()
        
        # Add group size analysis
        group_col = None
        for col in ['Total Passengers', 'group_size', 'passengers']:
            if col in data.columns:
                group_col = col
                break
        
        if group_col:
            analysis['group_size_stats'] = {
                'mean': data[group_col].mean(),
                'median': data[group_col].median(),
                'min': data[group_col].min(),
                'max': data[group_col].max(),
                'large_groups_6plus': len(data[data[group_col] >= 6])
            }
        
        return analysis
    
    def search_destinations(self, search_term: str, exact_match: bool = False) -> pd.DataFrame:
        """Search for destinations using fuzzy matching or exact matching"""
        if self.trips_data is None:
            return pd.DataFrame()
        
        # Get destination column
        dest_col = None
        for col in ['Drop Off Address', 'dropoff_location', 'destination']:
            if col in self.trips_data.columns:
                dest_col = col
                break
        
        if dest_col is None:
            return pd.DataFrame()
        
        if exact_match:
            # Exact match search
            filtered_data = self.trips_data[
                self.trips_data[dest_col].str.contains(search_term, case=False, na=False, regex=False)
            ]
        else:
            # Fuzzy search - look for partial matches
            search_lower = search_term.lower()
            filtered_data = self.trips_data[
                self.trips_data[dest_col].str.contains(search_lower, case=False, na=False, regex=False)
            ]
        
        return filtered_data
    
    def get_destination_stats(self, destination: str, time_period: str = None) -> Dict[str, Any]:
        """Get comprehensive statistics for a specific destination"""
        if self.trips_data is None:
            return {}
        
        # Search for the destination
        dest_data = self.search_destinations(destination)
        
        if dest_data.empty:
            return {"found": False, "message": f"No trips found to {destination}"}
        
        stats = {
            "found": True,
            "destination": destination,
            "total_trips": len(dest_data),
            "total_passengers": 0,
            "average_group_size": 0,
            "unique_destinations": 0,
            "date_range": {},
            "hourly_distribution": {},
            "daily_distribution": {},
            "monthly_distribution": {}
        }
        
        # Get destination column
        dest_col = None
        for col in ['Drop Off Address', 'dropoff_location', 'destination']:
            if col in dest_data.columns:
                dest_col = col
                break
        
        if dest_col:
            # Get unique destinations that match
            unique_dests = dest_data[dest_col].unique()
            stats["unique_destinations"] = len(unique_dests)
            stats["matching_destinations"] = list(unique_dests)
        
        # Calculate passenger statistics
        group_col = None
        for col in ['Total Passengers', 'group_size', 'passengers']:
            if col in dest_data.columns:
                group_col = col
                break
        
        if group_col:
            stats["total_passengers"] = dest_data[group_col].sum()
            stats["average_group_size"] = dest_data[group_col].mean()
            stats["min_group_size"] = dest_data[group_col].min()
            stats["max_group_size"] = dest_data[group_col].max()
        
        # Time-based analysis
        if 'Trip Date and Time' in dest_data.columns:
            try:
                dest_data['datetime'] = pd.to_datetime(dest_data['Trip Date and Time'])
                stats["date_range"] = {
                    "start": dest_data['datetime'].min().strftime('%Y-%m-%d'),
                    "end": dest_data['datetime'].max().strftime('%Y-%m-%d')
                }
                
                # Monthly distribution
                dest_data['month'] = dest_data['datetime'].dt.month
                stats["monthly_distribution"] = dest_data['month'].value_counts().to_dict()
                
                # Filter by time period if specified
                if time_period:
                    if time_period.lower() == "last month":
                        current_date = pd.Timestamp.now()
                        last_month = current_date - pd.DateOffset(months=1)
                        dest_data = dest_data[dest_data['datetime'] >= last_month]
                        stats["total_trips"] = len(dest_data)
                        stats["total_passengers"] = dest_data[group_col].sum() if group_col else 0
                        stats["average_group_size"] = dest_data[group_col].mean() if group_col else 0
                
            except Exception as e:
                stats["date_analysis_error"] = str(e)
        
        # Hourly distribution
        if 'hour' in dest_data.columns:
            stats["hourly_distribution"] = dest_data['hour'].value_counts().to_dict()
        
        # Daily distribution
        if 'day_of_week' in dest_data.columns:
            stats["daily_distribution"] = dest_data['day_of_week'].value_counts().to_dict()
        
        return stats
    
    def get_all_destinations(self) -> List[str]:
        """Get all unique destinations in the dataset"""
        if self.trips_data is None:
            return []
        
        dest_col = None
        for col in ['Drop Off Address', 'dropoff_location', 'destination']:
            if col in self.trips_data.columns:
                dest_col = col
                break
        
        if dest_col is None:
            return []
        
        return self.trips_data[dest_col].dropna().unique().tolist()
    
    def search_similar_destinations(self, search_term: str, limit: int = 10) -> List[str]:
        """Find destinations similar to the search term"""
        all_destinations = self.get_all_destinations()
        search_lower = search_term.lower()
        
        # Find destinations that contain the search term
        similar = [dest for dest in all_destinations 
                  if search_lower in dest.lower()]
        
        # Sort by relevance (exact matches first, then partial matches)
        similar.sort(key=lambda x: (
            0 if search_lower in x.lower() else 1,
            len(x)
        ))
        
        return similar[:limit]
    
    def analyze_group_size_patterns(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze group size patterns and distributions"""
        if self.trips_data is None:
            return {}
        
        data = self.trips_data.copy()
        
        # Apply filters if provided
        if filters:
            if 'age_group' in filters and 'age_group' in data.columns:
                data = data[data['age_group'] == filters['age_group']]
            if 'day_of_week' in filters and 'day_of_week' in data.columns:
                data = data[data['day_of_week'].str.lower() == filters['day_of_week'].lower()]
            if 'time_period' in filters and 'hour' in data.columns:
                if filters['time_period'] == 'morning':
                    data = data[(data['hour'] >= 6) & (data['hour'] < 12)]
                elif filters['time_period'] == 'afternoon':
                    data = data[(data['hour'] >= 12) & (data['hour'] < 18)]
                elif filters['time_period'] == 'evening':
                    data = data[(data['hour'] >= 18) & (data['hour'] < 24)]
        
        group_col = None
        for col in ['Total Passengers', 'group_size', 'passengers']:
            if col in data.columns:
                group_col = col
                break
        
        if group_col is None:
            return {"error": "No group size column found"}
        
        analysis = {
            "total_trips": len(data),
            "group_size_stats": {
                "mean": data[group_col].mean(),
                "median": data[group_col].median(),
                "mode": data[group_col].mode().iloc[0] if not data[group_col].mode().empty else None,
                "std": data[group_col].std(),
                "min": data[group_col].min(),
                "max": data[group_col].max(),
                "q1": data[group_col].quantile(0.25),
                "q3": data[group_col].quantile(0.75)
            },
            "group_size_distribution": data[group_col].value_counts().sort_index().to_dict(),
            "size_categories": {
                "small_groups_1_3": len(data[data[group_col] <= 3]),
                "medium_groups_4_6": len(data[(data[group_col] >= 4) & (data[group_col] <= 6)]),
                "large_groups_7_10": len(data[(data[group_col] >= 7) & (data[group_col] <= 10)]),
                "very_large_groups_11plus": len(data[data[group_col] >= 11])
            }
        }
        
        # Hourly group size patterns
        if 'hour' in data.columns:
            hourly_groups = data.groupby('hour')[group_col].agg(['mean', 'count']).reset_index()
            analysis["hourly_group_patterns"] = {
                "hours": hourly_groups['hour'].tolist(),
                "avg_group_sizes": hourly_groups['mean'].tolist(),
                "trip_counts": hourly_groups['count'].tolist()
            }
        
        # Day of week group size patterns
        if 'day_of_week' in data.columns:
            daily_groups = data.groupby('day_of_week')[group_col].agg(['mean', 'count']).reset_index()
            analysis["daily_group_patterns"] = {
                "days": daily_groups['day_of_week'].tolist(),
                "avg_group_sizes": daily_groups['mean'].tolist(),
                "trip_counts": daily_groups['count'].tolist()
            }
        
        # Age group correlations
        if 'age_group' in data.columns:
            age_groups = data.groupby('age_group')[group_col].agg(['mean', 'count']).reset_index()
            analysis["age_group_correlations"] = {
                "age_groups": age_groups['age_group'].tolist(),
                "avg_group_sizes": age_groups['mean'].tolist(),
                "trip_counts": age_groups['count'].tolist()
            }
        
        return analysis
    
    def analyze_hourly_patterns(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze hourly patterns with detailed insights"""
        if self.trips_data is None:
            return {}
        
        data = self.trips_data.copy()
        
        # Apply filters
        if filters:
            if 'age_group' in filters and 'age_group' in data.columns:
                data = data[data['age_group'] == filters['age_group']]
            if 'day_of_week' in filters and 'day_of_week' in data.columns:
                data = data[data['day_of_week'].str.lower() == filters['day_of_week'].lower()]
        
        if 'hour' not in data.columns:
            return {"error": "No hour column found"}
        
        analysis = {
            "total_trips": len(data),
            "hourly_distribution": data['hour'].value_counts().sort_index().to_dict(),
            "peak_hours": data['hour'].value_counts().head(5).to_dict(),
            "time_periods": {
                "early_morning_6_9": len(data[(data['hour'] >= 6) & (data['hour'] < 9)]),
                "morning_9_12": len(data[(data['hour'] >= 9) & (data['hour'] < 12)]),
                "afternoon_12_17": len(data[(data['hour'] >= 12) & (data['hour'] < 17)]),
                "evening_17_21": len(data[(data['hour'] >= 17) & (data['hour'] < 21)]),
                "night_21_6": len(data[(data['hour'] >= 21) | (data['hour'] < 6)])
            }
        }
        
        # Group size patterns by hour
        group_col = None
        for col in ['Total Passengers', 'group_size', 'passengers']:
            if col in data.columns:
                group_col = col
                break
        
        if group_col:
            hourly_groups = data.groupby('hour')[group_col].agg(['mean', 'count']).reset_index()
            analysis["hourly_group_analysis"] = {
                "hours": hourly_groups['hour'].tolist(),
                "avg_group_sizes": hourly_groups['mean'].tolist(),
                "trip_counts": hourly_groups['count'].tolist()
            }
            
            # Find peak hours for different group sizes
            large_groups = data[data[group_col] >= 6]
            if not large_groups.empty:
                analysis["large_group_peak_hours"] = large_groups['hour'].value_counts().head(5).to_dict()
        
        return analysis
    
    def analyze_day_of_week_patterns(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze day-of-week patterns with detailed insights"""
        if self.trips_data is None:
            return {}
        
        data = self.trips_data.copy()
        
        # Apply filters
        if filters:
            if 'age_group' in filters and 'age_group' in data.columns:
                data = data[data['age_group'] == filters['age_group']]
            if 'time_period' in filters and 'hour' in data.columns:
                if filters['time_period'] == 'morning':
                    data = data[(data['hour'] >= 6) & (data['hour'] < 12)]
                elif filters['time_period'] == 'afternoon':
                    data = data[(data['hour'] >= 12) & (data['hour'] < 18)]
                elif filters['time_period'] == 'evening':
                    data = data[(data['hour'] >= 18) & (data['hour'] < 24)]
        
        if 'day_of_week' not in data.columns:
            return {"error": "No day_of_week column found"}
        
        analysis = {
            "total_trips": len(data),
            "daily_distribution": data['day_of_week'].value_counts().to_dict(),
            "most_popular_day": data['day_of_week'].mode().iloc[0] if not data['day_of_week'].mode().empty else None,
            "weekend_vs_weekday": {
                "weekend_trips": len(data[data['day_of_week'].isin(['Saturday', 'Sunday'])]),
                "weekday_trips": len(data[data['day_of_week'].isin(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])])
            }
        }
        
        # Group size patterns by day
        group_col = None
        for col in ['Total Passengers', 'group_size', 'passengers']:
            if col in data.columns:
                group_col = col
                break
        
        if group_col:
            daily_groups = data.groupby('day_of_week')[group_col].agg(['mean', 'count']).reset_index()
            analysis["daily_group_analysis"] = {
                "days": daily_groups['day_of_week'].tolist(),
                "avg_group_sizes": daily_groups['mean'].tolist(),
                "trip_counts": daily_groups['count'].tolist()
            }
            
            # Weekend vs weekday group sizes
            weekend_data = data[data['day_of_week'].isin(['Saturday', 'Sunday'])]
            weekday_data = data[data['day_of_week'].isin(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])]
            
            analysis["weekend_vs_weekday_groups"] = {
                "weekend_avg_group_size": weekend_data[group_col].mean() if not weekend_data.empty else 0,
                "weekday_avg_group_size": weekday_data[group_col].mean() if not weekday_data.empty else 0,
                "weekend_large_groups": len(weekend_data[weekend_data[group_col] >= 6]) if not weekend_data.empty else 0,
                "weekday_large_groups": len(weekday_data[weekday_data[group_col] >= 6]) if not weekday_data.empty else 0
            }
        
        # Destination patterns by day
        dest_col = None
        for col in ['Drop Off Address', 'dropoff_location', 'destination']:
            if col in data.columns:
                dest_col = col
                break
        
        if dest_col:
            daily_destinations = data.groupby('day_of_week')[dest_col].apply(lambda x: x.value_counts().head(3).to_dict()).to_dict()
            analysis["daily_destination_patterns"] = daily_destinations
        
        return analysis
    
    def analyze_age_group_correlations(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze age group correlations with group sizes and destinations"""
        if self.trips_data is None:
            return {}
        
        data = self.trips_data.copy()
        
        # Apply filters
        if filters:
            if 'day_of_week' in filters and 'day_of_week' in data.columns:
                data = data[data['day_of_week'].str.lower() == filters['day_of_week'].lower()]
            if 'time_period' in filters and 'hour' in data.columns:
                if filters['time_period'] == 'morning':
                    data = data[(data['hour'] >= 6) & (data['hour'] < 12)]
                elif filters['time_period'] == 'afternoon':
                    data = data[(data['hour'] >= 12) & (data['hour'] < 18)]
                elif filters['time_period'] == 'evening':
                    data = data[(data['hour'] >= 18) & (data['hour'] < 24)]
        
        if 'age_group' not in data.columns:
            return {"error": "No age_group column found"}
        
        analysis = {
            "total_trips": len(data),
            "age_group_distribution": data['age_group'].value_counts().to_dict(),
            "most_common_age_group": data['age_group'].mode().iloc[0] if not data['age_group'].mode().empty else None
        }
        
        # Group size patterns by age group
        group_col = None
        for col in ['Total Passengers', 'group_size', 'passengers']:
            if col in data.columns:
                group_col = col
                break
        
        if group_col:
            age_groups = data.groupby('age_group')[group_col].agg(['mean', 'count', 'min', 'max']).reset_index()
            analysis["age_group_group_sizes"] = {
                "age_groups": age_groups['age_group'].tolist(),
                "avg_group_sizes": age_groups['mean'].tolist(),
                "trip_counts": age_groups['count'].tolist(),
                "min_group_sizes": age_groups['min'].tolist(),
                "max_group_sizes": age_groups['max'].tolist()
            }
            
            # Large group preferences by age
            large_groups = data[data[group_col] >= 6]
            if not large_groups.empty:
                large_group_ages = large_groups['age_group'].value_counts().to_dict()
                analysis["large_group_age_preferences"] = large_group_ages
        
        # Destination preferences by age group
        dest_col = None
        for col in ['Drop Off Address', 'dropoff_location', 'destination']:
            if col in data.columns:
                dest_col = col
                break
        
        if dest_col:
            age_destinations = data.groupby('age_group')[dest_col].apply(lambda x: x.value_counts().head(3).to_dict()).to_dict()
            analysis["age_group_destination_preferences"] = age_destinations
        
        # Time patterns by age group
        if 'hour' in data.columns:
            age_hours = data.groupby('age_group')['hour'].apply(lambda x: x.value_counts().head(3).to_dict()).to_dict()
            analysis["age_group_time_preferences"] = age_hours
        
        return analysis
    
    def analyze_monthly_trends(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze monthly trends and patterns"""
        if self.trips_data is None:
            return {}
        
        data = self.trips_data.copy()
        
        # Apply filters
        if filters:
            if 'age_group' in filters and 'age_group' in data.columns:
                data = data[data['age_group'] == filters['age_group']]
            if 'day_of_week' in filters and 'day_of_week' in data.columns:
                data = data[data['day_of_week'].str.lower() == filters['day_of_week'].lower()]
        
        # Convert to datetime if possible
        if 'Trip Date and Time' in data.columns:
            try:
                data['datetime'] = pd.to_datetime(data['Trip Date and Time'])
                data['month'] = data['datetime'].dt.month
                data['month_name'] = data['datetime'].dt.month_name()
                data['year'] = data['datetime'].dt.year
            except:
                return {"error": "Could not parse date column"}
        else:
            return {"error": "No date column found"}
        
        analysis = {
            "total_trips": len(data),
            "monthly_distribution": data['month'].value_counts().sort_index().to_dict(),
            "monthly_names": data['month_name'].value_counts().to_dict(),
            "yearly_distribution": data['year'].value_counts().sort_index().to_dict(),
            "most_active_month": data['month_name'].mode().iloc[0] if not data['month_name'].mode().empty else None
        }
        
        # Group size trends by month
        group_col = None
        for col in ['Total Passengers', 'group_size', 'passengers']:
            if col in data.columns:
                group_col = col
                break
        
        if group_col:
            monthly_groups = data.groupby('month')[group_col].agg(['mean', 'count']).reset_index()
            analysis["monthly_group_trends"] = {
                "months": monthly_groups['month'].tolist(),
                "avg_group_sizes": monthly_groups['mean'].tolist(),
                "trip_counts": monthly_groups['count'].tolist()
            }
        
        # Destination trends by month
        dest_col = None
        for col in ['Drop Off Address', 'dropoff_location', 'destination']:
            if col in data.columns:
                dest_col = col
                break
        
        if dest_col:
            monthly_destinations = data.groupby('month')[dest_col].apply(lambda x: x.value_counts().head(3).to_dict()).to_dict()
            analysis["monthly_destination_trends"] = monthly_destinations
        
        return analysis
