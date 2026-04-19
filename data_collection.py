"""
Real API Integration: OpenWeatherMap + GTFS Realtime simulation
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
from typing import Dict, Optional

class TransportDataCollector:
    """Collect real-time transport and weather data"""
    
    def __init__(self, weather_api_key: Optional[str] = None):
        """
        Initialize with OpenWeatherMap API key
        Get free key at: https://home.openweathermap.org/users/sign_up
        """
        self.weather_api_key = weather_api_key
        self.base_weather_url = "http://api.openweathermap.org/data/2.5/weather"
        self.cache = {}
        
    def get_weather_data(self, lat: float, lon: float) -> Dict:
        """
        Fetch real-time weather data from OpenWeatherMap API
        """
        if self.weather_api_key:
            try:
                params = {
                    'lat': lat,
                    'lon': lon,
                    'appid': self.weather_api_key,
                    'units': 'metric'
                }
                response = requests.get(self.base_weather_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'temperature': data['main']['temp'],
                        'humidity': data['main']['humidity'],
                        'weather_condition': data['weather'][0]['main'],
                        'wind_speed': data['wind']['speed'],
                        'pressure': data['main']['pressure'],
                        'timestamp': datetime.now()
                    }
            except Exception as e:
                print(f"Weather API error: {e}")
        
        return self._simulate_weather_data()
    
    def _simulate_weather_data(self) -> Dict:
        """Simulate realistic weather data"""
        conditions = ['Clear', 'Clouds', 'Rain', 'Snow', 'Fog', 'Drizzle']
        weights = [0.4, 0.3, 0.15, 0.05, 0.05, 0.05]
        
        return {
            'temperature': np.random.normal(15, 10),
            'humidity': np.random.uniform(30, 90),
            'weather_condition': np.random.choice(conditions, p=weights),
            'wind_speed': np.random.exponential(5),
            'pressure': np.random.normal(1013, 10),
            'timestamp': datetime.now()
        }
    
    def get_gtfs_realtime_data(self, route_id: str) -> Dict:
        """
        Simulate GTFS Realtime feed data
        In production, use: https://developers.google.com/transit/gtfs-realtime
        """
        
        return {
            'route_id': route_id,
            'vehicle_id': f'V_{route_id}_{np.random.randint(1, 20)}',
            'delay_seconds': np.random.exponential(300), 
            'speed_kmh': np.random.uniform(10, 60),
            'occupancy': np.random.choice(['EMPTY', 'MANY_SEATS', 'FEW_SEATS', 'STANDING', 'CRUSHED']),
            'timestamp': datetime.now(),
            'latitude': np.random.uniform(40.7, 42.0),
            'longitude': np.random.uniform(-87.9, -87.5)
        }
    
    def collect_batch_data(self, num_records: int = 1000) -> pd.DataFrame:
        """
        Collect batch of transport data with weather conditions
        """
        records = []
        
        for _ in range(num_records):
           
            route_id = f"R{np.random.randint(1, 20):03d}"
            hour = np.random.randint(0, 24)
            day = np.random.randint(0, 30)
            date = datetime(2024, 1, 1) + timedelta(days=day)
            
           
            weather = self._simulate_weather_data()
            
          
            events = ['None', 'Concert', 'Sports', 'Marathon', 'Festival']
            event_probs = [0.7, 0.1, 0.1, 0.05, 0.05]
            event = np.random.choice(events, p=event_probs)
         

            delay = self._calculate_delay(
                weather['weather_condition'], 
                event, 
                hour,
                date.weekday()
            )
            
            records.append({
                'route_id': route_id,
                'timestamp': date,
                'hour': hour,
                'day_of_week': date.weekday(),
                'weather_condition': weather['weather_condition'],
                'temperature': weather['temperature'],
                'humidity': weather['humidity'],
                'wind_speed': weather['wind_speed'],
                'event_type': event,
                'delay_minutes': delay,
                'latitude': np.random.uniform(40.7, 42.0),
                'longitude': np.random.uniform(-87.9, -87.5)
            })
        
        return pd.DataFrame(records)
    
    def _calculate_delay(self, weather: str, event: str, hour: int, day_of_week: int) -> float:
        """Calculate realistic delay based on factors"""
        delay = 0
        
        
        weather_impact = {
            'Clear': np.random.uniform(0, 3),
            'Clouds': np.random.uniform(1, 5),
            'Rain': np.random.uniform(5, 15),
            'Drizzle': np.random.uniform(3, 8),
            'Fog': np.random.uniform(5, 12),
            'Snow': np.random.uniform(15, 35)
        }
        delay += weather_impact.get(weather, np.random.uniform(0, 5))
        
        
        event_impact = {
            'None': 0,
            'Concert': np.random.uniform(8, 20),
            'Sports': np.random.uniform(5, 18),
            'Marathon': np.random.uniform(15, 40),
            'Festival': np.random.uniform(10, 25)
        }
        delay += event_impact.get(event, 0)
        
        
        if hour in [7, 8, 9, 17, 18, 19]:
            delay += np.random.uniform(5, 12)

        
        if day_of_week >= 5:
            delay *= 0.8
        
        return max(0, delay + np.random.normal(0, 2))


if __name__ == "__main__":
    collector = TransportDataCollector()
    df = collector.collect_batch_data(500)
    print(f"Collected {len(df)} records")
    print(df.head())
    df.to_csv('data/real_time_transport_data.csv', index=False)