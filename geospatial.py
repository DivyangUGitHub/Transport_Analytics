"""
Geospatial analysis for route-level delay patterns
"""

import pandas as pd
import numpy as np
import folium
from folium import plugins
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from sklearn.cluster import DBSCAN
import warnings
warnings.filterwarnings('ignore')

class GeospatialAnalyzer:
    """Analyze transport delays geographically"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.map = None
        
    def create_delay_hotspot_map(self, center_lat: float = 41.8781, 
                                  center_lon: float = -87.6298,
                                  zoom_start: int = 12) -> folium.Map:
        """
        Create interactive map with delay hotspots
        """
        # Base map
        self.map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_start,
            tiles='CartoDB positron'
        )
        
        # Add heatmap layer for delays
        heat_data = [[row['latitude'], row['longitude'], row['delay_minutes']] 
                     for _, row in self.data.iterrows()]
        
        plugins.HeatMap(heat_data, radius=15, blur=10, max_zoom=1).add_to(self.map)
        
        # Add markers for high delay locations (top 10%)
        threshold = self.data['delay_minutes'].quantile(0.9)
        high_delay = self.data[self.data['delay_minutes'] > threshold]
        
        for _, row in high_delay.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=row['delay_minutes'] / 5,
                popup=f"Delay: {row['delay_minutes']:.1f} min<br>Route: {row.get('route_name', 'Unknown')}",
                color='red',
                fill=True,
                fillColor='crimson',
                fillOpacity=0.6
            ).add_to(self.map)
        
        return self.map
    
    def identify_congestion_clusters(self, eps: float = 0.01, min_samples: int = 5):
        """
        Use DBSCAN clustering to identify congestion clusters
        """
        coordinates = self.data[['latitude', 'longitude']].values
        delays = self.data['delay_minutes'].values
        
        # Perform clustering
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(coordinates)
        self.data['cluster'] = clustering.labels_
        
        # Analyze clusters
        cluster_analysis = self.data.groupby('cluster').agg({
            'delay_minutes': ['mean', 'max', 'count'],
            'latitude': 'mean',
            'longitude': 'mean'
        }).round(2)
        
        # Filter out noise (-1 cluster)
        cluster_analysis = cluster_analysis[cluster_analysis.index != -1]
        cluster_analysis = cluster_analysis.sort_values(('delay_minutes', 'mean'), ascending=False)
        
        print("\n" + "="*50)
        print("CONGESTION CLUSTER ANALYSIS")
        print("="*50)
        print("\nTop 5 Congestion Hotspots:")
        print(cluster_analysis.head(5))
        
        return cluster_analysis
    
    def calculate_route_performance_metrics(self):
        """
        Calculate performance metrics per route with geospatial context
        """
        if 'route_name' not in self.data.columns:
            self.data['route_name'] = 'Route_' + self.data['route_id'].astype(str)
        
        route_metrics = self.data.groupby('route_name').agg({
            'delay_minutes': ['mean', 'median', 'std', 'max'],
            'latitude': 'mean',
            'longitude': 'mean',
            'route_id': 'first'
        }).round(2)
        
        route_metrics.columns = ['avg_delay', 'median_delay', 'std_delay', 
                                 'max_delay', 'lat', 'lon', 'route_id']
        
        # Add performance grade
        route_metrics['performance_grade'] = pd.cut(
            route_metrics['avg_delay'],
            bins=[0, 5, 10, 15, 20, 100],
            labels=['A (Excellent)', 'B (Good)', 'C (Fair)', 'D (Poor)', 'F (Critical)']
        )
        
        # Calculate reliability index
        route_metrics['reliability_index'] = 100 - (route_metrics['avg_delay'] / route_metrics['max_delay'].clip(lower=1) * 100)
        route_metrics['reliability_index'] = route_metrics['reliability_index'].clip(0, 100)
        
        print("\n" + "="*50)
        print("ROUTE PERFORMANCE METRICS")
        print("="*50)
        print(route_metrics[['avg_delay', 'max_delay', 'performance_grade', 'reliability_index']].head(10))
        
        return route_metrics
    
    def create_route_performance_map(self, route_metrics: pd.DataFrame):
        """
        Create map showing route performance
        """
        if self.map is None:
            self.map = folium.Map(location=[41.8781, -87.6298], zoom_start=11)
        
        # Color mapping based on performance
        color_map = {
            'A (Excellent)': 'green',
            'B (Good)': 'lightgreen',
            'C (Fair)': 'orange',
            'D (Poor)': 'red',
            'F (Critical)': 'darkred'
        }
        
        for _, route in route_metrics.iterrows():
            folium.Marker(
                location=[route['lat'], route['lon']],
                popup=f"""
                <b>{route.name}</b><br>
                Avg Delay: {route['avg_delay']:.1f} min<br>
                Max Delay: {route['max_delay']:.1f} min<br>
                Grade: {route['performance_grade']}<br>
                Reliability: {route['reliability_index']:.1f}%
                """,
                icon=folium.Icon(color=color_map.get(route['performance_grade'], 'gray'), 
                                icon='bus', prefix='fa')
            ).add_to(self.map)
        
        return self.map
    
    def generate_geospatial_report(self):
        """
        Generate comprehensive geospatial analysis report
        """
        print("\n" + "="*60)
        print("GEOSPATIAL ANALYSIS REPORT")
        print("="*60)
        
        # 1. Spatial statistics
        print("\n📍 Spatial Distribution Statistics:")
        print(f"   Total unique locations: {self.data[['latitude', 'longitude']].drop_duplicates().shape[0]}")
        print(f"   Latitude range: [{self.data['latitude'].min():.4f}, {self.data['latitude'].max():.4f}]")
        print(f"   Longitude range: [{self.data['longitude'].min():.4f}, {self.data['longitude'].max():.4f}]")
        
        # 2. High-risk zones
        high_risk = self.data[self.data['delay_minutes'] > self.data['delay_minutes'].quantile(0.9)]
        print(f"\n⚠️ High-Risk Zones (Top 10% delays):")
        print(f"   Number of incidents: {len(high_risk)}")
        print(f"   Average delay in high-risk zones: {high_risk['delay_minutes'].mean():.1f} min")
        
        # 3. Cluster analysis
        clusters = self.identify_congestion_clusters()
        print(f"\n🔍 Congestion Clusters Found: {len(clusters[clusters.index != -1])}")
        
        return {
            'spatial_stats': {
                'unique_locations': self.data[['latitude', 'longitude']].drop_duplicates().shape[0],
                'lat_range': (self.data['latitude'].min(), self.data['latitude'].max()),
                'lon_range': (self.data['longitude'].min(), self.data['longitude'].max())
            },
            'high_risk_zones': {
                'count': len(high_risk),
                'avg_delay': high_risk['delay_minutes'].mean()
            },
            'clusters': clusters
        }

# Example usage
if __name__ == "__main__":
    # Load or create sample data
    from utils import generate_synthetic_route_data
    
    df = generate_synthetic_route_data(num_routes=10, days=7)
    
    # Initialize geospatial analyzer
    geo_analyzer = GeospatialAnalyzer(df)
    
    # Create maps
    hotspot_map = geo_analyzer.create_delay_hotspot_map()
    hotspot_map.save('data/delay_hotspots.html')
    print("Hotspot map saved to 'data/delay_hotspots.html'")
    
    # Calculate route metrics
    route_metrics = geo_analyzer.calculate_route_performance_metrics()
    
    # Generate report
    report = geo_analyzer.generate_geospatial_report()
    
    # Save metrics
    route_metrics.to_csv('data/route_performance_metrics.csv')
    print("\nRoute metrics saved to 'data/route_performance_metrics.csv'")