"""
Utility functions for data processing and visualization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_synthetic_route_data(num_routes=10, days=30):
    """
    Generate realistic route-level delay data with coordinates
    """
    routes = []
    route_names = ['Red Line', 'Blue Line', 'Green Line', 'Yellow Line', 
                   'Purple Line', 'Orange Line', 'Pink Line', 'Brown Line',
                   'Silver Line', 'Gold Line']
    
    # Realistic coordinates for a city (e.g., Chicago)
    base_lat = 41.8781
    base_lon = -87.6298
    
    for i in range(min(num_routes, len(route_names))):
        # Generate random offset for each route
        lat_offset = random.uniform(-0.5, 0.5)
        lon_offset = random.uniform(-0.5, 0.5)
        
        for day in range(days):
            date = datetime(2024, 1, 1) + timedelta(days=day)
            for hour in range(6, 23):  # 6 AM to 10 PM
                # Base delay pattern
                weather_factor = 1.0
                event_factor = 1.0
                
                # Weekend effect
                if date.weekday() >= 5:
                    weather_factor *= 0.8
                
                # Rush hour effect
                if hour in [7,8,9,17,18,19]:
                    weather_factor *= 1.5
                
                # Generate delay with realistic patterns
                base_delay = np.random.exponential(5) * weather_factor * event_factor
                
                routes.append({
                    'route_id': f'R{i+1:03d}',
                    'route_name': route_names[i],
                    'latitude': base_lat + lat_offset + random.uniform(-0.05, 0.05),
                    'longitude': base_lon + lon_offset + random.uniform(-0.05, 0.05),
                    'date': date,
                    'hour': hour,
                    'delay_minutes': max(0, base_delay + np.random.normal(0, 2)),
                    'day_of_week': date.weekday(),
                    'is_weekend': 1 if date.weekday() >= 5 else 0
                })
    
    return pd.DataFrame(routes)

def calculate_route_performance(df):
    """
    Calculate performance metrics for each route
    """
    performance = df.groupby('route_name').agg({
        'delay_minutes': ['mean', 'median', 'std', 'max'],
        'route_id': 'first'
    }).round(2)
    
    performance.columns = ['avg_delay', 'median_delay', 'std_delay', 'max_delay', 'route_id']
    performance['reliability_score'] = 100 - (performance['avg_delay'] / 10)
    performance['reliability_score'] = performance['reliability_score'].clip(0, 100)
    
    return performance.reset_index()