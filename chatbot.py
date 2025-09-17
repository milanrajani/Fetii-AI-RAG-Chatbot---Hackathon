
import os
import pandas as pd
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from data_processor import FetiiDataProcessor
import streamlit as st
# Removed sample data generation - using real FetiiAI data instead

class FetiiChatbot:
    """GPT-powered chatbot for Fetii rideshare data analysis"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=1000
        )
        self.data_processor = FetiiDataProcessor()
        self.memory = ConversationBufferMemory(return_messages=True)
        self.conversation = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            verbose=True
        )
        
        # Initialize conversation with system prompt
        self._setup_system_prompt()
    
    def _setup_system_prompt(self):
        """Set up the system prompt for the chatbot"""
        system_prompt = """You are FetiiAI, an intelligent assistant for analyzing Fetii rideshare data. 
        
        You can answer ANY question about the rideshare data, including:
        - Trip patterns, destinations, and routes
        - User demographics and behavior analysis (age groups, specific demographics)
        - Group size analysis and statistics (large groups, small groups, specific sizes)
        - Time-based patterns (hourly, daily, weekly, monthly, seasonal)
        - Day of week analysis (Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday)
        - Time period analysis (morning, afternoon, evening, night)
        - Trip duration analysis
        - Popular destinations and locations
        - Geographic analysis (downtown, specific areas)
        - Temporal trends and patterns
        - Statistical analysis of any data aspect
        - Data exploration and insights
        - Complex queries combining multiple filters (age + day + location + time)
        
        ADVANCED ANALYTICAL TOPICS:
        - Group Size Analysis: Distribution patterns, correlations with time/day/age
        - Hourly Distribution: Peak hours, time patterns, group size variations
        - Day of Week Analysis: Weekend vs weekday patterns, popular days
        - Age Group Analysis: Demographics correlations, preferences by age
        - Monthly Trends: Seasonal patterns, temporal trends over time
        - Cross-dimensional Analysis: How different factors interact and correlate
        
        IMPORTANT: You have access to the complete dataset with comprehensive analysis capabilities. 
        The data includes day of week, hour, age groups, group sizes, and detailed location information.
        
        When analyzing data:
        1. Use the detailed analysis results provided in the context
        2. Look at hourly distribution, daily distribution, and destination analysis
        3. Apply filters for age groups, day of week, time periods, and locations
        4. Provide specific numbers, percentages, and insights
        5. Calculate relevant metrics based on the question
        6. Always be data-driven and accurate
        7. If the data shows specific patterns, explain them clearly
        
        For complex questions like "What are the top drop-off spots for 18-24 year-olds on Saturday nights?":
        - Use the age group filter (18-24)
        - Use the day of week filter (Saturday)
        - Use the time period filter (night/evening)
        - Provide specific destinations with trip counts
        - Give detailed analysis of the patterns
        
        For specific destination questions like "How many groups went to Moody Center last month?":
        - Use RAG (Retrieval-Augmented Generation) to search through ALL destinations
        - Look for exact matches first, then fuzzy matches
        - Provide specific trip counts, passenger numbers, and group sizes
        - If exact match not found, suggest similar destinations
        - Always provide concrete numbers and statistics
        
        IMPORTANT: You can answer questions about ANY destination in the dataset, not just top destinations.
        Use the comprehensive search capabilities to find and analyze any location mentioned.
        
        Be conversational, helpful, and provide detailed insights about any aspect of the rideshare data."""
        
        self.memory.chat_memory.add_message(SystemMessage(content=system_prompt))
    
    def load_data(self, data_file: str = None, trips_file: str = None, users_file: str = None) -> bool:
        """Load data into the processor - supports both single file with tabs or separate files"""
        return self.data_processor.load_data(data_file, trips_file, users_file)
    
    def process_question(self, question: str) -> Dict[str, Any]:
        """Process a user question and return response with data"""
        response = {
            "answer": "",
            "data": None,
            "visualization": None,
            "confidence": "high"
        }
        
        try:
            # Check if data is loaded
            if self.data_processor.trips_data is None:
                response["answer"] = "❌ No data loaded. Please load the FetiiAI data first using the 'Load FetiiAI Data' button."
                return response
            
            # Analyze the question to determine what data to fetch
            try:
                data_query = self._analyze_question(question)
            except Exception as e:
                st.error(f"❌ Error analyzing question: {str(e)}")
                st.exception(e)
                data_query = {"type": "general", "visualization": None}
            
            
            if data_query:
                # Fetch relevant data
                try:
                    data = self._fetch_data(data_query)
                    response["data"] = data
                except Exception as e:
                    st.error(f"❌ Error fetching data: {str(e)}")
                    st.exception(e)
                    response["data"] = None
                
                # Show data results
                if data is not None and not data.empty:
                    st.success(f"📊 Found {len(data)} records matching your query")
                else:
                    st.warning("⚠️ No data found matching your query")
                
                # Create visualization if appropriate and data is suitable
                if data_query and data_query.get("visualization") and data is not None and not data.empty:
                    try:
                        viz = self._create_visualization(data_query, data)
                        response["visualization"] = viz
                    except Exception as e:
                        st.warning(f"Could not create visualization: {str(e)}")
                        response["visualization"] = None
            
            # Generate natural language response
            try:
                context = self._build_context(data_query, response["data"])
            except Exception as e:
                st.error(f"❌ Error building context: {str(e)}")
                st.exception(e)
                context = "Error building context"
            
            try:
                prompt = f"""
                You are FetiiAI, an expert data analyst for rideshare data. You have access to real Fetii rideshare data and must provide accurate, data-driven answers.

                User Question: {question}
                
                DATA ANALYSIS CONTEXT:
                {context}
                
                INSTRUCTIONS:
                1. Use ONLY the data provided in the context above
                2. Provide specific numbers, counts, and statistics from the data
                3. If data is available, give exact answers (e.g., "X groups went to Moody Center last month")
                4. Include relevant insights and patterns from the data
                5. If no data is available, clearly state this and suggest what data would be needed
                6. Be conversational but data-focused
                7. Always base your answer on the actual uploaded dataset, not general knowledge
                
                Answer the user's question using the data provided:
                """
                
                response["answer"] = self.llm.invoke(prompt).content
            except Exception as e:
                st.error(f"❌ Error in LLM call: {str(e)}")
                st.exception(e)
                response["answer"] = f"I encountered an error processing your question: {str(e)}. Please try rephrasing your question."
                response["confidence"] = "low"
            
        except Exception as e:
            response["answer"] = f"I encountered an error processing your question: {str(e)}. Please try rephrasing your question."
            response["confidence"] = "low"
            st.error(f"❌ General Error: {str(e)}")
            st.exception(e)
        
        return response
    
    def _analyze_question(self, question: str) -> Optional[Dict[str, Any]]:
        """Analyze the question to determine what data to fetch - enhanced with RAG capabilities"""
        question_lower = question.lower()
        
        # Debug: Show what we're analyzing
        
        # Extract key information from the question
        analysis = {
            "type": "general",
            "visualization": "bar",
            "question": question,
            "filters": {},
            "destination_query": None,
            "time_period": None
        }
        
        # Extract destination from question using RAG approach
        destination = self._extract_destination_from_question(question)
        if destination:
            analysis["destination_query"] = destination
            analysis["type"] = "destination_search"
        
        # Extract time period
        time_period = self._extract_time_period(question)
        if time_period:
            analysis["time_period"] = time_period
        
        # Check for age group mentions
            if "18-24" in question_lower or "18 to 24" in question_lower:
             analysis["filters"]["age_group"] = "18-24"
            elif "25-34" in question_lower or "25 to 34" in question_lower:
             analysis["filters"]["age_group"] = "25-34"
            elif "35-44" in question_lower or "35 to 44" in question_lower:
             analysis["filters"]["age_group"] = "35-44"
        elif "45+" in question_lower or "45 and up" in question_lower:
            analysis["filters"]["age_group"] = "45+"
        
        # Check for day of week mentions
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in days:
            if day in question_lower:
                analysis["filters"]["day_of_week"] = day.capitalize()
                break
        
        # Check for time-related queries
        if any(word in question_lower for word in ["night", "evening", "late"]):
            analysis["filters"]["time_period"] = "evening"
        elif any(word in question_lower for word in ["morning", "early", "dawn"]):
            analysis["filters"]["time_period"] = "morning"
        elif any(word in question_lower for word in ["afternoon", "midday"]):
            analysis["filters"]["time_period"] = "afternoon"
        
        # Check for location mentions
        if "downtown" in question_lower:
            analysis["filters"]["location_keyword"] = "downtown"
        elif "austin" in question_lower:
            analysis["filters"]["location_keyword"] = "austin"
        
        # Check for group size mentions
        if "large group" in question_lower or "6+" in question_lower or "6 or more" in question_lower:
            analysis["filters"]["min_group_size"] = 6
        elif "small group" in question_lower or "1-3" in question_lower:
            analysis["filters"]["max_group_size"] = 3
        
        # Determine visualization type based on question content
        if any(word in question_lower for word in ["time", "hour", "when", "schedule", "duration", "pattern"]):
            analysis["visualization"] = "line"
        elif any(word in question_lower for word in ["distribution", "percentage", "proportion", "share"]):
            analysis["visualization"] = "pie"
        elif any(word in question_lower for word in ["top", "most", "popular", "best", "highest", "ranking"]):
            analysis["visualization"] = "bar"
        elif any(word in question_lower for word in ["map", "location", "geographic"]):
            analysis["visualization"] = "scatter"
        
        # Determine specific query type based on analytical topics
        if any(word in question_lower for word in ["group size", "group sizes", "group size analysis", "group distribution"]):
            analysis["type"] = "group_size_analysis"
        elif any(word in question_lower for word in ["hourly", "hourly distribution", "peak hours", "time patterns", "when do"]):
            analysis["type"] = "hourly_analysis"
        elif any(word in question_lower for word in ["day of week", "weekday", "weekend", "saturday", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday"]):
            analysis["type"] = "day_of_week_analysis"
        elif any(word in question_lower for word in ["age group", "age groups", "demographics", "young", "old", "18-24", "25-34", "35-44", "45+"]):
            analysis["type"] = "age_group_analysis"
        elif any(word in question_lower for word in ["monthly", "monthly trends", "seasonal", "over time", "trends"]):
            analysis["type"] = "monthly_analysis"
        elif any(word in question_lower for word in ["top", "most popular", "best", "ranking"]):
            if "destination" in question_lower or "drop" in question_lower or "location" in question_lower:
                analysis["type"] = "top_destinations"
            elif "time" in question_lower or "hour" in question_lower:
                analysis["type"] = "hourly_patterns"
        
        return analysis
    
    def _extract_destination_from_question(self, question: str) -> Optional[str]:
        """Extract destination from question using RAG approach"""
        question_lower = question.lower()
        
        # Common destination keywords to look for
        destination_keywords = [
            "moody center", "moody", "center",
            "downtown", "austin", "university", "campus",
            "airport", "mall", "stadium", "theater",
            "restaurant", "bar", "club", "hotel",
            "park", "lake", "river", "bridge"
        ]
        
        # Look for destination mentions
        for keyword in destination_keywords:
            if keyword in question_lower:
                # Try to find the full destination name
                similar_destinations = self.data_processor.search_similar_destinations(keyword, limit=5)
                if similar_destinations:
                    return similar_destinations[0]  # Return the most relevant match
        
        # If no specific destination found, look for "went to" or "go to" patterns
        import re
        patterns = [
            r"went to ([^?]+)",
            r"go to ([^?]+)",
            r"visiting ([^?]+)",
            r"at ([^?]+)",
            r"in ([^?]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question_lower)
            if match:
                potential_dest = match.group(1).strip()
                # Clean up the destination name
                potential_dest = re.sub(r'\s+(last|this|next)\s+(month|week|year)', '', potential_dest)
                potential_dest = re.sub(r'\s+(how many|groups|trips)', '', potential_dest)
                if potential_dest and len(potential_dest) > 2:
                    return potential_dest
        
        return None
    
    def _extract_time_period(self, question: str) -> Optional[str]:
        """Extract time period from question"""
        question_lower = question.lower()
        
        time_periods = {
            "last month": ["last month", "previous month"],
            "this month": ["this month", "current month"],
            "last week": ["last week", "previous week"],
            "this week": ["this week", "current week"],
            "yesterday": ["yesterday"],
            "today": ["today"],
            "last year": ["last year", "previous year"],
            "this year": ["this year", "current year"]
        }
        
        for period, keywords in time_periods.items():
            if any(keyword in question_lower for keyword in keywords):
                return period
        
        return None
    
    def _extract_day_of_week(self, question: str) -> Optional[str]:
        """Extract day of week from question"""
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in days:
            if day in question:
                return day.capitalize()
        return None
    
    def _extract_month(self, question: str) -> Optional[int]:
        """Extract month from question"""
        import datetime
        
        # Check for "last month"
        if "last month" in question:
            now = datetime.datetime.now()
            last_month = now.month - 1 if now.month > 1 else 12
            return last_month
        
        # Check for specific month names
        month_names = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }
        
        for month_name, month_num in month_names.items():
            if month_name in question:
                return month_num
        
        # Check for month numbers
        import re
        month_match = re.search(r'\b(\d{1,2})\b', question)
        if month_match:
            month_num = int(month_match.group(1))
            if 1 <= month_num <= 12:
                return month_num
        
        return None
    
    def _fetch_data(self, query: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Fetch data based on query parameters - enhanced for complex queries"""
        if self.data_processor.trips_data is None:
            return None
        
        if query is None:
            return None
        
        query_type = query.get("type")
        filters = query.get("filters", {})
        
        
        # Handle specific query types with enhanced analysis
        if query_type == "destination_search":
            destination = query.get("destination_query")
            time_period = query.get("time_period")
            
            # Get comprehensive destination statistics
            dest_stats = self.data_processor.get_destination_stats(destination, time_period)
            
            if dest_stats.get("found", False):
                # Return the actual data for the destination
                dest_data = self.data_processor.search_destinations(destination)
                return dest_data
            else:
                # Try fuzzy search for similar destinations
                similar_destinations = self.data_processor.search_similar_destinations(destination, limit=10)
                
                if similar_destinations:
                    # Return data for the most similar destination
                    best_match = similar_destinations[0]
                    dest_data = self.data_processor.search_destinations(best_match)
                    return dest_data
                else:
                    return pd.DataFrame()
        
        elif query_type == "top_destinations":
            age_group = filters.get("age_group")
            day_of_week = filters.get("day_of_week")
            result = self.data_processor.get_top_destinations_by_age_and_day(age_group, day_of_week)
            return result
        
        elif query_type == "group_size_analysis":
            analysis_result = self.data_processor.analyze_group_size_patterns(filters)
            # Return the original data for context, but the analysis is in the result
            return self.data_processor.trips_data
        
        elif query_type == "hourly_analysis":
            analysis_result = self.data_processor.analyze_hourly_patterns(filters)
            return self.data_processor.trips_data
        
        elif query_type == "day_of_week_analysis":
            analysis_result = self.data_processor.analyze_day_of_week_patterns(filters)
            return self.data_processor.trips_data
        
        elif query_type == "age_group_analysis":
            analysis_result = self.data_processor.analyze_age_group_correlations(filters)
            return self.data_processor.trips_data
        
        elif query_type == "monthly_analysis":
            analysis_result = self.data_processor.analyze_monthly_trends(filters)
            return self.data_processor.trips_data
        
        elif query_type == "hourly_patterns":
            age_group = filters.get("age_group")
            day_of_week = filters.get("day_of_week")
            return self.data_processor.get_hourly_patterns_by_demographics(age_group, day_of_week)
        
        elif query_type == "large_groups":
            min_size = filters.get("min_group_size", 6)
            location_keyword = filters.get("location_keyword")
            day_of_week = filters.get("day_of_week")
            return self.data_processor.get_large_groups_by_time_and_location(min_size, location_keyword, day_of_week)
        
        elif query_type == "destination":
            return self.data_processor.get_trips_by_destination(
                query.get("destination", ""),
                query.get("month")
            )
        elif query_type == "age_group":
            return self.data_processor.get_trips_by_age_group(
                query.get("age_group", ""),
                query.get("day_of_week")
            )
        elif query_type == "age_group_destinations":
            return self.data_processor.get_age_group_destinations(
                query.get("age_group", ""),
                query.get("day_of_week")
            )
        elif query_type == "hourly_distribution":
            return self.data_processor.get_hourly_distribution(
                query.get("day_of_week")
            )
        elif query_type == "summary":
            return self.data_processor.trips_data
        elif query_type == "general":
            # For general queries, return the full dataset for comprehensive analysis
            return self.data_processor.trips_data
        
        # Fallback: return the full dataset for any unknown query type
        return self.data_processor.trips_data
    
    def _create_visualization(self, query: Dict[str, Any], data: pd.DataFrame) -> Any:
        """Create visualization based on query and data"""
        if data is None or data.empty:
            return None
        
        if query is None:
            query = {"type": "general", "visualization": "bar"}
        
        try:
            viz_type = query.get("visualization", "bar")
            
            if query.get("type") == "top_destinations":
                return self.data_processor.create_visualization(
                    "bar", data, 
                    title="Top Destinations",
                    x_label="Destination",
                    y_label="Number of Trips"
                )
            elif query.get("type") == "age_group_destinations":
                age_group = query.get("age_group", "specified age group")
                day_filter = f" on {query.get('day_of_week')}" if query.get('day_of_week') else ""
                return self.data_processor.create_visualization(
                    "bar", data,
                    title=f"Top Destinations for {age_group} year-olds{day_filter}",
                    x_label="Destination",
                    y_label="Number of Trips"
                )
            elif query.get("type") == "hourly_distribution":
                return self.data_processor.create_visualization(
                    "line", data,
                    title="Hourly Trip Distribution",
                    x_label="Hour of Day",
                    y_label="Number of Trips"
                )
            elif query.get("type") == "destination":
                destination = query.get("destination", "specified destination")
                return self.data_processor.create_visualization(
                    "bar", data,
                    title=f"Trips to {destination}",
                    x_label="Trip Details",
                    y_label="Count"
                )
            else:
                return self.data_processor.create_visualization(
                    viz_type, data,
                    title=f"Analysis: {query.get('type', 'Data')}"
                )
        except Exception as e:
            st.error(f"Visualization creation error: {str(e)}")
            return None
    
    def _build_context(self, query: Dict[str, Any], data: pd.DataFrame) -> str:
        """Build detailed context string for the LLM using RAG approach - enhanced for complex queries"""
        context_parts = []
        
        # Handle case where query is None
        if query is None:
            query = {"type": "general"}
        
        # Get comprehensive analysis using the new detailed analysis function
        filters = query.get("filters", {})
        detailed_analysis = self.data_processor.get_detailed_trip_analysis(filters)
        
        # Add overall data summary first
        summary = self.data_processor.get_data_summary()
        if summary:
            context_parts.append(f"DATASET OVERVIEW:")
            context_parts.append(f"- Total trips in dataset: {summary.get('total_trips', 0)}")
            
            # Safe date range handling
            date_range = summary.get('date_range')
            if date_range and isinstance(date_range, dict):
                start_date = date_range.get('start', 'Unknown')
                end_date = date_range.get('end', 'Unknown')
                context_parts.append(f"- Date range: {start_date} to {end_date}")
            else:
                context_parts.append(f"- Date range: Unknown")
            
            context_parts.append(f"- Unique destinations: {summary.get('unique_destinations', 0)}")
            context_parts.append(f"- Average group size: {summary.get('average_group_size', 0)}")
            context_parts.append(f"- Most common day: {summary.get('most_common_day', 'Unknown')}")
            context_parts.append(f"- Most common hour: {summary.get('most_common_hour', 'Unknown')}")
            context_parts.append("")
        
        # Add detailed analysis results
        if detailed_analysis:
            context_parts.append(f"DETAILED ANALYSIS:")
            context_parts.append(f"- Filtered trips: {detailed_analysis.get('total_trips', 0)}")
            context_parts.append(f"- Available columns: {detailed_analysis.get('columns_available', [])}")
            
            # Add time-based analysis
            if 'hourly_distribution' in detailed_analysis:
                context_parts.append(f"- Hourly distribution: {detailed_analysis['hourly_distribution']}")
            
            if 'daily_distribution' in detailed_analysis:
                context_parts.append(f"- Daily distribution: {detailed_analysis['daily_distribution']}")
            
            # Add destination analysis
            if 'top_destinations' in detailed_analysis:
                context_parts.append(f"- Top destinations: {detailed_analysis['top_destinations']}")
            
            # Add group size analysis
            if 'group_size_stats' in detailed_analysis:
                stats = detailed_analysis['group_size_stats']
                context_parts.append(f"- Group size statistics:")
                context_parts.append(f"  * Average: {stats.get('mean', 0):.2f}")
                context_parts.append(f"  * Median: {stats.get('median', 0):.2f}")
                context_parts.append(f"  * Range: {stats.get('min', 0)} - {stats.get('max', 0)}")
                context_parts.append(f"  * Large groups (6+): {stats.get('large_groups_6plus', 0)}")
            
            context_parts.append("")
        
        # Add specific analysis based on query type
        if data is not None and not data.empty:
            context_parts.append(f"QUERY-SPECIFIC RESULTS:")
            context_parts.append(f"- Records found: {len(data)}")
            
            # For destination search queries
            if query.get("type") == "destination_search":
                destination = query.get("destination_query", "the specified destination")
                time_period = query.get("time_period", "")
                
                context_parts.append(f"- Destination search results for: {destination}")
                if time_period:
                    context_parts.append(f"- Time period: {time_period}")
                
                # Get destination statistics
                dest_stats = self.data_processor.get_destination_stats(destination, time_period)
                if dest_stats.get("found", False):
                    context_parts.append(f"- Total trips to {destination}: {dest_stats.get('total_trips', 0)}")
                    context_parts.append(f"- Total passengers: {dest_stats.get('total_passengers', 0)}")
                    context_parts.append(f"- Average group size: {dest_stats.get('average_group_size', 0):.2f}")
                    
                    if dest_stats.get("matching_destinations"):
                        context_parts.append(f"- Matching destinations: {dest_stats['matching_destinations']}")
                    
                    if dest_stats.get("date_range"):
                        date_range = dest_stats["date_range"]
                        context_parts.append(f"- Date range: {date_range.get('start')} to {date_range.get('end')}")
                    
                    if dest_stats.get("hourly_distribution"):
                        context_parts.append(f"- Peak hours: {dest_stats['hourly_distribution']}")
                    
                    if dest_stats.get("daily_distribution"):
                        context_parts.append(f"- Day of week distribution: {dest_stats['daily_distribution']}")
                else:
                    # Try to find similar destinations
                    similar_destinations = self.data_processor.search_similar_destinations(destination, limit=5)
                    if similar_destinations:
                        context_parts.append(f"- No exact match found, but similar destinations exist:")
                        for i, sim_dest in enumerate(similar_destinations, 1):
                            context_parts.append(f"  {i}. {sim_dest}")
                    else:
                        context_parts.append(f"- No trips found to {destination}")
                        context_parts.append("- Available destinations include various locations in Austin")
            
            # For top destinations queries
            elif query.get("type") == "top_destinations":
                if 'destination' in data.columns and 'trip_count' in data.columns:
                    context_parts.append("- Top destinations with trip counts:")
                    for _, row in data.head(10).iterrows():
                        context_parts.append(f"  * {row['destination']}: {row['trip_count']} trips")
                else:
                    context_parts.append("- Destination analysis available")
            
            # For hourly patterns queries
            elif query.get("type") == "hourly_patterns":
                if 'hour' in data.columns and 'trip_count' in data.columns:
                    context_parts.append("- Hourly trip distribution:")
                    for _, row in data.iterrows():
                        context_parts.append(f"  * Hour {row['hour']}: {row['trip_count']} trips")
                else:
                    context_parts.append("- Time pattern analysis available")
            
            # For group size analysis queries
            elif query.get("type") == "group_size_analysis":
                analysis_result = self.data_processor.analyze_group_size_patterns(filters)
                if analysis_result and not analysis_result.get("error"):
                    context_parts.append("- Group Size Analysis Results:")
                    stats = analysis_result.get("group_size_stats", {})
                    context_parts.append(f"  * Average group size: {stats.get('mean', 0):.2f}")
                    context_parts.append(f"  * Median group size: {stats.get('median', 0):.2f}")
                    context_parts.append(f"  * Most common group size: {stats.get('mode', 'N/A')}")
                    context_parts.append(f"  * Group size range: {stats.get('min', 0)} - {stats.get('max', 0)}")
                    
                    categories = analysis_result.get("size_categories", {})
                    context_parts.append(f"  * Small groups (1-3): {categories.get('small_groups_1_3', 0)} trips")
                    context_parts.append(f"  * Medium groups (4-6): {categories.get('medium_groups_4_6', 0)} trips")
                    context_parts.append(f"  * Large groups (7-10): {categories.get('large_groups_7_10', 0)} trips")
                    context_parts.append(f"  * Very large groups (11+): {categories.get('very_large_groups_11plus', 0)} trips")
                    
                    if "hourly_group_patterns" in analysis_result:
                        context_parts.append("- Hourly group size patterns available")
                    if "daily_group_patterns" in analysis_result:
                        context_parts.append("- Daily group size patterns available")
                    if "age_group_correlations" in analysis_result:
                        context_parts.append("- Age group correlations available")
            
            # For hourly analysis queries
            elif query.get("type") == "hourly_analysis":
                analysis_result = self.data_processor.analyze_hourly_patterns(filters)
                if analysis_result and not analysis_result.get("error"):
                    context_parts.append("- Hourly Pattern Analysis Results:")
                    context_parts.append(f"  * Total trips analyzed: {analysis_result.get('total_trips', 0)}")
                    
                    peak_hours = analysis_result.get("peak_hours", {})
                    if peak_hours:
                        context_parts.append(f"  * Peak hours: {peak_hours}")
                    
                    time_periods = analysis_result.get("time_periods", {})
                    if time_periods:
                        context_parts.append("- Time period distribution:")
                        for period, count in time_periods.items():
                            context_parts.append(f"    * {period.replace('_', ' ').title()}: {count} trips")
                    
                    if "hourly_group_analysis" in analysis_result:
                        context_parts.append("- Hourly group size patterns available")
                    if "large_group_peak_hours" in analysis_result:
                        context_parts.append("- Large group peak hours analysis available")
            
            # For day-of-week analysis queries
            elif query.get("type") == "day_of_week_analysis":
                analysis_result = self.data_processor.analyze_day_of_week_patterns(filters)
                if analysis_result and not analysis_result.get("error"):
                    context_parts.append("- Day-of-Week Analysis Results:")
                    context_parts.append(f"  * Total trips analyzed: {analysis_result.get('total_trips', 0)}")
                    context_parts.append(f"  * Most popular day: {analysis_result.get('most_popular_day', 'N/A')}")
                    
                    weekend_vs_weekday = analysis_result.get("weekend_vs_weekday", {})
                    if weekend_vs_weekday:
                        context_parts.append(f"  * Weekend trips: {weekend_vs_weekday.get('weekend_trips', 0)}")
                        context_parts.append(f"  * Weekday trips: {weekend_vs_weekday.get('weekday_trips', 0)}")
                    
                    if "daily_group_analysis" in analysis_result:
                        context_parts.append("- Daily group size patterns available")
                    if "weekend_vs_weekday_groups" in analysis_result:
                        context_parts.append("- Weekend vs weekday group size analysis available")
                    if "daily_destination_patterns" in analysis_result:
                        context_parts.append("- Daily destination patterns available")
            
            # For age group analysis queries
            elif query.get("type") == "age_group_analysis":
                analysis_result = self.data_processor.analyze_age_group_correlations(filters)
                if analysis_result and not analysis_result.get("error"):
                    context_parts.append("- Age Group Analysis Results:")
                    context_parts.append(f"  * Total trips analyzed: {analysis_result.get('total_trips', 0)}")
                    context_parts.append(f"  * Most common age group: {analysis_result.get('most_common_age_group', 'N/A')}")
                    
                    age_distribution = analysis_result.get("age_group_distribution", {})
                    if age_distribution:
                        context_parts.append("- Age group distribution:")
                        for age_group, count in age_distribution.items():
                            context_parts.append(f"    * {age_group}: {count} trips")
                    
                    if "age_group_group_sizes" in analysis_result:
                        context_parts.append("- Age group group size patterns available")
                    if "large_group_age_preferences" in analysis_result:
                        context_parts.append("- Large group age preferences available")
                    if "age_group_destination_preferences" in analysis_result:
                        context_parts.append("- Age group destination preferences available")
                    if "age_group_time_preferences" in analysis_result:
                        context_parts.append("- Age group time preferences available")
            
            # For monthly analysis queries
            elif query.get("type") == "monthly_analysis":
                analysis_result = self.data_processor.analyze_monthly_trends(filters)
                if analysis_result and not analysis_result.get("error"):
                    context_parts.append("- Monthly Trend Analysis Results:")
                    context_parts.append(f"  * Total trips analyzed: {analysis_result.get('total_trips', 0)}")
                    context_parts.append(f"  * Most active month: {analysis_result.get('most_active_month', 'N/A')}")
                    
                    monthly_dist = analysis_result.get("monthly_distribution", {})
                    if monthly_dist:
                        context_parts.append("- Monthly distribution:")
                        for month, count in monthly_dist.items():
                            context_parts.append(f"    * Month {month}: {count} trips")
                    
                    if "monthly_group_trends" in analysis_result:
                        context_parts.append("- Monthly group size trends available")
                    if "monthly_destination_trends" in analysis_result:
                        context_parts.append("- Monthly destination trends available")
            
            # For large groups queries
            elif query.get("type") == "large_groups":
                context_parts.append("- Large group trip analysis:")
                if 'Total Passengers' in data.columns:
                    large_groups = data[data['Total Passengers'] >= 6]
                    context_parts.append(f"  * Total large group trips: {len(large_groups)}")
                    if len(large_groups) > 0:
                        context_parts.append(f"  * Average group size: {large_groups['Total Passengers'].mean():.2f}")
                        context_parts.append(f"  * Largest group: {large_groups['Total Passengers'].max()}")
            
            # For general queries, provide comprehensive data context
            elif query.get("type") == "general" or query is None:
                context_parts.append("- Comprehensive data analysis available")
                
                # Show all available columns
                if hasattr(data, 'columns'):
                    context_parts.append(f"- Available data columns: {list(data.columns)}")
                
                # Provide detailed data statistics
                context_parts.append("- Data Statistics:")
                
                # Check for common columns and provide stats
                if 'Total Passengers' in data.columns:
                    total_passengers = data['Total Passengers'].sum()
                    avg_passengers = data['Total Passengers'].mean()
                    context_parts.append(f"  * Total passengers across all trips: {total_passengers}")
                    context_parts.append(f"  * Average passengers per trip: {avg_passengers:.2f}")
                
                if 'Trip Date and Time' in data.columns:
                    # Convert to datetime for analysis
                    try:
                        data['datetime'] = pd.to_datetime(data['Trip Date and Time'])
                        context_parts.append(f"  * Trip date range: {data['datetime'].min()} to {data['datetime'].max()}")
                        
                        # Calculate trip duration if we have pickup and dropoff times
                        if 'Pickup Time' in data.columns and 'Drop Off Time' in data.columns:
                            try:
                                pickup_times = pd.to_datetime(data['Pickup Time'], errors='coerce')
                                dropoff_times = pd.to_datetime(data['Drop Off Time'], errors='coerce')
                                durations = (dropoff_times - pickup_times).dt.total_seconds() / 60  # in minutes
                                durations = durations.dropna()
                                if not durations.empty:
                                    avg_duration = durations.mean()
                                    context_parts.append(f"  * Average trip duration: {avg_duration:.2f} minutes")
                                    context_parts.append(f"  * Shortest trip: {durations.min():.2f} minutes")
                                    context_parts.append(f"  * Longest trip: {durations.max():.2f} minutes")
                            except Exception as e:
                                context_parts.append(f"  * Duration calculation error: {str(e)}")
                    except Exception as e:
                        context_parts.append(f"  * Date analysis error: {str(e)}")
                
                if 'Drop Off Address' in data.columns:
                    unique_destinations = data['Drop Off Address'].nunique()
                    context_parts.append(f"  * Unique destinations: {unique_destinations}")
                
                # Show sample data
                if len(data) > 0:
                    context_parts.append(f"- Sample data (first 5 rows):")
                    sample_cols = ['Trip Date and Time', 'Pickup Time', 'Drop Off Time', 'Total Passengers', 'Drop Off Address']
                    available_cols = [col for col in sample_cols if col in data.columns]
                    if available_cols:
                        sample_data = data[available_cols].head(5).to_string(index=False)
                        context_parts.append(sample_data)
                    else:
                        sample_data = data.head(5).to_string(index=False)
                    context_parts.append(sample_data)
            elif query.get("type") == "destination":
                destination = query.get('destination', 'specified destination')
                context_parts.append(f"- Trips to {destination}: {len(data)}")
                
                # Add specific details about the destination
                if 'group_size' in data.columns:
                    total_passengers = data['group_size'].sum()
                    avg_group_size = data['group_size'].mean()
                    context_parts.append(f"- Total passengers to {destination}: {total_passengers}")
                    context_parts.append(f"- Average group size: {avg_group_size:.1f}")
                
                if 'pickup_time' in data.columns:
                    # Get time patterns
                    data_with_time = data.dropna(subset=['pickup_time'])
                    if not data_with_time.empty:
                        data_with_time['hour'] = pd.to_datetime(data_with_time['pickup_time']).dt.hour
                        peak_hour = data_with_time['hour'].mode().iloc[0] if not data_with_time['hour'].mode().empty else "Unknown"
                        context_parts.append(f"- Peak hour for {destination}: {peak_hour}:00")
                
                # Show sample trips
                if len(data) > 0:
                    context_parts.append(f"- Sample trips to {destination}:")
                    sample_trips = data.head(3)[['pickup_location', 'dropoff_location', 'group_size']].to_string(index=False)
                    context_parts.append(sample_trips)
                    
            elif query.get("type") == "age_group_destinations":
                age_group = query.get('age_group', 'specified age group')
                day_filter = f" on {query.get('day_of_week')}" if query.get('day_of_week') else ""
                context_parts.append(f"- Top destinations for {age_group} year-olds{day_filter}:")
                
                # Show top destinations with counts
                for i, (dest, count) in enumerate(data.head(5).items(), 1):
                    context_parts.append(f"  {i}. {dest}: {count} trips")
                
                if len(data) > 0:
                    total_trips = data.sum()
                    context_parts.append(f"- Total trips by {age_group} year-olds{day_filter}: {total_trips}")
                    
            elif query.get("type") == "large_groups":
                context_parts.append(f"- Large group trips (6+ people): {len(data)}")
                if 'group_size' in data.columns:
                    total_passengers = data['group_size'].sum()
                    avg_group_size = data['group_size'].mean()
                    context_parts.append(f"- Total passengers in large groups: {total_passengers}")
                    context_parts.append(f"- Average group size: {avg_group_size:.1f}")
                
                # Show top destinations for large groups
                if 'dropoff_location' in data.columns:
                    top_dests = data['dropoff_location'].value_counts().head(3)
                    context_parts.append(f"- Top destinations for large groups:")
                    for dest, count in top_dests.items():
                        context_parts.append(f"  - {dest}: {count} trips")
                        
            elif query.get("type") == "hourly_distribution":
                context_parts.append(f"- Hourly trip distribution:")
                for hour, count in data.head(10).items():
                    context_parts.append(f"  {hour}:00 - {count} trips")
                peak_hour = data.idxmax() if not data.empty else "Unknown"
                context_parts.append(f"- Peak hour: {peak_hour}:00")
                
            elif query.get("type") == "top_destinations":
                context_parts.append(f"- Top destinations overall:")
                for i, (dest, count) in enumerate(data.head(10).items(), 1):
                    context_parts.append(f"  {i}. {dest}: {count} trips")
                    
        else:
            context_parts.append("No specific data found for this query.")
            context_parts.append("Available data columns:")
            if self.data_processor.trips_data is not None:
                context_parts.append(f"- Trip data columns: {list(self.data_processor.trips_data.columns)}")
            if self.data_processor.users_data is not None:
                context_parts.append(f"- User data columns: {list(self.data_processor.users_data.columns)}")
        
        return "\n".join(context_parts)
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        history = []
        for message in self.memory.chat_memory.messages:
            if isinstance(message, HumanMessage):
                history.append({"role": "user", "content": message.content})
            elif isinstance(message, SystemMessage):
                history.append({"role": "assistant", "content": message.content})
        return history
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        self._setup_system_prompt()
    
    # Removed generate_sample_data method - using real FetiiAI data instead
